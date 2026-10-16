from typing import Any, Dict, List, Tuple
from backend.app.presenters.base import calculate_level_delta
from backend.app.schemas.envelope import StatTileMetric


def present_gst_collection(
    by_series: Dict[str, List[Dict[str, Any]]],
    obs_rows: List[Dict[str, Any]]
) -> Tuple[Dict[str, StatTileMetric], List[Dict[str, Any]]]:
    """Present GST Tax Collection indicator: Gross collection & monthly average in Rs lakh crore."""
    gro_pts = by_series.get("gross_collection", [])
    avg_pts = by_series.get("monthly_average", [])
    yoy_pts = by_series.get("yoy_growth", [])

    gro_latest = round(float(gro_pts[-1]["value"]), 2) if (gro_pts and gro_pts[-1]["value"] is not None) else None
    gro_p1 = round(float(gro_pts[-2]["value"]), 2) if (len(gro_pts) >= 2 and gro_pts[-2]["value"] is not None) else None
    gro_p2 = round(float(gro_pts[-3]["value"]), 2) if (len(gro_pts) >= 3 and gro_pts[-3]["value"] is not None) else None
    gro_delta = calculate_level_delta(gro_latest, gro_p1, gro_p2)

    avg_latest = round(float(avg_pts[-1]["value"]), 2) if (avg_pts and avg_pts[-1]["value"] is not None) else None
    avg_p1 = round(float(avg_pts[-2]["value"]), 2) if (len(avg_pts) >= 2 and avg_pts[-2]["value"] is not None) else None
    avg_p2 = round(float(avg_pts[-3]["value"]), 2) if (len(avg_pts) >= 3 and avg_pts[-3]["value"] is not None) else None
    avg_delta = calculate_level_delta(avg_latest, avg_p1, avg_p2)

    gro_tile = StatTileMetric(
        label="GST Collections",
        value=gro_latest,
        formattedValue=f"{gro_latest}%" if gro_latest is not None else "—",
        unit="Rs lakh crore",
        delta=gro_delta,
        change=gro_delta,
        formattedDelta=f"{'+' if (gro_delta or 0) > 0 else ''}{gro_delta}pp" if gro_delta is not None else None,
        deltaUnit="pp",
        change_unit="pp",
        deltaDirection="positive" if (gro_delta or 0) >= 0 else "negative",
        iconKey="gst"
    )

    avg_tile = StatTileMetric(
        label="Monthly Average",
        value=avg_latest,
        formattedValue=f"{avg_latest}" if avg_latest is not None else "—",
        unit="Rs lakh crore",
        delta=avg_delta,
        change=avg_delta,
        formattedDelta=f"{'+' if (avg_delta or 0) > 0 else ''}{avg_delta}pp" if avg_delta is not None else None,
        deltaUnit="pp",
        change_unit="pp",
        deltaDirection="positive" if (avg_delta or 0) >= 0 else "negative",
        iconKey="coins"
    )

    values = {"collections": gro_tile, "monthlyAverage": avg_tile}

    periods = sorted({r["period"] for r in obs_rows})
    series = []
    for p in periods:
        c_val = next((round(float(x["value"]), 2) for x in yoy_pts if x["period"] == p and x["value"] is not None), None)
        if c_val is None:
            c_val = next((round(float(x["value"]), 2) for x in gro_pts if x["period"] == p and x["value"] is not None), None)
        a_val = next((round(float(x["value"]), 2) for x in avg_pts if x["period"] == p and x["value"] is not None), None)
        series.append({
            "year": str(p),
            "collectionRate": c_val,
            "averageRate": a_val,
            "highlightLabel": f"{a_val}%" if a_val is not None else None
        })

    return values, series
