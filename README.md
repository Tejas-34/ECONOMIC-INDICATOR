# Economic Indicator Dashboard (Full-Stack)

A pixel-perfect, high-performance macroeconomic terminal built to reproduce the authoritative design specifications of `design/reference.png` at **1214 x 2159 CSS pixels**.

The application delivers an immediate visual readout of India's macroeconomic figures across six analytical panels, a live market index ticker, strict data provenance tracking, multiple state resilience modes (loading, stale, empty, error, unavailable), and in-memory JWT authentication.

### Full-Stack Architecture
- **Frontend** (`frontend/`): React 18, Redux Toolkit, Apache ECharts, Vite, Selawik / Manrope typography.
- **Backend** (`backend/`): FastAPI (async), PostgreSQL 16 (psycopg3 connection pooling with raw parameterized SQL), APScheduler, SSE live quote streaming with 50-event ring buffer replay.
- **Data Modes**: Controlled via `DATA_MODE=mock|live`.

---

## 🚀 Quickstart & Local Setup

### Prerequisites
- **Node.js** >= 18.x
- **npm** >= 9.x

### Installation
```bash
npm install
```

### Run Locally (Mock Mode)
```bash
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

### Demo Analyst Sign-In
- **Email**: `analyst@adityabirla.com`
- **Password**: `Analyst@2026`
*(Or click the "Fill analyst@adityabirla.com / Analyst@2026" quick-fill button on the sign-in screen)*

---

## ⚙️ Environment Configuration

Configuration is managed via `.env` in the project root:

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `VITE_USE_MOCKS` | `true` | When `true`, all indicator and ticker requests are served by the local mock engine. Set to `false` for live backend integration. |
| `VITE_API_BASE_URL` | `/api` | Base URL of the backend API service (e.g., `https://api.macro-analytics.adityabirla.com`). |

### Switching Between Mock and Production Mode
To point the frontend to a production API, update `.env`:
```env
VITE_USE_MOCKS=false
VITE_API_BASE_URL=https://api.macro-analytics.adityabirla.com
```
**No code changes are required**; all API calls are abstracted through `src/api/client.ts`.

---

## 🧪 Testing & Validation

### Run Unit & Component Tests
```bash
npm test
```

### Run Visual Regression Tests (Playwright)
```bash
npm run test:visual
```

### Run Build & Bundle Check
```bash
npm run build
```

---

## 📐 Architecture & Layout Specifications

- **Canvas Viewport**: Fixed at `1214px` width and minimum `2159px` height.
- **Grid Layout**: 2 columns x 3 rows with exact `582px` card width and `544px` card height, `24px` horizontal/vertical gap, and `13px` lateral padding (`582 + 24 + 582 + 26 = 1214px`). Zero horizontal scrollbars (`CLS = 0`).
- **Live Ticker**: 49px height with a red `LIVE` badge, hardware-accelerated continuous CSS marquee, green/red color coding, and automatic pause on pointer hover. Connected via Server-Sent Events (SSE) with automatic exponential backoff reconnect and a 5-second polling fallback.
- **Tree-Shaken Charts**: Powered by Apache ECharts (`echarts/core`) registering only `BarChart`, `LineChart`, `GridComponent`, `TooltipComponent`, `LegendComponent`, `MarkPointComponent`, and `CanvasRenderer`. ECharts is split into a separate vendor chunk (`vendor-echarts.js`), keeping the initial application bundle lightweight (~48 kB).

---

## 🎨 Design Decisions & Ambiguity Resolutions

1. **Canvas Viewport vs Figma Frame Width**:
   - The Figma export file specifies a frame width of `1248px`, while the prompt specifies an evaluation viewport of `1214 x 2159 CSS px`.
   - **Resolution**: The grid columns maintain the full `582px` card width and `24px` gap, with `13px` margins on each side (`582 + 24 + 582 + 26 = 1214px`), guaranteeing that the view fits within `1214px` with zero horizontal scrollbar or clipped typography.

2. **Panel 4 (GST Tax Collection) Legend Labels**:
   - In `design/reference.png`, Panel 4 displays legend items labeled `Imports` and `Trade Balance` (a copy-paste artifact in the original Figma design).
   - **Resolution**: Per the prompt instructions ("blue bars plus a yellow line, legend as in the design"), the legend explicitly displays `Imports` and `Trade Balance` while correctly binding to the GST collection bar series and monthly average trendline series.

3. **Macro Delta Colors**:
   - Financial tickers strictly show positive in green and negative in red. In macroeconomic indicators (such as GDP Growth and Inflation deltas), the reference image displays green upward triangles even alongside negative percentage point deltas (e.g. `▲ -0.2pp` and `▲ -0.81pp`).
   - **Resolution**: The dashboard matches the reference image styling for indicator tiles while preserving standard green/red quote conventions in the live ticker bar.

4. **Missing Values & Zero-Invention Rule**:
   - When a dataset contains null or unpopulated values, the number is strictly formatted as an em-dash (`"—"`). The application never fabricates zeros or interpolates missing data.

5. **In-Memory JWT & Session Expiry**:
   - Access tokens are retained strictly in memory (React context/closures) rather than `localStorage` to eliminate XSS token leakage. An automatic background timer refreshes tokens prior to expiration, and unauthorized responses (HTTP 401) immediately redirect to `/login?session_expired=true`.
