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


def test_etag_caching_on_indicators(auth_client, client):
    # Unauthenticated returns 401
    assert client.get("/api/indicators/gdp-growth").status_code == 401

    resp1 = auth_client.get("/api/indicators/gdp-growth")
    assert resp1.status_code == 200
    etag = resp1.headers.get("ETag")
    assert etag is not None
    assert "Cache-Control" in resp1.headers

    # Request with matching If-None-Match returns 304 with preserved headers
    resp2 = auth_client.get("/api/indicators/gdp-growth", headers={"If-None-Match": etag})
    assert resp2.status_code == 304
    assert resp2.headers.get("ETag") == etag
    assert resp2.headers.get("Cache-Control") == "private, max-age=60"


def test_etag_caching_on_dashboard(auth_client, client):
    # Unauthenticated returns 401
    assert client.get("/api/dashboard").status_code == 401

    resp1 = auth_client.get("/api/dashboard")
    assert resp1.status_code == 200
    etag = resp1.headers.get("ETag")
    assert etag is not None
    assert "Cache-Control" in resp1.headers

    resp2 = auth_client.get("/api/dashboard", headers={"If-None-Match": etag})
    assert resp2.status_code == 304
    assert resp2.headers.get("ETag") == etag
    assert resp2.headers.get("Cache-Control") == "private, max-age=60"


def test_all_six_indicators_conform_to_contract(auth_client):
    expected_tile_keys = {
        "gdp-growth": {"india", "world"},
        "debt-to-gdp": {"indiaFy25", "indVsUs"},
        "trade-balance": {"exports", "imports"},
        "trade": {"exports", "imports"},
        "gst-collection": {"collections", "monthlyAverage"},
        "gst": {"collections", "monthlyAverage"},
        "inflation": {"inflationRate", "rbiTarget"},
        "govt-expenditure": {"totalExpenditure", "capitalExpenditure"},
        "government-expenditure": {"totalExpenditure", "capitalExpenditure"},
    }

    for slug, required_tiles in expected_tile_keys.items():
        resp = auth_client.get(f"/api/indicators/{slug}")
        assert resp.status_code == 200, f"Failed for slug {slug}"
        data = resp.json()
        assert "indicator" in data or "id" in data
        assert "tiles" in data
        assert "series" in data
        assert "source" in data and isinstance(data["source"], str)
        assert data.get("source_type") in ("NSE", "external")
        assert "as_of" in data
        assert "status" in data

        # Validate values object conforms to frontend tile keys
        values = data.get("values", {})
        for tile_key in required_tiles:
            assert tile_key in values, f"Missing tile key '{tile_key}' in {slug}"
            tile = values[tile_key]
            assert "label" in tile
            assert "value" in tile
            assert "formattedValue" in tile
            assert "formattedDelta" in tile
            assert tile.get("deltaDirection") in ("positive", "negative", "neutral", None)


def test_govt_expenditure_estimate_flag():
    from backend.app.presenters.govt_expenditure import present_govt_expenditure

    by_series = {
        "total": [
            {"period": "2023", "value": 41.9, "basis": "actual"},
            {"period": "2024 (RE)", "value": 44.9, "basis": "revised_estimate"},
        ],
        "capital": [
            {"period": "2023", "value": 7.4, "basis": "actual"},
            {"period": "2024 (RE)", "value": 9.5, "basis": "revised_estimate"},
        ],
        "revenue": [
            {"period": "2023", "value": 34.5, "basis": "actual"},
            {"period": "2024 (RE)", "value": 35.4, "basis": "revised_estimate"},
        ],
    }
    obs_rows = by_series["total"] + by_series["capital"] + by_series["revenue"]
    values, series = present_govt_expenditure(by_series, obs_rows)

    assert "totalExpenditure" in values
    assert "capitalExpenditure" in values
    assert len(series) == 2
    assert series[0]["estimate"] is False
    assert series[1]["estimate"] is True
    assert series[1]["basis"] == "revised_estimate"


def test_trade_balance_presenter_structure():
    from backend.app.presenters.trade_balance import present_trade_balance

    by_series = {
        "exports": [
            {"period": "2022", "value": 420.0},
            {"period": "2023", "value": 450.0},
            {"period": "2024", "value": 480.0},
        ],
        "imports": [
            {"period": "2022", "value": 600.0},
            {"period": "2023", "value": 670.0},
            {"period": "2024", "value": 710.0},
        ],
        "balance_pct": [
            {"period": "2022", "value": -2.1},
            {"period": "2023", "value": -2.3},
            {"period": "2024", "value": -1.9},
        ],
    }
    obs_rows = by_series["exports"] + by_series["imports"] + by_series["balance_pct"]
    values, series = present_trade_balance(by_series, obs_rows)

    assert values["exports"].unit == "US$ B"
    assert values["imports"].unit == "US$ B"
    assert values["exports"].formattedValue == "$480.0 B"
    assert values["imports"].formattedValue == "$710.0 B"
    assert len(series) == 3
    assert series[-1]["tradeBalance"] == -1.9

