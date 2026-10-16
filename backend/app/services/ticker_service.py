import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from backend.app.cache import get_cached_ticker, set_cached_ticker
from backend.app.collectors.bse import BSECollector
from backend.app.collectors.nse import NSECollector
from backend.app.config import settings
from backend.app.market_hours import evaluate_market_status, compute_read_time_market_status
from backend.app.schemas.ticker import MarketIndexQuote, TickerSnapshotPayload

_ticker_job_lock = asyncio.Lock()
_nse_collector = NSECollector()
_bse_collector = BSECollector()


async def run_ticker_ingestion_job() -> Dict[str, Any]:
    """Execute live quote collection across NSE and BSE adapters and broadcast snapshot to SSE subscribers."""
    if _ticker_job_lock.locked():
        return {"status": "skipped_already_running"}

    async with _ticker_job_lock:
        if settings.DATA_MODE == "mock":
            return {"status": "skipped_mock_mode", "quotes": 0}

        from backend.app.db import execute_many, execute_write
        from backend.app.sse import broadcast_quote, broadcast_snapshot

        started_at = datetime.now(timezone.utc)
        quotes: List[Dict[str, Any]] = []

        try:
            # 1. Fetch NSE quotes (NIFTY BANK, NIFTY IT)
            nse_quotes = await _nse_collector.collect_indices()
            quotes.extend(nse_quotes)

            # 2. Fetch BSE quote (SENSEX)
            sensex = await _bse_collector.collect_sensex()
            if sensex:
                quotes.append(sensex)

            # 3. Persist and broadcast
            if quotes:
                latest_upserts = []
                history_inserts = []
                quote_models: List[MarketIndexQuote] = []

                for q in quotes:
                    m_status = compute_read_time_market_status(q["as_of"])
                    q["market_status"] = m_status

                    latest_upserts.append((
                        q["symbol"], q["name"], q["last"], q["change"], q["pct_change"],
                        m_status, q["source_id"], q["as_of"]
                    ))
                    history_inserts.append((
                        q["symbol"], q["last"], q["pct_change"], q["as_of"]
                    ))

                    # Model validation
                    quote_model = MarketIndexQuote.model_validate(q)
                    quote_models.append(quote_model)
                    await broadcast_quote(quote_model)

                # Broadcast consolidated snapshot with all quotes (I4)
                snapshot_payload = TickerSnapshotPayload(
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    quotes=quote_models
                )
                await broadcast_snapshot(snapshot_payload)

                # Batch upsert ticker_latest
                await execute_many("""
                    INSERT INTO ticker_latest (symbol, name, last, change, pct_change, market_status, source_id, as_of)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (symbol) DO UPDATE SET
                        last = EXCLUDED.last,
                        change = EXCLUDED.change,
                        pct_change = EXCLUDED.pct_change,
                        market_status = EXCLUDED.market_status,
                        source_id = EXCLUDED.source_id,
                        as_of = EXCLUDED.as_of,
                        fetched_at = NOW();
                """, latest_upserts)

                # Batch insert ticker_history
                await execute_many("""
                    INSERT INTO ticker_history (symbol, last, pct_change, as_of)
                    VALUES (%s, %s, %s, %s);
                """, history_inserts)

                # Invalidate cache
                set_cached_ticker("ticker_snapshot", None)

            status_str = "success"
            err = None
        except Exception as e:
            status_str = "failed"
            err = str(e)
            print(f"[TickerService] Ingestion failed: {e}")

        finished_at = datetime.now(timezone.utc)
        await execute_write("""
            INSERT INTO collector_runs (job, started_at, finished_at, status, rows, error)
            VALUES ('ticker_job', %s, %s, %s, %s, %s);
        """, (started_at, finished_at, status_str, len(quotes), err))

        return {
            "status": status_str,
            "quotes_count": len(quotes),
            "error": err
        }


async def get_latest_quotes_snapshot() -> TickerSnapshotPayload:
    """Fetch latest quotes from database with read-time market status computation (I5)."""
    cached = get_cached_ticker("ticker_snapshot")
    if cached:
        for q in cached.quotes:
            as_of_dt = datetime.fromisoformat(q.as_of) if isinstance(q.as_of, str) else q.as_of
            q.market_status = compute_read_time_market_status(as_of_dt)
        return cached

    from backend.app.db import fetch_all
    rows = await fetch_all("""
        SELECT symbol, name, last, change, pct_change, market_status, source_id, as_of, fetched_at
        FROM ticker_latest
        ORDER BY symbol ASC;
    """)

    if not rows:
        now_iso = datetime.now(timezone.utc).isoformat()
        return TickerSnapshotPayload(timestamp=now_iso, quotes=[])

    quote_models = []
    for r in rows:
        m_status = compute_read_time_market_status(r["as_of"])
        q_dict = {
            "symbol": r["symbol"],
            "name": r["name"],
            "last": float(r["last"]),
            "change": float(r["change"]),
            "pct_change": float(r["pct_change"]),
            "as_of": r["as_of"].isoformat(),
            "source": "NSE" if r["source_id"] == "nse" else "BSE",
            "market_status": m_status
        }
        quote_models.append(MarketIndexQuote.model_validate(q_dict))

    snapshot = TickerSnapshotPayload(
        timestamp=datetime.now(timezone.utc).isoformat(),
        quotes=quote_models
    )
    set_cached_ticker("ticker_snapshot", snapshot)
    return snapshot
