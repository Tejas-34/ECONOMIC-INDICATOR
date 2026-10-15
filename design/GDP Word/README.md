# GDP Growth — India vs World (YOY%) Implementation

This directory contains the precise, authoritative implementation of the **GDP Growth — India vs World (YOY%)** card for the Economic Indicator Dashboard, matching `design/GDP Word.png` and Figma `Frame 2087327363`.

## File Structure
- `GdpGrowthPanel.tsx`: Main React panel component integrating the header, country summary cards, chart, and source footer.
- `GdpGrowthPanel.module.css`: CSS module specifying exact Figma geometry, dimensions, colors, and gradients.
- `chartOption.ts`: Apache ECharts option builder with exact series data, bar widths, gradients, axes, and legends.
- `gdpGrowth.json`: Authoritative mock data contract with strict 2021–2025 rates.
- `image-9450.png`: Circular 3D India flag icon (43px x 43px).
- `image-9510.png`: Circular 3D Earth globe icon (43px x 43px).

---

## 1. Summary Cards Specifications
- **Dimensions**: `255px` width × `111px` height, `border-radius: 12px`.
- **Borders & Backgrounds**:
  - India: `rgba(0, 0, 0, 0.22)` with `border: 1px solid rgba(65, 93, 136, 0.45)`.
  - World: `rgba(2, 151, 159, 0.14)` with `border: 1px solid rgba(65, 93, 136, 0.45)`.
- **Country Icons**: `43px` circular 3D icons (`image-9450.png` and `image-9510.png`).
- **Country Labels**: "India" and "World" in `Segoe UI`, `18px`, regular 400, `#FFFFFF`.
- **Large Values**: "4.82%" and "3.82%" in `Segoe UI`, `36px`, semibold 600, `#FFFFFF`.
- **Delta Indicator**:
  - Background pill: `linear-gradient(90deg, rgba(26, 58, 70, 0.85) 0%, rgba(31, 68, 82, 0.3) 100%)`.
  - Triangle indicator: `Polygon 1` geometry in `#45FF5B`.
  - Text: `Segoe UI`, `20px`, semibold 600, `#45FF5B` (`-0.2pp` / `-0.81pp`).
  - Aligned on a single horizontal row without wrapping.

---

## 2. Chart Specifications
- **Dimensions & Grid**:
  - Left margin: `48px`
  - Right margin: `25px`
  - Top padding: `36px`
  - Bottom padding: `26px`
  - Outer border: `1px solid #5B5B5B`.
- **Y-Axis & Horizontal Grid**:
  - Scale: `0%`, `2%`, `4%`, `6%`, `8%`, `10%`.
  - Labels: `Segoe UI`, `14px`, semibold 600, `#CCCCCC`.
  - Split lines: `1px solid #5B5B5B` (subtle dark lines).
- **X-Axis**:
  - Years: `2021`, `2022`, `2023`, `2024`, `2025`.
  - Labels: `Segoe UI`, `15px`, semibold 600, `#CCCCCC`, margin `12px`.
- **Bars & Series Data**:
  | Year | India Rate | World Rate |
  |------|------------|------------|
  | 2021 | 8.7%       | 6.3%       |
  | 2022 | 6.3%       | 4.5%       |
  | 2023 | 8.7%       | 4.5%       |
  | 2024 | 8.7%       | 6.3%       |
  | 2025 | 6.8%       | 4.5%       |
- **Bar Styling**:
  - Bar width: `25.4px`.
  - Bar gap between India and World: `24%` (~6px).
  - Corner radius: `[4, 4, 0, 0]` (rounded top).
  - India gradient: Vertical linear gradient from `#0FB8E6` (top) to `#061E44` (bottom).
  - World gradient: Vertical linear gradient from `#FFB012` (top) to `#844B08` (bottom).
  - Value labels: Positioned directly above bars, `Segoe UI`, `14px`, semibold 600, `#CCCCCC`.
- **Legend**:
  - Position: Right-aligned (`right: 25`, `top: 4`).
  - India: `#0FB8E6` cyan rounded rectangle.
  - World: `#FFB012` orange rounded rectangle.
  - Text: `Segoe UI`, `15px`, semibold 600, `#CCCCCC`.
