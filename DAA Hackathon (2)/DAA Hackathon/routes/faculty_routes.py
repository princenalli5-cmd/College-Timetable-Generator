from flask import Blueprint, request, jsonify, render_template
from database.db import query_db, execute_db
from config import Config

faculty_bp = Blueprint('faculty', __name__)

@faculty_bp.route('/faculty', methods=['GET'])
def faculty_page():
    return render_template('faculty.html', college_name=Config.COLLEGE_NAME)

@faculty_bp.route('/availability', methods=['GET'])
def availability_page():
    faculty = query_db("SELECT * FROM faculty ORDER BY name")
    return render_template(
        'availability.html',
        faculty=faculty,
        working_days=Config.DEFAULT_WORKING_DAYS,
        periods=list(range(1, Config.DEFAULT_PERIODS_PER_DAY + 1)),
        college_name=Config.COLLEGE_NAME
    )

@faculty_bp.route('/api/faculty', methods=['GET'])
def get_faculty_list():
    faculty = query_db("SELECT * FROM faculty ORDER BY name")
    for f in faculty:
        # Assigned subjects
        subjects = query_db("SELECT id, code, name, weekly_hours, practical_hours FROM subjects WHERE faculty_id = ?", (f['id'],))
        f['assigned_subjects'] = subjects
        f['total_assigned_hours'] = sum(s['weekly_hours'] + s['practical_hours'] for s in subjects)

        # Scheduled hours in current timetable
        sched_count = query_db("SELECT COUNT(*) as c FROM timetable WHERE faculty_id = ?", (f['id'],), one=True)['c']
        f['scheduled_timetable_hours'] = sched_count

        # Blocked slots
        unavail = query_db("SELECT day, period, reason FROM faculty_availability WHERE faculty_id = ? AND is_available = 0", (f['id'],))
        f['unavailable_slots'] = unavail

    return jsonify({"status": "success", "count": len(faculty), "data": faculty}), 200

@faculty_bp.route('/api/faculty/<int:faculty_id>', methods=['GET'])
def get_faculty_details(faculty_id):
    faculty = query_db("SELECT * FROM faculty WHERE id = ?", (faculty_id,), one=True)
    if not faculty:
        return jsonify({"status": "error", "message": "Faculty not found."}), 404

    subjects = query_db("SELECT s.*, b.name as batch_name FROM subjects s JOIN student_batches b ON s.batch_id = b.id WHERE s.faculty_id = ?", (faculty_id,))
    unavail = query_db("SELECT day, period, reason FROM faculty_availability WHERE faculty_id = ? AND is_available = 0", (faculty_id,))
    assigned_timetable = query_db("""
        SELECT t.*, s.name as subject_name, s.code as subject_code, c.name as classroom_name, b.name as batch_name
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN classrooms c ON t.classroom_id = c.id
        JOIN student_batches b ON t.batch_id = b.id
        WHERE t.faculty_id = ?
        ORDER BY t.day, t.period
    """, (faculty_id,))

    return jsonify({
        "status": "success",
        "faculty": faculty,
        "subjects": subjects,
        "unavailable_slots": unavail,
        "timetable": assigned_timetable,
        "total_teaching_hours": len(assigned_timetable)
    }), 200

@faculty_bp.route('/api/faculty', methods=['POST'])
def create_faculty():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    department = data.get('department', '').strip()
    email = data.get('email', '').strip()
    designation = data.get('designation', 'Assistant Professor').strip()
    max_hours_per_day = int(data.get('max_hours_per_day', 4))
    max_hours_per_week = int(data.get('max_hours_per_week', 16))
    unavailable_slots = data.get('unavailable_slots', [])

    if not name or not department:
        return jsonify({"status": "error", "message": "Name and Department are required."}), 400

    try:
        last_id, _ = execute_db(
            """
            INSERT INTO faculty (name, department, email, designation, max_hours_per_day, max_hours_per_week)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, department, email or None, designation, max_hours_per_day, max_hours_per_week)
        )

        for slot in unavailable_slots:
            execute_db(
                "INSERT OR REPLACE INTO faculty_availability (faculty_id, day, period, is_available, reason) VALUES (?, ?, ?, 0, ?)",
                (last_id, slot['day'], int(slot['period']), slot.get('reason', 'Blocked by admin'))
            )

        return jsonify({"status": "success", "id": last_id, "message": "Faculty member added successfully."}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@faculty_bp.route('/api/faculty/<int:faculty_id>', methods=['PUT'])
def update_faculty(faculty_id):
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    department = data.get('department', '').strip()
    email = data.get('email', '').strip()
    designation = data.get('designation', 'Assistant Professor').strip()
    max_hours_per_day = int(data.get('max_hours_per_day', 4))
    max_hours_per_week = int(data.get('max_hours_per_week', 16))
    unavailable_slots = data.get('unavailable_slots')

    if not name or not department:
        return jsonify({"status": "error", "message": "Name and Department are required."}), 400

    try:
        _, rowcount = execute_db(
            """
            UPDATE faculty
            SET name = ?, department = ?, email = ?, designation = ?, max_hours_per_day = ?, max_hours_per_week = ?
            WHERE id = ?
            """,
            (name, department, email or None, designation, max_hours_per_day, max_hours_per_week, faculty_id)
        )
        if rowcount == 0:
            return jsonify({"status": "error", "message": "Faculty not found."}), 404

        if unavailable_slots is not None:
            execute_db("DELETE FROM faculty_availability WHERE faculty_id = ?", (faculty_id,))
            for slot in unavailable_slots:
                execute_db(
                    "INSERT INTO faculty_availability (faculty_id, day, period, is_available, reason) VALUES (?, ?, ?, 0, ?)",
                    (faculty_id, slot['day'], int(slot['period']), slot.get('reason', 'Blocked slot'))
                )

        return jsonify({"status": "success", "message": "Faculty updated successfully."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@faculty_bp.route('/api/faculty/<int:faculty_id>', methods=['DELETE'])
def delete_faculty(faculty_id):
    _, rowcount = execute_db("DELETE FROM faculty WHERE id = ?", (faculty_id,))
    if rowcount == 0:
        return jsonify({"status": "error", "message": "Faculty not found."}), 404
    return jsonify({"status": "success", "message": "Faculty deleted successfully."}), 200

@faculty_bp.route('/api/faculty/availability/toggle', methods=['POST'])
def toggle_availability():
    data = request.get_json() or {}
    faculty_id = data.get('faculty_id')
    day = data.get('day')
    period = data.get('period')
    is_available = int(data.get('is_available', 1))
    reason = data.get('reason', 'Admin toggle')

    if not faculty_id or not day or not period:
        return jsonify({"status": "error", "message": "faculty_id, day, and period are required."}), 400

    execute_db(
        """
        INSERT INTO faculty_availability (faculty_id, day, period, is_available, reason)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(faculty_id, day, period) DO UPDATE SET
            is_available = excluded.is_available,
            reason = excluded.reason
        """,
        (faculty_id, day, int(period), is_available, reason)
    )
    return jsonify({"status": "success", "message": "Availability updated."}), 200
