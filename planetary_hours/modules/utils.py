from datetime import datetime, timezone

def get_time(date: str) -> datetime:
    try:
        return datetime.strptime(date, "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid date format '{date}', expected YYYY-MM-DD") from e