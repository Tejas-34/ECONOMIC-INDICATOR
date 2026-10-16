import pytest
import respx
import httpx
from backend.app.collectors.base import BaseCollector, CircuitBreakerOpenException
from backend.app.collectors.world_bank import WorldBankCollector
from backend.app.collectors.imf import IMFCollector


@pytest.mark.asyncio
async def test_base_collector_retry_and_circuit_breaker():
    collector = BaseCollector(
        connect_timeout=1.0,
        read_timeout=1.0,
        max_retries=2,
        min_interval=0.01,
        failure_threshold=3,
        circuit_reset_seconds=60.0
    )

    test_url = "https://mock.api.example/fail"
    host = "mock.api.example"

    with respx.mock:
        respx.get(test_url).mock(return_value=httpx.Response(500))

        # 1st failure (exhausts 2 retries)
        with pytest.raises(Exception):
            await collector.get_with_resilience(test_url, bypass_throttle=True)

        # 2nd failure
        with pytest.raises(Exception):
            await collector.get_with_resilience(test_url, bypass_throttle=True)

        # 3rd failure trips the breaker
        with pytest.raises(Exception):
            await collector.get_with_resilience(test_url, bypass_throttle=True)

        # 4th call should immediately raise CircuitBreakerOpenException
        with pytest.raises(CircuitBreakerOpenException):
            await collector.get_with_resilience(test_url, bypass_throttle=True)

    # Clean up class-level state
    BaseCollector._failure_counts.pop(host, None)
    BaseCollector._circuit_open_until.pop(host, None)


@pytest.mark.asyncio
async def test_world_bank_collector_plausibility():
    collector = WorldBankCollector()

    # Mock response with 1 plausible and 1 implausible value (e.g. 999.0% GDP)
    wb_mock_response = [
        {"page": 1, "pages": 1},
        [
            {"indicator": {"id": "NY.GDP.MKTP.KD.ZG"}, "date": "2024", "value": 7.5},
            {"indicator": {"id": "NY.GDP.MKTP.KD.ZG"}, "date": "2025", "value": 999.0}
        ]
    ]

    with respx.mock:
        respx.get(url__startswith="https://api.worldbank.org/v2").mock(
            return_value=httpx.Response(200, json=wb_mock_response)
        )
        rows = await collector.collect_gdp_growth()
        # Ensure 999.0 was discarded by plausibility check (-20% to +30%)
        values = [r[3] for r in rows if r[3] is not None]
        assert 7.5 in values
        assert 999.0 not in values
