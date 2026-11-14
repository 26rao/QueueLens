"""
QueueLens CP-SAT Scheduling Engine
"""
import time
from collections import defaultdict
from typing import List, Optional

from ortools.sat.python import cp_model

PRIORITY_WEIGHTS = {"emergency": 100, "urgent": 10, "normal": 1}
UNSCHEDULED_PENALTY = 10000
CHANGE_PENALTY = 2
LATENESS_PENALTY = 3
AGING_COEFFICIENT = 0.1
AGING_THRESHOLD_MINUTES = 30


def run_optimizer(
    current_minute: int,
    patients: list,
    doctors: list,
    existing_appointments: list,
    unavailabilities: list,
    planning_horizon: int = 480,
    previous_schedule: list = None,
) -> dict:
    start_time = time.time()

    model = cp_model.CpModel()

    locked_appt_ids = {
        a["id"] for a in existing_appointments if a.get("status") in ("in_progress", "completed")
    }
    locked_patient_ids = {
        a["patient_id"] for a in existing_appointments if a.get("status") in ("in_progress", "completed")
    }

    schedulable_patients = [
        p for p in patients
        if p["status"] not in ("completed", "cancelled", "in_progress")
        and p["id"] not in locked_patient_ids
    ]

    active_doctors = [d for d in doctors if d["active"]]

    intervals_per_doctor = {d["id"]: [] for d in active_doctors}
    patient_assignments = {}

    horizon = planning_horizon

    for p in schedulable_patients:
        pid = p["id"]
        duration = p["service_duration_minutes"]
        earliest_start = max(p["arrival_minute"], current_minute)

        waiting_minutes = max(0, current_minute - p["arrival_minute"])
        aging_bonus = AGING_COEFFICIENT * max(0, waiting_minutes - AGING_THRESHOLD_MINUTES)
        base_weight = PRIORITY_WEIGHTS.get(p["priority"], 1)
        effective_weight = int(base_weight + aging_bonus)

        is_scheduled = model.NewBoolVar(f"sched_{pid}")

        eligible_doctors = [
            d for d in active_doctors if p["required_specialty"] in d["specialties"]
        ]

        if not eligible_doctors:
            patient_assignments[pid] = {
                "is_scheduled": is_scheduled,
                "assignments": [],
                "weight": effective_weight,
                "patient": p,
            }
            model.Add(is_scheduled == 0)
            continue

        # Guard: if duration >= horizon, can't schedule
        if earliest_start + duration > horizon:
            patient_assignments[pid] = {
                "is_scheduled": is_scheduled,
                "assignments": [],
                "weight": effective_weight,
                "patient": p,
            }
            model.Add(is_scheduled == 0)
            continue

        assignments = []
        for d in eligible_doctors:
            did = d["id"]
            s_lo = max(earliest_start, d["shift_start_minute"])
            s_hi = min(horizon - duration, d["shift_end_minute"] - duration)
            if s_lo > s_hi:
                continue

            start = model.NewIntVar(s_lo, s_hi, f"start_{pid}_{did}")
            end = model.NewIntVar(s_lo + duration, s_hi + duration, f"end_{pid}_{did}")
            is_assigned = model.NewBoolVar(f"assign_{pid}_{did}")
            interval = model.NewOptionalIntervalVar(start, duration, end, is_assigned, f"iv_{pid}_{did}")

            model.Add(start >= d["shift_start_minute"]).OnlyEnforceIf(is_assigned)
            model.Add(end <= d["shift_end_minute"]).OnlyEnforceIf(is_assigned)

            intervals_per_doctor[did].append(interval)
            assignments.append({
                "doctor_id": did,
                "start_var": start,
                "end_var": end,
                "is_assigned": is_assigned,
                "interval": interval,
            })

        assign_vars = [a["is_assigned"] for a in assignments]
        if assign_vars:
            model.Add(sum(assign_vars) <= 1)
            model.Add(sum(assign_vars) == is_scheduled)
        else:
            model.Add(is_scheduled == 0)

        patient_assignments[pid] = {
            "is_scheduled": is_scheduled,
            "assignments": assignments,
            "weight": effective_weight,
            "patient": p,
        }

    for did, intervals in intervals_per_doctor.items():
        if intervals:
            model.AddNoOverlap(intervals)

    # Unavailability constraints
    # Build lookup: doctor_id -> list of assignment dicts
    assignments_by_doctor = defaultdict(list)
    for pdata in patient_assignments.values():
        for a in pdata.get("assignments", []):
            assignments_by_doctor[a["doctor_id"]].append(a)

    for unav in unavailabilities:
        did = unav["doctor_id"]
        for a_data in assignments_by_doctor.get(did, []):
            is_assigned = a_data["is_assigned"]
            start_var = a_data["start_var"]
            end_var = a_data["end_var"]
            unav_id = unav.get("id", "u")
            before = model.NewBoolVar(f"bef_{unav_id}_{id(a_data)}")
            after = model.NewBoolVar(f"aft_{unav_id}_{id(a_data)}")
            model.Add(end_var <= unav["start_minute"]).OnlyEnforceIf(before)
            model.Add(start_var >= unav["end_minute"]).OnlyEnforceIf(after)
            model.AddBoolOr([before, after, is_assigned.Not()])

    # Objective
    wait_terms = []
    unscheduled_terms = []
    change_terms = []

    prev_lookup = {}
    if previous_schedule:
        for a in previous_schedule:
            prev_lookup[a.get("patient_id")] = a.get("start_minute", 0)

    for pid, pdata in patient_assignments.items():
        p = pdata["patient"]
        w = pdata["weight"]
        is_sched = pdata["is_scheduled"]

        unscheduled_terms.append(UNSCHEDULED_PENALTY * (1 - is_sched))

        for a in pdata.get("assignments", []):
            is_assigned = a["is_assigned"]
            start_var = a["start_var"]

            wait = model.NewIntVar(0, horizon, f"wait_{pid}_{a['doctor_id']}")
            model.Add(wait == start_var - p["arrival_minute"]).OnlyEnforceIf(is_assigned)
            model.Add(wait == 0).OnlyEnforceIf(is_assigned.Not())
            wait_terms.append(w * wait)

            if pid in prev_lookup:
                prev_start = prev_lookup[pid]
                diff = model.NewIntVar(-horizon, horizon, f"diff_{pid}_{a['doctor_id']}")
                abs_diff = model.NewIntVar(0, horizon, f"absdiff_{pid}_{a['doctor_id']}")
                model.Add(diff == start_var - prev_start).OnlyEnforceIf(is_assigned)
                model.Add(diff == 0).OnlyEnforceIf(is_assigned.Not())
                model.AddAbsEquality(abs_diff, diff)
                change_terms.append(CHANGE_PENALTY * abs_diff)

    objective_terms = wait_terms + unscheduled_terms + change_terms
    if objective_terms:
        model.Minimize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 2.0
    solver.parameters.num_search_workers = 4

    status = solver.Solve(model)
    exec_time = (time.time() - start_time) * 1000

    status_map = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.UNKNOWN: "UNKNOWN",
    }
    status_str = status_map.get(status, "UNKNOWN")

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        new_appointments = []
        unscheduled = []

        for a in existing_appointments:
            if a.get("id") in locked_appt_ids:
                new_appointments.append(a)

        for pid, pdata in patient_assignments.items():
            if solver.Value(pdata["is_scheduled"]) == 1:
                for a in pdata.get("assignments", []):
                    if solver.Value(a["is_assigned"]) == 1:
                        new_appointments.append({
                            "patient_id": pid,
                            "doctor_id": a["doctor_id"],
                            "start_minute": solver.Value(a["start_var"]),
                            "end_minute": solver.Value(a["end_var"]),
                            "status": "scheduled",
                        })
                        break
            else:
                unscheduled.append(pid)

        obj_val = solver.ObjectiveValue()

        return {
            "solver_status": status_str,
            "schedule": new_appointments,
            "unscheduled_patients": unscheduled,
            "objective_value": obj_val,
            "execution_time_ms": exec_time,
        }
    else:
        return run_fallback(
            current_minute, patients, doctors, existing_appointments,
            unavailabilities, planning_horizon, exec_time,
        )


def run_fallback(
    current_minute,
    patients,
    doctors,
    existing_appointments,
    unavailabilities,
    planning_horizon,
    prior_time_ms=0,
):
    """Priority-first FCFS fallback scheduler."""
    start_time = time.time()

    locked_appt_ids = {
        a.get("id") for a in existing_appointments
        if a.get("status") in ("in_progress", "completed")
    }
    locked_patient_ids = {
        a["patient_id"] for a in existing_appointments
        if a.get("status") in ("in_progress", "completed")
    }

    priority_order = {"emergency": 0, "urgent": 1, "normal": 2}
    schedulable = [
        p for p in patients
        if p["status"] not in ("completed", "cancelled", "in_progress")
        and p["id"] not in locked_patient_ids
    ]
    schedulable.sort(key=lambda p: (priority_order.get(p["priority"], 2), p["arrival_minute"]))

    active_doctors = [d for d in doctors if d["active"]]

    doctor_busy_until = {
        d["id"]: max(d["shift_start_minute"], current_minute) for d in active_doctors
    }

    unav_by_doc = {}
    for u in unavailabilities:
        unav_by_doc.setdefault(u["doctor_id"], []).append((u["start_minute"], u["end_minute"]))

    new_appointments = [a for a in existing_appointments if a.get("id") in locked_appt_ids]
    unscheduled = []

    for p in schedulable:
        earliest = max(p["arrival_minute"], current_minute)
        eligible = [d for d in active_doctors if p["required_specialty"] in d["specialties"]]

        best_start = None
        best_doctor = None

        for d in eligible:
            did = d["id"]
            candidate = max(earliest, doctor_busy_until.get(did, current_minute))
            duration = p["service_duration_minutes"]

            if candidate + duration > d["shift_end_minute"] or candidate >= planning_horizon:
                continue

            # Push past unavailability windows
            for unav_start, unav_end in unav_by_doc.get(did, []):
                if candidate < unav_end and candidate + duration > unav_start:
                    candidate = max(candidate, unav_end)

            if candidate + duration > d["shift_end_minute"] or candidate >= planning_horizon:
                continue

            if best_start is None or candidate < best_start:
                best_start = candidate
                best_doctor = d

        if best_doctor:
            end = best_start + p["service_duration_minutes"]
            new_appointments.append({
                "patient_id": p["id"],
                "doctor_id": best_doctor["id"],
                "start_minute": best_start,
                "end_minute": end,
                "status": "scheduled",
            })
            doctor_busy_until[best_doctor["id"]] = end
        else:
            unscheduled.append(p["id"])

    exec_time = prior_time_ms + (time.time() - start_time) * 1000
    return {
        "solver_status": "FALLBACK",
        "schedule": new_appointments,
        "unscheduled_patients": unscheduled,
        "objective_value": None,
        "execution_time_ms": exec_time,
    }


def validate_schedule(appointments, doctors, patients, unavailabilities):
    """Validate a schedule. Raises ValueError if invalid. Returns True if valid."""
    doctor_map = {d["id"]: d for d in doctors}
    patient_map = {p["id"]: p for p in patients}

    by_doctor = defaultdict(list)
    seen_patients = set()

    for appt in appointments:
        if appt.get("status") == "cancelled":
            continue
        pid = appt["patient_id"]
        did = appt["doctor_id"]
        start = appt["start_minute"]
        end = appt["end_minute"]

        if end <= start:
            raise ValueError(f"Appointment {appt.get('id', '?')} has end <= start")

        if pid in seen_patients:
            raise ValueError(f"Patient {pid} has duplicate active appointments")
        seen_patients.add(pid)

        if did not in doctor_map:
            raise ValueError(f"Unknown doctor {did}")
        d = doctor_map[did]

        if p := patient_map.get(pid):
            if p["required_specialty"] not in d["specialties"]:
                raise ValueError(f"Doctor {did} lacks specialty for patient {pid}")

        if start < d["shift_start_minute"] or end > d["shift_end_minute"]:
            raise ValueError(f"Appointment for {pid} outside doctor {did} shift")

        by_doctor[did].append((start, end, pid))

    for did, intervals in by_doctor.items():
        intervals.sort()
        for i in range(len(intervals) - 1):
            if intervals[i][1] > intervals[i + 1][0]:
                raise ValueError(
                    f"Overlapping appointments for doctor {did}: {intervals[i][2]} and {intervals[i+1][2]}"
                )

    unav_by_doc = {}
    for u in unavailabilities:
        unav_by_doc.setdefault(u["doctor_id"], []).append((u["start_minute"], u["end_minute"]))

    for appt in appointments:
        if appt.get("status") in ("cancelled", "completed", "in_progress"):
            continue
        did = appt["doctor_id"]
        start = appt["start_minute"]
        end = appt["end_minute"]
        for unav_start, unav_end in unav_by_doc.get(did, []):
            if start < unav_end and end > unav_start:
                raise ValueError(
                    f"Appointment {appt.get('id', '?')} conflicts with doctor {did} unavailability"
                )

    return True
