import sqlite3
import os
import sys
from flask import g, has_app_context

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config

_standalone_conn = None

def get_db():
    if has_app_context():
        if 'db' not in g:
            os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
            g.db = sqlite3.connect(
                Config.DATABASE_PATH,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON;")
        return g.db
    else:
        global _standalone_conn
        if _standalone_conn is None:
            os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
            _standalone_conn = sqlite3.connect(
                Config.DATABASE_PATH,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            _standalone_conn.row_factory = sqlite3.Row
            _standalone_conn.execute("PRAGMA foreign_keys = ON;")
        return _standalone_conn

def close_db(e=None):
    if has_app_context():
        db = g.pop('db', None)
        if db is not None:
            db.close()
    else:
        global _standalone_conn
        if _standalone_conn is not None:
            _standalone_conn.close()
            _standalone_conn = None

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = [dict(row) for row in cur.fetchall()]
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    last_id = cur.lastrowid
    rowcount = cur.rowcount
    cur.close()
    return last_id, rowcount

def init_db():
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database initialized successfully at:", Config.DATABASE_PATH)

def get_scheduling_problem_data(batch_ids=None, working_days=None, periods_per_day=None):
    """
    Extracts all active database entities and breaks courses down into discrete
    allocatable class sessions (each theory hour and practical lab block).
    """
    if working_days is None:
        working_days = Config.DEFAULT_WORKING_DAYS
    if periods_per_day is None:
        periods_per_day = Config.DEFAULT_PERIODS_PER_DAY

    # Fetch batches
    if batch_ids:
        placeholders = ','.join('?' for _ in batch_ids)
        batches = query_db(f"SELECT * FROM student_batches WHERE id IN ({placeholders}) ORDER BY id", batch_ids)
    else:
        batches = query_db("SELECT * FROM student_batches ORDER BY id")

    batches_map = {b['id']: b for b in batches}
    selected_batch_ids = list(batches_map.keys())

    if not selected_batch_ids:
        return {
            "sessions": [],
            "batches": [],
            "faculty": [],
            "classrooms": [],
            "time_slots": [],
            "faculty_unavailability": [],
            "working_days": working_days,
            "periods_per_day": periods_per_day
        }

    # Fetch subjects assigned to these batches
    placeholders = ','.join('?' for _ in selected_batch_ids)
    subjects = query_db(
        f"""
        SELECT s.*, b.name as batch_name, b.student_strength, f.name as faculty_name
        FROM subjects s
        JOIN student_batches b ON s.batch_id = b.id
        JOIN faculty f ON s.faculty_id = f.id
        WHERE s.batch_id IN ({placeholders})
        ORDER BY s.priority DESC, s.type DESC, s.id ASC
        """,
        selected_batch_ids
    )

    # Fetch faculty
    faculty = query_db("SELECT * FROM faculty ORDER BY id")

    # Fetch classrooms
    classrooms = query_db("SELECT * FROM classrooms WHERE is_available = 1 ORDER BY capacity DESC")

    # Fetch active time slots
    day_placeholders = ','.join('?' for _ in working_days)
    time_slots = query_db(
        f"""
        SELECT * FROM time_slots
        WHERE day IN ({day_placeholders}) AND period <= ? AND is_break = 0 AND is_active = 1
        """,
        working_days + [periods_per_day]
    )
    # Balanced dispersion across all working days and periods (Latin square pattern)
    # Guarantees even distribution across Monday-Saturday and Periods 1-6
    day_order_map = {day: idx for idx, day in enumerate(working_days)}
    num_days = max(1, len(working_days))
    num_periods = max(1, periods_per_day)

    def slot_dispersion_rank(slot):
        d_idx = day_order_map.get(slot['day'], 0)
        p_idx = (slot['period'] - 1) % num_periods
        return ((p_idx - d_idx) % num_days) * num_days + d_idx

    time_slots.sort(key=slot_dispersion_rank)

    # Fetch faculty unavailability
    faculty_unavailability = query_db(
        "SELECT faculty_id, day, period FROM faculty_availability WHERE is_available = 0"
    )

    # Decompose subjects into individual 1-hour sessions
    sessions = []
    session_counter = 1

    for sub in subjects:
        # 1. Weekly Theory Lectures (each 1 hour)
        for h in range(1, sub['weekly_hours'] + 1):
            sessions.append({
                "session_id": session_counter,
                "session_code": f"{sub['code']}-L{h}",
                "subject_id": sub['id'],
                "subject_name": sub['name'],
                "subject_code": sub['code'],
                "type": "Theory",
                "priority": sub['priority'],
                "batch_id": sub['batch_id'],
                "batch_name": sub['batch_name'],
                "student_strength": sub['student_strength'],
                "faculty_id": sub['faculty_id'],
                "faculty_name": sub['faculty_name'],
                "color_hex": sub.get('color_hex', '#315EAA'),
                "requires_lab": False,
                "session_number": h
            })
            session_counter += 1

        # 2. Practical Labs
        for p in range(1, sub['practical_hours'] + 1):
            sessions.append({
                "session_id": session_counter,
                "session_code": f"{sub['code']}-P{p}",
                "subject_id": sub['id'],
                "subject_name": f"{sub['name']} Lab",
                "subject_code": f"{sub['code']}P",
                "type": "Lab",
                "priority": "High",
                "batch_id": sub['batch_id'],
                "batch_name": sub['batch_name'],
                "student_strength": sub['student_strength'],
                "faculty_id": sub['faculty_id'],
                "faculty_name": sub['faculty_name'],
                "color_hex": sub.get('color_hex', '#19B6B1'),
                "requires_lab": True,
                "session_number": p
            })
            session_counter += 1

    return {
        "sessions": sessions,
        "batches": batches,
        "faculty": faculty,
        "classrooms": classrooms,
        "time_slots": time_slots,
        "faculty_unavailability": faculty_unavailability,
        "working_days": working_days,
        "periods_per_day": periods_per_day
    }
