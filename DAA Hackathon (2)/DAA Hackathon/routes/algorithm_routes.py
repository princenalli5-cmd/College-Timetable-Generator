from flask import Blueprint, request, jsonify, render_template
from database.db import query_db, get_scheduling_problem_data
from algorithms.comparison import AlgorithmComparator
from algorithms.graph_coloring import GraphColoringScheduler
from config import Config

algorithm_bp = Blueprint('algorithms', __name__)

@algorithm_bp.route('/comparison', methods=['GET'])
def comparison_page():
    return render_template('comparison.html', college_name=Config.COLLEGE_NAME)

@algorithm_bp.route('/api/compare-algorithms', methods=['POST'])
def compare_algorithms():
    data = request.get_json() or {}
    batch_ids = data.get('batch_ids')
    working_days = data.get('working_days', Config.DEFAULT_WORKING_DAYS)
    periods_per_day = int(data.get('periods_per_day', Config.DEFAULT_PERIODS_PER_DAY))

    problem_data = get_scheduling_problem_data(
        batch_ids=batch_ids,
        working_days=working_days,
        periods_per_day=periods_per_day
    )

    comparator = AlgorithmComparator(problem_data)
    comparison = comparator.run_all()

    return jsonify({
        "status": "success",
        "data": comparison
    }), 200

@algorithm_bp.route('/api/algorithm-logs', methods=['GET'])
def get_algorithm_logs():
    logs = query_db("SELECT * FROM algorithm_logs ORDER BY created_at DESC LIMIT 50")
    return jsonify({
        "status": "success",
        "count": len(logs),
        "data": logs
    }), 200

@algorithm_bp.route('/api/graph-data', methods=['GET'])
def get_graph_data():
    problem_data = get_scheduling_problem_data()
    gc = GraphColoringScheduler(problem_data)
    graph_data = gc.get_graph_data()
    return jsonify({
        "status": "success",
        "data": graph_data
    }), 200
