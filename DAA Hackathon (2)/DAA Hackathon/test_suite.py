"""
Comprehensive Automated Test Suite for Smart College Timetable Generator
Validates 6 Core Academic Constraints, DAA Algorithms, Substitution Engine, and API endpoints.
"""

import sys
import os
import unittest
import copy

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from database.db import get_scheduling_problem_data
from algorithms.constraints import ConstraintChecker
from algorithms.backtracking import BacktrackingScheduler
from algorithms.greedy import GreedyScheduler
from algorithms.graph_coloring import GraphColoringScheduler
from algorithms.hybrid import HybridScheduler
from algorithms.comparison import AlgorithmComparator
from app import app

class TestConstraintsAndAlgorithms(unittest.TestCase):
    def setUp(self):
        self.problem_data = get_scheduling_problem_data(batch_ids=[1, 2, 3])
        self.classrooms_map = {r["id"]: r for r in self.problem_data["classrooms"]}
        self.faculty_unavail = set(
            (u["faculty_id"], u["day"], u["period"])
            for u in self.problem_data["faculty_unavailability"]
        )

    def test_faculty_double_booking_detection(self):
        """Rule 1: Detect same faculty assigned to two classes simultaneously."""
        schedule = [
            {
                "session_code": "CS501-1",
                "subject_id": 1,
                "subject_name": "DAA",
                "faculty_id": 1,
                "faculty_name": "Dr. Alan Turing",
                "classroom_id": 1,
                "classroom_name": "LH-101",
                "classroom_type": "Normal",
                "classroom_capacity": 65,
                "batch_id": 1,
                "batch_name": "CSE-3A",
                "student_strength": 45,
                "day": "Monday",
                "period": 2
            },
            {
                "session_code": "CS501-2",
                "subject_id": 1,
                "subject_name": "DAA",
                "faculty_id": 1,  # Same faculty
                "faculty_name": "Dr. Alan Turing",
                "classroom_id": 2,
                "classroom_name": "LH-102",
                "classroom_type": "Normal",
                "classroom_capacity": 60,
                "batch_id": 2,
                "batch_name": "CSE-3B",
                "student_strength": 42,
                "day": "Monday",
                "period": 2  # Same slot
            }
        ]
        conflicts = ConstraintChecker.audit_full_schedule(schedule, self.faculty_unavail, self.classrooms_map)
        self.assertTrue(any("Faculty Double-Booking" in c["type"] for c in conflicts))

    def test_classroom_double_booking_detection(self):
        """Rule 2: Detect same classroom assigned to two classes simultaneously."""
        schedule = [
            {
                "session_code": "CS501-1",
                "subject_id": 1,
                "subject_name": "DAA",
                "faculty_id": 1,
                "classroom_id": 1,
                "classroom_name": "LH-101",
                "batch_id": 1,
                "day": "Tuesday",
                "period": 3
            },
            {
                "session_code": "AI501-1",
                "subject_id": 12,
                "subject_name": "ML",
                "faculty_id": 5,
                "classroom_id": 1,  # Same room LH-101
                "classroom_name": "LH-101",
                "batch_id": 3,
                "day": "Tuesday",
                "period": 3  # Same slot
            }
        ]
        conflicts = ConstraintChecker.audit_full_schedule(schedule, self.faculty_unavail, self.classrooms_map)
        self.assertTrue(any("Classroom Double-Booking" in c["type"] for c in conflicts))

    def test_batch_clash_detection(self):
        """Rule 3: Detect same student batch assigned to two classes simultaneously."""
        schedule = [
            {
                "session_code": "CS501-1",
                "subject_id": 1,
                "subject_name": "DAA",
                "faculty_id": 1,
                "classroom_id": 1,
                "batch_id": 1,
                "batch_name": "CSE-3A",
                "day": "Wednesday",
                "period": 1
            },
            {
                "session_code": "CS502-1",
                "subject_id": 3,
                "subject_name": "OS",
                "faculty_id": 2,
                "classroom_id": 2,
                "batch_id": 1,  # Same batch CSE-3A
                "batch_name": "CSE-3A",
                "day": "Wednesday",
                "period": 1  # Same slot
            }
        ]
        conflicts = ConstraintChecker.audit_full_schedule(schedule, self.faculty_unavail, self.classrooms_map)
        self.assertTrue(any("Batch Timetable Clash" in c["type"] for c in conflicts))

    def test_faculty_unavailability_detection(self):
        """Rule 4: Detect class assigned during faculty blocked hours."""
        # Turing is blocked on Monday period 1
        schedule = [
            {
                "session_code": "CS501-1",
                "subject_id": 1,
                "subject_name": "DAA",
                "faculty_id": 1,
                "classroom_id": 1,
                "batch_id": 1,
                "day": "Monday",
                "period": 1
            }
        ]
        unavail = {(1, "Monday", 1)}
        conflicts = ConstraintChecker.audit_full_schedule(schedule, unavail, self.classrooms_map)
        self.assertTrue(any("Faculty Unavailable" in c["type"] for c in conflicts))

    def test_classroom_capacity_detection(self):
        """Rule 5: Detect student batch exceeding room capacity."""
        schedule = [
            {
                "session_code": "CS501-1",
                "subject_name": "DAA",
                "faculty_id": 1,
                "classroom_id": 99,
                "batch_id": 1,
                "student_strength": 50,
                "day": "Friday",
                "period": 1
            }
        ]
        rooms = {99: {"id": 99, "name": "Tiny-Hall", "capacity": 25, "room_type": "Normal"}}
        conflicts = ConstraintChecker.audit_full_schedule(schedule, set(), rooms)
        self.assertTrue(any("Capacity" in c["type"] for c in conflicts))

    def test_lab_room_type_detection(self):
        """Rule 6: Detect lab class assigned to a normal lecture hall."""
        schedule = [
            {
                "session_code": "CS501P-1",
                "subject_name": "DAA Computing Lab",
                "type": "Lab",
                "requires_lab": True,
                "faculty_id": 1,
                "classroom_id": 1,
                "batch_id": 1,
                "day": "Monday",
                "period": 3
            }
        ]
        conflicts = ConstraintChecker.audit_full_schedule(schedule, set(), self.classrooms_map)
        self.assertTrue(any("Lab Facility Mismatch" in c["type"] for c in conflicts))

    def test_backtracking_solver(self):
        """Verify Backtracking generates a conflict-free schedule."""
        solver = BacktrackingScheduler(self.problem_data)
        res = solver.solve()
        self.assertTrue(res["success"])
        self.assertEqual(res["conflicts_count"], 0)
        self.assertEqual(res["scheduled_classes"], res["total_classes"])

    def test_greedy_solver(self):
        """Verify Greedy algorithm executes and produces schedule."""
        solver = GreedyScheduler(self.problem_data)
        res = solver.solve()
        self.assertGreater(res["scheduled_classes"], 0)
        self.assertEqual(res["conflicts_count"], 0)

    def test_graph_coloring_solver(self):
        """Verify Welsh-Powell Graph Coloring builds conflict graph & colors validly."""
        solver = GraphColoringScheduler(self.problem_data)
        res = solver.solve()
        self.assertTrue(res["success"])
        self.assertGreater(res["chromatic_number"], 0)
        self.assertEqual(res["conflicts_count"], 0)

    def test_hybrid_solver(self):
        """Verify Hybrid scheduler combines Greedy seeds with Backtracking."""
        solver = HybridScheduler(self.problem_data)
        res = solver.solve()
        self.assertTrue(res["success"])
        self.assertEqual(res["conflicts_count"], 0)

    def test_comparator_suite(self):
        """Verify unified benchmark runner compares all 4 algorithms."""
        comparator = AlgorithmComparator(self.problem_data)
        res = comparator.run_all()
        self.assertIn("backtracking", res)
        self.assertIn("greedy", res)
        self.assertIn("graph_coloring", res)
        self.assertIn("hybrid", res)

    def test_flask_api_endpoints(self):
        """Test Flask HTTP routes return 200 OK."""
        client = app.test_client()

        # Web pages
        self.assertEqual(client.get('/dashboard').status_code, 200)
        self.assertEqual(client.get('/timetable').status_code, 200)
        self.assertEqual(client.get('/generate').status_code, 200)
        self.assertEqual(client.get('/subjects').status_code, 200)
        self.assertEqual(client.get('/faculty').status_code, 200)
        self.assertEqual(client.get('/classrooms').status_code, 200)
        self.assertEqual(client.get('/batches').status_code, 200)
        self.assertEqual(client.get('/availability').status_code, 200)
        self.assertEqual(client.get('/substitution').status_code, 200)
        self.assertEqual(client.get('/conflicts').status_code, 200)
        self.assertEqual(client.get('/comparison').status_code, 200)
        self.assertEqual(client.get('/reports').status_code, 200)
        self.assertEqual(client.get('/settings').status_code, 200)

        # REST APIs
        self.assertEqual(client.get('/api/dashboard-stats').status_code, 200)
        self.assertEqual(client.get('/api/subjects').status_code, 200)
        self.assertEqual(client.get('/api/faculty').status_code, 200)
        self.assertEqual(client.get('/api/classrooms').status_code, 200)
        self.assertEqual(client.get('/api/batches').status_code, 200)
        self.assertEqual(client.get('/api/conflicts').status_code, 200)
        self.assertEqual(client.get('/api/graph-data').status_code, 200)

if __name__ == '__main__':
    unittest.main(verbosity=2)
