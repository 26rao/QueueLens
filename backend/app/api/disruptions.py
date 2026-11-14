import datetime
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import (
    Appointment, Disruption, Doctor, DoctorUnavailability,
    Patient, SimulationState,
)
from ..schemas import ApplyRequest, ParseRequest, ParseResponse, PreviewRequest, PreviewResponse
from ..services import ai_parser, disruption_service
from ..services.event_manager import manager

router = APIRouter()


def _load_state(db: Session):
    sim = db.query(SimulationState).filter(SimulationState.id == "singleton").first()
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
    appointments = [
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
    return sim, patients, doctors, appointments, unavailabilities


@router.post("/disruptions/parse", response_model=ParseResponse)
async def parse_disruption(body: ParseRequest):
    actions, parser_mode = await ai_parser.parse_disruption(body.text, settings)
    return ParseResponse(actions=actions, parser_mode=parser_mode)


@router.post("/disruptions/preview")
async def preview_disruption(body: PreviewRequest, db: Session = Depends(get_db)):
    sim, patients, doctors, appointments, unavailabilities = _load_state(db)
    current_version = sim.state_version if sim else 1

    if body.expected_state_version != current_version:
        raise HTTPException(
            status_code=409,
            detail=f"State version mismatch: expected {body.expected_state_version}, current {current_version}",
        )

    # Validate action durations
    for action in body.actions:
        if action.duration_minutes is not None:
            if action.duration_minutes < 1 or action.duration_minutes > 480:
                raise HTTPException(status_code=422, detail="duration_minutes must be between 1 and 480")

    actions_dicts = [a.model_dump(exclude_none=True) for a in body.actions]

    result = disruption_service.preview_disruption(
        actions=actions_dicts,
        current_state_version=current_version,
        patients=patients,
        doctors=doctors,
        appointments=appointments,
        unavailabilities=unavailabilities,
        current_minute=sim.current_minute if sim else 0,
        planning_horizon=settings.PLANNING_HORIZON,
    )
    return result


@router.post("/disruptions/apply")
async def apply_disruption(body: ApplyRequest, db: Session = Depends(get_db)):
    sim, patients, doctors, appointments, unavailabilities = _load_state(db)
    current_version = sim.state_version if sim else 1

    if body.expected_state_version != current_version:
        raise HTTPException(
            status_code=409,
            detail=f"State version mismatch: expected {body.expected_state_version}, current {current_version}",
        )

    cached = disruption_service.get_preview(body.preview_id, body.expected_state_version)
    if cached is None:
        raise HTTPException(status_code=404, detail="Preview not found or expired")

    opt_result = cached["opt_result"]
    mod_patients = cached["mod_patients"]
    mod_doctors = cached["mod_doctors"]
    mod_appointments = cached["mod_appointments"]
    mod_unavailabilities = cached["mod_unavailabilities"]
    actions = cached["actions"]

    # Commit in transaction
    new_version = current_version + 1

    # Add any new patients (such as emergency patients created in preview)
    existing_pids = {p.id for p in db.query(Patient).all()}
    for mp in mod_patients:
        if mp["id"] not in existing_pids:
            db.add(Patient(
                id=mp["id"],
                name=mp.get("name", "Emergency Patient"),
                priority=mp.get("priority", "emergency"),
                arrival_minute=mp.get("arrival_minute", sim.current_minute if sim else 0),
                appointment_minute=mp.get("appointment_minute"),
                service_duration_minutes=mp.get("service_duration_minutes", 20),
                required_specialty=mp.get("required_specialty", "general"),
                status=mp.get("status", "waiting"),
            ))
            existing_pids.add(mp["id"])

    # Synchronize unavailabilities from validated preview
    db.query(DoctorUnavailability).delete()
    for u in mod_unavailabilities:
        db.add(DoctorUnavailability(
            id=u.get("id") or f"unav-{uuid.uuid4().hex[:8]}",
            doctor_id=u["doctor_id"],
            start_minute=u["start_minute"],
            end_minute=u["end_minute"],
            reason=u.get("reason", "Disruption applied"),
        ))

    # Cancel existing scheduled appointments
    db.query(Appointment).filter(Appointment.status == "scheduled").delete()

    # Handle cancelled appointments from actions
    for action in actions:
        atype = action.get("type") or action.get("action_type")
        if atype == "cancel_appointment":
            appt_id = action.get("appointment_id")
            if appt_id:
                appt = db.query(Appointment).filter(Appointment.id == appt_id).first()
                if appt:
                    appt.status = "cancelled"
                    p = db.query(Patient).filter(Patient.id == appt.patient_id).first()
                    if p:
                        p.status = "waiting"

    # Flush so that foreign keys for newly added patients are in SQLite
    db.flush()

    # Insert new appointments
    for appt_data in opt_result["schedule"]:
        # Skip locked ones (already in db)
        if appt_data.get("id") and appt_data.get("status") in ("in_progress", "completed"):
            continue
        appt_id = appt_data.get("id") or f"A-{uuid.uuid4().hex[:8]}"
        # Only insert newly scheduled ones
        if appt_data.get("status") == "scheduled":
            db.add(Appointment(
                id=appt_id,
                patient_id=appt_data["patient_id"],
                doctor_id=appt_data["doctor_id"],
                start_minute=appt_data["start_minute"],
                end_minute=appt_data["end_minute"],
                status="scheduled",
                schedule_version=new_version,
            ))
            # Update patient appointment_minute
            p = db.query(Patient).filter(Patient.id == appt_data["patient_id"]).first()
            if p:
                p.status = "scheduled"
                p.appointment_minute = appt_data["start_minute"]

    # Record disruption log
    for action in actions:
        atype = action.get("type") or action.get("action_type")
        db.add(Disruption(
            id=f"D-{uuid.uuid4().hex[:8]}",
            action_type=atype,
            payload_json=action,
            created_at=datetime.datetime.utcnow(),
            simulation_minute=sim.current_minute if sim else 0,
            schedule_version_before=current_version,
            schedule_version_after=new_version,
        ))

    # Increment state version and record schedule version
    if sim:
        sim.state_version = new_version

    from ..models import ScheduleVersion
    db.add(ScheduleVersion(
        version=new_version,
        created_at=datetime.datetime.utcnow(),
        solver_status=opt_result["solver_status"],
        objective_value=opt_result.get("objective_value"),
        trigger="disruption_applied",
    ))

    db.commit()

    # Broadcast state change
    await manager.broadcast({
        "type": "state_updated",
        "state_version": new_version,
        "trigger": "disruption_applied",
    })

    return {
        "state_version": new_version,
        "solver_status": opt_result["solver_status"],
        "scheduled_count": len([a for a in opt_result["schedule"] if a.get("status") == "scheduled"]),
        "unscheduled_count": len(opt_result["unscheduled_patients"]),
    }
