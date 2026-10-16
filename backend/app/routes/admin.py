from typing import Any, Dict, Literal
from fastapi import APIRouter, Depends, HTTPException, Request, status
from backend.app.schemas.auth import AuthUser
from backend.app.security.dependencies import require_role
from backend.app.security.rate_limit import limiter

router = APIRouter(prefix="/api/admin", tags=["Admin Operations"])


@router.post(
    "/refresh/{job}",
    summary="On-demand trigger for data collection jobs (admin only)"
)
@limiter.limit("2/minute")
async def trigger_job_refresh(
    request: Request,
    job: Literal["macro", "ticker", "seeds"],
    admin: AuthUser = Depends(require_role("admin"))
) -> Dict[str, Any]:
    """Admin-only on-demand data refresh route."""
    if job == "macro":
        from backend.app.services.macro_job import run_macro_collection_job
        result = await run_macro_collection_job()
    elif job == "ticker":
        from backend.app.services.ticker_service import run_ticker_ingestion_job
        result = await run_ticker_ingestion_job()
    elif job == "seeds":
        from backend.app.collectors.seed_loader import load_seed_files_if_changed
        result = await load_seed_files_if_changed()
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown job '{job}'. Allowed: macro, ticker, seeds"
        )

    return {
        "status": "ok",
        "job": job,
        "triggered_by": admin.username,
        "result": result
    }
