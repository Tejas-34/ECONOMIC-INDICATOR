import asyncio
import random
import time
from typing import Any, Dict, Optional
import httpx
from urllib.parse import urlparse
from backend.app.config import settings


class CircuitBreakerOpenException(Exception):
    """Raised when request is blocked because the host's circuit breaker is open."""
    pass


class BaseCollector:
    """Resilient HTTP collector base enforcing timeouts, retry backoff with jitter,

    per-host rate limiting (15s interval), and a 5-failure circuit breaker.
    """

    # Class-level state across collector instances for per-host throttling and breakers
    _last_request_time: Dict[str, float] = {}
    _failure_counts: Dict[str, int] = {}
    _circuit_open_until: Dict[str, float] = {}
    _host_locks: Dict[str, asyncio.Lock] = {}

    def __init__(
        self,
        connect_timeout: float = settings.COLLECTOR_TIMEOUT_CONNECT,
        read_timeout: float = settings.COLLECTOR_TIMEOUT_READ,
        max_retries: int = settings.COLLECTOR_MAX_RETRIES,
        min_interval: float = settings.COLLECTOR_MIN_INTERVAL_SECONDS,
        failure_threshold: int = settings.COLLECTOR_CIRCUIT_FAILURES,
        circuit_reset_seconds: float = settings.COLLECTOR_CIRCUIT_RESET_SECONDS
    ):
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.max_retries = max_retries
        self.min_interval = min_interval
        self.failure_threshold = failure_threshold
        self.circuit_reset_seconds = circuit_reset_seconds

    def _get_host(self, url: str) -> str:
        parsed = urlparse(url)
        return parsed.netloc or "default"

    def _get_host_lock(self, host: str) -> asyncio.Lock:
        if host not in self._host_locks:
            self._host_locks[host] = asyncio.Lock()
        return self._host_locks[host]

    def _check_circuit(self, host: str) -> None:
        open_until = self._circuit_open_until.get(host, 0.0)
        now = time.time()
        if now < open_until:
            remaining = int(open_until - now)
            raise CircuitBreakerOpenException(
                f"Circuit breaker for host '{host}' is OPEN. Backing off for {remaining}s remaining."
            )
        # If open period expired, half-open trial
        if host in self._circuit_open_until and now >= open_until:
            del self._circuit_open_until[host]

    def _record_success(self, host: str) -> None:
        self._failure_counts[host] = 0
        self._circuit_open_until.pop(host, None)

    def _record_failure(self, host: str) -> None:
        fails = self._failure_counts.get(host, 0) + 1
        self._failure_counts[host] = fails
        if fails >= self.failure_threshold:
            open_until = time.time() + self.circuit_reset_seconds
            self._circuit_open_until[host] = open_until
            print(f"[CircuitBreaker] Host '{host}' reached {fails} consecutive failures. Tripping OPEN for {self.circuit_reset_seconds}s.")

    async def _throttle(self, host: str) -> None:
        async with self._get_host_lock(host):
            last_time = self._last_request_time.get(host, 0.0)
            now = time.time()
            elapsed = now - last_time
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                await asyncio.sleep(wait_time)
            self._last_request_time[host] = time.time()

    async def get_with_resilience(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Any] = None,
        bypass_throttle: bool = False
    ) -> httpx.Response:
        """Execute HTTP GET with circuit breaker, per-host throttling, and exponential backoff retry."""
        host = self._get_host(url)
        self._check_circuit(host)

        if not bypass_throttle:
            await self._throttle(host)

        timeout = httpx.Timeout(
            connect=self.connect_timeout,
            read=self.read_timeout,
            write=5.0,
            pool=5.0
        )

        last_exception: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                    response = await client.get(url, headers=headers, cookies=cookies)
                    if response.status_code >= 500:
                        raise httpx.HTTPStatusError(
                            f"Server Error {response.status_code}",
                            request=response.request,
                            response=response
                        )
                    if response.status_code in (401, 403, 429):
                        # Trippable client error
                        self._record_failure(host)
                        return response

                    # Successful response
                    self._record_success(host)
                    return response

            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                last_exception = exc
                if attempt == self.max_retries:
                    self._record_failure(host)
                    break
                # Exponential backoff with random jitter (1.0 * 2^(attempt-1) + jitter)
                delay = (1.0 * (2 ** (attempt - 1))) + random.uniform(0.1, 0.5)
                await asyncio.sleep(delay)

        raise last_exception or RuntimeError(f"Failed to fetch {url} after {self.max_retries} attempts.")
