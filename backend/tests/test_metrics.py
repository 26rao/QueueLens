from app.services.metrics import compute_metrics

DOCTORS = [
    {"id": "D01", "shift_start_minute": 0, "shift_end_minute": 480},
]


def test_waiting_time():
    patients = [{"id": "P1", "priority": "normal", "arrival_minute": 10, "status": "scheduled"}]
    appointments = [{"patient_id": "P1", "doctor_id": "D01", "start_minute": 40, "end_minute": 55, "status": "scheduled"}]
    metrics = compute_metrics(appointments, patients, DOCTORS, [], 0)
    assert metrics["avg_wait"] == 30.0


def test_utilization():
    patients = [{"id": "P1", "priority": "normal", "arrival_minute": 0, "status": "scheduled"}]
    appointments = [{"patient_id": "P1", "doctor_id": "D01", "start_minute": 0, "end_minute": 60, "status": "scheduled"}]
    metrics = compute_metrics(appointments, patients, DOCTORS, [], 0)
    # 60 / 480 * 100 = 12.5%
    assert metrics["doctor_utilization"]["D01"] == 12.5


def test_avg_by_priority():
    patients = [
        {"id": "P1", "priority": "emergency", "arrival_minute": 0, "status": "scheduled"},
        {"id": "P2", "priority": "normal", "arrival_minute": 0, "status": "scheduled"},
    ]
    appointments = [
        {"patient_id": "P1", "doctor_id": "D01", "start_minute": 10, "end_minute": 30, "status": "scheduled"},
        {"patient_id": "P2", "doctor_id": "D01", "start_minute": 50, "end_minute": 70, "status": "scheduled"},
    ]
    metrics = compute_metrics(appointments, patients, DOCTORS, [], 0)
    assert metrics["avg_wait_by_priority"]["emergency"] == 10.0
    assert metrics["avg_wait_by_priority"]["normal"] == 50.0
