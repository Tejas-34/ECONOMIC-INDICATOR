from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from fastapi import HTTPException, Response, status
from backend.app.cache import get_cached_macro, set_cached_macro
from backend.app.config import settings
from backend.app.db import fetch_all, fetch_one
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


async def assemble_indicator(slug: str) -> StandardIndicatorEnvelope:
    """Query PostgreSQL observations table and compile a standardized indicator envelope."""
    # 1. Fetch source info
    source_row = await fetch_one(
        "SELECT id, name, type, url FROM sources WHERE id = %s LIMIT 1;",
        ("worldbank" if slug in ("gdp-growth", "trade", "inflation") else ("imf" if slug == "debt-to-gdp" else "seed-budget" if slug == "government-expenditure" else "seed-gst"),)
    )
    source_prov = SourceProvenance(
        name=source_row["name"] if source_row else "Authoritative Statistical Agency",
        type=source_row["type"] if source_row else "external",
        url=source_row["url"] if source_row else ""
    )

    # 2. Fetch observations
    obs_rows = await fetch_all(
        "SELECT series, period, value, unit, basis, as_of, fetched_at FROM observations WHERE indicator = %s ORDER BY period ASC;",
        (slug,)
    )

    if not obs_rows:
        return StandardIndicatorEnvelope(
            indicator=slug,
            title=slug.replace("-", " ").title(),
            tiles=[],
            series=[],
            source=source_prov,
            as_of=datetime.now(timezone.utc).strftime("%Y"),
            fetched_at=datetime.now(timezone.utc).isoformat(),
            status="unavailable"
        )

    latest_fetched_at = max(r["fetched_at"].isoformat() for r in obs_rows if r.get("fetched_at"))
    overall_status = determine_status(latest_fetched_at)
    latest_as_of = max(str(r["as_of"]) for r in obs_rows if r.get("as_of"))

    tiles: List[StatTileMetric] = []
    series_list: List[TimeSeries] = []

    # Map by series -> points
    by_series: Dict[str, List[Dict[str, Any]]] = {}
    for r in obs_rows:
        s_name = r["series"]
        by_series.setdefault(s_name, []).append(r)

    # -------------------------------------------------------------
    # Panel-Specific Logic per Decisions D3–D9
    # -------------------------------------------------------------
    if slug == "gdp-growth":
        ind_pts = by_series.get("india", [])
        wld_pts = by_series.get("world", [])
        # Tiles: Rate series -> latest - previous in pp
        ind_latest = ind_pts[-1]["value"] if ind_pts else None
        ind_prev = ind_pts[-2]["value"] if len(ind_pts) >= 2 else None
        ind_delta = calculate_rate_delta(ind_latest, ind_prev)

        wld_latest = wld_pts[-1]["value"] if wld_pts else None
        wld_prev = wld_pts[-2]["value"] if len(wld_pts) >= 2 else None
        wld_delta = calculate_rate_delta(wld_latest, wld_prev)

        tiles = [
            StatTileMetric(
                label="India", value=float(ind_latest) if ind_latest is not None else None,
                unit="%", change=ind_delta, change_unit="pp", iconKey="india"
            ),
            StatTileMetric(
                label="World", value=float(wld_latest) if wld_latest is not None else None,
                unit="%", change=wld_delta, change_unit="pp", iconKey="world"
            )
        ]
        # Grouped bar series
        periods = sorted({r["period"] for r in obs_rows})
        series_list = [
            TimeSeries(name="india", points=[
                TimeSeriesPoint(period=p, value=next((float(x["value"]) for x in ind_pts if x["period"] == p and x["value"] is not None), None))
                for p in periods
            ]),
            TimeSeries(name="world", points=[
                TimeSeriesPoint(period=p, value=next((float(x["value"]) for x in wld_pts if x["period"] == p and x["value"] is not None), None))
                for p in periods
            ])
        ]

    elif slug == "debt-to-gdp":
        ind_pts = by_series.get("india", [])
        usa_pts = by_series.get("usa", [])

        ind_latest = ind_pts[-1]["value"] if ind_pts else None
        ind_prev = ind_pts[-2]["value"] if len(ind_pts) >= 2 else None
        ind_delta = calculate_rate_delta(ind_latest, ind_prev)

        usa_latest = usa_pts[-1]["value"] if usa_pts else None
        # Ind vs US gap in pp
        gap_latest = round(float(ind_latest - usa_latest), 2) if (ind_latest is not None and usa_latest is not None) else None
        usa_prev = usa_pts[-2]["value"] if len(usa_pts) >= 2 else None
        gap_prev = round(float(ind_prev - usa_prev), 2) if (ind_prev is not None and usa_prev is not None) else None
        gap_delta = calculate_rate_delta(gap_latest, gap_prev)

        tiles = [
            StatTileMetric(
                label="India (FY25)", value=float(ind_latest) if ind_latest is not None else None,
                unit="%", change=ind_delta, change_unit="pp", iconKey="india"
            ),
            StatTileMetric(
                label="Ind vs US", value=gap_latest,
                unit="pp", change=gap_delta, change_unit="pp", iconKey="us"
            )
        ]
        periods = sorted({r["period"] for r in obs_rows})
        series_list = [
            TimeSeries(name="india", points=[
                TimeSeriesPoint(period=p, value=next((float(x["value"]) for x in ind_pts if x["period"] == p and x["value"] is not None), None))
                for p in periods
            ])
        ]

    elif slug == "trade":
        exp_pts = by_series.get("exports", [])
        imp_pts = by_series.get("imports", [])
        bal_pts = by_series.get("balance_pct", [])

        # Level series -> delta = YoY(latest) - YoY(prev)
        exp_latest = exp_pts[-1]["value"] if exp_pts else None
        exp_p1 = exp_pts[-2]["value"] if len(exp_pts) >= 2 else None
        exp_p2 = exp_pts[-3]["value"] if len(exp_pts) >= 3 else None
        exp_delta = calculate_level_delta(exp_latest, exp_p1, exp_p2)

        imp_latest = imp_pts[-1]["value"] if imp_pts else None
        imp_p1 = imp_pts[-2]["value"] if len(imp_pts) >= 2 else None
        imp_p2 = imp_pts[-3]["value"] if len(imp_pts) >= 3 else None
        imp_delta = calculate_level_delta(imp_latest, imp_p1, imp_p2)

        tiles = [
            StatTileMetric(
                label="Exports", value=float(exp_latest) if exp_latest is not None else None,
                unit="US$ B", change=exp_delta, change_unit="pp", iconKey="exports"
            ),
            StatTileMetric(
                label="Imports", value=float(imp_latest) if imp_latest is not None else None,
                unit="US$ B", change=imp_delta, change_unit="pp", iconKey="imports"
            )
        ]
        periods = sorted({r["period"] for r in obs_rows})
        series_list = [
            TimeSeries(name="exports", points=[
                TimeSeriesPoint(period=p, value=next((float(x["value"]) for x in exp_pts if x["period"] == p and x["value"] is not None), None))
                for p in periods
            ]),
            TimeSeries(name="imports", points=[
                TimeSeriesPoint(period=p, value=next((float(x["value"]) for x in imp_pts if x["period"] == p and x["value"] is not None), None))
                for p in periods
            ]),
            TimeSeries(name="trade_balance", points=[
                TimeSeriesPoint(period=p, value=next((float(x["value"]) for x in bal_pts if x["period"] == p and x["value"] is not None), None))
                for p in periods
            ])
        ]

    elif slug == "gst":
        gro_pts = by_series.get("gross_collection", [])
        avg_pts = by_series.get("monthly_average", [])
        yoy_pts = by_series.get("yoy_growth", [])

        gro_latest = gro_pts[-1]["value"] if gro_pts else None
        gro_p1 = gro_pts[-2]["value"] if len(gro_pts) >= 2 else None
        gro_p2 = gro_pts[-3]["value"] if len(gro_pts) >= 3 else None
        gro_delta = calculate_level_delta(gro_latest, gro_p1, gro_p2)

        avg_latest = avg_pts[-1]["value"] if avg_pts else None
        avg_p1 = avg_pts[-2]["value"] if len(avg_pts) >= 2 else None
        avg_p2 = avg_pts[-3]["value"] if len(avg_pts) >= 3 else None
        avg_delta = calculate_level_delta(avg_latest, avg_p1, avg_p2)

        tiles = [
            StatTileMetric(
                label="GST Collections", value=float(gro_latest) if gro_latest is not None else None,
                unit="Rs lakh crore", change=gro_delta, change_unit="pp", iconKey="gst"
            ),
            StatTileMetric(
                label="Monthly Average", value=float(avg_latest) if avg_latest is not None else None,
                unit="Rs lakh crore", change=avg_delta, change_unit="pp", iconKey="coins"
            )
        ]
        periods = sorted({r["period"] for r in obs_rows})
        series_list = [
            TimeSeries(name="yoy_growth", points=[
                TimeSeriesPoint(period=p, value=next((float(x["value"]) for x in yoy_pts if x["period"] == p and x["value"] is not None), None))
                for p in periods
            ]),
            TimeSeries(name="monthly_average", points=[
                TimeSeriesPoint(period=p, value=next((float(x["value"]) for x in avg_pts if x["period"] == p and x["value"] is not None), None))
                for p in periods
            ])
        ]

    elif slug == "inflation":
        cpi_pts = by_series.get("cpi_rate", [])
        cpi_latest = cpi_pts[-1]["value"] if cpi_pts else None
        cpi_prev = cpi_pts[-2]["value"] if len(cpi_pts) >= 2 else None
        cpi_delta = calculate_rate_delta(cpi_latest, cpi_prev)

        tiles = [
            StatTileMetric(
                label="Inflation Rate", value=float(cpi_latest) if cpi_latest is not None else None,
                unit="%", change=cpi_delta, change_unit="pp", iconKey="inflation"
            ),
            StatTileMetric(
                label="RBI Target", value=4.0,
                unit="%", change=None, change_unit=None, iconKey="target"
            )
        ]
        periods = sorted({r["period"] for r in obs_rows})
        series_list = [
            TimeSeries(name="cpi_rate", points=[
                TimeSeriesPoint(period=p, value=next((float(x["value"]) for x in cpi_pts if x["period"] == p and x["value"] is not None), None))
                for p in periods
            ])
        ]

    elif slug == "government-expenditure":
        tot_pts = by_series.get("total", [])
        cap_pts = by_series.get("capital", [])
        rev_pts = by_series.get("revenue", [])

        tot_latest = tot_pts[-1]["value"] if tot_pts else None
        tot_p1 = tot_pts[-2]["value"] if len(tot_pts) >= 2 else None
        tot_p2 = tot_pts[-3]["value"] if len(tot_pts) >= 3 else None
        tot_delta = calculate_level_delta(tot_latest, tot_p1, tot_p2)

        cap_latest = cap_pts[-1]["value"] if cap_pts else None
        cap_p1 = cap_pts[-2]["value"] if len(cap_pts) >= 2 else None
        cap_p2 = cap_pts[-3]["value"] if len(cap_pts) >= 3 else None
        cap_delta = calculate_level_delta(cap_latest, cap_p1, cap_p2)

        tiles = [
            StatTileMetric(
                label="Total Expenditure", value=float(tot_latest) if tot_latest is not None else None,
                unit="Rs lakh crore", change=tot_delta, change_unit="pp", iconKey="expenditure"
            ),
            StatTileMetric(
                label="Capital Expenditure", value=float(cap_latest) if cap_latest is not None else None,
                unit="Rs lakh crore", change=cap_delta, change_unit="pp", iconKey="parliament"
            )
        ]
        periods = sorted({r["period"] for r in obs_rows})
        series_list = [
            TimeSeries(name="revenue", points=[
                TimeSeriesPoint(period=p, value=next((float(x["value"]) for x in rev_pts if x["period"] == p and x["value"] is not None), None), basis=next((x.get("basis") for x in rev_pts if x["period"] == p), None))
                for p in periods
            ]),
            TimeSeries(name="capital", points=[
                TimeSeriesPoint(period=p, value=next((float(x["value"]) for x in cap_pts if x["period"] == p and x["value"] is not None), None), basis=next((x.get("basis") for x in cap_pts if x["period"] == p), None))
                for p in periods
            ])
        ]

    envelope = StandardIndicatorEnvelope(
        indicator=slug,
        title=slug.replace("-", " ").title(),
        tiles=tiles,
        series=series_list,
        source=source_prov,
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
        response.status_code = status.HTTP_304_NOT_MODIFIED
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)

    return cached


async def get_dashboard_live(
    response: Response,
    if_none_match: Optional[str] = None
) -> DashboardResponse:
    cache_key = "dashboard_live"
    cached = get_cached_macro(cache_key)
    if cached is None:
        slugs = ["gdp-growth", "debt-to-gdp", "trade", "gst", "inflation", "government-expenditure"]
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
        response.status_code = status.HTTP_304_NOT_MODIFIED
        return Response(status_code=status.HTTP_304_NOT_MODIFIED)

    return cached
