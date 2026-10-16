from datetime import datetime, time as dtime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")
MARKET_OPEN_TIME = dtime(9, 15)
MARKET_CLOSE_TIME = dtime(15, 30)


def get_current_ist_time() -> datetime:
    """Return current datetime in Asia/Kolkata timezone."""
    return datetime.now(KOLKATA_TZ)


def is_market_hours(dt: Optional[datetime] = None) -> bool:
    """Check whether the given or current time falls within Indian equity trading hours:

    Monday through Friday between 09:15 and 15:30 IST.
    """
    if dt is None:
        ist_now = get_current_ist_time()
    else:
        if dt.tzinfo is None:
            ist_now = dt.replace(tzinfo=timezone.utc).astimezone(KOLKATA_TZ)
        else:
            ist_now = dt.astimezone(KOLKATA_TZ)

    # Monday is 0, Sunday is 6
    if ist_now.weekday() >= 5:  # Saturday or Sunday
        return False

    current_t = ist_now.time()
    return MARKET_OPEN_TIME <= current_t <= MARKET_CLOSE_TIME


def evaluate_market_status(
    upstream_as_of: Optional[datetime] = None,
    current_time: Optional[datetime] = None
) -> str:
    """Determine market status ('open', 'closed', 'stale').

    Per Decision D11: Holidays are detected if upstream timestamp fails to advance during market hours.
    """
    ist_now = current_time or get_current_ist_time()
    if not is_market_hours(ist_now):
        return "closed"

    if upstream_as_of is None:
        return "closed"

    # Normalize upstream timestamp to IST
    if upstream_as_of.tzinfo is None:
        upstream_ist = upstream_as_of.replace(tzinfo=timezone.utc).astimezone(KOLKATA_TZ)
    else:
        upstream_ist = upstream_as_of.astimezone(KOLKATA_TZ)

    # If during trading hours, the quote timestamp has not updated for > 15 minutes,
    # treat as market holiday or feed closed.
    stall_delta = ist_now - upstream_ist
    if stall_delta.total_seconds() > 900:  # 15 minutes
        return "closed"

    return "open"


def compute_read_time_market_status(
    as_of: Optional[datetime],
    current_time: Optional[datetime] = None
) -> str:
    """Compute read-time market status (open, closed, stale) per Decision I5:

    - not in market hours -> "closed" (CLOSED badge)
    - open & fresh (age <= 40s during market hours) -> "open" (LIVE badge)
    - holiday stall (> 15m without update during market hours) -> "closed"
    - stale (> 40s without update during market hours) -> "stale" (STALE badge)
    """
    ist_now = current_time or get_current_ist_time()
    if not is_market_hours(ist_now):
        return "closed"

    if as_of is None:
        return "closed"

    if as_of.tzinfo is None:
        as_of_ist = as_of.replace(tzinfo=timezone.utc).astimezone(KOLKATA_TZ)
    else:
        as_of_ist = as_of.astimezone(KOLKATA_TZ)

    age_sec = (ist_now - as_of_ist).total_seconds()

    if age_sec > 900:  # 15 min stall during market hours -> holiday/feed stopped
        return "closed"
    if age_sec > 40:  # > 2x 20s interval -> STALE
        return "stale"
    return "open"


