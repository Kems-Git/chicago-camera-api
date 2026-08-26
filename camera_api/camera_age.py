from datetime import datetime, timezone

RECENT_THRESHOLD_DAYS = 730


def is_recently_installed(go_live_date: str | None) -> bool | None:
    if not go_live_date:
        return None

    parsed = datetime.strptime(go_live_date, "%Y-%m-%dT%H:%M:%S.%f")
    age_days = (datetime.now(timezone.utc) - parsed.replace(tzinfo=timezone.utc)).days
    return age_days <= RECENT_THRESHOLD_DAYS
