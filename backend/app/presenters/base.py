from typing import Optional


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
