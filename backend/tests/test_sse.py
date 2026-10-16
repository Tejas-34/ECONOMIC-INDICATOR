import asyncio
from datetime import datetime, timezone
import pytest
from backend.app.schemas.ticker import MarketIndexQuote
from backend.app.security.jwt import generate_stream_ticket
from backend.app.sse import (
    broadcast_quote,
    subscribe_client,
    _active_subscribers,
    _event_ring_buffer
)


@pytest.mark.asyncio
async def test_sse_quote_broadcast_and_queue_delivery():
    ticket = generate_stream_ticket()
    # Subscribe client
    streaming_resp = await subscribe_client(ticket)
    assert streaming_resp.status_code == 200

    # Ensure client queue was registered
    assert len(_active_subscribers) > 0
    client_q = list(_active_subscribers)[0]

    # Broadcast a quote
    quote = MarketIndexQuote(
        symbol="SENSEX",
        name="BSE SENSEX",
        last=73500.0,
        change=250.0,
        pct_change=0.34,
        as_of=datetime.now(timezone.utc).isoformat(),
        source="BSE",
        market_status="open"
    )
    await broadcast_quote(quote)

    # Check client queue received event
    msg = await asyncio.wait_for(client_q.get(), timeout=2.0)
    assert "event: quote" in msg
    assert "SENSEX" in msg
    assert "73500" in msg

    # Cleanup
    _active_subscribers.discard(client_q)


@pytest.mark.asyncio
async def test_sse_ring_buffer_replay():
    # Broadcast 3 quotes to fill ring buffer
    for i in range(1, 4):
        q = MarketIndexQuote(
            symbol="NIFTY BANK",
            name="NIFTY BANK",
            last=46000.0 + i,
            change=10.0 * i,
            pct_change=0.1 * i,
            as_of=datetime.now(timezone.utc).isoformat(),
            source="NSE",
            market_status="open"
        )
        await broadcast_quote(q)

    # Capture last event ID
    assert len(_event_ring_buffer) >= 3
    first_id = _event_ring_buffer[-3][0]

    # New client connects with Last-Event-ID = first_id (should receive remaining 2)
    ticket = generate_stream_ticket()
    streaming_resp = await subscribe_client(ticket, last_event_id=str(first_id))
    client_q = list(_active_subscribers)[-1]

    # Expect at least 2 replayed events
    msg1 = await asyncio.wait_for(client_q.get(), timeout=2.0)
    msg2 = await asyncio.wait_for(client_q.get(), timeout=2.0)
    assert "event: quote" in msg1
    assert "event: quote" in msg2

    # Cleanup
    _active_subscribers.discard(client_q)
