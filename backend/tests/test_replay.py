import pytest
from sqlalchemy.orm import Session

from app.models import (
    DoctorUnavailability, Patient, SimulationState,
    SyntheticEvent, SyntheticGeneratorState,
)
from app.services.event_processor import process_simulation_tick


def test_deterministic_replay_flow(db_session: Session):
    """
    Test deterministic replay scenario:
    - Min 10: Dr. Rao (D1) unavailable for 60 min
    - Min 15: Two emergency arrivals
    - Min 70: Dr. Rao returns and queue recalculates
    """
    gen = db_session.query(SyntheticGeneratorState).filter(SyntheticGeneratorState.id == "singleton").first()
    gen.enabled = True
    gen.mode = "replay"
    gen.last_processed_minute = 0
    db_session.commit()

    # Advance to Min 10
    process_simulation_tick(db_session, current_minute=10)

    # Verify Dr. Rao unavailability event and record
    unav = db_session.query(DoctorUnavailability).filter(DoctorUnavailability.doctor_id == "D1").first()
    assert unav is not None
    assert unav.start_minute == 10
    assert unav.end_minute == 70

    unav_evt = db_session.query(SyntheticEvent).filter(SyntheticEvent.id == "EV-REP-UNAV-D1").first()
    assert unav_evt is not None
    assert unav_evt.simulation_minute == 10

    # Advance to Min 15: two emergency arrivals
    process_simulation_tick(db_session, current_minute=15)
    em_events = db_session.query(SyntheticEvent).filter(
        SyntheticEvent.event_type == "emergency_arrival",
        SyntheticEvent.simulation_minute == 15,
    ).all()
    assert len(em_events) == 2

    # Verify emergency patients were inserted
    p1 = db_session.query(Patient).filter(Patient.id == "P-REP-01").first()
    p2 = db_session.query(Patient).filter(Patient.id == "P-REP-02").first()
    assert p1 is not None and p1.priority == "emergency"
    assert p2 is not None and p2.priority == "emergency"

    # Advance to Min 70: Dr. Rao returns
    process_simulation_tick(db_session, current_minute=70)
    av_evt = db_session.query(SyntheticEvent).filter(SyntheticEvent.id == "EV-REP-AV-D1").first()
    assert av_evt is not None
    assert av_evt.simulation_minute == 70

    # DoctorUnavailability for D1 should be cleared
    active_unav = db_session.query(DoctorUnavailability).filter(
        DoctorUnavailability.doctor_id == "D1",
        DoctorUnavailability.end_minute >= 70,
    ).first()
    assert active_unav is None
