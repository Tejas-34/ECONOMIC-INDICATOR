import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx
from backend.app.collectors.base import BaseCollector
from backend.app.config import settings

DESKTOP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/market-data/live-market-indices",
}


class NSECollector(BaseCollector):
    """NSE allIndices adapter with session warming and cookie refreshing."""

    def __init__(self):
        super().__init__()
        self._session_cookies: Optional[httpx.Cookies] = None
        self._warmup_lock = asyncio.Lock()

    async def _warm_session(self) -> httpx.Cookies:
        async with self._warmup_lock:
            warm_headers = {
                "User-Agent": DESKTOP_HEADERS["User-Agent"],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
                "Accept-Language": DESKTOP_HEADERS["Accept-Language"],
            }
            async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
                resp = await client.get(settings.NSE_BASE_URL, headers=warm_headers)
                self._session_cookies = resp.cookies
                return self._session_cookies

    async def collect_indices(self) -> List[Dict[str, Any]]:
        """Collect NIFTY BANK and NIFTY IT indices."""
        if not self._session_cookies:
            await self._warm_session()

        url = settings.NSE_ALL_INDICES_URL
        try:
            resp = await self.get_with_resilience(
                url,
                headers=DESKTOP_HEADERS,
                cookies=self._session_cookies,
                bypass_throttle=False
            )
        except Exception:
            # Re-warm and try once more
            await self._warm_session()
            resp = await self.get_with_resilience(
                url,
                headers=DESKTOP_HEADERS,
                cookies=self._session_cookies,
                bypass_throttle=True
            )

        if resp.status_code in (401, 403):
            # Session expired, re-warm
            await self._warm_session()
            resp = await self.get_with_resilience(
                url,
                headers=DESKTOP_HEADERS,
                cookies=self._session_cookies,
                bypass_throttle=True
            )

        if resp.status_code != 200:
            return []

        payload = resp.json()
        indices_list = payload.get("data", [])
        as_of_time = datetime.now(timezone.utc)

        target_symbols = {"NIFTY BANK", "NIFTY IT"}
        results = []

        for item in indices_list:
            index_name = item.get("index") or item.get("indexSymbol")
            if index_name in target_symbols:
                last_val = float(item.get("last", 0.0) or item.get("lastPrice", 0.0))
                change_val = float(item.get("variation", 0.0) or item.get("change", 0.0))
                pct_val = float(item.get("percentChange", 0.0) or item.get("pChange", 0.0))

                # Plausibility check: -20% to +20%
                if not (-20.0 <= pct_val <= 20.0):
                    print(f"[NSECollector] Plausibility failure for {index_name}: pct_change={pct_val}")
                    continue

                results.append({
                    "symbol": index_name,
                    "name": index_name,
                    "last": last_val,
                    "change": change_val,
                    "pct_change": pct_val,
                    "source": "NSE",
                    "source_id": "nse",
                    "as_of": as_of_time
                })

        return results
