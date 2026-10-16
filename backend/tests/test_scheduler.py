import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, AsyncMock
from backend.app.scheduler import (
    get_scheduler,
    get_job_stats,
    record_job_execution,
    run_dynamic_ticker_job,
    bootstrap_macro_if_empty
)


def test_scheduler_job_registration():
    sched = get_scheduler()
    job_ids = [j.id for j in sched.get_jobs()]
    
    # Must have single dynamic ticker job, not separate market/off-hours jobs
    assert "ticker_dynamic" in job_ids
    assert "ticker_market_hours" not in job_ids
    assert "ticker_off_hours" not in job_ids

    # Must have startup macro bootstrap job
    assert "macro_bootstrap" in job_ids

    # Must have daily jobs
    assert "macro_daily" in job_ids
    assert "history_cleanup" in job_ids


def test_health_reports_job_execution_and_age(client):
    record_job_execution("test_job", "Test Job Name", status="success")

    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "jobs" in data

    # Verify test_job is present in stats with non-negative age
    test_stat = data["jobs"].get("test_job")
    assert test_stat is not None
    assert test_stat["status"] == "success"
    assert test_stat["age_seconds"] is not None
    assert test_stat["age_seconds"] >= 0.0


@pytest.mark.asyncio
async def test_dynamic_ticker_job_during_market_hours():
    with patch("backend.app.market_hours.is_market_hours", return_value=True):
        with patch("backend.app.services.ticker_service.run_ticker_ingestion_job", new_callable=AsyncMock) as mock_ingest:
            mock_ingest.return_value = {"status": "success", "quotes": 3}
            await run_dynamic_ticker_job()
            assert mock_ingest.call_count == 1

            stats = get_job_stats()
            assert "ticker_dynamic" in stats
            assert stats["ticker_dynamic"]["status"] == "success"
