"""Local-time guard for GitHub's UTC-only scheduled workflow."""

from datetime import datetime
from zoneinfo import ZoneInfo

from .config import SCHEDULED_LOCAL_HOUR, TIMEZONE


def is_scheduled_local_hour(current_time: datetime | None = None) -> bool:
    """Return whether the supplied/current instant is in the target Helsinki hour."""
    local_timezone = ZoneInfo(TIMEZONE)
    current_time = current_time or datetime.now(local_timezone)
    return current_time.astimezone(local_timezone).hour == SCHEDULED_LOCAL_HOUR
