# Economic Indicator Dashboard (Full-Stack)

A pixel-perfect, high-performance macroeconomic terminal built to reproduce the authoritative Figma design reference at the exact evaluation viewport of **1214 × 2159 CSS pixels**.

The application delivers an immediate visual readout of India's macroeconomic figures across six analytical panels, a live market index ticker via Server-Sent Events (SSE), strict data provenance tracking with estimate markers, multiple resilience states (loading, stale, empty, error, unavailable), and secure in-memory JWT authentication.

---

## 🏛️ Full-Stack Architecture & Security Boundary

```
[ Browser Client (1214 × 2159 px) ]
         │  HTTPS / WSS / SSE
         ▼
[ Caddy 2 Reverse Proxy (Ports 80/443) ]
         │  Internal Docker Bridge (proxy_net)
         ▼
[ FastAPI Backend (Port 8000) ]
  ├── APScheduler (Dynamic Ticker 20s/10m, Daily Macro 06:30 IST)
  ├── SSE Event Stream Hub (Single-use tickets, 50-event replay buffer)
  ├── Resilient Upstream Collectors (NSE/BSE, IMF, MoSPI, data.gov.in)
  └── psycopg3 Async Connection Pool (Raw parameterized SQL only)
         │  Private Isolated Network (internal_net - No published ports)
         ▼
[ PostgreSQL 16 Database ]
```

- **Frontend** (`frontend/`): React 18, TypeScript, Redux Toolkit, Apache ECharts, Vite, CSS Modules, Manrope typography.
- **Backend** (`backend/`): FastAPI (async), PostgreSQL 16 (`psycopg3` connection pooling with raw parameterized SQL), APScheduler, SSE live streaming with monotonic IDs.
- **Database Security Isolation**: PostgreSQL binds strictly to an internal Docker network with **zero published host ports**. Direct parameterized queries prevent SQL injection without ORM overhead.
- **Reverse Proxy** (`backend/Caddyfile`): Caddy 2 with unbuffered SSE streaming (`flush_interval -1`) and real client IP forwarding.
- **Runtime Mode**: Operates in **Live Data Mode** (`DATA_MODE=live`), backed by PostgreSQL and live upstream collectors.

---

## 📊 Analytical Panels & Data Provenance

The visible dashboard comprises a live market ticker and six indicator panels, matching the design authority:

| Panel | Primary Source | Type | As of Date | Transformation / Methodology | Limitations & Fallback |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Live Market Ticker** | NSE allIndices / BSE | NSE / Non-NSE | Real-time | SENSEX, NIFTY 50, INR/USD live quotes; dynamic market hours status (LIVE / CLOSED / STALE). | BSE direct API intermittently returns HTTP 403; automatically falls back to Yahoo Finance feed. |
| **GDP Growth** | IMF WEO / MoSPI | Non-NSE | 2024-12-31 | India YoY growth (+7.0%, +0.3pp) vs World YoY growth (+3.2%, +0.1pp); historical comparison (2021–2025). | Annual figures released bi-annually. |
| **Debt to GDP Ratio** | IMF DataMapper (`GGXWDG_NGDP`) | Non-NSE | 2025-12-31 | India FY25 ratio (84.3%, -0.5pp) vs US comparison (-40.1%, -2.6pp); 2021–2025 annual series with floating pill badges. | Projections past current fiscal year represent IMF staff estimates. |
| **Trade Balance** | Ministry of Commerce & Industry / RBI | Non-NSE | 2025-03-31 | Exports ($437.1B) and Imports ($677.2B); scaled percentage-of-GDP bars (0–10%) and green Trade Balance trend line overlay. | Final balance numbers revised quarterly. |
| **GST Tax Collection** | data.gov.in (Rajya Sabha) / MoF | Non-NSE | 2025-03-31 | Total collections (₹16.34L Cr) and Monthly Average (₹1.63L Cr) formatted in single-line typography; 2021–2025 domestic vs imports breakdown. | Sourced from official Rajya Sabha resource `a49bb4e6-662a-4cd1-83b7-6add74c1b984`. |
| **Inflation (CPI)** | MoSPI / RBI | Non-NSE | 2025-02-28 | CPI Headline (3.6%, -1.5pp) and Core Inflation (3.8%, -0.2pp); RBI 4.0% (±2.0%) tolerance band overlay. | Monthly lag of ~12 days. |
| **Government Expenditure** | Union Budget (`indiabudget.gov.in`) | Non-NSE | 2025-03-31 | Total Expenditure (₹48.21L Cr) and Capital Expenditure (₹11.11L Cr); dual-axis bar & line chart + annual figures table (FY21–FY25 BE). | Sourced from official Union Budget *Budget at a Glance* (Statement 6). |

Every panel displays an authoritative `SourceFooter` with:
- Source name and reporting period (`As of`).
- `Non-NSE` tag for external government or multilateral feeds.
- `Estimate` indicator for Revised Estimates (RE) and Budget Estimates (BE).

---

## 📈 Live Market Ticker & Streaming Protocol

1. **Immediate Initial Snapshot**: On mount, the frontend queries `GET /api/ticker` to render instant prices without waiting for an SSE cycle.
2. **Single-Use Stream Ticket Handshake**: Browser requests a 30-second single-use ticket via `POST /api/auth/stream-ticket` and connects EventSource to `${origin}/api/stream/ticker?ticket=...`. Missing or expired tickets return HTTP 403 Forbidden.
3. **Monotonic Ring-Buffer Replay**: The server assigns sequential IDs to every tick and maintains a 50-event ring buffer. On reconnect with `Last-Event-ID`, missed events are replayed immediately.
4. **Heartbeats & Backoff**: Server sends 15-second heartbeat comments (`: ping\n\n`). Client reconnects with exponential backoff (1s–30s) and jitter.
5. **Polling Fallback**: If SSE fails after 3 consecutive attempts, client automatically falls back to periodic polling (`GET /api/ticker` every 10s) while continuing background SSE reconnection.
6. **Market Status**:
   - `LIVE`: During NSE trading hours (09:15–15:30 IST, Mon–Fri) with quotes fresh within 40 seconds.
   - `STALE`: Trading hours but quotes older than 40s or SSE disconnected > 60s.
   - `CLOSED`: Outside trading hours, weekends, or market holidays.

---

## 🛡️ Resilience & UI States

- **Loading Skeletons**: High-fidelity animated skeletons render during initial data fetching.
- **Stale-While-Revalidate**: Every 5 minutes, each panel independently refreshes its data (`fetchIndicatorThunk`). If a network failure occurs, the panel **retains its last valid observation**, displays a `STALE` badge, and never blanks out or impacts adjacent panels.
- **Missing Value Handling**: Missing or incomplete observations strictly render as `"—"` and never invent data or replace valid points.
- **Error States with Retry**: Failed panels without prior observations render an error card with a manual `Retry Data` button.
- **Empty States**: If a reporting period contains zero data points, an explicit empty state notice is displayed.

---

## 🔐 Security & Evaluation Access

- **JWT HS256 Authentication**: Secure in-memory token storage with automatic 60-minute session expiry.
- **Startup Guard**: In live mode, backend refuses to boot with insecure or default secrets unless `ALLOW_INSECURE_DEFAULTS=true` is set.
- **Rate Limiting**: Sensitive endpoints (e.g. `POST /api/auth/login`) are rate-limited to 5 requests/minute per client IP using `slowapi`.
- **Protected Endpoints**: All indicator and ticker endpoints require a valid Bearer token.
- **No Browser Upstream Credentials**: The frontend communicates exclusively with the FastAPI backend; zero external API keys or upstream credentials reside in client code.

### Panel Evaluation Credentials
- **Username**: `analyst@adityabirla.com`
- **Password**: `Analyst@2026`
- **Role**: `admin`

---

## ⚙️ Environment Variables

Configuration is driven via `.env` in the project root:

| Variable | Context | Default Value | Description |
| :--- | :--- | :--- | :--- |
| `DATA_MODE` | Backend | `live` | Operational mode: `live` connects to PostgreSQL and collectors. |
| `POSTGRES_USER` | Backend / DB | `postgres` | Database username. |
| `POSTGRES_PASSWORD` | Backend / DB | *(required in prod)* | Database user password. |
| `DATABASE_URL` | Backend | *(constructed)* | PostgreSQL connection string for psycopg3 async pool. |
| `JWT_SECRET` | Backend | *(required in prod)* | Secret key (min 32 chars) for signing HS256 tokens. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Backend | `60` | Token lifetime before session expiration. |
| `STREAM_TICKET_EXPIRE_SECONDS`| Backend | `30` | Single-use SSE ticket lifetime. |
| `EVAL_USERNAME` | Backend | `analyst@adityabirla.com` | Evaluation analyst username. |
| `EVAL_PASSWORD` | Backend | `Analyst@2026` | Evaluation analyst password hashed at boot. |
| `ALLOW_INSECURE_DEFAULTS` | Backend | `false` | Set to `true` strictly during local development. |
| `FRONTEND_ORIGIN` | Backend | `http://localhost:5173` | Allowed CORS origin. |
| `VITE_API_BASE_URL` | Frontend | `/api` | Base API route prefix. |

---

## 🚀 Running the Application

### Option 1: Docker Compose (Root 1-Command Startup)

```bash
# 1. Create .env from template
cp .env.example .env

# 2. Build and launch all containers (PostgreSQL + FastAPI + Caddy Web Server)
docker compose up -d --build

# 3. Verify deployment and network isolation
./backend/scripts/deploy_verify.sh
```

- **Frontend & Caddy Reverse Proxy**: [http://localhost](http://localhost) (or `http://<YOUR-EC2-PUBLIC-IP>`)
- **Backend API Direct**: [http://localhost:8000/api](http://localhost:8000/api)
- **System Health Check**: [http://localhost/health](http://localhost/health)
- **Interactive OpenAPI Docs**: [http://localhost/docs](http://localhost/docs)

---

## ☁️ AWS EC2 Deployment Guide

The application is completely containerized and verified to run on any AWS EC2 instance (Ubuntu 22.04 / 24.04 LTS or Amazon Linux 2023).

### Step 1: Launch EC2 Instance & Configure Security Group
- **Instance Type**: `t3.small` or `t3.medium` (minimum 2 GB RAM, 20 GB disk).
- **Inbound Security Group Rules**:
  - `HTTP` (Port 80) from `0.0.0.0/0` (Public web access).
  - `HTTPS` (Port 443) from `0.0.0.0/0` (SSL/TLS).
  - `SSH` (Port 22) from your IP.
  - *(Optional)* Custom TCP (Port 8000) if direct backend access without Caddy is desired.

### Step 2: SSH into your EC2 Instance
```bash
ssh -i your-key.pem ubuntu@<YOUR-EC2-PUBLIC-IP>
```

### Step 3: Install Docker and Docker Compose
```bash
# For Ubuntu:
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker
```

### Step 4: Clone Repository & Launch
```bash
git clone https://github.com/tejaspatare1885/Economics-Indicator.git
cd Economics-Indicator

# Copy environment configuration
cp .env.example .env

# Launch entire stack with 1 command
docker compose up -d --build
```

### Step 5: Access Dashboard
Open your browser and navigate to:
```text
http://<YOUR-EC2-PUBLIC-IP>
```
Log in using the evaluation analyst credentials:
- **Email**: `analyst@adityabirla.com`
- **Password**: `Analyst@2026`

---

### Option 2: Local Development

#### 1. Backend (FastAPI + PostgreSQL)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations and seed evaluation user
python scripts/migrate.py
python scripts/seed_user.py
python scripts/load_seeds.py

# Start live FastAPI server
DATA_MODE=live ALLOW_INSECURE_DEFAULTS=true uvicorn backend.app.main:app --port 8000 --reload
```

#### 2. Frontend (React 18 + Vite)
```bash
cd frontend
npm install

# Start Vite development server
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 System Health & Diagnostic Probes

```bash
# 1. Test live system health & scheduler statistics
curl -s http://localhost:8000/health | jq .

# 2. Execute upstream API reachability probe
./backend/.venv/bin/python backend/scripts/probe_sources.py

# 3. Production build check
cd frontend && npm run build
```

---

## 📝 Assumptions & Known Limitations

1. **NSE & BSE Market Hours**: Market data reflects trading hours (09:15–15:30 IST, Monday to Friday). Outside these hours, the terminal displays the last closing quotes and marks market status as `CLOSED`.
2. **Upstream Cloudflare / Anti-Scraping**: Public BSE endpoints occasionally enforce Cloudflare bot protection (HTTP 403). The collector seamlessly falls back to Yahoo Finance ticker data without service interruption.
3. **Macroeconomic Reporting Frequencies**: Macro indicators are reported on differing cadences (monthly for CPI and GST, quarterly for Trade Balance, and annually for GDP, Debt-to-GDP, and Budget Expenditure). Observation dates are explicitly documented in each panel's `SourceFooter`.
4. **Target Viewport**: The application is tailored to the evaluation resolution of **1214 × 2159 CSS pixels**, centered with zero unintended horizontal scroll and fully stable chart canvases.
