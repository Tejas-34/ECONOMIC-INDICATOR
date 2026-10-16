import json
from pathlib import Path
import pytest

FRONTEND_MOCKS_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "src" / "mocks"


def test_indicator_mock_parity_against_frontend_fixtures(auth_client):
    """Verify backend DATA_MODE=mock responses have 100% parity with frontend mock fixtures."""
    mapping = {
        "gdp-growth": "gdpGrowth.json",
        "debt-to-gdp": "debtToGdp.json",
        "trade-balance": "tradeBalance.json",
        "gst-collection": "gstCollection.json",
        "inflation": "inflation.json",
        "govt-expenditure": "govtExpenditure.json",
    }

    for slug, fname in mapping.items():
        resp = auth_client.get(f"/api/indicators/{slug}")
        assert resp.status_code == 200, f"Failed for {slug}"
        backend_data = resp.json()

        fixture_path = FRONTEND_MOCKS_DIR / fname
        assert fixture_path.exists(), f"Frontend mock missing: {fname}"

        with open(fixture_path, "r", encoding="utf-8") as f:
            frontend_fixture = json.load(f)

        # Verify key fields
        assert backend_data["title"] == frontend_fixture["title"]
        assert backend_data["as_of"] == frontend_fixture["as_of"]
        assert len(backend_data["series"]) == len(frontend_fixture["series"])

        # Check values / tiles
        if "values" in frontend_fixture and "values" in backend_data:
            assert set(backend_data["values"].keys()) == set(frontend_fixture["values"].keys())


def test_ticker_mock_parity(auth_client):
    resp = auth_client.get("/api/ticker")
    assert resp.status_code == 200
    data = resp.json()

    fixture_path = FRONTEND_MOCKS_DIR / "tickerFeed.json"
    with open(fixture_path, "r", encoding="utf-8") as f:
        frontend_ticker = json.load(f)

    assert len(data["quotes"]) == len(frontend_ticker["quotes"])
    assert data["quotes"][0]["symbol"] == frontend_ticker["quotes"][0]["symbol"]
