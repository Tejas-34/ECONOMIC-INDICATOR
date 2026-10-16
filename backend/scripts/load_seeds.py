#!/usr/bin/env python3
"""Standalone script to idempotently load curated seed CSV files into PostgreSQL."""

import asyncio
import sys
from backend.app.config import settings
from backend.app.db import init_pool, close_pool
from backend.app.collectors.seed_loader import load_seed_files_if_changed


async def main():
    print("[LoadSeeds] Initializing connection pool...")
    try:
        await init_pool()
        print("[LoadSeeds] Loading seed files if modified...")
        results = await load_seed_files_if_changed()
        print(f"[LoadSeeds] Finished seed ingestion: {results}")
    except Exception as e:
        print(f"[LoadSeeds] Error during seed loading: {e}", file=sys.stderr)
        if settings.DATA_MODE != "mock":
            sys.exit(1)
    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
