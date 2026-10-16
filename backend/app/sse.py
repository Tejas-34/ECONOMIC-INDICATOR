import asyncio
from collections import deque
import json
from pathlib import Path
from typing import AsyncGenerator, Dict, List, Optional, Set, Tuple
from fastapi import HTTPException, Response, status
from fastapi.responses import StreamingResponse
from backend.app.schemas.ticker import MarketIndexQuote, TickerSnapshotPayload
from backend.app.security.jwt import consume_stream_ticket

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"

# Monotonic event ID counter
_current_event_id: int = 0

# Ring buffer of the last 50 events for Last-Event-ID reconnection replay
# Stores tuples of (event_id: int, event_type: str, data_json: str)
_event_ring_buffer: deque[Tuple[int, str, str]] = deque(maxlen=50)

# Active subscriber queues: queue -> set of queues
_active_subscribers: Set[asyncio.Queue] = set()
_broadcaster_lock = asyncio.Lock()


async def broadcast_quote(quote: MarketIndexQuote) -> None:
    """Format and broadcast a new index quote event to all active SSE subscribers."""
    global _current_event_id
    _current_event_id += 1
    event_id = _current_event_id
    data_json = json.dumps(quote.model_dump())

    # Record in 50-event ring buffer for reconnection replay
    _event_ring_buffer.append((event_id, "quote", data_json))

    formatted_event = f"id: {event_id}\nevent: quote\ndata: {data_json}\n\n"

    # Broadcast to all connected clients
    for q in list(_active_subscribers):
        if q.full():
            try:
                q.get_nowait()  # Drop oldest event on congestion
            except asyncio.QueueEmpty:
                pass
        try:
            q.put_nowait(formatted_event)
        except asyncio.QueueFull:
            pass


async def subscribe_client(ticket: str, last_event_id: Optional[str] = None) -> StreamingResponse:
    """Validate single-use ticket and return an SSE StreamingResponse with heartbeat and replay."""
    # Verify and immediately consume ticket
    if not consume_stream_ticket(ticket):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or expired stream ticket"
        )

    client_queue: asyncio.Queue[str] = asyncio.Queue(maxsize=100)
    _active_subscribers.add(client_queue)

    # Replay missed events from ring buffer if Last-Event-ID was supplied
    if last_event_id:
        try:
            last_id_int = int(last_event_id)
            for eid, etype, edata in list(_event_ring_buffer):
                if eid > last_id_int:
                    replay_msg = f"id: {eid}\nevent: {etype}\ndata: {edata}\n\n"
                    await client_queue.put(replay_msg)
        except ValueError:
            pass

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            while True:
                try:
                    # Wait up to 15 seconds for next quote event, then emit heartbeat ping
                    msg = await asyncio.wait_for(client_queue.get(), timeout=15.0)
                    yield msg
                except asyncio.TimeoutError:
                    # 15-second heartbeat comment
                    yield ": ping\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            _active_subscribers.discard(client_queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


async def mock_event_generator() -> AsyncGenerator[str, None]:
    """Generates periodic mock SSE events for ticker testing in DATA_MODE=mock."""
    event_id = 0
    filepath = FIXTURES_DIR / "tickerFeed.json"
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    snapshot = TickerSnapshotPayload.model_validate(data)

    while True:
        for quote in snapshot.quotes:
            event_id += 1
            payload = quote.model_dump()
            yield f"id: {event_id}\nevent: quote\ndata: {json.dumps(payload)}\n\n"
            await asyncio.sleep(3.0)
        yield ": ping\n\n"
        await asyncio.sleep(2.0)
