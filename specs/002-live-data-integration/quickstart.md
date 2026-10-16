# Quickstart Validation Guide: End-to-End Live Dashboard Integration

**Feature**: [002-live-data-integration](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/002-live-data-integration/spec.md)  
**Date**: 2026-10-16  
**Status**: Approved

This guide outlines end-to-end validation scenarios to verify that the integrated FastAPI backend and React dashboard function reliably across live and mock modes, with full authentication, streaming, resilience, and security.

---

## Prerequisites & Environment Setup

1. **Docker & Docker Compose**: Ensure Docker engine is active.
2. **Environment File**:
   Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```
   Ensure `.env` contains:
   ```env
   DATA_MODE=live
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=prod_secure_pg_password_2026!
   DATABASE_URL=postgresql://postgres:prod_secure_pg_password_2026!@db:5432/economic_indicators
   JWT_SECRET=prod_super_secret_jwt_key_randomized_hex_or_base64_2026!
   EVAL_USERNAME=analyst@adityabirla.com
   EVAL_PASSWORD=SecureAnalystPass@2026!
   FRONTEND_ORIGIN=http://localhost:5173
   ALLOW_INSECURE_DEFAULTS=false
   ```

---

## Validation Scenario 1: Backend Startup Guard & Secret Verification

**Goal**: Prove the backend halts in `DATA_MODE=live` if default or insecure secrets are detected without `ALLOW_INSECURE_DEFAULTS=true`.

1. Start the backend with default example `JWT_SECRET`:
   ```bash
   JWT_SECRET="c2VjdXJlX2p3dF9zZWNyZXRfa2V5X2Zvcl9lY29ub21pY19pbmRpY2F0b3JfZGFzaGJvYXJkXzIwMjY=" \
   DATA_MODE=live \
   ALLOW_INSECURE_DEFAULTS=false \
   python3 -m backend.app.main
   ```
2. **Expected Outcome**:
   The process raises `RuntimeError` or `SystemExit(1)` displaying:
   `[Startup Guard] FATAL: Insecure or default JWT_SECRET detected in live data mode. Refusing to start.`

---

## Validation Scenario 2: Live Database Migrations & Runtime User Seeding

**Goal**: Prove PostgreSQL migrations execute and `seed_user.py` hashes `EVAL_PASSWORD` dynamically at runtime.

1. Launch PostgreSQL and run migrations:
   ```bash
   docker compose up -d db
   python3 -m backend.scripts.migrate
   python3 -m backend.scripts.seed_user
   ```
2. Verify seeded user in database:
   ```bash
   docker compose exec db psql -U postgres -d economic_indicators -c "SELECT username, role, SUBSTRING(password_hash, 1, 10) FROM users;"
   ```
3. **Expected Outcome**:
   Record returns username `analyst@adityabirla.com`, role `admin`, and a valid bcrypt hash prefix (`$2b$12$...`).

---

## Validation Scenario 3: End-to-End Authentication & Dashboard First Paint

**Goal**: Prove the analyst can authenticate, receive a 60-minute JWT token, and load the consolidated dashboard via `GET /api/dashboard` (ETag/304).

1. Launch backend:
   ```bash
   docker compose up -d backend
   ```
2. Authenticate via login endpoint:
   ```bash
   curl -s -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"analyst@adityabirla.com","password":"SecureAnalystPass@2026!"}' > /tmp/login.json
   cat /tmp/login.json
   ```
   Extract token:
   ```bash
   TOKEN=$(grep -o '"accessToken":"[^"]*' /tmp/login.json | cut -d'"' -f4)
   ```
3. Query `/api/dashboard` with Bearer token:
   ```bash
   curl -i -s http://localhost:8000/api/dashboard \
     -H "Authorization: Bearer $TOKEN" > /tmp/dashboard_res.txt
   head -n 15 /tmp/dashboard_res.txt
   ```
4. Test ETag 304 Not Modified conditional request:
   ```bash
   ETAG=$(grep -i '^etag:' /tmp/dashboard_res.txt | tr -d '\r' | awk '{print $2}')
   curl -i -s http://localhost:8000/api/dashboard \
     -H "Authorization: Bearer $TOKEN" \
     -H "If-None-Match: $ETAG" | head -n 10
   ```
5. **Expected Outcome**:
   - Initial call returns HTTP 200 with all 6 indicator payloads matching `IndicatorResponse` shapes in [indicator-api.json](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/002-live-data-integration/contracts/indicator-api.json).
   - Conditional call returns HTTP 304 Not Modified with identical `ETag` and `Cache-Control: private, max-age=60` headers, with zero response body.

---

## Validation Scenario 4: Live SSE Ticker Streaming & Snapshot Replay

**Goal**: Acquire a single-use stream ticket, connect to `/api/stream/ticker`, receive named `"snapshot"` events, and verify ticket consumption.

1. Acquire stream ticket:
   ```bash
   curl -s -X POST http://localhost:8000/api/auth/stream-ticket \
     -H "Authorization: Bearer $TOKEN" > /tmp/ticket.json
   TICKET=$(grep -o '"ticket":"[^"]*' /tmp/ticket.json | cut -d'"' -f4)
   ```
2. Connect to SSE stream:
   ```bash
   curl -N -s "http://localhost:8000/api/stream/ticker?ticket=$TICKET" | head -n 20
   ```
3. Verify ticket reuse is rejected:
   ```bash
   curl -i -s "http://localhost:8000/api/stream/ticker?ticket=$TICKET"
   ```
4. **Expected Outcome**:
   - Stream yields `event: snapshot` with monotonic `id: ...`, client retry hint, and quotes array containing NIFTY BANK, NIFTY IT, and SENSEX with read-time `market_status`.
   - Reusing the same ticket returns HTTP 403 Forbidden (`Invalid or expired stream ticket`).

---

## Validation Scenario 5: Stale-While-Revalidate & Error Isolation

**Goal**: Verify that when one indicator encounters upstream failure, the panel retains last known data labeled "Stale", while other panels remain fully operational.

1. Inspect panel response during normal state:
   ```bash
   curl -s http://localhost:8000/api/indicators/gdp-growth \
     -H "Authorization: Bearer $TOKEN" | grep -o '"status":"[^"]*'
   ```
2. In browser frontend:
   - Disconnect network or mock endpoint failure for `trade-balance`.
   - Verify `trade-balance` displays an isolated error card with "Retry" action.
   - Verify remaining 5 panels continue to display data without blanking.
   - Click "Retry" after restoring connectivity; verify panel recovers to normal state.

---

## Validation Scenario 6: Standalone Mock Mode & Bundle Verification

**Goal**: Verify mock mode works offline and mock JSON fixtures are tree-shaken out of production builds.

1. Build frontend in live mode:
   ```bash
   cd frontend
   VITE_USE_MOCKS=false npm run build
   ```
2. Verify absence of mock JSON in `frontend/dist/`:
   ```bash
   grep -rn "usr_mock_001" dist/ || echo "✓ Mock files cleanly excluded from production bundle"
   ```
3. Run frontend in mock mode:
   ```bash
   VITE_USE_MOCKS=true npm run build
   ```
   - Launch preview (`npm run preview`); verify "MOCK DATA" ribbon appears in the top corner.

---

## Validation Scenario 7: OpenAPI Drift Verification & CI Test Suite

**Goal**: Ensure automated CI checks validate TypeScript type alignment and backend test suites.

1. Generate TypeScript schemas from FastAPI OpenAPI:
   ```bash
   cd frontend
   npm run gen:api
   git diff --exit-code src/api/schema.d.ts
   ```
2. Run backend and frontend test suites:
   ```bash
   # Backend live contract & auth tests
   pytest backend/tests/test_indicators.py backend/tests/test_auth.py backend/tests/test_sse.py -v

   # Frontend unit & hook tests
   cd frontend && npm test
   ```
3. **Expected Outcome**:
   - Zero schema drift between backend OpenAPI and frontend types.
   - All contract, auth, SSE, timeout, and retry tests pass cleanly.
