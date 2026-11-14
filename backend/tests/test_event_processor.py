import pytest
from sqlalchemy.orm import Session

from app.models import (
    Appointment, Patient, SimulationState,
    SyntheticEvent, SyntheticGeneratorState,
)
from app.services.event_processor import process_simulation_tick
from app.services.synthetic_events import generate_events_for_minute


def test_process_simulation_tick_transitions(db_session: Session):
    """Test that scheduled appointments transition to in_progress and completed."""
    # Find a scheduled appointment
    appt = db_session.query(Appointment).filter(Appointment.status == "scheduled").first()
    assert appt is not None

    start = appt.start_minute
    end = appt.end_minute

    # Tick at start minute: should become in_progress
    res = process_simulation_tick(db_session, current_minute=start)
    db_session.refresh(appt)
    assert appt.status == "in_progress"

    # Tick at end minute: should become completed and generate consultation_completed event
    res = process_simulation_tick(db_session, current_minute=end)
    db_session.refresh(appt)
    assert appt.status == "completed"

    comp_events = db_session.query(SyntheticEvent).filter(
        SyntheticEvent.event_type == "consultation_completed"
    ).all()
    assert len(comp_events) >= 1


def test_live_synthetic_arrival_and_reoptimization(db_session: Session):
    """Test that in live_synthetic mode, an arrival triggers patient addition and schedule reoptimization."""
    gen = db_session.query(SyntheticGeneratorState).filter(SyntheticGeneratorState.id == "singleton").first()
    gen.enabled = True
    gen.mode = "live_synthetic"
    gen.last_processed_minute = 0
    db_session.commit()

    initial_patient_count = db_session.query(Patient).count()

    # Minute 5 has a scheduled arrival in synthetic_events schedule
    result = process_simulation_tick(db_session, current_minute=5)

    # Check that new patient was added
    new_patient_count = db_session.query(Patient).count()
    assert new_patient_count == initial_patient_count + 1

    # Check that events were generated
    events = db_session.query(SyntheticEvent).filter(SyntheticEvent.simulation_minute == 5).all()
    event_types = [e.event_type for e in events]
    assert "patient_arrival" in event_types
    assert "queue_reoptimized" in event_types


def test_manual_mode_does_not_generate_synthetic_arrivals(db_session: Session):
    """Test that in manual mode (disabled), no synthetic arrivals are injected."""
    gen = db_session.query(SyntheticGeneratorState).filter(SyntheticGeneratorState.id == "singleton").first()
    gen.enabled = False
    gen.mode = "manual"
    gen.last_processed_minute = 0
    db_session.commit()

    initial_patient_count = db_session.query(Patient).count()

    # Advance to minute 12 (which has an event in live schedule)
    result = process_simulation_tick(db_session, current_minute=12)

    assert db_session.query(Patient).count() == initial_patient_count
    # No synthetic patient arrival events
    assert db_session.query(SyntheticEvent).filter(
        SyntheticEvent.event_type.in_(["patient_arrival", "emergency_arrival"])
    ).count() == 0
