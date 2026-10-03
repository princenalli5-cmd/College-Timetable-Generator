from flask import Blueprint, request, jsonify, render_template
from database.db import query_db, execute_db
from config import Config

classroom_bp = Blueprint('classrooms', __name__)

@classroom_bp.route('/classrooms', methods=['GET'])
def classrooms_page():
    return render_template('classrooms.html', college_name=Config.COLLEGE_NAME)

@classroom_bp.route('/api/classrooms', methods=['GET'])
def get_classrooms():
    rooms = query_db("SELECT * FROM classrooms ORDER BY name")
    for r in rooms:
        booked = query_db("SELECT COUNT(*) as c FROM timetable WHERE classroom_id = ?", (r['id'],), one=True)['c']
        r['booked_periods'] = booked
        r['utilization_pct'] = round((booked / 30.0) * 100, 1)
    return jsonify({"status": "success", "count": len(rooms), "data": rooms}), 200

@classroom_bp.route('/api/classrooms/<int:room_id>/schedule', methods=['GET'])
def get_classroom_schedule(room_id):
    room = query_db("SELECT * FROM classrooms WHERE id = ?", (room_id,), one=True)
    if not room:
        return jsonify({"status": "error", "message": "Classroom not found."}), 404

    sessions = query_db("""
        SELECT t.*, s.name as subject_name, s.code as subject_code, s.color_hex,
               f.name as faculty_name, b.name as batch_name
        FROM timetable t
        JOIN subjects s ON t.subject_id = s.id
        JOIN faculty f ON t.faculty_id = f.id
        JOIN student_batches b ON t.batch_id = b.id
        WHERE t.classroom_id = ?
        ORDER BY t.day, t.period
    """, (room_id,))

    return jsonify({
        "status": "success",
        "classroom": room,
        "schedule": sessions
    }), 200

@classroom_bp.route('/api/classrooms', methods=['POST'])
def create_classroom():
    data = request.get_json() or {}
    name = data.get('name', '').strip().upper()
    capacity = int(data.get('capacity', 60))
    room_type = data.get('room_type', 'Normal')
    building = data.get('building', 'Main Academic Block').strip()
    is_available = int(data.get('is_available', 1))

    if not name or capacity <= 0:
        return jsonify({"status": "error", "message": "Room name and positive capacity are required."}), 400

    try:
        last_id, _ = execute_db(
            "INSERT INTO classrooms (name, capacity, room_type, building, is_available) VALUES (?, ?, ?, ?, ?)",
            (name, capacity, room_type, building, is_available)
        )
        return jsonify({"status": "success", "id": last_id, "message": "Classroom added successfully."}), 201
    except Exception as e:
        return jsonify({"status": "error", "message": f"Classroom with name '{name}' already exists: {e}"}), 400

@classroom_bp.route('/api/classrooms/<int:room_id>', methods=['PUT'])
def update_classroom(room_id):
    data = request.get_json() or {}
    name = data.get('name', '').strip().upper()
    capacity = int(data.get('capacity', 60))
    room_type = data.get('room_type', 'Normal')
    building = data.get('building', 'Main Academic Block').strip()
    is_available = int(data.get('is_available', 1))

    if not name or capacity <= 0:
        return jsonify({"status": "error", "message": "Room name and positive capacity are required."}), 400

    try:
        _, rowcount = execute_db(
            "UPDATE classrooms SET name = ?, capacity = ?, room_type = ?, building = ?, is_available = ? WHERE id = ?",
            (name, capacity, room_type, building, is_available, room_id)
        )
        if rowcount == 0:
            return jsonify({"status": "error", "message": "Classroom not found."}), 404
        return jsonify({"status": "success", "message": "Classroom updated successfully."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@classroom_bp.route('/api/classrooms/<int:room_id>', methods=['DELETE'])
def delete_classroom(room_id):
    _, rowcount = execute_db("DELETE FROM classrooms WHERE id = ?", (room_id,))
    if rowcount == 0:
        return jsonify({"status": "error", "message": "Classroom not found."}), 404
    return jsonify({"status": "success", "message": "Classroom deleted successfully."}), 200
