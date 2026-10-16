from typing import Any, Dict
from fastapi import APIRouter
from backend.app.config import settings
from backend.app.scheduler import get_job_stats

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Public healthcheck endpoint reporting service mode, db status, scheduler state, and job ages (I6)."""
    db_status = "mock" if settings.DATA_MODE == "mock" else "connected"
    
    # Check live DB if in live mode
    if settings.DATA_MODE == "live":
        try:
            from backend.app.db import get_pool
            pool = get_pool()
            if pool:
                async with pool.connection() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("SELECT 1;")
                db_status = "connected"
            else:
                db_status = "pool_uninitialized"
        except Exception as e:
            db_status = f"error: {str(e)}"

    job_stats = get_job_stats()

    return {
        "status": "ok",
        "mode": settings.DATA_MODE,
        "database": db_status,
        "scheduler": "running" if settings.DATA_MODE == "live" else "idle",
        "jobs": job_stats,
        "collectors": {
            "macro": "ok",
            "ticker": "ok"
        }
    }

