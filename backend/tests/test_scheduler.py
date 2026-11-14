import pytest
from app.services.scheduler import run_fallback, run_optimizer, validate_schedule


DOCTORS = [
    {"id": "D01", "name": "Dr. Rao", "specialties": ["general"],
     "shift_start_minute": 0, "shift_end_minute": 480, "active": True},
    {"id": "D03", "name": "Dr. Shah", "specialties": ["cardiology"],
     "shift_start_minute": 0, "shift_end_minute": 480, "active": True},
]

PATIENTS_GENERAL = [
    {"id": "P1", "name": "P1", "priority": "normal", "arrival_minute": 0,
     "service_duration_minutes": 30, "required_specialty": "general", "status": "waiting"},
    {"id": "P2", "name": "P2", "priority": "normal", "arrival_minute": 10,
     "service_duration_minutes": 30, "required_specialty": "general", "status": "waiting"},
]


def test_no_overlap():
    result = run_optimizer(0, PATIENTS_GENERAL, DOCTORS, [], [], 480)
    schedule = result["schedule"]
    # Both should be scheduled with doctor D01 (general)
    d01_appts = [(a["start_minute"], a["end_minute"]) for a in schedule if a["doctor_id"] == "D01"]
    d01_appts.sort()
    for i in range(len(d01_appts) - 1):
        assert d01_appts[i][1] <= d01_appts[i + 1][0], "Overlap detected"


def test_specialty_match():
    patients = [
        {"id": "PC1", "name": "PC1", "priority": "normal", "arrival_minute": 0,
         "service_duration_minutes": 20, "required_specialty": "cardiology", "status": "waiting"},
    ]
    result = run_optimizer(0, patients, DOCTORS, [], [], 480)
    schedule = result["schedule"]
    for appt in schedule:
        if appt["patient_id"] == "PC1":
            assert appt["doctor_id"] == "D03", "Cardiology patient must go to cardiology doctor"


def test_shift_bounds():
    patients = [
        {"id": f"P{i}", "name": f"P{i}", "priority": "normal", "arrival_minute": 0,
         "service_duration_minutes": 15, "required_specialty": "general", "status": "waiting"}
        for i in range(5)
    ]
    result = run_optimizer(0, patients, DOCTORS, [], [], 480)
    for appt in result["schedule"]:
        d = next(d for d in DOCTORS if d["id"] == appt["doctor_id"])
        assert appt["start_minute"] >= d["shift_start_minute"]
        assert appt["end_minute"] <= d["shift_end_minute"]


def test_locked_appointments():
    locked = [
        {"id": "LOCKED1", "patient_id": "P1", "doctor_id": "D01",
         "start_minute": 5, "end_minute": 35, "status": "in_progress", "schedule_version": 1},
    ]
    patients = [
        {"id": "P1", "name": "P1", "priority": "normal", "arrival_minute": 0,
         "service_duration_minutes": 30, "required_specialty": "general", "status": "in_progress"},
        {"id": "P2", "name": "P2", "priority": "normal", "arrival_minute": 10,
         "service_duration_minutes": 20, "required_specialty": "general", "status": "waiting"},
    ]
    result = run_optimizer(10, patients, DOCTORS, locked, [], 480)
    ids = [a.get("id") or a.get("patient_id") for a in result["schedule"]]
    # Locked appointment preserved
    assert any(a.get("id") == "LOCKED1" for a in result["schedule"])


def test_unscheduled_reported():
    # Patient needing a specialty nobody has
    patients = [
        {"id": "PX", "name": "PX", "priority": "normal", "arrival_minute": 0,
         "service_duration_minutes": 20, "required_specialty": "neurology", "status": "waiting"},
    ]
    result = run_optimizer(0, patients, DOCTORS, [], [], 480)
    assert "PX" in result["unscheduled_patients"]


def test_fallback():
    result = run_fallback(0, PATIENTS_GENERAL, DOCTORS, [], [], 480)
    assert result["solver_status"] == "FALLBACK"
    assert len(result["schedule"]) > 0
    # Validate no overlaps
    validate_schedule(
        result["schedule"], DOCTORS,
        PATIENTS_GENERAL, []
    )


def test_validate_no_overlap_raises():
    bad_schedule = [
        {"id": "A1", "patient_id": "P1", "doctor_id": "D01",
         "start_minute": 0, "end_minute": 30, "status": "scheduled"},
        {"id": "A2", "patient_id": "P2", "doctor_id": "D01",
         "start_minute": 10, "end_minute": 40, "status": "scheduled"},
    ]
    with pytest.raises(ValueError, match="Overlapping"):
        validate_schedule(bad_schedule, DOCTORS, PATIENTS_GENERAL, [])
