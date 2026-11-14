import pytest
from sqlalchemy.exc import IntegrityError
from app.models import SyntheticEvent, SyntheticGeneratorState, Doctor, Patient, Appointment
from app.database import Base


def test_generator_state_default(db_session):
    gen = db_session.query(SyntheticGeneratorState).filter(SyntheticGeneratorState.id == "singleton").first()
    assert gen is not None, "Generator state singleton must exist"
    assert gen.enabled is False, "Default generator must be disabled"
    assert gen.mode == "manual", "Default mode must be manual"
    assert gen.seed == 42


def test_synthetic_event_persistence(db_session):
    event_id = "EV-TEST-001"
    evt = SyntheticEvent(
        id=event_id,
        event_type="patient_arrival",
        simulation_minute=10,
        description="Patient P-TEST-1 arrived",
        payload_json={"patient_id": "P-TEST-1", "priority": "normal"},
        status="pending",
        state_version=1,
    )
    db_session.add(evt)
    db_session.commit()

    saved = db_session.query(SyntheticEvent).filter(SyntheticEvent.id == event_id).first()
    assert saved is not None
    assert saved.event_type == "patient_arrival"
    assert saved.simulation_minute == 10
    assert saved.payload_json["patient_id"] == "P-TEST-1"
    assert saved.status == "pending"


def test_duplicate_event_id_rejected(db_session):
    event_id = "EV-DUP-001"
    evt1 = SyntheticEvent(
        id=event_id,
        event_type="patient_arrival",
        simulation_minute=5,
        description="First",
        payload_json={},
        status="pending",
    )
    db_session.add(evt1)
    db_session.commit()

    # Adding same ID must raise IntegrityError
    evt2 = SyntheticEvent(
        id=event_id,
        event_type="patient_arrival",
        simulation_minute=6,
        description="Duplicate",
        payload_json={},
        status="pending",
    )
    db_session.add(evt2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_existing_data_intact(db_session):
    assert db_session.query(Doctor).count() == 5, "Initial 5 doctors intact"
    assert db_session.query(Patient).count() >= 25, "Initial 25 patients intact"
    assert db_session.query(Appointment).count() >= 20, "Appointments intact"
