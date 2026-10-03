-- Smart College Timetable Generator Database Schema
-- Production SQLite Architecture

DROP TABLE IF EXISTS substitutions;
DROP TABLE IF EXISTS timetable;
DROP TABLE IF EXISTS algorithm_logs;
DROP TABLE IF EXISTS faculty_availability;
DROP TABLE IF EXISTS time_slots;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS classrooms;
DROP TABLE IF EXISTS faculty;
DROP TABLE IF EXISTS student_batches;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS system_settings;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    role TEXT DEFAULT 'Administrator',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE student_batches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    department TEXT NOT NULL,
    semester INTEGER NOT NULL,
    section TEXT NOT NULL DEFAULT 'A',
    student_strength INTEGER NOT NULL DEFAULT 45,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE faculty (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    email TEXT UNIQUE,
    designation TEXT DEFAULT 'Assistant Professor',
    max_hours_per_day INTEGER DEFAULT 4,
    max_hours_per_week INTEGER DEFAULT 18,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE classrooms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    building TEXT DEFAULT 'Main Academic Block',
    room_type TEXT NOT NULL CHECK(room_type IN ('Normal', 'Lab')),
    capacity INTEGER NOT NULL DEFAULT 60,
    is_available INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE subjects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    semester INTEGER NOT NULL DEFAULT 5,
    type TEXT NOT NULL CHECK(type IN ('Theory', 'Lab')),
    priority TEXT NOT NULL DEFAULT 'Medium' CHECK(priority IN ('High', 'Medium', 'Low')),
    weekly_hours INTEGER NOT NULL DEFAULT 3,
    practical_hours INTEGER NOT NULL DEFAULT 0,
    batch_id INTEGER NOT NULL,
    faculty_id INTEGER NOT NULL,
    color_hex TEXT DEFAULT '#315EAA',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (batch_id) REFERENCES student_batches(id) ON DELETE CASCADE,
    FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE
);

CREATE TABLE faculty_availability (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    faculty_id INTEGER NOT NULL,
    day TEXT NOT NULL,
    period INTEGER NOT NULL,
    is_available INTEGER NOT NULL DEFAULT 1,
    reason TEXT DEFAULT '',
    FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE,
    UNIQUE(faculty_id, day, period)
);

CREATE TABLE time_slots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    day TEXT NOT NULL,
    period INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    is_break INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    UNIQUE(day, period)
);

CREATE TABLE timetable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_code TEXT NOT NULL,
    subject_id INTEGER NOT NULL,
    faculty_id INTEGER NOT NULL,
    classroom_id INTEGER NOT NULL,
    batch_id INTEGER NOT NULL,
    time_slot_id INTEGER NOT NULL,
    day TEXT NOT NULL,
    period INTEGER NOT NULL,
    algorithm_used TEXT DEFAULT 'Backtracking',
    is_locked INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
    FOREIGN KEY (faculty_id) REFERENCES faculty(id) ON DELETE CASCADE,
    FOREIGN KEY (classroom_id) REFERENCES classrooms(id) ON DELETE CASCADE,
    FOREIGN KEY (batch_id) REFERENCES student_batches(id) ON DELETE CASCADE,
    FOREIGN KEY (time_slot_id) REFERENCES time_slots(id) ON DELETE CASCADE
);

CREATE TABLE substitutions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timetable_id INTEGER NOT NULL,
    original_faculty_id INTEGER NOT NULL,
    substitute_faculty_id INTEGER NOT NULL,
    day TEXT NOT NULL,
    period INTEGER NOT NULL,
    reason TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'Approved' CHECK(status IN ('Approved', 'Pending', 'Rejected')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (timetable_id) REFERENCES timetable(id) ON DELETE CASCADE,
    FOREIGN KEY (original_faculty_id) REFERENCES faculty(id) ON DELETE CASCADE,
    FOREIGN KEY (substitute_faculty_id) REFERENCES faculty(id) ON DELETE CASCADE
);

CREATE TABLE algorithm_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    algorithm_name TEXT NOT NULL,
    execution_time_ms REAL NOT NULL,
    scheduled_classes INTEGER NOT NULL,
    unscheduled_classes INTEGER NOT NULL,
    conflicts_count INTEGER NOT NULL,
    backtracking_steps INTEGER NOT NULL,
    decisions_count INTEGER NOT NULL,
    success_status INTEGER NOT NULL,
    metrics_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE system_settings (
    setting_key TEXT PRIMARY KEY,
    setting_value TEXT NOT NULL
);

-- Indices for rapid constraint checking and filtering
CREATE INDEX idx_timetable_day_period ON timetable(day, period);
CREATE INDEX idx_timetable_batch ON timetable(batch_id);
CREATE INDEX idx_timetable_faculty ON timetable(faculty_id);
CREATE INDEX idx_timetable_classroom ON timetable(classroom_id);
CREATE INDEX idx_faculty_avail ON faculty_availability(faculty_id, day, period);
