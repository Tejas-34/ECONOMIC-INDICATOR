# Implementation Plan: Economic Indicator Dashboard (Full-Stack Backend & Integration)

**Branch**: `001-economic-indicator-dashboard` | **Date**: 2026-10-16 | **Spec**: [specs/001-economic-indicator-dashboard/spec.md](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/001-economic-indicator-dashboard/spec.md)

**Input**: Feature specification from [specs/001-economic-indicator-dashboard/spec.md](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/001-economic-indicator-dashboard/spec.md) and technical requirements defined in the prompt.

---

## Summary

Deliver a production-grade, highly resilient backend API and integration layer for the Economic Indicator dashboard. The backend is built using **FastAPI (async)**, **PostgreSQL 16** via **psycopg3 connection pooling** (raw parameterized SQL only), an in-process **APScheduler (AsyncIOScheduler)** started in the FastAPI lifespan, and live **Server-Sent Events (SSE)** for real-time market index quotes.

The backend operates under dual runtime modes (`DATA_MODE=mock|live`). In `mock` mode, it deterministically serves static JSON fixtures (`fixtures/*.json`) identical in shape to the React frontend mocks with zero database writes or upstream network calls. In `live` mode, it coordinates upstream collector adapters (NSE session warming, BSE, World Bank, IMF, data.gov.in, Union Budget seed CSVs), enforcing strict network resilience rules (connect/read timeouts, exponential backoff with jitter, circuit breakers, per-host throttling, and domain plausibility boundaries).

---

## Technical Context

**Backend Runtime & Framework**: Python 3.11+, FastAPI (async), Uvicorn (single-worker process)  
**Database**: PostgreSQL 16  
**Database Driver & Pooling**: `psycopg[binary,pool]` (psycopg3) using `AsyncConnectionPool`, raw parameterized SQL (strictly no ORM)  
**Task Scheduling**: `APScheduler` (`AsyncIOScheduler`) managed within the FastAPI lifespan context  
**HTTP Client**: `httpx` (`AsyncClient`) with connection pooling and custom retry/circuit breaker transports  
**Validation & Settings**: `pydantic` v2, `pydantic-settings`  
**Security & Authentication**: `PyJWT` (JWT HS256, 60-min access tokens, no refresh tokens), `passlib[bcrypt]` for password hashing, `slowapi` for IP-based rate limiting (5 req/min on login)  
**Live Streaming**: FastAPI SSE (`StreamingResponse` / `asyncio.Queue` broadcaster with 50-event ring buffer and monotonic IDs)  
**In-Memory Cache**: `cachetools` (TTLCache: 5s ticker, 10 min macro indicators), HTTP ETags, and `Cache-Control` headers  
**Testing Framework**: `pytest`, `pytest-asyncio`, `respx` (for mocking HTTP upstreams)  
**Deployment**: Docker, Docker Compose (internal non-exposed Postgres network), Caddy reverse proxy  
**Frontend Integration**: React 18, Redux Toolkit, Vite, running in `frontend/` communicating with backend via `VITE_API_BASE_URL`

---

## Constitution Check

| Principle / Gate | Status | Evaluation |
| :--- | :---: | :--- |
| **I. Self-Contained Components** | PASSED | Each collector adapter (`app/collectors/`), route module (`app/routes/`), and service (`app/services/`) is modular and decoupled via clean Pydantic interfaces. |
| **II. Clean Data Abstraction** | PASSED | Standardized response envelope `{indicator, tiles, series, source, as_of, fetched_at, status}` completely insulates frontend consumers from upstream variations. |
| **III. Test-First Quality** | PASSED | Comprehensive test suite covering authentication, rate limiting, SQL injection resilience, plausibility enforcement, stale labeling, market hours, and SSE token replay. |
| **IV. Observability & Provenance** | PASSED | Every collector run writes execution metadata, duration, row counts, and errors to `collector_runs`; panels display exact data sources, URLs, and timestamps. |
| **V. Simplicity & Minimal Footprint** | PASSED | Raw parameterized SQL with psycopg3 pool replaces heavy ORMs; single Uvicorn process hosts scheduler and SSE broadcaster without requiring Redis or Celery. |

---

## Project Structure

```text
Economics-Indicator/
├── backend/
│   ├── app/
│   │   ├── collectors/          # Upstream source adapters (NSE, BSE, World Bank, IMF, Seed)
│   │   │   ├── base.py          # BaseCollector with retry, jitter, circuit breaker, rate limit
│   │   │   ├── nse.py           # NSE allIndices adapter with session warming
│   │   │   ├── bse.py           # BSE SENSEX adapter with Yahoo Finance fallback
│   │   │   ├── world_bank.py    # GDP, Trade, Inflation World Bank API collector
│   │   │   ├── imf.py           # Debt to GDP DataMapper collector
│   │   │   └── seed_loader.py   # Idempotent CSV loader with SHA-256 checksums
│   │   ├── routes/              # FastAPI APIRouters
│   │   │   ├── auth.py          # /api/auth/login, /api/auth/me, /api/auth/stream-ticket
│   │   │   ├── indicators.py    # /api/indicators/{id}, /api/dashboard
│   │   │   ├── ticker.py        # /api/ticker, /api/stream/ticker (SSE)
│   │   │   ├── admin.py         # /api/admin/refresh/{job}
│   │   │   └── health.py        # /health (db, scheduler, collector status)
│   │   ├── schemas/             # Pydantic v2 models
│   │   │   ├── envelope.py      # Standard indicator response envelope & tiles
│   │   │   ├── ticker.py        # Ticker quote and stream models
│   │   │   ├── auth.py          # Credentials, JWT tokens, session payloads
│   │   │   └── collectors.py    # Internal validated upstream observation schemas
│   │   ├── security/            # Auth & protection
│   │   │   ├── jwt.py           # Token creation, verification, single-use SSE tickets
│   │   │   ├── passwords.py     # bcrypt password hashing & verification
│   │   │   └── rate_limit.py    # slowapi Limiter definitions
│   │   ├── services/            # Business logic
│   │   │   ├── indicator_service.py # Tile delta calculations (D3), envelope assembly
│   │   │   └── ticker_service.py    # Quote snapshots, market status resolution
│   │   ├── cache.py             # In-memory TTLCache with collector invalidation
│   │   ├── config.py            # pydantic-settings Settings model
│   │   ├── db.py                # psycopg3 connection pool management
│   │   ├── main.py              # FastAPI application & lifespan management
│   │   ├── market_hours.py      # Indian exchange hours (09:15-15:30 Asia/Kolkata) & holidays
│   │   ├── scheduler.py         # APScheduler AsyncIOScheduler job setups
│   │   └── sse.py               # Broadcaster with bounded queues & ring buffer
│   ├── data/
│   │   └── seed/                # Raw curated CSV source files
│   │       ├── government_expenditure.csv
│   │       └── gst_monthly.csv
│   ├── fixtures/                # Static mock JSON payloads (identical to frontend mocks)
│   │   ├── gdpGrowth.json
│   │   ├── debtToGdp.json
│   │   ├── tradeBalance.json
│   │   ├── gstCollection.json
│   │   ├── inflation.json
│   │   ├── govtExpenditure.json
│   │   └── tickerFeed.json
│   ├── migrations/              # Numbered raw SQL migrations
│   │   ├── 001_initial_schema.sql
│   │   ├── 002_create_observations.sql
│   │   └── 003_create_ticker_tables.sql
│   ├── scripts/                 # Standalone maintenance utilities
│   │   ├── migrate.py           # Numbered SQL migration runner
│   │   ├── seed_user.py         # Initial analyst user seeder
│   │   ├── load_seeds.py        # Standalone CSV seed loader
│   │   └── probe_sources.py     # Upstream API reachability & diagnostic probe
│   ├── tests/                   # Pytest test suite
│   │   ├── conftest.py          # Test database fixtures, respx mocks, test client
│   │   ├── test_auth.py         # Login, rate limiting, token expiration, tickets
│   │   ├── test_indicators.py   # Envelope structure, D3 tile delta rules, stale handling
│   │   ├── test_collectors.py   # Upstream parsing, circuit breaker, plausibility bounds
│   │   ├── test_market_hours.py # Zoneinfo market hours, holiday detection
│   │   └── test_sse.py          # SSE connection, heartbeat, ticket reuse, ring buffer replay
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── pyproject.toml
│   ├── requirements.txt
│   └── README.md
├── frontend/                    # React 18 + Redux Toolkit dashboard SPA
├── design/                      # Visual reference assets & mockups
├── specs/                       # Feature specifications, plans, and contracts
└── README.md                    # Root workspace documentation
```

---

## Database Architecture & Migrations

All database interactions use **psycopg3** with `AsyncConnectionPool`. Migrations are managed by `scripts/migrate.py` applying ordered SQL files inside transactions.

### Core Tables

1. **`users`**:
   - `id SERIAL PRIMARY KEY`
   - `username VARCHAR(64) UNIQUE NOT NULL`
   - `password_hash VARCHAR(255) NOT NULL`
   - `role VARCHAR(32) NOT NULL DEFAULT 'viewer'` (values: `viewer`, `admin`)
   - `created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`

2. **`sources`**:
   - `id VARCHAR(64) PRIMARY KEY` (e.g. `worldbank`, `imf`, `nse`, `bse`, `seed-budget`, `seed-gst`)
   - `name VARCHAR(255) NOT NULL`
   - `type VARCHAR(32) NOT NULL` (`nse`, `external`, `external-curated`)
   - `url TEXT NOT NULL`
   - `notes TEXT`

3. **`observations`**:
   - `id BIGSERIAL PRIMARY KEY`
   - `indicator VARCHAR(64) NOT NULL` (`gdp-growth`, `debt-to-gdp`, `trade-balance`, `gst-collection`, `inflation`, `govt-expenditure`)
   - `series VARCHAR(64) NOT NULL` (`india`, `world`, `exports`, `imports`, `capex`, etc.)
   - `period VARCHAR(32) NOT NULL` (`2021`, `FY2024-25`, etc.)
   - `value NUMERIC(18, 4)` (can be `NULL`)
   - `unit VARCHAR(32)` (`%`, `US$ B`, `Rs lakh crore`)
   - `basis VARCHAR(32)` (`actual`, `revised_estimate`, `budget_estimate`, or `NULL`)
   - `source_id VARCHAR(64) REFERENCES sources(id)`
   - `as_of DATE NOT NULL`
   - `fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`
   - **Constraint**: `UNIQUE(indicator, series, period)`

4. **`ticker_latest`**:
   - `symbol VARCHAR(32) PRIMARY KEY` (`SENSEX`, `NIFTY BANK`, `NIFTY IT`)
   - `name VARCHAR(64) NOT NULL`
   - `last NUMERIC(12, 2) NOT NULL`
   - `change NUMERIC(10, 2) NOT NULL`
   - `pct_change NUMERIC(6, 2) NOT NULL`
   - `market_status VARCHAR(16) NOT NULL` (`open`, `closed`, `stale`)
   - `source_id VARCHAR(64) REFERENCES sources(id)`
   - `as_of TIMESTAMPTZ NOT NULL`
   - `fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`

5. **`ticker_history`**:
   - `id BIGSERIAL PRIMARY KEY`
   - `symbol VARCHAR(32) NOT NULL`
   - `last NUMERIC(12, 2) NOT NULL`
   - `pct_change NUMERIC(6, 2) NOT NULL`
   - `as_of TIMESTAMPTZ NOT NULL`
   - *Purged by daily cleanup job retaining 7 days of records.*

6. **`collector_runs`**:
   - `id BIGSERIAL PRIMARY KEY`
   - `job VARCHAR(64) NOT NULL`
   - `started_at TIMESTAMPTZ NOT NULL`
   - `finished_at TIMESTAMPTZ`
   - `status VARCHAR(32) NOT NULL` (`success`, `failed`, `skipped_rate_limit`, `circuit_open`)
   - `rows INTEGER DEFAULT 0`
   - `error TEXT`

7. **`seed_files`**:
   - `path VARCHAR(255) PRIMARY KEY`
   - `checksum VARCHAR(64) NOT NULL` (SHA-256)
   - `loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()`

### Upsert Protocol
All write operations utilize PostgreSQL `ON CONFLICT (...) DO UPDATE` and ONLY update with non-null, validated records. If an upstream batch has invalid numbers, existing rows are untouched.

---

## Collector Resilience & Upstream Protections

Every collector inherits from `BaseCollector`:
- **Timeouts**: `connect=3.0s`, `read=8.0s`.
- **Retries**: Maximum 3 retries using exponential backoff with random jitter (`initial=1.0s`, `max=5.0s`).
- **Throttling**: Minimum interval of 15 seconds per external host.
- **Circuit Breaker**: Trips on 5 consecutive failures, halting external requests for 5 minutes.
- **Single-Flight Lock**: An `asyncio.Lock` per job prevents concurrent runs of the same collector.
- **Plausibility Guards**:
  - GDP Growth: `-20.0%` to `+30.0%`
  - Inflation Rate: `-10.0%` to `+50.0%`
  - Debt to GDP: `0.0%` to `200.0%`
  - Ticker % Change: `-20.0%` to `+20.0%`
  - Zero `NaN` or `Infinity` accepted; invalid records trigger error logging, keep previous database row, and increment failure metrics.
- **NSE Session Warming**: Connects to `https://www.nseindia.com` to capture cookies before invoking `allIndices` with full desktop browser headers (`User-Agent`, `Accept-Language`, `Referer`), renewing session cookies on 401/403.
- **BSE Adapter**: Scrapes/fetches SENSEX quotes with fallback to Yahoo Finance (`^BSESN`).

---

## Scheduling & Lifespan Architecture

`AsyncIOScheduler` runs directly inside the FastAPI lifespan context:
1. **Ticker Job**:
   - Scheduled every 20 seconds during market hours (`09:15 - 15:30 Asia/Kolkata`, Mon-Fri).
   - Scheduled every 10 minutes outside market hours.
2. **Macro Job**:
   - Scheduled daily at `06:30 Asia/Kolkata`.
   - Also executed at application startup if `observations` table is empty.
3. **Seed Ingestion Job**:
   - Executed at startup; compares SHA-256 checksum against `seed_files` table, loading only on change.
4. **Ticker History Purge**:
   - Daily job deleting records older than 7 days.
5. **Scheduler Constraints**:
   - `max_instances=1`, `coalesce=True`, `misfire_grace_time=60`.

---

## Caching & Live SSE Broadcasting

1. **Database as Truth**: PostgreSQL stores all valid observations.
2. **In-Memory TTL Cache**: `cachetools.TTLCache` (5-second TTL for ticker, 10-minute TTL for macro indicators). Invalidated immediately when a collector finishes an upsert.
3. **HTTP Cache**: Endpoints return `ETag` and `Cache-Control: private, max-age=60` for indicator and dashboard endpoints; `Cache-Control: no-store` for ticker.
4. **SSE Broadcasting (`/api/stream/ticker`)**:
   - Client requests single-use ticket via `POST /api/auth/stream-ticket`.
   - Connects to `/api/stream/ticker?ticket=...` with 30-second ticket expiration.
   - Broadcaster tracks active client queues (`asyncio.Queue(maxsize=100)`, dropping oldest on congestion).
   - Keeps 50-event in-memory ring buffer for `Last-Event-ID` reconnection replay.
   - Sends SSE heartbeat comments (`: ping\n\n`) every 15 seconds.
   - Cleans up client queues on disconnect.

---

## Testing & Quality Gates

1. **Unit & Integration (`pytest`, `pytest-asyncio`, `respx`)**:
   - Auth tests: valid credentials, expired JWT, invalid signature, role authorization, 5/min IP rate limiting.
   - SQL injection resilience tests across query parameters and filters.
   - Upstream parser tests with `respx` verifying timeout, retry, backoff, and circuit breaker behavior.
   - Plausibility guard tests asserting that out-of-bounds data preserves existing database records.
   - Staleness tests verifying that data older than 2x refresh interval returns `status="stale"`.
   - Market hours evaluation (weekdays, off-hours, holiday timestamp staleness).
   - SSE connection tests (ticket reuse rejection, event delivery, 15s heartbeat, ring buffer replay).
   - Parity test verifying that `DATA_MODE=mock` response payloads match `frontend/src/mocks/*.json`.
2. **Visual & End-to-End (`playwright`)**:
   - Full-page regression tests validating dashboard at 1214 x 2159 CSS pixels against real backend responses.
