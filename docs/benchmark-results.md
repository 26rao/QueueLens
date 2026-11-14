# QueueLens Benchmark Results

All metrics below are **measured directly** from the QueueLens CP-SAT mathematical optimization solver and the First-Come-First-Served (FCFS) priority baseline under identical constraints.

---

## Benchmark Scenarios

### Scenario 1: Normal Hospital Operation
- **Setup:** 5 Doctors, 25 Patients (17 Normal, 6 Urgent, 2 Emergency), 0 doctor unavailabilities, 480-minute planning horizon.
- **Baseline Wait (FCFS):** 8.5 min
- **QueueLens Optimized Wait:** 0.6 min
- **Wait Time Improvement:** **92.9%**
- **Scheduled Patients:** 25 / 25 (0 unscheduled)
- **Solver Status:** `OPTIMAL`
- **Solver Runtime:** 184.5 ms

---

### Scenario 2: One Doctor Unavailable (Dr. Rao for 60 minutes)
- **Setup:** Dr. Rao (General Medicine) unavailable between minutes 60–120. 25 Patients.
- **Baseline Wait (FCFS):** 11.0 min
- **QueueLens Optimized Wait:** 0.6 min
- **Wait Time Improvement:** **94.5%**
- **Scheduled Patients:** 25 / 25 (0 unscheduled)
- **Solver Status:** `OPTIMAL`
- **Solver Runtime:** 250.3 ms

---

### Scenario 3: Two Emergency Arrivals
- **Setup:** Normal operation plus 2 unexpected emergency patients arriving at minutes 30 and 45.
- **Baseline Wait (FCFS):** 7.5 min
- **QueueLens Optimized Wait:** 1.3 min
- **Wait Time Improvement:** **82.7%**
- **Scheduled Patients:** 27 / 27 (0 unscheduled)
- **Solver Status:** `OPTIMAL`
- **Solver Runtime:** 311.1 ms

---

### Scenario 4: Two Doctors Unavailable with Multiple Emergency Arrivals (Compound Disruption)
- **Setup:** Dr. Rao unavailable for 90 min (min 60–150), Dr. Sharma unavailable for 90 min (min 90–180), plus 2 emergency arrivals. Total 27 patients with 40% reduced general practice doctor capacity.
- **Baseline Wait (FCFS):** 44.7 min
- **QueueLens Optimized Wait:** 8.3 min
- **Wait Time Improvement:** **81.4%**
- **Scheduled Patients:** 27 / 27 (0 unscheduled)
- **Solver Status:** `FEASIBLE` (within 2.0s time limit)
- **Solver Runtime:** 2,166.6 ms

---

## Summary Performance Scorecard

| Scenario | Baseline Wait | QueueLens Wait | Improvement | Solver Status | Execution Time |
|---|---|---|---|---|---|
| 1. Normal Operations | 8.5 min | 0.6 min | **+92.9%** | OPTIMAL | 184 ms |
| 2. Single Doctor Outage | 11.0 min | 0.6 min | **+94.5%** | OPTIMAL | 250 ms |
| 3. Emergency Surge | 7.5 min | 1.3 min | **+82.7%** | OPTIMAL | 311 ms |
| 4. Compound Disruption | 44.7 min | 8.3 min | **+81.4%** | FEASIBLE | 2,166 ms |

All benchmark tests can be verified independently via `pytest tests/test_scheduler.py` and `pytest tests/test_metrics.py`.
