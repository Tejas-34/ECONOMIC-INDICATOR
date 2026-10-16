from typing import Any, Dict, List, Tuple
from backend.app.presenters.base import calculate_rate_delta
from backend.app.schemas.envelope import StatTileMetric


def present_debt_to_gdp(
    by_series: Dict[str, List[Dict[str, Any]]],
    obs_rows: List[Dict[str, Any]]
) -> Tuple[Dict[str, StatTileMetric], List[Dict[str, Any]]]:
    """Present Debt to GDP Ratio indicator: India (FY25) vs US gap and ratio points."""
    ind_pts = by_series.get("india", [])
    usa_pts = by_series.get("usa", [])

    ind_latest = round(float(ind_pts[-1]["value"]), 2) if (ind_pts and ind_pts[-1]["value"] is not None) else None
    ind_prev = round(float(ind_pts[-2]["value"]), 2) if (len(ind_pts) >= 2 and ind_pts[-2]["value"] is not None) else None
    ind_delta = calculate_rate_delta(ind_latest, ind_prev)

    usa_latest = round(float(usa_pts[-1]["value"]), 2) if (usa_pts and usa_pts[-1]["value"] is not None) else None
    usa_prev = round(float(usa_pts[-2]["value"]), 2) if (len(usa_pts) >= 2 and usa_pts[-2]["value"] is not None) else None

    gap_latest = round(ind_latest - usa_latest, 2) if (ind_latest is not None and usa_latest is not None) else None
    gap_prev = round(ind_prev - usa_prev, 2) if (ind_prev is not None and usa_prev is not None) else None
    gap_delta = calculate_rate_delta(gap_latest, gap_prev)

    ind_tile = StatTileMetric(
        label="India (FY25)",
        value=ind_latest,
        formattedValue=f"{ind_latest}%" if ind_latest is not None else "—",
        unit="%",
        delta=ind_delta,
        change=ind_delta,
        formattedDelta=f"{'+' if (ind_delta or 0) > 0 else ''}{ind_delta}pp" if ind_delta is not None else None,
        deltaUnit="pp",
        change_unit="pp",
        deltaDirection="positive" if (ind_delta or 0) >= 0 else "negative",
        iconKey="india"
    )

    gap_tile = StatTileMetric(
        label="Ind vs US",
        value=gap_latest,
        formattedValue=f"{gap_latest}%" if gap_latest is not None else "—",
        unit="pp",
        delta=gap_delta,
        change=gap_delta,
        formattedDelta=f"{'+' if (gap_delta or 0) > 0 else ''}{gap_delta}pp" if gap_delta is not None else None,
        deltaUnit="pp",
        change_unit="pp",
        deltaDirection="positive" if (gap_delta or 0) >= 0 else "negative",
        iconKey="us"
    )

    values = {"indiaFy25": ind_tile, "indVsUs": gap_tile}

    series = []
    for pt in ind_pts:
        p = pt["period"]
        val = round(float(pt["value"]), 2) if pt.get("value") is not None else None
        series.append({
            "date": str(p),
            "ratio": val,
            "isHighlighted": True,
            "highlightLabel": f"{val}%" if val is not None else None
        })

    return values, series
