import pytest


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_state(client):
    resp = client.get("/api/state")
    assert resp.status_code == 200
    data = resp.json()
    assert "patients" in data
    assert "doctors" in data
    assert "appointments" in data
    assert len(data["doctors"]) == 5
    assert len(data["patients"]) == 25


def test_parse_endpoint(client):
    resp = client.post("/api/disruptions/parse", json={"text": "Dr. Rao is unavailable for 60 minutes"})
    assert resp.status_code == 200
    data = resp.json()
    assert any(a["type"] == "doctor_unavailable" for a in data["actions"])


def test_reset(client):
    resp = client.post("/api/reset")
    assert resp.status_code == 200
