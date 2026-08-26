from datetime import datetime, timezone

STALE_THRESHOLD_DAYS = 730


def is_stale(go_live_date: str | None) -> bool | None:
    if not go_live_date:
        return None

    parsed = datetime.strptime(go_live_date, "%Y-%m-%dT%H:%M:%S.%f")
    age_days = (datetime.now(timezone.utc) - parsed.replace(tzinfo=timezone.utc)).days
    return age_days > STALE_THRESHOLD_DAYS
