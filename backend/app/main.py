import datetime
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, SessionLocal, engine
from .models import (  # noqa: F401 - needed for Base.metadata.create_all
    Appointment, Disruption, Doctor, DoctorUnavailability,
    Patient, ScheduleVersion, SimulationState,
)
from .seed import seed_database, run_initial_optimization
from .services.event_manager import manager
from .services.simulation_service import start_simulation, stop_simulation

from .api import analytics, disruptions, doctors, optimization, patients, simulation, state


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
        run_initial_optimization(db, settings.PLANNING_HORIZON)
    finally:
        db.close()

    def get_current_state():
        db = SessionLocal()
        try:
            sim = db.query(SimulationState).filter(SimulationState.id == "singleton").first()
            if sim:
                return {
                    "current_minute": sim.current_minute,
                    "speed": sim.speed,
                    "paused": sim.paused,
                    "state_version": sim.state_version,
                }
            return None
        finally:
            db.close()

    start_simulation(SessionLocal, manager, get_current_state)

    yield

    stop_simulation()


def _run_initial_optimization(db):
    if db.query(Appointment).count() > 0:
        return

    sim = db.query(SimulationState).filter(SimulationState.id == "singleton").first()
    current_minute = sim.current_minute if sim else 0
    current_version = sim.state_version if sim else 1

    from .services.scheduler import run_optimizer

    patients_data = [
        {"id": p.id, "name": p.name, "priority": p.priority, "arrival_minute": p.arrival_minute,
         "service_duration_minutes": p.service_duration_minutes, "required_specialty": p.required_specialty,
         "status": p.status, "appointment_minute": p.appointment_minute}
        for p in db.query(Patient).all()
    ]
    doctors_data = [
        {"id": d.id, "name": d.name,
         "specialties": d.specialties if isinstance(d.specialties, list) else [],
         "shift_start_minute": d.shift_start_minute, "shift_end_minute": d.shift_end_minute, "active": d.active}
        for d in db.query(Doctor).filter(Doctor.active == True).all()
    ]

    result = run_optimizer(current_minute, patients_data, doctors_data, [], [], settings.PLANNING_HORIZON)

    for appt_data in result["schedule"]:
        appt_id = f"A-{uuid.uuid4().hex[:8]}"
        db.add(Appointment(
            id=appt_id,
            patient_id=appt_data["patient_id"],
            doctor_id=appt_data["doctor_id"],
            start_minute=appt_data["start_minute"],
            end_minute=appt_data["end_minute"],
            status="scheduled",
            schedule_version=current_version,
        ))
        p = db.query(Patient).filter(Patient.id == appt_data["patient_id"]).first()
        if p:
            p.status = "scheduled"
            p.appointment_minute = appt_data["start_minute"]

    # Update schedule version record
    sv = db.query(ScheduleVersion).filter(ScheduleVersion.version == current_version).first()
    if sv:
        sv.solver_status = result["solver_status"]
        sv.objective_value = result.get("objective_value")

    db.commit()


app = FastAPI(title="QueueLens API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(state.router, prefix="/api")
app.include_router(patients.router, prefix="/api")
app.include_router(doctors.router, prefix="/api")
app.include_router(disruptions.router, prefix="/api")
app.include_router(optimization.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(simulation.router, prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "queuelens"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
