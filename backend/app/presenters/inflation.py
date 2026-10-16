from typing import Any, Dict, List, Tuple
from backend.app.presenters.base import calculate_rate_delta
from backend.app.schemas.envelope import StatTileMetric


def present_inflation(
    by_series: Dict[str, List[Dict[str, Any]]],
    obs_rows: List[Dict[str, Any]]
) -> Tuple[Dict[str, StatTileMetric], List[Dict[str, Any]]]:
    """Present Inflation indicator: CPI rate vs RBI 4.0% policy target."""
    cpi_pts = by_series.get("cpi_rate", [])
    cpi_latest = round(float(cpi_pts[-1]["value"]), 2) if (cpi_pts and cpi_pts[-1]["value"] is not None) else None
    cpi_prev = round(float(cpi_pts[-2]["value"]), 2) if (len(cpi_pts) >= 2 and cpi_pts[-2]["value"] is not None) else None
    cpi_delta = calculate_rate_delta(cpi_latest, cpi_prev)

    cpi_tile = StatTileMetric(
        label="Inflation Rate",
        value=cpi_latest,
        formattedValue=f"{cpi_latest}%" if cpi_latest is not None else "—",
        unit="%",
        delta=cpi_delta,
        change=cpi_delta,
        formattedDelta=f"{'+' if (cpi_delta or 0) > 0 else ''}{cpi_delta}pp" if cpi_delta is not None else None,
        deltaUnit="pp",
        change_unit="pp",
        deltaDirection="positive" if (cpi_delta or 0) >= 0 else "negative",
        iconKey="inflation"
    )

    target_tile = StatTileMetric(
        label="RBI Target",
        value=4.0,
        formattedValue="4.0%",
        unit="%",
        delta=None,
        change=None,
        formattedDelta=None,
        deltaUnit="pp",
        change_unit="pp",
        deltaDirection="neutral",
        iconKey="target"
    )

    values = {"inflationRate": cpi_tile, "rbiTarget": target_tile}

    periods = sorted({r["period"] for r in obs_rows if r.get("series") == "cpi_rate"})
    series = [
        {
            "year": str(p),
            "cpiRate": round(float(next((x["value"] for x in cpi_pts if x["period"] == p and x["value"] is not None), 0)), 2),
        }
        for p in periods
    ]

    return values, series
