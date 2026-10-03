from flask import Blueprint, render_template, jsonify, request, Response
from database.db import query_db
from config import Config
import io
import csv

report_bp = Blueprint('reports', __name__)

@report_bp.route('/reports', methods=['GET'])
def reports_page():
    return render_template('reports.html', college_name=Config.COLLEGE_NAME)

@report_bp.route('/settings', methods=['GET'])
def settings_page():
    settings_rows = query_db("SELECT * FROM system_settings")
    settings = {r['setting_key']: r['setting_value'] for r in settings_rows}
    return render_template(
        'settings.html',
        settings=settings,
        college_name=Config.COLLEGE_NAME,
        academic_year=Config.CURRENT_ACADEMIC_YEAR
    )

@report_bp.route('/api/reports/faculty-workload', methods=['GET'])
def get_workload_report():
    data = query_db("""
        SELECT f.name as faculty_name, f.department, f.designation, f.max_hours_per_week,
               COUNT(t.id) as scheduled_hours,
               GROUP_CONCAT(DISTINCT s.code) as subjects_taught
        FROM faculty f
        LEFT JOIN timetable t ON f.id = t.faculty_id
        LEFT JOIN subjects s ON t.subject_id = s.id
        GROUP BY f.id
        ORDER BY f.department, f.name
    """)
    for d in data:
        max_h = d['max_hours_per_week'] or 16
        d['utilization_pct'] = round((d['scheduled_hours'] / max_h) * 100, 1)
        d['is_overloaded'] = d['scheduled_hours'] > max_h
    return jsonify({"status": "success", "data": data}), 200

@report_bp.route('/api/reports/room-utilization', methods=['GET'])
def get_room_utilization_report():
    data = query_db("""
        SELECT c.name as room_name, c.building, c.room_type, c.capacity,
               COUNT(t.id) as scheduled_periods,
               COUNT(DISTINCT t.day) as active_days
        FROM classrooms c
        LEFT JOIN timetable t ON c.id = t.classroom_id
        GROUP BY c.id
        ORDER BY c.name
    """)
    for d in data:
        d['utilization_pct'] = round((d['scheduled_periods'] / 30.0) * 100, 1)
    return jsonify({"status": "success", "data": data}), 200

@report_bp.route('/api/reports/export-csv/<report_type>', methods=['GET'])
def export_csv(report_type):
    output = io.StringIO()
    writer = csv.writer(output)

    if report_type == 'timetable':
        rows = query_db("""
            SELECT t.session_code, s.code, s.name, s.type, f.name as faculty,
                   c.name as room, b.name as batch, t.day, t.period, ts.start_time, ts.end_time
            FROM timetable t
            JOIN subjects s ON t.subject_id = s.id
            JOIN faculty f ON t.faculty_id = f.id
            JOIN classrooms c ON t.classroom_id = c.id
            JOIN student_batches b ON t.batch_id = b.id
            JOIN time_slots ts ON t.time_slot_id = ts.id
            ORDER BY t.day, t.period
        """)
        writer.writerow(['Session Code', 'Course Code', 'Course Name', 'Type', 'Faculty', 'Classroom', 'Batch', 'Day', 'Period', 'Start Time', 'End Time'])
        for r in rows:
            writer.writerow([r['session_code'], r['code'], r['name'], r['type'], r['faculty'], r['room'], r['batch'], r['day'], r['period'], r['start_time'], r['end_time']])
        filename = "college_full_timetable.csv"

    elif report_type == 'faculty_workload':
        rows = query_db("""
            SELECT f.name, f.department, f.designation, f.max_hours_per_week, COUNT(t.id) as scheduled
            FROM faculty f
            LEFT JOIN timetable t ON f.id = t.faculty_id
            GROUP BY f.id
            ORDER BY f.name
        """)
        writer.writerow(['Faculty Name', 'Department', 'Designation', 'Max Hours/Week', 'Scheduled Hours'])
        for r in rows:
            writer.writerow([r['name'], r['department'], r['designation'], r['max_hours_per_week'], r['scheduled']])
        filename = "faculty_workload_report.csv"

    else:
        rows = query_db("SELECT * FROM classrooms")
        writer.writerow(['Room Name', 'Building', 'Type', 'Capacity'])
        for r in rows:
            writer.writerow([r['name'], r['building'], r['room_type'], r['capacity']])
        filename = "classrooms_report.csv"

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )
