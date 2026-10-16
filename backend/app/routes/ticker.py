import json
from pathlib import Path
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse
from backend.app.config import settings
from backend.app.schemas.auth import AuthUser
from backend.app.schemas.ticker import TickerSnapshotPayload
from backend.app.security.dependencies import get_current_user

router = APIRouter(prefix="/api", tags=["Ticker"])

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"


def load_fixture_ticker() -> TickerSnapshotPayload:
    filepath = FIXTURES_DIR / "tickerFeed.json"
    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ticker fixture missing on server"
        )
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return TickerSnapshotPayload.model_validate(data)


@router.get(
    "/ticker",
    response_model=TickerSnapshotPayload,
    summary="Get current market index quotes snapshot"
)
@router.get(
    "/ticker/latest",
    response_model=TickerSnapshotPayload,
    include_in_schema=False
)
async def get_ticker_snapshot(
    response: Response,
    user: AuthUser = Depends(get_current_user)
) -> TickerSnapshotPayload:
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    if settings.DATA_MODE == "mock":
        return load_fixture_ticker()

    from backend.app.services.ticker_service import get_latest_quotes_snapshot
    return await get_latest_quotes_snapshot()


@router.get(
    "/stream/ticker",
    summary="Connect to Server-Sent Events (SSE) live ticker stream"
)
@router.get(
    "/ticker/stream",
    include_in_schema=False
)
async def stream_ticker(
    ticket: str | None = Query(default=None, description="Single-use stream ticket"),
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID")
):
    from backend.app.security.jwt import consume_stream_ticket
    if not ticket or not consume_stream_ticket(ticket):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing or invalid stream ticket"
        )

    if settings.DATA_MODE == "mock":
        from backend.app.sse import mock_event_generator
        return StreamingResponse(
            mock_event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    from backend.app.sse import subscribe_client
    return await subscribe_client(ticket=ticket, last_event_id=last_event_id, already_validated=True)

