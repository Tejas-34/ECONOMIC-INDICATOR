import asyncio
from datetime import datetime, timezone
from typing import Any, Dict
from backend.app.collectors.data_gov import DataGovGSTCollector
from backend.app.collectors.imf import IMFCollector
from backend.app.collectors.seed_loader import load_seed_files_if_changed
from backend.app.collectors.world_bank import WorldBankCollector
from backend.app.config import settings

_macro_job_lock = asyncio.Lock()


async def run_macro_collection_job() -> Dict[str, Any]:
    """Execute macro data collection job across World Bank, IMF, and seed loaders."""
    if _macro_job_lock.locked():
        return {"status": "skipped_already_running"}

    async with _macro_job_lock:
        if settings.DATA_MODE == "mock":
            return {"status": "skipped_mock_mode", "rows": 0}

        from backend.app.cache import invalidate_macro_cache
        from backend.app.db import execute_many, execute_write

        started_at = datetime.now(timezone.utc)
        total_rows = 0
        status_str = "success"
        error_msg = None

        try:
            wb = WorldBankCollector()
            imf = IMFCollector()
            gst_col = DataGovGSTCollector()

            # Run upstream collections
            gdp_rows = await wb.collect_gdp_growth()
            inflation_rows = await wb.collect_inflation()
            trade_rows = await wb.collect_trade()
            debt_rows = await imf.collect_debt_to_gdp()
            gst_rows = await gst_col.collect_gst_collection()

            all_rows = gdp_rows + inflation_rows + trade_rows + debt_rows + gst_rows

            if all_rows:
                upsert_sql = """
                    INSERT INTO observations (indicator, series, period, value, unit, basis, source_id, as_of)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (indicator, series, period) DO UPDATE SET
                        value = EXCLUDED.value,
                        unit = EXCLUDED.unit,
                        basis = EXCLUDED.basis,
                        source_id = EXCLUDED.source_id,
                        as_of = EXCLUDED.as_of,
                        fetched_at = NOW();
                """
                await execute_many(upsert_sql, all_rows)
                total_rows += len(all_rows)

            # Ingest seed files as well
            seed_res = await load_seed_files_if_changed()
            total_rows += sum(v for v in seed_res.values() if isinstance(v, int))

            # Invalidate cached indicator responses
            invalidate_macro_cache()

        except Exception as e:
            status_str = "failed"
            error_msg = str(e)
            print(f"[MacroJob] Macro collection failed: {e}")

        finished_at = datetime.now(timezone.utc)
        try:
            await execute_write("""
                INSERT INTO collector_runs (job, started_at, finished_at, status, rows, error)
                VALUES ('macro_job', %s, %s, %s, %s, %s);
            """, (started_at, finished_at, status_str, total_rows, error_msg))
        except Exception as log_err:
            print(f"[MacroJob] Failed to log run to collector_runs: {log_err}")

        return {
            "status": status_str,
            "rows": total_rows,
            "error": error_msg,
            "duration_seconds": round((finished_at - started_at).total_seconds(), 2)
        }
