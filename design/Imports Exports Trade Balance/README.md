# Imports, Exports & Trade Balance Dashboard Card

## Overview
This directory contains the pixel-perfect, production-grade implementation of the **Imports, Exports & Trade Balance** macroeconomic indicator card for the Aditya Birla Economic Indicator terminal. It was restored to match `design/import Export.png` and the original Figma specifications (`Frame 2087327383`, `Frame 2087327427`, and `Frame 2087327428` in `design/figma-export.css`).

## Key Improvements & Visual Alignment

### 1. Summary Cards (Exports & Imports)
- **2-Level Vertical Hierarchy**: Replaced the cramped single-row layout where numbers overlapped the illustrations. The card now positions:
  - Top: Label (`Exports` / `Imports`) in white 18px Segoe UI.
  - Middle: Prominent monetary value (`$382.9 B`) in 32px Segoe UI Semibold (`line-height: 38px`).
  - Bottom: Neon green change pill (`▲ -0.81pp`) positioned directly underneath the monetary value.
- **Card Geometry & Backdrop**: Exact Figma dimensions (`255px` × `111px`), `12px` border-radius, `1px solid rgba(65, 93, 136, 0.45)`, with subtle radial cyan lighting backdrop (`#009092` with `blur(22px)`).
- **3D Shipping Illustrations**:
  - Exports: High-resolution shipping vessel with containers, crane, and bright green rising arrow (`exports-3d.png`).
  - Imports: High-resolution shipping vessel with container truck, cranes, and bright blue downward curved arrow (`imports-3d.png`).
  - Positioned cleanly at the lower-right of each card (`right: 8px, bottom: 4px`) with zero collision or overlap with text.

### 2. Grouped Bar Chart (Imports & Exports 2021–2025)
- **Bar Geometry**:
  - `barWidth: 26px` (wider, prominent bars filling the chart area).
  - `barGap: '20%'` (~5px gap between Imports and Exports within each year).
  - Top corner radius: `borderRadius: [4, 4, 0, 0]`.
- **Gradients**:
  - **Imports**: Linear gradient from bright cyan `#0FB8E6` / `#00D2FF` at top, rich blue `#0278A6` in middle, to deep navy `#061E44` at bottom.
  - **Exports**: Linear gradient from bright amber/gold `#FFB012` at top, warm orange `#C96E06` in middle, to dark bronze/brown `#5A2A00` at bottom.
- **Data Labels**:
  - Centered cleanly above each respective bar in `#CCCCCC` 13px Segoe UI Semibold (`distance: 6px`).
  - Fixed the previous bug where `8.7%` was repeated on every bar.

### 3. Trade Balance Line & Pill Badges
- **Line & Markers**:
  - Vivid green line (`#22D700`, width `2.5px`, rounded cap and join).
  - Circular markers (`symbol: 'circle'`, size `9px`, color `#22D700`).
  - Connects points in year order: `2.8%` (2021) → `2.2%` (2022) → `1.7%` (2023) → `1.1%` (2024) → `0.8%` (2025).
- **Pill Badges**:
  - Frosted glass capsules (`backgroundColor: 'rgba(10, 20, 35, 0.75)'`, `borderColor: 'rgba(255, 255, 255, 0.22)'`, `borderRadius: 10px`, `padding: [3, 8]`).
  - Text: `6.3` in crisp `#CCCCCC` 12px Segoe UI Semibold.
  - Positioned directly below markers for 2021–2024 (`position: 'bottom'`).
  - Positioned to the right of the marker for 2025 (`position: 'right', distance: 6px`) to prevent baseline clipping and mirror the Figma reference.

### 4. Legend
- Aligned to the top-right above the chart (`top: 4px, right: 20px`).
- Order & Styling:
  1. `Imports`: Cyan/blue rounded rectangle (`itemWidth: 22px, itemHeight: 12px`).
  2. `Exports`: Orange rounded rectangle.
  3. `Trade Balance`: Green line with circular center marker.
- Text: `#CCCCCC`, `14px`, `500` font weight, Segoe UI.

### 5. Source Footer
- Preserved at card bottom:
  - Left: `Source: Ministry of Commerce and Industry` + `Non-NSE` cyan badge.
  - Right: `As of: FY 2024-25`.

## Data Discrepancy Resolution
In the initial project mock data, `importsValue` and `exportsValue` had placeholder `8.7%` duplicated across all years from 2022 to 2025. This was corrected according to the visual target reference and Figma rectangle heights:
- **2021**: Imports `8.7%`, Exports `6.3%`, Trade Balance `2.8%` (Pill label: `2.8`)
- **2022**: Imports `6.3%`, Exports `4.5%`, Trade Balance `2.2%` (Pill label: `2.2`)
- **2023**: Imports `8.7%`, Exports `4.5%`, Trade Balance `1.7%` (Pill label: `1.7`)
- **2024**: Imports `8.7%`, Exports `6.3%`, Trade Balance `1.1%` (Pill label: `1.1`)
- **2025**: Imports `6.8%`, Exports `4.5%`, Trade Balance `0.8%` (Pill label: `0.8`)

## Files in this Directory
- `TradeBalancePanel.tsx`: Main React component with custom `TradeSummaryCard`.
- `TradeBalancePanel.module.css`: CSS module containing the 2-level card layout, glow, and typography.
- `chartOption.ts`: Apache ECharts option builder with gradients, legend, and pill badge logic.
- `tradeBalance.json`: Complete typed mock dataset matching the contract.
- `exports-3d.png`: 3D shipping illustration with rising green arrow.
- `imports-3d.png`: 3D shipping illustration with curved blue arrow.
