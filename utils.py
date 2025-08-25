from datetime import datetime, timezone

def to_sc_ts(dt: datetime) -> str:
    dt = dt.astimezone(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def now_ts() -> str:
    now = datetime.now(timezone.utc)
    return to_sc_ts(now)
