# 📊 GB Energy Dashboard - Chart Specifications

**Dashboard:** `1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc`  
**Sheet:** `Dashboard`  
**Theme:** Orange (#FF8C00) with National Grid Blue (#004C97)

---

## 🎨 Color Palette

| Role | Hex | RGB (0-1 scale) | Usage |
|------|-----|-----------------|-------|
| **Primary Orange** | `#FF8C00` | `(1.0, 0.55, 0.0)` | Title bar, KPI highlights, accent bars, wind turbines |
| **NG Blue** | `#004C97` | `(0.0, 0.30, 0.59)` | Chart axes, text emphasis, GSP points |
| **Positive Green** | `#43A047` | `(0.26, 0.63, 0.28)` | Normal/increasing performance, high generation |
| **Warning Red** | `#E53935` | `(0.90, 0.22, 0.21)` | Outage alerts, shortfall warnings |
| **Neutral Gray** | `#F5F5F5` | `(0.96, 0.96, 0.96)` | Filter band, panels |
| **Background Cream** | `#FFF7F0` | `(1.0, 0.97, 0.94)` | Overall sheet background |
| **DNO Border Orange** | `#FFD180` | `(1.0, 0.82, 0.50)` | Map DNO region boundaries |

---

## 📐 Chart Zones & Specifications

### 1. Fuel Mix Pie Chart
**Location:** `Dashboard!A20:F40`  
**Type:** Doughnut / Pie  
**Data Source:** `Dashboard!A10:B18` (Fuel Type, MW)

**Configuration:**
- **Chart Title:** "Live Generation Mix by Fuel Type"
- **Title Position:** Top center
- **Legend:** Right side
- **Colors:** Rotate through: Orange → Blue → Green → Gray → Yellow → Purple
- **Data Labels:** Show percentage + MW value
- **Hole Size (Doughnut):** 40%

**Color Mapping (Suggested):**
```javascript
{
  "Wind": "#FF8C00",        // Orange
  "Nuclear": "#004C97",     // Blue
  "CCGT": "#43A047",        // Green
  "Coal": "#757575",        // Gray
  "Solar": "#FFD180",       // Light Orange
  "Biomass": "#8E24AA",     // Purple
  "Hydro": "#039BE5",       // Light Blue
  "Imports": "#D32F2F"      // Red
}
```

---

### 2. Interconnector Flows Chart
**Location:** `Dashboard!G20:L40`  
**Type:** Multi-series Line Chart (or Stacked Bar)  
**Data Source:** `Dashboard!E10:F18` (Interconnector, MW Flow)

**Configuration:**
- **Chart Title:** "Interconnector Flows (Import ↓ / Export ↑)"
- **X-Axis:** Time (HH:MM format)
- **Y-Axis:** MW (show negative for exports)
- **Series:** One line per interconnector (IFA, IFA2, BritNed, NSL, Moyle, ElecLink, Viking)
- **Colors:** Orange for imports (positive), Blue for exports (negative)
- **Legend:** Bottom
- **Gridlines:** Horizontal major only

**Visual Indicators:**
- Import (↓): Solid line, Orange
- Export (↑): Dashed line, Blue

---

### 3. Demand vs Generation Trend
**Location:** `Dashboard!A45:F65`  
**Type:** Stacked Area Chart (48h historical)  
**Data Source:** Link to time-series data (from `Live_Raw_Gen` or create summary range)

**Configuration:**
- **Chart Title:** "48h Demand vs Generation Trend"
- **X-Axis:** Time (DD/MM HH:MM)
- **Y-Axis:** MW
- **Series:**
  - Generation (stacked by fuel type): Wind, Nuclear, CCGT, etc.
  - Demand (line overlay): Red dashed line
- **Colors:** Use fuel type palette from Chart 1
- **Legend:** Bottom, 2 columns
- **Fill Opacity:** 70%

**Stacking Order (bottom to top):**
1. Nuclear (base load) - Blue
2. CCGT - Green
3. Wind - Orange
4. Solar - Yellow
5. Other - Gray

---

### 4. System Prices (SSP/SBP/MID)
**Location:** `Dashboard!G45:L65`  
**Type:** 3-Line Chart (48h historical)  
**Data Source:** Create price range (link to BMRS API or manual entry)

**Configuration:**
- **Chart Title:** "System Prices: SSP / SBP / MID (48h)"
- **X-Axis:** Time (DD/MM HH:MM)
- **Y-Axis:** £/MWh
- **Series:**
  - MID Price: Orange, solid, 3px
  - SBP (System Buy Price): Red, solid, 2px
  - SSP (System Sell Price): Green, solid, 2px
- **Legend:** Top right
- **Gridlines:** Both horizontal & vertical
- **Range:** Auto-scale with £10 padding

**Annotations:**
- Add horizontal line for "Target Price" (e.g., £50/MWh) - Gray dashed

---

### 5. Financial KPIs Chart
**Location:** `Dashboard!A68:L90`  
**Type:** Combo Chart (Column + Line)  
**Data Source:** `Dashboard!H10:L18` (or create KPI summary range)

**Configuration:**
- **Chart Title:** "Financial KPIs: BOD/BID & Imbalance Costs"
- **X-Axis:** Time period (daily buckets)
- **Left Y-Axis:** £ millions (BOD/BID volumes)
- **Right Y-Axis:** £/MWh (imbalance price)
- **Series:**
  - BOD (Bid-Offer Data) Volume: Orange column
  - BID Acceptance: Blue column
  - Imbalance Price: Red line (right axis)
- **Legend:** Bottom center
- **Column Width:** 80%

---

### 6. Wind Performance: Forecast vs Actual
**Location:** `Dashboard!A46:F62` (Alternative placement if space allows)  
**Type:** Dual-Axis Line Chart  
**Data Source:** `Wind_Warnings` sheet or create summary range

**Configuration:**
- **Chart Title:** "Wind Forecast vs Actual (24h)"
- **X-Axis:** Time (HH:MM)
- **Left Y-Axis:** MW
- **Right Y-Axis:** % Deviation
- **Series:**
  - Forecast: Orange dashed line
  - Actual: Orange solid line
  - Deviation %: Red line (right axis)
- **Alert Zone:** Shade red background where deviation > 15%
- **Legend:** Top right

---

### 7. Frequency & BM Costs
**Location:** `Dashboard!G46:L62` (Alternative placement)  
**Type:** Line + Column Combo  
**Data Source:** Create summary range or link to IRIS data

**Configuration:**
- **Chart Title:** "System Frequency & BM Costs"
- **X-Axis:** Time (HH:MM)
- **Left Y-Axis:** Hz (49.5 - 50.5)
- **Right Y-Axis:** £k (BM Cost)
- **Series:**
  - System Frequency: Blue line (left axis), 3px
  - BM Cost: Orange column (right axis)
- **Target Line:** 50.0 Hz (green dashed)
- **Alert Zones:**
  - Red shading: < 49.8 Hz or > 50.2 Hz
  - Amber: 49.8-49.9 Hz and 50.1-50.2 Hz

---

## 🗺️ Map Layer Specifications

**Sheet:** `Energy_Map`  
**Location:** Full width `A1:Z90`

### Interactive Map (via Apps Script or Data Studio)

**Layers:**

1. **DNO Boundaries**
   - Geometry: Polygons
   - Stroke: `#FFD180` (light orange), 2px
   - Fill: Transparent or 10% opacity orange
   - Tooltip: DNO Name, Peak Demand (MW), Coverage Area (km²)

2. **GSP Points**
   - Geometry: Markers (circle)
   - Color: `#004C97` (NG Blue)
   - Size: 8px
   - Tooltip: GSP ID, Connected DNO, Current Flow (MW), Capacity (MW)

3. **Offshore Wind Farms**
   - Geometry: Markers (custom turbine icon)
   - Color: `#FF8C00` (Orange)
   - Size: 12px
   - Lines connecting to nearest GSP: Orange dashed, 1px
   - Tooltip: Farm Name, Capacity (MW), Status, Distance to GSP (km)

4. **Active Outages**
   - Geometry: Warning icon (⚠️)
   - Color: `#E53935` (Red)
   - Size: 10px
   - Animation: Pulse effect
   - Tooltip: Plant Name, MW Lost, Duration, Estimated Restoration

**Controls:**
- Filter: Region dropdown (sync with Dashboard!D3)
- Toggle layers: Checkboxes for DNO/GSP/Wind/Outages
- Zoom: Auto-fit to GB boundary
- Legend: Bottom right corner

---

## 📊 Data Source Ranges

| Chart | Source Sheet | Range | Update Frequency |
|-------|--------------|-------|------------------|
| Fuel Mix | Dashboard | A10:B18 | 5 min (live) |
| Interconnectors | Dashboard | E10:F18 | 5 min (live) |
| Demand Trend | Live_Raw_Gen | Time-series | 5 min |
| Prices | External/Manual | Summary range | 10 min |
| Financial | Dashboard | H10:L18 | Daily |
| Wind Perf | Wind_Warnings | Time-series | 10 min |
| Frequency | External API | Real-time | 5 min |

---

## 🔧 Apps Script Implementation Notes

### Chart Creation Template
```javascript
function createFuelMixPie() {
  const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName("Dashboard");
  const dataRange = sheet.getRange("A10:B18");
  
  const chart = sheet.newChart()
    .setChartType(Charts.ChartType.PIE)
    .addRange(dataRange)
    .setPosition(20, 1, 0, 0)  // Row 20, Col A
    .setOption('title', 'Live Generation Mix by Fuel Type')
    .setOption('titleTextStyle', {fontSize: 14, bold: true, color: '#004C97'})
    .setOption('pieHole', 0.4)
    .setOption('legend', {position: 'right'})
    .setOption('colors', ['#FF8C00', '#004C97', '#43A047', '#757575', '#FFD180'])
    .setOption('pieSliceTextStyle', {fontSize: 11})
    .build();
  
  sheet.insertChart(chart);
}
```

### Dynamic Color Assignment
```javascript
function getFuelColor(fuelType) {
  const colorMap = {
    'Wind': '#FF8C00',
    'Nuclear': '#004C97',
    'CCGT': '#43A047',
    'Coal': '#757575',
    'Solar': '#FFD180',
    'Biomass': '#8E24AA',
    'Hydro': '#039BE5'
  };
  return colorMap[fuelType] || '#BDBDBD';  // Default gray
}
```

---

## ✅ Implementation Checklist

- [x] Orange theme applied to dashboard
- [x] Chart zones marked with placeholders
- [x] Color palette documented
- [ ] Create chart generation script (`create_charts.gs`)
- [ ] Test chart auto-refresh with live data
- [ ] Implement map layer via Apps Script or embed Data Studio
- [ ] Add chart update triggers (onEdit, time-driven)
- [ ] Create chart management menu: "📊 Charts" → Update All, Reset, Configure

---

## 📝 Future Enhancements

1. **Interactive Filters:** Link Dashboard!B3, D3, F3 dropdowns to chart filtering
2. **Drill-Down:** Click chart series → show detailed breakdown
3. **Export Charts:** PDF report generation with all charts
4. **Alerts Integration:** Overlay alert markers on time-series charts
5. **Mobile View:** Responsive chart sizing for tablet/phone
6. **Animation:** Smooth transitions when data updates
7. **Forecast Overlay:** Show predicted values (dotted lines) beyond current time

---

**Last Updated:** 2025-11-29  
**Script Files:**
- `apply_orange_redesign.py` - Theme & layout
- `add_validation_and_formatting.py` - Dropdowns & conditional formatting
- `create_charts.gs` - Chart generation (TODO)
