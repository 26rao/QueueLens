import asyncio
from typing import Optional

_simulation_task: Optional[asyncio.Task] = None
_running = False


async def simulation_loop(get_db_session, event_manager, get_current_state):
    global _running
    _running = True

    while _running:
        try:
            state = await asyncio.get_event_loop().run_in_executor(None, get_current_state)
            if state is None or state["paused"] or state["speed"] == 0:
                await asyncio.sleep(1.0)
                continue

            speed = state["speed"]
            sleep_time = 60.0 / speed  # real seconds for 1 simulated minute

            await asyncio.sleep(sleep_time)

            await asyncio.get_event_loop().run_in_executor(
                None, advance_simulation_minute, get_db_session
            )

            new_state = await asyncio.get_event_loop().run_in_executor(None, get_current_state)
            if new_state:
                await event_manager.broadcast({
                    "type": "simulation_tick",
                    "state_version": new_state["state_version"],
                    "simulation_minute": new_state["current_minute"],
                })
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(5.0)


def advance_simulation_minute(get_db_session):
    from ..models import Appointment, Patient, SimulationState

    db = get_db_session()
    try:
        sim = db.query(SimulationState).filter(SimulationState.id == "singleton").first()
        if not sim or sim.paused or sim.speed == 0:
            return

        sim.current_minute += 1
        current = sim.current_minute

        appts = db.query(Appointment).filter(
            Appointment.status.in_(["scheduled", "in_progress"])
        ).all()

        for appt in appts:
            if appt.status == "scheduled" and appt.start_minute <= current:
                appt.status = "in_progress"
            elif appt.status == "in_progress" and appt.end_minute <= current:
                appt.status = "completed"
                patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
                if patient:
                    patient.status = "completed"

        db.commit()
    finally:
        db.close()


def start_simulation(get_db_session, event_manager, get_current_state):
    global _simulation_task
    loop = asyncio.get_event_loop()
    _simulation_task = loop.create_task(
        simulation_loop(get_db_session, event_manager, get_current_state)
    )


def stop_simulation():
    global _simulation_task, _running
    _running = False
    if _simulation_task:
        _simulation_task.cancel()
        _simulation_task = None
