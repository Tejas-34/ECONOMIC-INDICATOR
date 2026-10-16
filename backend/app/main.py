import sys
from pathlib import Path

# Ensure repository root is in sys.path
_repo_root = str(Path(__file__).resolve().parent.parent.parent)
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from backend.app.config import settings, validate_startup_secrets
from backend.app.routes import admin, auth, health, indicators, ticker
from backend.app.security.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context managing database pool, background scheduler, and initial startup tasks."""
    # Startup Guard & Configuration Validation
    if settings.DATA_MODE == "live":
        validate_startup_secrets(settings)
        try:
            from backend.app.db import init_pool
            await init_pool()
        except Exception as e:
            print(f"[Lifespan] DB pool init warning: {e}")

        try:
            from backend.scripts.migrate import run_migrations
            run_migrations()
        except Exception as e:
            print(f"[Lifespan] Migrations warning: {e}")

        try:
            from backend.scripts.seed_user import seed_evaluation_user
            seed_evaluation_user()
        except Exception as e:
            print(f"[Lifespan] Seed user warning: {e}")

        try:
            from backend.app.collectors.seed_loader import load_seed_files_if_changed
            await load_seed_files_if_changed()
        except Exception as e:
            print(f"[Lifespan] Seed data loading warning: {e}")

        try:
            from backend.app.scheduler import start_scheduler
            start_scheduler()
        except Exception as e:
            print(f"[Lifespan] Scheduler start warning: {e}")

    yield

    # Shutdown
    if settings.DATA_MODE == "live":
        try:
            from backend.app.scheduler import shutdown_scheduler
            shutdown_scheduler()
        except Exception as e:
            print(f"[Lifespan] Scheduler shutdown warning: {e}")
        try:
            from backend.app.db import close_pool
            await close_pool()
        except Exception as e:
            print(f"[Lifespan] DB pool close warning: {e}")


app = FastAPI(
    title="Economic Indicator Dashboard API",
    description="FastAPI backend serving macroeconomic indicators and live market index quotes.",
    version="1.0.0",
    lifespan=lifespan
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration supporting single origin, comma-separated list, or wildcard regex
cors_origins = [orig.strip() for orig in settings.FRONTEND_ORIGIN.split(",") if orig.strip() and orig.strip() != "*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["http://localhost:5173", "http://localhost"],
    allow_origin_regex=r".*" if "*" in settings.FRONTEND_ORIGIN else None,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["ETag", "Content-Disposition"]
)

# Application routes
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(indicators.router)
app.include_router(ticker.router)


@app.get("/")
async def root():
    return {
        "service": "Economic Indicator Dashboard API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
