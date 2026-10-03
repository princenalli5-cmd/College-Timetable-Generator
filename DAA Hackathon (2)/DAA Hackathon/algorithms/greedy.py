"""
Greedy Algorithm for College Timetable Scheduling
Selects the most constrained and highest priority classes first,
assigning each to the first locally optimal valid slot.
"""

import time
from algorithms.constraints import ConstraintChecker

class GreedyScheduler:
    def __init__(self, problem_data):
        self.sessions = problem_data["sessions"]
        self.classrooms = problem_data["classrooms"]
        self.time_slots = problem_data["time_slots"]
        self.unavailability = set(
            (u['faculty_id'], u['day'], u['period'])
            for u in problem_data.get("faculty_unavailability", [])
        )
        self.classrooms_map = {r['id']: r for r in self.classrooms}
        self.working_days = problem_data.get("working_days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"])
        self.day_order = {day: idx for idx, day in enumerate(self.working_days)}

        self.decision_count = 0
        self.step_trace = []
        self.schedule = []
        self.unscheduled = []

    def _get_candidate_slots(self, session, current_assignment):
        b_id = session.get("batch_id")
        day_counts = {d: 0 for d in self.working_days}
        period_counts = {p: 0 for p in range(1, 7)}
        for item in current_assignment:
            if item.get("batch_id") == b_id:
                day_counts[item["day"]] = day_counts.get(item["day"], 0) + 1
                period_counts[item["period"]] = period_counts.get(item["period"], 0) + 1

        return sorted(self.time_slots, key=lambda sl: (
            day_counts.get(sl["day"], 0),
            period_counts.get(sl["period"], 0),
            self.day_order.get(sl["day"], 99),
            sl["period"]
        ))

    def solve(self):
        start_time = time.perf_counter()

        # 1. Sort sessions greedily by constraint difficulty:
        # - Labs first (hardest room requirement)
        # - High priority subjects next
        # - Highest student strength (hardest capacity requirement)
        priority_map = {"High": 3, "Medium": 2, "Low": 1}
        sorted_sessions = sorted(
            self.sessions,
            key=lambda s: (
                1 if s.get("requires_lab") else 0,
                priority_map.get(s.get("priority", "Medium"), 1),
                s.get("student_strength", 0)
            ),
            reverse=True
        )

        current_assignment = []

        # 2. Iterate through sorted sessions and greedily pick best slot
        for session in sorted_sessions:
            assigned = False
            valid_rooms = [
                r for r in self.classrooms
                if (not session.get("requires_lab") or r["room_type"] == "Lab")
                and r["capacity"] >= session["student_strength"]
            ]

            if not valid_rooms:
                valid_rooms = [r for r in self.classrooms if r["capacity"] >= session["student_strength"]]

            candidate_slots = self._get_candidate_slots(session, current_assignment)
            for slot in candidate_slots:
                for room in valid_rooms:
                    self.decision_count += 1
                    is_valid, reason = ConstraintChecker.is_slot_valid(
                        session, slot, room, current_assignment, self.unavailability
                    )

                    if is_valid:
                        record = {
                            "session_code": session["session_code"],
                            "subject_id": session["subject_id"],
                            "subject_name": session["subject_name"],
                            "subject_code": session["subject_code"],
                            "subject_type": session["type"],
                            "faculty_id": session["faculty_id"],
                            "faculty_name": session["faculty_name"],
                            "classroom_id": room["id"],
                            "classroom_name": room["name"],
                            "classroom_type": room["room_type"],
                            "classroom_capacity": room["capacity"],
                            "batch_id": session["batch_id"],
                            "batch_name": session["batch_name"],
                            "student_strength": session["student_strength"],
                            "time_slot_id": slot["id"],
                            "day": slot["day"],
                            "period": slot["period"],
                            "start_time": slot["start_time"],
                            "end_time": slot["end_time"],
                            "color_hex": session.get("color_hex", "#315EAA")
                        }
                        current_assignment.append(record)
                        assigned = True

                        if len(self.step_trace) < 150:
                            self.step_trace.append({
                                "step": self.decision_count,
                                "session_code": session["session_code"],
                                "subject": session["subject_name"],
                                "batch": session["batch_name"],
                                "faculty": session["faculty_name"],
                                "room": room["name"],
                                "day": slot["day"],
                                "period": slot["period"],
                                "status": "Assigned"
                            })
                        break
                if assigned:
                    break

            if not assigned:
                self.unscheduled.append(session)
                if len(self.step_trace) < 150:
                    self.step_trace.append({
                        "step": self.decision_count,
                        "session_code": session["session_code"],
                        "subject": session["subject_name"],
                        "batch": session["batch_name"],
                        "faculty": session["faculty_name"],
                        "room": "None",
                        "day": "None",
                        "period": None,
                        "status": "Failed"
                    })

        end_time = time.perf_counter()
        execution_time_ms = round((end_time - start_time) * 1000, 2)
        self.schedule = current_assignment

        conflicts = ConstraintChecker.audit_full_schedule(
            self.schedule, self.unavailability, self.classrooms_map
        )

        return {
            "algorithm": "Greedy",
            "execution_time_ms": execution_time_ms,
            "scheduled_classes": len(self.schedule),
            "total_classes": len(self.sessions),
            "unscheduled_classes": len(self.unscheduled),
            "conflicts_count": len(conflicts),
            "backtracking_steps": 0,
            "decisions_count": self.decision_count,
            "success": len(self.unscheduled) == 0,
            "schedule": self.schedule,
            "step_trace": self.step_trace[:100]
        }
