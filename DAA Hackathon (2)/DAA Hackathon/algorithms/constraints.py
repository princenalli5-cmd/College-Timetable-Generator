"""
Academic Scheduling Constraint Engine & Conflict Auditor
Validates hard and soft scheduling rules across faculty, classrooms, batches, and time.
"""

class ConstraintChecker:
    @staticmethod
    def is_slot_valid(session, slot, room, current_schedule, faculty_unavailability_set):
        """
        Fast incremental constraint validation for algorithms.
        Checks:
        1. Faculty not already teaching in this slot
        2. Classroom not already booked in this slot
        3. Student batch not already in class in this slot
        4. Faculty not unavailable/blocked in this slot
        5. Classroom capacity >= batch student strength
        6. Lab subject requires Lab classroom
        7. Max 2 sessions of the same subject per day for the batch
        """
        slot_day = slot['day']
        slot_period = slot['period']
        fac_id = session['faculty_id']
        batch_id = session['batch_id']
        room_id = room['id']
        sub_id = session['subject_id']

        # 1. Faculty availability check
        if (fac_id, slot_day, slot_period) in faculty_unavailability_set:
            return False, "Faculty unavailable during this time slot"

        # 2. Classroom type check (Lab sessions must be held in Lab rooms)
        if session.get('requires_lab', False):
            if room.get('room_type') != 'Lab':
                return False, "Lab sessions require a designated Computing/Practical Lab"
        else:
            # Prefer normal rooms for theory, though lab can be used if capacity matches
            pass

        # 3. Classroom capacity check
        if room.get('capacity', 0) < session.get('student_strength', 0):
            return False, f"Room capacity ({room.get('capacity')}) insufficient for batch strength ({session.get('student_strength')})"

        # 4. Check collisions against currently scheduled sessions
        daily_subject_count = 0
        for entry in current_schedule:
            e_day = entry['day']
            e_period = entry['period']

            if e_day == slot_day and e_period == slot_period:
                # Faculty double-booking
                if entry['faculty_id'] == fac_id:
                    return False, f"Faculty {session['faculty_name']} already scheduled in this slot"
                # Classroom double-booking
                if entry['classroom_id'] == room_id:
                    return False, f"Classroom {room['name']} already booked in this slot"
                # Student batch collision
                if entry['batch_id'] == batch_id:
                    return False, f"Batch {session['batch_name']} already has a class in this slot"

            # Check daily subject balance (max 2 per day)
            if e_day == slot_day and entry['batch_id'] == batch_id and entry['subject_id'] == sub_id:
                daily_subject_count += 1
                if daily_subject_count >= 2:
                    return False, f"Exceeded maximum 2 sessions of {session['subject_name']} per day"

        return True, "Valid Slot"

    @staticmethod
    def audit_full_schedule(schedule_entries, faculty_unavailability_set, classrooms_map):
        """
        Performs comprehensive conflict audit on the entire schedule.
        Returns a list of conflict objects with remedial recommendations.
        """
        conflicts = []
        n = len(schedule_entries)

        # 1. Pairwise collision checks (O(N^2) comprehensive analysis)
        for i in range(n):
            s1 = schedule_entries[i]
            for j in range(i + 1, n):
                s2 = schedule_entries[j]

                # If in the same day and period
                if s1['day'] == s2['day'] and s1['period'] == s2['period']:
                    # Faculty double-booking
                    if s1['faculty_id'] == s2['faculty_id']:
                        conflicts.append({
                            "type": "Faculty Double-Booking",
                            "severity": "Critical",
                            "subject": f"{s1.get('subject_name')} vs {s2.get('subject_name')}",
                            "faculty": s1.get('faculty_name'),
                            "classroom": f"{s1.get('classroom_name')} & {s2.get('classroom_name')}",
                            "day": s1['day'],
                            "period": s1['period'],
                            "suggested_correction": f"Reassign {s2.get('subject_name')} or faculty {s1.get('faculty_name')} to an alternate period."
                        })

                    # Classroom double-booking
                    if s1['classroom_id'] == s2['classroom_id']:
                        conflicts.append({
                            "type": "Classroom Double-Booking",
                            "severity": "Critical",
                            "subject": f"{s1.get('subject_name')} vs {s2.get('subject_name')}",
                            "faculty": f"{s1.get('faculty_name')} & {s2.get('faculty_name')}",
                            "classroom": s1.get('classroom_name'),
                            "day": s1['day'],
                            "period": s1['period'],
                            "suggested_correction": f"Move {s2.get('subject_name')} to an unoccupied classroom or another slot."
                        })

                    # Student batch timetable clash
                    if s1['batch_id'] == s2['batch_id']:
                        conflicts.append({
                            "type": "Student Batch Timetable Clash",
                            "severity": "Critical",
                            "subject": f"{s1.get('subject_name')} vs {s2.get('subject_name')}",
                            "faculty": f"{s1.get('faculty_name')} & {s2.get('faculty_name')}",
                            "classroom": f"{s1.get('classroom_name')} & {s2.get('classroom_name')}",
                            "day": s1['day'],
                            "period": s1['period'],
                            "suggested_correction": f"Reschedule {s2.get('subject_name')} to another free period for batch {s1.get('batch_name')}."
                        })

        # 2. Resource & availability checks
        for s in schedule_entries:
            fac_id = s.get('faculty_id')
            day = s.get('day')
            period = s.get('period')
            room_id = s.get('classroom_id')
            room = classrooms_map.get(room_id, {})

            # Faculty unavailable check
            if (fac_id, day, period) in faculty_unavailability_set:
                conflicts.append({
                    "type": "Faculty Unavailable Violation",
                    "severity": "High",
                    "subject": s.get('subject_name'),
                    "faculty": s.get('faculty_name'),
                    "classroom": s.get('classroom_name'),
                    "day": day,
                    "period": period,
                    "suggested_correction": f"{s.get('faculty_name')} is marked unavailable on {day} Period {period}. Move class to an active teaching hour."
                })

            # Classroom capacity check
            student_count = s.get('student_strength', 0)
            capacity = room.get('capacity', 0)
            if capacity > 0 and student_count > capacity:
                conflicts.append({
                    "type": "Classroom Capacity Overload",
                    "severity": "Medium",
                    "subject": s.get('subject_name'),
                    "faculty": s.get('faculty_name'),
                    "classroom": f"{room.get('name')} (Cap: {capacity})",
                    "day": day,
                    "period": period,
                    "suggested_correction": f"Batch strength ({student_count}) exceeds room capacity ({capacity}). Shift to a larger lecture hall."
                })

            # Lab room type mismatch
            is_lab = s.get('type') == 'Lab' or 'Lab' in str(s.get('subject_name', '')) or s.get('requires_lab')
            if is_lab and room.get('room_type') != 'Lab':
                conflicts.append({
                    "type": "Lab Facility Mismatch",
                    "severity": "High",
                    "subject": s.get('subject_name'),
                    "faculty": s.get('faculty_name'),
                    "classroom": f"{room.get('name')} ({room.get('room_type')})",
                    "day": day,
                    "period": period,
                    "suggested_correction": "Practical session assigned to normal classroom. Reassign to an equipped Computing/Practical Lab."
                })

        return conflicts
