# QueueLens Demonstration Script (90-Second Walkthrough)

**Project:** QueueLens — Intelligent Queue Optimization & Adaptive Scheduling System  
**Target Duration:** 75–90 seconds

---

## 00:00 – 00:20: Opening & Problem Statement

> *"In real hospitals, static appointment schedules break constantly. A doctor is called away, two critical emergency patients arrive, and appointments overrun. Today, staff are forced to manually shuffle queues on whiteboards or static spreadsheets—leading to delayed emergencies, excessive patient waiting, and burned-out doctors.*
>
> *QueueLens solves this with AI-assisted operational disruption handling and mathematical constraint optimization."*

---

## 00:20 – 00:45: Live Dashboard Overview

> *(Screen: Navigate to the QueueLens Dashboard)*
>
> *"Here is our live Hospital Operations Command Center. We are monitoring 5 doctors across General Medicine, Cardiology, and Orthopedics, and 25 patients with varying arrival times and clinical priorities.*
>
> *Notice our Schedule Timeline: each doctor's shift is laid out from 08:00 to 16:00, with appointments color-coded by clinical urgency: Red for Emergency, Amber for Urgent, and Teal for Normal."*

---

## 00:45 – 01:10: Simulating a Real-World Hospital Disruption

> *(Screen: Click Disruption Copilot example or type)*
>
> *"Now let's simulate an operational emergency: **'Dr. Rao and Dr. Sharma are unavailable for 60 minutes. Add two emergency patients.'**
>
> *We click 'Parse'. The AI copilot extracts structured actions with zero manual form-filling: recording the two doctor outages and creating the two incoming emergency cases.*
>
> *Next, we click 'Preview Schedule Impact'. Under the hood, Google OR-Tools CP-SAT solves the multi-objective optimization problem in milliseconds, respecting specialty qualifications, non-overlapping slots, shift boundaries, and locked ongoing treatments."*

---

## 01:10 – 01:30: Explainable Impact Comparison & Live Commit

> *(Screen: Point to the Impact Preview card)*
>
> *"QueueLens gives administrators transparent, explainable decisions. Look at our comparison table: under a naive first-come, first-served queue, average wait times would surge to over 44 minutes. With QueueLens mathematical optimization, average wait time is kept to just 8.3 minutes—an **81% reduction in patient waiting time**, while ensuring 100% of emergency cases are prioritized.*
>
> *The administrator clicks 'Confirm and Apply Schedule'. The changes are atomically committed, and all connected browser sessions and side-by-side monitors update via WebSockets instantly."*

---

## 01:30+: Closing

> *"QueueLens bridges natural language operational control with mathematical constraint programming to keep hospitals running smoothly during unpredictable emergencies. Thank you."*
