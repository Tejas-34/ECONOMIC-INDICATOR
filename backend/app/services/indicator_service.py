from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, Response, status
from backend.app.cache import get_cached_macro, set_cached_macro
from backend.app.config import settings
from backend.app.db import fetch_all, fetch_one
from backend.app.presenters import get_presenter
from backend.app.schemas.envelope import (
    DashboardResponse,
    SourceProvenance,
    StandardIndicatorEnvelope,
    StatTileMetric,
    TimeSeries,
    TimeSeriesPoint,
)

REFRESH_INTERVAL_MACRO_HOURS = 24


def calculate_rate_delta(latest: Optional[float], previous: Optional[float]) -> Optional[float]:
    """Rate series delta: latest - previous in percentage points (pp)."""
    if latest is None or previous is None:
        return None
    return round(latest - previous, 2)


def calculate_yoy_growth(latest: Optional[float], previous: Optional[float]) -> Optional[float]:
    """YoY growth percentage: ((latest - previous) / previous) * 100."""
    if latest is None or previous is None or previous == 0:
        return None
    return round(((latest - previous) / abs(previous)) * 100, 2)


def calculate_level_delta(
    latest: Optional[float],
    prev1: Optional[float],
    prev2: Optional[float]
) -> Optional[float]:
    """Level series delta: YoY_growth(latest) - YoY_growth(prev1) in pp."""
    yoy_latest = calculate_yoy_growth(latest, prev1)
    yoy_prev = calculate_yoy_growth(prev1, prev2)
    if yoy_latest is None or yoy_prev is None:
        return None
    return round(yoy_latest - yoy_prev, 2)


def determine_status(fetched_at_str: Optional[str]) -> str:
    """Mark status as 'stale' if fetched_at exceeds 2x refresh interval."""
    if not fetched_at_str:
        return "unavailable"
    try:
        dt = datetime.fromisoformat(fetched_at_str.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if now - dt > timedelta(hours=REFRESH_INTERVAL_MACRO_HOURS * 2):
            return "stale"
        return "ok"
    except Exception:
        return "ok"


SLUG_ALIASES = {
    "trade-balance": "trade",
    "gst-collection": "gst",
    "govt-expenditure": "government-expenditure",
}

PANEL_TITLES = {
    "gdp-growth": ("GDP Growth - India vs World", "(YOY%)"),
    "debt-to-gdp": ("Debt to GDP Ratio", "(IND)"),
    "trade": ("Imports, Exports & Trade Balance", None),
    "gst": ("GST Tax Collection", "(₹ Lakh Cr)"),
    "inflation": ("Inflation", "(IND)"),
    "government-expenditure": ("Government Expenditure", None),
}


async def assemble_indicator(slug: str) -> StandardIndicatorEnvelope:
    """Query PostgreSQL observations table and compile a standardized indicator envelope."""
    canonical_slug = SLUG_ALIASES.get(slug, slug)

    # 1. Fetch source info
    src_target = (
        "worldbank" if canonical_slug in ("gdp-growth", "trade", "inflation")
        else "imf" if canonical_slug == "debt-to-gdp"
        else "seed-budget" if canonical_slug == "government-expenditure"
        else "data-gov-in"
    )
    source_row = await fetch_one(
        "SELECT id, name, type, url FROM sources WHERE id = %s LIMIT 1;",
        (src_target,)
    )
    if not source_row and canonical_slug == "gst":
        source_row = await fetch_one(
            "SELECT id, name, type, url FROM sources WHERE id = 'seed-gst' LIMIT 1;"
        )
    source_prov = SourceProvenance(
        name=source_row["name"] if source_row else "Authoritative Statistical Agency",
        type=source_row["type"] if source_row else "external",
        url=source_row["url"] if source_row else ""
    )

    # 2. Fetch observations
    obs_rows = await fetch_all(
        "SELECT series, period, value, unit, basis, as_of, fetched_at FROM observations WHERE indicator = %s ORDER BY period ASC;",
        (canonical_slug,)
    )

    title, subtitle = PANEL_TITLES.get(canonical_slug, (canonical_slug.replace("-", " ").title(), None))

    if not obs_rows:
        return StandardIndicatorEnvelope(
            id=slug,
            indicator=canonical_slug,
            title=title,
            subtitle=subtitle,
            values={},
            tiles=[],
            series=[],
            source=source_prov,
            source_type=source_prov.type,
            as_of=datetime.now(timezone.utc).strftime("%Y"),
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="unavailable"
        )

    latest_fetched_at = max(r["fetched_at"].isoformat() for r in obs_rows if r.get("fetched_at"))
    overall_status = determine_status(latest_fetched_at)
    latest_as_of = max(str(r["as_of"]) for r in obs_rows if r.get("as_of"))

    tiles: List[StatTileMetric] = []
    values_dict: Dict[str, Any] = {}
    series_data: List[Any] = []

    # Map by series -> points
    by_series: Dict[str, List[Dict[str, Any]]] = {}
    for r in obs_rows:
        s_name = r["series"]
        by_series.setdefault(s_name, []).append(r)

    # -------------------------------------------------------------
    # Panel-Specific Presenter Delegation (I1/I2)
    # -------------------------------------------------------------
    presenter = get_presenter(canonical_slug)
    if presenter:
        values_dict, series_data = presenter(by_series, obs_rows)
        tiles = list(values_dict.values())
    else:
        values_dict = {}
        tiles = []
        series_data = []

    envelope = StandardIndicatorEnvelope(
        id=slug,
        indicator=canonical_slug,
        title=title,
        subtitle=subtitle,
        values=values_dict,
        tiles=tiles,
        series=series_data,
        source=source_prov,
        source_type=source_prov.type,
        as_of=latest_as_of,
        fetched_at=latest_fetched_at,
        status=overall_status
    )
    return envelope


async def get_indicator_live(
    slug: str,
    response: Response,
    if_none_match: Optional[str] = None
) -> StandardIndicatorEnvelope:
    canonical_slug = {
        "trade-balance": "trade",
        "gst-collection": "gst",
        "govt-expenditure": "government-expenditure"
    }.get(slug, slug)

    cache_key = f"indicator_{canonical_slug}"
    cached = get_cached_macro(cache_key)
    if cached is None:
        cached = await assemble_indicator(canonical_slug)
        set_cached_macro(cache_key, cached)

    etag = f'"{canonical_slug}-{cached.as_of}-{cached.fetched_at}"'
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "private, max-age=60"

    if if_none_match and if_none_match == etag:
        return Response(
            status_code=status.HTTP_304_NOT_MODIFIED,
            headers={"ETag": etag, "Cache-Control": "private, max-age=60"}
        )

    return cached


async def get_dashboard_live(
    response: Response,
    if_none_match: Optional[str] = None
) -> DashboardResponse:
    cache_key = "dashboard_live"
    cached = get_cached_macro(cache_key)
    if cached is None:
        slugs = ["gdp-growth", "debt-to-gdp", "trade-balance", "gst-collection", "inflation", "govt-expenditure"]
        envelopes = [await assemble_indicator(s) for s in slugs]
        cached = DashboardResponse(
            indicators=envelopes,
            as_of=envelopes[0].as_of if envelopes else "2026",
            fetched_at=envelopes[0].fetched_at if envelopes else datetime.now(timezone.utc).isoformat()
        )
        set_cached_macro(cache_key, cached)

    etag = f'"dashboard-{cached.as_of}-{cached.fetched_at}"'
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "private, max-age=60"

    if if_none_match and if_none_match == etag:
        return Response(
            status_code=status.HTTP_304_NOT_MODIFIED,
            headers={"ETag": etag, "Cache-Control": "private, max-age=60"}
        )

    return cached
