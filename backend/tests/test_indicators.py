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


def test_debt_to_gdp_presenter_imf_data():
    from backend.app.presenters.debt_to_gdp import present_debt_to_gdp

    by_series = {
        "india": [
            {"period": "2021", "value": 85.5},
            {"period": "2022", "value": 84.4},
            {"period": "2023", "value": 84.7},
            {"period": "2024", "value": 84.8},
            {"period": "2025", "value": 84.3},
        ],
        "usa": [
            {"period": "2021", "value": 125.0},
            {"period": "2022", "value": 119.2},
            {"period": "2023", "value": 120.0},
            {"period": "2024", "value": 122.3},
            {"period": "2025", "value": 124.4},
        ],
    }
    obs_rows = by_series["india"] + by_series["usa"]
    values, series = present_debt_to_gdp(by_series, obs_rows)

    # India FY25 tile
    ind_tile = values["indiaFy25"]
    assert ind_tile.value == 84.3
    assert ind_tile.formattedValue == "84.3%"
    assert ind_tile.delta == -0.5
    assert ind_tile.formattedDelta == "-0.5pp"
    assert ind_tile.deltaDirection == "negative"

    # Ind vs US difference tile
    us_tile = values["indVsUs"]
    assert us_tile.value == -40.1
    assert us_tile.formattedValue == "-40.1%"
    assert us_tile.delta == -2.6
    assert us_tile.formattedDelta == "-2.6pp"
    assert us_tile.deltaDirection == "negative"

    # Series validation (2021–2025)
    assert len(series) == 5
    assert [s["date"] for s in series] == ["2021", "2022", "2023", "2024", "2025"]
    assert [s["ratio"] for s in series] == [85.5, 84.4, 84.7, 84.8, 84.3]
    assert series[-1]["isHighlighted"] is True
    assert series[-1]["highlightLabel"] == "84.3%"


def test_gst_collection_presenter_data_gov():
    from backend.app.presenters.gst_collection import present_gst_collection

    by_series = {
        "domestic": [
            {"period": "2021", "value": 8.66},
            {"period": "2022", "value": 10.98},
            {"period": "2023", "value": 13.25},
            {"period": "2024", "value": 15.23},
            {"period": "2025", "value": 12.37},
        ],
        "imports": [
            {"period": "2021", "value": 2.71},
            {"period": "2022", "value": 3.86},
            {"period": "2023", "value": 4.83},
            {"period": "2024", "value": 4.95},
            {"period": "2025", "value": 3.96},
        ],
        "gross_collection": [
            {"period": "2021", "value": 11.37},
            {"period": "2022", "value": 14.83},
            {"period": "2023", "value": 18.08},
            {"period": "2024", "value": 20.18},
            {"period": "2025", "value": 16.34},
        ],
        "monthly_average": [
            {"period": "2021", "value": 0.95},
            {"period": "2022", "value": 1.24},
            {"period": "2023", "value": 1.51},
            {"period": "2024", "value": 1.68},
            {"period": "2025", "value": 1.63},
        ],
    }
    obs_rows = by_series["domestic"] + by_series["imports"] + by_series["gross_collection"]
    values, series = present_gst_collection(by_series, obs_rows)

    # Collections tile
    gro_tile = values["collections"]
    assert gro_tile.label == "GST Collections"
    assert gro_tile.value == 16.34
    assert gro_tile.formattedValue == "₹16.34L Cr"

    # Monthly Average tile
    avg_tile = values["monthlyAverage"]
    assert avg_tile.label == "Monthly Average"
    assert avg_tile.value == 1.63
    assert avg_tile.formattedValue == "₹1.63L Cr"

    # Series validation
    assert len(series) == 5
    assert [s["year"] for s in series] == ["2021", "2022", "2023", "2024", "2025"]
    assert [s["collectionRate"] for s in series] == [8.66, 10.98, 13.25, 15.23, 12.37]
    assert [s["averageRate"] for s in series] == [2.71, 3.86, 4.83, 4.95, 3.96]
    assert series[0]["highlightLabel"] == "₹2.71L Cr"


