from typing import Any, Dict, List, Tuple
from backend.app.presenters.base import calculate_level_delta
from backend.app.schemas.envelope import StatTileMetric


def present_govt_expenditure(
    by_series: Dict[str, List[Dict[str, Any]]],
    obs_rows: List[Dict[str, Any]]
) -> Tuple[Dict[str, StatTileMetric], List[Dict[str, Any]]]:
    """Present Government Expenditure indicator: Total & Capital expenditure with estimate markings."""
    tot_pts = by_series.get("total", [])
    cap_pts = by_series.get("capital", [])
    rev_pts = by_series.get("revenue", [])

    tot_latest = round(float(tot_pts[-1]["value"]), 2) if (tot_pts and tot_pts[-1]["value"] is not None) else None
    tot_p1 = round(float(tot_pts[-2]["value"]), 2) if (len(tot_pts) >= 2 and tot_pts[-2]["value"] is not None) else None
    tot_p2 = round(float(tot_pts[-3]["value"]), 2) if (len(tot_pts) >= 3 and tot_pts[-3]["value"] is not None) else None
    tot_delta = calculate_level_delta(tot_latest, tot_p1, tot_p2)

    cap_latest = round(float(cap_pts[-1]["value"]), 2) if (cap_pts and cap_pts[-1]["value"] is not None) else None
    cap_p1 = round(float(cap_pts[-2]["value"]), 2) if (len(cap_pts) >= 2 and cap_pts[-2]["value"] is not None) else None
    cap_p2 = round(float(cap_pts[-3]["value"]), 2) if (len(cap_pts) >= 3 and cap_pts[-3]["value"] is not None) else None
    cap_delta = calculate_level_delta(cap_latest, cap_p1, cap_p2)

    tot_tile = StatTileMetric(
        label="Total Expenditure",
        value=tot_latest,
        formattedValue=f"₹{tot_latest:.2f}L Cr" if tot_latest is not None else "—",
        unit="Rs lakh crore",
        delta=tot_delta,
        change=tot_delta,
        formattedDelta=f"{'+' if (tot_delta or 0) > 0 else ''}{tot_delta}pp" if tot_delta is not None else None,
        deltaUnit="pp",
        change_unit="pp",
        deltaDirection="positive" if (tot_delta or 0) >= 0 else "negative",
        iconKey="expenditure"
    )

    cap_tile = StatTileMetric(
        label="Capital Expenditure",
        value=cap_latest,
        formattedValue=f"₹{cap_latest:.2f}L Cr" if cap_latest is not None else "—",
        unit="Rs lakh crore",
        delta=cap_delta,
        change=cap_delta,
        formattedDelta=f"{'+' if (cap_delta or 0) > 0 else ''}{cap_delta}pp" if cap_delta is not None else None,
        deltaUnit="pp",
        change_unit="pp",
        deltaDirection="positive" if (cap_delta or 0) >= 0 else "negative",
        iconKey="parliament"
    )

    values = {"totalExpenditure": tot_tile, "capitalExpenditure": cap_tile}

    periods = sorted({r["period"] for r in obs_rows})
    series = []
    for p in periods:
        r_row = next((x for x in rev_pts if x["period"] == p), None)
        c_row = next((x for x in cap_pts if x["period"] == p), None)
        t_row = next((x for x in tot_pts if x["period"] == p), None)

        r_val = round(float(r_row["value"]), 2) if (r_row and r_row.get("value") is not None) else None
        c_val = round(float(c_row["value"]), 2) if (c_row and c_row.get("value") is not None) else None
        t_val = round(float(t_row["value"]), 2) if (t_row and t_row.get("value") is not None) else None

        basis = (t_row or c_row or r_row or {}).get("basis")
        is_estimate = bool(
            basis in ("revised_estimate", "budget_estimate")
            or "(RE)" in str(p)
            or "(BE)" in str(p)
        )

        series.append({
            "year": str(p),
            "revenueExpenditure": r_val,
            "capitalExpenditure": c_val,
            "totalExpenditure": t_val,
            "basis": basis,
            "estimate": is_estimate
        })

    return values, series
