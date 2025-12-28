# Live Dashboard v2 - Current Layout Analysis
**Date**: 28 December 2025  
**Spreadsheet**: GB Live 2 (1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA)  
**Sheet**: Live Dashboard v2

---

## 📐 Sheet Dimensions
- **Total Size**: 102 rows × 27 columns (A-AA)
- **Frozen Rows**: 2 (header stays visible when scrolling)
- **Last Updated**: 28/12/2025, 17:22:43 (v2.0) SP 35

---

## 🎯 Layout Structure

### **Header Section (Rows 1-12)**

#### Title & Status (Rows 1-4)
- **A1**: `⚡ GB LIVE ENERGY VIEW` (Main title)
- **P1**: Sparkline example formula
- **AA1**: `PYTHON_MANAGED` (Flag for automated updates)
- **A2**: Last updated timestamp with version and settlement period
- **A3**: IRIS status indicator (`⚠️ IRIS Delayed (5m ago)`)
- **A4**: `⚡ Market Overview` (Section header)

#### Market Overview KPIs (Rows 5-6)
**Row 5 (Labels)**:
- A5: `BM-MID Spread £/MWh`
- C5: `Market Index £/MWh`
- E5: `Grid Frequency`
- G5: `🏭 Total Generation`
- I5: `🌬️ Wind Output`
- K5: `🔌 System Demand`

**Row 6 (Values)**:
- A6: `£33.74` (Spread value)
- C6: `£46.34` (Market index)
- E6: `+0.000 Hz` (Frequency deviation)
- G6: `38.0 GW` (Total generation)
- I6: `3.6 GW` (Wind output)
- K6: `38.0 GW` (System demand)

#### Section Headers (Rows 10, 12)
- **A10**: `🔋 Generation Mix` (Left section header)
- **G10**: `🌍 Interconnectors & Map` (Right section header)
- **K10**: `📊 MARKET DYNAMICS - 24 HOUR VIEW` (Far right section)

**Row 12 (Column Headers)**:
- **A12-C12**: Generation Mix headers (`🛢️ Fuel Type`, `⚡ GW`, `📊 Share`, `📊 Bar`)
- **G12-H12**: Interconnector headers (`🔗 Connection`, `🌊 Flow Trend`)
- **K12**: Market dynamics header

---

### **Data Section (Rows 13+)**

#### Left Section (Columns A-D): Generation Mix
**Location**: A13:D22 (10 fuel types)

| Row | Fuel Type | GW (Col B) | Share (Col C) | Bar Chart (Col D) |
|-----|-----------|------------|---------------|-------------------|
| 13 | 🌬️ WIND | 3.6 | 11.50% | (Formula) |
| 14 | ⚛️ NUCLEAR | 3.9 | 12.40% | |
| 15 | 🏭 CCGT | 17.7 | 56.10% | |
| 16 | 🌿 BIOMASS | 3 | 9.50% | |
| 17 | 💧 NPSHYD | 1.1 | 3.50% | |
| 18 | ❓ OTHER | 1.4 | 4.60% | |
| 19 | 🛢️ OCGT | 0 | 0.00% | |
| 20 | ⛏️ COAL | 0 | 0.00% | |
| 21 | 🛢️ OIL | 0 | 0.00% | |
| 22 | 💧 PS | 0.8 | 2.50% | |

**Note**: Columns E-F appear to be empty/reserved for sparklines or additional charts.

---

#### Middle Section (Columns G-J): Interconnectors & Outages

**Interconnectors** (G13:H22):
| Row | Connection | Flow/Trend |
|-----|------------|------------|
| 13 | 🇫🇷 ElecLink | +997 MW |
| 14 | 🇮🇪 East-West | -531 MW |
| 15 | 🇫🇷 IFA | +1505 MW |
| 16 | 🇮🇪 Greenlink | -514 MW |
| 17 | 🇫🇷 IFA2 | +991 MW |
| 18 | 🇮🇪 Moyle | -451 MW |
| 19 | 🇳🇱 BritNed | +408 MW |
| 20 | 🇧🇪 Nemo | +997 MW |
| 21 | 🇳🇴 NSL | +1397 MW |
| 22 | 🇩🇰 Viking Link | +1423 MW |

**Active Outages** (G25:J35+):
- **G25**: Header with summary (`⚠️ ACTIVE OUTAGES - Top 15 by Capacity | Total: 15 units | Offline: 5,738 MW | Normal Capacity: 6,780 MW`)
- **G26:J26**: Column headers (`Asset Name`, `Fuel Type`, `Unavail (MW)`, `Normal (MW)`)
- **G27:J35**: Outage data (15 rows)
  - Example: DIDCB6, 🔥 Fossil Gas, 666 MW unavailable, 710 MW normal capacity

---

#### Right Section (Columns K-N): Market Dynamics (NEW KPIs) ⭐

**Current Status**: KPIs ALREADY EXIST in column K! Data was previously added.

**Location**: K13:N22 (10 KPI rows with sparklines)

| Row | KPI Name (Col K) | Value (Col L) | Description (Col M) | Sparkline (Col N?) |
|-----|------------------|---------------|---------------------|---------------------|
| 13 | Real-time imbalance price | £80.08/MWh | SSP=SBP ⚖ Balanced | ? |
| 14 | *(Label missing)* | £64.53/MWh | Rolling mean | ? |
| 15 | 7-Day Average | £67.90/MWh | Rolling mean | ? |
| 16 | Deviation from 7d | -27.90% | vs 7-day avg | ? |
| 17 | 30-Day Average | £69.48/MWh | Rolling mean | ? |
| 18 | 30-Day Low | £-2.71/MWh | Min price | ? |
| 19 | Deviation from 7d | +12.80% | vs 7-day avg | ? |
| 20 | EWAP Offer | £0.00/MWh | Energy-weighted avg | ? |
| 21 | 30-Day High | £129.50/MWh | Max price | ? |
| 22 | Dispatch Intensity | 56.0/hr | Acceptances/hour • 10.4% active | ? |

**Additional Context Rows**:
- K26: `Cause` (relates to outages section)
- K27-35: Outage cause labels (Turbine/Generator, OPR, Statutory, Maintenance, Operational, Mechanical)

---

## 🔍 Key Observations

### ✅ What's Working
1. **Clear 3-column layout**: Generation Mix (A-D) | Interconnectors/Outages (G-J) | Market Dynamics (K-N)
2. **KPIs already implemented** in column K with values in L and descriptions in M
3. **Data is live**: Updated 28/12/2025 17:22:43, Settlement Period 35
4. **Good use of emojis** for visual clarity (fuel types, country flags)
5. **Frozen rows** keep headers visible when scrolling

### ⚠️ Issues Identified
1. **Row 14 missing KPI label** in column K (has value £64.53/MWh but no description)
2. **Duplicate "Deviation from 7d"** labels in K16 and K19 (confusing)
3. **EWAP Offer shows £0.00** - likely data issue or calculation error
4. **No visible sparklines** in column N (may need chart objects or SPARKLINE formulas)
5. **Column spacing**: Columns E-F empty, could be used for generation mix sparklines
6. **Outage cause data** (K26-35) overlaps with KPI section visually

---

## 🎨 Formatting Details

### Colors & Styling (Visual Inspection Needed)
- **Frozen Rows**: 2 (title and timestamp stay at top)
- **Cell AA1**: `PYTHON_MANAGED` flag (likely hidden from users)
- **Batch test cells**: Z2-AA4 (test markers, should be hidden or removed)

### Data Types
- **Currency**: £ symbol with 2 decimal places (e.g., £80.08/MWh)
- **Percentages**: 2 decimal places with % symbol (e.g., 11.50%)
- **Power**: 1 decimal place with GW/MW units (e.g., 3.6 GW)
- **Frequency**: 3 decimal places with Hz unit (e.g., +0.000 Hz)
- **Rates**: 1 decimal place with /hr unit (e.g., 56.0/hr)

---

## 🚀 Recommendations for Improvement

### 1. Fix Missing/Duplicate Labels
- **K14**: Add label (possibly "Hourly Average" or "Current Hour Average")
- **K16/K19**: Rename one to avoid duplication (K16: "Deviation from 7d", K19: "Price Volatility" or "Deviation from 30d")

### 2. Add Sparklines
- **Column N**: Add SPARKLINE formulas showing 24-hour trends for each KPI
- **Column D**: Add SPARKLINE formulas for generation mix trends (7-day history)
- **Column I**: Add SPARKLINE formulas for interconnector flow trends

### 3. Fix Data Issues
- **EWAP Offer (K20)**: Investigate why it shows £0.00 (should be derived from bmrs_boalf)
- **30-Day Low (K18)**: £-2.71/MWh seems unusual (negative price event?)

### 4. Enhance Outages Section
- **Separate outage causes** (K26-35) from Market Dynamics section with clear divider
- Consider moving outages to separate section or sheet if list grows beyond 15 items

### 5. Clean Up Test Data
- **Remove batch test cells** (Z2-AA4) before production use
- **Hide column AA** (PYTHON_MANAGED flag doesn't need to be visible)

---

## 📊 Data Sources (BigQuery Tables)

Based on KPI definitions:

| KPI | BigQuery Table | Key Fields |
|-----|----------------|------------|
| Real-time imbalance price | `bmrs_costs` | `systemSellPrice`, `settlementDate`, `settlementPeriod` |
| 7/30-Day Averages | `bmrs_costs` | Rolling aggregations over date ranges |
| EWAP Offer | `bmrs_boalf` OR `boalf_with_prices` | `acceptancePrice`, `acceptanceVolume` (energy-weighted) |
| Dispatch Intensity | `bmrs_boalf` | COUNT of `acceptanceNumber` per hour |
| Generation Mix | `bmrs_fuelinst_iris` | `fuelType`, `generation` |
| Interconnectors | `bmrs_fuelinst_iris` | `fuelType='INTELEC'`, `psrType` (connection name) |
| Outages | `bmrs_remit_unavailability` | `assetId`, `fuelType`, `unavailableCapacity`, `normalCapacity` |

---

## 🔧 Update Frequency

- **Live Metrics**: Every 5 minutes (update_live_metrics.py - currently PAUSED)
- **Full Refresh**: Daily at 4:00 AM (unified_dashboard_refresh.py - currently PAUSED)
- **IRIS Status**: Real-time check (5-minute delay indicator in A3)

---

## 📝 Next Steps

**IMMEDIATE** (User Requested):
- ✅ **Layout analysis complete** - Column K already has KPIs!
- 🔄 **Add/improve sparklines** in column N for 24-hour trends
- 🔄 **Fix missing K14 label** and duplicate K16/K19 labels
- 🔄 **Investigate EWAP Offer £0.00 issue**

**AFTER LAYOUT CHANGES**:
- Resume auto-updates (uncomment cron jobs)
- Test refresh cycle with new layout
- Monitor IRIS ingestion status

---

**Generated**: 28 December 2025  
**Analyzed by**: GitHub Copilot (Claude Sonnet 4.5)
