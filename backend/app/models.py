import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, JSON
from .database import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    specialties = Column(JSON, nullable=False, default=list)
    shift_start_minute = Column(Integer, nullable=False, default=0)
    shift_end_minute = Column(Integer, nullable=False, default=480)
    active = Column(Boolean, nullable=False, default=True)


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    priority = Column(String, nullable=False, default="normal")
    arrival_minute = Column(Integer, nullable=False, default=0)
    appointment_minute = Column(Integer, nullable=True)
    service_duration_minutes = Column(Integer, nullable=False, default=15)
    required_specialty = Column(String, nullable=False, default="general")
    status = Column(String, nullable=False, default="waiting")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(String, ForeignKey("doctors.id"), nullable=False)
    start_minute = Column(Integer, nullable=False)
    end_minute = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="scheduled")
    schedule_version = Column(Integer, nullable=False, default=1)


class DoctorUnavailability(Base):
    __tablename__ = "doctor_unavailabilities"

    id = Column(String, primary_key=True)
    doctor_id = Column(String, ForeignKey("doctors.id"), nullable=False)
    start_minute = Column(Integer, nullable=False)
    end_minute = Column(Integer, nullable=False)
    reason = Column(String, nullable=True)


class Disruption(Base):
    __tablename__ = "disruptions"

    id = Column(String, primary_key=True)
    action_type = Column(String, nullable=False)
    payload_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    simulation_minute = Column(Integer, nullable=False, default=0)
    schedule_version_before = Column(Integer, nullable=True)
    schedule_version_after = Column(Integer, nullable=True)
    original_text = Column(String, nullable=True)


class SimulationState(Base):
    __tablename__ = "simulation_state"

    id = Column(String, primary_key=True, default="singleton")
    current_minute = Column(Integer, nullable=False, default=0)
    speed = Column(Integer, nullable=False, default=1)
    paused = Column(Boolean, nullable=False, default=False)
    state_version = Column(Integer, nullable=False, default=1)


class ScheduleVersion(Base):
    __tablename__ = "schedule_versions"

    version = Column(Integer, primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    solver_status = Column(String, nullable=False)
    objective_value = Column(Float, nullable=True)
    trigger = Column(String, nullable=False)


class SyntheticEvent(Base):
    __tablename__ = "synthetic_events"

    id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False)
    simulation_minute = Column(Integer, nullable=False)
    description = Column(String, nullable=False)
    payload_json = Column(JSON, nullable=False)
    status = Column(String, nullable=False, default="pending")
    state_version = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)


class SyntheticGeneratorState(Base):
    __tablename__ = "synthetic_generator_state"

    id = Column(String, primary_key=True, default="singleton")
    enabled = Column(Boolean, nullable=False, default=False)
    mode = Column(String, nullable=False, default="manual")
    seed = Column(Integer, nullable=False, default=42)
    next_event_index = Column(Integer, nullable=False, default=0)
    last_processed_minute = Column(Integer, nullable=False, default=0)

