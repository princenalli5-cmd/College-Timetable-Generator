from flask import Blueprint, request, jsonify, render_template
from database.db import query_db, execute_db
from config import Config

batch_bp = Blueprint('batches', __name__)

@batch_bp.route('/batches', methods=['GET'])
def batches_page():
    return render_template('batches.html', college_name=Config.COLLEGE_NAME)

@batch_bp.route('/api/batches', methods=['GET'])
def get_batches():
    batches = query_db("SELECT * FROM student_batches ORDER BY name")
    for b in batches:
        subjects = query_db(
            """
            SELECT s.id, s.code, s.name, s.weekly_hours, s.practical_hours, s.type, f.name as faculty_name
            FROM subjects s
            JOIN faculty f ON s.faculty_id = f.id
            WHERE s.batch_id = ?
            """,
            (b['id'],)
        )
        b['subjects'] = subjects
        b['total_weekly_hours'] = sum(s['weekly_hours'] + s['practical_hours'] for s in subjects)
    return jsonify({"status": "success", "count": len(batches), "data": batches}), 200

@batch_bp.route('/api/batches', methods=['POST'])
def create_batch():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    department = data.get('department', '').strip()
    semester = int(data.get('semester', 1))
    section = data.get('section', 'A').strip().upper()
    student_strength = int(data.get('student_strength', 45))

    if not name or not department:
        return jsonify({"status": "error", "message": "Batch Name and Department are required."}), 400

    try:
        last_id, _ = execute_db(
            "INSERT INTO student_batches (name, department, semester, section, student_strength) VALUES (?, ?, ?, ?, ?)",
            (name, department, semester, section, student_strength)
        )
        return jsonify({"status": "success", "id": last_id, "message": "Student batch created successfully."}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": f"Batch '{name}' already exists: {e}"}), 400

@batch_bp.route('/api/batches/<int:batch_id>', methods=['PUT'])
def update_batch(batch_id):
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    department = data.get('department', '').strip()
    semester = int(data.get('semester', 1))
    section = data.get('section', 'A').strip().upper()
    student_strength = int(data.get('student_strength', 45))

    if not name or not department:
        return jsonify({"status": "error", "message": "Batch Name and Department are required."}), 400

    try:
        _, rowcount = execute_db(
            "UPDATE student_batches SET name = ?, department = ?, semester = ?, section = ?, student_strength = ? WHERE id = ?",
            (name, department, semester, section, student_strength, batch_id)
        )
        if rowcount == 0:
            return jsonify({"status": "error", "message": "Batch not found."}), 404
        return jsonify({"status": "success", "message": "Student batch updated successfully."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@batch_bp.route('/api/batches/<int:batch_id>', methods=['DELETE'])
def delete_batch(batch_id):
    _, rowcount = execute_db("DELETE FROM student_batches WHERE id = ?", (batch_id,))
    if rowcount == 0:
        return jsonify({"status": "error", "message": "Batch not found."}), 404
    return jsonify({"status": "success", "message": "Student batch deleted successfully."}), 200
