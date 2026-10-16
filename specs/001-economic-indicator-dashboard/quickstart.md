# Quickstart & Validation Guide: Economic Indicator Dashboard (Full-Stack)

**Feature**: [001-economic-indicator-dashboard](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/001-economic-indicator-dashboard/spec.md)  
**Date**: 2026-10-16  
**Status**: Ready for Implementation

This guide provides instructions to bootstrap, configure, run, and validate the FastAPI backend and React frontend both locally (mock and live modes) and in Docker Compose.

---

## 1. Prerequisites & Environment Configuration

### Required Tools
- **Python**: 3.11+
- **PostgreSQL**: 16.x (local or Docker)
- **Node.js**: 18.x+ (with `npm`)
- **Docker & Docker Compose**: (optional, for containerized run)

### Backend Environment Configuration
Create `backend/.env` (from `backend/.env.example`):

```env
DATA_MODE=mock
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/economic_indicators
JWT_SECRET=c2VjdXJlX2p3dF9zZWNyZXRfa2V5X2Zvcl9lY29ub21pY19pbmRpY2F0b3JfZGFzaGJvYXJkXzIwMjY=
EVAL_USERNAME=analyst@adityabirla.com
EVAL_PASSWORD_HASH=$2b$12$e6mO7jJ6g5lWkY8g2k.yquMhT6UfO6b5HjCgV4s9R2E1k3m8t2Y1e
FRONTEND_ORIGIN=http://localhost:5173
```

### Frontend Environment Configuration
In `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_USE_MOCKS=false
```

---

## 2. Backend Setup & Local Run

### 2.1 Virtual Environment & Dependencies
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2.2 Database Initialization & Migrations (Live Mode)
```bash
# Run numbered SQL migrations
python scripts/migrate.py

# Seed default evaluation analyst user
python scripts/seed_user.py

# Idempotently load seed CSVs (data/seed/gst_monthly.csv, government_expenditure.csv)
python scripts/load_seeds.py
```

### 2.3 Diagnostic Upstream Probe
Run the standalone diagnostic tool to verify upstream reachability (World Bank, IMF, NSE, BSE):
```bash
python scripts/probe_sources.py
```

### 2.4 Start Backend Server
```bash
# In mock mode:
DATA_MODE=mock uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# In live mode (requires Postgres running):
DATA_MODE=live uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 3. Frontend Local Run

In a separate terminal:
```bash
cd frontend
npm install
npm run dev
```
Navigate to `http://localhost:5173`.

---

## 4. Docker Compose Deployment

To run both backend and PostgreSQL in an isolated private network:
```bash
docker-compose up --build
```
- API is accessible at `http://localhost:8000`.
- PostgreSQL binds exclusively to the internal Docker network (no public port published).
- Database migrations and seed loader execute automatically on container startup.

---

## 5. Verification & Test Execution

### 5.1 Backend Pytest Suite
```bash
cd backend
pytest -v
```
Test suite validates:
- **Authentication**: Successful login, token expiration (60m), role enforcement (`viewer` vs `admin`), and rate limiting (5 req/min per IP).
- **SQL Injection**: Parameterized SQL security across endpoints.
- **Collector Resilience**: Retries with exponential backoff + jitter, circuit breaker (5 failures -> 5m pause), and domain plausibility boundaries.
- **Staleness Logic**: Indicators older than $2 \times \text{refresh\_interval}$ labelled `stale`.
- **Market Hours**: Evaluation of `Asia/Kolkata` time and holiday quote stall detection.
- **SSE Stream**: Single-use 30s ticket enforcement, event queue delivery, 15s heartbeats, ring buffer replay via `Last-Event-ID`.
- **Mock Mode Parity**: Verifies that `DATA_MODE=mock` responses match static fixtures.

### 5.2 Frontend Tests
```bash
# Unit tests
npm test

# Visual regression tests (1214 x 2159 px benchmark)
npm run test:visual
```

---

## 6. End-to-End Validation Scenarios

### Scenario 1: Authentication & Stream Ticket Acquisition
1. Perform analyst login:
   ```bash
   curl -X POST http://localhost:8000/api/auth/login \
     -H "Content-Type: application/json" \
     -d '{"username":"analyst@adityabirla.com","password":"Analyst@2026"}'
   ```
2. Request single-use SSE ticket using the Bearer token:
   ```bash
   curl -X POST http://localhost:8000/api/auth/stream-ticket \
     -H "Authorization: Bearer <TOKEN>"
   ```
3. Connect to live ticker stream:
   ```bash
   curl -N "http://localhost:8000/api/stream/ticker?ticket=<TICKET>"
   ```
   Observe quote stream events and 15s heartbeat comments. Reusing the ticket results in HTTP 403.

### Scenario 2: Indicator Envelope & Tile Change Verification
1. Request GDP indicator data:
   ```bash
   curl -H "Authorization: Bearer <TOKEN>" http://localhost:8000/api/indicators/gdp-growth
   ```
2. Verify response matches standard envelope:
   - Contains `indicator`, `tiles`, `series`, `source`, `as_of`, `fetched_at`, and `status`.
   - Rate series deltas calculated as $\text{latest} - \text{previous}$ in `pp`.
   - Missing data renders as `null` with no invented numbers.
