from datetime import datetime
from zoneinfo import ZoneInfo
from backend.app.market_hours import is_market_hours, evaluate_market_status

KOLKATA = ZoneInfo("Asia/Kolkata")


def test_market_hours_weekday_open():
    # Tuesday 11:30 AM IST -> Open
    tue_trading = datetime(2026, 10, 20, 11, 30, tzinfo=KOLKATA)
    assert is_market_hours(tue_trading) is True


def test_market_hours_weekend_closed():
    # Saturday 11:30 AM IST -> Closed
    sat_noon = datetime(2026, 10, 24, 11, 30, tzinfo=KOLKATA)
    assert is_market_hours(sat_noon) is False

    # Sunday -> Closed
    sun_noon = datetime(2026, 10, 25, 11, 30, tzinfo=KOLKATA)
    assert is_market_hours(sun_noon) is False


def test_market_hours_after_hours_closed():
    # Wednesday 17:00 IST -> Closed
    wed_after = datetime(2026, 10, 21, 17, 0, tzinfo=KOLKATA)
    assert is_market_hours(wed_after) is False

    # Wednesday 08:30 IST -> Before open
    wed_before = datetime(2026, 10, 21, 8, 30, tzinfo=KOLKATA)
    assert is_market_hours(wed_before) is False


def test_market_hours_holiday_stall_detection():
    # In trading hours (10:30 AM IST), but upstream quote was timestamped at 09:30 AM (>15 min stall)
    now_ist = datetime(2026, 10, 20, 10, 30, tzinfo=KOLKATA)
    stalled_as_of = datetime(2026, 10, 20, 9, 30, tzinfo=KOLKATA)
    status = evaluate_market_status(stalled_as_of, current_time=now_ist)
    assert status == "closed"


def test_market_hours_fresh_quote():
    now_ist = datetime(2026, 10, 20, 10, 30, tzinfo=KOLKATA)
    fresh_as_of = datetime(2026, 10, 20, 10, 28, tzinfo=KOLKATA)
    status = evaluate_market_status(fresh_as_of, current_time=now_ist)
    assert status == "open"
