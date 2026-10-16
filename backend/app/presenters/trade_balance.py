from typing import Any, Dict, List, Tuple
from backend.app.presenters.base import calculate_level_delta
from backend.app.schemas.envelope import StatTileMetric


def present_trade_balance(
    by_series: Dict[str, List[Dict[str, Any]]],
    obs_rows: List[Dict[str, Any]]
) -> Tuple[Dict[str, StatTileMetric], List[Dict[str, Any]]]:
    """Present Imports, Exports & Trade Balance indicator: US$ B levels and signed % GDP line."""
    exp_pts = by_series.get("exports", [])
    imp_pts = by_series.get("imports", [])
    bal_pts = by_series.get("balance_pct", [])

    exp_latest = round(float(exp_pts[-1]["value"]), 2) if (exp_pts and exp_pts[-1]["value"] is not None) else None
    exp_p1 = round(float(exp_pts[-2]["value"]), 2) if (len(exp_pts) >= 2 and exp_pts[-2]["value"] is not None) else None
    exp_p2 = round(float(exp_pts[-3]["value"]), 2) if (len(exp_pts) >= 3 and exp_pts[-3]["value"] is not None) else None
    exp_delta = calculate_level_delta(exp_latest, exp_p1, exp_p2)

    imp_latest = round(float(imp_pts[-1]["value"]), 2) if (imp_pts and imp_pts[-1]["value"] is not None) else None
    imp_p1 = round(float(imp_pts[-2]["value"]), 2) if (len(imp_pts) >= 2 and imp_pts[-2]["value"] is not None) else None
    imp_p2 = round(float(imp_pts[-3]["value"]), 2) if (len(imp_pts) >= 3 and imp_pts[-3]["value"] is not None) else None
    imp_delta = calculate_level_delta(imp_latest, imp_p1, imp_p2)

    exp_tile = StatTileMetric(
        label="Exports",
        value=exp_latest,
        formattedValue=f"${exp_latest} B" if exp_latest is not None else "—",
        unit="US$ B",
        delta=exp_delta,
        change=exp_delta,
        formattedDelta=f"{'+' if (exp_delta or 0) > 0 else ''}{exp_delta}pp" if exp_delta is not None else None,
        deltaUnit="pp",
        change_unit="pp",
        deltaDirection="positive" if (exp_delta or 0) >= 0 else "negative",
        iconKey="exports"
    )

    imp_tile = StatTileMetric(
        label="Imports",
        value=imp_latest,
        formattedValue=f"${imp_latest} B" if imp_latest is not None else "—",
        unit="US$ B",
        delta=imp_delta,
        change=imp_delta,
        formattedDelta=f"{'+' if (imp_delta or 0) > 0 else ''}{imp_delta}pp" if imp_delta is not None else None,
        deltaUnit="pp",
        change_unit="pp",
        deltaDirection="positive" if (imp_delta or 0) >= 0 else "negative",
        iconKey="imports"
    )

    values = {"exports": exp_tile, "imports": imp_tile}

    periods = sorted({r["period"] for r in obs_rows})
    series = []
    for p in periods:
        i_val = next((round(float(x["value"]), 2) for x in imp_pts if x["period"] == p and x["value"] is not None), None)
        e_val = next((round(float(x["value"]), 2) for x in exp_pts if x["period"] == p and x["value"] is not None), None)
        b_val = next((round(float(x["value"]), 2) for x in bal_pts if x["period"] == p and x["value"] is not None), None)
        series.append({
            "year": str(p),
            "importsValue": i_val,
            "exportsValue": e_val,
            "tradeBalance": b_val,
            "tradeBalanceLabel": str(b_val) if b_val is not None else "—"
        })

    return values, series
