# Economic Indicator Dashboard (Full-Stack)

A pixel-perfect, high-performance macroeconomic terminal built to reproduce the authoritative design specifications of `design/reference.png` at **1214 x 2159 CSS pixels**.

The application delivers an immediate visual readout of India's macroeconomic figures across six analytical panels, a live market index ticker via Server-Sent Events (SSE), strict data provenance tracking with estimate markers, multiple resilience states (loading, stale, empty, error, unavailable), and secure in-memory JWT authentication.

---

## 🏛️ Full-Stack Architecture

- **Frontend** (`frontend/`): React 18, Redux Toolkit, Apache ECharts, Vite, Selawik / Manrope typography.
- **Backend** (`backend/`): FastAPI (async), PostgreSQL 16 (psycopg connection pooling with raw parameterized SQL), APScheduler, SSE live quote streaming with monotonic IDs and 50-event ring buffer replay.
- **Reverse Proxy** (`backend/Caddyfile`): Caddy 2 with unbuffered SSE streaming (`flush_interval -1`) and real client IP forwarding.
- **Operational Modes**: Controlled via `DATA_MODE=live|mock` and `VITE_USE_MOCKS=false|true`.

---

## ⚙️ Environment Variables & Configuration

Configuration is managed via `.env` in the root repository. A template is provided in `.env.example`:

| Variable | Mode / Context | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `DATA_MODE` | Backend | `live` | `live` connects to PostgreSQL and collectors; `mock` serves offline fixtures. |
| `POSTGRES_USER` | Backend / DB | `postgres` | Database username. |
| `POSTGRES_PASSWORD` | Backend / DB | *(required in live)* | Database user password (no default permitted in live mode). |
| `DATABASE_URL` | Backend | *(constructed)* | Full PostgreSQL connection string with psycopg driver. |
| `JWT_SECRET` | Backend | *(required in live)* | Minimum 32-character secret key used to sign and verify HS256 JWT tokens. |
| `JWT_ALGORITHM` | Backend | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Backend | `60` | Lifespan of Bearer access tokens before session expiration. |
| `STREAM_TICKET_EXPIRE_SECONDS`| Backend | `30` | Lifespan of single-use ticket for `/api/stream/ticker`. |
| `EVAL_USERNAME` | Backend | `analyst@adityabirla.com` | Lead Macro Analyst username. |
| `EVAL_PASSWORD` | Backend | *(required in live)* | Plaintext password hashed at runtime via `scripts/seed_user.py`. |
| `ALLOW_INSECURE_DEFAULTS` | Backend | `false` | When `false`, backend refuses to start in live mode with default or weak secrets. Set to `true` strictly in dev. |
| `FRONTEND_ORIGIN` | Backend | `http://localhost:5173` | Allowed CORS origin for browser clients. |
| `VITE_USE_MOCKS` | Frontend | `false` | When `false`, connects to the backend API; when `true`, dynamically imports local mock fixtures. |
| `VITE_API_BASE_URL` | Frontend | `/api` | Base API route prefix (supports absolute origin or `/api`). |

---

## 🚀 Running the Application

### Option 1: Docker Compose (Recommended for Production & E2E)
```bash
# 1. Create your local .env from the template
cp .env.example .env

# 2. Launch PostgreSQL, FastAPI backend, and Caddy
docker compose up --build
```
- Frontend & Reverse Proxy: [http://localhost](http://localhost) (or [http://localhost:5173](http://localhost:5173) in dev)
- Backend API Direct: [http://localhost:8000/api](http://localhost:8000/api)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

### Option 2: Local Development

#### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations and seed the evaluation analyst user
alembic upgrade head
EVAL_PASSWORD=YourSecurePassword@2026! python scripts/seed_user.py

# Start the FastAPI server
DATA_MODE=live ALLOW_INSECURE_DEFAULTS=true uvicorn backend.app.main:app --port 8000 --reload
```

#### 2. Frontend Setup
```bash
cd frontend
npm install

# Start Vite development server
npm run dev
```

---

## 📈 Live Market Ticker & Streaming Protocol

The live ticker at the top of the terminal provides real-time market quotes (SENSEX, NIFTY 50, INR/USD):

1. **Initial Snapshot**: On component mount, the client performs `GET /api/ticker` to render quotes instantly without waiting for a streaming cycle.
2. **Single-Use Ticket Handshake**: The client requests a 30-second ticket via `POST /api/auth/stream-ticket` and connects EventSource directly to `${origin}/api/stream/ticker?ticket=...`. Missing, expired, or reused tickets are strictly rejected with HTTP 403.
3. **Snapshot Broadcast**: The backend publishes a single named `"snapshot"` event per ingestion cycle containing all updated quotes, accompanied by monotonic sequence IDs, retry hints, and 15-second heartbeat comments (`: ping\n\n`).
4. **Ring-Buffer Replay**: On reconnection with `Last-Event-ID`, the server replays missed events from a 50-event ring buffer.
5. **Backoff & Polling Fallback**: Reconnects with exponential backoff (1s to 30s) and jitter. After 3 consecutive stream failures, the client initiates fallback polling (`GET /api/ticker` every 10s) while SSE continues retrying in the background.
6. **Read-Time Market Status**:
   - `LIVE`: Trading hours (09:15–15:30 IST, Mon–Fri) and latest quote fresh (<= 40s).
   - `STALE`: Trading hours and quote older than 40s, or SSE disconnected > 60s.
   - `CLOSED`: Outside market hours, weekends, or trading stall > 15m (holiday). Hovering over the badge displays the exact last updated timestamp.

---

## 📊 Analytical Panels & Stale-While-Revalidate

- **First Paint Consolidation**: On initial load, the dashboard queries `GET /api/dashboard` (ETag / HTTP 304 cached) to populate all six panels in a single request.
- **5-Minute Isolated Panel Refresh**: Every 5 minutes, each panel independently refreshes its data (`fetchIndicatorThunk`).
- **Stale-While-Revalidate**: If an individual panel refresh fails (e.g., 500 error or network timeout), the panel **never blanks out**; it retains its last good data and marks its state as `stale`. One failing panel never degrades or resets the other five panels.
- **Data Provenance & SourceFooters**: Every panel displays its authoritative data source (`MoSPI`, `IMF`, `Ministry of Finance`), a `Non-NSE` badge for external feeds, the reporting period date, and an `Estimate` marker (e.g. for Revised and Budget estimates in Government Expenditure).

---

## 🔐 Security & Authorization

- **Mandatory Bearer Authentication**: Every `/api/*` endpoint (except `POST /api/auth/login` and `/health`) requires a valid Bearer token (`get_current_user`).
- **Global 401 Handler**: Any 401 response from the API immediately clears in-memory credentials and redirects to `/login?session_expired=true`.
- **60-Minute Session Timer**: Access tokens expire after 60 minutes. A client-side timer logs the user out upon expiration; no insecure refresh tokens are used.
- **Startup Guard**: In live mode (`DATA_MODE=live`), the server will immediately terminate at boot if default secrets or weak credentials are detected, unless `ALLOW_INSECURE_DEFAULTS=true` is set for local testing.
- **Real Client IP Rate Limiting**: Behind Caddy reverse proxy, rate limiting keys on the real client IP extracted from `X-Forwarded-For`.
- **Zero Mock Leakage**: Dynamic mock imports ensure that mock data files and tokens are completely stripped from production bundles (`VITE_USE_MOCKS=false npm run build`).

---

## 🧪 Testing Suite

```bash
# Backend pytest suite (mock mode)
DATA_MODE=mock ./backend/.venv/bin/pytest backend/tests/ -v

# Frontend unit and component tests (Vitest)
npm --prefix frontend test

# Visual regression & Playwright E2E tests (Mock evaluation)
npm --prefix frontend run test:visual

# OpenAPI schema drift verification
npm --prefix frontend run gen:api
git diff --exit-code frontend/src/api/schema.d.ts
```
