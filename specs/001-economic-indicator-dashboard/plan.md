# Implementation Plan: Economic Indicator Dashboard

**Branch**: `001-economic-indicator-dashboard` | **Date**: 2026-10-15 | **Spec**: [specs/001-economic-indicator-dashboard/spec.md](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/001-economic-indicator-dashboard/spec.md)

**Input**: Feature specification from [specs/001-economic-indicator-dashboard/spec.md](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/001-economic-indicator-dashboard/spec.md) and technical constraints specified in prompt.

---

## Summary

Deliver a pixel-perfect, high-performance macroeconomic indicator dashboard frontend reproducing `design/reference.png` at an authoritative 1214 x 2159 CSS pixel viewport. The application provides signed-in financial analysts with an immediate visual readout of India's macroeconomic figures across six analytical panels, a live market ticker, strict data provenance tracking, multiple state resilience modes (loading, stale, empty, error, unavailable), and in-memory JWT authentication. Built with React 18, Vite, TypeScript, tree-shaken Apache ECharts, CSS Modules with custom token variables, and a mock API abstraction layer swappable via a single environment variable change.

---

## Technical Context

**Language/Version**: TypeScript 5.x, React 18.x  
**Primary Dependencies**:
- Build & Runtime: Vite 5+, React 18, React Router DOM 6+
- Visualizations: Apache ECharts (`echarts/core`) with `echarts-for-react` (tree-shaken imports: BarChart, LineChart, Tooltip, Grid, Legend, MarkPoint)
- Fonts & Typography: Self-hosted metric-compatible `Selawik` (Segoe UI fallback), `@fontsource/manrope` (weights 600, 700)
- Styling: Plain CSS Modules with CSS custom properties injected from `src/styles/tokens.css` (mapped from `design/token.md` and `design/figma-export.css`)

**Storage**: In-memory React Context / closure for JWT access tokens and user session; deterministic static JSON fixtures in `src/mocks/` during mock mode.

**Testing**:
- Unit & Component: Vitest + React Testing Library (for components, state handling, and option builders)
- Visual Regression: Playwright full-page screenshot tests at 1214 x 2159 CSS px compared against `design/reference.png`
- Code Quality: ESLint + Prettier

**Target Platform**: Modern desktop browsers (Chromium, Firefox, WebKit) benchmarked at 1214 x 2159 CSS pixels.  
**Project Type**: Single-Page Frontend Application (SPA).  
**Performance Goals**:
- Initial render < 1.5 seconds under mock conditions
- 60 fps continuous scrolling on the live market ticker
- Ticker hover pause response latency < 50 milliseconds
- Chart hover tooltip display latency < 100 milliseconds
- Zero cumulative layout shift (CLS = 0) between loading skeletons and active charts

**Constraints**:
- Strict visual match with `design/reference.png` at 1214 CSS px width without horizontal scroll or clipped content
- Fixed panel dimensions: 582px width x 544px height; fixed chart canvas height of 310px
- Zero invented numbers: missing or unpopulated fields strictly format as em-dash (`"—"`)
- Frontend only: Swapping to real backend API requires only changing `VITE_API_BASE_URL` and `VITE_USE_MOCKS=false` in `.env`
- Isolated ticker execution: Ticker stream events must not cause parent re-renders or panel recalculations

**Scale/Scope**: 1 login view, 1 protected dashboard view, 6 analytical indicator panels, 1 real-time ticker bar, 1 mock API/stream layer.

---

## Constitution Check

| Principle / Gate | Status | Evaluation |
| :--- | :---: | :--- |
| **I. Self-Contained Components** | PASSED | Each panel is encapsulated in its own folder (`src/panels/[PanelName]/`) with isolated chart option builders, tests, and mock data. |
| **II. Clean Data Abstraction** | PASSED | Single typed API client (`src/api/client.ts`) with strict generic contracts (`IndicatorEnvelope`) decouples UI from backend implementation. |
| **III. Test-First Quality** | PASSED | Unit tests for panel states, data transforms, and auth lifecycle; Playwright visual regression tests enforce the 1214 x 2159 pixel benchmark. |
| **IV. Observability & Provenance** | PASSED | Explicit data source badges ("as of" dates and non-NSE tags) on every panel; clear visual representation of stale/error/loading states. |
| **V. Simplicity & Minimal Footprint** | PASSED | Tree-shaken ECharts bundle; no heavy state-management libraries (Redux/MobX); native CSS Modules over bloated runtime CSS-in-JS. |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-economic-indicator-dashboard/
├── plan.md              # This implementation plan
├── research.md          # Architectural decisions & library evaluations
├── data-model.md        # TypeScript interfaces, state machines, and entities
├── quickstart.md        # Setup, execution, and validation guide
├── contracts/           # API and SSE JSON schema definitions
│   ├── indicator-api.json
│   ├── ticker-stream.json
│   └── auth-api.json
└── checklists/
    └── requirements.md  # Specification quality checklist
```

### Source Code (repository root)

```text
public/
├── assets/              # Extracted 3D icons, flag SVGs, and candlestick backgrounds
└── fonts/               # Self-hosted Selawik font files

src/
├── api/
│   ├── client.ts        # Typed HTTP & mock client reading VITE_API_BASE_URL
│   └── types.ts         # Indicator, ticker, and auth TypeScript contracts
├── auth/
│   ├── AuthContext.tsx  # In-memory JWT storage, login, refresh timer, logout
│   ├── ProtectedRoute.tsx # Route guard redirecting unauthenticated users to /login
│   └── LoginPage.tsx    # Clean analyst sign-in view
├── components/
│   ├── Header/          # "ECONOMIC INDICATOR" title + candlestick backdrop
│   ├── Ticker/          # Continuous scrolling live ticker with hover pause
│   ├── PanelShell/      # Card container (582x544px), glassmorphic styling, states
│   ├── StatTile/        # KPI tile with delta pill and 3D graphic / flag icon
│   ├── SourceFooter/    # Provenance attribution and "as of" timestamp
│   ├── StatusBadge/     # Stale, Live, Unavailable status badges
│   └── Skeleton/        # Matching dark skeleton placeholder
├── hooks/
│   ├── useIndicatorData.ts # SWR-like data hook handling panel states
│   └── useTickerStream.ts  # SSE connection with reconnect backoff & polling fallback
├── mocks/
│   ├── gdpGrowth.json
│   ├── debtToGdp.json
│   ├── tradeBalance.json
│   ├── gstCollection.json
│   ├── inflation.json
│   ├── govtExpenditure.json
│   └── tickerFeed.json
├── panels/
│   ├── GdpGrowthPanel/  # Grouped bar chart (India vs World)
│   ├── DebtToGdpPanel/  # Area line chart with pill markers
│   ├── TradeBalancePanel/ # Grouped bars + Trade Balance green line
│   ├── GstCollectionPanel/ # Bar chart + yellow trendline
│   ├── InflationPanel/  # Line chart with highlighted badge
│   └── GovtExpenditurePanel/ # Stacked bar chart with segment & top total labels
├── styles/
│   ├── tokens.css       # CSS custom properties from design/token.md
│   └── global.css       # Base reset, font declarations, canvas styling
├── App.tsx              # React Router setup (/login, /dashboard)
└── main.tsx             # Application bootstrap & ECharts registration

tests/
├── components/          # Vitest + RTL tests for StatTile, Ticker, PanelShell
├── hooks/               # Tests for useIndicatorData and useTickerStream
└── visual/              # Playwright visual regression specs (1214x2159)
```

**Structure Decision**: A clean single-project SPA architecture organized by functional concerns (`components/`, `panels/`, `api/`, `auth/`, `mocks/`). Lazy loading is used across the six panel chart modules to minimize initial script evaluation time.

---

## Complexity Tracking

*No constitutional violations or unneeded architectural complexities detected.*
