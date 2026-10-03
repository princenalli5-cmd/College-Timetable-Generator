import sqlite3
import os
import sys

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config
from database.db import init_db

def seed_database():
    init_db()
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cur = conn.cursor()

    # 1. Admin User
    cur.execute(
        """
        INSERT INTO users (username, password_hash, full_name, email, role)
        VALUES (?, ?, ?, ?, ?)
        """,
        ('admin', 'pbkdf2:sha256:mock_hash_for_demo', 'Dr. Robert Vance', 'admin@aist.edu', 'Chief Academic Officer')
    )

    # 2. Student Batches
    batches_data = [
        ('CSE-3A', 'Computer Science & Engineering', 5, 'A', 45),
        ('CSE-3B', 'Computer Science & Engineering', 5, 'B', 42),
        ('AIDS-3A', 'Artificial Intelligence & Data Science', 5, 'A', 48)
    ]
    cur.executemany(
        """
        INSERT INTO student_batches (name, department, semester, section, student_strength)
        VALUES (?, ?, ?, ?, ?)
        """,
        batches_data
    )

    # 3. Faculty Members
    faculty_data = [
        ('Dr. Alan Turing', 'Computer Science & Engineering', 'turing@aist.edu', 'Professor & Head', 4, 16),
        ('Dr. Grace Hopper', 'Computer Science & Engineering', 'hopper@aist.edu', 'Professor', 4, 16),
        ('Dr. Claude Shannon', 'Computer Science & Engineering', 'shannon@aist.edu', 'Associate Professor', 4, 16),
        ('Prof. Ada Lovelace', 'Computer Science & Engineering', 'lovelace@aist.edu', 'Assistant Professor', 4, 18),
        ('Dr. John von Neumann', 'Artificial Intelligence & Data Science', 'neumann@aist.edu', 'Professor & Chair', 4, 16),
        ('Dr. Geoffrey Hinton', 'Artificial Intelligence & Data Science', 'hinton@aist.edu', 'Associate Professor', 4, 16),
        ('Prof. Margaret Hamilton', 'Artificial Intelligence & Data Science', 'hamilton@aist.edu', 'Assistant Professor', 4, 18)
    ]
    cur.executemany(
        """
        INSERT INTO faculty (name, department, email, designation, max_hours_per_day, max_hours_per_week)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        faculty_data
    )

    # 4. Classrooms & Labs
    classroom_data = [
        ('LH-101', 'Main Academic Block', 'Normal', 65, 1),
        ('LH-102', 'Main Academic Block', 'Normal', 60, 1),
        ('LH-201', 'Main Academic Block', 'Normal', 60, 1),
        ('LH-202', 'Main Academic Block', 'Normal', 55, 1),
        ('CS-LAB-1', 'Computing & Informatics Wing', 'Lab', 60, 1),
        ('AI-LAB-2', 'Computing & Informatics Wing', 'Lab', 55, 1)
    ]
    cur.executemany(
        """
        INSERT INTO classrooms (name, building, room_type, capacity, is_available)
        VALUES (?, ?, ?, ?, ?)
        """,
        classroom_data
    )

    # 5. Time Slots (5 Working Days x 6 Periods + Recess)
    days = Config.DEFAULT_WORKING_DAYS
    slots_data = []
    for day in days:
        for p_info in Config.PERIOD_TIMINGS:
            if not p_info["is_break"]:
                slots_data.append((
                    day,
                    p_info["period"],
                    p_info["start_time"],
                    p_info["end_time"],
                    0,
                    1
                ))
    cur.executemany(
        """
        INSERT INTO time_slots (day, period, start_time, end_time, is_break, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        slots_data
    )

    # 6. Academic Subjects
    # Palette colors:
    # 0: #315EAA, 1: #19B6B1, 2: #20A477, 3: #E6A23C, 4: #8B5CF6, 5: #EC4899, 6: #0EA5E9, 7: #6366F1
    subjects_data = [
        # Batch 1: CSE-3A (Sem 5)
        ('CS501', 'Design & Analysis of Algorithms', 'Computer Science & Engineering', 5, 'Theory', 'High', 3, 0, 1, 1, '#315EAA'),
        ('CS501P', 'DAA Computing Lab', 'Computer Science & Engineering', 5, 'Lab', 'High', 0, 2, 1, 1, '#19B6B1'),
        ('CS502', 'Operating Systems', 'Computer Science & Engineering', 5, 'Theory', 'High', 3, 0, 1, 2, '#20A477'),
        ('CS503', 'Database Management Systems', 'Computer Science & Engineering', 5, 'Theory', 'Medium', 3, 0, 1, 3, '#8B5CF6'),
        ('CS503P', 'DBMS Practical Lab', 'Computer Science & Engineering', 5, 'Lab', 'High', 0, 2, 1, 3, '#19B6B1'),
        ('CS504', 'Computer Networks', 'Computer Science & Engineering', 5, 'Theory', 'Medium', 3, 0, 1, 4, '#0EA5E9'),

        # Batch 2: CSE-3B (Sem 5)
        ('CS501', 'Design & Analysis of Algorithms', 'Computer Science & Engineering', 5, 'Theory', 'High', 3, 0, 2, 1, '#315EAA'),
        ('CS501P', 'DAA Computing Lab', 'Computer Science & Engineering', 5, 'Lab', 'High', 0, 2, 2, 1, '#19B6B1'),
        ('CS502', 'Operating Systems', 'Computer Science & Engineering', 5, 'Theory', 'High', 3, 0, 2, 2, '#20A477'),
        ('CS503', 'Database Management Systems', 'Computer Science & Engineering', 5, 'Theory', 'Medium', 3, 0, 2, 3, '#8B5CF6'),
        ('CS504', 'Computer Networks', 'Computer Science & Engineering', 5, 'Theory', 'Medium', 3, 0, 2, 4, '#0EA5E9'),

        # Batch 3: AIDS-3A (Sem 5)
        ('AI501', 'Machine Learning Foundations', 'Artificial Intelligence & Data Science', 5, 'Theory', 'High', 3, 0, 3, 5, '#E6A23C'),
        ('AI501P', 'Machine Learning Applied Lab', 'Artificial Intelligence & Data Science', 5, 'Lab', 'High', 0, 2, 3, 5, '#19B6B1'),
        ('AI502', 'Deep Learning & Neural Nets', 'Artificial Intelligence & Data Science', 5, 'Theory', 'High', 3, 0, 3, 6, '#EC4899'),
        ('AI503', 'Big Data Analytics', 'Artificial Intelligence & Data Science', 5, 'Theory', 'Medium', 3, 0, 3, 7, '#6366F1'),
        ('AI503P', 'Big Data Computing Lab', 'Artificial Intelligence & Data Science', 5, 'Lab', 'High', 0, 2, 3, 7, '#19B6B1'),
        ('AI504', 'Natural Language Processing', 'Artificial Intelligence & Data Science', 5, 'Theory', 'Medium', 3, 0, 3, 6, '#0EA5E9'),
    ]
    cur.executemany(
        """
        INSERT INTO subjects (code, name, department, semester, type, priority, weekly_hours, practical_hours, batch_id, faculty_id, color_hex)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        subjects_data
    )

    # 7. Faculty Unavailability (Blocked periods)
    # Turing (id 1) blocked Monday P1
    # Hopper (id 2) blocked Tuesday P3
    # Shannon (id 3) blocked Wednesday P4
    # Neumann (id 5) blocked Thursday P2
    cur.executemany(
        """
        INSERT INTO faculty_availability (faculty_id, day, period, is_available, reason)
        VALUES (?, ?, ?, ?, ?)
        """,
        [
            (1, 'Monday', 1, 0, 'Department Academic Council Meeting'),
            (2, 'Tuesday', 3, 0, 'Grant Research & Faculty Development'),
            (3, 'Wednesday', 4, 0, 'Cyber Infrastructure Inspection'),
            (5, 'Thursday', 2, 0, 'Dean Advisory Panel Session')
        ]
    )

    # 8. System Settings
    cur.executemany(
        """
        INSERT INTO system_settings (setting_key, setting_value)
        VALUES (?, ?)
        """,
        [
            ('academic_year', Config.CURRENT_ACADEMIC_YEAR),
            ('semester', Config.CURRENT_SEMESTER),
            ('college_name', Config.COLLEGE_NAME),
            ('theme_mode', 'light')
        ]
    )

    conn.commit()
    conn.close()
    print("Database seeded with sample academic data successfully.")
    
    # Pre-generate full conflict-free college timetable
    from algorithms.hybrid import HybridScheduler
    from database.db import get_scheduling_problem_data, execute_db
    problem_data = get_scheduling_problem_data(working_days=Config.DEFAULT_WORKING_DAYS)
    solver = HybridScheduler(problem_data)
    result = solver.solve()
    if result.get("schedule"):
        execute_db("DELETE FROM timetable")
        for item in result["schedule"]:
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
        print(f"Generated full college timetable with {len(result['schedule'])} sessions across all batches.")

if __name__ == '__main__':
    seed_database()
