# Tasks: End-to-End Live Dashboard Integration

**Feature**: [002-live-data-integration](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/002-live-data-integration/spec.md)  
**Implementation Plan**: [plan.md](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/002-live-data-integration/plan.md)  
**Status**: Ready for Implementation

---

## Phase 1: Security Baseline (Item 1)

**Purpose**: Remove committed secrets, add environment configuration templates, enforce live-mode startup guards, hash seed passwords dynamically at runtime, and eliminate mock password bypasses.

**Done when**: Live login works with the environment password; backend startup fails fast in live mode if defaults or insecure secrets are detected.

- [X] T001 Remove committed default secrets and add live-mode startup guard in `backend/app/config.py` and `backend/app/main.py`
- [X] T002 Add `.env.example` templates in repo root `.env.example` and `backend/.env.example`
- [X] T003 Update `backend/scripts/seed_user.py` to hash `EVAL_PASSWORD` dynamically at runtime using bcrypt
- [X] T004 Drop mock-mode hardcoded password bypass in `backend/app/routes/auth.py`
- [X] T005 [P] Add unit/integration tests for startup guard failure and runtime seed user login in `backend/tests/test_security.py`

---

## Phase 2: Schema Contract & Drift Prevention (Item 2)

**Purpose**: Establish Pydantic response models as the single source of truth, export OpenAPI specification, generate TypeScript types, and enforce automated CI schema drift prevention.

**Done when**: `npm run gen:api` generates `frontend/src/api/schema.d.ts` matching backend models, and CI fails on uncommitted schema drift.

- [X] T006 Align Pydantic response models in `backend/app/schemas/envelope.py` and `backend/app/schemas/auth.py` with canonical indicator slugs and roles
- [X] T007 Implement OpenAPI specification export script in `backend/scripts/export_openapi.py`
- [X] T008 Add `openapi-typescript` devDependency and `"gen:api"` script in `frontend/package.json` to generate `frontend/src/api/schema.d.ts`
- [X] T009 Add automated schema drift verification script/step in CI workflow

---

## Phase 3: Presenters & Indicator Data Transformation (Item 3 - US1)

**Purpose**: Implement dedicated presenters for all six macroeconomic panels (`app/presenters/`) handling unit conversion, YoY growth rates, estimate tagging, and display string formatting.

**Done when**: Live responses from all six indicator endpoints validate exactly against the public `IndicatorResponse` contract against seeded PostgreSQL.

- [X] T010 [P] [US1] Create GDP Growth presenter in `backend/app/presenters/gdp_growth.py`
- [X] T011 [P] [US1] Create Debt to GDP presenter in `backend/app/presenters/debt_to_gdp.py`
- [X] T012 [P] [US1] Create Trade Balance presenter in `backend/app/presenters/trade_balance.py`
- [X] T013 [P] [US1] Create GST Collection presenter in `backend/app/presenters/gst_collection.py`
- [X] T014 [P] [US1] Create Inflation presenter in `backend/app/presenters/inflation.py`
- [X] T015 [P] [US1] Create Government Expenditure presenter in `backend/app/presenters/govt_expenditure.py`
- [X] T016 [US1] Implement presenter registry dispatcher in `backend/app/presenters/__init__.py` and refactor `backend/app/services/indicator_service.py` to delegate presentation
- [X] T017 [US1] Fix HTTP 304 Not Modified header preservation in `backend/app/routes/indicators.py` and `backend/app/services/indicator_service.py`
- [X] T018 [US1] Add live-mode PostgreSQL contract tests validating exact keys, tiles, and series shapes in `backend/tests/test_indicators.py`

---

## Phase 4: Route Protection & Global 401 Authorization (Item 4 - US1)

**Purpose**: Protect all indicator, dashboard, and ticker routes with mandatory Bearer authentication (`get_current_user`).

**Done when**: Every protected route rejects unauthenticated requests with HTTP 401, and authenticated analysts with valid Bearer tokens access data cleanly.

- [X] T019 [US1] Attach `get_current_user` Bearer dependency to all indicator and dashboard endpoints in `backend/app/routes/indicators.py` and `backend/app/routes/ticker.py`
- [X] T020 [US1] Add comprehensive auth tests verifying HTTP 401 on unauthenticated access across all protected endpoints in `backend/tests/test_auth.py`

---

## Phase 5: Scheduler Fixes & Background Ingestion (Item 5 - US2)

**Purpose**: Unify ticker ingestion into a single dynamic-cadence job, trigger startup bootstrapping, and expose job execution ages on `/health`.

**Done when**: Single scheduler job runs at 20s market hours / 10m off-hours; initial macro and ticker collections run at startup; `/health` reports execution age per job.

- [X] T021 [US2] Consolidate overlapping ticker jobs into a single dynamic-cadence job in `backend/app/scheduler.py`
- [X] T022 [US2] Add non-blocking startup ticker ingestion and macro bootstrap via `next_run_time=now` in `backend/app/scheduler.py`
- [X] T023 [US2] Update `/health` endpoint in `backend/app/routes/health.py` to report last run timestamp and elapsed age per scheduled job

---

## Phase 6: Server-Sent Events Ticker Streaming (Item 6 - US2)

**Purpose**: Stream market quotes under a single named `"snapshot"` SSE event with monotonic IDs, 15s heartbeats, mandatory single-use tickets, and read-time market status.

**Done when**: EventSource receives named `"snapshot"` events with all 3 quotes; ticket reuse is rejected with HTTP 403; ring-buffer replay works via `Last-Event-ID`.

- [X] T024 [US2] Update `backend/app/sse.py` to broadcast named `"snapshot"` events with monotonic ID, retry hint, and 15-second heartbeat comments
- [X] T025 [US2] Enforce mandatory single-use ticket validation on `GET /api/stream/ticker` in `backend/app/routes/ticker.py` and `backend/app/sse.py`
- [X] T026 [US2] Compute read-time `market_status` (`open` & fresh = `LIVE`, `closed` = `CLOSED`, >2x interval or SSE down >60s = `STALE`) in `backend/app/services/ticker_service.py`
- [X] T027 [US2] Add SSE snapshot, mandatory ticket, and ring-buffer replay tests in `backend/tests/test_sse.py`

---

## Phase 7: Frontend API Client Rewrite (Item 7 - US1/US4)

**Purpose**: Rewrite `frontend/src/api/client.ts` with a universal `request()` wrapper handling base URL normalization, Bearer authentication, 10-second timeout, 2 retries with backoff, ETag caching, global 401 interception, dynamic mock loading, and "MOCK DATA" ribbon.

**Done when**: All client requests use the unified wrapper; 401 redirects to `/login?session_expired=true`; mocks are dynamically imported and excluded from production builds.

- [X] T028 [US1] Implement universal `request()` wrapper in `frontend/src/api/client.ts` with URL normalization, Bearer header, 10s AbortController timeout, 2 retries, and global 401 handler
- [X] T029 [US4] Configure dynamic mock loading in `frontend/src/api/client.ts` with live default (`VITE_USE_MOCKS !== 'true'`)
- [X] T030 [US4] Add visible "MOCK DATA" ribbon in `frontend/src/components/Header/Header.tsx` or `frontend/src/App.tsx` when mock mode is active
- [X] T031 [US1] Add unit tests for timeout, retry, ETag, and 401 handling in `frontend/tests/api/client.test.ts`

---

## Phase 8: Auth Cleanup & Session Expiry (Item 8 - US1)

**Purpose**: Eliminate fake refresh token hacks, establish a 60-minute countdown expiry timer, align roles to `viewer` | `admin`, and restrict demo quick-fill to development builds.

**Done when**: Analyst logs in, timer terminates session at 60 minutes with session-expired notice, roles match across types, and quick-fill button is absent in production builds.

- [X] T032 [US1] Remove fake token refresh loop and implement 60-minute countdown timer logging out upon expiry in `frontend/src/auth/AuthContext.tsx`
- [X] T033 [US1] Align user roles to `viewer` | `admin` in `frontend/src/api/types.ts` and `frontend/src/auth/AuthContext.tsx`
- [X] T034 [US1] Restrict demo quick-fill credentials button to `import.meta.env.DEV` and display session expired notice in `frontend/src/auth/LoginPage.tsx`

---

## Phase 9: Frontend Ticker Stream Hook & Market Status Badge (Item 9 - US2)

**Purpose**: Rewrite `useTickerStream` to fetch an initial snapshot, acquire a single-use ticket, connect to the named `"snapshot"` SSE event with backoff, and fall back to 10s polling after 3 consecutive failures.

**Done when**: Header ticker displays live streaming quotes, reflects read-time `LIVE`/`CLOSED`/`STALE` status with hover timestamps, and falls back to polling seamlessly.

- [X] T035 [US2] Rewrite `useTickerStream` hook in `frontend/src/hooks/useTickerStream.ts` with ticket fetch, named `"snapshot"` listener, 1s–30s backoff with jitter, and 10s polling fallback after 3 failures
- [X] T036 [US2] Update `Ticker` component in `frontend/src/components/Ticker/Ticker.tsx` and `StatusBadge` to display dynamic `LIVE`, `CLOSED`, or `STALE` status with hover tooltips
- [X] T037 [US2] Add unit tests for `useTickerStream` with a mock EventSource in `frontend/tests/hooks/useTickerStream.test.ts`

---

## Phase 10: Dashboard Store, Refresh & SourceFooter (Item 10 - US1/US3)

**Purpose**: Update Redux store for initial `GET /api/dashboard` first paint, 5-minute periodic refresh, stale-while-revalidate error handling, and SourceFooter estimate markers.

**Done when**: Dashboard renders in under 3s via consolidated payload; panels refresh every 5m; failed panels retain last valid data marked stale; SourceFooter displays source string, Non-NSE badge, as-of date, and estimate marker.

- [X] T038 [US1] Update Redux indicators slice in `frontend/src/store/slices/indicatorsSlice.ts` to support `fetchDashboardThunk` (ETag/304), 5-minute refresh, and stale-while-revalidate
- [X] T039 [US1] Update `useIndicatorData` hook in `frontend/src/hooks/useIndicatorData.ts` to consume dashboard store with isolated panel error handling and retry
- [X] T040 [US3] Update `SourceFooter` in `frontend/src/components/SourceFooter/SourceFooter.tsx` to display source string, `Non-NSE` badge, as-of date, and estimate indicator

---

## Phase 11: Docker Compose & Caddy Reverse Proxy Hardening (Item 11)

**Purpose**: Harden deployment configuration with `env_file`, unpublished PostgreSQL port, Caddy non-buffering SSE proxying, and real client IP rate limiting.

**Done when**: `docker compose up` starts with no inline secrets, PostgreSQL is unreachable from the host, Caddy streams SSE without buffering, and rate limiting keys on client IP.

- [X] T041 Configure `backend/Caddyfile` with `flush_interval -1` for `/api/stream/*` and forward client IP headers
- [X] T042 Update `docker-compose.yml` to use `env_file: [.env]`, remove inline passwords, and unpublish PostgreSQL port
- [X] T043 Add real client IP extraction from `X-Forwarded-For` in `backend/app/security/rate_limit.py`
- [X] T044 Verify Docker Compose stack launches cleanly and PostgreSQL is strictly isolated

---

## Phase 12: Playwright End-to-End Tests (Item 12)

**Purpose**: Implement full end-to-end integration tests on Docker Compose verifying live login, all six indicator panels, ticker streaming, and outage/recovery behavior.

**Done when**: Playwright e2e test executes against live Compose stack; stopping backend transitions ticker to STALE; restarting backend restores LIVE; visual regression tests pass in mock mode.

- [X] T045 Create Playwright e2e test in `frontend/tests/visual/e2e-live.spec.ts` covering login, live values on all 6 panels, ticker streaming, backend stop -> STALE, and restart -> recovery
- [X] T046 Verify existing visual regression tests pass cleanly in mock mode without layout shifts at 1214 × 2159 resolution

---

## Phase 13: CI Updates, Spec Contracts & Documentation (Item 13)

**Purpose**: Finalize CI pipeline with PostgreSQL service container and production bundle mock exclusion check, update documentation and contract files.

**Done when**: GitHub Actions runs live backend tests and OpenAPI drift check; production bundle has zero mock files; README contains complete operational guides.

- [X] T047 Update `.github/workflows/ci.yml` with PostgreSQL service container, live backend contract tests, OpenAPI drift check, and production build check verifying mock exclusion
- [X] T048 Update `README.md` with environment variables, operational modes, execution commands, and ticker behavior

---

## Dependencies & Execution Order

1. **Phase 1 (Security Baseline)** MUST complete first to ensure uncommitted credentials and startup guards protect the environment.
2. **Phase 2 (Contract)** establishes the single source of truth Pydantic models and generates frontend TypeScript types.
3. **Phase 3 (Presenters)** implements data transformation for all six panels, keeping backend contract tests green.
4. **Phase 4 (Route Protection)** secures all endpoints with Bearer auth.
5. **Phase 5 & 6 (Scheduler & SSE)** upgrade background ingestion, streaming protocols, and read-time market status.
6. **Phase 7 & 8 (Frontend Client & Auth)** implement the resilient HTTP wrapper, 60m expiry timer, and dynamic mock imports.
7. **Phase 9 & 10 (Frontend Ticker & Dashboard Store)** wire up the live SSE stream, status badges, dashboard store, and SourceFooter indicators.
8. **Phase 11, 12 & 13 (Compose, Playwright & CI)** harden deployment containers, run full outage/recovery e2e scenarios, and finalize CI pipelines.
