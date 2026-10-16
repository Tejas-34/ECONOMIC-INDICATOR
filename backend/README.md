# Economic Indicator Dashboard: FastAPI Backend

Production-grade, resilient FastAPI backend for the Economic Indicator Dashboard. Serves macroeconomic indicator panels and live market index quotes via Server-Sent Events (SSE), backed by PostgreSQL 16 (psycopg3 connection pooling with raw parameterized SQL).

---

## 1. Architecture & Core Decisions

- **Framework**: FastAPI (async), Uvicorn single-worker process.
- **Database**: PostgreSQL 16 accessed via `psycopg[binary,pool]` (`AsyncConnectionPool`) with raw parameterized SQL only (strictly zero ORM overhead).
- **Scheduling**: `APScheduler` (`AsyncIOScheduler`) managing background collectors within the FastAPI lifespan context.
- **Live Streaming**: Server-Sent Events (SSE) at `GET /api/stream/ticker?ticket=...` with single-use 30-second authorization tickets, 15s heartbeat comments (`: ping\n\n`), bounded queues (`maxsize=100`, dropping oldest on congestion), and a 50-event in-memory ring buffer for `Last-Event-ID` reconnection replay.
- **Resilience Engine**: `BaseCollector` enforcing 3.0s connect / 8.0s read timeouts, 3 retries with exponential backoff and random jitter, 15-second minimum interval per external host, 5-failure circuit breaker, and domain plausibility boundaries.
- **Attribution & Provenance**: Standardized indicator envelope (`{indicator, title, tiles, series, source, as_of, fetched_at, status}`). Missing values render strictly as `null` ("—" in UI) and never invent numbers.
- **Security**: JWT HS256 with 60-minute expiration, bcrypt password hashing, slowapi rate limiting (5 req/min on login), and strict CORS origin locking.

---

## 2. Operational Architecture

The backend operates strictly in **Live Mode (`DATA_MODE=live`)**:
- Connects directly to PostgreSQL 16 via `psycopg3` connection pool.
- Background APScheduler dynamically updates quotes every 20 seconds during NSE market hours (09:15–15:30 IST) and every 10 minutes off-hours.
- Executes upstream collectors with automated fallback (NSE/BSE ticker with Yahoo Finance fallback, World Bank, IMF DataMapper).
- Ingests official Union Budget (`indiabudget.gov.in`) and GST monthly figures (`data.gov.in`) into PostgreSQL `observations`.

---

## 3. Quickstart & Local Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 16

### Installation
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### Running the Server
```bash
# Start FastAPI live server (PostgreSQL connected)
DATA_MODE=live ALLOW_INSECURE_DEFAULTS=true uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

---

## 4. Database Migrations & Seed Utilities

```bash
# 1. Apply numbered SQL migrations (001, 002, 003)
python backend/scripts/migrate.py

# 2. Seed default evaluation analyst user
python backend/scripts/seed_user.py

# 3. Idempotently load curated seed CSVs into observations table
python backend/scripts/load_seeds.py

# 4. Run diagnostic upstream reachability probe
python backend/scripts/probe_sources.py
```

---

## 5. Authentication & Evaluation Access

- **Evaluation Username**: `analyst@adityabirla.com`
- **Evaluation Password**: `Analyst@2026`
- **Role**: `admin`
- **Token Validity**: 60 minutes
- **Rate Limit**: 5 login attempts per minute per IP address.

### Example Auth & SSE Workflow
```bash
# 1. Authenticate analyst
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"analyst@adityabirla.com","password":"Analyst@2026"}'

# 2. Acquire single-use stream ticket
curl -X POST http://localhost:8000/api/auth/stream-ticket \
  -H "Authorization: Bearer <TOKEN>"

# 3. Connect to live SSE ticker stream
curl -N "http://localhost:8000/api/stream/ticker?ticket=<TICKET>"
```

---

## 6. API Route Directory

| Method | Endpoint | Access | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/health` | Public | System health, database status, scheduler state |
| `POST` | `/api/auth/login` | Public (Rate-limited) | Analyst login (5 req/min per IP) |
| `GET` | `/api/auth/me` | Bearer Token | Authenticated user identity |
| `POST` | `/api/auth/stream-ticket` | Bearer Token | Generate single-use 30-second SSE ticket |
| `GET` | `/api/indicators/{slug}` | Public/Token | Individual panel envelope (`gdp-growth`, `debt-to-gdp`, `trade`, `gst`, `inflation`, `government-expenditure`) |
| `GET` | `/api/dashboard` | Public/Token | Consolidated dashboard with all 6 panels |
| `GET` | `/api/ticker` | Public | Current market quotes snapshot |
| `GET` | `/api/stream/ticker` | Ticket Query Param | Real-time SSE live quote stream |
| `POST` | `/api/admin/refresh/{job}` | Admin Role | On-demand collector execution (`macro`, `ticker`, `seeds`) |

---

## 7. Diagnostics & Upstream Verification

Run upstream probe and verify system health:
```bash
# 1. Run live diagnostic upstream reachability probe
./backend/.venv/bin/python backend/scripts/probe_sources.py

# 2. Check live system health and background scheduler stats
curl -s http://localhost:8000/health | jq .
```

Verification covers:
- World Bank, IMF DataMapper, and NSE/BSE upstream latency and status
- Active database connection pool status
- Dynamic scheduler job execution states (ticker 20s/10m, daily macro, history cleanup)
- Authentication and rate-limit guard enforcement
- Real-time SSE streaming with single-use tickets

---

## 8. Production Docker Deployment & Security Isolation

In production, PostgreSQL binds exclusively to an internal Docker network with **no published host ports**, ensuring the database is unreachable from the public internet.

```bash
# Start production stack with Caddy reverse proxy:
docker compose -f backend/docker-compose.prod.yml up -d --build

# Verify deployment and network isolation:
./backend/scripts/deploy_verify.sh
```
