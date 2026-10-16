from datetime import date
from typing import Any, Dict, List
from backend.app.collectors.base import BaseCollector
from backend.app.config import settings


class IMFCollector(BaseCollector):
    """Collector for IMF DataMapper: Debt to GDP Ratio (IND and USA)."""

    INDICATOR = "GGXWDG_NGDP"

    async def collect_debt_to_gdp(self, start_year: int = 2021, end_year: int = 2025) -> List[tuple]:
        url = f"{settings.IMF_DATAMAPPER_BASE_URL}/{self.INDICATOR}/IND/USA"
        response = await self.get_with_resilience(url)
        if response.status_code != 200:
            return []

        payload = response.json()
        indicator_data = payload.get("values", {}).get(self.INDICATOR, {})
        ind_series = indicator_data.get("IND", {})
        usa_series = indicator_data.get("USA", {})

        rows = []
        for year_str in [str(y) for y in range(start_year, end_year + 1)]:
            # India Debt to GDP
            ind_val = ind_series.get(year_str)
            if ind_val is not None:
                ind_val = float(ind_val)
                # Plausibility check: 0% to 200%
                if 0.0 <= ind_val <= 200.0:
                    rows.append((
                        "debt-to-gdp", "india", year_str, ind_val, "%", "actual", "imf", date(int(year_str), 12, 31)
                    ))

            # USA Debt to GDP
            usa_val = usa_series.get(year_str)
            if usa_val is not None:
                usa_val = float(usa_val)
                if 0.0 <= usa_val <= 200.0:
                    rows.append((
                        "debt-to-gdp", "usa", year_str, usa_val, "%", "actual", "imf", date(int(year_str), 12, 31)
                    ))

        return rows
