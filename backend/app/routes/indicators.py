from fastapi import APIRouter, Depends, Header, Response
from backend.app.schemas.auth import AuthUser
from backend.app.schemas.envelope import DashboardResponse, StandardIndicatorEnvelope
from backend.app.security.dependencies import get_current_user
from backend.app.services.indicator_service import get_dashboard_live, get_indicator_live

router = APIRouter(prefix="/api", tags=["Indicators"])


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
    return await get_dashboard_live(response, if_none_match)
