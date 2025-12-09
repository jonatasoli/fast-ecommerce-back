from datetime import datetime, timedelta, timezone
from typing import Optional

BACKOFF_SCHEDULE = [300, 600, 1200]


def get_backoff_delay(attempts: int) -> Optional[int]:
    """Return delay in seconds for a given attempt, or None if exhausted."""
    return BACKOFF_SCHEDULE[attempts] if attempts < len(BACKOFF_SCHEDULE) else None


def is_job_expired(
    updated_at: datetime,
    *,
    days: int = 7,
    now: Optional[datetime] = None,
) -> bool:
    """Check if a job updated_at is older than retention window."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    return updated_at < cutoff
