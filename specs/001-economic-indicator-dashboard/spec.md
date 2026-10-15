# Feature Specification: Economic Indicator Dashboard

**Feature Branch**: `001-economic-indicator-dashboard`

**Created**: 2026-10-15

**Status**: Draft

**Input**: User description: "Build the frontend of an "Economic Indicator" dashboard that reproduces the attached design (design/reference.png) exactly. The design is the authority for layout, typography, colours, charts, cards and labels. Evaluation viewport is 1214 x 2159 CSS px; at that size the whole screen must be legible and stable with no horizontal scroll, clipped content or layout shift. Users: signed-in analysts who want a quick read of India's macro indicators. They sign in, see the dashboard, and see each figure with its source and "as of" date. Screen structure (top to bottom): 1. Title 'ECONOMIC INDICATOR' over a dark candlestick-chart background. 2. Live ticker bar: red 'LIVE' badge with a dot, then a continuously scrolling loop of index quotes, e.g. SENSEX 73,158.24 (+0.42%), NIFTY BANK 46,919.80 (-0.12%), NIFTY IT 37,842.15 (+1.10%). Positive changes green, negative red. 3. Six panels in a 2-column x 3-row grid, each with a header, two stat tiles, and a chart: a. GDP Growth - India vs World (YOY%): tiles India 4.82% and World 3.82% with change in pp; grouped bar chart 2021-2025, India (blue) vs World (orange), y-axis 0-10%, value labels on bars. b. Debt to GDP Ratio (IND): tiles India (FY25) 3.82% and Ind vs US 3.82%; area/line chart, y-axis 50-100%, x-axis dates (25 Jul ... 22 Aug), pill-shaped value labels on selected points. c. Imports, Exports & Trade Balance: tiles Exports $382.9 B and Imports $382.9 B; grouped bars (Imports blue, Exports orange) 2021-2025 plus a green Trade Balance line. d. GST Tax Collection (YOY%): tiles GST Collections 3.82% and Monthly Average 1.97; blue bars plus a yellow line, legend as in the design. e. Inflation (IND): tiles Inflation Rate 2.1% and RBI Target 4%; line chart 2021-2025, y-axis 0-10%. f. Government Expenditure: tiles Total Expenditure 4.82% and Capital Expenditure 3.82%; stacked bars 2021-2025, Revenue Expenditure (blue) and Capital Expenditure (orange) with segment and total labels. Behaviour: Every chart has hover tooltips; legend items toggle series on and off; the ticker pauses on hover. Each panel shows its data source and 'as of' date (non-NSE sources identified as such). Each panel has loading (skeleton), empty, error, stale (data kept but labelled stale) and unavailable states. Missing values render as '—'. Never invent numbers. Sign-in page, protected dashboard route, sign-out, and automatic redirect to sign-in when the session expires. Ticker updates arrive without page reload (live updates). Scope: frontend only. Data comes from a mock API layer that matches the future real API shape; swapping to the real API must only need a base-URL environment variable change. Acceptance: overlaying the screen on design/reference.png at 1214 px wide shows no visible misalignment in spacing, font size, colours or chart proportions; all states above are demonstrable."

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

#### API Contract & Modularity
- **FR-026**: System MUST supply a mock data abstraction layer whose schema, parameter signatures, and response payloads exactly mirror the target production API specification.
- **FR-027**: System MUST allow switching from mock data to live backend API services exclusively through an environment configuration change (base URL) without requiring frontend codebase modifications.

### Key Entities

- **Market Index Quote**: Represents real-time exchange quotes displayed in the live ticker stream.
  - Attributes: Symbol name (e.g., SENSEX), current price/index points, absolute change value, percentage change value, price change direction (positive, negative, unchanged), last update timestamp.
- **Indicator Panel**: Represents an analytical macro card within the dashboard grid.
  - Attributes: Panel ID, panel title, panel subtitle/unit qualifier (e.g., YOY%), category, primary data source name, source classification (NSE vs non-NSE), "as of" reporting timestamp, current lifecycle state (loading, active, empty, error, stale, unavailable).
- **Stat Metric Tile**: Represents a high-level summary KPI tile displayed at the top of an indicator panel.
  - Attributes: Metric label, current primary value string, value unit (e.g. %, $B), delta change value, delta change unit (e.g. pp), delta direction (up/positive, down/negative), associated icon or 3D artwork identifier.
- **Indicator Time-Series**: Represents historical or categorical data series feeding chart components.
  - Attributes: Series identifier, series display label, theme color gradient, time series points (array of period strings, numerical values, formatted display labels, segment breakdown if stacked).
- **Analyst Session**: Represents an authenticated user's access context.
  - Attributes: Analyst identifier/email, authentication token/session token, session creation time, session expiration timestamp, authentication status (authenticated, unauthenticated, expired).

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
