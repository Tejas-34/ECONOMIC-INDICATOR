from fastapi import APIRouter, Depends, Header, HTTPException, Query, Response, status
from backend.app.schemas.auth import AuthUser
from backend.app.schemas.ticker import TickerSnapshotPayload
from backend.app.security.dependencies import get_current_user
from backend.app.security.jwt import consume_stream_ticket
from backend.app.services.ticker_service import get_latest_quotes_snapshot
from backend.app.sse import subscribe_client

router = APIRouter(prefix="/api", tags=["Ticker"])


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
    if not ticket or not consume_stream_ticket(ticket):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing or invalid stream ticket"
        )

    return await subscribe_client(ticket=ticket, last_event_id=last_event_id, already_validated=True)
