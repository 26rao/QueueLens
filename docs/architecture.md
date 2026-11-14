# QueueLens System Architecture

QueueLens is an intelligent queue optimization and adaptive scheduling system for hospital operations.

---

## High-Level Architecture

```
Internet / User Browser
         |
         v
+-------------------------------------------------------------+
|                     Reverse Proxy (Nginx)                   |
|  - Serves React 18 / Vite Static SPA on /                   |
|  - Routes REST API on /api/*                                |
|  - Proxies WebSockets on /ws                                |
+-------------------------------------------------------------+
         |                                 |
         | (Static Bundle)                 | (API & WS Requests)
         v                                 v
+------------------+             +----------------------------+
|  React Frontend  |             |      FastAPI Backend       |
|  - Tailwind CSS  |             |  - REST Endpoints          |
|  - Recharts      |             |  - Simulation Clock Task   |
|  - WebSocket Hook|             |  - Connection Manager (WS) |
+------------------+             +----------------------------+
                                               |
                     +-------------------------+-------------------------+
                     |                         |                         |
                     v                         v                         v
          +--------------------+    +--------------------+    +--------------------+
          |  OR-Tools CP-SAT   |    |    AI Disruption   |    | SQLite Persistent  |
          |  Optimizer Engine  |    |    Copilot Engine  |    | Storage Engine     |
          |  - Hard Constraints|    |  - Deterministic   |    |  - Patients & Docs |
          |  - Multi-Objective |    |    Regex Parser    |    |  - Appointments    |
          |  - FCFS Fallback   |    |  - Optional LLM    |    |  - Disruptions     |
          |  - Validations     |    |  - Preview Cache   |    |  - Simulation State|
          +--------------------+    +--------------------+    +--------------------+
```

---

## Core Interaction Lifecycle

```
[Observe]
Dashboard loads authoritative hospital state (5 doctors, 25 patients, initial schedule) via GET /api/state.
    │
    ▼
[Disrupt]
Administrator describes an operational disruption in natural language (e.g. "Dr. Rao is unavailable for 60 min and add 2 emergency patients").
    │
    ▼
[Interpret]
AI Disruption Parser translates plain text into validated structured disruption actions (doctor_unavailable, add_emergency, cancel_appointment).
    │
    ▼
[Optimize & Preview]
POST /api/disruptions/preview generates an in-memory candidate state, solves with OR-Tools CP-SAT (multi-objective minimization of weighted wait, lateness, stability, and unscheduled penalty), calculates before/after/baseline metrics, and caches the preview with state_version validation.
    │
    ▼
[Review & Confirm]
Administrator reviews the Impact Comparison (comparing Baseline vs QueueLens optimization) and clicks "Confirm and Apply Schedule".
    │
    ▼
[Commit & Broadcast]
POST /api/disruptions/apply verifies the state version, validates the schedule constraints, atomically commits records in a single database transaction, increments state version, and broadcasts WebSocket event to all connected dashboards.
```

---

## Mathematical Optimization Model (Google OR-Tools CP-SAT)

The scheduler minimizes:

$$\min \sum_{i} w_i W_i + \lambda \sum_{i} D_i + \mu \sum_{i} L_i + \rho \sum_{i} U_i$$

Where:
- $W_i$: Patient waiting time from arrival: $\max(0, \text{start}_i - \text{arrival}_i)$
- $w_i$: Priority weight (Emergency = 100, Urgent = 10, Normal = 1) + aging bonus
- $D_i$: Schedule disturbance penalty: $|\text{start}_i - \text{previous\_start}_i|$
- $L_i$: Appointment lateness delay
- $U_i$: Binary unscheduled indicator with heavy penalty ($\rho = 10,000$)

### Hard Constraints
1. **Unique Assignment:** Schedulable patients assigned to at most 1 doctor.
2. **Specialty Eligibility:** Doctors only treat patients requiring supported specialties.
3. **No-Overlap:** Optional interval variables with `AddNoOverlap` per doctor.
4. **Shift Boundaries:** Appointments must finish within doctor shift minutes (0–480).
5. **Arrival Time:** Start time $\ge$ patient arrival time.
6. **Simulation Horizon:** Start time $\ge$ current simulation minute.
7. **Unavailability Intervals:** Non-overlap with doctor outage windows.
8. **Locked Ongoing Treatments:** In-progress appointments are preserved without disruption.
