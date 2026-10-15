# Quickstart & Validation Guide: Economic Indicator Dashboard

**Feature**: [001-economic-indicator-dashboard](file:///Users/tejaspatare/Documents/AdityaBirla/Economics-Indicator/specs/001-economic-indicator-dashboard/spec.md)  
**Date**: 2026-10-15  
**Status**: Ready for Implementation

This guide provides setup instructions and runnable validation steps to verify the dashboard functionality, visual fidelity, real-time ticker, and authentication states.

---

## 1. Prerequisites & Environment Setup

### Required Tools
- Node.js >= 18.x
- npm >= 9.x or pnpm >= 8.x

### Environment Configuration
Create a `.env` file in the project root:

```env
# Mock Mode (default for local development & visual evaluation)
VITE_USE_MOCKS=true
VITE_API_BASE_URL=/api

# For production integration:
# VITE_USE_MOCKS=false
# VITE_API_BASE_URL=https://api.macro-analytics.adityabirla.com
```

### Installation
```bash
npm install
```

---

## 2. Local Development & Demo Execution

Start the Vite development server:
```bash
npm run dev
```

Navigate to `http://localhost:5173`.

### Demo Analyst Credentials
When prompted at the sign-in screen:
- **Email**: `analyst@adityabirla.com`
- **Password**: `Analyst@2026`

---

## 3. End-to-End Validation Scenarios

### Scenario A: Fixed 1214 x 2159 Viewport & Visual Layout
1. Open Chrome DevTools (`Cmd + Option + I`).
2. Toggle Device Toolbar and set explicit dimensions: **1214 px width x 2159 px height** (Device Pixel Ratio: 1.0).
3. **Verify**:
   - Header "ECONOMIC INDICATOR" is centered over the dark candlestick background graphic.
   - Red "LIVE" badge and indicator dot appear on the left of the ticker bar.
   - Exactly 6 indicator panels render in a 2-column by 3-row grid.
   - No horizontal scrollbars appear anywhere on the page (`window.innerWidth === document.documentElement.scrollWidth`).
   - Card dimensions measure `582px` width x `544px` height with `24px` grid gap.

### Scenario B: Live Ticker Scrolling & Pause on Hover
1. Observe the horizontal ticker quotes (`SENSEX`, `NIFTY BANK`, `NIFTY IT`).
2. **Verify**:
   - Quotes scroll smoothly from right to left in a continuous loop.
   - Positive price and percent changes render in green (`#69F6B8` or `#45FF5B`).
   - Negative price and percent changes render in red (`#FF716A` or `#FF0000`).
3. Hover mouse pointer over the ticker bar.
4. **Verify**: The ticker immediately freezes / pauses in place.
5. Move mouse pointer out of the ticker bar.
6. **Verify**: The scrolling animation resumes seamlessly without jumping.

### Scenario C: Chart Interactions & Series Toggling
1. Move mouse pointer over bars in Panel 1 ("GDP Growth").
2. **Verify**: A dark hover tooltip appears displaying year, series (India or World), and exact percentage.
3. Click the "India" legend item.
4. **Verify**: The blue India bars toggle to hidden; only orange World bars remain visible.
5. Click "India" legend again.
6. **Verify**: Blue bars re-appear.

### Scenario D: Panel Lifecycle States Demonstration
Toggle mock response states in developer tools or via state test toggles:
- **Loading State**: Reload page or throttle network to "Slow 3G". Verify dark skeleton placeholder cards render without shifting layout.
- **Stale State**: In mock mode, set `status: 'stale'`. Verify the "STALE" badge is displayed while historical data remains legible.
- **Unavailable State**: In mock mode, set `status: 'unavailable'`. Verify unavailable notice is rendered and figures show as `" — "`.
- **Error State**: Simulate a network error. Verify the panel displays an error card with a `[Retry]` action.

### Scenario E: Authentication & Automatic Session Expiry
1. Log in with demo analyst credentials. Access dashboard.
2. Manually sign out via the navigation control.
3. **Verify**: User is redirected to `/login`; attempting to directly navigate to `/` redirects back to `/login`.
4. Log in again. Simulate token expiration (e.g. trigger session timeout).
5. **Verify**: The application redirects to `/login?session_expired=true` within 1 second.

---

## 4. Automated Testing Commands

### Unit & Component Tests
```bash
# Run Vitest test suite
npm run test

# Run tests in watch mode
npm run test:watch
```

### Visual Regression & Overlay Validation
```bash
# Execute Playwright screenshot comparison against design/reference.png
npx playwright test tests/visual/dashboard.spec.ts
```

### Linting & Formatting
```bash
npm run lint
npm run format:check
```
