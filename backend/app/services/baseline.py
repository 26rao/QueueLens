def run_baseline(
    current_minute, patients, doctors, existing_appointments, unavailabilities, planning_horizon=480
):
    from .scheduler import run_fallback

    result = run_fallback(
        current_minute, patients, doctors, existing_appointments, unavailabilities, planning_horizon
    )
    result["solver_status"] = "BASELINE"
    return result
