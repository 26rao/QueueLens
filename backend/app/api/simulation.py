from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import SimulationState
from ..services.event_manager import manager
from ..services.simulation_service import advance_simulation_minute
from ..database import SessionLocal

router = APIRouter()


class AdvanceRequest(BaseModel):
    minutes: int = 1


class SpeedRequest(BaseModel):
    speed: int


@router.post("/simulation/advance")
async def advance(body: AdvanceRequest, db: Session = Depends(get_db)):
    if body.minutes < 1 or body.minutes > 480:
        raise HTTPException(status_code=422, detail="minutes must be 1–480")
    sim = db.query(SimulationState).filter(SimulationState.id == "singleton").first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not initialized")

    for _ in range(body.minutes):
        advance_simulation_minute(lambda: SessionLocal())

    db.refresh(sim)
    await manager.broadcast({
        "type": "simulation_tick",
        "simulation_minute": sim.current_minute,
        "state_version": sim.state_version,
    })
    return {"current_minute": sim.current_minute, "state_version": sim.state_version}


@router.post("/simulation/speed")
async def set_speed(body: SpeedRequest, db: Session = Depends(get_db)):
    if body.speed not in (0, 1, 5, 15):
        raise HTTPException(status_code=422, detail="speed must be 0, 1, 5, or 15")
    sim = db.query(SimulationState).filter(SimulationState.id == "singleton").first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not initialized")
    sim.speed = body.speed
    db.commit()
    return {"speed": sim.speed}


@router.post("/simulation/pause")
async def toggle_pause(db: Session = Depends(get_db)):
    sim = db.query(SimulationState).filter(SimulationState.id == "singleton").first()
    if not sim:
        raise HTTPException(status_code=404, detail="Simulation not initialized")
    sim.paused = not sim.paused
    db.commit()
    return {"paused": sim.paused}


@router.post("/reset")
async def reset(db: Session = Depends(get_db)):
    """Reset simulation scenario to initial deterministic seed."""
    from ..seed import reset_scenario
    from ..services.disruption_service import clear_preview_cache
    from ..config import settings

    clear_preview_cache()
    reset_scenario(db, settings.PLANNING_HORIZON)

    sim = db.query(SimulationState).filter(SimulationState.id == "singleton").first()
    state_version = sim.state_version if sim else 1

    await manager.broadcast({
        "type": "scenario_reset",
        "state_version": state_version,
        "simulation_minute": 0,
    })
    return {"status": "ok", "state_version": state_version}
