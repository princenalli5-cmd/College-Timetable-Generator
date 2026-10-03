from flask import Blueprint, render_template, jsonify, request
from database.db import query_db
from config import Config

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def root():
    return render_template('dashboard.html', college_name=Config.COLLEGE_NAME, academic_year=Config.CURRENT_ACADEMIC_YEAR)

@dashboard_bp.route('/dashboard')
def dashboard_view():
    return render_template('dashboard.html', college_name=Config.COLLEGE_NAME, academic_year=Config.CURRENT_ACADEMIC_YEAR)

@dashboard_bp.route('/api/dashboard-stats', methods=['GET'])
def get_dashboard_stats():
    """Returns commercial-grade statistics, utilization, workload, and activity feeds."""
    # 1. Total counts
    total_subjects = query_db("SELECT COUNT(*) as c FROM subjects", one=True)['c']
    total_faculty = query_db("SELECT COUNT(*) as c FROM faculty", one=True)['c']
    total_classrooms = query_db("SELECT COUNT(*) as c FROM classrooms WHERE is_available = 1", one=True)['c']
    total_batches = query_db("SELECT COUNT(*) as c FROM student_batches", one=True)['c']
    scheduled_classes = query_db("SELECT COUNT(*) as c FROM timetable", one=True)['c']

    # Total expected lecture and lab hours across all subjects
    expected_hours = query_db("SELECT SUM(weekly_hours + practical_hours) as s FROM subjects", one=True)['s'] or 0
    unscheduled_classes = max(0, expected_hours - scheduled_classes)

    # 2. Latest generation log
    latest_log = query_db("SELECT * FROM algorithm_logs ORDER BY created_at DESC LIMIT 1", one=True)
    generation_status = "Generated" if scheduled_classes > 0 else "Pending"
    last_algorithm = latest_log['algorithm_name'] if latest_log else "None"
    conflicts_count = latest_log['conflicts_count'] if latest_log else 0

    # 3. Room Utilization (Chart data)
    # Rooms vs number of booked periods
    room_util = query_db("""
        SELECT c.name, c.room_type, c.capacity, COUNT(t.id) as booked_periods
        FROM classrooms c
        LEFT JOIN timetable t ON c.id = t.classroom_id
        GROUP BY c.id
        ORDER BY c.name
    """)
    # Max possible slots per room = 5 days * 6 periods = 30 slots
    room_labels = [r['name'] for r in room_util]
    room_util_pct = [round((r['booked_periods'] / 30.0) * 100, 1) for r in room_util]

    # 4. Faculty Workload (Teaching hours)
    fac_workload = query_db("""
        SELECT f.name, f.max_hours_per_week, COUNT(t.id) as scheduled_hours
        FROM faculty f
        LEFT JOIN timetable t ON f.id = t.faculty_id
        GROUP BY f.id
        ORDER BY f.name
    """)
    fac_labels = [f['name'].split()[-1] for f in fac_workload] # last name for clean chart
    fac_hours = [f['scheduled_hours'] for f in fac_workload]
    fac_max = [f['max_hours_per_week'] for f in fac_workload]

    # 5. Weekly Scheduling Overview (Classes by Day)
    days_order = Config.DEFAULT_WORKING_DAYS
    day_counts_map = {d: 0 for d in days_order}
    day_rows = query_db("SELECT day, COUNT(*) as c FROM timetable GROUP BY day")
    for r in day_rows:
        if r['day'] in day_counts_map:
            day_counts_map[r['day']] = r['c']

    # 6. Recent Activities Feed
    recent_classes = query_db("""
        SELECT t.id, t.session_code, s.name as subject_name, s.code as subject_code,
               f.name as faculty_name, c.name as classroom_name,
               b.name as batch_name, t.day, t.period, t.algorithm_used
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN faculty f ON t.faculty_id = f.id
        JOIN classrooms c ON t.classroom_id = c.id
        JOIN student_batches b ON t.batch_id = b.id
        ORDER BY t.id DESC LIMIT 6
    """)

    return jsonify({
        "status": "success",
        "data": {
            "total_subjects": total_subjects,
            "total_faculty": total_faculty,
            "total_classrooms": total_classrooms,
            "total_batches": total_batches,
            "scheduled_classes": scheduled_classes,
            "unscheduled_classes": unscheduled_classes,
            "generation_status": generation_status,
            "last_algorithm": last_algorithm,
            "conflicts_count": conflicts_count,
            "charts": {
                "room_utilization": {
                    "labels": room_labels,
                    "utilization_pct": room_util_pct
                },
                "faculty_workload": {
                    "labels": fac_labels,
                    "scheduled": fac_hours,
                    "max_hours": fac_max
                },
                "weekly_overview": {
                    "labels": days_order,
                    "counts": [day_counts_map[d] for d in days_order]
                }
            },
            "recent_activities": recent_classes
        }
    }), 200
