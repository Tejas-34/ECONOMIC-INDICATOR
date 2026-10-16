# Research & Architecture Decisions: End-to-End Live Dashboard Integration

**Feature**: [002-live-data-integration](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/002-live-data-integration/spec.md)  
**Date**: 2026-10-16  
**Status**: Approved

This document consolidates architectural investigations, technology evaluations, and concrete engineering decisions for integrating the FastAPI backend and React frontend into an authenticated, resilient, end-to-end live dashboard.

---

## 1. Presenter Architecture & Contract Decoupling (`app/presenters/`)

### Decision
Extract presentation logic from `assemble_indicator` into dedicated presenter modules under `backend/app/presenters/`:
- `gdp_growth.py`
- `debt_to_gdp.py`
- `trade_balance.py`
- `gst_collection.py`
- `inflation.py`
- `govt_expenditure.py`
- `__init__.py` (registry dispatcher)

`backend/app/services/indicator_service.py` (`assemble_indicator`) will act strictly as the data access layer: querying PostgreSQL for raw observations and source records, determining freshness status, and delegating the formatting, unit conversion, delta computation, and series structuring to the corresponding presenter.

### Rationale
1. **Single Responsibility**: `assemble_indicator` was accumulating raw SQL querying, complex panel-specific unit math, delta rules (D3–D9), and formatting string concatenations in one 460-line function.
2. **Contract Fidelity (I1/I2)**: The frontend public contract is [`frontend/src/api/types.ts`](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/frontend/src/api/types.ts). Each presenter is directly responsible for outputting the exact `values` keys and `series` rows required by each panel.
3. **Unit Conversion & Estimates**: Presenters perform unit conversions (US$ to $B, Rs crore to lakh crore) and tag Government Expenditure series observations with `estimate: true` for Revised/Budget Estimates so the frontend can mark them.
4. **Isolate Testing**: Each presenter can be unit-tested in isolation against raw observation records without requiring database connections.

### Alternatives Considered
- *Keep all logic in `assemble_indicator`*: Rejected due to maintainability and regression risks when updating individual indicator formulas.
- *Push presentation logic to SQL views*: Rejected because formatted display strings, directional indicators (`positive`/`negative`/`neutral`), and delta unit annotations are business logic that belongs in Python service layers, not SQL views.

---

## 2. Schema Single Source of Truth & Drift Prevention (`openapi-typescript`)

### Decision
Define explicit Pydantic response models for every endpoint response. Export the OpenAPI JSON specification via a backend CLI/script, and add an npm script `npm run gen:api` in `frontend/package.json` utilizing `openapi-typescript` to generate `frontend/src/api/schema.d.ts`. CI will run `npm run gen:api && git diff --exit-code frontend/src/api/schema.d.ts` to fail on uncommitted schema drift.

### Rationale
1. **Zero Drift**: Manually maintained TypeScript types inevitably drift from backend Pydantic models. Generating types directly from FastAPI's OpenAPI schema guarantees compile-time synchronization.
2. **Developer Ergonomics**: Backend engineers update Pydantic models; frontend engineers run `npm run gen:api` to reflect new fields or validation constraints immediately.
3. **Automated CI Enforcement**: Any schema change on the backend without corresponding frontend type generation fails the pull request immediately.

### Alternatives Considered
- *Maintain manual TypeScript types*: Rejected; already led to subtle field mismatches (such as `values` dictionary vs `tiles` list).
- *JSON Schema Validator runtime libraries in browser*: Rejected due to client bundle bloat and runtime overhead compared to compile-time TypeScript checks.

---

## 3. Authentication, Token Lifecycle & Route Protection

### Decision
1. **Mandatory Bearer Authentication**: Enforce `Depends(get_current_user)` on all `/api/*` endpoints except `POST /api/auth/login` and `GET /health`.
2. **Single-Use Stream Tickets**: For the live SSE stream, require a single-use ticket acquired via authenticated `POST /api/auth/stream-ticket` and validated at `GET /api/stream/ticker?ticket=...`. Ticket is consumed immediately upon validation and expires in 30 seconds.
3. **Global 401 Interception**: The frontend API client wrapper intercepts any HTTP 401 response, purges the in-memory access token, halts active timers/pollers, and redirects to `/login?session_expired=true`.
4. **60-Minute Token Lifespan & Timer Logout**: Tokens are valid for 60 minutes with no refresh tokens or fake refresh loops. The frontend starts a 60-minute countdown timer upon login that triggers an automatic logout with the session expired notification.
5. **Role Alignment**: Roles are strictly `viewer` | `admin` across Pydantic schemas, database enums, and TypeScript types.
6. **Runtime Seeding & Insecure Dev Button**: `seed_user.py` hashes `EVAL_PASSWORD` from the environment at runtime using bcrypt. No hardcoded password hashes or bypass credentials exist in source code. The login quick-fill button is guarded by `import.meta.env.DEV`.

### Rationale
1. **Security-by-Default**: Open endpoints leak financial statistics and market trends. Enforcing token checks on indicators, dashboard, ticker, and stream prevents unauthorized scraping.
2. **Clean Session Expiry**: Silent refresh loops without backend refresh token infrastructure are insecure. Explicit expiration with immediate redirection protects analyst consoles.
3. **Credential Hygiene**: Storing evaluation hashes in repository code violates enterprise security standards.

---

## 4. HTTP Caching, ETag & 304 Header Preservation

### Decision
Fix the FastAPI ETag / 304 handling in `indicators.py` and `indicator_service.py`. When an incoming `If-None-Match` matches the computed ETag:
```python
if if_none_match and if_none_match == etag:
    return Response(
        status_code=status.HTTP_304_NOT_MODIFIED,
        headers={
            "ETag": etag,
            "Cache-Control": "private, max-age=60"
        }
    )
```

### Rationale
Previous code returned `Response(status_code=304)` without attaching the `ETag` and `Cache-Control` headers, which were set on the FastAPI route parameter `response` instead of the returned object. As a result, 304 responses lost their cache headers, causing clients to invalidate their local caches or re-request data unnecessarily.

---

## 5. Live Ticker Protocol: Unified Cadence, Dynamic Status & Snapshot Events

### Decision
1. **Dynamic-Cadence Scheduler**: Replace the two overlapping APScheduler ticker jobs with a single job `ticker_ingestion`. In the job or trigger, check Kolkata market hours (09:15–15:30 IST, Mon–Fri). In market hours, schedule next run in 20 seconds; off-hours, schedule next run in 10 minutes.
2. **Startup Ingestion & Macro Bootstrap**: On backend startup, schedule immediate execution via `next_run_time=datetime.now(timezone.utc)` for the ticker job and for macro collection if the `observations` table has zero records.
3. **Read-Time Status Evaluation**: Do not persist stale status flags in the database. Compute `market_status` at read time:
   - `open` and updated within 2x interval = `LIVE`
   - outside trading hours or holiday = `CLOSED`
   - no update for >2x interval or SSE stream down >60s = `STALE`
4. **Named "snapshot" SSE Event**: The server broadcasts all three market quotes (NIFTY BANK, NIFTY IT, SENSEX) under a single named event `event: snapshot` with monotonic ID, retry hint (e.g. `retry: 3000`), and a 15-second heartbeat `: ping\n\n`.
5. **Client Protocol & Resilient Reconnection**:
   - On mount: fetch `GET /api/ticker` initial snapshot.
   - Request fresh ticket via `POST /api/auth/stream-ticket`.
   - Connect directly to API origin `EventSource /api/stream/ticker?ticket=...`.
   - On disconnect: exponential backoff (1s to 30s with jitter); request a fresh ticket per reconnection attempt.
   - After 3 consecutive failures: start concurrent 10s polling to `GET /api/ticker` while SSE continues reconnection retries in the background.

---

## 6. Secrets Hardening, Startup Guard & Reverse Proxy Client IP

### Decision
1. **Startup Guard (I9)**: In `backend/app/main.py`, during lifespan startup when `DATA_MODE=live`:
   - Inspect `JWT_SECRET`, database connection URL, and `EVAL_PASSWORD`.
   - If any secret contains default example values (e.g., `c2VjdX...`, `Analyst@2026`, `postgres_secure_password_2026`) and `ALLOW_INSECURE_DEFAULTS` is not `true`, abort startup immediately with an actionable error message.
2. **Real Client IP Keying Behind Reverse Proxy**:
   - SlowAPI rate limiting must not use `request.client.host` because behind Caddy or Docker bridge, every request appears to originate from the proxy container.
   - Implement `get_real_client_ip(request: Request) -> str` that checks `request.headers.get("X-Forwarded-For")` (taking the leftmost untrusted IP) or `request.headers.get("X-Real-IP")`, falling back to `request.client.host`.
3. **Caddy Non-Buffering for SSE**:
   - In `backend/Caddyfile`, configure `handle /api/stream/*` with `flush_interval -1` so Caddy never buffers SSE events.

---

## 7. Frontend Architecture: Universal Client Wrapper & State Management

### Decision
1. **Unified Request Wrapper (`frontend/src/api/client.ts`)**:
   - Implement `async function request<T>(path: string, options: RequestOptions): Promise<T>`:
     - Base URL normalization: strip trailing slashes, ensure `/api` is prefixed consistently.
     - Automatically attaches `Authorization: Bearer <token>` from memory.
     - Enforces 10-second timeout via `AbortController`.
     - Executes up to 2 retries with exponential backoff on network failures or 5xx server errors.
     - Checks HTTP 401: invokes global logout handler and redirect to `/login?session_expired=true`.
     - Supports `ETag` tracking and returns cached response on 304.
2. **Dynamic Mock Loading**:
   - In live mode (`VITE_USE_MOCKS !== 'true'`), mock JSON files are never statically imported.
   - In mock mode (`VITE_USE_MOCKS === 'true'`), use dynamic `import('../mocks/...')` so Vite tree-shakes mock JSON files out of production builds.
   - A visible "MOCK DATA" ribbon renders in the top-right corner when mock mode is enabled.
3. **Dashboard Store & 5-Minute Refresh**:
   - First paint triggers `GET /api/dashboard` (ETag/304), distributing envelopes to the store.
   - Individual panels refresh every 5 minutes. On failure, retain last valid data and label as stale (stale-while-revalidate).
   - In `SourceFooter.tsx`, render authoritative source, `Non-NSE` badge, as-of period, and an estimate indicator for series containing estimates.

---

## 8. Docker Compose & Deployment Architecture

### Decision
1. **Secrets via `env_file`**: Update `docker-compose.yml` to load variables from `.env` using `env_file: [.env]`. Remove inline passwords and secret tokens.
2. **PostgreSQL Network Isolation**: Ensure PostgreSQL has no `ports` mapped to the host, remaining accessible solely to the backend container over the Docker internal bridge network.
3. **Production Caddy Reverse Proxy**: Serves compiled frontend static files from `/srv/frontend/dist`, proxies `/api/*` to `backend:8000`, and streams `/api/stream/*` without buffering.
