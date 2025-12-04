# Dashboard V3 Issues & Rebuild Plan

## 🔍 Current State Audit (3 Dec 2025)

### Spreadsheet: 1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc

**Total Sheets**: 36 tabs

### ❌ Critical Issues Found

#### 1. **Missing Core Sheets**
- ❌ **Chart Data** - MISSING (required for buildDashboard() combo chart)
- ❌ **VLP_Data** - MISSING (backing data for VLP metrics)
- ❌ **ESO_Actions** - MISSING (ESO interventions table source)
- ❌ **Audit** - MISSING (logging dashboard rebuilds and errors)

#### 2. **Existing Sheets Status**
- ✅ **Dashboard** - EXISTS (but layout needs rebuild)
- ✅ **VLP Revenue** - EXISTS (known currency formatting bug in Settlement Period)
- ✅ **Market_Prices** - EXISTS
- ✅ **BESS** - EXISTS

#### 3. **Known VLP Revenue Issues**
- Settlement Period showing "£17.00" instead of "17" (fixed in Python but not redeployed)
- Charts may be duplicated or mispositioned
- Deprecated gspread API calls in source scripts

#### 4. **Chart Infrastructure Missing**
- No "Chart Data" sheet = `buildDashboard()` will fail
- Current dashboard has 12+ chart sheets (Chart_SO_Actions, Chart_Price_Correlation, etc.) but no unified Chart Data!A1:J49
- Combo chart with 8 series + dual axes NOT implemented

---

## 📋 Dashboard V3 Architecture (Target State)

### Sheet Structure

```
GB ENERGY DASHBOARD V3 (Spreadsheet)
├── Dashboard (main view)
│   ├── A1: ⚡ GB ENERGY DASHBOARD – REAL-TIME (orange banner)
│   ├── A2: Live Data timestamp formula
│   ├── B3: Time range dropdown (1 Year, 6 Months, etc.)
│   ├── A4-B5: Region filter + Live Gen vs Demand
│   ├── F9-H11: KPI bar (VLP Revenue, Wholesale Avg, Market Vol %)
│   ├── A9-E21: Fuel mix + Interconnectors table
│   ├── A24-H35: Active Outages table
│   ├── A37-F42: ESO Interventions table
│   └── L5: Combo chart (Chart Data!A1:J49)
│
├── Chart Data (NEW - must create)
│   ├── A: Time / Settlement Period
│   ├── B: DA Price (£/MWh)
│   ├── C: Imbalance Price (£/MWh)
│   ├── D: System Demand (MW)
│   ├── E: System Generation (MW)
│   ├── F: IC Net Flow (MW)
│   ├── G: BM Actions (MW)
│   ├── H: VLP Revenue (£k)
│   ├── I: Overlay 1 (dashed)
│   └── J: Overlay 2 (dashed)
│
├── VLP_Data (NEW - must create)
│   ├── From: v_btm_bess_inputs_unified (BigQuery)
│   ├── Columns: settlementDate, settlementPeriod, net_margin_per_mwh, 
│   │            ppa_discharge_revenue, dc_revenue, dm_revenue, cm_revenue, etc.
│   └── Refresh: Every 5 minutes via Railway Python
│
├── ESO_Actions (NEW - must create)
│   ├── From: bmrs_boalf (BigQuery)
│   ├── Columns: bmUnitId, acceptanceNumber, acceptanceTime, volume, 
│   │            cashflowAmount, action_type
│   └── Filter: Last 24 hours, >100 MW actions
│
├── Audit (NEW - must create)
│   ├── Columns: Action, Timestamp, User/Source, Status, Error
│   └── Logs: buildDashboard() calls, data refreshes, errors
│
└── Existing Sheets (keep)
    ├── BESS (battery analysis)
    ├── VLP Revenue (VLP dashboard - already working)
    ├── Market_Prices (price data)
    └── Chart_* (12 existing chart sheets - consolidate into Chart Data)
```

---

## 🎨 Design Specification

### Color Palette

```python
ORANGE     = {"red": 1.0,  "green": 0.64,  "blue": 0.3}    # #FFA24D - Title banner
BLUE       = {"red": 0.2,  "green": 0.404, "blue": 0.839}  # #3367D6 - KPI headers
LIGHT_BLUE = {"red": 0.89, "green": 0.95,  "blue": 0.99}   # #E3F2FD - Table headers
LIGHT_GREY = {"red": 0.93, "green": 0.93,  "blue": 0.93}   # #EEEEEE - Table rows
KPI_GREY   = {"red": 0.96, "green": 0.96,  "blue": 0.96}   # #F4F4F4 - KPI values
GREEN      = {"red": 0.18, "green": 0.49,  "blue": 0.20}   # #2E7D32 - IC imports
RED        = {"red": 0.78, "green": 0.16,  "blue": 0.16}   # #C62828 - IC exports / >500 MW
```

### Column Widths
- **A-E**: 150px (tables)
- **F-H**: 120px (KPIs)
- **I-Z**: Auto

### Frozen Rows/Columns
- **Rows**: 3 (title, timestamp, filters)
- **Columns**: 1 (row labels)

### Conditional Formatting Rules

#### 1. Interconnector Flow (Column E)
- **Green** (imports): `TEXT_CONTAINS "← Import"`
- **Red** (exports): `TEXT_CONTAINS "→ Export"`

#### 2. Active Outages (Column D: MW Lost)
- **Red + white bold**: `NUMBER_GREATER 500`

#### 3. ESO Interventions (Column C: MW)
- **Red + white bold**: `NUMBER_GREATER 500`

---

## 🛠️ Implementation Plan (15 Tasks)

### Phase 1: Infrastructure (Tasks 1-3)
**Goal**: Set up Railway + Python environment

1. ✅ **Railway Environment Setup**
   - Add env vars: `GCP_PROJECT_ID`, `GCP_DATASETS`, `GOOGLE_APPLICATION_CREDENTIALS`, `SPREADSHEET_ID`
   - Create `tools/inspect_bigquery_schema.py` 
   - Optional: OpenAI integration for schema analysis

2. ✅ **Python Layout Script**
   - Create `dashboard/layout_gb_energy_v3.py`
   - Implement `write_layout_values()` with all sections
   - Implement `apply_layout_formatting()` with color scheme

3. ✅ **Conditional Formatting**
   - Add IC flow rules (green/red)
   - Add >500 MW red flags for outages + ESO actions

### Phase 2: Chart Infrastructure (Tasks 4-6)
**Goal**: Implement buildDashboard() combo chart

4. ✅ **Apps Script buildDashboard()**
   - Create `apps-script/dashboard_combo_chart.gs`
   - 8 series: 0-1 price (line, right), 2-4 MW (area, left), 5-7 overlays (dashed, left)
   - Position at column L, row 5
   - Stamp audit log

5. ✅ **Python Combo Chart Builder** (alternative)
   - Add `rebuild_combo_chart()` to layout script
   - Use Sheets API `basicChart` spec
   - Match Apps Script functionality

6. ✅ **Chart Data Schema**
   - Define A-J columns (time, prices, MW metrics, overlays)
   - Document in `CHART_DATA_SCHEMA.md`
   - Create sample data generator

### Phase 3: Data Pipeline (Tasks 7-9)
**Goal**: Wire BigQuery → Google Sheets

7. ✅ **Backing Tab Population**
   - VLP_Data from `v_btm_bess_inputs_unified`
   - Market_Prices from `bmrs_mid_iris` + historical
   - ESO_Actions from `bmrs_boalf_iris`
   - BESS metrics (SoC, RTE, cycles)
   - Fuel_Mix from `bmrs_fuelinst_iris`
   - IC_Flows from interconnector tables

8. ✅ **Apps Script Menu**
   - Create `⚡ GB Energy` menu with:
     - 📊 Rebuild Chart → `buildDashboard()`
     - Toggle IC Overlay
     - Refresh Data
   - Multi-select dropdown handler for B3
   - Deploy via `clasp push`

9. ✅ **Audit Logging**
   - Create Audit sheet with: Action, Timestamp, User, Status, Error
   - Log from Python: layout updates, data refreshes, errors
   - Log from Apps Script: buildDashboard() calls, user actions

### Phase 4: Validation & Deployment (Tasks 10-12)
**Goal**: Test and deploy Dashboard V3

10. ✅ **Red Flag Formatting**
    - Active Outages >500 MW → red bg + white bold
    - ESO Interventions >500 MW → red bg + white bold
    - Test with sample data

11. ✅ **Integration Script**
    - Create `full_dashboard_rebuild.py`
    - Sequence: layout → format → chart → populate → validate
    - CLI args: `--spreadsheet-id`, `--mode` (layout-only | full-rebuild)

12. ✅ **Validation & Testing**
    - Run on `1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc`
    - Verify: all sections, KPIs, chart 8 series, conditional formatting
    - Document issues in `VALIDATION_RESULTS.md`

### Phase 5: Current Issues Cleanup (Tasks 13-15)
**Goal**: Fix "the mess" in existing spreadsheet

13. ✅ **Audit Current Spreadsheet**
    - Identify: missing sections, broken formulas, incorrect formatting
    - Check: duplicate charts, misaligned ranges, currency bugs
    - Output: `DASHBOARD_ISSUES.md` (this file)

14. ✅ **Railway Deployment**
    - Deploy Python scripts with cron:
      - Every 5 min: live data refresh
      - Every 30 min: full rebuild
    - Logging to Railway console
    - Health check endpoint

15. ✅ **Documentation**
    - Create `DASHBOARD_V3_ARCHITECTURE.md`
    - Cover: Railway + Python + Apps Script flow
    - Include: BigQuery schema, Chart Data spec, buildDashboard() flow
    - Add: troubleshooting guide

---

## 🚀 Quick Start: Fix The Mess

### Immediate Actions (Manual)

#### 1. Create Missing Sheets

```bash
cd /Users/georgemajor/GB-Power-Market-JJ
python3 << 'EOF'
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
gc = gspread.authorize(creds)
ss = gc.open_by_key(SPREADSHEET_ID)

# Create missing sheets
missing = ['Chart Data', 'VLP_Data', 'ESO_Actions', 'Audit']
for sheet_name in missing:
    try:
        ss.add_worksheet(title=sheet_name, rows=100, cols=20)
        print(f'✅ Created: {sheet_name}')
    except Exception as e:
        print(f'⚠️  {sheet_name}: {e}')
EOF
```

#### 2. Set Up Chart Data Headers

```python
chart_data = ss.worksheet('Chart Data')
headers = [
    'Time/SP', 'DA Price (£/MWh)', 'Imbalance Price (£/MWh)',
    'Demand (MW)', 'Generation (MW)', 'IC Flow (MW)',
    'BM Actions (MW)', 'VLP Revenue (£k)', 'Overlay 1', 'Overlay 2'
]
chart_data.update('A1:J1', [headers])
```

#### 3. Deploy Full Layout

```bash
# Option A: Run Python layout script
python3 dashboard/layout_gb_energy_v3.py

# Option B: Run full rebuild
python3 full_dashboard_rebuild.py --spreadsheet-id 1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc --mode full-rebuild
```

#### 4. Deploy Apps Script

```bash
cd apps-script
clasp push
# Then open Google Sheets → Extensions → Apps Script → Run onOpen()
```

---

## 📊 Chart Data Schema (A-J Columns)

### Column Definitions

| Column | Name | Type | Source | Purpose |
|--------|------|------|--------|---------|
| **A** | Time/SP | STRING | Settlement Period (P1-P50) | X-axis |
| **B** | DA Price | FLOAT | `bmrs_mid.systemSellPrice` | Line (right axis) |
| **C** | Imbalance Price | FLOAT | `bmrs_mid.imbalancePriceBuy` | Line (right axis) |
| **D** | Demand | FLOAT | `demand_outturn.demand` | Area (left axis) |
| **E** | Generation | FLOAT | SUM of `bmrs_fuelinst.generation` | Area (left axis) |
| **F** | IC Flow | FLOAT | Net interconnector flow | Area (left axis) |
| **G** | BM Actions | FLOAT | `bmrs_boalf.volume` | Line dashed (left axis) |
| **H** | VLP Revenue | FLOAT | `v_btm_bess_inputs_unified.net_margin_per_mwh` | Line dashed (left axis) |
| **I** | Overlay 1 | FLOAT | User toggle (e.g., wind forecast) | Line dashed (left axis) |
| **J** | Overlay 2 | FLOAT | User toggle (e.g., solar forecast) | Line dashed (left axis) |

### Sample Query (BigQuery → Chart Data)

```sql
WITH latest_48_periods AS (
  SELECT 
    CAST(settlementDate AS DATE) as date,
    settlementPeriod,
    CONCAT('P', CAST(settlementPeriod AS STRING)) as time_sp,
    systemSellPrice as da_price,
    imbalancePriceBuy as imbalance_price
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
  WHERE settlementDate >= CURRENT_DATE() - 2
  ORDER BY settlementDate DESC, settlementPeriod DESC
  LIMIT 48
),
demand_data AS (
  SELECT 
    CAST(demand_date AS DATE) as date,
    settlement_period,
    demand_mw as demand
  FROM `inner-cinema-476211-u9.uk_energy_prod.demand_outturn`
  WHERE demand_date >= CURRENT_DATE() - 2
),
generation_data AS (
  SELECT
    CAST(settlementDate AS DATE) as date,
    settlementPeriod,
    SUM(generation) as generation
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
  WHERE settlementDate >= CURRENT_DATE() - 2
  GROUP BY date, settlementPeriod
)
SELECT
  l.time_sp,
  l.da_price,
  l.imbalance_price,
  d.demand,
  g.generation,
  0 as ic_flow,  -- TODO: add IC table join
  0 as bm_actions,  -- TODO: add boalf join
  0 as vlp_revenue,  -- TODO: add VLP view join
  NULL as overlay1,
  NULL as overlay2
FROM latest_48_periods l
LEFT JOIN demand_data d ON l.date = d.date AND l.settlementPeriod = d.settlement_period
LEFT JOIN generation_data g ON l.date = g.date AND l.settlementPeriod = g.settlementPeriod
ORDER BY l.date, l.settlementPeriod
```

---

## 🔧 Troubleshooting

### Issue: buildDashboard() fails with "Chart Data not found"
**Solution**: Run step 1 & 2 from Quick Start to create Chart Data sheet with headers

### Issue: KPI formulas return #REF!
**Solution**: Verify VLP_Data and Market_Prices sheets exist and have data in columns C-D

### Issue: Combo chart shows blank
**Solution**: 
1. Check Chart Data has 48+ rows of data
2. Verify columns A-J have numeric values (not text)
3. Run `buildDashboard()` from Apps Script menu

### Issue: Settlement Period still shows "£1.00"
**Solution**: Redeploy `vlp_dashboard_python.py` with `str(int(...))` fix applied

### Issue: Conditional formatting not working
**Solution**: Check rules in Format → Conditional formatting → verify ranges match A9:E21, A24:H35, A37:F42

---

## 📈 Success Criteria

### ✅ Dashboard V3 Complete When:

1. **Structure**
   - ✅ All 4 missing sheets created (Chart Data, VLP_Data, ESO_Actions, Audit)
   - ✅ Dashboard layout matches spec (title, filters, KPIs, tables, chart)
   - ✅ Column widths and frozen rows/cols set

2. **Functionality**
   - ✅ buildDashboard() creates combo chart with 8 series + dual axes
   - ✅ KPIs calculate from live data
   - ✅ Tables populate from backing sheets via formulas
   - ✅ Conditional formatting highlights IC flows and >500 MW events

3. **Data Pipeline**
   - ✅ Railway Python updates VLP_Data, Market_Prices, ESO_Actions every 5 min
   - ✅ Chart Data populates from BigQuery with 48 periods
   - ✅ Audit log records all refreshes and errors

4. **User Experience**
   - ✅ "⚡ GB Energy" menu with Rebuild Chart, Toggle Overlays, Refresh Data
   - ✅ Time range dropdown in B3 filters chart
   - ✅ No currency formatting bugs (e.g., Settlement Period)
   - ✅ Professional color scheme (orange, blue, grey) applied

---

## 📚 Related Documentation

- `PROJECT_CONFIGURATION.md` - BigQuery project settings
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Data schema reference
- `PRICING_DATA_ARCHITECTURE.md` - IRIS pricing architecture
- `VLP_DASHBOARD_DEPLOYMENT.md` - VLP Revenue sheet (working example)
- `APPS_SCRIPT_GUIDE.md` - Apps Script setup with CLASP

---

**Last Updated**: 3 December 2025  
**Status**: 🔴 Dashboard V3 not deployed - 4 missing sheets, chart infrastructure incomplete  
**Next Action**: Create missing sheets → deploy Python layout → test buildDashboard()
