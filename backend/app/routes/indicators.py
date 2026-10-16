import json
from pathlib import Path
from typing import Dict, List
from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from backend.app.config import settings
from backend.app.schemas.auth import AuthUser
from backend.app.schemas.envelope import DashboardResponse, StandardIndicatorEnvelope
from backend.app.security.dependencies import get_current_user

router = APIRouter(prefix="/api", tags=["Indicators"])

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"

INDICATOR_FIXTURE_MAP: Dict[str, str] = {
    "gdp-growth": "gdpGrowth.json",
    "debt-to-gdp": "debtToGdp.json",
    "trade": "tradeBalance.json",
    "trade-balance": "tradeBalance.json",
    "gst": "gstCollection.json",
    "gst-collection": "gstCollection.json",
    "inflation": "inflation.json",
    "government-expenditure": "govtExpenditure.json",
    "govt-expenditure": "govtExpenditure.json",
}

ALL_INDICATOR_KEYS: List[str] = [
    "gdp-growth",
    "debt-to-gdp",
    "trade-balance",
    "gst-collection",
    "inflation",
    "govt-expenditure"
]


def load_fixture_envelope(slug: str) -> StandardIndicatorEnvelope:
    filename = INDICATOR_FIXTURE_MAP.get(slug)
    if not filename:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Indicator '{slug}' not found"
        )
    filepath = FIXTURES_DIR / filename
    if not filepath.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fixture file '{filename}' missing on server"
        )
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return StandardIndicatorEnvelope.model_validate(data)


@router.get(
    "/indicators/{indicator_slug}",
    response_model=StandardIndicatorEnvelope,
    summary="Get individual macroeconomic indicator panel data"
)
async def get_indicator(
    indicator_slug: str,
    response: Response,
    if_none_match: str | None = Header(default=None),
    user: AuthUser = Depends(get_current_user)
) -> StandardIndicatorEnvelope:
    if settings.DATA_MODE == "mock":
        envelope = load_fixture_envelope(indicator_slug)
        # Compute deterministic ETag based on slug and as_of
        etag = f'"{indicator_slug}-{envelope.as_of}"'
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "private, max-age=60"
        if if_none_match and if_none_match == etag:
            return Response(
                status_code=status.HTTP_304_NOT_MODIFIED,
                headers={"ETag": etag, "Cache-Control": "private, max-age=60"}
            )
        return envelope

    # Live mode delegate
    from backend.app.services.indicator_service import get_indicator_live
    return await get_indicator_live(indicator_slug, response, if_none_match)


@router.get(
    "/dashboard",
    response_model=DashboardResponse,
    summary="Get consolidated dashboard with all six indicator panels"
)
async def get_dashboard(
    response: Response,
    if_none_match: str | None = Header(default=None),
    user: AuthUser = Depends(get_current_user)
) -> DashboardResponse:
    if settings.DATA_MODE == "mock":
        envelopes = [load_fixture_envelope(slug) for slug in ALL_INDICATOR_KEYS]
        dashboard = DashboardResponse(
            indicators=envelopes,
            as_of=envelopes[0].as_of if envelopes else "2026",
            fetched_at=envelopes[0].fetched_at if envelopes else "2026-10-16T00:00:00Z"
        )
        etag = f'"dashboard-{dashboard.as_of}"'
        response.headers["ETag"] = etag
        response.headers["Cache-Control"] = "private, max-age=60"
        if if_none_match and if_none_match == etag:
            return Response(
                status_code=status.HTTP_304_NOT_MODIFIED,
                headers={"ETag": etag, "Cache-Control": "private, max-age=60"}
            )
        return dashboard

    # Live mode delegate
    from backend.app.services.indicator_service import get_dashboard_live
    return await get_dashboard_live(response, if_none_match)
