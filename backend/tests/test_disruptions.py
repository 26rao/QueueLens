import pytest
from app.services.ai_parser import parse_deterministic


def test_parse_doctor_unavailable():
    actions = parse_deterministic("Dr. Rao is unavailable for 60 minutes")
    assert len(actions) == 1
    assert actions[0]["type"] == "doctor_unavailable"
    assert actions[0]["doctor_id"] == "D01"
    assert actions[0]["duration_minutes"] == 60


def test_parse_add_emergency():
    actions = parse_deterministic("Add 2 emergency patients")
    assert any(a["type"] == "add_emergency" and a["count"] == 2 for a in actions)


def test_parse_doctor_available():
    actions = parse_deterministic("Dr. Rao is available again")
    assert any(a["type"] == "doctor_available" and a["doctor_id"] == "D01" for a in actions)


def test_invalid_duration(client):
    # Preview with invalid duration should return 422
    state = client.get("/api/state").json()
    version = state["state_version"]
    resp = client.post("/api/disruptions/preview", json={
        "actions": [{"type": "doctor_unavailable", "doctor_id": "D01", "duration_minutes": 0}],
        "expected_state_version": version,
    })
    assert resp.status_code == 422


def test_compound_command():
    actions = parse_deterministic("Dr. Rao unavailable 90 minutes and add 2 emergency patients")
    types = [a["type"] for a in actions]
    assert "doctor_unavailable" in types
    assert "add_emergency" in types
    assert len(actions) == 2
