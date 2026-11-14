"""
Deterministic Synthetic Hospital Event Generator.
Produces structured events for hospital operations (arrivals, emergencies, doctor status).
"""
import random
from typing import List, Dict, Any, Optional

MAX_SYNTHETIC_PATIENTS = 60

# Predictable schedule of events for live demonstration
SCHEDULED_ARRIVALS = [
    {"minute": 5, "priority": "normal", "specialty": "general", "duration": 20},
    {"minute": 12, "priority": "normal", "specialty": "cardiology", "duration": 15},
    {"minute": 20, "priority": "urgent", "specialty": "general", "duration": 25},
    {"minute": 30, "priority": "normal", "specialty": "orthopedics", "duration": 20},
    {"minute": 40, "priority": "emergency", "specialty": "general", "duration": 20},
    {"minute": 55, "priority": "normal", "specialty": "general", "duration": 15},
    {"minute": 70, "priority": "urgent", "specialty": "cardiology", "duration": 25},
    {"minute": 85, "priority": "normal", "specialty": "orthopedics", "duration": 30},
    {"minute": 100, "priority": "normal", "specialty": "general", "duration": 20},
    {"minute": 115, "priority": "emergency", "specialty": "cardiology", "duration": 25},
    {"minute": 130, "priority": "normal", "specialty": "general", "duration": 15},
    {"minute": 150, "priority": "urgent", "specialty": "orthopedics", "duration": 20},
]

# Deterministic judge replay scenario:
# Min 0: Normal operations
# Min 10: Dr. Rao unavailable for 60 min
# Min 15: Two emergency arrivals
# Min 70: Dr. Rao returns, queue recalculated
REPLAY_SCHEDULE = [
    {
        "minute": 10,
        "id": "EV-REP-UNAV-D1",
        "event_type": "doctor_unavailability",
        "description": "Dr. Rao unavailable for 60 min (Emergency consultation)",
        "payload_json": {
            "doctor_id": "D1",
            "start_minute": 10,
            "end_minute": 70,
            "reason": "Emergency consultation",
        },
    },
    {
        "minute": 15,
        "id": "EV-REP-EM-01",
        "event_type": "emergency_arrival",
        "description": "🚨 Emergency patient P-REP-01 arrived (General)",
        "payload_json": {
            "patient_id": "P-REP-01",
            "name": "Patient P-REP-01",
            "priority": "emergency",
            "arrival_minute": 15,
            "service_duration_minutes": 20,
            "required_specialty": "general",
            "status": "waiting",
        },
    },
    {
        "minute": 15,
        "id": "EV-REP-EM-02",
        "event_type": "emergency_arrival",
        "description": "🚨 Emergency patient P-REP-02 arrived (Cardiology)",
        "payload_json": {
            "patient_id": "P-REP-02",
            "name": "Patient P-REP-02",
            "priority": "emergency",
            "arrival_minute": 15,
            "service_duration_minutes": 25,
            "required_specialty": "cardiology",
            "status": "waiting",
        },
    },
    {
        "minute": 70,
        "id": "EV-REP-AV-D1",
        "event_type": "doctor_availability",
        "description": "Dr. Rao returned to duty — queue recalculated",
        "payload_json": {
            "doctor_id": "D1",
        },
    },
]


def generate_events_for_minute(
    minute: int,
    seed: int = 42,
    next_event_index: int = 0,
    mode: str = "live_synthetic",
    existing_patient_count: int = 25,
) -> List[Dict[str, Any]]:
    """
    Generate proposed events due strictly at `minute`.
    Returns list of event dictionaries (does NOT mutate DB).
    """
    if mode == "replay":
        events = []
        for item in REPLAY_SCHEDULE:
            if item["minute"] == minute:
                events.append({
                    "id": item["id"],
                    "event_type": item["event_type"],
                    "simulation_minute": minute,
                    "description": item["description"],
                    "payload_json": item["payload_json"],
                    "status": "pending",
                })
        return events

    if existing_patient_count >= (25 + MAX_SYNTHETIC_PATIENTS):
        return []

    events = []

    # Check predictable schedule first
    for item in SCHEDULED_ARRIVALS:
        if item["minute"] == minute:
            idx = next_event_index + len(events)
            patient_id = f"P-SYN-{idx + 1:03d}"
            is_emergency = item["priority"] == "emergency"
            event_type = "emergency_arrival" if is_emergency else "patient_arrival"
            
            desc = (
                f"🚨 Emergency patient {patient_id} arrived ({item['specialty'].capitalize()})"
                if is_emergency
                else f"Patient {patient_id} checked in ({item['specialty'].capitalize()} - {item['priority']})"
            )

            events.append({
                "id": f"EV-SYN-{idx + 1:04d}",
                "event_type": event_type,
                "simulation_minute": minute,
                "description": desc,
                "payload_json": {
                    "patient_id": patient_id,
                    "name": f"Patient {patient_id}",
                    "priority": item["priority"],
                    "arrival_minute": minute,
                    "service_duration_minutes": item["duration"],
                    "required_specialty": item["specialty"],
                    "status": "waiting",
                },
                "status": "pending",
            })

    # For minutes beyond scheduled arrivals in live_synthetic mode:
    # Deterministic procedural generation every 15 minutes after min 150
    if not events and mode == "live_synthetic" and minute > 150 and minute % 15 == 0:
        rng = random.Random(seed + minute)
        priority = rng.choices(["normal", "urgent", "emergency"], weights=[0.75, 0.20, 0.05])[0]
        specialty = rng.choice(["general", "cardiology", "orthopedics"])
        duration = rng.choice([15, 20, 25, 30])
        idx = next_event_index + len(events)
        patient_id = f"P-SYN-{idx + 1:03d}"
        is_emergency = priority == "emergency"
        event_type = "emergency_arrival" if is_emergency else "patient_arrival"
        
        desc = (
            f"🚨 Emergency patient {patient_id} arrived ({specialty.capitalize()})"
            if is_emergency
            else f"Patient {patient_id} checked in ({specialty.capitalize()} - {priority})"
        )

        events.append({
            "id": f"EV-SYN-{idx + 1:04d}",
            "event_type": event_type,
            "simulation_minute": minute,
            "description": desc,
            "payload_json": {
                "patient_id": patient_id,
                "name": f"Patient {patient_id}",
                "priority": priority,
                "arrival_minute": minute,
                "service_duration_minutes": duration,
                "required_specialty": specialty,
                "status": "waiting",
            },
            "status": "pending",
        })

    return events
