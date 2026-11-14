import asyncio
from typing import Optional
from .event_processor import process_simulation_tick

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
            # Check elapsed real seconds for 1 simulated minute
            sleep_time = max(0.1, 60.0 / speed)

            await asyncio.sleep(sleep_time)

            # Re-check state after sleep in case pause/speed was changed
            state_after = await asyncio.get_event_loop().run_in_executor(None, get_current_state)
            if state_after is None or state_after["paused"] or state_after["speed"] == 0:
                continue

            result = await asyncio.get_event_loop().run_in_executor(
                None, advance_simulation_minute, get_db_session
            )

            new_state = await asyncio.get_event_loop().run_in_executor(None, get_current_state)
            if new_state:
                msg = {
                    "type": "simulation_tick",
                    "state_version": new_state["state_version"],
                    "simulation_minute": new_state["current_minute"],
                }
                if result and result.get("processed_events"):
                    msg["events"] = result["processed_events"]
                await event_manager.broadcast(msg)
        except asyncio.CancelledError:
            break
        except Exception:
            await asyncio.sleep(5.0)


def advance_simulation_minute(get_db_session, force_advance: bool = False):
    """
    Advance simulation by 1 minute and execute event processor.
    force_advance=True bypasses pause/speed checks (used by manual +15min API).
    """
    from ..models import SimulationState

    db = get_db_session()
    try:
        sim = db.query(SimulationState).filter(SimulationState.id == "singleton").first()
        if not sim:
            return None
        if not force_advance and (sim.paused or sim.speed == 0):
            return None

        sim.current_minute += 1
        current = sim.current_minute

        result = process_simulation_tick(db, current)
        return result
    finally:
        db.close()


def advance_simulation_batch(get_db_session, minutes: int):
    """Advance simulation sequentially by multiple minutes (e.g. +15 min manual step)."""
    last_result = None
    for _ in range(minutes):
        last_result = advance_simulation_minute(get_db_session, force_advance=True)
    return last_result


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
