# Feature Specification: Economic Indicator Dashboard

**Feature Branch**: `001-economic-indicator-dashboard`

**Created**: 2026-10-15

**Status**: Draft

**Input**: User description: "Build the Economic Indicator dashboard with a FastAPI backend and PostgreSQL database serving the React frontend. The design (design/reference.png) is the authority for layout, typography, colours, charts, cards and labels. Evaluation viewport is 1214 x 2159 CSS px; at that size the whole screen must be legible and stable with no horizontal scroll, clipped content or layout shift. The FastAPI backend serves live/mock macroeconomic data from World Bank, IMF, NSE, BSE, data.gov.in, and curated Union Budget seed CSVs via unified standardized indicator envelopes, backed by PostgreSQL (psycopg3 connection pooling with raw SQL) and protected by JWT authentication with live SSE market index streaming."

## Clarifications

### Session 2026-10-16
- Q: What is the backend scope and technology stack? → A: FastAPI backend with PostgreSQL database using psycopg3 with connection pooling and raw parameterized SQL. Single Uvicorn worker hosting scheduler and in-memory broadcaster in-process. Out of scope: ORM, Redis, multi-worker, user registration UI.
- Q: How are operational data modes structured? → A: DATA_MODE=mock|live. Mock mode serves fixtures/*.json matching frontend shapes without DB writes or upstream calls (used for tests/demos). Live mode connects to PostgreSQL and runs upstream data collectors. Both modes share identical routes and response envelopes.
- Q: What is the standard response envelope for indicator endpoints? → A: {indicator, tiles[{label,value,unit,change,change_unit}], series[{name,points[{period,value}]}], source{name,type: nse|external|external-curated,url}, as_of, fetched_at, status: ok|stale|unavailable}. Missing values are null; never invent numbers.
- Q: What is the calculation rule for stat tile changes? → A: Rate series (GDP, inflation, debt): change = latest - previous in percentage points (pp). Level series (exports, imports, GST, expenditure): change = YoY growth(latest) - YoY growth(previous) in pp. If unavailable, null.
- Q: What are the upstream sources and mappings for each macroeconomic panel? → A:
  - GDP Growth: World Bank NY.GDP.MKTP.KD.ZG for IN and WLD (2021-2025). Missing latest year is null; as_of reflects last available year.
  - Debt to GDP: IMF DataMapper GGXWDG_NGDP for IND and USA annual. Chart x-axis uses years (documented deviation from design dates). Tile "India (FY25)" = latest actual; "Ind vs US" = India minus US gap in pp.
  - Trade Balance: World Bank NE.EXP.GNFS.CD and NE.IMP.GNFS.CD in US$ B for exports/imports tiles. Bars = YoY growth %. Line = trade balance % of GDP (NE.RSB.GNFS.ZS), signed (axis extends below 0 when negative).
  - GST Tax Collection: Curated seed file (data/seed/gst_monthly.csv) labeled external-curated. Tile "GST Collections" = FY YoY growth %; "Monthly Average" = FY average gross collection in Rs lakh crore. Bars = YoY growth %; line = monthly average.
  - Inflation: World Bank FP.CPI.TOTL.ZG for India (2021-2025). RBI target = config constant 4.0 (policy constant, labeled so; change = null).
  - Government Expenditure: Seed CSV (data/seed/government_expenditure.csv) in Rs lakh crore. Total = total_expenditure; Capital = effective capex; Revenue = total - effective capex. X-axis shows fiscal year start (2021..2025 -> FY2021-22..FY2025-26); FY2025-26 is Revised Estimate. Points carry basis: actual|revised_estimate|budget_estimate. Tiles = YoY growth % of total and capex.
- Q: How are market index ticker quotes and market hours handled? → A: NIFTY BANK and NIFTY IT from NSE allIndices endpoint (source type: nse). SENSEX from BSE source (source type: external, labeled non-NSE). Payload: symbol, last, change, pct_change, as_of, source, market_status (open|closed|stale). Live stream via SSE using single-use 30-second ticket. Market hours: Mon-Fri 09:15-15:30 Asia/Kolkata (via zoneinfo). Market closed if holiday or upstream timestamp does not advance.
- Q: What security, auth, and freshness rules govern backend services? → A: JWT HS256 with 60-minute access token (no refresh token), Bearer header, bcrypt password hashing, roles: viewer|admin, seeded evaluation user from env vars. Login rate-limited to 5 requests/min/IP. Generic error messages. All /api/* protected except login. CORS restricted to deployed frontend origin. Data is marked stale when fetched_at exceeds 2x refresh interval or refresh failed (stale data retained and labeled).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Macroeconomic Indicator Visual Readout (Priority: P1)

As a financial analyst, I want to view a centralized macroeconomic dashboard matching the reference design layout at 1214 x 2159 CSS px so that I can immediately evaluate India's primary economic indicators without visual clutter, clipped data, or layout shifts.

**Why this priority**: Core value of the product. The primary dashboard layout and its six core analytical panels provide the immediate visual readout demanded by analysts.

**Independent Test**: Can be tested independently by loading the dashboard route in an authenticated state at 1214 x 2159 CSS px viewport and verifying that the header, ticker, and all six indicator panels render with the exact typography, card proportions, colors, data tiles, and charts matching `design/reference.png`.

**Acceptance Scenarios**:

1. **Given** an authenticated analyst navigating to the dashboard at 1214 x 2159 CSS px, **When** the page renders, **Then** the header displays "ECONOMIC INDICATOR" centered over a dark candlestick-chart graphic background, followed by the live ticker bar, followed by a 2-column by 3-row grid of six indicator panels without horizontal scrolling or clipped cards.
2. **Given** Panel 1 ("GDP Growth - India vs World (YOY%)"), **When** viewing the card, **Then** it presents two stat tiles (India: 4.82% with delta `-0.2pp`; World: 3.82% with delta `-0.81pp`) and a grouped bar chart spanning years 2021–2025 with India (blue) and World (orange), Y-axis ranging 0% to 10%, and numeric value labels rendered directly on the bars.
3. **Given** Panel 2 ("Debt to GDP Ratio (IND)"), **When** viewing the card, **Then** it presents two stat tiles (India FY25: 3.82% with delta `-0.81pp`; Ind vs US: 3.82% with delta `-0.81pp`) and an area/line chart spanning dates (25 Jul to 22 Aug), Y-axis ranging 50% to 100%, with pill-shaped value labels at selected inflection points.
4. **Given** Panel 3 ("Imports, Exports & Trade Balance"), **When** viewing the card, **Then** it presents two stat tiles (Exports: $382.9 B with delta `-0.81pp`; Imports: $382.9 B with delta `-0.81pp`) with graphic artwork, and a chart combining grouped bars (Imports blue, Exports orange) from 2021 to 2025 with an overlaid green Trade Balance line and circular value badges.
5. **Given** Panel 4 ("GST Tax Collection (YOY%)"), **When** viewing the card, **Then** it presents two stat tiles (GST Collections: 3.82% with delta `-0.81pp`; Monthly Average: 1.97 with delta `-0.81pp`), blue bars spanning 2021–2025, a yellow trendline with data points, and the legend matching the design.
6. **Given** Panel 5 ("Inflation (IND)"), **When** viewing the card, **Then** it presents two stat tiles (Inflation Rate: 2.1% with delta `-0.2pp`; RBI Target: 4% with delta `-0.2pp`) with 3D thematic artwork, and a line chart spanning 2021–2025 with Y-axis 0% to 10% and highlighted pill badges.
7. **Given** Panel 6 ("Government Expenditure"), **When** viewing the card, **Then** it presents two stat tiles (Total Expenditure: 4.82% with delta `-0.2pp`; Capital Expenditure: 3.82% with delta `-0.2pp`), and stacked bar charts from 2021 to 2025 depicting Revenue Expenditure (blue) and Capital Expenditure (orange) with segment values inside each bar and total values labeled above.

---

### User Story 2 - Real-Time Market Index Ticker (Priority: P2)

As an analyst monitoring real-time market movements, I want a continuously scrolling live ticker bar at the top of the dashboard that pauses on hover and receives background updates without full page reload.

**Why this priority**: Provides live market context (Sensex, Nifty Bank, Nifty IT) alongside static macro trends; live movement without reloading is critical for active trading and desk monitoring.

**Independent Test**: Can be tested independently by loading the ticker component with mock quote feeds, observing continuous smooth looping, verifying that positive quotes display in green and negative quotes in red, observing that hovering halts the animation, and asserting that new quote updates reflect in the stream without page flicker or reloads.

**Acceptance Scenarios**:

1. **Given** the ticker bar, **When** viewed on screen, **Then** it displays a prominent red "LIVE" badge with an indicator dot on the left, followed by a continuously scrolling horizontal stream of index quotes (e.g. SENSEX 73,158.24 (+0.42%), NIFTY BANK 46,919.80 (-0.12%), NIFTY IT 37,842.15 (+1.10%)).
2. **Given** index quote values, **When** change is positive (> 0), **Then** the quote and delta are displayed in green text; **When** change is negative (< 0), **Then** the quote and delta are displayed in red text.
3. **Given** the scrolling ticker, **When** the user moves the mouse cursor over the ticker area, **Then** the scrolling animation pauses immediately so the analyst can inspect quotes; **When** the mouse leaves, **Then** scrolling resumes smoothly.
4. **Given** new market index data arriving from the data service, **When** received, **Then** the quote values in the ticker update dynamically in place without resetting scroll position or reloading the page.

---

### User Story 3 - Interactive Chart Exploration & Series Toggling (Priority: P3)

As an analyst analyzing specific data trends, I want to hover over chart series to inspect exact underlying numbers in tooltips and click legend items to toggle series visibility on and off.

**Why this priority**: Enhances analytical depth by allowing granular inspection of specific data points and isolated comparison between conflicting series (e.g., viewing India alone vs World alone).

**Independent Test**: Can be tested independently by hovering across data points in each chart type (grouped bar, line, area, stacked bar) to confirm tooltip contents, and clicking legend swatches to verify series hide/show behavior.

**Acceptance Scenarios**:

1. **Given** any chart on the dashboard, **When** the user hovers over a bar, line point, or area segment, **Then** a contextual tooltip appears displaying the series name, time period, exact numerical value, and unit of measure.
2. **Given** any chart with a legend (such as India vs World or Revenue vs Capital Expenditure), **When** the user clicks on a legend item, **Then** the corresponding series toggles between hidden and visible, and the remaining visible series rescale or adjust gracefully.
3. **Given** a toggled-off series, **When** the analyst clicks the legend item a second time, **Then** the series becomes visible again and tooltips re-engage for that series.

---

### User Story 4 - Data Governance & State Resilience (Priority: P4)

As an analyst verifying data provenance, I want each indicator panel to clearly state its authoritative data source and "as of" date, and handle various data availability states (loading, empty, error, stale, unavailable) with missing data shown as "—" and never invented numbers.

**Why this priority**: Macro analysts require strict data integrity and compliance; misrepresenting missing data or obscuring data sources damages credibility and regulatory auditability.

**Independent Test**: Can be tested independently by injecting simulated response states (success, loading, empty dataset, network error, stale cached data, and unavailable) into individual panels and verifying that appropriate badges, skeleton screens, and fallback labels render accurately.

**Acceptance Scenarios**:

1. **Given** an active indicator panel, **When** rendered, **Then** it displays the authoritative source name (e.g., MoSPI, RBI, Ministry of Commerce) and "as of" date/period, explicitly identifying non-NSE sources as such.
2. **Given** a panel awaiting data from the service layer, **When** in a loading state, **Then** it renders a dark skeleton loader matching the dimensions of the header, stat tiles, and chart area without inducing layout shifts.
3. **Given** an indicator panel where data is unavailable or empty, **When** rendered, **Then** missing numerical figures are displayed strictly as "—" (em-dash), no fictional numbers are displayed, and an empty/unavailable state notice is presented.
4. **Given** a panel encountering a network or server retrieval failure, **When** an error occurs, **Then** the panel displays a clean error state message with an option to retry data retrieval.
5. **Given** cached data whose timestamp exceeds freshness thresholds, **When** rendered, **Then** the existing data remains visible but is prominently marked with a "Stale" indicator badge alongside its historical "as of" timestamp.

---

### User Story 5 - Analyst Authentication & Session Lifecycle (Priority: P5)

As an authorized analyst, I want to sign in through a secure authentication screen, access the protected dashboard, sign out when finished, and be automatically redirected to the sign-in page if my session expires.

**Why this priority**: Guarantees access control for proprietary macroeconomic analytics and prevents unauthorized dashboard access.

**Independent Test**: Can be tested independently by attempting to access the dashboard route while unauthenticated (expecting redirect), submitting valid analyst credentials to access the dashboard, triggering session timeout to observe automatic redirect, and manually signing out.

**Acceptance Scenarios**:

1. **Given** an unauthenticated user attempting to visit the dashboard route, **When** the route is loaded, **Then** the user is immediately redirected to the sign-in screen.
2. **Given** the sign-in screen, **When** the analyst submits valid credentials, **Then** an authenticated session is established and the user is redirected to the main dashboard.
3. **Given** an authenticated session, **When** the user clicks "Sign Out", **Then** the session is cleared, protected state is flushed, and the user is redirected to the sign-in screen.
4. **Given** an active dashboard session, **When** the session reaches expiration or invalidation, **Then** the system automatically terminates access and redirects the analyst to the sign-in screen with an explanatory session-expired prompt.

---

### Edge Cases

- **Network Interruption during Ticker Stream**: If the live ticker connection disconnects or fails to poll, the ticker displays a subtle offline/reconnecting indicator while retaining the last known quotes, and resumes automatic live updates once connectivity is restored.
- **Partial Panel Failure**: If one or two panels encounter API errors while others succeed, the successful panels render normally while only the failed panels display error cards, avoiding full-page crashes.
- **Null or Sparse Time-Series Points**: If a historical year or month has no reported indicator value, the chart renders a continuous baseline or dashed gap with a "—" tooltip label rather than zero or interpolated false data.
- **Viewport Dimension Variations**: While 1214 x 2159 CSS px is the authoritative evaluation resolution, slight browser chrome adjustments or mobile scaling must not trigger horizontal scroll bars or clipped typography.
- **Rapid Legend Toggling**: Rapid clicks on chart legends must not cause browser graphics memory leaks, erratic animation queuing, or inconsistent series visibility states.
- **Session Expiry During Ongoing User Interaction**: If a session expires while an analyst has a chart tooltip active, the redirect must cleanly unmount chart listeners and navigate smoothly to the sign-in screen without unhandled exceptions.

## Requirements *(mandatory)*

### Functional Requirements

#### Viewport & Layout Architecture
- **FR-001**: System MUST render the entire dashboard view within a 1214 x 2159 CSS pixel viewport without horizontal scrollbars, clipped text, overlapping elements, or unexpected layout shifts.
- **FR-002**: System MUST structure the page layout top-to-bottom into three distinct visual tiers: Header banner, Live Ticker Bar, and a 2-column by 3-row Indicator Grid containing six discrete analytical panels.
- **FR-003**: System MUST apply the authoritative visual styling from `design/reference.png` and `design/index.css`, including dark background theme, typography hierarchies, card borders, gradients, and color palettes.

#### Header & Brand Identity
- **FR-004**: System MUST render a full-width header featuring the title "ECONOMIC INDICATOR" in uppercase typography, superimposed over a dark graphical background depicting financial candlestick chart patterns.

#### Real-Time Index Ticker
- **FR-005**: System MUST provide a continuous horizontal scrolling ticker beneath the header displaying major financial indices including SENSEX, NIFTY BANK, and NIFTY IT with current points, absolute change, and percentage change.
- **FR-006**: System MUST anchor a red "LIVE" status badge containing an indicator circle to the left side of the ticker stream.
- **FR-007**: System MUST render positive index price movements and percentage deltas in green, and negative price movements and percentage deltas in red.
- **FR-008**: System MUST temporarily pause ticker scrolling animation when an analyst hovers a pointer over any part of the ticker bar, and resume scrolling smoothly when the pointer exits.
- **FR-009**: System MUST update ticker quotes dynamically in real time without triggering full or partial page refreshes.

#### Analytical Panels & Visualizations
- **FR-010**: System MUST render Panel 1 titled "GDP Growth - India vs World (YOY%)" containing:
  - Stat tile 1: India flag icon, "India" label, current value "4.82%", and percentage point delta `-0.2pp`.
  - Stat tile 2: World globe icon, "World" label, current value "3.82%", and percentage point delta `-0.81pp`.
  - Grouped bar chart comparing India (blue gradient) and World (orange gradient) across years 2021 to 2025 with Y-axis bounded from 0% to 10% and prominent numeric labels displayed directly on top of each bar.
- **FR-011**: System MUST render Panel 2 titled "Debt to GDP Ratio (IND)" containing:
  - Stat tile 1: India flag icon, "India (FY25)" label, current value "3.82%", and delta `-0.81pp`.
  - Stat tile 2: US flag icon, "Ind vs US" label, current value "3.82%", and delta `-0.81pp`.
  - Area/line chart tracking historical dates (spanning 25 Jul through 22 Aug) on the X-axis, with Y-axis scaled from 50% to 100%, cyan line with translucent fill, and pill-shaped value badges on highlighted data points.
- **FR-012**: System MUST render Panel 3 titled "Imports, Exports & Trade Balance" containing:
  - Stat tile 1: "Exports" label, "$382.9 B" metric, delta `-0.81pp`, and commercial coin artwork.
  - Stat tile 2: "Imports" label, "$382.9 B" metric, delta `-0.81pp`, and logistics container artwork.
  - Dual-axis or composite chart featuring grouped bars (Imports in blue, Exports in orange) for years 2021 to 2025, combined with an overlaid green line representing Trade Balance with circular value badges.
- **FR-013**: System MUST render Panel 4 titled "GST Tax Collection (YOY%)" containing:
  - Stat tile 1: "GST Collections" label, "3.82%" metric, delta `-0.81pp`, and invoice/currency graphic.
  - Stat tile 2: "Monthly Average" label, "1.97" metric, delta `-0.81pp`, and coin stack graphic.
  - Visualization featuring blue bars alongside a yellow trendline with data points across 2021 to 2025, with legend matching the design reference.
- **FR-014**: System MUST render Panel 5 titled "Inflation (IND)" containing:
  - Stat tile 1: "Inflation Rate" label, "2.1%" metric, delta `-0.2pp`, and monetary icon.
  - Stat tile 2: "RBI Target" label, "4%" metric, delta `-0.2pp`, and RBI target dartboard icon.
  - Line chart over the 2021 to 2025 timeframe, Y-axis scaled from 0% to 10%, highlighting inflection values with rounded badge overlays.
- **FR-015**: System MUST render Panel 6 titled "Government Expenditure" containing:
  - Stat tile 1: "Total Expenditure" label, "4.82%" metric, delta `-0.2pp`, and expenditure graph artwork.
  - Stat tile 2: "Capital Expenditure" label, "3.82%" metric, delta `-0.2pp`, and parliament architecture artwork.
  - Stacked bar chart spanning 2021 to 2025, dividing each annual bar into Revenue Expenditure (blue) and Capital Expenditure (orange), displaying segment value labels inside each block and the combined total expenditure labeled above each bar.

#### Interactive Chart Features
- **FR-016**: System MUST display an interactive hover tooltip over every chart data point or segment showing full period name, series label, and exact metric value.
- **FR-017**: System MUST allow users to click legend items to toggle the visibility of individual data series within multi-series charts.

#### Attribution, Provenance & Data States
- **FR-018**: System MUST display the authoritative data source and "as of" reporting timestamp on every indicator panel.
- **FR-019**: System MUST explicitly label all non-NSE data sources (e.g. Reserve Bank of India, Ministry of Statistics & Programme Implementation, Ministry of Finance) to distinguish them from exchange data feeds.
- **FR-020**: System MUST support and visually represent six distinct panel lifecycle states:
  1. *Loading*: Dark skeleton placeholders mirroring the dimensions of headers, stat boxes, and charts.
  2. *Active*: Fully populated data with current visual fidelity.
  3. *Empty*: Clean zero-data empty state graphic and notice.
  4. *Error*: Informative failure state with retry option.
  5. *Stale*: Retained historical data clearly overlaid or tagged with a "Stale" indicator badge.
  6. *Unavailable*: Indicator marked unavailable when upstream feeds are decommissioned or down.
- **FR-021**: System MUST render any missing, unpopulated, or null data metric strictly as an em-dash ("—") and MUST NEVER invent or extrapolate fictional figures.

#### Security, Authentication & Session
- **FR-022**: System MUST provide a dedicated analyst sign-in page with credential input fields and authentication action.
- **FR-023**: System MUST protect the dashboard route, denying access to unauthenticated sessions and redirecting unauthenticated requests directly to sign-in.
- **FR-024**: System MUST provide a clear sign-out capability that terminates the active analyst session and returns to the sign-in page.
- **FR-025**: System MUST monitor session validity and automatically redirect the analyst to the sign-in view upon session expiration.

#### API Contract & Backend Architecture
- **FR-026**: System MUST provide dual runtime operational modes controlled via `DATA_MODE=mock|live`. In `mock` mode, the backend MUST serve static JSON fixtures matching the frontend schema with zero database writes or external upstream requests. In `live` mode, the backend MUST query PostgreSQL and execute upstream data collector jobs.
- **FR-027**: System MUST serve every macroeconomic indicator endpoint (`/api/indicators/{id}`) using a standardized response envelope: `{indicator, tiles[{label,value,unit,change,change_unit}], series[{name,points[{period,value,basis?}]}], source{name,type,url}, as_of, fetched_at, status}`.
- **FR-028**: System MUST compute stat tile changes strictly as: (a) for rate series (GDP, inflation, debt), change = latest - previous in percentage points (`pp`); (b) for level series (exports, imports, GST, expenditure), change = YoY growth(latest) - YoY growth(previous) in `pp`. Missing or non-computable changes MUST be returned as `null`.
- **FR-029**: System MUST collect live and historical indicator data from authoritative upstreams:
  - GDP: World Bank `NY.GDP.MKTP.KD.ZG` for India and World (2021–2025). Missing values MUST be null; `as_of` MUST state the latest available year.
  - Debt to GDP: IMF DataMapper `GGXWDG_NGDP` for India and USA (annual data). The chart X-axis MUST display years (documented deviation from the design reference dates). Tile 1 MUST reflect the latest actual; Tile 2 MUST reflect India minus US gap in percentage points (`pp`).
  - Trade: World Bank `NE.EXP.GNFS.CD` and `NE.IMP.GNFS.CD` for export/import tiles in US$ B. Series bars represent YoY growth %; line represents signed trade balance % of GDP (`NE.RSB.GNFS.ZS`).
  - GST: Seed dataset (`data/seed/gst_monthly.csv`) labeled `external-curated`. Tile 1 reflects FY YoY growth %; Tile 2 reflects FY average monthly gross collection in Rs lakh crore.
  - Inflation: World Bank `FP.CPI.TOTL.ZG` for India (2021–2025). RBI Target tile MUST return policy constant `4.0` (labeled policy constant, change `null`).
  - Government Expenditure: Seed dataset (`data/seed/government_expenditure.csv`) in Rs lakh crore with total, effective capex, and revenue expenditure across fiscal years FY2021-22 through FY2025-26. Each point MUST include `basis` (`actual`, `revised_estimate`, `budget_estimate`).
- **FR-030**: System MUST stream live market index quotes (NIFTY BANK and NIFTY IT from NSE allIndices endpoint; SENSEX from BSE source labeled non-NSE) via Server-Sent Events (SSE). Each quote MUST provide `symbol`, `last`, `change`, `pct_change`, `as_of`, `source`, and `market_status` (`open`, `closed`, `stale`).
- **FR-031**: System MUST compute market open/closed status for Indian market hours: Monday through Friday, 09:15 to 15:30 Asia/Kolkata (via `zoneinfo`). If an upstream quote timestamp fails to advance during market hours (indicating a market holiday), the system MUST label the market as `closed`.
- **FR-032**: System MUST protect all `/api/*` endpoints (except `/api/auth/login`) using JWT HS256 tokens with 60-minute expiration. Passwords MUST be hashed using `bcrypt`. Roles MUST include `viewer` and `admin`. Evaluation user credentials MUST be seeded from environment variables.
- **FR-033**: System MUST enforce IP-based rate limiting on login attempts at a threshold of 5 requests per minute per IP address, returning generic failure messages upon authentication failure.
- **FR-034**: System MUST issue single-use, 30-second validity tickets for authorizing SSE ticker stream connections.
- **FR-035**: System MUST run under a single Uvicorn worker process hosting the in-process background scheduler and in-memory SSE broadcast manager. Database persistence MUST utilize `psycopg3` with connection pooling, parameterized SQL queries, and numbered `.sql` migration files.
- **FR-036**: System MUST mark an indicator's status as `stale` when `fetched_at` exceeds twice its expected refresh interval or when the most recent collector execution fails. Stale data MUST be retained in the database and served with `status: "stale"`, and MUST NEVER be overwritten with corrupt or invented data.

### Key Entities

- **Standard Indicator Envelope**: Unified JSON response structure for macro panels.
  - Attributes: `indicator` (slug), `tiles` (array of `StatTileMetric`), `series` (array of `TimeSeries`), `source` (`name`, `type`: `nse` | `external` | `external-curated`, `url`), `as_of` (date/year string), `fetched_at` (ISO timestamp), `status` (`ok` | `stale` | `unavailable`).
- **Stat Metric Tile**: Summary KPI tile inside an indicator panel.
  - Attributes: `label` (string), `value` (number | null), `unit` (string), `change` (number | null), `change_unit` (string, e.g. `pp`).
- **Time Series Point**: Chronological observation point in a chart series.
  - Attributes: `period` (year/date string), `value` (number | null), `basis` (`actual` | `revised_estimate` | `budget_estimate` | null).
- **Market Index Quote**: Exchange index quote for live ticker stream.
  - Attributes: `symbol`, `last`, `change`, `pct_change`, `as_of`, `source` (`nse` | `external`), `market_status` (`open` | `closed` | `stale`).
- **User Account & Session**: Authorized analyst account and JWT credential.
  - Attributes: `id`, `email`, `hashed_password`, `role` (`viewer` | `admin`), `created_at`.
- **Data Refresh Record**: Metadata tracking ingestion and freshness.
  - Attributes: `indicator_id`, `fetched_at`, `refresh_interval_seconds`, `last_status` (`ok` | `failed`), `error_message`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% visual alignment score when the dashboard view rendered at 1214 x 2159 CSS pixels is overlaid on `design/reference.png`, with zero horizontal scrollbars, zero clipped text elements, and zero unprompted layout shift (CLS = 0).
- **SC-002**: Initial dashboard visual presentation renders completely in under 1.5 seconds on broadband connections under standard mock API latency.
- **SC-003**: Continuous ticker scrolling animation maintains a smooth 60 frames-per-second visual cadence and halts scrolling within 50 milliseconds of pointer hover.
- **SC-004**: Interactive chart hover tooltips render and position within 100 milliseconds of user pointer movement over any chart data node.
- **SC-005**: 100% of the six required panel lifecycle states (loading skeleton, active, empty, error, stale, unavailable) can be individually triggered, observed, and validated in test demonstrations.
- **SC-006**: 100% of reported figures across all six panels display explicit data source attribution and "as of" reporting timestamps, with 0 instances of invented numbers or unformatted missing values (all null values render as "—").
- **SC-007**: Unauthenticated access attempts to protected dashboard views are blocked and redirected to the sign-in page 100% of the time, and expired sessions trigger automated redirection within 1 second of expiry detection.
- **SC-008**: Transitioning from mock API data to a live API endpoint requires modifying exactly 1 configuration variable (the API base URL) with zero frontend component alterations.

## Assumptions

- **Target Display Specifications**: The authoritative evaluation viewport is fixed at 1214 x 2159 CSS pixels (portrait orientation layout typical of digital display terminals and high-density analyst screens). Responsive fluid behavior may scale proportionally, but pixel perfection is judged against 1214 x 2159 CSS px.
- **Typography & Font Availability**: Fonts referenced in `design/index.css` (such as 'Manrope' and 'Segoe UI' or appropriate web-safe sans-serif fallbacks) will be loaded to match letterforms and weights.
- **Iconography and Illustrations**: The 3D illustrative icons in stat tiles (coins, ship, invoice, dartboard, building) and flags (India, US) are represented through high-fidelity visual assets or SVGs directly matching `design/reference.png`.
- **Legend Labels in Panel 4**: Panel 4 ("GST Tax Collection (YOY%)") reflects the visual legend design matching the reference image as requested by the user prompt ("blue bars plus a yellow line, legend as in the design").
- **Authentication Credentials**: For initial frontend development and analyst demonstration, a default analyst credential set (e.g., `analyst@adityabirla.com` / `Analyst@2026`) or simulated credential input is accepted by the mock authentication service.
- **Ticker Update Frequency**: Mock live ticker updates simulate push updates at a cadence of every 3 to 5 seconds to demonstrate live quote updates without page reload.
