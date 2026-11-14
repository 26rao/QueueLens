export type Priority = 'emergency' | 'urgent' | 'normal';
export type PatientStatus = 'waiting' | 'scheduled' | 'in_progress' | 'completed' | 'cancelled' | 'unscheduled';
export type AppointmentStatus = 'scheduled' | 'in_progress' | 'completed' | 'cancelled';

export interface Patient {
  id: string;
  name: string;
  priority: Priority;
  arrival_minute: number;
  appointment_minute: number | null;
  service_duration_minutes: number;
  required_specialty: string;
  status: PatientStatus;
}

export interface Doctor {
  id: string;
  name: string;
  specialties: string[];
  shift_start_minute: number;
  shift_end_minute: number;
  active: boolean;
  unavailabilities: Unavailability[];
}

export interface Unavailability {
  id: string;
  doctor_id: string;
  start_minute: number;
  end_minute: number;
  reason: string;
}

export interface Appointment {
  id: string;
  patient_id: string;
  doctor_id: string;
  start_minute: number;
  end_minute: number;
  status: AppointmentStatus;
  schedule_version: number;
}

export interface Metrics {
  avg_wait: number;
  median_wait: number;
  max_wait: number;
  avg_wait_by_priority: Record<string, number>;
  scheduled_count: number;
  unscheduled_count: number;
  doctor_utilization: Record<string, number>;
  total_patients: number;
}

export interface SimulationState {
  current_minute: number;
  speed: number;
  paused: boolean;
}

export interface DashboardState {
  state_version: number;
  solver_status?: string;
  simulation: SimulationState;
  patients: Patient[];
  doctors: Doctor[];
  appointments: Appointment[];
  metrics: Metrics;
  alerts: Alert[];
}

export interface Alert {
  type: string;
  payload: Record<string, unknown>;
  minute: number;
}

export interface DisruptionAction {
  type: string;
  doctor_id?: string;
  duration_minutes?: number;
  count?: number;
  required_specialty?: string;
  appointment_id?: string;
}

export interface PreviewResponse {
  preview_id: string;
  base_state_version: number;
  solver_status: string;
  before_metrics: Metrics;
  after_metrics: Metrics;
  baseline_metrics: Metrics;
  proposed_appointments: Appointment[];
  affected_patients: string[];
  unscheduled_patients: string[];
}
