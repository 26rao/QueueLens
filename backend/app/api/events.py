from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db
from ..models import SyntheticEvent, SyntheticGeneratorState
from ..schemas import EventListResponse, SyntheticEventRead

router = APIRouter()


@router.get("/events", response_model=EventListResponse)
def get_events(
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Returns the latest committed synthetic hospital events,
    ordered by simulation time and creation sequence.
    """
    events = (
        db.query(SyntheticEvent)
        .order_by(SyntheticEvent.simulation_minute.desc(), SyntheticEvent.created_at.desc())
        .limit(limit)
        .all()
    )

    gen = db.query(SyntheticGeneratorState).filter(SyntheticGeneratorState.id == "singleton").first()
    mode = gen.mode if gen else "manual"
    enabled = gen.enabled if gen else False

    event_reads = [
        SyntheticEventRead(
            id=e.id,
            event_type=e.event_type,
            simulation_minute=e.simulation_minute,
            description=e.description,
            payload_json=e.payload_json or {},
            status=e.status,
            state_version=e.state_version,
            created_at=e.created_at,
        )
        for e in events
    ]

    return EventListResponse(
        events=event_reads,
        mode=mode,
        enabled=enabled,
    )
