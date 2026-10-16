from typing import Any, Callable, Dict, List, Tuple
from backend.app.schemas.envelope import StatTileMetric
from backend.app.presenters.gdp_growth import present_gdp_growth
from backend.app.presenters.debt_to_gdp import present_debt_to_gdp
from backend.app.presenters.trade_balance import present_trade_balance
from backend.app.presenters.gst_collection import present_gst_collection
from backend.app.presenters.inflation import present_inflation
from backend.app.presenters.govt_expenditure import present_govt_expenditure

PresenterFn = Callable[
    [Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]],
    Tuple[Dict[str, StatTileMetric], List[Dict[str, Any]]]
]

PRESENTER_MAP: Dict[str, PresenterFn] = {
    "gdp-growth": present_gdp_growth,
    "debt-to-gdp": present_debt_to_gdp,
    "trade": present_trade_balance,
    "trade-balance": present_trade_balance,
    "gst": present_gst_collection,
    "gst-collection": present_gst_collection,
    "inflation": present_inflation,
    "government-expenditure": present_govt_expenditure,
    "govt-expenditure": present_govt_expenditure,
}


def get_presenter(slug: str) -> PresenterFn | None:
    """Resolve presenter for canonical or legacy indicator slug."""
    return PRESENTER_MAP.get(slug)
