#!/usr/bin/env python3
"""Diagnostic probe utility to verify reachability and latency of all upstream APIs."""

import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from backend.app.config import settings

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "probe_results.json"

DESKTOP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


async def probe_world_bank(client: httpx.AsyncClient) -> Dict[str, Any]:
    url = f"{settings.WORLD_BANK_BASE_URL}/country/IND/indicator/NY.GDP.MKTP.KD.ZG?format=json"
    start = time.time()
    try:
        resp = await client.get(url, timeout=8.0)
        dur = round((time.time() - start) * 1000, 2)
        return {
            "target": "World Bank API (GDP)",
            "url": url,
            "status_code": resp.status_code,
            "latency_ms": dur,
            "reachable": resp.status_code == 200,
            "error": None
        }
    except Exception as e:
        return {
            "target": "World Bank API (GDP)",
            "url": url,
            "status_code": None,
            "latency_ms": round((time.time() - start) * 1000, 2),
            "reachable": False,
            "error": str(e)
        }


async def probe_imf(client: httpx.AsyncClient) -> Dict[str, Any]:
    url = f"{settings.IMF_DATAMAPPER_BASE_URL}/GGXWDG_NGDP/IND"
    start = time.time()
    try:
        resp = await client.get(url, timeout=8.0)
        dur = round((time.time() - start) * 1000, 2)
        return {
            "target": "IMF DataMapper (Debt-to-GDP)",
            "url": url,
            "status_code": resp.status_code,
            "latency_ms": dur,
            "reachable": resp.status_code == 200,
            "error": None
        }
    except Exception as e:
        return {
            "target": "IMF DataMapper (Debt-to-GDP)",
            "url": url,
            "status_code": None,
            "latency_ms": round((time.time() - start) * 1000, 2),
            "reachable": False,
            "error": str(e)
        }


async def probe_nse(client: httpx.AsyncClient) -> Dict[str, Any]:
    warm_url = settings.NSE_BASE_URL
    api_url = settings.NSE_ALL_INDICES_URL
    start = time.time()
    try:
        # Step 1: Warmup session
        warm_resp = await client.get(warm_url, headers=DESKTOP_HEADERS, timeout=8.0)
        cookies = warm_resp.cookies
        # Step 2: Query API
        api_headers = {
            **DESKTOP_HEADERS,
            "Referer": "https://www.nseindia.com/market-data/live-market-indices",
            "Accept": "application/json, text/plain, */*"
        }
        resp = await client.get(api_url, headers=api_headers, cookies=cookies, timeout=8.0)
        dur = round((time.time() - start) * 1000, 2)
        return {
            "target": "NSE allIndices (NIFTY BANK / IT)",
            "url": api_url,
            "status_code": resp.status_code,
            "latency_ms": dur,
            "reachable": resp.status_code == 200,
            "cookies_captured": len(cookies) > 0,
            "error": None if resp.status_code == 200 else f"HTTP {resp.status_code}"
        }
    except Exception as e:
        return {
            "target": "NSE allIndices (NIFTY BANK / IT)",
            "url": api_url,
            "status_code": None,
            "latency_ms": round((time.time() - start) * 1000, 2),
            "reachable": False,
            "error": str(e)
        }


async def probe_bse(client: httpx.AsyncClient) -> Dict[str, Any]:
    url = settings.BSE_SENSEX_URL
    start = time.time()
    try:
        resp = await client.get(url, headers=DESKTOP_HEADERS, timeout=8.0)
        dur = round((time.time() - start) * 1000, 2)
        return {
            "target": "BSE API (SENSEX)",
            "url": url,
            "status_code": resp.status_code,
            "latency_ms": dur,
            "reachable": resp.status_code == 200,
            "error": None
        }
    except Exception as e:
        return {
            "target": "BSE API (SENSEX)",
            "url": url,
            "status_code": None,
            "latency_ms": round((time.time() - start) * 1000, 2),
            "reachable": False,
            "error": str(e)
        }


async def run_probes() -> Dict[str, Any]:
    print("=" * 60)
    print(" Upstream API Reachability & Diagnostic Probe")
    print("=" * 60)

    async with httpx.AsyncClient(follow_redirects=True) as client:
        results = await asyncio.gather(
            probe_world_bank(client),
            probe_imf(client),
            probe_nse(client),
            probe_bse(client)
        )

    probe_output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "probes": results
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(probe_output, f, indent=2)

    for p in results:
        status_icon = "✓" if p["reachable"] else "✗"
        print(f"[{status_icon}] {p['target']:<32} Code: {str(p['status_code']):<5} Latency: {p['latency_ms']}ms")
        if p.get("error"):
            print(f"    Notice: {p['error']}")

    print("=" * 60)
    print(f"Diagnostics recorded in: {OUTPUT_PATH}")
    return probe_output


if __name__ == "__main__":
    asyncio.run(run_probes())
