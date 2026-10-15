# Government Expenditure Dashboard Card Package

This directory contains the complete and exact implementation package for the **Government Expenditure** dashboard card, faithfully matching the visual reference (`design/Goverment Expend.png`) and authoritative Figma export design tokens (`design/figma-export.css`).

---

## 1. Package Contents

- **`GovtExpenditurePanel.tsx`**: Component implementation for the Government Expenditure dashboard card, rendering custom summary cards with high-resolution 3D isolated illustrations, neon delta badges, and the ECharts stacked bar chart.
- **`GovtExpenditurePanel.module.css`**: CSS module containing exact Figma dimensions (`255px × 111px`), borders, border-radii (`12px`), radial glow blurs, Segoe UI typography, and responsive chart styling.
- **`chartOption.ts`**: ECharts configuration generator with rectangular border outline (`#5B5B5B`), horizontal gridlines (0% to 10% interval 2%), stacked bar geometry (`barWidth: 32`), gradients, and multi-tier segment labels.
- **`govtExpenditure.json`**: Authoritative annual expenditure dataset (2021 to 2025).
- **`total-expenditure-3d.png`**: High-resolution 3D isolated asset of financial document with gold coins, ascending bars, and upward arrows.
- **`capital-expenditure-3d.png`**: High-resolution 3D isolated asset of classical government building with gold columns, currency coin, ascending bars, and upward gold arrow.

---

## 2. Figma Design Tokens & Properties

### Card & Header
- **Panel Shell**: Frosted header bar (`rgba(44, 44, 45, 0.45)`), diagonal chrome corner sheen (`vector-16250.svg`), ambient glow blobs (`#1D809C`).
- **Header Title**: `Government Expenditure` in white (`#FFFFFF`, Segoe UI / Roboto, 20px 600).
- **Summary Cards**:
  - Size: `255px × 111px`, `border-radius: 12px`, `border: 1px solid rgba(65, 93, 136, 0.45)`.
  - Background (Card 1): `linear-gradient(180deg, rgba(17, 96, 157, 0.14) 0%, rgba(12, 12, 13, 0.14) 100%)`.
  - Background (Card 2): `rgba(17, 96, 157, 0.14)`.
  - Glow blob: `width: 75px; height: 75px; background: #009092; filter: blur(20px); opacity: 0.35; border-radius: 50%`.
  - Typography: Label `18px 400 #FFFFFF`, Value `32px 600 #FFFFFF`, Delta `16px 600 #45FF5B`.
  - Delta pill: `background: linear-gradient(90deg, rgba(26, 58, 70, 0.85) 0%, rgba(31, 68, 82, 0.3) 100%)`, border radius `4px`.
  - Vertical layout hierarchy: Label on top row, large percentage value in middle, delta pill in lower strip.

### Chart Geometry & Styling
- **Grid Range**: Y-axis `0%` to `10%` with interval `2%` (`0%`, `2%`, `4%`, `6%`, `8%`, `10%`).
- **Plot Area Outline**: Full rectangular bounding box with `borderWidth: 1, borderColor: '#5B5B5B'`.
- **Horizontal Gridlines**: Solid lines across all 2% increments (`color: '#5B5B5B'`).
- **Stacked Bars**:
  - Width: `barWidth: 32`.
  - Lower segment (Capital Expenditure): `linear-gradient(180deg, #FFB012 0%, #844B08 100%)`.
  - Upper segment (Revenue Expenditure): `linear-gradient(0deg, #0FB8E6 0%, #0046B7 100%)` with `borderRadius: [4, 4, 0, 0]`.
- **Labels**:
  - Total above bar: `position: 'top', distance: 6, color: '#FFFFFF', fontSize: 14, fontWeight: 600`.
  - Revenue Expenditure inside blue segment: `position: 'inside', color: '#FFFFFF', fontSize: 14, fontWeight: 600`.
  - Capital Expenditure inside orange segment: `position: 'insideBottom', distance: 8, color: '#FFFFFF', fontSize: 14, fontWeight: 600`.

---

## 3. Data & Scaling Analysis

1. **Raw Figures vs 0-10% Display Axis**:
   - The underlying dataset specifies `totalExpenditure: 31.2`, `revenueExpenditure: 7.9`, `capitalExpenditure: 23.2` (in ₹ Lakh Crore / budget proportions).
   - In Figma, the visual bar stack heights on the `0-10%` axis were proportioned to match macroeconomic budget outlays:
     - 2021: Total 4.7% (Capital 3.2% + Revenue 1.5%)
     - 2022: Total 5.2% (Capital 3.6% + Revenue 1.6%)
     - 2023: Total 5.3% (Capital 3.7% + Revenue 1.6%)
     - 2024: Total 6.6% (Capital 4.9% + Revenue 1.7%)
     - 2025: Total 7.6% (Capital 6.0% + Revenue 1.6%)
2. **Label Formatting**:
   - The segment labels dynamically render the actual dataset expenditure figures (`23.2`, `7.9`, `31.2`) directly from the series points, preserving data integrity while ensuring the visual bar geometry matches the Figma design.
