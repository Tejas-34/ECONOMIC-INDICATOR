# Research & Architecture Decisions: Economic Indicator Dashboard

**Feature**: [001-economic-indicator-dashboard](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/001-economic-indicator-dashboard/spec.md)  
**Date**: 2026-10-15  
**Status**: Approved

This document consolidates architectural investigations, technology evaluations, and design decisions for implementing the frontend dashboard.

---

## 1. Styling Architecture & Design Tokens

### Decision
Use **CSS Modules** combined with **CSS Custom Properties (CSS Variables)** declared in `src/styles/tokens.css` based on `design/token.md` and `design/figma-export.css`.

### Rationale
1. **Pixel-Level Fidelity**: The Figma export contains explicit subpixel borders (`1.07px #415D88`), complex radial/linear gradients, exact backdrop filters (`blur(59.2px)`), and fine-tuned component coordinates. CSS Modules allow exact reproduction without fighting utility class abstraction limits.
2. **Encapsulation**: CSS Modules automatically scope class names to prevent collision between panels, stat tiles, and ticker elements.
3. **Token Management**: Centralizing colors (`--color-bg-panel`, `--color-accent-cyan`, `--color-delta-pos`, `--color-delta-neg`, etc.), typography sizes, and radii in `:root` allows consistent theming and straightforward audits against `design/token.md`.

### Alternatives Considered
- **Tailwind CSS**: Rejected because the majority of styles in the Figma export rely on custom gradients, arbitrary subpixel borders, and non-standard blur radii. Generating endless arbitrary utility strings (e.g. `bg-[linear-gradient(0deg,#061E44,#0FB8E6)]`) creates bloated, unreadable markup.
- **CSS-in-JS (Styled-Components / Emotion)**: Rejected due to runtime JavaScript style calculation overhead, larger client bundle, and potential SSR/Vite hydration complexity.

---

## 2. Charting Library & Tree-Shaking Strategy

### Decision
Use **Apache ECharts** (`echarts/core`) via `echarts-for-react`, employing tree-shaken imports and lazy loading panel charts via React `Suspense` / `React.lazy`.

### Registered Modules
```typescript
import * as echarts from 'echarts/core';
import { BarChart, LineChart } from 'echarts/charts';
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkPointComponent,
  GraphicComponent
} from 'echarts/components';
import { CanvasRenderer } from 'echarts/renderers';

echarts.use([
  BarChart,
  LineChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  MarkPointComponent,
  GraphicComponent,
  CanvasRenderer
]);
```

### Rationale
1. **Complex Chart Requirements**:
   - Panel 1 (GDP Growth): Grouped bars with vertical gradient fills (`#061E44` to `#0FB8E6` and `#FFB012` to `#844B08`) and top-anchored numeric labels.
   - Panel 2 (Debt to GDP): Smooth area gradient line chart with custom pill-shaped value labels at selected inflection points.
   - Panel 3 (Trade Balance): Combined grouped bars + overlaid green line with circular pill badges.
   - Panel 4 (GST): Bar chart combined with connected yellow line with point markers.
   - Panel 5 (Inflation): Area line chart with custom highlighted badges.
   - Panel 6 (Expenditure): Stacked bars with dual labels (individual segment values inside bars, total sum above each bar).
2. **Tree-Shaking**: Importing only required charts and components reduces ECharts bundle footprint by >60% compared to importing the full `echarts` bundle.
3. **Event Support**: Native support for hover tooltips, click events for legend toggles, and resize observers.
4. **Isolated Option Builders**: Each panel contains its own memoized option builder function (`buildGdpChartOption`, `buildDebtChartOption`, etc.) that cleanly separates data mapping from rendering.

### Alternatives Considered
- **Recharts**: Insufficient control over custom pill badges, complex stacked bar total annotations, and custom multi-stop canvas gradient definitions.
- **Chart.js**: Difficult to achieve exact stacked bar segment labels plus top totals simultaneously with fine-grained SVG/canvas filters.
- **D3.js directly**: High development overhead and boilerplate for tooltips, legend toggling, and canvas/SVG resizing.

---

## 3. Real-Time Ticker Architecture

### Decision
Implement a custom React hook `useTickerStream` utilizing **Server-Sent Events (SSE)** with automatic exponential backoff reconnection (1s, 2s, 4s, 8s, up to 15s max) and a silent **polling fallback** (`/api/ticker/latest` every 5 seconds) if SSE fails repeatedly.

### Component Isolation & Performance
- The ticker state is encapsulated within `src/components/Ticker/Ticker.tsx` or a dedicated context.
- Quote updates received via SSE/polling update internal ticker state without triggering re-renders in the parent dashboard layout or the six indicator panels.
- Continuous scrolling is powered by CSS hardware-accelerated animations (`transform: translate3d(...)`) with `animation-play-state: paused` on `:hover`.

### Alternatives Considered
- **WebSockets**: Overkill for a unidirectional market index quote broadcast; introduces stateful connection management on proxies and firewalls.
- **Pure Polling**: Fails to meet the "live updates arrive without page reload" latency expectation and causes unnecessary HTTP connection bursts.

---

## 4. API Client & Mock Layer Architecture

### Decision
Create a unified API client `src/api/client.ts` with an environment-based mock routing layer:
- `VITE_API_BASE_URL`: Defines the backend root endpoint.
- `VITE_USE_MOCKS=true`: Intercepts calls and serves static/dynamic JSON mocks from `src/mocks/`.

### Indicator Contract
All 6 indicator panel endpoints follow a uniform contract:
```typescript
export type SourceType = 'NSE' | 'external';
export type IndicatorStatus = 'ok' | 'stale' | 'unavailable';

export interface IndicatorResponse<TValues = Record<string, unknown>, TSeries = unknown> {
  id: string;
  title: string;
  subtitle?: string;
  source: string;
  source_type: SourceType;
  as_of: string;
  status: IndicatorStatus;
  values: TValues;
  series: TSeries;
}
```

### Swappability Guarantee
When switching from mock mode to a production backend, only `.env` needs updating:
```env
VITE_API_BASE_URL=https://api.macro-analytics.adityabirla.com
VITE_USE_MOCKS=false
```
Zero lines of application or component code need to be modified.

---

## 5. In-Memory Authentication & Session Management

### Decision
Store the JWT access token strictly in **memory** (within React state / closure in `src/auth/AuthContext.tsx`). Provide automatic token refreshing via a background timer scheduled ~60 seconds before token expiration (`exp` claim).

### Security & Lifecycle
- **No Secrets in Storage**: Access tokens are never stored in `localStorage` or `sessionStorage` to guard against XSS extraction.
- **Route Protection**: `<ProtectedRoute>` wrapper inspects authentication status; unauthenticated accesses are redirected to `/login` with the attempted destination preserved in state.
- **401 Interception**: When any API response returns HTTP 401 Unauthorized, the client triggers a refresh attempt; if the refresh fails or the session is invalid, user session state is reset and the user is redirected to `/login?session_expired=true`.
- **Demo Mode**: For development/mock evaluation, preset mock credentials (`analyst@adityabirla.com` / `Analyst@2026`) generate valid mock JWTs with simulated expiry controls.

---

## 6. Self-Hosted Typography & Assets

### Decision
- **Typography**:
  - `Segoe UI` stack: `'Segoe UI', Selawik, system-ui, -apple-system, sans-serif`.
  - Self-host **Selawik** (open-source, metric-compatible replacement created by Microsoft) via `public/fonts/`.
  - Load **Manrope** (weights 600, 700 for ticker symbols) via `@fontsource/manrope`.
- **Images & Icons**:
  - Extract frames and artwork from `design/frames/` and `design/reference.png`.
  - Store optimized SVGs and WebP assets in `src/assets/` / `public/assets/`.
  - Flag icons (India, US) and 3D finance graphics (coins, ships, invoices, dartboards, buildings) loaded as static image assets.

---

## 7. Layout Fidelity & Visual Regression Testing

### Decision
- **Fixed Canvas**: Sized at `1214px` width and minimum `2159px` height.
- **Grid Layout**: 2 columns x 3 rows with `582px` card width and `544px` card height, `24px` horizontal/vertical gap, and `30px` lateral padding.
- **Zero Cumulative Layout Shift (CLS)**: Fixed dimensions for panel cards (`582 x 544 px`) and fixed chart containers (`height: 310px`) ensure identical layout during loading skeletons and active data states.
- **Visual Regression**: Playwright automated test suite configured to capture full-page screenshots at `1214 x 2159` viewport and perform pixel diffing against `design/reference.png`.
