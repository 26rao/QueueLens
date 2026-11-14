import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Appointment, Disruption, Doctor, DoctorUnavailability, Patient, ScheduleVersion, SimulationState
from ..services.metrics import compute_metrics

router = APIRouter()


@router.get("/state")
def get_state(db: Session = Depends(get_db)):
    sim = db.query(SimulationState).filter(SimulationState.id == "singleton").first()
    patients = db.query(Patient).all()
    doctors = db.query(Doctor).all()
    appointments = db.query(Appointment).filter(Appointment.status != "cancelled").all()
    unavailabilities = db.query(DoctorUnavailability).all()

    current_ver = sim.state_version if sim else 1
    sv = db.query(ScheduleVersion).filter(ScheduleVersion.version == current_ver).first()
    solver_status = sv.solver_status if sv else "OPTIMAL"

    recent = db.query(Disruption).order_by(Disruption.created_at.desc()).limit(10).all()
    alerts = []
    for d in recent:
        payload = d.payload_json if isinstance(d.payload_json, dict) else json.loads(d.payload_json or "{}")
        alerts.append({"type": d.action_type, "payload": payload, "minute": d.simulation_minute})

    patients_data = [_patient_to_dict(p) for p in patients]
    unav_list = [_unav_to_dict(u) for u in unavailabilities]
    doctors_data = [_doctor_to_dict(d, unavailabilities) for d in doctors]
    appointments_data = [_appt_to_dict(a) for a in appointments]

    metrics = compute_metrics(
        appointments_data,
        patients_data,
        [{"id": d.id, "shift_start_minute": d.shift_start_minute, "shift_end_minute": d.shift_end_minute} for d in doctors],
        unav_list,
        sim.current_minute if sim else 0,
    )

    return {
        "state_version": sim.state_version if sim else 1,
        "solver_status": solver_status,
        "simulation": {
            "current_minute": sim.current_minute if sim else 0,
            "speed": sim.speed if sim else 1,
            "paused": sim.paused if sim else False,
        },
        "patients": patients_data,
        "doctors": doctors_data,
        "appointments": appointments_data,
        "metrics": metrics,
        "alerts": alerts,
    }


def _patient_to_dict(p):
    return {
        "id": p.id, "name": p.name, "priority": p.priority,
        "arrival_minute": p.arrival_minute, "appointment_minute": p.appointment_minute,
        "service_duration_minutes": p.service_duration_minutes,
        "required_specialty": p.required_specialty, "status": p.status,
    }


def _doctor_to_dict(d, all_unavailabilities):
    unavs = [_unav_to_dict(u) for u in all_unavailabilities if u.doctor_id == d.id]
    return {
        "id": d.id, "name": d.name,
        "specialties": d.specialties if isinstance(d.specialties, list) else [],
        "shift_start_minute": d.shift_start_minute, "shift_end_minute": d.shift_end_minute,
        "active": d.active, "unavailabilities": unavs,
    }


def _unav_to_dict(u):
    return {
        "id": u.id, "doctor_id": u.doctor_id,
        "start_minute": u.start_minute, "end_minute": u.end_minute, "reason": u.reason,
    }


def _appt_to_dict(a):
    return {
        "id": a.id, "patient_id": a.patient_id, "doctor_id": a.doctor_id,
        "start_minute": a.start_minute, "end_minute": a.end_minute,
        "status": a.status, "schedule_version": a.schedule_version,
    }
