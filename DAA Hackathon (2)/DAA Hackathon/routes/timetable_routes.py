import json
from flask import Blueprint, request, jsonify, render_template
from database.db import query_db, execute_db, get_scheduling_problem_data
from algorithms.backtracking import BacktrackingScheduler
from algorithms.greedy import GreedyScheduler
from algorithms.graph_coloring import GraphColoringScheduler
from algorithms.hybrid import HybridScheduler
from algorithms.constraints import ConstraintChecker
from config import Config

timetable_bp = Blueprint('timetable', __name__)

@timetable_bp.route('/timetable', methods=['GET'])
def timetable_page():
    batches = query_db("SELECT * FROM student_batches ORDER BY name")
    faculty = query_db("SELECT * FROM faculty ORDER BY name")
    rooms = query_db("SELECT * FROM classrooms ORDER BY name")
    departments = query_db("SELECT DISTINCT department FROM student_batches ORDER BY department")
    return render_template(
        'timetable.html',
        batches=batches,
        faculty=faculty,
        rooms=rooms,
        departments=[d['department'] for d in departments],
        period_timings=Config.PERIOD_TIMINGS,
        college_name=Config.COLLEGE_NAME
    )

@timetable_bp.route('/generate', methods=['GET'])
def generate_page():
    batches = query_db("SELECT * FROM student_batches ORDER BY name")
    faculty = query_db("SELECT * FROM faculty ORDER BY name")
    rooms = query_db("SELECT * FROM classrooms ORDER BY name")
    departments = query_db("SELECT DISTINCT department FROM student_batches ORDER BY department")
    return render_template(
        'generate.html',
        batches=batches,
        faculty=faculty,
        rooms=rooms,
        departments=[d['department'] for d in departments],
        default_days=Config.DEFAULT_WORKING_DAYS,
        college_name=Config.COLLEGE_NAME
    )

@timetable_bp.route('/api/generate-timetable', methods=['POST'])
def generate_timetable():
    data = request.get_json() or {}
    algorithm = data.get('algorithm', 'backtracking').lower()
    batch_ids = data.get('batch_ids')
    working_days = data.get('working_days', Config.DEFAULT_WORKING_DAYS)
    periods_per_day = int(data.get('periods_per_day', Config.DEFAULT_PERIODS_PER_DAY))

    # Load problem data
    problem_data = get_scheduling_problem_data(
        batch_ids=batch_ids,
        working_days=working_days,
        periods_per_day=periods_per_day
    )

    if not problem_data["sessions"]:
        return jsonify({
            "status": "error",
            "message": "No courses found for scheduling in the selected criteria."
        }), 400

    # Select solver
    if algorithm in ['backtracking', 'bt']:
        solver = BacktrackingScheduler(problem_data)
    elif algorithm in ['greedy']:
        solver = GreedyScheduler(problem_data)
    elif algorithm in ['graph_coloring', 'graph', 'welsh_powell']:
        solver = GraphColoringScheduler(problem_data)
    elif algorithm in ['hybrid', 'hybrid_scheduling']:
        solver = HybridScheduler(problem_data)
    else:
        return jsonify({"status": "error", "message": f"Unsupported algorithm '{algorithm}'."}), 400

    result = solver.solve()

    # Save to SQLite if classes were scheduled
    schedule = result.get("schedule", [])
    if schedule:
        if batch_ids:
            placeholders = ','.join('?' for _ in batch_ids)
            execute_db(f"DELETE FROM timetable WHERE batch_id IN ({placeholders})", batch_ids)
        else:
            execute_db("DELETE FROM timetable")

        for item in schedule:
            execute_db(
                """
                INSERT INTO timetable (session_code, subject_id, faculty_id, classroom_id, batch_id, time_slot_id, day, period, algorithm_used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item["session_code"],
                    item["subject_id"],
                    item["faculty_id"],
                    item["classroom_id"],
                    item["batch_id"],
                    item["time_slot_id"],
                    item["day"],
                    item["period"],
                    result["algorithm"]
                )
            )

    # Save execution log
    execute_db(
        """
        INSERT INTO algorithm_logs (algorithm_name, execution_time_ms, scheduled_classes, unscheduled_classes, conflicts_count, backtracking_steps, decisions_count, success_status, metrics_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result["algorithm"],
            result["execution_time_ms"],
            result["scheduled_classes"],
            result["unscheduled_classes"],
            result["conflicts_count"],
            result["backtracking_steps"],
            result["decisions_count"],
            1 if result["success"] else 0,
            json.dumps({"algorithm": result["algorithm"], "total_classes": result["total_classes"]})
        )
    )

    return jsonify({
        "status": "success",
        "result": result
    }), 200

@timetable_bp.route('/api/timetable', methods=['GET'])
def get_timetable():
    batch_id = request.args.get('batch_id')
    faculty_id = request.args.get('faculty_id')
    classroom_id = request.args.get('classroom_id')
    department = request.args.get('department')
    day = request.args.get('day')

    query = """
        SELECT t.*, s.name as subject_name, s.code as subject_code, s.type as subject_type, s.color_hex,
               f.name as faculty_name, f.department as faculty_department,
               c.name as classroom_name, c.room_type as classroom_type, c.capacity as classroom_capacity,
               b.name as batch_name, b.department as batch_department, b.student_strength,
               ts.start_time, ts.end_time
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN faculty f ON t.faculty_id = f.id
        JOIN classrooms c ON t.classroom_id = c.id
        JOIN student_batches b ON t.batch_id = b.id
        JOIN time_slots ts ON t.time_slot_id = ts.id
        WHERE 1=1
    """
    params = []
    if batch_id:
        query += " AND t.batch_id = ?"
        params.append(batch_id)
    if faculty_id:
        query += " AND t.faculty_id = ?"
        params.append(faculty_id)
    if classroom_id:
        query += " AND t.classroom_id = ?"
        params.append(classroom_id)
    if department:
        query += " AND (b.department = ? OR f.department = ?)"
        params.append(department)
        params.append(department)
    if day:
        query += " AND t.day = ?"
        params.append(day)

    query += " ORDER BY t.day, t.period"
    entries = query_db(query, params)

    return jsonify({
        "status": "success",
        "count": len(entries),
        "data": entries
    }), 200

@timetable_bp.route('/api/timetable/move', methods=['PUT'])
def move_timetable_session():
    """
    Drag-and-Drop validation and persistence.
    Validates faculty, classroom, batch availability and capacity before updating.
    """
    data = request.get_json() or {}
    timetable_id = data.get('timetable_id')
    target_day = data.get('target_day')
    target_period = int(data.get('target_period', 1))
    target_room_id = data.get('target_room_id') # optional, keep current room if omitted

    if not timetable_id or not target_day:
        return jsonify({"status": "error", "message": "Timetable ID and target day are required."}), 400

    # 1. Fetch current entry
    entry = query_db("""
        SELECT t.*, s.name as subject_name, s.type as subject_type,
               b.name as batch_name, b.student_strength,
               f.name as faculty_name,
               c.name as current_room_name, c.capacity as current_capacity, c.room_type as current_room_type
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN student_batches b ON t.batch_id = b.id
        JOIN faculty f ON t.faculty_id = f.id
        JOIN classrooms c ON t.classroom_id = c.id
        WHERE t.id = ?
    """, (timetable_id,), one=True)

    if not entry:
        return jsonify({"status": "error", "message": "Timetable session not found."}), 404

    dest_room_id = target_room_id if target_room_id else entry['classroom_id']
    dest_room = query_db("SELECT * FROM classrooms WHERE id = ?", (dest_room_id,), one=True)
    if not dest_room:
        return jsonify({"status": "error", "message": "Target classroom not found."}), 404

    # 2. Check Faculty Unavailability
    unavail = query_db(
        "SELECT 1 FROM faculty_availability WHERE faculty_id = ? AND day = ? AND period = ? AND is_available = 0",
        (entry['faculty_id'], target_day, target_period),
        one=True
    )
    if unavail:
        return jsonify({
            "status": "conflict",
            "message": f"Cannot move: Faculty {entry['faculty_name']} is unavailable on {target_day} Period {target_period}."
        }), 409

    # 3. Check Classroom Capacity
    if dest_room['capacity'] < entry['student_strength']:
        return jsonify({
            "status": "conflict",
            "message": f"Cannot move: Classroom {dest_room['name']} capacity ({dest_room['capacity']}) is less than batch size ({entry['student_strength']})."
        }), 409

    # 4. Check Lab Type Requirement
    is_lab = entry['subject_type'] == 'Lab' or 'Lab' in entry['subject_name']
    if is_lab and dest_room['room_type'] != 'Lab':
        return jsonify({
            "status": "conflict",
            "message": f"Cannot move: Practical lab course requires an equipped Lab space, but {dest_room['name']} is a Normal lecture hall."
        }), 409

    # 5. Check Collisions with other sessions in target slot
    collisions = query_db(
        """
        SELECT t.*, f.name as fac_name, c.name as rm_name, b.name as bt_name
        FROM timetable t
        JOIN faculty f ON t.faculty_id = f.id
        JOIN classrooms c ON t.classroom_id = c.id
        JOIN student_batches b ON t.batch_id = b.id
        WHERE t.day = ? AND t.period = ? AND t.id != ?
        """,
        (target_day, target_period, timetable_id)
    )

    for c in collisions:
        if c['faculty_id'] == entry['faculty_id']:
            return jsonify({
                "status": "conflict",
                "message": f"Faculty Clash: {entry['faculty_name']} is already teaching {c['session_code']} at {target_day} Period {target_period}."
            }), 409
        if c['classroom_id'] == dest_room_id:
            return jsonify({
                "status": "conflict",
                "message": f"Classroom Collision: Room {dest_room['name']} is already reserved by batch {c['bt_name']} in this period."
            }), 409
        if c['batch_id'] == entry['batch_id']:
            return jsonify({
                "status": "conflict",
                "message": f"Batch Clash: Student batch {entry['batch_name']} already has class {c['session_code']} at this time."
            }), 409

    # 6. Find target time slot ID
    target_slot = query_db(
        "SELECT id FROM time_slots WHERE day = ? AND period = ?",
        (target_day, target_period),
        one=True
    )
    if not target_slot:
        return jsonify({"status": "error", "message": f"Time slot for {target_day} Period {target_period} does not exist."}), 400

    # 7. Apply Move Update in Database
    execute_db(
        """
        UPDATE timetable
        SET day = ?, period = ?, classroom_id = ?, time_slot_id = ?
        WHERE id = ?
        """,
        (target_day, target_period, dest_room_id, target_slot['id'], timetable_id)
    )

    return jsonify({
        "status": "success",
        "message": f"Session successfully moved to {target_day} Period {target_period} ({dest_room['name']})."
    }), 200
