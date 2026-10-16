# Research & Architecture Decisions: Economic Indicator Dashboard (Full-Stack)

**Feature**: [001-economic-indicator-dashboard](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/001-economic-indicator-dashboard/spec.md)  
**Date**: 2026-10-16  
**Status**: Approved

This document consolidates architectural investigations, technology evaluations, and design decisions for implementing the full-stack FastAPI backend and its integration with the React dashboard.

---

## 1. Backend Web Framework & Concurrency

### Decision
Use **FastAPI (async)** running on a **single Uvicorn worker process**.

### Rationale
1. **High Concurrency for SSE**: Real-time market index quotes require maintaining open streaming connections to all active analyst browser sessions. FastAPI's native `asyncio` foundation handles thousands of concurrent SSE connections with minimal memory footprint.
2. **Lifespan Integration**: FastAPI's `@asynccontextmanager` lifespan cleanly initializes and disposes the database connection pool, the background task scheduler, the HTTP client pool, and the SSE broadcaster within a single event loop.
3. **Single-Worker Predictability**: A single Uvicorn process eliminates distributed coordination overhead:
   - In-memory broadcasting queues and ring buffers run without requiring Redis or pub/sub infrastructure.
   - `APScheduler` executes jobs without distributed locking or multi-worker race conditions.
4. **Pydantic v2 Native Speed**: High-performance Rust-backed serialization and validation ensure low latency when transforming complex time series data into standardized response envelopes.

### Alternatives Considered
- **Flask / Django**: Rejected due to synchronous blocking defaults, awkward SSE handling, and heavy ORM baggage.
- **Celery + Redis**: Rejected as overengineered; the background workload consists of lightweight periodic polling (ticker every 20s, macro daily at 06:30 IST), easily handled by an in-process `AsyncIOScheduler`.

---

## 2. Database Engine, Access & Migration Strategy

### Decision
Use **PostgreSQL 16** with **psycopg3 (`psycopg[binary,pool]`)**, an **`AsyncConnectionPool`**, raw parameterized SQL queries, and numbered `.sql` migration files.

### Rationale
1. **No ORM Overhead**: The application schema is lean (7 tables) and relies heavily on atomic upserts (`ON CONFLICT (indicator, series, period) DO UPDATE`). Raw parameterized SQL provides predictable performance, zero N+1 query surprises, and zero ORM mapping abstraction bugs.
2. **psycopg3 Native Async & Pipeline Support**: Direct `async with pool.connection()` context managers provide robust connection pooling, automatic cleanup on client aborts, and efficient parameterized type conversions.
3. **Deterministic Numbered Migrations**: Sequential SQL scripts (`migrations/001_initial_schema.sql`, `002_...`) tracked in a `schema_migrations` table run inside explicit transactions, making schema upgrades auditable and reproducible without Alembic or third-party tools.

### Alternatives Considered
- **SQLAlchemy / Tortoise ORM**: Rejected per project constraints (out of scope). ORMs add unnecessary complexity, query overhead, and migration friction.
- **SQLite**: Rejected because concurrent collector writes and read streams under asynchronous loads risk database locks; PostgreSQL 16 provides row-level MVCC locking.

---

## 3. In-Process Task Scheduling

### Decision
Use **APScheduler** (`AsyncIOScheduler`) started within the FastAPI lifespan context.

### Rationale
1. **Direct Event Loop Integration**: `AsyncIOScheduler` schedules native Python async functions directly onto the FastAPI event loop, sharing the global `httpx.AsyncClient` and `AsyncConnectionPool`.
2. **Scheduling Windows & Constraints**:
   - **Market Ticker**: Every 20 seconds during market hours (`09:15-15:30 Asia/Kolkata`, Mon–Fri) and every 10 minutes outside market hours.
   - **Macro Indicators**: Daily at `06:30 Asia/Kolkata` (post-closing / morning readiness) and on application startup if the `observations` table is empty.
   - **Seed Loader**: Startup check calculating SHA-256 checksums against `seed_files`.
   - **Ticker History Purge**: Daily cleanup retaining the last 7 days of quote snapshots.
3. **Execution Guardrails**:
   - `max_instances=1`: Guarantees a job never runs concurrently with itself.
   - `coalesce=True`: Collapses missed triggers during temporary slowdowns.
   - `misfire_grace_time=60`: Tolerates transient event loop delays.
   - Every run writes its start time, finish time, row count, status, and error log into `collector_runs`.

---

## 4. Upstream Collector Resilience & Data Governance

### Decision
Implement a standardized `BaseCollector` pattern with timeouts, exponential backoff with jitter, per-host throttling, circuit breakers, and domain plausibility guards.

### Rationale
1. **Network Resilience**:
   - Connect timeout: `3.0s`; Read timeout: `8.0s`.
   - Retries: Maximum 3 attempts with exponential backoff plus random jitter (`delay = min(5.0, 1.0 * (2 ** attempt) + random.uniform(0, 0.5))`).
   - Per-host minimum interval: `15.0s` between consecutive requests to the same host to prevent being rate-limited or IP-banned.
   - Circuit Breaker: 5 consecutive failures trip the breaker, rejecting requests to that host for `5.0 minutes`.
2. **Domain Plausibility Guards**:
   - GDP Growth: `-20.0%` to `+30.0%`
   - Inflation: `-10.0%` to `+50.0%`
   - Debt to GDP: `0.0%` to `200.0%`
   - Ticker % Change: `-20.0%` to `+20.0%`
   - Any value outside bounds, `NaN`, or `Infinity` is rejected. The database retains the last known good observation, and a failure record is logged in `collector_runs`.
3. **Upstream Adapter Strategies**:
   - **NSE Adapter**: Visits `https://www.nseindia.com` first to warm session cookies, then queries `/api/allIndices` with full desktop browser headers (`User-Agent`, `Accept-Language`, `Referer`), renewing session cookies on HTTP 401/403.
   - **BSE Adapter**: Fetches SENSEX with an automated fallback to Yahoo Finance (`^BSESN`).
   - **World Bank & IMF**: Formatted REST queries with ISO3 country codes (`IND`, `WLD`, `USA`) and indicator codes.
   - **Seed Loader**: Reads `data/seed/gst_monthly.csv` and `data/seed/government_expenditure.csv`, computing SHA-256 checksums to guarantee idempotent imports.

---

## 5. Live Streaming Architecture (Server-Sent Events)

### Decision
Implement **Server-Sent Events (SSE)** via FastAPI `StreamingResponse` using an in-process broadcaster with a 50-event ring buffer and single-use tickets.

### Rationale
1. **Unidirectional Push**: Market ticker updates flow unidirectionally from server to clients. SSE operates over standard HTTP/1.1 and HTTP/2 without WebSocket handshake complexity or stateful proxy upgrades.
2. **Single-Use 30-Second Ticket**:
   - Authenticated clients call `POST /api/auth/stream-ticket` (requiring Bearer JWT).
   - Backend issues a cryptographically random, single-use ticket stored with a 30-second TTL.
   - Client opens `GET /api/stream/ticker?ticket=<ticket>`.
   - Prevents passing persistent JWT access tokens in query parameters (which appear in server access logs and browser history).
3. **Congestion & Disconnect Management**:
   - Each connected client gets a bounded `asyncio.Queue(maxsize=100)`. If a slow client queue fills, the oldest event is dropped.
   - A global ring buffer stores the last 50 quote events, supporting `Last-Event-ID` replay when clients reconnect after transient network drops.
   - Every 15 seconds, a heartbeat comment (`: ping\n\n`) is sent to keep intermediate proxies and browser connections alive.
   - Disconnected client queues are unregistered and garbage collected.

---

## 6. Multi-Tier Caching & Freshness Strategy

### Decision
Implement a 4-tier caching architecture prioritizing database truth and fast response delivery.

### Rationale
1. **PostgreSQL as Source of Truth**: All verified observations and quote snapshots live in PostgreSQL.
2. **In-Memory TTL Cache (`cachetools`)**: Assembled response envelopes are cached in memory (5 seconds for ticker, 10 minutes for macro indicators), invalidated immediately by collector write hooks.
3. **HTTP Cache Control & ETags**:
   - `/api/dashboard` and `/api/indicators/*`: `Cache-Control: private, max-age=60` with `ETag` generation; returns HTTP 304 Not Modified when data has not changed.
   - `/api/ticker` and `/api/stream/ticker`: `Cache-Control: no-store, no-cache`.
4. **Upstream Protection**: Endpoints only query the local database or in-memory cache; clients NEVER trigger upstream external network requests directly.

---

## 7. Authentication, Security & Rate Limiting

### Decision
Use **JWT HS256** with 60-minute access tokens, **bcrypt** password hashing, and **slowapi** IP-based rate limiting.

### Rationale
1. **Access Tokens**: 60-minute access token signed with `JWT_SECRET` (minimum 32 bytes enforced at startup). No refresh token mechanism (per project constraints).
2. **Rate Limiting**: Login endpoint `POST /api/auth/login` is rate-limited to 5 requests per minute per client IP using `slowapi`, protecting against brute-force attacks.
3. **Security Headers & CORS**:
   - `CORS`: Allowed origins strictly bound to `FRONTEND_ORIGIN`.
   - Security headers: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Content-Security-Policy`.
4. **Seeded Evaluation User**: Default analyst account seeded from `EVAL_USERNAME` and `EVAL_PASSWORD_HASH` on startup if not present.
