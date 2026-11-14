import datetime
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Appointment, Doctor, DoctorUnavailability, Patient, ScheduleVersion, SimulationState
from ..services.event_manager import manager
from ..services.scheduler import run_optimizer

router = APIRouter()


@router.post("/optimize")
async def optimize(db: Session = Depends(get_db)):
    sim = db.query(SimulationState).filter(SimulationState.id == "singleton").first()
    current_minute = sim.current_minute if sim else 0
    current_version = sim.state_version if sim else 1

    patients = [
        {"id": p.id, "name": p.name, "priority": p.priority, "arrival_minute": p.arrival_minute,
         "appointment_minute": p.appointment_minute, "service_duration_minutes": p.service_duration_minutes,
         "required_specialty": p.required_specialty, "status": p.status}
        for p in db.query(Patient).all()
    ]
    doctors = [
        {"id": d.id, "name": d.name, "specialties": d.specialties if isinstance(d.specialties, list) else [],
         "shift_start_minute": d.shift_start_minute, "shift_end_minute": d.shift_end_minute, "active": d.active}
        for d in db.query(Doctor).filter(Doctor.active == True).all()
    ]
    existing_appointments = [
        {"id": a.id, "patient_id": a.patient_id, "doctor_id": a.doctor_id,
         "start_minute": a.start_minute, "end_minute": a.end_minute, "status": a.status,
         "schedule_version": a.schedule_version}
        for a in db.query(Appointment).filter(Appointment.status != "cancelled").all()
    ]
    unavailabilities = [
        {"id": u.id, "doctor_id": u.doctor_id, "start_minute": u.start_minute,
         "end_minute": u.end_minute, "reason": u.reason}
        for u in db.query(DoctorUnavailability).all()
    ]

    result = run_optimizer(
        current_minute, patients, doctors, existing_appointments,
        unavailabilities, settings.PLANNING_HORIZON,
    )

    new_version = current_version + 1

    # Remove old scheduled appointments
    db.query(Appointment).filter(Appointment.status == "scheduled").delete()

    for appt_data in result["schedule"]:
        if appt_data.get("status") in ("in_progress", "completed"):
            continue
        appt_id = appt_data.get("id") or f"A-{uuid.uuid4().hex[:8]}"
        db.add(Appointment(
            id=appt_id,
            patient_id=appt_data["patient_id"],
            doctor_id=appt_data["doctor_id"],
            start_minute=appt_data["start_minute"],
            end_minute=appt_data["end_minute"],
            status="scheduled",
            schedule_version=new_version,
        ))
        p = db.query(Patient).filter(Patient.id == appt_data["patient_id"]).first()
        if p:
            p.status = "scheduled"
            p.appointment_minute = appt_data["start_minute"]

    db.add(ScheduleVersion(
        version=new_version,
        created_at=datetime.datetime.utcnow(),
        solver_status=result["solver_status"],
        objective_value=result.get("objective_value"),
        trigger="manual_optimize",
    ))

    if sim:
        sim.state_version = new_version

    db.commit()

    await manager.broadcast({
        "type": "state_updated",
        "state_version": new_version,
        "trigger": "optimize",
    })

    return {
        "solver_status": result["solver_status"],
        "scheduled_count": len([a for a in result["schedule"] if a.get("status") == "scheduled"]),
        "unscheduled_count": len(result["unscheduled_patients"]),
        "objective_value": result.get("objective_value"),
        "execution_time_ms": result["execution_time_ms"],
        "state_version": new_version,
    }
