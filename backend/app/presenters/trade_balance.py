from typing import Any, Dict, List, Optional, Tuple
from backend.app.presenters.base import calculate_level_delta
from backend.app.schemas.envelope import StatTileMetric


def _to_billions(val: Any) -> Optional[float]:
    if val is None:
        return None
    v = float(val)
    if abs(v) > 10_000:
        return round(v / 1e9, 2)
    return round(v, 2)


def _fmt_billions(val: Optional[float]) -> str:
    if val is None:
        return "—"
    return f"${val:.1f} B"


def present_trade_balance(
    by_series: Dict[str, List[Dict[str, Any]]],
    obs_rows: List[Dict[str, Any]]
) -> Tuple[Dict[str, StatTileMetric], List[Dict[str, Any]]]:
    """Present Imports, Exports & Trade Balance indicator: US$ B levels and signed % GDP line."""
    exp_pts = by_series.get("exports", [])
    imp_pts = by_series.get("imports", [])
    bal_pts = by_series.get("balance_pct", [])

    exp_latest = _to_billions(exp_pts[-1]["value"]) if (exp_pts and exp_pts[-1].get("value") is not None) else None
    exp_p1 = _to_billions(exp_pts[-2]["value"]) if (len(exp_pts) >= 2 and exp_pts[-2].get("value") is not None) else None
    exp_p2 = _to_billions(exp_pts[-3]["value"]) if (len(exp_pts) >= 3 and exp_pts[-3].get("value") is not None) else None
    exp_delta = calculate_level_delta(exp_latest, exp_p1, exp_p2)

    imp_latest = _to_billions(imp_pts[-1]["value"]) if (imp_pts and imp_pts[-1].get("value") is not None) else None
    imp_p1 = _to_billions(imp_pts[-2]["value"]) if (len(imp_pts) >= 2 and imp_pts[-2].get("value") is not None) else None
    imp_p2 = _to_billions(imp_pts[-3]["value"]) if (len(imp_pts) >= 3 and imp_pts[-3].get("value") is not None) else None
    imp_delta = calculate_level_delta(imp_latest, imp_p1, imp_p2)

    exp_tile = StatTileMetric(
        label="Exports",
        value=exp_latest,
        formattedValue=_fmt_billions(exp_latest),
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
        formattedValue=_fmt_billions(imp_latest),
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
        i_raw = next((x["value"] for x in imp_pts if x["period"] == p and x.get("value") is not None), None)
        e_raw = next((x["value"] for x in exp_pts if x["period"] == p and x.get("value") is not None), None)
        b_raw = next((x["value"] for x in bal_pts if x["period"] == p and x.get("value") is not None), None)

        i_val = _to_billions(i_raw)
        e_val = _to_billions(e_raw)
        b_val = round(float(b_raw), 2) if b_raw is not None else None

        # Scale values to 0–10% range if in raw billions so bars fit Figma 0–10% scale
        scaled_i = round(i_val / 100, 1) if (i_val is not None and abs(i_val) > 10) else i_val
        scaled_e = round(e_val / 100, 1) if (e_val is not None and abs(e_val) > 10) else e_val
        tb_label = f"{abs(b_val):.1f}" if b_val is not None else "—"

        series.append({
            "year": str(p),
            "importsValue": scaled_i,
            "exportsValue": scaled_e,
            "tradeBalance": b_val,
            "tradeBalanceLabel": tb_label
        })

    return values, series
