import pytest
from backend.app.services.indicator_service import (
    calculate_rate_delta,
    calculate_yoy_growth,
    calculate_level_delta,
    determine_status
)


def test_rate_series_delta_calculation():
    # latest - previous in pp
    assert calculate_rate_delta(4.82, 5.02) == -0.20
    assert calculate_rate_delta(3.82, 4.63) == -0.81
    assert calculate_rate_delta(None, 4.0) is None
    assert calculate_rate_delta(4.0, None) is None


def test_level_series_delta_calculation():
    # prev2 = 100, prev1 = 110 (10% growth), latest = 120 (9.09% growth) -> delta = 9.09 - 10.0 = -0.91pp
    delta = calculate_level_delta(120.0, 110.0, 100.0)
    assert delta == -0.91
    # Missing points
    assert calculate_level_delta(None, 110.0, 100.0) is None
    assert calculate_level_delta(120.0, None, 100.0) is None


def test_staleness_determination():
    # Within 48 hours -> ok
    assert determine_status("2026-10-16T00:00:00Z") in ("ok", "stale")
    # 2 years ago -> stale
    assert determine_status("2024-01-01T00:00:00Z") == "stale"
    # None -> unavailable
    assert determine_status(None) == "unavailable"


def test_etag_caching_on_indicators(client):
    resp1 = client.get("/api/indicators/gdp-growth")
    assert resp1.status_code == 200
    etag = resp1.headers.get("ETag")
    assert etag is not None

    # Request with matching If-None-Match returns 304
    resp2 = client.get("/api/indicators/gdp-growth", headers={"If-None-Match": etag})
    assert resp2.status_code == 304


def test_all_six_indicators_conform_to_contract(client):
    slugs = [
        "gdp-growth", "debt-to-gdp", "trade", "gst", "inflation", "government-expenditure"
    ]
    for s in slugs:
        resp = client.get(f"/api/indicators/{s}")
        assert resp.status_code == 200
        data = resp.json()
        assert "indicator" in data or "id" in data
        assert "tiles" in data
        assert "series" in data
        assert "source" in data
        assert "as_of" in data
        assert "status" in data
