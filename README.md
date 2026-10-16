# Economic Indicator Dashboard

A full-stack macroeconomic terminal built to reproduce the Figma design specification at the evaluation viewport of 1214 x 2159 CSS pixels.

The dashboard provides real-time market index quotes and six macroeconomic indicator panels for India: GDP Growth, Debt-to-GDP Ratio, Trade Balance, GST Tax Collection, Inflation, and Government Expenditure.

---

## Architecture

The system consists of three containerized services communicating across isolated Docker bridge networks:

- Frontend: React 18 single-page application built with TypeScript, Redux Toolkit, Apache ECharts, CSS Modules, and Manrope typography.
- Backend: FastAPI asynchronous application in Python 3.11, using psycopg3 connection pooling with raw parameterized SQL queries, APScheduler for background tasks, and Server-Sent Events (SSE) for market feeds.
- Web Server and Proxy: Caddy 2 reverse proxy serving production static assets and proxying API endpoints with unbuffered streaming for SSE.
- Database: PostgreSQL 16 database strictly bound to an internal Docker network with no exposed host ports.

```
[ Browser Client (1214 x 2159 px) ]
         |
         | HTTP / HTTPS / SSE
         v
[ Caddy 2 Reverse Proxy (Port 80) ]
         |
         | proxy_net
         v
[ FastAPI Backend (Port 8000) ]
         |
         | internal_net (isolated)
         v
[ PostgreSQL 16 Database ]
```

---

## Indicator Panels and Data Sources

The dashboard displays six analytical panels and a live market ticker. Each indicator tracks official sources, reporting dates, and estimation statuses.

| Panel | Primary Source | Type | As of Date | Methodology and Scope |
| :--- | :--- | :---: | :---: | :--- |
| Live Market Ticker | NSE / BSE | Market | Real-time | SENSEX, NIFTY 50, and INR/USD live prices with positive/negative point changes and trading session status. |
| GDP Growth | IMF WEO / MoSPI | Non-NSE | 2024-12-31 | Real GDP annual growth rate for India (+7.0%) compared with World growth (+3.2%), with 2021-2025 historical data. |
| Debt to GDP Ratio | IMF DataMapper | Non-NSE | 2025-12-31 | General government gross debt as a percentage of GDP for India (84.3%) and comparison against the US (-40.1% gap), with 2021-2025 annual badges. |
| Trade Balance | Ministry of Commerce / RBI | Non-NSE | 2025-03-31 | Merchandise Exports ($437.1B) and Imports ($677.2B) alongside Trade Balance percentage-of-GDP trend line. |
| GST Tax Collection | data.gov.in / Ministry of Finance | Non-NSE | 2025-03-31 | Total GST collections (Rs 16.34L Cr) and monthly average (Rs 1.63L Cr) with domestic and import breakdowns for 2021-2025. |
| Inflation (CPI) | MoSPI / RBI | Non-NSE | 2025-02-28 | CPI Headline (3.6%) and Core Inflation (3.8%) with RBI medium-term target band (4.0% +/- 2.0%) overlay. |
| Government Expenditure | Union Budget (indiabudget.gov.in) | Non-NSE | 2025-03-31 | Total Expenditure (Rs 48.21L Cr) and Capital Expenditure (Rs 11.11L Cr) across FY21 to FY25 (Actuals, RE, BE). |

Every panel includes a SourceFooter displaying the source name, reporting date (as of), a Non-NSE identifier for external public data, and an Estimate marker for budget and revised projections.

---

## Live Ticker and Streaming Protocol

The market ticker streams live index prices through the following flow:

1. Initial Snapshot: On page load, the frontend requests GET /api/ticker to display prices immediately.
2. Single-Use Ticket: The client requests a 30-second ticket through POST /api/auth/stream-ticket and connects EventSource to /api/stream/ticker?ticket=...
3. Event Buffer and Replay: The backend assigns sequential IDs to each tick and keeps a 50-event ring buffer. Reconnecting clients pass Last-Event-ID to retrieve missed ticks without gap.
4. Heartbeats: The server transmits comment heartbeats (: ping) every 15 seconds to prevent intermediate proxy timeout.
5. Reconnection and Fallback: The client reconnects using exponential backoff with jitter. If SSE fails 3 times consecutively, it falls back to periodic polling (GET /api/ticker every 10 seconds).
6. Market Status: Quotes are tagged LIVE during NSE trading hours (09:15 to 15:30 IST, Monday to Friday), STALE when upstream quotes are delayed past 40 seconds, and CLOSED outside trading hours.

---

## Resilience and Interface States

The user interface handles network disruptions and missing data gracefully:

- Loading State: Animated skeletons display while initial queries resolve.
- Stale-While-Revalidate: Panels refresh independently on a 5-minute interval. If a background refresh fails, the panel retains its existing data and displays a STALE badge instead of blanking out.
- Missing Values: If an upstream provider omits a value, the terminal renders a dash (-) rather than fabricating numbers.
- Error State: If an initial fetch fails without cached data, an error notice with a manual retry button is displayed.
- Empty State: Explicit empty indicators render if a reporting period contains no observations.

---

## Security and Authentication

- Authentication Method: JSON Web Token (JWT) signed with HMAC SHA-256 (HS256).
- Token Lifetime: Access tokens expire after 60 minutes. Tokens are held in browser memory and cleared on session expiration.
- Rate Limiting: Sensitive endpoints such as POST /api/auth/login are limited to 5 requests per minute per IP address via slowapi.
- Database Security: The PostgreSQL database is attached solely to the private internal_net Docker bridge. Port 5432 has no host mapping and cannot be reached from the public internet.
- SQL Injection Protection: All database queries use parameterized SQL through psycopg3. No dynamic SQL concatenation is used.
- Browser Security: Client code contains zero external API credentials or upstream private keys.

### Evaluation Credentials

- Username: analyst@adityabirla.com
- Password: Analyst@2026
- Role: admin

---

## Configuration

Environment variables are defined in .env (template provided in .env.example):

| Variable | Context | Default Value | Description |
| :--- | :--- | :--- | :--- |
| DATA_MODE | Backend | live | Operational mode (live connects to PostgreSQL and collectors). |
| POSTGRES_USER | Database | postgres | PostgreSQL administrative username. |
| POSTGRES_PASSWORD | Database | postgres_secure_2026 | PostgreSQL administrative password. |
| POSTGRES_DB | Database | economic_indicators | Target database name. |
| DATABASE_URL | Backend | constructed | Full PostgreSQL connection string for psycopg3. |
| JWT_SECRET | Backend | 32+ character string | Secret key for signing and validating JWT tokens. |
| ACCESS_TOKEN_EXPIRE_MINUTES | Backend | 60 | Token validity period in minutes. |
| STREAM_TICKET_EXPIRE_SECONDS | Backend | 30 | Single-use SSE stream ticket expiration in seconds. |
| EVAL_USERNAME | Backend | analyst@adityabirla.com | Default evaluation analyst account. |
| EVAL_PASSWORD | Backend | Analyst@2026 | Default evaluation password. |
| ALLOW_INSECURE_DEFAULTS | Backend | true | Allows development startup with evaluation defaults. |
| FRONTEND_ORIGIN | Backend | * | Allowed CORS origin or wildcard for reverse proxy. |
| VITE_API_BASE_URL | Frontend | /api | Relative API prefix routed through reverse proxy. |

---

## Quickstart with Docker Compose

Prerequisites: Docker Engine 24+ and Docker Compose v2.

```bash
# 1. Clone the repository
git clone https://github.com/tejaspatare1885/Economics-Indicator.git
cd Economics-Indicator

# 2. Copy the environment configuration
cp .env.example .env

# 3. Build and start all services
docker compose up -d --build
```

Access Points:
- Dashboard: http://localhost
- Health Check: http://localhost/health
- Direct Backend API: http://localhost:8000/api
- Interactive API Documentation: http://localhost/docs

---

## AWS EC2 Deployment Guide

The application runs on any modern Linux EC2 instance (Ubuntu 22.04 LTS, Ubuntu 24.04 LTS, or Amazon Linux 2023).

### 1. Launch Instance and Configure Security Groups

- Recommended instance: t3.small or t3.medium (2 GB RAM minimum, 20 GB storage).
- Inbound security group rules:
  - Port 80 (HTTP): Allow from 0.0.0.0/0
  - Port 443 (HTTPS): Allow from 0.0.0.0/0
  - Port 22 (SSH): Allow from your IP address

### 2. Connect via SSH

```bash
ssh -i your-key.pem ubuntu@<YOUR-EC2-PUBLIC-IP>
```

### 3. Install Docker and Docker Compose

```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
newgrp docker
```

### 4. Deploy Application

```bash
git clone https://github.com/tejaspatare1885/Economics-Indicator.git
cd Economics-Indicator
cp .env.example .env
docker compose up -d --build
```

### 5. Access the Terminal

Open your browser and navigate to:
```text
http://<YOUR-EC2-PUBLIC-IP>
```

Log in using the evaluation credentials:
- Username: analyst@adityabirla.com
- Password: Analyst@2026

---

## Local Development

### Backend Setup

Prerequisites: Python 3.11+ and PostgreSQL 16.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run migrations and seed data
python scripts/migrate.py
python scripts/seed_user.py
python scripts/load_seeds.py

# Start server
DATA_MODE=live ALLOW_INSECURE_DEFAULTS=true uvicorn backend.app.main:app --port 8000 --reload
```

### Frontend Setup

Prerequisites: Node.js 20+ and npm.

```bash
cd frontend
npm install
npm run dev
```

The frontend development server starts at http://localhost:5173.

---

## Verification and Diagnostics

```bash
# 1. System health and scheduler status
curl -s http://localhost/health | jq .

# 2. Automated upstream reachability probe
docker compose exec backend python backend/scripts/probe_sources.py

# 3. Full deployment and isolation verification
./backend/scripts/deploy_verify.sh

# 4. Production frontend build test
cd frontend && npm run build
```

---

## Assumptions and Limitations

1. Market Hours: Market data reflects Indian stock market trading hours (09:15 to 15:30 IST, Monday through Friday). Outside trading hours, the terminal displays the most recent closing prices and sets the session status to CLOSED.
2. Upstream Bot Protection: Direct BSE query endpoints occasionally return HTTP 403 due to Cloudflare rate limits. When this occurs, the collector automatically falls back to secondary Yahoo Finance feeds without downtime.
3. Reporting Cadence: Macroeconomic indicators operate on disparate release cycles (CPI and GST monthly, Trade Balance quarterly, GDP and Budget Expenditure annually). Exact observation periods are noted on each panel.
4. Viewport Specification: Layout geometries are optimized for the evaluation resolution of 1214 x 2159 CSS pixels, centered with no horizontal scroll.
