import copy
import datetime
import uuid
from typing import Dict, List, Optional

from .baseline import run_baseline
from .metrics import compute_metrics
from .scheduler import run_optimizer, validate_schedule

_preview_cache: Dict[str, Dict] = {}
PREVIEW_TTL_SECONDS = 300


def _clean_cache():
    now = datetime.datetime.utcnow()
    expired = [
        k for k, v in _preview_cache.items()
        if (now - v["created_at"]).total_seconds() > PREVIEW_TTL_SECONDS
    ]
    for k in expired:
        del _preview_cache[k]


def clear_preview_cache():
    _preview_cache.clear()


def preview_disruption(
    actions: List[Dict],
    current_state_version: int,
    patients: List[Dict],
    doctors: List[Dict],
    appointments: List[Dict],
    unavailabilities: List[Dict],
    current_minute: int,
    planning_horizon: int = 480,
) -> Dict:
    _clean_cache()

    before_metrics = compute_metrics(appointments, patients, doctors, unavailabilities, current_minute)

    mod_patients = copy.deepcopy(patients)
    mod_doctors = copy.deepcopy(doctors)
    mod_appointments = copy.deepcopy(appointments)
    mod_unavailabilities = copy.deepcopy(unavailabilities)

    for action in actions:
        atype = action.get("type") or action.get("action_type")

        if atype == "doctor_unavailable":
            did = action["doctor_id"]
            duration = action.get("duration_minutes", 60)
            mod_unavailabilities.append({
                "id": f"unav-preview-{uuid.uuid4().hex[:8]}",
                "doctor_id": did,
                "start_minute": current_minute,
                "end_minute": current_minute + duration,
                "reason": "Disruption",
            })

        elif atype == "doctor_available":
            did = action["doctor_id"]
            mod_unavailabilities = [
                u for u in mod_unavailabilities
                if not (u["doctor_id"] == did and u["end_minute"] > current_minute)
            ]

        elif atype == "add_emergency":
            count = action.get("count", 1)
            duration = action.get("duration_minutes", 20)
            specialty = action.get("required_specialty", "general")
            for _ in range(count):
                eid = f"P-EM-{uuid.uuid4().hex[:6]}"
                mod_patients.append({
                    "id": eid,
                    "name": "Emergency Patient",
                    "priority": "emergency",
                    "arrival_minute": current_minute,
                    "appointment_minute": None,
                    "service_duration_minutes": duration,
                    "required_specialty": specialty,
                    "status": "waiting",
                })

        elif atype == "cancel_appointment":
            appt_id = action.get("appointment_id")
            for a in mod_appointments:
                if a.get("id") == appt_id:
                    a["status"] = "cancelled"
                    for p in mod_patients:
                        if p["id"] == a["patient_id"]:
                            p["status"] = "waiting"

    opt_result = run_optimizer(
        current_minute, mod_patients, mod_doctors,
        mod_appointments, mod_unavailabilities, planning_horizon,
    )

    baseline_result = run_baseline(
        current_minute, mod_patients, mod_doctors,
        mod_appointments, mod_unavailabilities, planning_horizon,
    )

    after_metrics = compute_metrics(
        opt_result["schedule"], mod_patients, mod_doctors, mod_unavailabilities, current_minute
    )
    baseline_metrics = compute_metrics(
        baseline_result["schedule"], mod_patients, mod_doctors, mod_unavailabilities, current_minute
    )

    before_appt_map = {a["patient_id"]: a for a in appointments}
    after_appt_map = {a["patient_id"]: a for a in opt_result["schedule"]}
    affected = []
    for pid, after_a in after_appt_map.items():
        before_a = before_appt_map.get(pid)
        if (
            before_a is None
            or before_a.get("doctor_id") != after_a.get("doctor_id")
            or before_a.get("start_minute") != after_a.get("start_minute")
        ):
            affected.append(pid)

    preview_id = f"preview-{uuid.uuid4().hex[:12]}"
    _preview_cache[preview_id] = {
        "created_at": datetime.datetime.utcnow(),
        "state_version": current_state_version,
        "actions": actions,
        "mod_patients": mod_patients,
        "mod_doctors": mod_doctors,
        "mod_appointments": mod_appointments,
        "mod_unavailabilities": mod_unavailabilities,
        "opt_result": opt_result,
    }

    return {
        "preview_id": preview_id,
        "base_state_version": current_state_version,
        "solver_status": opt_result["solver_status"],
        "before_metrics": before_metrics,
        "after_metrics": after_metrics,
        "baseline_metrics": baseline_metrics,
        "proposed_appointments": opt_result["schedule"],
        "affected_patients": affected,
        "unscheduled_patients": opt_result["unscheduled_patients"],
    }


def get_preview(preview_id: str, expected_state_version: int) -> Optional[Dict]:
    _clean_cache()
    if preview_id not in _preview_cache:
        return None
    cached = _preview_cache[preview_id]
    if cached["state_version"] != expected_state_version:
        return None
    return cached
