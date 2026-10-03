import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-college-timetable-saa-secret-2026')
    DATABASE_PATH = os.path.join(BASE_DIR, 'database', 'timetable.db')
    
    COLLEGE_NAME = "Apex Institute of Science & Technology"
    COLLEGE_ACRONYM = "AIST"
    CURRENT_ACADEMIC_YEAR = "2025 - 2026"
    CURRENT_SEMESTER = "Odd Semester (Fall 2025)"
    
    DEFAULT_WORKING_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    DEFAULT_PERIODS_PER_DAY = 6
    
    PERIOD_TIMINGS = [
        {"period": 1, "start_time": "09:00", "end_time": "10:00", "is_break": False, "label": "Period 1"},
        {"period": 2, "start_time": "10:00", "end_time": "11:00", "is_break": False, "label": "Period 2"},
        {"period": 3, "start_time": "11:15", "end_time": "12:15", "is_break": False, "label": "Period 3"},
        {"period": 4, "start_time": "12:15", "end_time": "13:15", "is_break": False, "label": "Period 4"},
        {"period": 0, "start_time": "13:15", "end_time": "14:00", "is_break": True, "label": "Lunch Recess", "short_label": "LUNCH"},
        {"period": 5, "start_time": "14:00", "end_time": "15:00", "is_break": False, "label": "Period 5"},
        {"period": 6, "start_time": "15:00", "end_time": "16:00", "is_break": False, "label": "Period 6"},
    ]

    SUBJECT_COLOR_PALETTE = [
        {"bg": "#EBF2FD", "border": "#315EAA", "text": "#1E3A8A"},
        {"bg": "#E6FAF8", "border": "#19B6B1", "text": "#0F766E"},
        {"bg": "#E8F8F2", "border": "#20A477", "text": "#065F46"},
        {"bg": "#FEF7EB", "border": "#E6A23C", "text": "#9A3412"},
        {"bg": "#F3EFFC", "border": "#8B5CF6", "text": "#5B21B6"},
        {"bg": "#FDF2F8", "border": "#EC4899", "text": "#9D174D"},
        {"bg": "#F0F9FF", "border": "#0EA5E9", "text": "#075985"},
        {"bg": "#EEF2FF", "border": "#6366F1", "text": "#3730A3"}
    ]
