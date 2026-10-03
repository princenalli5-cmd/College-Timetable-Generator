from flask import Blueprint, render_template, jsonify, request
from database.db import query_db, execute_db
from config import Config

substitution_bp = Blueprint('substitution', __name__)

@substitution_bp.route('/substitution', methods=['GET'])
def substitution_page():
    faculty = query_db("SELECT * FROM faculty ORDER BY name")
    timetable_sessions = query_db("""
        SELECT t.id, t.session_code, s.name as subject_name, s.code as subject_code,
               f.name as faculty_name, f.id as faculty_id,
               c.name as classroom_name, b.name as batch_name,
               t.day, t.period, ts.start_time, ts.end_time
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN faculty f ON t.faculty_id = f.id
        JOIN classrooms c ON t.classroom_id = c.id
        JOIN student_batches b ON t.batch_id = b.id
        JOIN time_slots ts ON t.time_slot_id = ts.id
        ORDER BY t.day, t.period
    """)
    return render_template(
        'substitution.html',
        faculty=faculty,
        sessions=timetable_sessions,
        college_name=Config.COLLEGE_NAME
    )

@substitution_bp.route('/api/substitutions', methods=['GET'])
def get_substitutions():
    subs = query_db("""
        SELECT sub.*,
               f1.name as original_faculty_name, f1.department as original_department,
               f2.name as substitute_faculty_name, f2.department as substitute_department,
               t.session_code, s.name as subject_name, s.code as subject_code,
               c.name as classroom_name, b.name as batch_name,
               ts.start_time, ts.end_time
        FROM substitutions sub
        JOIN timetable t ON sub.timetable_id = t.id
        JOIN faculty f1 ON sub.original_faculty_id = f1.id
        JOIN faculty f2 ON sub.substitute_faculty_id = f2.id
        JOIN subjects s ON t.subject_id = s.id
        JOIN classrooms c ON t.classroom_id = c.id
        JOIN student_batches b ON t.batch_id = b.id
        JOIN time_slots ts ON t.time_slot_id = ts.id
        ORDER BY sub.id DESC
    """)
    return jsonify({"status": "success", "count": len(subs), "data": subs}), 200

@substitution_bp.route('/api/substitution/recommendations', methods=['GET'])
def get_substitution_recommendations():
    timetable_id = request.args.get('timetable_id')
    if not timetable_id:
        return jsonify({"status": "error", "message": "timetable_id is required."}), 400

    session = query_db("""
        SELECT t.*, s.name as subject_name, s.code as subject_code, s.department as subject_department,
               f.name as faculty_name, f.department as faculty_department,
               b.name as batch_name, c.name as classroom_name
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN faculty f ON t.faculty_id = f.id
        JOIN student_batches b ON t.batch_id = b.id
        JOIN classrooms c ON t.classroom_id = c.id
        WHERE t.id = ?
    """, (timetable_id,), one=True)

    if not session:
        return jsonify({"status": "error", "message": "Timetable session not found."}), 404

    target_day = session['day']
    target_period = session['period']
    orig_fac_id = session['faculty_id']
    subj_dept = session['subject_department']

    # Find faculty who are NOT teaching in this day and period
    all_faculty = query_db("SELECT * FROM faculty WHERE id != ?", (orig_fac_id,))
    busy_fac_ids = set(r['faculty_id'] for r in query_db(
        "SELECT faculty_id FROM timetable WHERE day = ? AND period = ?",
        (target_day, target_period)
    ))

    # Faculty blocked slots
    blocked_fac_ids = set(r['faculty_id'] for r in query_db(
        "SELECT faculty_id FROM faculty_availability WHERE day = ? AND period = ? AND is_available = 0",
        (target_day, target_period)
    ))

    # Workload counts
    workload_rows = query_db("SELECT faculty_id, COUNT(*) as c FROM timetable GROUP BY faculty_id")
    workload_map = {r['faculty_id']: r['c'] for r in workload_rows}

    recommendations = []
    for fac in all_faculty:
        fac_id = fac['id']
        is_free = fac_id not in busy_fac_ids
        is_available = fac_id not in blocked_fac_ids
        same_dept = fac['department'] == subj_dept
        current_load = workload_map.get(fac_id, 0)
        max_load = fac['max_hours_per_week']
        under_capacity = current_load < max_load

        # Calculate suitability match score
        score = 0
        reasons = []

        if not is_free:
            score -= 100
            reasons.append("Currently teaching another class")
        else:
            score += 40
            reasons.append("Free in this time slot")

        if not is_available:
            score -= 50
            reasons.append("Marked personal unavailable slot")
        else:
            score += 20
            reasons.append("Available schedule window")

        if same_dept:
            score += 30
            reasons.append(f"Domain match ({fac['department']})")
        else:
            score += 5
            reasons.append(f"Cross-department ({fac['department']})")

        if under_capacity:
            score += 10
            reasons.append(f"Workload headroom: {current_load}/{max_load} hrs")
        else:
            score -= 15
            reasons.append(f"At max weekly capacity ({current_load}/{max_load} hrs)")

        recommendations.append({
            "faculty_id": fac_id,
            "faculty_name": fac['name'],
            "department": fac['department'],
            "designation": fac['designation'],
            "is_eligible": is_free and is_available,
            "match_score": max(0, min(100, score)),
            "current_hours": current_load,
            "max_hours": max_load,
            "reasons": reasons
        })

    # Sort candidates by eligibility and match score descending
    recommendations.sort(key=lambda r: (r['is_eligible'], r['match_score']), reverse=True)

    return jsonify({
        "status": "success",
        "affected_session": session,
        "recommendations": recommendations
    }), 200

@substitution_bp.route('/api/substitutions', methods=['POST'])
def create_substitution():
    data = request.get_json() or {}
    timetable_id = data.get('timetable_id')
    substitute_faculty_id = data.get('substitute_faculty_id')
    reason = data.get('reason', 'Faculty leave/emergency').strip()

    if not timetable_id or not substitute_faculty_id:
        return jsonify({"status": "error", "message": "Session and substitute faculty are required."}), 400

    session = query_db("SELECT * FROM timetable WHERE id = ?", (timetable_id,), one=True)
    if not session:
        return jsonify({"status": "error", "message": "Session not found."}), 404

    # Record substitution
    last_id, _ = execute_db(
        """
        INSERT INTO substitutions (timetable_id, original_faculty_id, substitute_faculty_id, day, period, reason, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (timetable_id, session['faculty_id'], substitute_faculty_id, session['day'], session['period'], reason, 'Approved')
    )

    # Immediately update timetable to reassign the faculty
    execute_db(
        "UPDATE timetable SET faculty_id = ? WHERE id = ?",
        (substitute_faculty_id, timetable_id)
    )

    return jsonify({
        "status": "success",
        "substitution_id": last_id,
        "message": "Faculty substitution approved and timetable updated successfully."
    }), 201
