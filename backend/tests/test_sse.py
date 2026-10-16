import asyncio
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
from fastapi import HTTPException
import pytest
from backend.app.market_hours import compute_read_time_market_status
from backend.app.schemas.ticker import MarketIndexQuote, TickerSnapshotPayload
from backend.app.security.jwt import generate_stream_ticket
from backend.app.sse import (
    broadcast_quote,
    broadcast_snapshot,
    subscribe_client,
    _active_subscribers,
    _event_ring_buffer
)

KOLKATA = ZoneInfo("Asia/Kolkata")


@pytest.mark.asyncio
async def test_sse_snapshot_broadcast_and_queue_delivery():
    ticket = generate_stream_ticket()
    streaming_resp = await subscribe_client(ticket)
    assert streaming_resp.status_code == 200

    assert len(_active_subscribers) > 0
    client_q = list(_active_subscribers)[-1]

    quotes = [
        MarketIndexQuote(
            symbol="SENSEX",
            name="BSE SENSEX",
            last=73500.0,
            change=250.0,
            pct_change=0.34,
            as_of=datetime.now(timezone.utc).isoformat(),
            source="BSE",
            market_status="open"
        ),
        MarketIndexQuote(
            symbol="NIFTY BANK",
            name="NIFTY BANK",
            last=48000.0,
            change=120.0,
            pct_change=0.25,
            as_of=datetime.now(timezone.utc).isoformat(),
            source="NSE",
            market_status="open"
        )
    ]
    snapshot = TickerSnapshotPayload(
        timestamp=datetime.now(timezone.utc).isoformat(),
        quotes=quotes
    )
    await broadcast_snapshot(snapshot)

    msg = await asyncio.wait_for(client_q.get(), timeout=2.0)
    assert "event: snapshot" in msg
    assert "retry: 5000" in msg
    assert "SENSEX" in msg
    assert "NIFTY BANK" in msg

    _active_subscribers.discard(client_q)


@pytest.mark.asyncio
async def test_sse_mandatory_ticket_enforcement(client):
    # Missing ticket -> 403
    resp_no_ticket = client.get("/api/stream/ticker")
    assert resp_no_ticket.status_code == 403

    # Invalid ticket -> 403
    resp_bad_ticket = client.get("/api/stream/ticker?ticket=invalid_ticket_xyz")
    assert resp_bad_ticket.status_code == 403

    # Generate valid ticket
    ticket = generate_stream_ticket()

    # Direct subscribe with valid ticket succeeds
    streaming_resp = await subscribe_client(ticket)
    assert streaming_resp.status_code == 200
    client_q = list(_active_subscribers)[-1]
    _active_subscribers.discard(client_q)

    # Re-use of the exact same ticket must be rejected with 403 (single-use)
    with pytest.raises(HTTPException) as exc:
        await subscribe_client(ticket)
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_sse_ring_buffer_replay():
    # Broadcast 3 snapshots to fill ring buffer
    for i in range(1, 4):
        q = MarketIndexQuote(
            symbol="NIFTY IT",
            name="NIFTY IT",
            last=35000.0 + i,
            change=10.0 * i,
            pct_change=0.1 * i,
            as_of=datetime.now(timezone.utc).isoformat(),
            source="NSE",
            market_status="open"
        )
        snap = TickerSnapshotPayload(
            timestamp=datetime.now(timezone.utc).isoformat(),
            quotes=[q]
        )
        await broadcast_snapshot(snap)

    assert len(_event_ring_buffer) >= 3
    first_id = _event_ring_buffer[-3][0]

    # Reconnect with Last-Event-ID = first_id
    ticket = generate_stream_ticket()
    streaming_resp = await subscribe_client(ticket, last_event_id=str(first_id))
    client_q = list(_active_subscribers)[-1]

    msg1 = await asyncio.wait_for(client_q.get(), timeout=2.0)
    msg2 = await asyncio.wait_for(client_q.get(), timeout=2.0)
    assert "event: snapshot" in msg1
    assert "event: snapshot" in msg2

    _active_subscribers.discard(client_q)


def test_read_time_market_status_calculation():
    # 1. During market hours: Tuesday 11:30 AM IST
    market_open_time = datetime(2026, 10, 20, 11, 30, 0, tzinfo=KOLKATA)

    # Fresh quote (10 seconds ago) -> open
    fresh_as_of = datetime(2026, 10, 20, 11, 29, 50, tzinfo=KOLKATA)
    assert compute_read_time_market_status(fresh_as_of, current_time=market_open_time) == "open"

    # Stale quote (>40 seconds, e.g. 50s ago) -> stale
    stale_as_of = datetime(2026, 10, 20, 11, 29, 10, tzinfo=KOLKATA)
    assert compute_read_time_market_status(stale_as_of, current_time=market_open_time) == "stale"

    # Holiday stall (>15 minutes ago during market hours) -> closed
    holiday_as_of = datetime(2026, 10, 20, 11, 0, 0, tzinfo=KOLKATA)
    assert compute_read_time_market_status(holiday_as_of, current_time=market_open_time) == "closed"

    # 2. Outside market hours: Saturday noon -> closed
    weekend_time = datetime(2026, 10, 24, 12, 0, 0, tzinfo=KOLKATA)
    assert compute_read_time_market_status(fresh_as_of, current_time=weekend_time) == "closed"

