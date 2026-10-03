from flask import Blueprint, jsonify, render_template
from database.db import query_db
from algorithms.constraints import ConstraintChecker
from config import Config

conflict_bp = Blueprint('conflicts', __name__)

@conflict_bp.route('/conflicts', methods=['GET'])
def conflicts_page():
    return render_template('conflicts.html', college_name=Config.COLLEGE_NAME)

@conflict_bp.route('/api/conflicts', methods=['GET'])
def audit_conflicts():
    """Runs automated full audit against all 6 scheduling constraints."""
    entries = query_db("""
        SELECT t.*, s.name as subject_name, s.code as subject_code, s.type,
               f.name as faculty_name, c.name as classroom_name, c.room_type as classroom_type, c.capacity as classroom_capacity,
               b.name as batch_name, b.student_strength,
               ts.start_time, ts.end_time
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN faculty f ON t.faculty_id = f.id
        JOIN classrooms c ON t.classroom_id = c.id
        JOIN student_batches b ON t.batch_id = b.id
        JOIN time_slots ts ON t.time_slot_id = ts.id
    """)

    rooms = query_db("SELECT * FROM classrooms")
    classroom_map = {r['id']: r for r in rooms}

    unavail_rows = query_db("SELECT faculty_id, day, period FROM faculty_availability WHERE is_available = 0")
    faculty_unavail = set((r['faculty_id'], r['day'], r['period']) for r in unavail_rows)

    conflicts = ConstraintChecker.audit_full_schedule(entries, faculty_unavail, classroom_map)

    # Calculate status per rule category
    rule_statuses = {
        "faculty_clash": any(c['type'] == 'Faculty Double-Booking' for c in conflicts),
        "classroom_clash": any(c['type'] == 'Classroom Double-Booking' for c in conflicts),
        "batch_clash": any(c['type'] == 'Student Batch Timetable Clash' for c in conflicts),
        "faculty_unavailable": any(c['type'] == 'Faculty Unavailable Violation' for c in conflicts),
        "capacity_overload": any(c['type'] == 'Classroom Capacity Overload' for c in conflicts),
        "lab_mismatch": any(c['type'] == 'Lab Facility Mismatch' for c in conflicts)
    }

    return jsonify({
        "status": "success",
        "total_scheduled": len(entries),
        "conflicts_count": len(conflicts),
        "rule_statuses": rule_statuses,
        "conflicts": conflicts
    }), 200
