from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from backend.app.config import settings

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")
_scheduler: Optional[AsyncIOScheduler] = None


async def purge_old_ticker_history() -> None:
    """Purge ticker history older than 7 days per data retention specification."""
    if settings.DATA_MODE == "mock":
        return
    try:
        from backend.app.db import execute_write
        deleted = await execute_write(
            "DELETE FROM ticker_history WHERE as_of < NOW() - INTERVAL '7 days';"
        )
        print(f"[Scheduler] Purged {deleted} historical ticker records older than 7 days.")
    except Exception as e:
        print(f"[Scheduler] History purge error: {e}")


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone=KOLKATA_TZ)

        from backend.app.services.macro_job import run_macro_collection_job
        from backend.app.services.ticker_service import run_ticker_ingestion_job

        # 1. Ticker job during market hours: every 20 seconds, Mon-Fri 09:15-15:30
        _scheduler.add_job(
            run_ticker_ingestion_job,
            trigger=CronTrigger(
                day_of_week="mon-fri",
                hour="9-15",
                minute="*",
                second="*/20",
                timezone=KOLKATA_TZ
            ),
            id="ticker_market_hours",
            name="Ticker Market Hours (20s)",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60
        )

        # 2. Ticker job outside market hours: every 10 minutes
        _scheduler.add_job(
            run_ticker_ingestion_job,
            trigger=IntervalTrigger(minutes=10, timezone=KOLKATA_TZ),
            id="ticker_off_hours",
            name="Ticker Off Hours (10m)",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=120
        )

        # 3. Daily macro collection job: 06:30 IST every morning
        _scheduler.add_job(
            run_macro_collection_job,
            trigger=CronTrigger(hour=6, minute=30, timezone=KOLKATA_TZ),
            id="macro_daily",
            name="Macroeconomic Daily Collector (06:30 IST)",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=300
        )

        # 4. Daily ticker history 7-day retention purge: midnight IST
        _scheduler.add_job(
            purge_old_ticker_history,
            trigger=CronTrigger(hour=0, minute=0, timezone=KOLKATA_TZ),
            id="history_cleanup",
            name="Ticker History Purge (7 Days)",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=600
        )

    return _scheduler


def start_scheduler() -> None:
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        print("[Scheduler] APScheduler AsyncIOScheduler started successfully.")


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        print("[Scheduler] APScheduler shut down cleanly.")
        _scheduler = None
