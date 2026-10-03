"""
Graph Coloring Algorithm for College Timetable Scheduling
Models sessions as vertices, mutual conflicts as edges, and time slots as colors.
Implements the Welsh-Powell heuristic to minimize chromatic number chi(G).
"""

import time
from algorithms.constraints import ConstraintChecker

class GraphColoringScheduler:
    def __init__(self, problem_data):
        self.sessions = problem_data["sessions"]
        self.classrooms = problem_data["classrooms"]
        self.time_slots = problem_data["time_slots"]
        self.unavailability = set(
            (u['faculty_id'], u['day'], u['period'])
            for u in problem_data.get("faculty_unavailability", [])
        )
        self.classrooms_map = {r['id']: r for r in self.classrooms}

        self.decision_count = 0
        self.step_trace = []
        self.schedule = []
        self.adjacency_list = {}
        self.vertex_degrees = {}
        self.edges = []

    def _build_conflict_graph(self):
        """Builds conflict graph G = (V, E) where edge indicates mutual scheduling clash."""
        self.adjacency_list = {s["session_id"]: set() for s in self.sessions}
        self.edges = []
        n = len(self.sessions)

        for i in range(n):
            s1 = self.sessions[i]
            for j in range(i + 1, n):
                s2 = self.sessions[j]
                has_conflict = False

                # Conflict 1: Shared faculty
                if s1["faculty_id"] == s2["faculty_id"]:
                    has_conflict = True

                # Conflict 2: Shared student batch
                if s1["batch_id"] == s2["batch_id"]:
                    has_conflict = True

                # Conflict 3: Both need scarce lab rooms
                if s1.get("requires_lab") and s2.get("requires_lab"):
                    lab_count = sum(1 for r in self.classrooms if r["room_type"] == "Lab")
                    if lab_count <= 2:
                        has_conflict = True

                if has_conflict:
                    self.adjacency_list[s1["session_id"]].add(s2["session_id"])
                    self.adjacency_list[s2["session_id"]].add(s1["session_id"])
                    self.edges.append({
                        "source": s1["session_id"],
                        "target": s2["session_id"]
                    })

        self.vertex_degrees = {v: len(neighbors) for v, neighbors in self.adjacency_list.items()}

    def solve(self):
        start_time = time.perf_counter()
        self._build_conflict_graph()

        # 1. Welsh-Powell: Sort vertices by degree in descending order
        sorted_vertex_ids = sorted(
            self.adjacency_list.keys(),
            key=lambda v: self.vertex_degrees[v],
            reverse=True
        )

        session_map = {s["session_id"]: s for s in self.sessions}
        color_assignments = {} # session_id -> color_index
        max_color = 0

        total_slots = len(self.time_slots)
        total_rooms = len(self.classrooms)
        lab_rooms = sum(1 for r in self.classrooms if r["room_type"] == "Lab")

        color_usage = {}

        # 2. Assign lowest valid color not shared by adjacent neighbors and respecting faculty availability
        for vid in sorted_vertex_ids:
            self.decision_count += 1
            session = session_map[vid]
            fac_id = session["faculty_id"]
            req_lab = session.get("requires_lab", False)

            neighbor_colors = {color_assignments[nbr] for nbr in self.adjacency_list[vid] if nbr in color_assignments}

            color = 0
            while True:
                if color in neighbor_colors:
                    color += 1
                    continue

                if color < total_slots:
                    slot = self.time_slots[color]
                    if (fac_id, slot["day"], slot["period"]) in self.unavailability:
                        color += 1
                        continue

                    usage = color_usage.get(color, {"count": 0, "lab_count": 0})
                    if usage["count"] >= total_rooms:
                        color += 1
                        continue
                    if req_lab and usage["lab_count"] >= lab_rooms:
                        color += 1
                        continue

                break

            color_assignments[vid] = color
            max_color = max(max_color, color)

            if color not in color_usage:
                color_usage[color] = {"count": 0, "lab_count": 0}
            color_usage[color]["count"] += 1
            if req_lab:
                color_usage[color]["lab_count"] += 1

        chromatic_number = max_color + 1

        # 3. Map colors to available physical time slots & assign rooms
        current_assignment = []
        unscheduled = []

        color_groups = {}
        for vid, col in color_assignments.items():
            if col not in color_groups:
                color_groups[col] = []
            color_groups[col].append(session_map[vid])

        total_available_slots = len(self.time_slots)

        for col, group in color_groups.items():
            if col < total_available_slots:
                slot = self.time_slots[col]
                used_room_ids = set()

                # Prioritize labs first within the color group
                sorted_group = sorted(group, key=lambda s: 1 if s.get("requires_lab") else 0, reverse=True)

                for session in sorted_group:
                    assigned_room = None
                    valid_rooms = [
                        r for r in self.classrooms
                        if (not session.get("requires_lab") or r["room_type"] == "Lab")
                        and r["capacity"] >= session["student_strength"]
                        and r["id"] not in used_room_ids
                    ]

                    if not valid_rooms:
                        valid_rooms = [
                            r for r in self.classrooms
                            if r["capacity"] >= session["student_strength"]
                            and r["id"] not in used_room_ids
                        ]

                    if valid_rooms:
                        assigned_room = valid_rooms[0]
                        used_room_ids.add(assigned_room["id"])

                    is_fac_avail = (session["faculty_id"], slot["day"], slot["period"]) not in self.unavailability

                    if assigned_room and is_fac_avail:
                        record = {
                            "session_code": session["session_code"],
                            "subject_id": session["subject_id"],
                            "subject_name": session["subject_name"],
                            "subject_code": session["subject_code"],
                            "subject_type": session["type"],
                            "faculty_id": session["faculty_id"],
                            "faculty_name": session["faculty_name"],
                            "classroom_id": assigned_room["id"],
                            "classroom_name": assigned_room["name"],
                            "classroom_type": assigned_room["room_type"],
                            "classroom_capacity": assigned_room["capacity"],
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
                    else:
                        unscheduled.append(session)
            else:
                unscheduled.extend(group)

        end_time = time.perf_counter()
        execution_time_ms = round((end_time - start_time) * 1000, 2)
        self.schedule = current_assignment

        conflicts = ConstraintChecker.audit_full_schedule(
            self.schedule, self.unavailability, self.classrooms_map
        )

        return {
            "algorithm": "Graph Coloring",
            "execution_time_ms": execution_time_ms,
            "scheduled_classes": len(self.schedule),
            "total_classes": len(self.sessions),
            "unscheduled_classes": len(unscheduled),
            "conflicts_count": len(conflicts),
            "backtracking_steps": 0,
            "decisions_count": self.decision_count,
            "chromatic_number": chromatic_number,
            "success": len(unscheduled) == 0 and len(conflicts) == 0,
            "schedule": self.schedule,
            "step_trace": self.step_trace[:100]
        }

    def get_graph_data(self):
        """Returns structured node-link data for HTML5 Canvas / network visualization."""
        if not self.adjacency_list:
            self._build_conflict_graph()

        color_assignments = {}
        sorted_vertex_ids = sorted(
            self.adjacency_list.keys(),
            key=lambda v: self.vertex_degrees[v],
            reverse=True
        )

        for vid in sorted_vertex_ids:
            neighbor_colors = {color_assignments[nbr] for nbr in self.adjacency_list[vid] if nbr in color_assignments}
            color = 0
            while color in neighbor_colors:
                color += 1
            color_assignments[vid] = color

        session_map = {s["session_id"]: s for s in self.sessions}
        vertices = []
        for vid, deg in self.vertex_degrees.items():
            s = session_map.get(vid, {})
            vertices.append({
                "id": vid,
                "label": s.get("session_code", f"S{vid}"),
                "code": s.get("subject_code", ""),
                "name": s.get("subject_name", ""),
                "batch": s.get("batch_name", ""),
                "faculty": s.get("faculty_name", ""),
                "color": color_assignments.get(vid, 0),
                "degree": deg
            })

        return {
            "vertex_count": len(vertices),
            "edge_count": len(self.edges),
            "chromatic_number": (max(color_assignments.values()) + 1) if color_assignments else 0,
            "vertices": vertices,
            "edges": self.edges
        }
