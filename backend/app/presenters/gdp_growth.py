from typing import Any, Dict, List, Tuple
from backend.app.presenters.base import calculate_rate_delta
from backend.app.schemas.envelope import StatTileMetric


def present_gdp_growth(
    by_series: Dict[str, List[Dict[str, Any]]],
    obs_rows: List[Dict[str, Any]]
) -> Tuple[Dict[str, StatTileMetric], List[Dict[str, Any]]]:
    """Present GDP Growth indicator: India vs World rate deltas and time series."""
    ind_pts = by_series.get("india", [])
    wld_pts = by_series.get("world", [])

    ind_latest = round(float(ind_pts[-1]["value"]), 2) if (ind_pts and ind_pts[-1]["value"] is not None) else None
    ind_prev = round(float(ind_pts[-2]["value"]), 2) if (len(ind_pts) >= 2 and ind_pts[-2]["value"] is not None) else None
    ind_delta = calculate_rate_delta(ind_latest, ind_prev)

    wld_latest = round(float(wld_pts[-1]["value"]), 2) if (wld_pts and wld_pts[-1]["value"] is not None) else None
    wld_prev = round(float(wld_pts[-2]["value"]), 2) if (len(wld_pts) >= 2 and wld_pts[-2]["value"] is not None) else None
    wld_delta = calculate_rate_delta(wld_latest, wld_prev)

    ind_tile = StatTileMetric(
        label="India",
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

    wld_tile = StatTileMetric(
        label="World",
        value=wld_latest,
        formattedValue=f"{wld_latest}%" if wld_latest is not None else "—",
        unit="%",
        delta=wld_delta,
        change=wld_delta,
        formattedDelta=f"{'+' if (wld_delta or 0) > 0 else ''}{wld_delta}pp" if wld_delta is not None else None,
        deltaUnit="pp",
        change_unit="pp",
        deltaDirection="positive" if (wld_delta or 0) >= 0 else "negative",
        iconKey="world"
    )

    values = {"india": ind_tile, "world": wld_tile}

    periods = sorted({r["period"] for r in obs_rows})
    series = [
        {
            "year": str(p),
            "indiaRate": round(float(next((x["value"] for x in ind_pts if x["period"] == p and x["value"] is not None), 0)), 2),
            "worldRate": round(float(next((x["value"] for x in wld_pts if x["period"] == p and x["value"] is not None), 0)), 2),
        }
        for p in periods
    ]

    return values, series
