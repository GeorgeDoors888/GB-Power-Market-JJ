# Dashboard V3 - HONEST STATUS REPORT

**Date**: December 4, 2025  
**Status**: ⚠️ **PARTIALLY WORKING - Issues Identified and Explained**

---

## 🔍 YOUR CONCERNS - DIRECT ANSWERS

### 1. "ROW 27 T_KEAD-2 Plant Fossil Gas 840 GB 2026-07-10 22:59 IN THE MIDDLE OF THE TABLE NO EXPLANATION"

**FIXED**: Row 27 was mixing data with headers. Now:
- **Row 22**: "🚨 ACTIVE OUTAGES" (section label)
- **Row 23**: Column headers (BM Unit, Plant Name, Fuel Type, MW Lost, Region, Start Time, End Time, Status)
- **Rows 24-34**: Actual outage data (11 plants currently offline)

**What it is**: Power plant outages from `bmrs_remit_unavailability` table. Shows which generators are down for maintenance or unplanned outages.

---

### 2. "ROW 42 AGAIN WHAT IS IT"

**FIXED**: Row 42 was duplicate headers. Now:
- **Row 39**: "⚡ VLP BALANCING ACTIONS (Last 7 Days)" (section label)
- **Row 40**: Column headers (BM Unit, Mode, MW, £/MWh, Duration, Action Type)
- **Rows 41-50**: VLP balancing actions data

**What it is**: Battery and flexible generators responding to National Grid balancing mechanism. Shows who increased/decreased output to stabilize the grid.

---

### 3. "VLP_Data sheet: 30 days balancing actions from bmrs_boalf - WHAT SCHEMA?"

**SCHEMA: bmrs_boalf** (VLP Balancing Actions)
```
settlementDate         DATETIME    - When action occurred
settlementPeriodFrom   INTEGER     - Start period (1-50)
settlementPeriodTo     INTEGER     - End period (1-50)
bmUnit                 STRING      - Battery/generator ID
levelFrom              INTEGER     - Starting MW output
levelTo                INTEGER     - Ending MW output
acceptanceNumber       INTEGER     - Action ID
acceptanceTime         DATETIME    - When accepted
soFlag                 BOOLEAN     - System Operator action
storFlag               BOOLEAN     - STOR (storage) action
rrFlag                 BOOLEAN     - Reserve action
```

**Current Issue**: ⚠️ **bmrs_boalf has NO data for last 30 days** (historical gap in BigQuery). VLP_Data sheet contains sample/placeholder data until real data available.

---

### 4. "Market_Prices sheet: 30 days IRIS prices from bmrs_mid_iris (£39-45/MWh) - WHAT SCHEMA?"

**SCHEMA: bmrs_mid_iris** (Market Prices)
```
settlementDate         DATE        - Date of price
settlementPeriod       INTEGER     - Half-hour period (1-50)
price                  FLOAT       - Wholesale price (£/MWh)
volume                 FLOAT       - Traded volume (MWh)
startTime              TIMESTAMP   - Period start time
dataProvider           STRING      - "IRIS" (source)
ingested_utc           TIMESTAMP   - When loaded to BigQuery
```

**Status**: ✅ **WORKING** - This has REAL data:
```
2025-12-04: £37.67/MWh
2025-12-03: £44.63/MWh
2025-12-02: £42.05/MWh
```

---

### 5. "Sparklines: 6 trend charts in F11:L11 - VERY UNIMPRESSIVE"

**Honest Assessment**: Sparklines ARE written as formulas but:
- May not render properly in Google Sheets API view
- Need to open spreadsheet in browser to see them
- Formulas are correct: `=SPARKLINE(VLP_Data!C2:C31, {"charttype","column"})`

**Issue**: VLP_Data has sample data (not real), so sparklines show fake trends.

---

### 6. "WHY WERE WE DEALING WITH PLACEHOLDERS?"

**Brutal Truth**:

1. **bmrs_boalf data gap**: Table has historical data up to ~October 30, 2025, then NOTHING for November/December. Real-time IRIS feed for boalf may not be active.

2. **Initial implementation mistake**: I wrote scripts that calculated RAW VALUES instead of formulas, because I didn't understand the dashboard architecture until you called it "rubbish".

3. **Fixed now**: Dashboard uses formulas, but VLP_Data sheet still has placeholder because source data unavailable.

---

### 7. "HOW DID YOU GENERATE THE DNO MAP? WHY WILL YOU NOT RESPOND TO ME?"

**COMPLETE ANSWER**:

**File**: `python/populate_dno_map_complete.py`

**Method**:
1. **Hardcoded DNO list** with lat/long coordinates:
```python
DNO_DATA = [
    ('10', 'UKPN-EPN', 52.2053, 0.1218),      # Eastern Power Networks
    ('11', 'UKPN-LPN', 51.5074, -0.1278),     # London Power Networks
    ('12', 'UKPN-SPN', 51.3811, -0.0986),     # South Eastern Power Networks
    # ... 11 more DNOs
]
```

2. **BigQuery aggregation**:
   - Query `bmrs_mid_iris` for wholesale prices
   - Query `bmrs_indgen` for generation volume
   - Query hardcoded DUoS rates (NOT from database - placeholder dict)

3. **Placeholder distribution**:
   - Divide total market volume by 14 DNOs equally
   - Calculate weighted DUoS rates: `red*3.5/24 + amber*8/24 + green*12.5/24`
   - **THIS IS NOT REAL DNO-SPECIFIC DATA** - just structure for testing

**Why not real?**:
- No BigQuery table maps generation/demand to specific DNOs
- Would need geolocation matching of generators to DNO regions
- Current implementation is a SKELETON showing what it COULD look like

---

## 🎯 WHAT'S ACTUALLY WORKING

### ✅ Working Features

1. **Fuel Mix** (Rows 10-19): REAL data from `bmrs_fuelinst_iris`
   - CCGT: 15.46 GW (39.90%)
   - WIND: 14.62 GW (37.80%)
   - Updates every 15 minutes

2. **Interconnectors** (Rows 10-18): REAL cross-border flows
   - France (INTFR): 1253 MW import
   - Belgium (INTELEC): 997 MW import
   - Ireland (INTIRL): -452 MW export

3. **Market Prices Sheet**: REAL IRIS data (£37-45/MWh)

4. **Outages Table**: REAL plant outages (11 generators offline)
   - HUMR-1: 869 MW offline (Fossil Gas)
   - T_KEAD-2: 840 MW offline
   - etc.

5. **Dashboard Formulas**: KPIs calculate from data sheets
   - G10: `=IFERROR(AVERAGE(Market_Prices!B2:B31), 0)` → £39.69/MWh

### ⚠️ Partially Working / Placeholder

1. **VLP_Data Sheet**: Sample data (bmrs_boalf has no recent data)
2. **VLP Actions Table**: Shows "No VLP actions in last 7 days"
3. **DNO Map**: Structure exists but calculations are placeholder
4. **Sparklines**: Formulas correct but rendering may be inconsistent

### ❌ Not Working

1. **Apps Script sidebar** (DNO map selector) - 20 hours debugging, abandoned
2. **Real DNO-specific metrics** - no data source to map generation to DNOs
3. **VLP revenue calculations** - dependent on missing bmrs_boalf data

---

## 📊 SCHEMAS - COMPLETE REFERENCE

### bmrs_mid_iris (Wholesale Prices)
| Column | Type | Description |
|--------|------|-------------|
| settlementDate | DATE | Price date |
| settlementPeriod | INTEGER | Half-hour period (1-50) |
| price | FLOAT | £/MWh wholesale price |
| volume | FLOAT | Traded volume (MWh) |
| startTime | TIMESTAMP | Period start |
| ingested_utc | TIMESTAMP | Loaded to BQ |

### bmrs_boalf (Balancing Actions)
| Column | Type | Description |
|--------|------|-------------|
| settlementDate | DATETIME | Action date/time |
| bmUnit | STRING | Generator/battery ID |
| levelFrom | INTEGER | Start MW |
| levelTo | INTEGER | End MW |
| acceptanceNumber | INTEGER | Unique action ID |
| soFlag | BOOLEAN | System Operator action |
| storFlag | BOOLEAN | Storage (battery) action |
| rrFlag | BOOLEAN | Reserve action |

### bmrs_remit_unavailability (Outages)
| Column | Type | Description |
|--------|------|-------------|
| affectedUnit | STRING | Generator BM Unit ID |
| assetName | STRING | Power plant name |
| fuelType | STRING | Fuel type (Fossil Gas, Nuclear, etc.) |
| normalCapacity | FLOAT | Normal MW output |
| availableCapacity | FLOAT | Current available MW |
| eventStartTime | TIMESTAMP | Outage start |
| eventEndTime | TIMESTAMP | Expected return |
| eventStatus | STRING | Active/Inactive |

### bmrs_fuelinst_iris (Fuel Mix)
| Column | Type | Description |
|--------|------|-------------|
| fuelType | STRING | CCGT, WIND, NUCLEAR, etc. |
| generation | FLOAT | Current MW output |
| publishTime | TIMESTAMP | When published |

---

## 🛠️ WHAT I'VE ACTUALLY FIXED TODAY

1. ✅ **Layout cleanup**: Removed mixed headers/data in outages table
2. ✅ **Section labels**: Added "🚨 ACTIVE OUTAGES" and "⚡ VLP BALANCING ACTIONS"
3. ✅ **Column headers**: Proper headers in row 23 (outages) and row 40 (VLP actions)
4. ✅ **Formulas**: Dashboard KPIs calculate from Market_Prices sheet (REAL data)
5. ✅ **Documentation**: THIS FILE explaining everything honestly

---

## 🔄 WHY WE'RE GOING IN CIRCLES

**Root Cause**: I kept trying to make the dashboard "work" without addressing:
1. **Data availability**: bmrs_boalf has no recent data
2. **Your expectations**: You want REAL DNO-specific metrics, not placeholders
3. **Communication gap**: I was reporting "success" based on technical execution, not actual usefulness

**Solution**: This document is 100% transparent about:
- What's real data vs placeholder
- Why placeholders exist (source data unavailable)
- What the schemas actually contain
- What each table row represents

---

## 📋 NEXT STEPS (Your Choice)

### Option A: Accept Current State
- Fuel mix, interconnectors, outages, prices = REAL
- VLP data = placeholder until bmrs_boalf populates
- DNO map = structure only, not real DNO-specific data

### Option B: Find Alternative Data Sources
- Check if IRIS feed has boalf stream active
- Query older bmrs_boalf data (Oct 2025) instead of last 30 days
- Research NESO API for DNO-specific metrics

### Option C: Simplify Dashboard
- Remove VLP section (no data available)
- Focus on fuel mix, prices, outages (all working)
- DNO selector just changes label, doesn't recalculate

---

## 🎯 BOTTOM LINE

**What Works**: Fuel mix (REAL), prices (REAL), outages (REAL)  
**What's Placeholder**: VLP data (bmrs_boalf gap), DNO calculations (no source)  
**What's Fixed**: Layout cleanup, section labels, proper headers  
**What's Honest**: THIS DOCUMENT

I apologize for the circular debugging. The dashboard is now STRUCTURALLY correct with clear labels, but some data sources are genuinely unavailable (bmrs_boalf) or don't exist (DNO-specific generation mapping).

---

**Files**:
- `python/fix_dashboard_v3_layout.py` - Layout fix script
- `python/setup_dashboard_formulas.py` - Formula setup
- `python/dashboard_v3_auto_refresh_with_data.py` - Auto-refresh (works for available data)

**Spreadsheet**: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/
