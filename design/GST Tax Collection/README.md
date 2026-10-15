# GST Tax Collection (YOY%) Dashboard Card

## Overview
This directory contains the pixel-perfect, production-grade implementation of the **GST Tax Collection (YOY%)** macroeconomic indicator card for the Aditya Birla Economic Indicator terminal. It matches `design/GST Tax Collection.png` and the original Figma specifications (`Frame 2087327407`, `Frame 2087327426`, and `Frame 2087327427` in `design/figma-export.css`).

## Key Improvements & Visual Alignment

### 1. Summary Cards (GST Collections & Monthly Average)
- **2-Level Vertical Content Hierarchy**: Replaced the previous single-row layout where numbers and delta indicators collided with the illustrations:
  - Top: Card label (`GST Collections` / `Monthly Average`) in white 18px Segoe UI.
  - Middle: Metric value (`3.82%` / `1.97`) in 32px Segoe UI Semibold (`line-height: 38px`).
  - Bottom: Neon green change pill (`▲ -0.81pp`) positioned directly underneath the value in the lower-left area.
- **Card Geometry & Backdrop**: Exact Figma dimensions (`255px` × `111px`), `12px` border-radius, `1px solid rgba(65, 93, 136, 0.45)`, with subtle radial cyan lighting backdrop (`#009092` with `blur(20px)`).
- **3D Illustrations**:
  - GST Collections: High-resolution GST receipt with rupee symbol, gold coins, and small downward arrow (`image-9600.png`).
  - Monthly Average: High-resolution glass calendar with gold rings, bar chart with rising trendline, and circular currency symbol x̄ (`image-9580.png`).
  - Positioned cleanly at the lower-right of each card (`right: 8px, bottom: 4px`) with zero overlap with text or delta badges.

### 2. Bar Chart (Imports 2021–2025)
- **Bar Geometry**:
  - `barWidth: 28px` (prominent bars filling the chart area).
  - Top corner radius: `borderRadius: [4, 4, 0, 0]`.
- **Gradients**:
  - Linear gradient from bright cyan/teal `#0FB8E6` / `#00D2FF` at top, rich blue `#0278A6` in middle, to deep navy `#061E44` at bottom.
- **Data Heights & Labels**:
  - Heights verified from Figma geometry (`Rectangle 3468481` to `3468485`):
    - **2021**: `8.7%`
    - **2022**: `6.6%` (distinct shorter bar)
    - **2023**: `8.7%`
    - **2024**: `8.7%`
    - **2025**: `6.8%` (distinct shorter bar)
  - Centered percentage labels above each bar in `#CCCCCC` 13px Segoe UI Semibold.

### 3. Trade Balance Line & Pill Badges
- **Line & Markers**:
  - Exact yellow from Figma: `#F4E15C` (width `2.5px`, rounded cap and join).
  - Circular markers: `#F4E15C`, size `9px`.
  - Line path:
    - **2021**: `2.8%`
    - **2022**: `2.8%` (flat between 2021 and 2022)
    - **2023**: `3.6%` (rises to 3.6%)
    - **2024**: `3.6%` (remains level across 2023 and 2024)
    - **2025**: `3.1%` (declines to 3.1%)
- **Pill Badges**:
  - Frosted glass capsules (`backgroundColor: 'rgba(10, 20, 35, 0.75)'`, `borderColor: 'rgba(255, 255, 255, 0.22)'`, `borderRadius: 10px`, `padding: [3, 8]`).
  - Text: `2.8%`, `2.8%`, `3.6%`, `3.6%`, `3.1%` in crisp `#CCCCCC` 12px Segoe UI Semibold.
  - Positioned below each marker (`position: 'bottom', distance: 8px`).

### 4. Legend
- Aligned to the top-right above the chart (`top: 4px, right: 20px`).
- Two series only (Exports excluded per Figma specification):
  1. `Imports`: Cyan rounded square (`22px` × `12px`).
  2. `Trade Balance`: Yellow line with central circular marker.
- Text: `#CCCCCC`, `14px`, `500` font weight, Segoe UI.

### 5. Source Footer
- Preserved at card bottom:
  - Left: `Source: Goods and Services Tax Network (GSTN)` + `Non-NSE` cyan badge.
  - Right: `As of: July 2025`.

## Data Discrepancy Resolution
In the initial project mock data, `collectionRate` was hardcoded to `8.7%` for all 5 years, and `averageRate` had arbitrary numbers with no label alignment. This was resolved using the exact Figma rectangle heights and marker coordinates:

| Year | Imports (Bar) | Trade Balance (Line) | Pill Label |
| :--- | :---: | :---: | :---: |
| **2021** | 8.7% | 2.8% | 2.8% |
| **2022** | 6.6% | 2.8% | 2.8% |
| **2023** | 8.7% | 3.6% | 3.6% |
| **2024** | 8.7% | 3.6% | 3.6% |
| **2025** | 6.8% | 3.1% | 3.1% |

## Files in this Directory
- `GstCollectionPanel.tsx`: Main React component with custom `GstSummaryCard`.
- `GstCollectionPanel.module.css`: CSS module with 2-level card layout, glow, and typography.
- `chartOption.ts`: Apache ECharts option builder with cyan bar gradients, yellow trade balance line, and pill badge logic.
- `gstCollection.json`: Complete typed mock dataset matching the contract.
- `image-9600.png`: 3D GST receipt and stacked coins illustration.
- `image-9580.png`: 3D calendar and chart with x̄ circular currency symbol illustration.
