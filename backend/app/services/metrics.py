import statistics
from typing import Any, Dict, List


def compute_metrics(
    appointments: List[Dict],
    patients: List[Dict],
    doctors: List[Dict],
    unavailabilities: List[Dict],
    current_minute: int = 0,
) -> Dict:
    patient_map = {p["id"]: p for p in patients}

    waits = []
    waits_by_priority: Dict[str, List[float]] = {"emergency": [], "urgent": [], "normal": []}
    scheduled_pids = set()

    active_appts = [a for a in appointments if a.get("status") != "cancelled"]

    for appt in active_appts:
        pid = appt["patient_id"]
        p = patient_map.get(pid)
        if not p:
            continue
        scheduled_pids.add(pid)
        wait = max(0, appt["start_minute"] - p["arrival_minute"])
        waits.append(wait)
        prio = p.get("priority", "normal")
        if prio in waits_by_priority:
            waits_by_priority[prio].append(wait)

    unscheduled_pids = set()
    for p in patients:
        if p["status"] in ("waiting", "unscheduled") and p["id"] not in scheduled_pids:
            unscheduled_pids.add(p["id"])

    avg_wait = statistics.mean(waits) if waits else 0
    median_wait = statistics.median(waits) if waits else 0
    max_wait = max(waits) if waits else 0

    avg_by_priority = {
        prio: (statistics.mean(w) if w else 0)
        for prio, w in waits_by_priority.items()
    }

    unav_by_doc: Dict[str, List] = {}
    for u in unavailabilities:
        unav_by_doc.setdefault(u["doctor_id"], []).append((u["start_minute"], u["end_minute"]))

    doc_utilization = {}
    for d in doctors:
        did = d["id"]
        shift_minutes = d["shift_end_minute"] - d["shift_start_minute"]
        unav_minutes = sum(
            min(e, d["shift_end_minute"]) - max(s, d["shift_start_minute"])
            for s, e in unav_by_doc.get(did, [])
            if s < d["shift_end_minute"] and e > d["shift_start_minute"]
        )
        available = max(1, shift_minutes - unav_minutes)
        busy = sum(
            a["end_minute"] - a["start_minute"]
            for a in active_appts
            if a["doctor_id"] == did
        )
        doc_utilization[did] = round(min(100.0, busy / available * 100), 1)

    return {
        "avg_wait": round(avg_wait, 1),
        "median_wait": round(median_wait, 1),
        "max_wait": round(max_wait, 1),
        "avg_wait_by_priority": avg_by_priority,
        "scheduled_count": len(scheduled_pids),
        "unscheduled_count": len(unscheduled_pids),
        "doctor_utilization": doc_utilization,
        "total_patients": len(patients),
    }
