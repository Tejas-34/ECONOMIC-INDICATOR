# Implementation Tasks: Economic Indicator Dashboard

**Feature**: [001-economic-indicator-dashboard](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/001-economic-indicator-dashboard/spec.md)  
**Date**: 2026-10-15  
**Status**: Completed  
**Plan**: [plan.md](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/001-economic-indicator-dashboard/plan.md)

---

## Phase 1: Setup & Tooling Infrastructure

**Purpose**: Project initialization, tooling configuration, design tokens, and self-hosted fonts.

- [X] T001 Initialize React 18, Vite, TypeScript, ESLint, Prettier, and Vitest configuration in `package.json`, `vite.config.ts`, and `tsconfig.json`. Done when: `npm run build` and `npm test` execute cleanly with zero errors.
- [X] T002 [P] Configure design tokens and CSS custom properties extracted from `design/token.md` and `design/figma-export.css` in `src/styles/tokens.css`. Done when: all color, typography, gradient, border, and radius tokens are defined in `:root` and importable without syntax errors.
- [X] T003 [P] Configure global CSS reset and self-hosted typography (Selawik font files and `@fontsource/manrope`) in `src/styles/global.css` and `public/fonts/`. Done when: fonts load locally and the root layout eliminates default browser margins and horizontal overflow.

---

## Phase 2: Foundational Prerequisites

**Purpose**: Core data layer, mock JSON fixtures, app shell, and shared reusable component primitives.

**⚠️ CRITICAL**: Foundational tasks must be completed before implementing specific user stories.

- [X] T004 [P] Define complete TypeScript interfaces for indicators, stat tiles, ticker quotes, and user sessions in `src/api/types.ts`. Done when: all types compile with strict TypeScript checks enabled.
- [X] T005 [P] Create deterministic mock JSON fixtures for all six panels and the ticker feed in `src/mocks/gdpGrowth.json`, `src/mocks/debtToGdp.json`, `src/mocks/tradeBalance.json`, `src/mocks/gstCollection.json`, `src/mocks/inflation.json`, `src/mocks/govtExpenditure.json`, and `src/mocks/tickerFeed.json`. Done when: all fixtures validate against `specs/001-economic-indicator-dashboard/contracts/indicator-api.json`.
- [X] T006 Implement unified API client reading `VITE_API_BASE_URL` with mock interception toggle (`VITE_USE_MOCKS`) in `src/api/client.ts`. Done when: unit tests verify successful data fetching in both mock mode and simulated HTTP mode.
- [X] T007 Implement indicator data retrieval hook with caching and state management in `src/hooks/useIndicatorData.ts`. Done when: unit tests verify loading, success, and error states.
- [X] T008 Scaffold fixed-canvas App shell layout sized at 1214 px width with candlestick header graphic in `src/components/Header/Header.tsx`, `src/components/Header/Header.module.css`, and `src/App.tsx`. Done when: rendering at 1214 px width produces zero horizontal scroll (`document.documentElement.scrollWidth === 1214`).
- [X] T009 [P] Implement reusable `PanelShell` container (fixed 582px x 544px) with glassmorphism card styling in `src/components/PanelShell/PanelShell.tsx` and `src/components/PanelShell/PanelShell.module.css`. Done when: component renders with exact 582x544 px dimensions and card border highlight.
- [X] T010 [P] Implement reusable `StatTile` component (KPI value, unit, percentage point delta badge with green/red directional indicators, artwork slot) in `src/components/StatTile/StatTile.tsx` and `src/components/StatTile/StatTile.module.css`. Done when: unit tests confirm green styling for positive changes, red for negative changes, and "—" fallback for null values.
- [X] T011 [P] Implement `SourceFooter` (source name, non-NSE distinction, "as of" timestamp) and `StatusBadge` (stale, live, unavailable) in `src/components/SourceFooter/SourceFooter.tsx` and `src/components/StatusBadge/StatusBadge.tsx`. Done when: unit tests confirm proper badge labels and source attribution.
- [X] T012 [P] Implement `PanelSkeleton` placeholder component matching panel header, stat tiles, and chart dimensions in `src/components/Skeleton/PanelSkeleton.tsx` and `src/components/Skeleton/PanelSkeleton.module.css`. Done when: dark skeleton matches 582x544 px dimensions with smooth pulse animation.

**Checkpoint**: Core foundation and design primitives are ready. User story implementations can proceed.

---

## Phase 3: User Story 1 - Macroeconomic Indicator Visual Readout (Priority: P1) 🎯 MVP

**Goal**: Deliver the 6 analytical panels in a 2x3 grid with pixel-matched ECharts visualizations, stat tiles, and exact layout.

**Independent Test**: Load the dashboard view at 1214 x 2159 CSS px; verify all 6 panels render with exact charts, stat tiles, value labels, and zero layout shift.

- [X] T013 [US1] Initialize tree-shaken Apache ECharts registry with BarChart, LineChart, Grid, Tooltip, Legend, and CanvasRenderer in `src/panels/echartsSetup.ts`. Done when: ECharts initializes without loading unneeded chart packages.
- [X] T014 [US1] Implement Panel 1 (GDP Growth - India vs World) with stat tiles, grouped vertical gradient bars (2021-2025, 0-10% y-axis), and bar-top numeric labels in `src/panels/GdpGrowthPanel/GdpGrowthPanel.tsx`, `src/panels/GdpGrowthPanel/chartOption.ts`, and `src/panels/GdpGrowthPanel/GdpGrowthPanel.module.css`. Done when: visual output matches `design/frames/Frame 2087327363.png` and component tests pass.
- [X] T015 [US1] Implement Panel 2 (Debt to GDP Ratio IND) with stat tiles, cyan area/line chart (25 Jul - 22 Aug, 50-100% y-axis), and pill-shaped inflection labels in `src/panels/DebtToGdpPanel/DebtToGdpPanel.tsx`, `src/panels/DebtToGdpPanel/chartOption.ts`, and `src/panels/DebtToGdpPanel/DebtToGdpPanel.module.css`. Done when: visual output matches `design/frames/Frame 2087327378.png` and component tests pass.
- [X] T016 [US1] Implement Panel 3 (Imports, Exports & Trade Balance) with stat tiles, grouped bars (Imports blue, Exports orange), and Trade Balance green trendline in `src/panels/TradeBalancePanel/TradeBalancePanel.tsx`, `src/panels/TradeBalancePanel/chartOption.ts`, and `src/panels/TradeBalancePanel/TradeBalancePanel.module.css`. Done when: visual output matches `design/frames/Frame 2087327381.png` and component tests pass.
- [X] T017 [US1] Implement Panel 4 (GST Tax Collection YOY%) with stat tiles, blue bars, yellow trendline with nodes, and design-matching legend in `src/panels/GstCollectionPanel/GstCollectionPanel.tsx`, `src/panels/GstCollectionPanel/chartOption.ts`, and `src/panels/GstCollectionPanel/GstCollectionPanel.module.css`. Done when: visual output matches `design/frames/Frame 2087327382.png` and component tests pass.
- [X] T018 [US1] Implement Panel 5 (Inflation IND) with stat tiles, line chart (2021-2025, 0-10% y-axis), and highlighted pill badges in `src/panels/InflationPanel/InflationPanel.tsx`, `src/panels/InflationPanel/chartOption.ts`, and `src/panels/InflationPanel/InflationPanel.module.css`. Done when: visual output matches `design/frames/Frame 2087327383.png` and component tests pass.
- [X] T019 [US1] Implement Panel 6 (Government Expenditure) with stat tiles, stacked bars (Revenue blue, Capital orange), segment labels inside bars, and total labels above in `src/panels/GovtExpenditurePanel/GovtExpenditurePanel.tsx`, `src/panels/GovtExpenditurePanel/chartOption.ts`, and `src/panels/GovtExpenditurePanel/GovtExpenditurePanel.module.css`. Done when: visual output matches `design/frames/Frame 2087327407.png` and component tests pass.
- [X] T020 [US1] Assemble the six panels into the 2-column by 3-row grid layout with 24px gap and 30px lateral padding in `src/panels/DashboardGrid.tsx` and `src/panels/DashboardGrid.module.css`. Done when: all six panels render within the grid with exact dimensions and zero layout shift.

**Checkpoint**: MVP visual readout is complete. All 6 panels render with high fidelity.

---

## Phase 4: User Story 2 - Real-Time Market Index Ticker (Priority: P2)

**Goal**: Deliver a continuous live scrolling ticker with pause-on-hover, SSE connectivity, and polling fallback.

**Independent Test**: Load the ticker bar, observe continuous smooth scrolling, verify hover pause, and confirm quote updates arrive without page reload.

- [X] T021 [US2] Implement live ticker component with red "LIVE" badge, hardware-accelerated marquee scrolling, and green/red price deltas in `src/components/Ticker/Ticker.tsx` and `src/components/Ticker/Ticker.module.css`. Done when: ticker scrolls continuously at 60fps and pauses within 50ms of hover.
- [X] T022 [US2] Implement `useTickerStream` custom hook supporting Server-Sent Events (SSE) with exponential reconnect backoff and 5-second polling fallback in `src/hooks/useTickerStream.ts`. Done when: hook unit tests verify SSE message handling, reconnect backoff logic, and automatic fallback to `/api/ticker/latest`.
- [X] T023 [US2] Connect `useTickerStream` to `Ticker.tsx`, isolating ticker state updates so they do not trigger parent dashboard or panel re-renders in `src/components/Ticker/Ticker.tsx`. Done when: live quote updates re-render only the ticker component.

**Checkpoint**: Real-time ticker is fully operational and isolated from dashboard panels.

---

## Phase 5: User Story 3 - Interactive Chart Exploration & Series Toggling (Priority: P3)

**Goal**: Provide rich chart hover tooltips and interactive legend toggles to show/hide series.

**Independent Test**: Hover over data nodes on each chart to verify tooltip contents; click legend items to verify series toggling.

- [X] T024 [P] [US3] Implement custom HTML hover tooltips showing series name, period, and formatted values for all six panel chart options in `src/panels/*/chartOption.ts`. Done when: tooltips appear on hover with dark styling and exact values in <100ms.
- [X] T025 [US3] Implement interactive legend series toggle handlers enabling users to click legend items to toggle series visibility in `src/components/PanelShell/PanelLegend.tsx` and `src/panels/*/*.tsx`. Done when: clicking a legend item toggles series visibility and remaining series adjust gracefully.

**Checkpoint**: Charts support granular interactive inspection and series toggling.

---

## Phase 6: User Story 4 - Data Governance & State Resilience (Priority: P4)

**Goal**: Handle loading, empty, error, stale, and unavailable lifecycle states with strict non-invention formatting ("—").

**Independent Test**: Inject simulated states into panels; verify skeleton loader, empty notice, error banner with retry, and stale badge render properly without inventing numbers.

- [X] T026 [US4] Implement loading skeleton transition in `src/components/PanelShell/PanelShell.tsx` and `src/panels/*/*.tsx`. Done when: loading state renders `PanelSkeleton` without causing layout shifts.
- [X] T027 [P] [US4] Implement empty and unavailable state views in `src/components/PanelShell/PanelShell.tsx`, ensuring all missing or null values strictly render as em-dash ("—") in `src/components/StatTile/StatTile.tsx`. Done when: empty datasets display informative empty/unavailable notices and never display false zeros.
- [X] T028 [P] [US4] Implement error and stale state views with retry action and visible "STALE" badge in `src/components/PanelShell/PanelShell.tsx`. Done when: error state displays a retry button that triggers re-fetch, and stale state retains cached data with a prominent badge.

**Checkpoint**: All six lifecycle states are fully demonstrable and resilient across all panels.

---

## Phase 7: User Story 5 - Analyst Authentication & Session Lifecycle (Priority: P5)

**Goal**: Secure dashboard access with in-memory JWT authentication, login route, route guard, and auto-redirect on session expiry.

**Independent Test**: Attempt unauthenticated access (expect redirect), log in with demo credentials, simulate session expiration, and verify redirection to `/login?session_expired=true`.

- [X] T029 [US5] Implement in-memory JWT authentication provider with background refresh timer in `src/auth/AuthContext.tsx`. Done when: auth unit tests verify login, in-memory token retention (no storage leaks), refresh scheduling, and logout.
- [X] T030 [P] [US5] Implement analyst login view with email/password validation and error messaging in `src/auth/LoginPage.tsx` and `src/auth/LoginPage.module.css`. Done when: form validates credentials, triggers login, and navigates to the dashboard.
- [X] T031 [US5] Implement `<ProtectedRoute>` route guard and HTTP 401 response interceptor in `src/auth/ProtectedRoute.tsx` and `src/api/client.ts`. Done when: unauthenticated routes redirect to `/login` and expired tokens trigger automatic redirection to `/login?session_expired=true`.

**Checkpoint**: Authentication and session security are fully established.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Visual overlay validation, performance optimization, accessibility, and documentation.

- [X] T032 [P] Perform visual fidelity tuning on typography, spacing, gradient stops, borders, and chart pill badges to match `design/reference.png` at 1214 x 2159 CSS px in `src/styles/tokens.css` and panel stylesheets. Done when: visual inspection shows zero visible misalignment.
- [X] T033 [P] Implement automated Playwright screenshot visual regression test at 1214 x 2159 CSS px comparing against `design/reference.png` in `tests/visual/dashboard.spec.ts` and `playwright.config.ts`. Done when: screenshot test passes within threshold.
- [X] T034 [P] Implement code-splitting for panel chart options, memoization, and bundle size optimization in `vite.config.ts` and `src/App.tsx`. Done when: each panel is lazy-loaded and the initial JavaScript bundle remains lightweight.
- [X] T035 [P] Create comprehensive frontend documentation in `README.md` covering environment variables (`VITE_API_BASE_URL`, `VITE_USE_MOCKS`), local development instructions, mock vs real API switching, and Figma design ambiguity resolutions. Done when: README provides clear, end-to-end guidance for setup and verification.
