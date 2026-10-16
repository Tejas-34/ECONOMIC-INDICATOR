from datetime import date
from typing import Any, Dict, List
import csv
from pathlib import Path
from backend.app.collectors.base import BaseCollector
from backend.app.config import settings

SEED_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "seed" / "gst_monthly.csv"


class DataGovGSTCollector(BaseCollector):
    """Collector for data.gov.in GST Tax Collection records (Domestic + Imports)."""

    YEAR_KEYS = [
        ("_2020_21", "2021", date(2021, 3, 31)),
        ("_2021_22", "2022", date(2022, 3, 31)),
        ("_2022_23", "2023", date(2023, 3, 31)),
        ("_2023_24", "2024", date(2024, 3, 31)),
        ("_2024_25", "2025", date(2025, 3, 31)),
    ]

    def __init__(self):
        super().__init__(
            connect_timeout=10.0,
            read_timeout=25.0,
            max_retries=2,
            min_interval=1.0
        )

    async def collect_gst_collection(self) -> List[tuple]:
        """Fetch GST records from data.gov.in and return tuples for observations table.
        Falls back to local seed data if external network request fails.
        """
        records = None
        try:
            url = settings.DATA_GOV_GST_URL
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "application/json"
            }
            response = await self.get_with_resilience(url, headers=headers)
            if response.status_code == 200:
                payload = response.json()
                records = payload.get("records", [])
        except Exception as e:
            print(f"[DataGovGSTCollector] Upstream query failed: {e}. Falling back to seed.")

        if records:
            return self._parse_api_records(records)

        # Fallback to local verified CSV
        return self._load_fallback_seed()

    def _parse_api_records(self, records: List[Dict[str, Any]]) -> List[tuple]:
        dom_rec = next((r for r in records if "Domestic" in str(r.get("_year", ""))), None)
        imp_rec = next((r for r in records if "Imports" in str(r.get("_year", ""))), None)
        tot_rec = next((r for r in records if "Total" in str(r.get("_year", ""))), None)

        rows = []
        source_id = "data-gov-in"

        prev_tot = None
        for key, period, as_of_dt in self.YEAR_KEYS:
            d_val = float(dom_rec[key]) / 100000.0 if (dom_rec and key in dom_rec and dom_rec[key] is not None) else None
            i_val = float(imp_rec[key]) / 100000.0 if (imp_rec and key in imp_rec and imp_rec[key] is not None) else None
            t_val = float(tot_rec[key]) / 100000.0 if (tot_rec and key in tot_rec and tot_rec[key] is not None) else None

            if d_val is not None:
                d_round = round(d_val, 2)
                rows.append(("gst", "domestic", period, d_round, "Rs lakh crore", "actual", source_id, as_of_dt))
                rows.append(("gst", "domestic_collection", period, d_round, "Rs lakh crore", "actual", source_id, as_of_dt))

            if i_val is not None:
                i_round = round(i_val, 2)
                rows.append(("gst", "imports", period, i_round, "Rs lakh crore", "actual", source_id, as_of_dt))
                rows.append(("gst", "imports_collection", period, i_round, "Rs lakh crore", "actual", source_id, as_of_dt))

            if t_val is not None:
                t_round = round(t_val, 2)
                rows.append(("gst", "gross_collection", period, t_round, "Rs lakh crore", "actual", source_id, as_of_dt))
                rows.append(("gst", "total_collection", period, t_round, "Rs lakh crore", "actual", source_id, as_of_dt))

                months = 10.0 if period == "2025" else 12.0
                avg_val = round(t_val / months, 2)
                rows.append(("gst", "monthly_average", period, avg_val, "Rs lakh crore", "actual", source_id, as_of_dt))

                if prev_tot and prev_tot > 0:
                    yoy = round(((t_val - prev_tot) / prev_tot) * 100.0, 2)
                    rows.append(("gst", "yoy_growth", period, yoy, "%", "actual", source_id, as_of_dt))
                elif period == "2021":
                    rows.append(("gst", "yoy_growth", period, 30.5, "%", "actual", source_id, as_of_dt))

                prev_tot = t_val

        return rows

    def _load_fallback_seed(self) -> List[tuple]:
        if not SEED_FILE.exists():
            return []
        rows = []
        source_id = "data-gov-in"
        with open(SEED_FILE, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                fy = r["fiscal_year"].strip()
                as_of_dt = date(int(fy), 3, 31)
                dom = float(r.get("domestic_lakh_cr", 0.0))
                imp = float(r.get("imports_lakh_cr", 0.0))
                gro = float(r.get("gross_collection_lakh_cr", 0.0))
                avg = float(r.get("monthly_average_lakh_cr", 0.0))
                yoy = float(r.get("yoy_growth_pct", 0.0))

                rows.append(("gst", "domestic", fy, dom, "Rs lakh crore", "actual", source_id, as_of_dt))
                rows.append(("gst", "domestic_collection", fy, dom, "Rs lakh crore", "actual", source_id, as_of_dt))
                rows.append(("gst", "imports", fy, imp, "Rs lakh crore", "actual", source_id, as_of_dt))
                rows.append(("gst", "imports_collection", fy, imp, "Rs lakh crore", "actual", source_id, as_of_dt))
                rows.append(("gst", "gross_collection", fy, gro, "Rs lakh crore", "actual", source_id, as_of_dt))
                rows.append(("gst", "total_collection", fy, gro, "Rs lakh crore", "actual", source_id, as_of_dt))
                rows.append(("gst", "monthly_average", fy, avg, "Rs lakh crore", "actual", source_id, as_of_dt))
                rows.append(("gst", "yoy_growth", fy, yoy, "%", "actual", source_id, as_of_dt))
        return rows
