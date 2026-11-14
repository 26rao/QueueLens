from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Appointment, Doctor, DoctorUnavailability, Patient, SimulationState
from ..services.metrics import compute_metrics

router = APIRouter()


@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    sim = db.query(SimulationState).filter(SimulationState.id == "singleton").first()
    patients = [
        {"id": p.id, "priority": p.priority, "arrival_minute": p.arrival_minute, "status": p.status}
        for p in db.query(Patient).all()
    ]
    appointments = [
        {"id": a.id, "patient_id": a.patient_id, "doctor_id": a.doctor_id,
         "start_minute": a.start_minute, "end_minute": a.end_minute, "status": a.status}
        for a in db.query(Appointment).filter(Appointment.status != "cancelled").all()
    ]
    doctors = [
        {"id": d.id, "shift_start_minute": d.shift_start_minute, "shift_end_minute": d.shift_end_minute}
        for d in db.query(Doctor).all()
    ]
    unavailabilities = [
        {"doctor_id": u.doctor_id, "start_minute": u.start_minute, "end_minute": u.end_minute}
        for u in db.query(DoctorUnavailability).all()
    ]
    metrics = compute_metrics(
        appointments, patients, doctors, unavailabilities,
        sim.current_minute if sim else 0,
    )
    return metrics
