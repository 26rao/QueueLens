# QueueLens — Intelligent Queue Optimization & Adaptive Scheduling System

> **HackGlobal 2026 Hackathon**  
> **Track:** Civic and Real-World Impact  
> **Core Workflow:** Observe → Disrupt → Interpret → Optimize → Preview → Confirm → Update

---

## 1. Problem Statement

Hospitals and outpatient clinics operate with scarce medical resources, unpredictable patient arrivals, and unexpected operational disruptions:
- Doctors are abruptly called away for emergencies or sick leave.
- Emergency patients arrive requiring immediate prioritization.
- Appointments overrun expected durations, triggering compounding delays.

Traditional hospital scheduling systems rely on static, predetermined time slots. When disruptions hit, hospital administrative staff are forced to manually shuffle queues on whiteboards, spreadsheets, or cumbersome multiple-field EHR forms. This leads to:
- Excessive patient waiting times.
- Dangerous delays in emergency appointments.
- Unbalanced workload and poor doctor utilization.
- Zero visibility into the systemic ripple effects of schedule modifications.

---

## 2. Proposed Solution

**QueueLens** is a real-time, AI-assisted hospital scheduling and queue optimization platform. It bridges natural language operational interaction with mathematical constraint programming:

1. **Real-Time Operational Monitoring:** Live patient queues, doctor status, and interactive scheduling timeline across specialties.
2. **AI Disruption Copilot:** Administrators describe operational changes in ordinary language (e.g., *"Dr. Rao is unavailable for 60 minutes and add two emergency patients"*).
3. **Dual-Mode Parsing Engine:** Deterministic regex parsing (works 100% offline without API keys) plus optional LLM-assisted parsing.
4. **Google OR-Tools CP-SAT Constraint Optimization:** Mathematical optimization enforcing hard clinical and resource constraints (specialty matching, non-overlapping appointments, shift bounds, locked active treatments) while minimizing weighted wait times and schedule volatility.
5. **Explainable Impact Comparison:** Before committing, administrators see side-by-side metrics comparing the pre-disruption schedule, naive first-come-first-served baseline under disruption, and the QueueLens optimized schedule.
6. **Atomic State Propagation:** Single-transaction commit with state versioning and instant WebSocket broadcasts to all connected dashboards.

---

## 3. System Architecture

```text
User / Administrator Browser
             │
             ▼
+──────────────────────────────────────────────────────────────+
|                     Nginx Reverse Proxy                      |
|  - Serves React 18 / Vite SPA on /                           |
|  - Routes REST API on /api/*                                 |
|  - Upgrades WebSockets on /ws                                |
+──────────────────────────────────────────────────────────────+
             │                                   │
             ▼                                   ▼
+────────────────────────+           +─────────────────────────+
|     React Frontend     |           |     FastAPI Backend     |
|  - Tailwind CSS        |           |  - REST Endpoints       |
|  - Lucide Icons        |           |  - WebSocket Manager    |
|  - Recharts Analytics  |           |  - Simulation Clock     |
+────────────────────────+           +─────────────────────────+
                                                  │
                 ┌────────────────────────────────┼────────────────────────────────┐
                 ▼                                ▼                                ▼
    +────────────────────────+       +────────────────────────+       +────────────────────────+
    |   OR-Tools CP-SAT      |       |   AI Disruption Parser |       |   SQLite Database      |
    |   Constraint Solver    |       |   - Deterministic      |       |   - Doctors & Shifts   |
    |   - Hard Constraints   |       |   - Optional LLM       |       |   - Patients & Queues  |
    |   - Multi-Objective    |       |   - Preview Cache      |       |   - Appointments       |
    |   - Fallback FCFS      |       |   - Conflict Detection |       |   - Disruptions Log    |
    +────────────────────────+       +────────────────────────+       +────────────────────────+
```

---

## 4. Key Features

- **Multi-Doctor & Specialty Support:** Pre-configured with 5 doctors across General Medicine, Cardiology, and Orthopedics.
- **Dynamic Capacity Management:** Handles temporary doctor outages with exact minute intervals.
- **Triage Priority Weighting:** Emergency ($w=100$), Urgent ($w=10$), Normal ($w=1$) with waiting-time aging anti-starvation mechanisms.
- **Interactive CSS Gantt/Timeline:** Real-time visual timeline mapping doctor shifts, unavailability blocks, and appointments.
- **Disruption Simulation Controls:** Speed controls (1x, 5x, 15x), step forward (+15 min), pause/resume, and one-click scenario reset.
- **Stale Preview Concurrency Protection:** State version verification rejects outdated or concurrent mutation conflicts (HTTP 409).

---

## 5. Technology Stack

| Component | Technology | Rationale |
|---|---|---|
| **Frontend** | React 18, Vite, TypeScript | Fast, type-safe interactive UI |
| **Styling** | Tailwind CSS v4, Lucide React | High-density healthcare dashboard theme |
| **Analytics** | Recharts | Responsive waiting time & doctor utilization charts |
| **Backend** | Python 3.11+, FastAPI, Uvicorn | Async REST APIs & WebSockets |
| **Optimization** | Google OR-Tools CP-SAT | Industrial-strength constraint satisfaction solver |
| **Database** | SQLite + SQLAlchemy 2.0 | Persistent, zero-maintenance relational storage |
| **AI Parsing** | Deterministic Regex + Optional OpenAI API | 100% offline functionality with optional LLM enhancements |
| **Reverse Proxy** | Nginx | Single-port routing for frontend, API, and WebSockets |
| **Deployment** | Docker & Docker Compose | Single-command deployment on Vultr Compute |

---

## 6. Measured Benchmark Results

All benchmark scenarios below were **measured directly** from the seeded hospital scenario (5 doctors, 25 patients) comparing the QueueLens CP-SAT solver against a standard FCFS baseline under identical constraints:

| Scenario | Baseline Wait | QueueLens Wait | Wait Time Reduction | Solver Status | Runtime |
|---|---|---|---|---|---|
| **1. Normal Operations** | 8.5 min | 0.6 min | **+92.9%** | OPTIMAL | 184 ms |
| **2. Single Doctor Outage** (60 min) | 11.0 min | 0.6 min | **+94.5%** | OPTIMAL | 250 ms |
| **3. Emergency Surge** (+2 Emergency) | 7.5 min | 1.3 min | **+82.7%** | OPTIMAL | 311 ms |
| **4. Compound Disruption** (2 Doctors Out + Emergencies) | 44.7 min | 8.3 min | **+81.4%** | FEASIBLE | 2,166 ms |

*See [docs/benchmark-results.md](docs/benchmark-results.md) for detailed breakdowns.*

---

## 7. Local Setup & Quickstart

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+

### Step 1: Clone Repository
```bash
git clone https://github.com/YOUR_USERNAME/queuelens.git
cd queuelens
```

### Step 2: Backend Setup
```bash
cd backend
python -m venv .venv

# On Windows:
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --port 8000
```
Backend will be available at `http://localhost:8000`. Test via:
- Health check: `http://localhost:8000/api/health`
- Swagger UI docs: `http://localhost:8000/docs`

### Step 3: Frontend Setup
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
Frontend development server will open at `http://localhost:5173`.

---

## 8. Docker & Vultr Deployment

QueueLens is fully containerized using Docker Compose for single-instance deployment on **Vultr Cloud Compute** (Ubuntu 22.04 / 24.04 LTS).

### Environment Configuration (`.env`)
Create a `.env` file at repository root (or copy from `.env.example`):
```dotenv
APP_ENV=production
DATABASE_URL=sqlite:////app/data/queuelens.db
PLANNING_HORIZON=480
CORS_ORIGINS=*
LLM_ENABLED=false
LLM_API_KEY=
LLM_BASE_URL=
LLM_MODEL=
```

### One-Command Deployment
```bash
docker compose up -d --build
```

Verify deployment:
```bash
docker compose ps
curl http://localhost/api/health
```

Access the dashboard at `http://<YOUR_VULTR_IP>/`.

---

## 9. Running Tests

QueueLens includes comprehensive unit and integration tests covering the CP-SAT optimizer, disruption parsing, metric calculations, and API endpoints:

```bash
cd backend
.venv\Scripts\pytest -v
```

**Test Coverage Summary:**
- `test_scheduler.py`: Non-overlapping appointments, specialty eligibility, shift constraints, locked active appointments, unscheduled reporting, fallback engine, and independent schedule validator.
- `test_disruptions.py`: Deterministic parser for doctor outage, doctor availability recovery, emergency arrivals, appointment cancellations, and compound instructions.
- `test_metrics.py`: Waiting time computations, priority breakdowns, doctor utilization formulas.
- `test_api.py`: `/api/health`, `/api/state`, `/api/reset`, and disruption preview/apply endpoints.

---

## 10. Scope & Disclaimer

> [!IMPORTANT]
> QueueLens is a hackathon prototype developed for **HackGlobal 2026** using synthetic hospital operational data. It is **not** a validated medical triage device or clinical decision-support system. Clinical urgency categories are supplied as external inputs. Production deployment would require hospital EHR integrations (HL7/FHIR), user authentication (OAuth2/SSO), and clinical validation.

---

## 11. Credits & Acknowledgements

- **Mathematical Optimization:** Google OR-Tools CP-SAT Team
- **Frameworks:** FastAPI, React, Vite, Tailwind CSS, Recharts
- **Icons:** Lucide React
- **Cloud Infrastructure:** Vultr Cloud Compute
