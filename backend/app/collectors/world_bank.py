from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from backend.app.collectors.base import BaseCollector
from backend.app.config import settings


class WorldBankCollector(BaseCollector):
    """Collector for World Bank indicators: GDP Growth, Inflation, and Trade Balance."""

    INDICATORS = {
        "gdp": "NY.GDP.MKTP.KD.ZG",
        "inflation": "FP.CPI.TOTL.ZG",
        "exports": "NE.EXP.GNFS.CD",
        "imports": "NE.IMP.GNFS.CD",
        "trade_balance_pct": "NE.RSB.GNFS.ZS",
    }

    async def fetch_series(
        self,
        indicator_code: str,
        country_code: str = "IND",
        start_year: int = 2021,
        end_year: int = 2025
    ) -> List[Dict[str, Any]]:
        url = (
            f"{settings.WORLD_BANK_BASE_URL}/country/{country_code}/indicator/{indicator_code}"
            f"?date={start_year}:{end_year}&format=json"
        )
        response = await self.get_with_resilience(url)
        if response.status_code != 200:
            return []

        payload = response.json()
        if not isinstance(payload, list) or len(payload) < 2:
            return []

        records = payload[1]
        results = []
        for rec in records:
            val = rec.get("value")
            year = str(rec.get("date"))
            results.append({
                "period": year,
                "value": float(val) if val is not None else None,
                "as_of": date(int(year), 12, 31) if year.isdigit() else date.today()
            })
        # Sort chronologically
        results.sort(key=lambda x: x["period"])
        return results

    async def collect_gdp_growth(self) -> List[tuple]:
        """Collect GDP growth for India and World."""
        ind_points = await self.fetch_series(self.INDICATORS["gdp"], country_code="IND")
        wld_points = await self.fetch_series(self.INDICATORS["gdp"], country_code="WLD")

        rows = []
        for p in ind_points:
            # Plausibility check: -20% to +30%
            val = p["value"]
            if val is not None and not (-20.0 <= val <= 30.0):
                continue
            rows.append((
                "gdp-growth", "india", p["period"], val, "%", "actual", "worldbank", p["as_of"]
            ))

        for p in wld_points:
            val = p["value"]
            if val is not None and not (-20.0 <= val <= 30.0):
                continue
            rows.append((
                "gdp-growth", "world", p["period"], val, "%", "actual", "worldbank", p["as_of"]
            ))

        return rows

    async def collect_inflation(self) -> List[tuple]:
        """Collect CPI inflation for India and add RBI Target policy constant."""
        cpi_points = await self.fetch_series(self.INDICATORS["inflation"], country_code="IND")
        rows = []
        for p in cpi_points:
            val = p["value"]
            # Plausibility check: -10% to +50%
            if val is not None and not (-10.0 <= val <= 50.0):
                continue
            rows.append((
                "inflation", "cpi_rate", p["period"], val, "%", "actual", "worldbank", p["as_of"]
            ))

        # RBI Target policy constant 4.0%
        today = date.today()
        for yr in ["2021", "2022", "2023", "2024", "2025"]:
            rows.append((
                "inflation", "rbi_target", yr, 4.0, "%", "actual", "worldbank", today
            ))

        return rows

    async def collect_trade(self) -> List[tuple]:
        """Collect Exports, Imports (US$ B), and Trade Balance % of GDP."""
        exp_points = await self.fetch_series(self.INDICATORS["exports"], country_code="IND")
        imp_points = await self.fetch_series(self.INDICATORS["imports"], country_code="IND")
        bal_points = await self.fetch_series(self.INDICATORS["trade_balance_pct"], country_code="IND")

        rows = []
        # Convert values to US$ Billions (divide by 1e9)
        for p in exp_points:
            val_b = round(p["value"] / 1e9, 2) if p["value"] is not None else None
            rows.append((
                "trade", "exports", p["period"], val_b, "US$ B", "actual", "worldbank", p["as_of"]
            ))

        for p in imp_points:
            val_b = round(p["value"] / 1e9, 2) if p["value"] is not None else None
            rows.append((
                "trade", "imports", p["period"], val_b, "US$ B", "actual", "worldbank", p["as_of"]
            ))

        for p in bal_points:
            val = round(p["value"], 2) if p["value"] is not None else None
            rows.append((
                "trade", "balance_pct", p["period"], val, "% of GDP", "actual", "worldbank", p["as_of"]
            ))

        return rows
