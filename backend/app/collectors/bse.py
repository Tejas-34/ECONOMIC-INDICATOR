from datetime import datetime, timezone
from typing import Any, Dict, Optional
import httpx
from backend.app.collectors.base import BaseCollector
from backend.app.config import settings

DESKTOP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
}


class BSECollector(BaseCollector):
    """BSE SENSEX adapter with documented Yahoo Finance fallback."""

    YAHOO_SENSEX_URL = "https://query1.finance.yahoo.com/v8/finance/chart/%5EBSESN?interval=1m&range=1d"

    async def _fetch_yahoo_fallback(self) -> Optional[Dict[str, Any]]:
        """Fallback to Yahoo Finance chart endpoint for SENSEX quote."""
        try:
            resp = await self.get_with_resilience(
                self.YAHOO_SENSEX_URL,
                headers=DESKTOP_HEADERS,
                bypass_throttle=True
            )
            if resp.status_code == 200:
                data = resp.json()
                meta = data.get("chart", {}).get("result", [{}])[0].get("meta", {})
                last_price = meta.get("regularMarketPrice")
                prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")

                if last_price is not None and prev_close is not None:
                    change = round(float(last_price - prev_close), 2)
                    pct_change = round((change / prev_close) * 100, 2)
                    return {
                        "symbol": "SENSEX",
                        "name": "BSE SENSEX",
                        "last": round(float(last_price), 2),
                        "change": change,
                        "pct_change": pct_change,
                        "source": "BSE (via Yahoo Finance)",
                        "source_id": "bse",
                        "as_of": datetime.now(timezone.utc)
                    }
        except Exception as e:
            print(f"[BSECollector] Yahoo fallback error: {e}")
        return None

    async def collect_sensex(self) -> Optional[Dict[str, Any]]:
        """Fetch SENSEX quote from BSE or fallback source."""
        url = settings.BSE_SENSEX_URL
        quote = None
        try:
            resp = await self.get_with_resilience(url, headers=DESKTOP_HEADERS)
            if resp.status_code == 200:
                payload = resp.json()
                # If BSE returned valid data
                data_pts = payload.get("data", [])
                if data_pts:
                    latest = data_pts[-1]
                    last_val = float(latest.get("val", 0.0))
                    quote = {
                        "symbol": "SENSEX",
                        "name": "BSE SENSEX",
                        "last": last_val,
                        "change": 0.0,
                        "pct_change": 0.0,
                        "source": "BSE",
                        "source_id": "bse",
                        "as_of": datetime.now(timezone.utc)
                    }
        except Exception as bse_err:
            print(f"[BSECollector] Direct BSE query error: {bse_err}, falling back to Yahoo Finance")

        if quote is None:
            quote = await self._fetch_yahoo_fallback()

        if quote is not None:
            pct = quote.get("pct_change", 0.0)
            if not (-20.0 <= pct <= 20.0):
                print(f"[BSECollector] Plausibility failure for SENSEX: pct_change={pct}")
                return None

        return quote
