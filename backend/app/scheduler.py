from datetime import datetime, timezone
from typing import Any, Dict, Optional
from zoneinfo import ZoneInfo
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from backend.app.config import settings

KOLKATA_TZ = ZoneInfo("Asia/Kolkata")
_scheduler: Optional[AsyncIOScheduler] = None
_job_execution_history: Dict[str, Dict[str, Any]] = {}
_last_off_hours_ticker_run: Optional[datetime] = None


def record_job_execution(job_id: str, name: str, status: str = "success", error: Optional[str] = None) -> None:
    """Record job completion timestamp and status for health reporting."""
    _job_execution_history[job_id] = {
        "name": name,
        "last_run": datetime.now(timezone.utc),
        "status": status,
        "error": error
    }


def get_job_stats() -> Dict[str, Dict[str, Any]]:
    """Return execution age and status per job for /health endpoint."""
    now = datetime.now(timezone.utc)
    stats: Dict[str, Dict[str, Any]] = {}

    sched = _scheduler
    if sched:
        for job in sched.get_jobs():
            hist = _job_execution_history.get(job.id, {})
            last_run = hist.get("last_run")
            age = (now - last_run).total_seconds() if last_run else None
            nrt = getattr(job, "next_run_time", None)
            stats[job.id] = {
                "name": job.name,
                "last_run": last_run.isoformat() if last_run else None,
                "age_seconds": round(age, 1) if age is not None else None,
                "status": hist.get("status", "pending"),
                "next_run_time": nrt.isoformat() if nrt else None
            }

    for j_id, hist in _job_execution_history.items():
        if j_id not in stats:
            last_run = hist.get("last_run")
            age = (now - last_run).total_seconds() if last_run else None
            stats[j_id] = {
                "name": hist.get("name", j_id),
                "last_run": last_run.isoformat() if last_run else None,
                "age_seconds": round(age, 1) if age is not None else None,
                "status": hist.get("status", "completed"),
                "next_run_time": None
            }

    return stats


async def purge_old_ticker_history() -> None:
    """Purge ticker history older than 7 days per data retention specification."""
    job_id = "history_cleanup"
    job_name = "Ticker History Purge (7 Days)"
    if settings.DATA_MODE == "mock":
        record_job_execution(job_id, job_name, status="skipped_mock")
        return
    try:
        from backend.app.db import execute_write
        deleted = await execute_write(
            "DELETE FROM ticker_history WHERE as_of < NOW() - INTERVAL '7 days';"
        )
        print(f"[Scheduler] Purged {deleted} historical ticker records older than 7 days.")
        record_job_execution(job_id, job_name, status="success")
    except Exception as e:
        print(f"[Scheduler] History purge error: {e}")
        record_job_execution(job_id, job_name, status="error", error=str(e))


async def run_dynamic_ticker_job() -> None:
    """Single dynamic-cadence ticker ingestion: 20s during market hours, 10m off-hours (I6)."""
    global _last_off_hours_ticker_run
    from backend.app.market_hours import is_market_hours
    from backend.app.services.ticker_service import run_ticker_ingestion_job

    job_id = "ticker_dynamic"
    job_name = "Dynamic Ticker Ingestion (20s market / 10m off-hours)"

    now_ist = datetime.now(KOLKATA_TZ)
    in_market = is_market_hours(now_ist)

    should_run = False
    if in_market:
        should_run = True
    else:
        # Off-hours: run every 10 minutes (600s)
        now_utc = datetime.now(timezone.utc)
        if _last_off_hours_ticker_run is None or (now_utc - _last_off_hours_ticker_run).total_seconds() >= 600:
            _last_off_hours_ticker_run = now_utc
            should_run = True

    if should_run:
        try:
            res = await run_ticker_ingestion_job()
            record_job_execution(job_id, job_name, status=res.get("status", "success"))
        except Exception as e:
            record_job_execution(job_id, job_name, status="error", error=str(e))


async def run_scheduled_macro_job() -> None:
    """Execute scheduled daily macro collection at 06:30 IST."""
    from backend.app.services.macro_job import run_macro_collection_job
    job_id = "macro_daily"
    job_name = "Macroeconomic Daily Collector (06:30 IST)"
    try:
        res = await run_macro_collection_job()
        record_job_execution(job_id, job_name, status=res.get("status", "success"))
    except Exception as e:
        record_job_execution(job_id, job_name, status="error", error=str(e))


async def bootstrap_macro_if_empty() -> None:
    """Startup macro collection if observations table is empty (non-blocking) (I6)."""
    job_id = "macro_bootstrap"
    job_name = "Startup Macro Bootstrap If Empty"
    if settings.DATA_MODE == "mock":
        record_job_execution(job_id, job_name, status="skipped_mock")
        return
    try:
        from backend.app.db import fetch_one
        row = await fetch_one("SELECT COUNT(*) AS cnt FROM observations;")
        cnt = row["cnt"] if row else 0
        if cnt == 0:
            print("[Scheduler] observations table is empty. Bootstrapping macro collection.")
            from backend.app.services.macro_job import run_macro_collection_job
            res = await run_macro_collection_job()
            record_job_execution(job_id, job_name, status=res.get("status", "bootstrapped"))
        else:
            print(f"[Scheduler] observations table has {cnt} rows. Macro bootstrap skipped.")
            record_job_execution(job_id, job_name, status="skipped_populated")
    except Exception as e:
        print(f"[Scheduler] Macro bootstrap warning: {e}")
        record_job_execution(job_id, job_name, status="error", error=str(e))


def get_scheduler() -> AsyncIOScheduler:
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler(timezone=KOLKATA_TZ)

        now_utc = datetime.now(timezone.utc)

        # 1. Single dynamic-cadence ticker job (20s market hours / 10m off-hours), immediate on startup
        _scheduler.add_job(
            run_dynamic_ticker_job,
            trigger=IntervalTrigger(seconds=20, timezone=KOLKATA_TZ),
            next_run_time=now_utc,
            id="ticker_dynamic",
            name="Dynamic Ticker Ingestion (20s market / 10m off-hours)",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=60
        )

        # 2. Non-blocking startup macro collection if observations is empty
        _scheduler.add_job(
            bootstrap_macro_if_empty,
            next_run_time=now_utc,
            id="macro_bootstrap",
            name="Startup Macro Bootstrap If Empty",
            max_instances=1,
            coalesce=True,
            misfire_grace_time=120
        )

        # 3. Daily macro collection job: 06:30 IST every morning
        _scheduler.add_job(
            run_scheduled_macro_job,
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

