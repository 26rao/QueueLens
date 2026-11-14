"""
Event Processor for QueueLens Live Synthetic Digital Twin.
Validates and applies events atomically, executes CP-SAT re-optimization,
and persists synthetic event records.
"""
import datetime
import uuid
from typing import List, Dict, Any, Optional

from sqlalchemy.orm import Session

from ..models import (
    Appointment, Disruption, Doctor, DoctorUnavailability,
    Patient, ScheduleVersion, SimulationState, SyntheticEvent, SyntheticGeneratorState,
)
from .synthetic_events import generate_events_for_minute
from .scheduler import run_optimizer, validate_schedule


def process_simulation_tick(db: Session, current_minute: int, planning_horizon: int = 480) -> Dict[str, Any]:
    """
    Called on every simulation minute advancement (both background clock and manual +15 advance).
    1. Updates appointment transitions (scheduled -> in_progress -> completed).
    2. Identifies and processes due synthetic events if live_synthetic mode is active.
    3. Reoptimizes schedule when new patients arrive.
    4. Atomically commits and returns event details.
    """
    sim = db.query(SimulationState).filter(SimulationState.id == "singleton").first()
    if not sim:
        return {"processed_events": [], "state_version": 1}

    gen = db.query(SyntheticGeneratorState).filter(SyntheticGeneratorState.id == "singleton").first()
    if not gen:
        gen = SyntheticGeneratorState(id="singleton", enabled=False, mode="manual", seed=42)
        db.add(gen)
        db.commit()

    processed_events = []
    reoptimized = False

    # 1. Clock-driven appointment status transitions
    active_appts = db.query(Appointment).filter(
        Appointment.status.in_(["scheduled", "in_progress"])
    ).all()

    doctor_map = {d.id: d for d in db.query(Doctor).all()}
    patient_map = {p.id: p for p in db.query(Patient).all()}

    for appt in active_appts:
        if appt.status == "scheduled" and appt.start_minute <= current_minute:
            appt.status = "in_progress"
            p = patient_map.get(appt.patient_id)
            if p and p.status != "completed":
                p.status = "in_progress"

        elif appt.status == "in_progress" and appt.end_minute <= current_minute:
            appt.status = "completed"
            p = patient_map.get(appt.patient_id)
            d = doctor_map.get(appt.doctor_id)
            if p:
                p.status = "completed"

            # Record consultation completed event
            comp_id = f"EV-COMP-{appt.id}"
            if not db.query(SyntheticEvent).filter(SyntheticEvent.id == comp_id).first():
                evt = SyntheticEvent(
                    id=comp_id,
                    event_type="consultation_completed",
                    simulation_minute=current_minute,
                    description=f"Consultation completed — {d.name if d else appt.doctor_id} with {p.name if p else appt.patient_id}",
                    payload_json={"appointment_id": appt.id, "doctor_id": appt.doctor_id, "patient_id": appt.patient_id},
                    status="applied",
                    state_version=sim.state_version,
                )
                db.add(evt)
                processed_events.append(evt)

    # 2. Check for synthetic events due if enabled
    if gen.enabled and gen.mode in ("live_synthetic", "replay"):
        start_min = gen.last_processed_minute + 1
        end_min = current_minute

        total_patients = db.query(Patient).count()

        for m in range(start_min, end_min + 1):
            due_events = generate_events_for_minute(
                minute=m,
                seed=gen.seed,
                next_event_index=gen.next_event_index,
                mode=gen.mode,
                existing_patient_count=total_patients,
            )

            for item in due_events:
                # Check for duplicate event ID
                if db.query(SyntheticEvent).filter(SyntheticEvent.id == item["id"]).first():
                    continue

                p_data = item["payload_json"]
                
                if item["event_type"] in ("patient_arrival", "emergency_arrival"):
                    new_patient = Patient(
                        id=p_data["patient_id"],
                        name=p_data["name"],
                        priority=p_data["priority"],
                        arrival_minute=p_data["arrival_minute"],
                        appointment_minute=None,
                        service_duration_minutes=p_data["service_duration_minutes"],
                        required_specialty=p_data["required_specialty"],
                        status="waiting",
                    )
                    db.add(new_patient)
                    db.flush()
                    gen.next_event_index += 1
                    total_patients += 1
                    reoptimized = True

                elif item["event_type"] == "doctor_unavailability":
                    unav = DoctorUnavailability(
                        id=f"unav-{item['id']}",
                        doctor_id=p_data["doctor_id"],
                        start_minute=p_data["start_minute"],
                        end_minute=p_data["end_minute"],
                        reason=p_data.get("reason", "Disruption"),
                    )
                    db.add(unav)
                    db.flush()
                    reoptimized = True

                elif item["event_type"] == "doctor_availability":
                    doc_id = p_data["doctor_id"]
                    db.query(DoctorUnavailability).filter(
                        DoctorUnavailability.doctor_id == doc_id,
                        DoctorUnavailability.end_minute >= current_minute,
                    ).delete()
                    db.flush()
                    reoptimized = True

                # Record synthetic event
                evt = SyntheticEvent(
                    id=item["id"],
                    event_type=item["event_type"],
                    simulation_minute=item["simulation_minute"],
                    description=item["description"],
                    payload_json=item["payload_json"],
                    status="applied",
                    state_version=sim.state_version + 1,
                )
                db.add(evt)
                processed_events.append(evt)

        # 3. If new arrivals occurred, re-optimize schedule
        if reoptimized:
            _execute_reoptimization(db, sim, current_minute, planning_horizon, processed_events)

    gen.last_processed_minute = current_minute
    db.commit()

    return {
        "processed_events": [
            {
                "id": e.id,
                "event_type": e.event_type,
                "simulation_minute": e.simulation_minute,
                "description": e.description,
                "status": e.status,
            }
            for e in processed_events
        ],
        "state_version": sim.state_version,
    }


def _execute_reoptimization(db: Session, sim: SimulationState, current_minute: int, planning_horizon: int, processed_events: list):
    """Run CP-SAT optimizer and commit new schedule version atomically."""
    patients_data = [
        {"id": p.id, "name": p.name, "priority": p.priority, "arrival_minute": p.arrival_minute,
         "appointment_minute": p.appointment_minute, "service_duration_minutes": p.service_duration_minutes,
         "required_specialty": p.required_specialty, "status": p.status}
        for p in db.query(Patient).all()
    ]
    doctors_data = [
        {"id": d.id, "name": d.name, "specialties": d.specialties if isinstance(d.specialties, list) else [],
         "shift_start_minute": d.shift_start_minute, "shift_end_minute": d.shift_end_minute, "active": d.active}
        for d in db.query(Doctor).filter(Doctor.active == True).all()
    ]
    existing_appts = [
        {"id": a.id, "patient_id": a.patient_id, "doctor_id": a.doctor_id,
         "start_minute": a.start_minute, "end_minute": a.end_minute, "status": a.status,
         "schedule_version": a.schedule_version}
        for a in db.query(Appointment).all()
    ]
    unavs = [
        {"id": u.id, "doctor_id": u.doctor_id, "start_minute": u.start_minute,
         "end_minute": u.end_minute, "reason": u.reason}
        for u in db.query(DoctorUnavailability).all()
    ]

    opt_result = run_optimizer(current_minute, patients_data, doctors_data, existing_appts, unavs, planning_horizon)

    try:
        validate_schedule(opt_result["schedule"], doctors_data, patients_data, unavs)
    except ValueError:
        # Optimization result invalid, keep previous schedule
        return

    new_version = sim.state_version + 1
    sim.state_version = new_version

    # Keep track of reassigned count
    before_map = {a.patient_id: a.start_minute for a in db.query(Appointment).filter(Appointment.status == "scheduled").all()}
    reassigned_count = 0

    # Delete un-started scheduled appointments
    db.query(Appointment).filter(Appointment.status == "scheduled").delete()

    for appt_data in opt_result["schedule"]:
        if appt_data.get("id") and appt_data.get("status") in ("in_progress", "completed"):
            continue
        if appt_data.get("status") == "scheduled":
            appt_id = f"A-{uuid.uuid4().hex[:8]}"
            pid = appt_data["patient_id"]
            if pid in before_map and before_map[pid] != appt_data["start_minute"]:
                reassigned_count += 1

            db.add(Appointment(
                id=appt_id,
                patient_id=pid,
                doctor_id=appt_data["doctor_id"],
                start_minute=appt_data["start_minute"],
                end_minute=appt_data["end_minute"],
                status="scheduled",
                schedule_version=new_version,
            ))
            p = db.query(Patient).filter(Patient.id == pid).first()
            if p:
                p.status = "scheduled"
                p.appointment_minute = appt_data["start_minute"]

    # Record ScheduleVersion
    db.add(ScheduleVersion(
        version=new_version,
        created_at=datetime.datetime.utcnow(),
        solver_status=opt_result["solver_status"],
        objective_value=opt_result.get("objective_value"),
        trigger="live_synthetic_arrival",
    ))

    # Record reoptimization event
    reopt_evt = SyntheticEvent(
        id=f"EV-OPT-v{new_version}",
        event_type="queue_reoptimized",
        simulation_minute=current_minute,
        description=f"Queue reoptimized — {reassigned_count} assignment(s) adapted ({opt_result['solver_status']})",
        payload_json={"solver_status": opt_result["solver_status"], "reassigned": reassigned_count},
        status="applied",
        state_version=new_version,
    )
    db.add(reopt_evt)
    processed_events.append(reopt_evt)
