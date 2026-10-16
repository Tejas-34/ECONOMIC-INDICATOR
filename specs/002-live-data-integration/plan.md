# Implementation Plan: End-to-End Live Dashboard Integration

**Branch**: `002-live-data-integration` | **Date**: 2026-10-16 | **Spec**: [spec.md](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/002-live-data-integration/spec.md)

**Input**: Feature specification from `/specs/002-live-data-integration/spec.md` and user directives.

## Summary

Integrate the existing React frontend and FastAPI backend into a production-grade, secure, resilient dashboard operating end-to-end on live data (`DATA_MODE=live`, `VITE_USE_MOCKS=false`) while maintaining complete functional parity in mock mode for offline testing and demos.

### Key Technical Pillars
1. **Presenter Architecture (`app/presenters/`)**: Decouple data access from presentation formatting by creating per-indicator presenters that transform database observations into the public `IndicatorResponse` contract ([`frontend/src/api/types.ts`](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/frontend/src/api/types.ts)).
2. **Schema Synchronization (`openapi-typescript`)**: Establish Pydantic response models as the single source of truth; export OpenAPI schema; generate `frontend/src/api/schema.d.ts` via `npm run gen:api`; enforce CI failure on schema drift.
3. **Authentication & Session Lifecycle**: Enforce Bearer token verification (`get_current_user`) across all `/api/*` routes except login and health; require single-use tickets for SSE; global 401 redirection to `/login?session_expired=true`; client 60-minute token timer logout; eliminate hardcoded password bypasses and runtime-hash `EVAL_PASSWORD` from environment.
4. **Resilient Ticker Streaming**: Single dynamic-cadence scheduler job (20s market hours, 10m off-hours); initial snapshot via `GET /api/ticker`; mandatory single-use ticket; named `"snapshot"` SSE event; 1s–30s exponential backoff with jitter; concurrent 10-second polling fallback after 3 consecutive push failures; read-time `market_status` driving dynamic `LIVE`/`CLOSED`/`STALE` badges.
5. **Stability & HTTP Caching**: Initial paint via `GET /api/dashboard` with valid ETag/304 header preservation; 5-minute panel refresh with stale-while-revalidate; 10-second `AbortController` request timeout; 2 retries with backoff; isolated panel error recovery.
6. **Hardened Configuration & Deployment**: Backend startup guard rejecting default secrets in live mode unless `ALLOW_INSECURE_DEFAULTS=true`; rate limiting keyed to real client IP behind proxy (`X-Forwarded-For`); Docker Compose `env_file` with unpublished PostgreSQL port; Caddy configured with `flush_interval -1` for non-buffering SSE.

---

## Technical Context

**Language/Version**: Python 3.11 (backend), TypeScript 5.5 + Node 20 (frontend)  
**Primary Dependencies**:
- Backend: FastAPI 0.115, Pydantic v2, APScheduler 3.10, SlowAPI 0.1.9, psycopg3 (`psycopg[binary,pool]`), PyJWT / cryptography, passlib / bcrypt
- Frontend: React 18.3, Redux Toolkit 2.13, ECharts 5.5, `echarts-for-react`, React Router 6.26, `openapi-typescript`
- Proxy: Caddy 2 (or Vite proxy in local development)  
**Storage**: PostgreSQL 16 (raw parameterized SQL via psycopg3 async connection pool), seed CSVs (`data/seed/`)  
**Testing**: pytest + pytest-asyncio + httpx (backend), Vitest + React Testing Library (frontend), Playwright (end-to-end integration & visual regression)  
**Target Platform**: Linux Docker container / Docker Compose, modern evergreen workstation browsers  
**Project Type**: Web application (FastAPI backend + React SPA frontend)  
**Performance Goals**:
- Initial authenticated dashboard load under 3.0s
- Ticker quote updates rendered within 2.0s of ingestion
- SSE stream reconnection and catch-up within 5.0s of network restoration
- 10s request timeout with 2 retries on network failures  
**Constraints**:
- Reference evaluation resolution: 1214 × 2159 CSS pixels with 0% layout shift, zero horizontal scrolling, and zero card clipping
- Zero visual redesign or alterations to established typography and color schemes
- Zero mock JSON fixtures bundled into production frontend builds  
**Scale/Scope**:
- 6 indicator panels: `gdp-growth`, `debt-to-gdp`, `trade-balance`, `gst-collection`, `inflation`, `govt-expenditure`
- 3 market indices: NIFTY BANK, NIFTY IT, SENSEX
- 2 user roles: `viewer`, `admin`
- Dual runtime modes: `DATA_MODE=live|mock`, `VITE_USE_MOCKS=false|true`

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / Rule | Compliance Status | Justification / Notes |
| :--- | :---: | :--- |
| **Separation of Concerns** | PASSED | Presenters isolate business formatting from data access in `indicator_service.py`. |
| **Contract Fidelity** | PASSED | Frontend `IndicatorResponse` is the public contract. Generated TypeScript types prevent schema drift. |
| **Security by Default** | PASSED | Mandatory Bearer auth on all data routes; single-use stream tickets; startup guard on secrets; unpublished DB port. |
| **Zero Visual Redesign** | PASSED | Reference layout, CSS Grid, cards, colors, and 1214 × 2159 viewport stability preserved. |
| **Offline Testability** | PASSED | Standalone mock mode preserved with zero external dependencies for automated tests and demos. |

---

## Project Structure

### Documentation (this feature)

```text
specs/002-live-data-integration/
├── plan.md              # Implementation architecture and module breakdown
├── research.md          # Architecture decisions and technical rationale (Phase 0)
├── data-model.md        # Entity definitions, schemas, and lifecycle diagrams (Phase 1)
├── quickstart.md        # End-to-end runnable validation scenarios (Phase 1)
├── contracts/           # Machine-readable JSON schema contracts (Phase 1)
│   ├── auth-api.json
│   ├── indicator-api.json
│   ├── ticker-stream.json
│   └── dashboard-api.json
└── checklists/
    └── requirements.md  # Specification quality checklist
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── presenters/                     # NEW: Dedicated indicator presentation modules
│   │   ├── __init__.py                 # Presenter registry dispatcher
│   │   ├── gdp_growth.py               # GDP Growth presenter (india/world, rate deltas)
│   │   ├── debt_to_gdp.py              # Debt to GDP presenter (indiaFy25/indVsUs)
│   │   ├── trade_balance.py            # Trade Balance presenter (exports/imports, US$ B)
│   │   ├── gst_collection.py           # GST Collection presenter (YoY %, Rs lakh crore)
│   │   ├── inflation.py                # Inflation presenter (CPI vs 4.0 RBI policy target)
│   │   └── govt_expenditure.py         # Govt Expenditure presenter (estimate flags)
│   ├── routes/
│   │   ├── auth.py                     # Stream ticket & login routes
│   │   ├── indicators.py               # Protected indicator & dashboard endpoints, ETag fix
│   │   ├── ticker.py                   # Protected snapshot & SSE stream endpoints
│   │   └── health.py                   # Health endpoint reporting job ages
│   ├── schemas/
│   │   ├── auth.py                     # AuthUser, LoginResponse (roles: viewer|admin)
│   │   ├── envelope.py                 # IndicatorResponse, StatTileMetric Pydantic models
│   │   └── ticker.py                   # TickerSnapshotPayload, MarketIndexQuote models
│   ├── security/
│   │   ├── dependencies.py             # get_current_user Bearer dependency
│   │   ├── jwt.py                      # Token encoding, ticket generation/consumption
│   │   └── rate_limit.py               # IP extraction from X-Forwarded-For
│   ├── services/
│   │   ├── indicator_service.py        # Data access only; delegates to presenters
│   │   └── ticker_service.py           # Single-job ticker ingestion & snapshot generation
│   ├── config.py                       # Startup guard, env loading without committed defaults
│   ├── main.py                         # Startup guard validation in lifespan
│   ├── scheduler.py                    # Unified dynamic-cadence ticker job & startup bootstrap
│   └── sse.py                          # Named "snapshot" event, replay, client heartbeat
├── scripts/
│   ├── seed_user.py                    # Runtime bcrypt hashing of EVAL_PASSWORD
│   └── export_openapi.py               # NEW: CLI script to dump OpenAPI JSON for frontend
├── tests/                              # Contract tests, auth tests, SSE snapshot & replay tests
├── Caddyfile                           # SSE flush_interval -1 configuration
├── Dockerfile
└── docker-compose.yml

frontend/
├── src/
│   ├── api/
│   │   ├── client.ts                   # Unified request() wrapper (timeout, retry, ETag, 401)
│   │   ├── types.ts                    # Public contract types (aligned with backend)
│   │   └── schema.d.ts                 # NEW: Generated TypeScript types from OpenAPI
│   ├── auth/
│   │   ├── AuthContext.tsx             # 60m expiry timer, remove fake refresh, roles viewer|admin
│   │   └── LoginPage.tsx               # Session-expired notice, dev-only quick-fill button
│   ├── hooks/
│   │   ├── useIndicatorData.ts         # Hook consuming dashboard store & stale-while-revalidate
│   │   └── useTickerStream.ts          # Ticket fetch, snapshot listener, backoff, polling fallback
│   ├── store/
│   │   └── slices/
│   │       └── indicatorsSlice.ts      # Consolidated dashboard store with 5-minute refresh
│   ├── components/
│   │   ├── SourceFooter/SourceFooter.tsx # Source string, Non-NSE badge, estimate indicator
│   │   └── Ticker/Ticker.tsx           # Badge driven by market_status (LIVE/CLOSED/STALE)
│   └── mocks/                          # Dynamically imported; tree-shaken from production
├── package.json                        # Scripts: gen:api, openapi-typescript devDependency
├── vite.config.ts                      # Direct SSE origin connection, proxy config
└── tests/                              # Unit, client, hook, and Playwright e2e tests
```

---

## Detailed Implementation Breakdown

### Phase A: Backend Presenters & Contract Alignment (I1, I2)
1. **Create `backend/app/presenters/`**:
   - `gdp_growth.py`: builds `values.india`, `values.world`, series rows `year`, `indiaRate`, `worldRate`.
   - `debt_to_gdp.py`: builds `values.indiaFy25`, `values.indVsUs` (gap), series rows `year`, `indiaDebt`, `usaDebt`.
   - `trade_balance.py`: converts US$ to $B, builds `values.exports`, `values.imports`, series rows with YoY growth bars and signed `tradeBalancePctGdp` line.
   - `gst_collection.py`: converts Rs crore to lakh crore, builds `values.collections` (YoY %), `values.monthlyAverage`, series rows `period`, `growthRate`, `monthlyAverage`.
   - `inflation.py`: builds `values.inflationRate`, `values.rbiTarget` (constant 4.0, delta `null`), series rows `year`, `actualRate`, `targetRate`.
   - `govt_expenditure.py`: converts Rs crore to lakh crore, builds `values.totalExpenditure`, `values.capitalExpenditure`, series rows `year`, `total`, `capital`, `revenue`, `basis`, `estimate: true` for RE/BE.
2. **Refactor `backend/app/services/indicator_service.py`**:
   - Strip inline formatting logic; keep PostgreSQL querying, cache retrieval, and freshness determination.
   - Dispatch to presenter: `presenter = get_presenter(canonical_slug); return presenter.format(obs_rows, source_row, overall_status)`.
3. **Fix ETag & 304 Handling**:
   - In `backend/app/routes/indicators.py` and `indicator_service.py`, return `Response(status_code=304, headers={"ETag": etag, "Cache-Control": "private, max-age=60"})` to preserve headers without body.

### Phase B: OpenAPI Schema Generation & TypeScript Drift Gate (I1)
1. **Create `backend/scripts/export_openapi.py`**:
   - Exports `app.openapi()` to `backend/openapi.json`.
2. **Add `openapi-typescript` in `frontend/package.json`**:
   - Add script `"gen:api": "openapi-typescript ../backend/openapi.json -o src/api/schema.d.ts"`.
3. **Automate in CI (`.github/workflows/ci.yml`)**:
   - Step: run `python backend/scripts/export_openapi.py`, then `cd frontend && npm run gen:api && git diff --exit-code src/api/schema.d.ts`.

### Phase C: Authentication, Security & Startup Guard (I3, I9)
1. **Route Protection**:
   - Attach `user: AuthUser = Depends(get_current_user)` to:
     - `GET /api/dashboard`
     - `GET /api/indicators/{indicator_slug}`
     - `GET /api/ticker` and `GET /api/ticker/latest`
     - `GET /api/stream/ticker` (validates mandatory `ticket` parameter)
2. **Align User Roles**:
   - Update `AuthUser.role` and DB enum to `Literal["viewer", "admin"]`.
3. **Runtime Seeding in `backend/scripts/seed_user.py`**:
   - Hash `os.environ["EVAL_PASSWORD"]` at runtime using bcrypt; remove hardcoded defaults.
4. **Startup Guard**:
   - In `backend/app/main.py` lifespan: check if `DATA_MODE == "live"`. If secrets match insecure defaults and `ALLOW_INSECURE_DEFAULTS != "true"`, raise `SystemExit(1)`.
5. **Rate Limiting Key Behind Proxy**:
   - In `backend/app/security/rate_limit.py`: key on `X-Forwarded-For` leftmost IP or `X-Real-IP`.

### Phase D: Ticker Protocol, SSE & Dynamic Scheduler (I4, I5, I6)
1. **Dynamic Scheduler Cadence**:
   - Unify into a single job in `backend/app/scheduler.py`: checks Kolkata market hours (09:15–15:30 IST, Mon–Fri).
   - If market open: schedule next run in 20s. If market closed: schedule next run in 10m.
   - On startup: trigger immediate execution (`next_run_time=now`) for ticker and for macro collection if `observations` is empty.
2. **Read-Time `market_status`**:
   - Evaluated dynamically in `ticker_service.py` at read time:
     - Open & fresh (<2x interval) → `open`
     - Outside trading hours → `closed`
     - Delayed (>2x interval or SSE down >60s) → `stale`
3. **Named `"snapshot"` Event Broadcast**:
   - In `backend/app/sse.py`: format SSE event as `event: snapshot\nid: {id}\nretry: 3000\ndata: {json}\n\n`.
   - Send 15s heartbeat comment `: ping\n\n`.
4. **Health Reporting**:
   - Update `GET /health` to report last run timestamp and elapsed age per scheduled job.

### Phase E: Frontend Universal Client, Auth & State Hydration (I3, I4, I7, I8)
1. **Refactor `frontend/src/api/client.ts`**:
   - Implement `request<T>(path, options)`:
     - Normalizes `VITE_API_BASE_URL`.
     - Injects `Authorization: Bearer <inMemoryToken>`.
     - Enforces 10-second `AbortController` timeout.
     - Performs 2 retries with exponential backoff on network failures.
     - On HTTP 401: invokes `handleSessionExpired()`, clearing token and navigating to `/login?session_expired=true`.
     - Supports conditional `ETag` and returns cached payload on 304.
2. **Dynamic Mock Loading & Ribbon**:
   - Default to live (`VITE_USE_MOCKS !== 'true'`).
   - Use dynamic `import()` for mocks only when `VITE_USE_MOCKS === 'true'`.
   - Display "MOCK DATA" ribbon when active.
3. **Auth Expiry Timer & Quick-Fill**:
   - In `AuthContext.tsx`: remove fake refresh loop. Start 60-minute countdown timer logging out upon expiry.
   - In `LoginPage.tsx`: show session-expired alert; render demo quick-fill credentials button only when `import.meta.env.DEV`.
4. **Resilient `useTickerStream`**:
   - On mount: `GET /api/ticker`, then `POST /api/auth/stream-ticket`, then `EventSource /api/stream/ticker?ticket=...`.
   - Listen to `event: snapshot`; replace quote array.
   - Reconnect with 1s–30s exponential backoff and jitter.
   - After 3 consecutive failures: start concurrent 10-second polling to `GET /api/ticker`.
   - Terminate all timers and streams on unmount or sign-out.
5. **Dashboard Store & 5-Minute Refresh**:
   - First paint fetches `GET /api/dashboard` (ETag/304), distributing to Redux store.
   - Refresh every 5 minutes with stale-while-revalidate behavior.
   - Update `SourceFooter.tsx` to render source, `Non-NSE` badge, as-of period, and estimate indicator.

### Phase F: Docker Compose, Caddy & CI Integration (I9, Quality)
1. **Update `docker-compose.yml`**:
   - Load configuration via `env_file: [.env]`. Remove inline secrets.
   - Remove `ports` from `db` service (PostgreSQL isolated within `internal_network`).
2. **Update `backend/Caddyfile`**:
   - Set `flush_interval -1` for `/api/stream/*` to disable SSE buffering.
3. **Comprehensive Quality Test Suites**:
   - **Backend**:
     - Contract tests validating exact keys and types emitted in live mode against seeded PostgreSQL.
     - Auth tests: verify 401 on every protected route (`/indicators/*`, `/dashboard`, `/ticker`, `/stream/ticker`); verify ticket reuse is rejected (HTTP 403).
     - SSE snapshot and replay tests.
   - **Frontend**:
     - Client tests for 401 handling, 10s timeout, and 2 retries with backoff.
     - Ticker hook tests with a mock `EventSource`: snapshot reception, reconnect backoff, 3-strike polling fallback, unmount cleanup.
     - Production bundle test: verify mock JSON files are 100% absent from `dist/`.
   - **Playwright E2E**:
     - Live login, all six panels display live values, ticker streaming updates, backend stopped leads to STALE, restart leads to recovery.
     - Visual snapshot tests run in mock mode.
   - **CI Pipeline (`.github/workflows/ci.yml`)**:
     - Add PostgreSQL service container for live backend contract tests.
     - Add OpenAPI drift check.
     - Build frontend with `VITE_USE_MOCKS=false`.
4. **Update `README.md`**:
   - Document environment variables, live vs mock modes, startup commands, and ticker behavior.
