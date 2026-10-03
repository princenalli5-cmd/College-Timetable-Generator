from flask import Blueprint, request, jsonify, render_template
from database.db import query_db, execute_db
from config import Config

subject_bp = Blueprint('subjects', __name__)

@subject_bp.route('/subjects', methods=['GET'])
def subjects_page():
    batches = query_db("SELECT * FROM student_batches ORDER BY name")
    faculty = query_db("SELECT * FROM faculty ORDER BY name")
    return render_template(
        'subjects.html',
        batches=batches,
        faculty=faculty,
        palette=Config.SUBJECT_COLOR_PALETTE,
        college_name=Config.COLLEGE_NAME
    )

@subject_bp.route('/api/subjects', methods=['GET'])
def get_subjects():
    query = """
        SELECT s.*, b.name as batch_name, b.student_strength, f.name as faculty_name, f.department as faculty_department
        FROM subjects s
        JOIN student_batches b ON s.batch_id = b.id
        JOIN faculty f ON s.faculty_id = f.id
        ORDER BY s.priority DESC, s.name ASC
    """
    subjects = query_db(query)
    return jsonify({"status": "success", "count": len(subjects), "data": subjects}), 200

@subject_bp.route('/api/subjects', methods=['POST'])
def create_subject():
    data = request.get_json() or {}
    code = data.get('code', '').strip().upper()
    name = data.get('name', '').strip()
    department = data.get('department', 'Computer Science & Engineering').strip()
    semester = int(data.get('semester', 5))
    subj_type = data.get('type', 'Theory')
    priority = data.get('priority', 'Medium')
    weekly_hours = int(data.get('weekly_hours', 3))
    practical_hours = int(data.get('practical_hours', 0))
    batch_id = data.get('batch_id')
    faculty_id = data.get('faculty_id')
    color_hex = data.get('color_hex', '#315EAA')

    if not code or not name or not batch_id or not faculty_id:
        return jsonify({"status": "error", "message": "Code, Name, Batch, and Faculty are required."}), 400

    try:
        last_id, _ = execute_db(
            """
            INSERT INTO subjects (code, name, department, semester, type, priority, weekly_hours, practical_hours, batch_id, faculty_id, color_hex)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (code, name, department, semester, subj_type, priority, weekly_hours, practical_hours, int(batch_id), int(faculty_id), color_hex)
        )
        return jsonify({"status": "success", "id": last_id, "message": "Subject created successfully."}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@subject_bp.route('/api/subjects/<int:subject_id>', methods=['PUT'])
def update_subject(subject_id):
    data = request.get_json() or {}
    code = data.get('code', '').strip().upper()
    name = data.get('name', '').strip()
    department = data.get('department', 'Computer Science & Engineering').strip()
    semester = int(data.get('semester', 5))
    subj_type = data.get('type', 'Theory')
    priority = data.get('priority', 'Medium')
    weekly_hours = int(data.get('weekly_hours', 3))
    practical_hours = int(data.get('practical_hours', 0))
    batch_id = data.get('batch_id')
    faculty_id = data.get('faculty_id')
    color_hex = data.get('color_hex', '#315EAA')

    if not code or not name or not batch_id or not faculty_id:
        return jsonify({"status": "error", "message": "Code, Name, Batch, and Faculty are required."}), 400

    try:
        _, rowcount = execute_db(
            """
            UPDATE subjects
            SET code = ?, name = ?, department = ?, semester = ?, type = ?, priority = ?, weekly_hours = ?,
                practical_hours = ?, batch_id = ?, faculty_id = ?, color_hex = ?
            WHERE id = ?
            """,
            (code, name, department, semester, subj_type, priority, weekly_hours, practical_hours, int(batch_id), int(faculty_id), color_hex, subject_id)
        )
        if rowcount == 0:
            return jsonify({"status": "error", "message": "Subject not found."}), 404
        return jsonify({"status": "success", "message": "Subject updated successfully."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@subject_bp.route('/api/subjects/<int:subject_id>', methods=['DELETE'])
def delete_subject(subject_id):
    _, rowcount = execute_db("DELETE FROM subjects WHERE id = ?", (subject_id,))
    if rowcount == 0:
        return jsonify({"status": "error", "message": "Subject not found."}), 404
    return jsonify({"status": "success", "message": "Subject deleted successfully."}), 200
