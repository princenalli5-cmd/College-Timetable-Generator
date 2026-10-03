import os
from flask import Flask, redirect, url_for
from config import Config
from database.db import init_db, close_db
from routes.dashboard_routes import dashboard_bp
from routes.timetable_routes import timetable_bp
from routes.faculty_routes import faculty_bp
from routes.classroom_routes import classroom_bp
from routes.batch_routes import batch_bp
from routes.subject_routes import subject_bp
from routes.substitution_routes import substitution_bp
from routes.conflict_routes import conflict_bp
from routes.algorithm_routes import algorithm_bp
from routes.report_routes import report_bp

app = Flask(__name__)
app.config.from_object(Config)

# Register Teardown Hook
app.teardown_appcontext(close_db)

# Register Blueprints
app.register_blueprint(dashboard_bp)
app.register_blueprint(timetable_bp)
app.register_blueprint(faculty_bp)
app.register_blueprint(classroom_bp)
app.register_blueprint(batch_bp)
app.register_blueprint(subject_bp)
app.register_blueprint(substitution_bp)
app.register_blueprint(conflict_bp)
app.register_blueprint(algorithm_bp)
app.register_blueprint(report_bp)

# Auto-initialize database schema and seed data if not present
if not os.path.exists(Config.DATABASE_PATH):
    print("Database not found. Initializing schema and seed data...")
    init_db()
    from database.seed import seed_database
    seed_database()

if __name__ == '__main__':
    print("==========================================================================")
    print(" Starting Smart College Timetable Generator (SaaS DAA Edition)")
    print(f" Institution: {Config.COLLEGE_NAME}")
    print(" Web URL: http://127.0.0.1:5000")
    print("==========================================================================")
    app.run(host='127.0.0.1', port=5000, debug=True)
