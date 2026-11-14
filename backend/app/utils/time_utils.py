def minute_to_time_str(minute: int) -> str:
    """Convert simulation minute to HH:MM string (starting from 08:00)."""
    base_hour = 8
    total_minutes = base_hour * 60 + minute
    h = total_minutes // 60
    m = total_minutes % 60
    return f"{h:02d}:{m:02d}"


def time_str_to_minute(time_str: str) -> int:
    """Convert HH:MM to simulation minute."""
    h, m = map(int, time_str.split(":"))
    return (h - 8) * 60 + m
