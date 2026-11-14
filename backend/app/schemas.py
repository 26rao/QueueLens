import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DoctorUnavailabilityRead(BaseModel):
    id: str
    doctor_id: str
    start_minute: int
    end_minute: int
    reason: Optional[str] = None

    model_config = {"from_attributes": True}


class DoctorRead(BaseModel):
    id: str
    name: str
    specialties: List[str]
    shift_start_minute: int
    shift_end_minute: int
    active: bool
    unavailabilities: List[DoctorUnavailabilityRead] = []

    model_config = {"from_attributes": True}


class PatientRead(BaseModel):
    id: str
    name: str
    priority: str
    arrival_minute: int
    appointment_minute: Optional[int] = None
    service_duration_minutes: int
    required_specialty: str
    status: str

    model_config = {"from_attributes": True}


class PatientCreate(BaseModel):
    id: Optional[str] = None
    name: str
    priority: str
    arrival_minute: int
    service_duration_minutes: int
    required_specialty: str


class AppointmentRead(BaseModel):
    id: str
    patient_id: str
    doctor_id: str
    start_minute: int
    end_minute: int
    status: str
    schedule_version: int

    model_config = {"from_attributes": True}


class DisruptionAction(BaseModel):
    type: str
    doctor_id: Optional[str] = None
    duration_minutes: Optional[int] = None
    count: Optional[int] = None
    required_specialty: Optional[str] = None
    appointment_id: Optional[str] = None


class ParseRequest(BaseModel):
    text: str


class ParseResponse(BaseModel):
    actions: List[Dict[str, Any]]
    parser_mode: str


class PreviewRequest(BaseModel):
    actions: List[DisruptionAction]
    expected_state_version: int


class MetricsRead(BaseModel):
    avg_wait: float
    median_wait: float
    max_wait: float
    avg_wait_by_priority: Dict[str, float]
    scheduled_count: int
    unscheduled_count: int
    doctor_utilization: Dict[str, float]
    total_patients: int


class PreviewResponse(BaseModel):
    preview_id: str
    base_state_version: int
    solver_status: str
    before_metrics: Dict[str, Any]
    after_metrics: Dict[str, Any]
    baseline_metrics: Dict[str, Any]
    proposed_appointments: List[Dict[str, Any]]
    affected_patients: List[str]
    unscheduled_patients: List[str]


class ApplyRequest(BaseModel):
    preview_id: str
    expected_state_version: int


class SimulationRead(BaseModel):
    current_minute: int
    speed: int
    paused: bool


class DashboardState(BaseModel):
    state_version: int
    simulation: SimulationRead
    patients: List[PatientRead]
    doctors: List[DoctorRead]
    appointments: List[AppointmentRead]
    metrics: MetricsRead
    alerts: List[Dict[str, Any]]


class OptimizeResponse(BaseModel):
    solver_status: str
    scheduled_count: int
    unscheduled_count: int
    objective_value: Optional[float] = None
    execution_time_ms: float
    state_version: int


class SyntheticEventRead(BaseModel):
    id: str
    event_type: str
    simulation_minute: int
    description: str
    payload_json: Dict[str, Any]
    status: str
    state_version: Optional[int] = None
    created_at: Optional[datetime.datetime] = None


class EventListResponse(BaseModel):
    events: List[SyntheticEventRead]
    mode: str
    enabled: bool


class SimulationModeRequest(BaseModel):
    mode: str  # manual, live_synthetic, replay
    enabled: Optional[bool] = None

