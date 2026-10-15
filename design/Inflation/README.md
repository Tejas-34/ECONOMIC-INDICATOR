# Inflation (IND) Dashboard Card Package

This directory contains the complete and exact implementation package for the **Inflation (IND)** dashboard card, faithfully matching the visual reference (`design/inflation.png`) and authoritative Figma export design tokens (`design/figma-export.css`).

---

## 1. Package Contents

- **`InflationPanel.tsx`**: Component implementation for the Inflation dashboard card, rendering custom stacked summary cards with 3D illustrations, neon delta badges, and the ECharts time-series line chart.
- **`InflationPanel.module.css`**: CSS module containing exact Figma dimensions (`255px × 111px`), borders, border-radii (`12px`), radial glow blurs, Segoe UI typography, and responsive chart styling.
- **`chartOption.ts`**: ECharts configuration generator with subtle vertical gridlines, horizontal 0% baseline, glowing cyan line (`#00F0FF`), per-year circular data markers, and gradient area fill.
- **`inflation.json`**: Accurate annual dataset (`2021` to `2025`) without intermediate pseudo-quarters or mid-chart badges.
- **`image-9590.png`**: High-resolution 3D isolated asset of the Inflation Rate shopping basket with gold coins, upward trend arrow, groceries, and percentage tags.
- **`rbi-target-3d.png`**: High-resolution 3D isolated asset of the Reserve Bank of India building with gold coins and bullseye target with arrow.

---

## 2. Figma Design Tokens & Properties

### Card & Layout
- **Panel Shell**: Frosted header bar (`rgba(44, 44, 45, 0.45)`), diagonal chrome corner sheen (`vector-16250.svg`), ambient glow blobs (`#1D809C`, blur `59.2px`).
- **Header Title**: `Inflation` in white (`#FFFFFF`, Segoe UI / Roboto, 20px 600) + ` (IND)` in bright cyan (`#0FCBF0` / `#00D2FF`, 20px 600).
- **Summary Cards**:
  - Size: `255px × 111px`, `border-radius: 12px`, `border: 1px solid rgba(65, 93, 136, 0.45)`.
  - Background (Card 1): `linear-gradient(180deg, rgba(17, 96, 157, 0.14) 0%, rgba(12, 12, 13, 0.14) 100%)`.
  - Background (Card 2): `rgba(17, 96, 157, 0.14)`.
  - Glow blob: `width: 75px; height: 75px; background: #009092; filter: blur(20px); opacity: 0.35; border-radius: 50%`.
  - Typography: Label `18px 400 #FFFFFF`, Value `32px 600 #FFFFFF`, Delta `16px 600 #45FF5B`.
  - Delta pill: `background: linear-gradient(90deg, rgba(26, 58, 70, 0.85) 0%, rgba(31, 68, 82, 0.3) 100%)`, border radius `4px`.

### Chart Geometry & Styling
- **Grid Range**: Y-axis `0%` to `10%` with interval `2%` (`0%`, `2%`, `4%`, `6%`, `8%`, `10%`).
- **Timeline**: 5 annual points (`2021`, `2022`, `2023`, `2024`, `2025`).
- **Graph Stroke**: Strictly sharp linear line segments (`smooth: false`) with no circular point markers (`showSymbol: false`), faithfully matching `design/inflation.png`.
- **Year Point Rate Badges**: Floating pill badges on each year point (`symbolSize: [46, 22]`, `rgba(0, 0, 0, 0.75)` background, `10px` border-radius) displaying the annual inflation rate.
- **Vertical Gridlines**: 5 subtle vertical lines passing through each year (`rgba(255, 255, 255, 0.12)`, width `1px`).
- **Baseline**: Horizontal solid line at `0%` (`rgba(255, 255, 255, 0.22)`, width `1.2px`).
- **Stroke & Area Gradient**:
  - Stroke: Vibrant glowing cyan (`#00F0FF`, width `2.5px`).
  - Area: Translucent cyan area fill fading down to 0% at baseline.
