# Feature Specification: End-to-End Live Dashboard Integration

**Feature Branch**: `002-live-data-integration`

**Created**: 2026-10-16

**Status**: Draft

**Input**: User description: "Integrate the existing React frontend and FastAPI backend so the dashboard runs end-to-end on live data (DATA_MODE=live, VITE_USE_MOCKS=false): login, six indicator panels, live ticker via SSE, stale/error states, secure by default. Mock mode must keep working for tests and demos. No visual redesign."

## Clarifications

### Session 2026-10-16
- Q: What defines the public contract between frontend and backend, and how is drift prevented? → A: The frontend `IndicatorResponse` shape in `frontend/src/api/types.ts` is the public contract. Backend live mode emits exactly that: `values` keyed by tile name, panel-specific `series` rows, `source` as a string, `source_type` (`NSE`|`external`), `as_of`, `status`, plus `formattedValue`, `formattedDelta`, `deltaDirection` on stat tiles. Canonical indicator slugs are `gdp-growth`, `debt-to-gdp`, `trade-balance`, `gst-collection`, `inflation`, `govt-expenditure` (old aliases kept undocumented). Single source of truth is Pydantic response models -> OpenAPI -> generated TypeScript types (`openapi-typescript`); CI fails on schema drift.
- Q: How are per-panel shapes, unit conversions, metric semantics, and estimate markings structured? → A: Per-panel shapes match `frontend/src/api/types.ts` (tile keys: `india`/`world`, `indiaFy25`/`indVsUs`, `exports`/`imports`, `collections`/`monthlyAverage`, `inflationRate`/`rbiTarget`, `totalExpenditure`/`capitalExpenditure`). Backend performs unit conversions (US$ to $B, Rs crore to lakh crore), YoY growth for bar series, and display string formatting. Metric semantics (D3–D9) are preserved. Government expenditure series points carry `basis` and an `estimate` boolean; UI visually marks estimated points.
- Q: What are the authentication, session lifecycle, and authorization rules? → A: Every `/api/*` endpoint except `POST /api/auth/login` and `/health` requires a valid Bearer token. SSE connection requires a mandatory single-use ticket. Any HTTP 401 response invokes a single global handler: clears client token and redirects to `/login?session_expired=true`. No refresh tokens; sessions use a 60-minute access token. A client-side timer triggers logout upon token expiry with a session-expired notice. Roles are `viewer` | `admin` (aligned with frontend types). The hardcoded password bypass is removed; runtime user seeding hashes `EVAL_PASSWORD` from environment variables without plaintext passwords or hashes in repository code. The demo quick-fill button is restricted to development builds (`import.meta.env.DEV`).
- Q: How does the market index ticker protocol, event streaming, and reconnection work? → A: On mount, client fetches `GET /api/ticker` snapshot, requests a ticket via `POST /api/auth/stream-ticket`, and connects to `EventSource /api/stream/ticker?ticket=...` with a fresh ticket per (re)connection. Server broadcasts a named `"snapshot"` event per ingestion cycle containing all quotes (monotonic ID, retry hint, 15-second heartbeat comment, and `Last-Event-ID` ring-buffer replay). Client replaces quote list on each snapshot event. Reconnection uses exponential backoff (1s to 30s with jitter). After 3 consecutive SSE failures, client initiates concurrent 10-second polling to `/api/ticker` while SSE retries in the background. All polling and streaming terminate on logout or unmount.
- Q: What are the criteria for computing ticker market status and the LIVE badge? → A: `market_status` is evaluated dynamically at read time: `open` and fresh = `LIVE`; `closed` = `CLOSED`; no updates for >2x ingestion interval or SSE down for >60s = `STALE`. Tooltip shows last update timestamp on hover.
- Q: How is the background scheduler configured, executed, and monitored? → A: On backend startup (following migrations and seeding), the scheduler performs a non-blocking initial ticker ingestion and runs macro collection if the `observations` table is empty. Replaces overlapping ticker jobs with a single unified job running every 20 seconds during market hours (09:15–15:30 IST, Mon–Fri) and every 10 minutes off-hours. `/health` endpoint exposes the last execution timestamp and elapsed age per scheduled job.
- Q: How is frontend configuration, mock data bundling, and base URL normalization handled? → A: Live data mode is default (`VITE_USE_MOCKS=false`). Mock mode activates only when `VITE_USE_MOCKS=true`, loading mock fixtures via dynamic `import()` to ensure mocks are tree-shaken and excluded from production bundles. A persistent "MOCK DATA" ribbon displays when mock mode is active. `VITE_API_BASE_URL` accepts either origin or origin + `/api` and is normalized client-side. Development uses the Vite proxy; SSE connects directly to the API origin to bypass buffering proxies.
- Q: What resilience, caching, and timeout mechanisms govern dashboard data loading? → A: Initial dashboard load uses `GET /api/dashboard` with ETag/304 conditional validation, distributing payloads to individual panels. Panels refresh every 5 minutes. On refetch failure, client retains last valid data and marks panel stale (stale-while-revalidate). All GET requests enforce a 10-second timeout via `AbortController` and execute up to 2 retries with exponential backoff before failing. Failures remain strictly isolated so one failing panel never blanks others.
- Q: What security safeguards and startup validation guard secrets and network access? → A: `JWT_SECRET`, database password, and `EVAL_PASSWORD` are loaded exclusively from environment variables (`.env.example`, docker-compose env file). In live data mode, backend startup fails fast if default or insecure secret values are detected, unless explicitly overridden via `ALLOW_INSECURE_DEFAULTS=true` for local development. Rate limiting extracts and keys on real client IP addresses from proxy forwarding headers (`X-Forwarded-For`).
- Q: What architectural and functional elements are explicitly out of scope? → A: Visual redesign, new panels, refresh token implementation, and multi-worker Uvicorn processes are strictly out of scope.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Macroeconomic Indicator Live Visual Readout (Priority: P1)

As an authenticated macroeconomic analyst (`viewer` or `admin`), I want to log into the economic indicator dashboard and view real-time data across all six macroeconomic indicator panels populated from live operational services so that I can analyze national financial trends and make timely advisory decisions based on authoritative statistics.

**Why this priority**: The primary business purpose of the dashboard is delivering macroeconomic indicators to authenticated analysts from authoritative sources. Without end-to-end authenticated data delivery and visual rendering of the six core indicators, the dashboard delivers no business value.

**Independent Test**: Can be fully tested by providing analyst credentials at the login prompt, confirming authentication, and verifying that the initial dashboard render (`GET /api/dashboard` with ETag/304 distribution) populates all six indicator panels (GDP Growth, Debt to GDP, Trade Balance, GST Collections, Inflation, and Government Expenditure) with live values, stat tiles, and multi-year trend charts with authentic source attribution.

**Acceptance Scenarios**:

1. **Given** an unauthenticated analyst on the application root, **When** they submit valid analyst credentials on the login screen, **Then** the system establishes a secure authenticated session with a 60-minute access token, stores authorization in client memory, and redirects to the full dashboard view.
2. **Given** an active authenticated session in live data mode, **When** the dashboard renders, **Then** the initial render executes `GET /api/dashboard` with ETag/304 support and distributes data to all six panels displaying their respective KPI stat tiles (with values, units, changes, and direction indicators), time-series charts, authoritative source names, and data as-of periods matching live backend observations.
3. **Given** an active authenticated session approaching 60 minutes, **When** the 60-minute token timer expires, **Then** the client automatically terminates the session, clears the token from memory, and redirects to `/login?session_expired=true` displaying a session expired notice.
4. **Given** an active authenticated session, **When** the analyst activates the sign-out action, **Then** the session is immediately invalidated, authorization tokens are purged from memory, and the user is redirected to the login interface.

---

### User Story 2 - Real-Time Market Index Ticker Streaming & Auto-Recovery (Priority: P2)

As a financial analyst monitoring market conditions, I want the market index ticker to stream real-time price quotes, point deltas, and percentage changes for key indices (NIFTY BANK, NIFTY IT, and SENSEX) continuously via push updates so that I receive up-to-the-minute market movements without manual screen refreshing.

**Why this priority**: Continuous streaming market context provides immediate operational feedback on market open/closed status and ongoing financial volatility, complementing the slower-moving macroeconomic indicator panels.

**Independent Test**: Can be fully tested by observing the header ticker over several minutes, confirming incoming live quote updates via named `"snapshot"` SSE events, disconnecting the network link to observe automatic reconnect attempts with fresh single-use tickets, `Last-Event-ID` replay, and verifying concurrent fallback to polling if push streaming is disrupted.

**Acceptance Scenarios**:

1. **Given** an authenticated dashboard view in live data mode, **When** the ticker mounts, **Then** it fetches an initial quote snapshot via `GET /api/ticker`, requests a single-use ticket via `POST /api/auth/stream-ticket`, and connects directly to the API origin at `EventSource /api/stream/ticker?ticket=...` bypassing buffering proxies.
2. **Given** an active live stream, **When** the backend ingestion cycle broadcasts a named `"snapshot"` event with monotonic ID and retry hint, **Then** the client replaces its quote list and renders updated quotes with dynamic `LIVE`, `CLOSED`, or `STALE` status badges with hover tooltips showing last update timestamps.
3. **Given** an active real-time ticker stream, **When** network connectivity drops, **Then** the client automatically reconnects with exponential backoff (1s to 30s with jitter), requesting a fresh single-use ticket and providing `Last-Event-ID` for ring-buffer replay.
4. **Given** 3 consecutive SSE reconnection failures, **When** push streaming remains disconnected, **Then** the ticker initiates concurrent 10-second polling to `GET /api/ticker` while continuing background SSE reconnect attempts until push connectivity is restored.

---

### User Story 3 - Freshness Transparency, Degradation & Isolated Error Handling (Priority: P3)

As an analyst viewing indicators during upstream data delay or intermittent network interruption, I want explicit visual indication of data freshness (stale indicators) and isolated panel-level error recovery so that I never mistake outdated data for current data and can retry failed panels without disrupting the rest of the dashboard.

**Why this priority**: Statistical agencies and financial exchanges occasionally experience delays, maintenance windows, or rate caps. Ensuring that data freshness is transparent and failures do not crash the entire application protects analyst trust and ensures uninterrupted operational visibility.

**Independent Test**: Can be fully tested by simulating an upstream data source timeout or stale indicator status: verify that the affected panel renders last known values labeled with a visible "Stale" indicator and fetch timestamp; simulate a network failure on one indicator endpoint: verify that only that panel renders an error card with a working "Retry" button while the other five panels remain intact and interactive.

**Acceptance Scenarios**:

1. **Given** an indicator whose source data has exceeded established refresh intervals (>2x the refresh interval), **When** the panel is displayed, **Then** it presents the latest available historical observations accompanied by an explicit stale status label and the timestamp of the last successful data fetch.
2. **Given** panels executing their 5-minute periodic refresh, **When** a refetch request encounters a network or server error after 2 retries with backoff and a 10-second `AbortController` timeout, **Then** the affected panel retains its last known good data and marks itself stale (stale-while-revalidate), leaving all other five panels unaffected.
3. **Given** a panel currently displaying an error state, **When** the analyst activates the "Retry" action, **Then** only that specific panel refetches its data (`GET /api/indicators/{id}`) and transitions back to its standard visual presentation upon success.

---

### User Story 4 - Seamless Dual-Mode Operation (Mock vs Live) (Priority: P4)

As an automated quality assurance engineer or product presenter, I want the system to operate seamlessly in either live data mode or standalone mock mode via configuration toggles so that end-to-end automated tests and offline demonstrations can run reliably without external service dependencies.

**Why this priority**: Decoupling the presentation layer from external data dependencies via a deterministic mock mode guarantees repeatable testing in CI/CD pipelines, rapid UI verification, and risk-free client presentations in air-gapped or network-restricted environments.

**Independent Test**: Can be fully tested by running automated end-to-end test suites with mock mode enabled to verify zero network or database dependencies, then toggling to live mode to verify full live database and upstream collector connectivity with identical visual layout and component behavior.

**Acceptance Scenarios**:

1. **Given** the application configured with default settings (`VITE_USE_MOCKS=false`), **When** an analyst signs in, **Then** the application authenticates against the live user registry, fetches live indicators from the backend service, and opens the live index push stream.
2. **Given** the application configured with mock mode enabled (`VITE_USE_MOCKS=true`), **When** a user accesses the dashboard, **Then** mock datasets are dynamically imported (excluded from production builds) and a persistent "MOCK DATA" ribbon is displayed across the interface.
3. **Given** either operational mode, **When** the dashboard is evaluated at the reference resolution of 1214 x 2159 pixels, **Then** the visual presentation, typography, color palette, and layout proportions remain visually identical with zero layout shifts or horizontal scrollbars.

---

### Edge Cases

- **Session Expiry & Global 401 Handler**: When an analyst's session authorization expires during active dashboard viewing or any request returns HTTP 401, a global client handler immediately clears the token from client memory and redirects to `/login?session_expired=true` displaying a prominent session-expired notice.
- **Off-Market Hours & Holidays**: When the live ticker runs outside exchange trading hours (09:15–15:30 IST, Mon–Fri), the background scheduler adjusts ingestion frequency to every 10 minutes, the ticker computes `market_status: closed`, and the badge renders `CLOSED` with the last closing quotes.
- **Missing or Partial Upstream Data Points**: When an authoritative agency has not published a specific observation, the panel renders missing values as explicit placeholder indicators (`—`) and marks the as-of period as the last reported date, strictly avoiding artificial number generation or chart distortion.
- **Government Expenditure Estimate Marking**: When government expenditure series points contain revised or budget estimates (`basis: revised_estimate | budget_estimate`), the data carries `estimate: true` and the chart UI visibly marks these points as estimates.
- **Rapid Authentication Attempts & Reverse Proxy IP**: When a client submits more than 5 failed login attempts in a one-minute window, the system enforces a rate-limit cooldown keyed on the real client IP extracted from proxy headers (`X-Forwarded-For`).
- **Startup Guard with Insecure Secrets**: In live mode, backend startup strictly halts if default or insecure secrets (`JWT_SECRET`, database password, `EVAL_PASSWORD`) are detected, unless explicitly overridden via `ALLOW_INSECURE_DEFAULTS=true` for local development.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide authenticated access control requiring valid analyst credentials before granting access to the macroeconomic dashboard, with all `/api/*` routes requiring Bearer authentication except `POST /api/auth/login` and `GET /health`.
- **FR-002**: System MUST store session authentication tokens exclusively in client memory, preventing exposure of access tokens to unencrypted browser persistent storage.
- **FR-003**: System MUST enforce a 60-minute access token lifespan without refresh tokens, using a client-side timer to log the user out upon token expiry and redirecting to `/login?session_expired=true`.
- **FR-004**: System MUST install a global HTTP 401 interceptor that clears client tokens and redirects to `/login?session_expired=true`.
- **FR-005**: System MUST support distinct analyst user roles: `viewer` and `admin`, aligned across backend Pydantic schemas and frontend TypeScript types.
- **FR-006**: System MUST hash `EVAL_PASSWORD` from environment variables at runtime during database seeding, with no hardcoded passwords, hashes, or bypass shortcuts committed in repository code.
- **FR-007**: System MUST restrict demo quick-fill credentials buttons strictly to development builds (`import.meta.env.DEV`), excluding them from production artifacts.
- **FR-008**: System MUST treat `frontend/src/api/types.ts` (`IndicatorResponse`) as the public data contract, with backend live mode emitting matching shapes: `values` keyed by tile name, panel-specific `series` rows, `source` as a string, `source_type` (`NSE` | `external`), `as_of`, `status`, and tile metrics containing `formattedValue`, `formattedDelta`, and `deltaDirection`.
- **FR-009**: System MUST enforce canonical indicator slugs: `gdp-growth`, `debt-to-gdp`, `trade-balance`, `gst-collection`, `inflation`, and `govt-expenditure` (retaining legacy aliases for backward compatibility without documenting them).
- **FR-010**: System MUST establish Pydantic response models as the single source of truth, generating OpenAPI schemas and frontend TypeScript types via `openapi-typescript` with automated CI verification failing on schema drift.
- **FR-011**: System MUST perform all unit conversions (US$ to $B, Rs crore to lakh crore), YoY growth rate calculations for bar series, and display string formatting on the backend before delivery to the frontend.
- **FR-012**: System MUST tag Government Expenditure series observations with reporting `basis` and an `estimate` boolean flag, and the UI MUST visually mark estimated points.
- **FR-013**: System MUST execute initial dashboard rendering via `GET /api/dashboard` utilizing ETag/304 conditional caching and distribute payloads to individual panels.
- **FR-014**: System MUST refresh indicator panels every 5 minutes, retaining last known valid data and marking the panel stale if a refresh fails (stale-while-revalidate).
- **FR-015**: System MUST enforce a 10-second timeout on all GET requests via `AbortController` and execute up to 2 retries with exponential backoff before reporting a retrieval failure.
- **FR-016**: System MUST isolate retrieval errors to the specific failing panel, ensuring that an error in one panel does not impair, blank, or crash the remaining panels.
- **FR-017**: System MUST provide a dedicated "Retry" action within any panel experiencing an error to allow manual re-fetching of that panel's data via `GET /api/indicators/{id}`.
- **FR-018**: System MUST initialize the header ticker on mount by fetching a baseline snapshot via `GET /api/ticker`, then acquiring a mandatory single-use ticket via `POST /api/auth/stream-ticket`, and establishing an `EventSource` connection to `/api/stream/ticker?ticket=...`.
- **FR-019**: System MUST broadcast a named `"snapshot"` SSE event per ingestion cycle containing all quotes, formatted with a monotonic event ID, a client retry hint, 15-second heartbeat comments, and event ring-buffer replay via `Last-Event-ID`.
- **FR-020**: System MUST replace the client quote list upon each received `"snapshot"` event.
- **FR-021**: System MUST reconnect interrupted SSE streams using exponential backoff (1s to 30s with random jitter), requesting a fresh single-use ticket on each reconnect attempt.
- **FR-022**: System MUST initiate concurrent snapshot polling to `GET /api/ticker` every 10 seconds after 3 consecutive SSE reconnection failures, while continuing SSE reconnection attempts in the background until push streaming recovers.
- **FR-023**: System MUST terminate all ticker streaming and polling connections immediately upon user logout or component unmount.
- **FR-024**: System MUST compute `market_status` dynamically at read time: `open` and fresh = `LIVE`, `closed` = `CLOSED`, and no update for >2x ingestion interval or SSE down for >60s = `STALE`, displaying the exact last update timestamp in a hover tooltip.
- **FR-025**: System MUST run an automated background scheduler that performs initial ticker ingestion and non-blocking macro observation collection on startup if data tables are empty, and executes ticker ingestion every 20 seconds during market hours (09:15–15:30 IST, Mon–Fri) and every 10 minutes off-hours.
- **FR-026**: System MUST report execution timestamps and elapsed age per scheduled job via the `/health` endpoint.
- **FR-027**: System MUST configure live data mode as the default (`VITE_USE_MOCKS=false`), activating mock mode only when `VITE_USE_MOCKS=true`.
- **FR-028**: System MUST load mock data fixtures using dynamic `import()`, ensuring all mock files are tree-shaken and excluded from production builds.
- **FR-029**: System MUST display a visible "MOCK DATA" ribbon across the user interface whenever mock mode is enabled.
- **FR-030**: System MUST normalize `VITE_API_BASE_URL` client-side to accept either base origin or origin with `/api` path, using the Vite proxy in development while connecting SSE directly to the API origin to bypass proxy buffering.
- **FR-031**: System MUST refuse backend startup in live mode if default or insecure secrets (`JWT_SECRET`, database password, `EVAL_PASSWORD`) are present, unless `ALLOW_INSECURE_DEFAULTS=true` is explicitly set for local development.
- **FR-032**: System MUST extract real client IP addresses from reverse proxy headers (`X-Forwarded-For`) for authentication rate limiting (5 requests/minute).
- **FR-033**: System MUST preserve all existing visual styling, color palettes, typography, and card dimensions at the reference 1214 x 2159 viewport without visual redesign, horizontal scrollbars, or layout shifts.

### Out of Scope

- Visual redesign or modification of established layout, color schemes, or typography.
- Creation of new indicator panels beyond the six specified panels.
- Refresh token rotation or refresh endpoint implementation.
- Multi-worker Uvicorn clustering or distributed horizontal process scheduling.

### Key Entities

- **Analyst Session**: Authenticated user session containing user ID, username, email, assigned role (`viewer` | `admin`), session expiration timestamp, and in-memory 60-minute JWT Bearer token.
- **Standard Indicator Envelope (`IndicatorResponse`)**: Standardized data structure containing `id` (canonical slug), `title`, `subtitle`, `source` (string), `source_type` (`NSE` | `external`), `as_of`, `status` (`ok` | `stale` | `unavailable`), `values` (dictionary of named `StatTileMetric` objects), and `series` (panel-specific array of observation points).
- **Stat Tile Metric**: Individual KPI metric tile containing `label`, `value`, `formattedValue`, `unit`, `delta`, `formattedDelta`, `deltaUnit`, `deltaDirection` (`positive` | `negative` | `neutral`), `sublabel`, and `iconKey`.
- **Market Index Quote Snapshot**: Structured quote payload emitted under the named event `"snapshot"`, containing an array of `MarketIndexQuote` objects (`symbol`, `last`, `change`, `pct_change`, `as_of`, `source`, `market_status`), monotonic event ID, and server retry hint.
- **Stream Authorization Ticket**: Short-lived, single-use authorization token required for establishing an authenticated SSE connection, validated and invalidated immediately upon connection opening.
- **Scheduled Job Health Record**: Status entry tracking job name, last execution start, last execution completion, success status, and elapsed age in seconds.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Analysts can authenticate and view the complete dashboard with all six indicator panels loaded via `GET /api/dashboard` in under 3.0 seconds on standard broadband connections.
- **SC-002**: Live market index quotes reflect price updates on the dashboard display within 2.0 seconds of ingestion during active market hours (20-second ingestion cycle).
- **SC-003**: The live ticker push stream recovers and resumes data flow within 5.0 seconds of network restoration following an intermittent connectivity drop without requiring manual page reload.
- **SC-004**: 100% of expired sessions or unauthorized requests trigger the global 401 handler, clearing client tokens and redirecting to `/login?session_expired=true` within 500ms.
- **SC-005**: In the event of an upstream or network error on any single panel refresh, 100% of remaining panels continue to display and function without visual degradation, while the affected panel retains last good data with stale-while-revalidate labeling.
- **SC-006**: Automated test suites and offline product demonstrations execute to 100% completion in mock mode with zero external network or database dependencies, and mock data fixtures are 100% excluded from production bundles.
- **SC-007**: 0% layout shift, horizontal scrollbar emergence, or card clipping occurs at the reference viewport resolution of 1214 x 2159 pixels across both mock and live modes.
- **SC-008**: 100% of unauthenticated requests to protected `/api/*` routes are rejected with HTTP 401 Bearer challenges, and 100% of insecure live mode startups without custom secrets are blocked.

## Assumptions

- Analysts access the dashboard using modern evergreen workstation browsers supporting standard Server-Sent Events, modern asynchronous networking, and responsive CSS Grid.
- The reference evaluation viewport is 1214 x 2159 CSS pixels, representing high-resolution vertical analyst monitoring displays.
- In live data mode, the backend database service and upstream connectivity to statistical agencies (World Bank, IMF, NSE, BSE) are provisioned and operational.
- When statistical agencies publish data on annual or quarterly schedules, the most recently published reporting period is treated as the current authoritative baseline.
- Default evaluation credentials for testing and demonstration are provisioned in the application environment configuration via `EVAL_PASSWORD`.
