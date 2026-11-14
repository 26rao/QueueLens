import datetime
import random
import uuid

from .models import (
    Appointment, Disruption, Doctor, DoctorUnavailability,
    Patient, ScheduleVersion, SimulationState,
)


def seed_database(db):
    if db.query(Doctor).count() > 0:
        return

    doctors = [
        {"id": "D01", "name": "Dr. Rao", "specialties": ["general"], "shift_start_minute": 0, "shift_end_minute": 480},
        {"id": "D02", "name": "Dr. Sharma", "specialties": ["general"], "shift_start_minute": 0, "shift_end_minute": 480},
        {"id": "D03", "name": "Dr. Shah", "specialties": ["cardiology"], "shift_start_minute": 0, "shift_end_minute": 480},
        {"id": "D04", "name": "Dr. Mehta", "specialties": ["orthopedics"], "shift_start_minute": 0, "shift_end_minute": 480},
        {"id": "D05", "name": "Dr. Nair", "specialties": ["general", "cardiology"], "shift_start_minute": 0, "shift_end_minute": 480},
    ]
    for d in doctors:
        db.add(Doctor(**d, active=True))

    rng = random.Random(42)
    priorities = ["normal"] * 17 + ["urgent"] * 6 + ["emergency"] * 2
    rng.shuffle(priorities)
    specialties_pool = ["general", "general", "general", "cardiology", "cardiology", "orthopedics"]

    for i, priority in enumerate(priorities):
        pid = f"P{101 + i}"
        arrival = rng.randint(0, 240)
        duration = rng.choice([10, 15, 20, 25, 30])
        specialty = rng.choice(specialties_pool)
        db.add(Patient(
            id=pid,
            name=f"Patient {101 + i}",
            priority=priority,
            arrival_minute=arrival,
            appointment_minute=None,
            service_duration_minutes=duration,
            required_specialty=specialty,
            status="waiting",
        ))

    db.add(SimulationState(id="singleton", current_minute=0, speed=1, paused=False, state_version=1))
    db.add(ScheduleVersion(
        version=1,
        created_at=datetime.datetime.utcnow(),
        solver_status="pending",
        objective_value=None,
        trigger="seed",
    ))
    db.commit()


def run_initial_optimization(db, planning_horizon=480):
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

    result = run_optimizer(current_minute, patients_data, doctors_data, [], [], planning_horizon)

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

    sv = db.query(ScheduleVersion).filter(ScheduleVersion.version == current_version).first()
    if sv:
        sv.solver_status = result["solver_status"]
        sv.objective_value = result.get("objective_value")

    db.commit()


def reset_scenario(db, planning_horizon=480):
    """Restore the deterministic scenario from scratch."""
    db.query(Appointment).delete()
    db.query(Disruption).delete()
    db.query(DoctorUnavailability).delete()
    db.query(Patient).delete()
    db.query(Doctor).delete()
    db.query(ScheduleVersion).delete()
    db.query(SimulationState).delete()
    db.commit()

    seed_database(db)
    run_initial_optimization(db, planning_horizon)
