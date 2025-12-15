# VLP Revenue Engine Implementation Guide

**Date**: 5 December 2025  
**Status**: Ready for Implementation  
**Priority**: High

## Executive Summary

This guide provides step-by-step instructions for implementing a comprehensive VLP (Virtual Lead Party) revenue engine with:
- **BigQuery view** combining 6 revenue streams (BM, ESO, CM, DSO, PPA, Avoided Import)
- **Python optimizer** for BESS+CHP dispatch decisions with SoC tracking
- **Google Sheets dashboard** with revenue breakdown, margin allocation, and visualization charts

**Total Complexity**: 26 todo items (17 core + 3 optional enhancements + 6 validation/documentation)  
**Estimated Time**: 2-3 days for core implementation + 1 day for optional features  
**Dependencies**: BigQuery, Google Sheets API, Python 3.8+, inner-cinema-credentials.json

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                             │
├─────────────────────────────────────────────────────────────────┤
│ bmrs_boalf │ bmrs_costs │ ESO services │ CM data │ Site meters │
└───────┬─────────────────────────────────────────────────────┬───┘
        │                                                     │
        v                                                     v
┌─────────────────────────────────────────────────────────────────┐
│           BigQuery View: v_vlp_site_revenue_stack                │
│  • Combines all inputs per settlement period                    │
│  • Computes 6 revenue streams (r_bm, r_eso, r_cm, r_ppa, etc.)  │
│  • Applies DUoS bands (RED/AMBER/GREEN) and levies              │
│  • Calculates import costs and fuel costs                       │
└───────┬─────────────────────────────────────────────────────────┘
        │
        v
┌─────────────────────────────────────────────────────────────────┐
│           Python Engine: vlp_revenue_engine.py                   │
│  • fetch_vlp_inputs(): Read BigQuery view                       │
│  • optimise_bess_chp(): Per-SP optimizer                        │
│    - Battery: charge/discharge/idle decisions                   │
│    - CHP: run/off decisions                                     │
│    - SoC tracking (2.5 MWh initial, 0.25-5.0 MWh bounds)        │
│  • Split margins: 70% site / 30% VLP                            │
│  • write_dashboard(): Update Google Sheets                      │
└───────┬─────────────────────────────────────────────────────────┘
        │
        v
┌─────────────────────────────────────────────────────────────────┐
│              Google Sheets Dashboard                             │
│  • BESS worksheet: Full time series (soc, actions, margins)     │
│  • Dashboard worksheet: KPIs + 4 charts                         │
│    - Chart 1: Revenue stack (stacked column)                    │
│    - Chart 2: SoC over time (line)                              │
│    - Chart 3: Battery actions (column)                          │
│    - Chart 4: Per-SP gross margin (area line)                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Prerequisites (Todos #1-2)

### Todo #1: Gather Configuration Information

Before starting implementation, collect:

1. **BMU IDs** (replace placeholders in SQL):
   - Battery BMU: `'X_BAT01'` → Your actual sBMU ID (e.g., `'FBPGM002'`)
   - CHP BMU: `'X_CHP01'` → Your actual sBMU ID (e.g., `'XXCHP001'`)
   - **How to find**: Query `bmrs_boalf` for your site's BMUs:
     ```sql
     SELECT DISTINCT bmUnit 
     FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
     WHERE bmUnit LIKE '%YOUR_SITE%'
     ORDER BY bmUnit
     ```

2. **Battery Specification** (confirm which to use):
   - **Option A**: 2.5 MW power / 5.0 MWh capacity (from new VLP spec)
   - **Option B**: 25 MW power / 50 MWh capacity (from earlier three-tier analysis)
   - **Impact**: Optimizer dynamics, revenue projections, SoC cycling all scale 10x
   - **Recommendation**: Use Option A (2.5 MW) unless you have actual 25 MW battery

3. **Site ID(s)**:
   - Identifier for your VLP site (e.g., `'SITE_001'`, `'Flexgen_Battery_01'`)
   - Used in `site_metered_flows` and `capacity_market_site` tables

4. **Spreadsheet ID**:
   - Default: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA` (existing dashboard)
   - Or: Create new spreadsheet and use its ID
   - Update `SPREADSHEET_ID` in `vlp_revenue_engine.py`

**Record values here**:
```
BMU_BATTERY = "____________"
BMU_CHP = "____________"
BATTERY_POWER_MW = ______
BATTERY_ENERGY_MWH = ______
SITE_ID = "____________"
SPREADSHEET_ID = "____________"
```

### Todo #2: Verify BigQuery Tables

Check which tables exist in your dataset:

```bash
# List all tables
bq ls inner-cinema-476211-u9:uk_energy_prod

# Check specific tables
bq show inner-cinema-476211-u9:uk_energy_prod.bmrs_boalf
bq show inner-cinema-476211-u9:uk_energy_prod.bmrs_costs
```

Search for ESO/CM tables (names may vary):
```bash
# Look for ESO services table
bq ls inner-cinema-476211-u9:uk_energy_prod | grep -i "eso\|service\|dc"

# Look for Capacity Market table
bq ls inner-cinema-476211-u9:uk_energy_prod | grep -i "cm\|capacity"

# Check if site metered flows exists (likely not)
bq show inner-cinema-476211-u9:uk_energy_prod.site_metered_flows
```

**Expected Results**:
- ✅ `bmrs_boalf` - exists (391M+ rows)
- ✅ `bmrs_costs` - exists (deduplicated after Oct 29)
- ❓ `esoservices_dc_site` - likely needs creation
- ❓ `capacity_market_site` - likely needs creation
- ❌ `site_metered_flows` - **definitely needs creation**

---

## Phase 2: Data Preparation (Todos #3-5)

### Todo #3: Create site_metered_flows Table

This is the **most critical dependency** - without it, the view won't work.

**Option A: Derive from Existing HH Data** (if you have metering system):
```python
# create_site_metered_flows.py
from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
client = bigquery.Client(project=PROJECT_ID)

# Adapt this query to your actual HH meter data structure
sql = """
CREATE OR REPLACE TABLE `{}.{}.site_metered_flows` AS
SELECT
  CAST(settlement_date AS DATE) AS settlementDate,
  settlement_period AS settlementPeriod,
  'SITE_001' AS site_id,  -- Replace with your site ID
  
  -- Adapt these columns to your meter data
  battery_import_mwh AS batt_charge_mwh,
  battery_export_mwh AS batt_discharge_mwh,
  chp_export_mwh,
  chp_onsite_mwh,
  grid_import_mwh AS site_import_mwh,
  total_load_mwh AS site_load_mwh,
  chp_fuel_input_mwh_thermal AS chp_fuel_mwh_th
  
FROM `{}.{}.YOUR_HH_METER_TABLE`
WHERE settlement_date >= '2025-01-01'
""".format(PROJECT_ID, DATASET, PROJECT_ID, DATASET)

job = client.query(sql)
job.result()
print("✅ site_metered_flows table created")
```

**Option B: Create Stub Table for Testing** (if no real data yet):
```sql
CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_prod.site_metered_flows` AS
SELECT
  c.settlementDate,
  c.settlementPeriod,
  'SITE_001' AS site_id,
  
  -- Stub values (replace with real data later)
  0.5 AS batt_charge_mwh,      -- ~1 MW charging
  0.8 AS batt_discharge_mwh,   -- ~1.6 MW discharging
  0.3 AS chp_export_mwh,       -- CHP exports 0.3 MWh
  0.4 AS chp_onsite_mwh,       -- CHP serves 0.4 MWh onsite
  0.2 AS site_import_mwh,      -- Grid import 0.2 MWh
  1.0 AS site_load_mwh,        -- Total load 1.0 MWh
  1.75 AS chp_fuel_mwh_th      -- Fuel input (thermal)
  
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs` c
WHERE c.settlementDate >= '2025-10-17'
  AND c.settlementDate <= '2025-10-23'
```

**Validation**:
```sql
SELECT 
  COUNT(*) as rows,
  MIN(settlementDate) as earliest,
  MAX(settlementDate) as latest,
  AVG(batt_charge_mwh) as avg_charge,
  AVG(batt_discharge_mwh) as avg_discharge
FROM `inner-cinema-476211-u9.uk_energy_prod.site_metered_flows`
```

### Todo #4: Create ESO Services Table

```sql
CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_prod.esoservices_dc_site` AS
SELECT
  c.settlementDate,
  c.settlementPeriod,
  
  -- Dynamic Containment (DC) - replace with actual contract values
  2.0 AS dc_avail_mw,                    -- 2 MW DC availability
  9.0 AS dc_price_avail_gbp_per_mw_h,    -- £9/MW/h availability price
  0.5 AS dc_util_mwh,                    -- 0.5 MWh utilization
  50.0 AS dc_price_util_gbp_per_mwh      -- £50/MWh utilization price
  
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs` c
WHERE c.settlementDate >= '2025-10-17'
  AND c.settlementDate <= '2025-10-23'
```

**Note**: If you have actual ESO service contracts, replace stub values with:
- Contract availability (MW) per SP
- Availability price (£/MW/h) from contract
- Actual utilization (MWh) from ESO dispatch data
- Utilization price (£/MWh) from contract

### Todo #5: Create Capacity Market Table

```sql
CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_prod.capacity_market_site` AS
SELECT
  'SITE_001' AS site_id,
  15.0 AS cm_price_gbp_per_kw_year,        -- £15/kW/year (2026/27 clearing price)
  24000.0 AS derated_kw,                    -- 24 MW de-rated capacity
  50000.0 AS expected_dispatched_mwh_year   -- Expected annual discharge
```

**Explanation**:
- `cm_price_gbp_per_kw_year`: T-4 auction clearing price (£15/kW/year typical for 2026/27)
- `derated_kw`: Battery capacity after de-rating factors (24 MW = 24,000 kW)
- `expected_dispatched_mwh_year`: Annual discharge estimate for per-MWh allocation

**Revenue calculation**:
- Annual CM revenue = £15/kW/year × 24,000 kW = £360,000/year
- Per-MWh equivalent = £360,000 / 50,000 MWh = £7.20/MWh

---

## Phase 3: BigQuery View Creation (Todos #6-7)

### Todo #6: Create v_vlp_site_revenue_stack View

1. Open BigQuery console or create Python script:

```python
# create_vlp_view.py
from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
client = bigquery.Client(project=PROJECT_ID)

# Read SQL from file or paste the CREATE VIEW statement from user
with open('v_vlp_site_revenue_stack.sql', 'r') as f:
    sql = f.read()

# CRITICAL: Replace placeholders
sql = sql.replace("'X_BAT01'", "'FBPGM002'")  # Your battery BMU
sql = sql.replace("'X_CHP01'", "'XXCHP001'")  # Your CHP BMU

# Execute
job = client.query(sql)
job.result()
print("✅ View v_vlp_site_revenue_stack created successfully")
```

2. **Manual verification in BigQuery console**:
   - Navigate to `inner-cinema-476211-u9.uk_energy_prod`
   - Confirm `v_vlp_site_revenue_stack` appears in table list (with view icon)

### Todo #7: Test BigQuery View

```sql
-- Basic validation
SELECT 
  COUNT(*) as row_count,
  MIN(ts_halfhour) as earliest,
  MAX(ts_halfhour) as latest,
  AVG(wholesale_price_gbp_per_mwh) as avg_wholesale_price,
  AVG(import_cost_gbp_per_mwh) as avg_import_cost,
  SUM(r_bm_gbp) as total_bm_revenue,
  SUM(r_eso_gbp) as total_eso_revenue,
  SUM(r_cm_gbp) as total_cm_revenue,
  SUM(r_ppa_gbp) as total_ppa_revenue,
  SUM(r_avoided_import_gbp) as total_avoided_import,
  SUM(r_dso_gbp) as total_dso_revenue
FROM `inner-cinema-476211-u9.uk_energy_prod.v_vlp_site_revenue_stack`
```

**Expected Results** (7-day period Oct 17-23):
- `row_count`: 336 (7 days × 48 SP/day)
- `avg_wholesale_price`: £40-80/MWh
- `total_bm_revenue`: Should be non-zero if BMU IDs correct
- `total_ppa_revenue`: Should be non-zero (depends on discharge amounts)

**If results look wrong**:
- All revenues zero → Check BMU IDs in `bmrs_boalf` query (todo #1)
- NULL values → Check table JOINs (todos #3-5)
- Row count zero → Check date range in source tables

---

## Phase 4: Python Engine Implementation (Todos #8-12)

### Todo #8: Create vlp_revenue_engine.py

Save the Python code provided by user as `vlp_revenue_engine.py`, then update configuration:

```python
# At top of file (lines 25-32), update:
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
VIEW = "v_vlp_site_revenue_stack"
SERVICE_ACCOUNT_FILE = "inner-cinema-credentials.json"
SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"  # From todo #1

# Battery parameters (lines 34-39) - confirm with todo #1
BATTERY_POWER_MW = 2.5      # Or 25.0 if using larger battery
BATTERY_ENERGY_MWH = 5.0    # Or 50.0 if using larger battery
EFFICIENCY = 0.85
SOC_MIN = 0.05 * BATTERY_ENERGY_MWH  # 5% minimum (0.25 MWh for 5 MWh battery)
SOC_MAX = BATTERY_ENERGY_MWH
INITIAL_SOC = 2.5           # Starting SoC (MWh) - adjust if needed

# CHP parameters (lines 41-45)
CHP_MAX_MW = 2.0
CHP_MIN_MW = 0.0
CHP_EFF_EL = 0.40           # 40% electrical efficiency
CHP_FUEL_COST_GBP_PER_MWH_TH = 20.0  # £20/MWh thermal (must match view)

# Opex and splits (lines 47-49)
FIXED_OPEX_SITE_GBP = 100_000.0      # £100k fixed opex (adjust to actual)
VARIABLE_OPEX_PER_MWH_GBP = 3.0      # £3/MWh variable (currently unused)
SITE_SHARE = 0.7                      # 70% site / 30% VLP split
```

### Todo #9: Fix Authentication

**Issue**: Earlier troubleshooting showed `gspread.Credentials` fails with "No access token" error, but `oauth2client.ServiceAccountCredentials` works.

**Solution**: Replace `make_gs_client()` function (lines 57-65):

```python
# BEFORE (doesn't work):
from google.oauth2.service_account import Credentials
def make_gs_client():
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE,
        scopes=[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    return gspread.authorize(creds)

# AFTER (working authentication from earlier session):
from oauth2client.service_account import ServiceAccountCredentials
def make_gs_client():
    scope = [
        'https://spreadsheets.google.com/feeds',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        SERVICE_ACCOUNT_FILE,
        scope
    )
    return gspread.authorize(creds)
```

**Also update imports** (line 12):
```python
# Remove:
# from google.oauth2.service_account import Credentials

# Add:
from oauth2client.service_account import ServiceAccountCredentials
```

**Install missing dependency**:
```bash
pip3 install --user oauth2client
```

### Todo #10: Test fetch_vlp_inputs()

```bash
python3 -c "
from vlp_revenue_engine import fetch_vlp_inputs
df = fetch_vlp_inputs()
print(f'✅ Loaded {len(df)} rows')
print(f'Columns: {df.columns.tolist()[:10]}...')  # First 10 columns
print(f'Date range: {df[\"ts_halfhour\"].min()} to {df[\"ts_halfhour\"].max()}')
print(df.head())
"
```

**Expected Output**:
```
✅ Loaded 336 rows
Columns: ['ts_halfhour', 'settlementDate', 'settlementPeriod', 'site_id', ...]
Date range: 2025-10-17 00:00:00 to 2025-10-23 23:30:00
   ts_halfhour  settlementDate  settlementPeriod  wholesale_price_gbp_per_mwh  ...
```

**If errors**:
- "No module named 'oauth2client'" → Run `pip3 install --user oauth2client`
- "Table not found" → View not created yet (todo #6)
- "Access Denied" → Check credentials file exists: `ls -la inner-cinema-credentials.json`

### Todo #11: Test Optimizer (Small Dataset)

Modify `main()` function to test 1 day first:

```python
# In vlp_revenue_engine.py, modify fetch_vlp_inputs():
def fetch_vlp_inputs() -> pd.DataFrame:
    client = make_bq_client()
    sql = f"""
    SELECT *
    FROM `{PROJECT_ID}.{DATASET}.{VIEW}`
    WHERE settlementDate = '2025-12-04'  -- TEST: 1 day only (48 SPs)
    ORDER BY ts_halfhour
    """
    df = client.query(sql).to_dataframe()
    return df
```

Run optimizer:
```bash
python3 vlp_revenue_engine.py
```

**Expected Output**:
```
Total gross margin: £3,245
Site margin:         £2,171
VLP margin:          £973
```

**Validation Checks**:
1. **SoC stays within bounds**: Check BESS sheet, `soc_end` column should be 0.25 to 5.0 MWh
2. **Battery actions make sense**: During high-price RED periods (SP 33-39), `batt_action='DISCHARGE'`
3. **CHP logic**: If `margin_chp_ppa_per_mwh > 0`, then `chp_action='RUN'`
4. **No crashes**: Script completes without errors

### Todo #12: Validate Optimizer Logic

Pick a specific high-price settlement period and manually verify:

```python
# Add debug output to optimise_bess_chp() for SP 35 (17:00-17:30):
for idx, row in df.iterrows():
    if row['settlementPeriod'] == 35:  # RED period
        print(f"DEBUG SP {row['settlementPeriod']}:")
        print(f"  Import cost: £{import_cost:.2f}/MWh")
        print(f"  PPA price: £{ppa_price:.2f}/MWh")
        print(f"  CM per MWh: £{row['cm_revenue_gbp_per_mwh_eq']:.2f}/MWh")
        print(f"  Unit value discharge: £{unit_value_discharge:.2f}/MWh")
        print(f"  Battery cost: £{c_batt:.2f}/MWh")
        print(f"  Margin discharge: £{margin_batt_discharge_per_mwh:.2f}/MWh")
        print(f"  SoC before: {soc:.2f} MWh")
        print(f"  Action: {batt_action}, Discharge: {batt_discharge_mwh:.2f} MWh")
        print(f"  SoC after: {rec['soc_end']:.2f} MWh")
        print(f"  Gross margin: £{gross_margin_sp:.2f}")
```

**Expected RED Period Behavior** (SP 33-39, 16:00-19:30):
- `import_cost`: ~£125/MWh (wholesale £80 + DUoS £17.64 + levies £98.15)
- `margin_batt_discharge_per_mwh`: **POSITIVE** (PPA £150 + CM £7 > cost £147)
- `batt_action`: **DISCHARGE**
- `soc_end`: Decreases by discharge amount

**Expected GREEN Period Behavior** (SP 1-16, 00:00-08:00):
- `import_cost`: ~£55/MWh (wholesale £35 + DUoS £0.11 + levies £98.15)
- `margin_import_ppa_per_mwh`: **POSITIVE** (PPA £150 > cost £55)
- `batt_action`: **CHARGE** (if SoC < SOC_MAX)
- `soc_end`: Increases by charge amount

---

## Phase 5: Dashboard Creation (Todos #13-18)

### Todo #13: Prepare Dashboard Layout

1. Open spreadsheet: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

2. Navigate to **Dashboard** worksheet (create if doesn't exist)

3. Clear rows 1-100 to prepare for new layout

4. Manually set headers (script will populate data):
   - A1: `VLP Site – BESS & CHP Value Stack`
   - A2: `Total Gross Margin (£/period sum)`
   - A3: `Site vs VLP Split`
   - A4: `Revenue Line`
   - B4: `Value (£/period sum)`
   - D4: `Total Gross Margin`
   - D5: `Site Margin (after fixed Opex)`
   - D6: `VLP Margin`

### Todo #14: Test write_dashboard()

Remove date filter from `fetch_vlp_inputs()` (restore full query), then run:

```bash
python3 vlp_revenue_engine.py
```

**Verify Google Sheets Updates**:

1. **BESS Worksheet** (new or updated):
   - Row 1: Headers (`ts_halfhour`, `settlementDate`, `settlementPeriod`, ..., `soc_start`, `soc_end`, `batt_action`, `batt_charge_mwh_opt`, `batt_discharge_mwh_opt`, `chp_action`, `chp_elec_mwh_opt`, `gross_margin_sp_gbp`)
   - Rows 2+: Full time series data (336 rows for 7-day period)

2. **Dashboard Worksheet**:
   - A5: `BM revenue` | B5: £XXX (sum of `r_bm_gbp`)
   - A6: `ESO revenue` | B6: £XXX
   - A7: `CM revenue` | B7: £XXX
   - A8: `DSO revenue` | B8: £0 (placeholder)
   - A9: `PPA export revenue` | B9: £XXX
   - A10: `Avoided import value` | B10: £XXX
   - D4: £XXX (total gross margin)
   - D5: £XXX (site margin after £100k opex)
   - D6: £XXX (VLP margin = 30% of gross)
   - A99: `Last Updated: 2025-12-05 14:30:45`

**Troubleshooting**:
- "Worksheet BESS not found" → Script creates it automatically
- "Worksheet Dashboard not found" → Create Dashboard worksheet manually first
- Authentication error → Check todo #9 implemented correctly

### Todo #15-18: Create Dashboard Charts

**Chart 1: Revenue Stack (Stacked Column)**
1. Select Dashboard A5:B10
2. Insert → Chart
3. Chart type: Stacked column chart
4. Position: Move chart to E4:J18
5. Customize:
   - Title: "VLP Revenue Stack (£)"
   - Vertical axis: "Revenue (£)"
   - Legend: Show (right side)
   - Colors: Assign distinct colors to each series

**Chart 2: SoC Over Time (Line Chart)**
1. Switch to BESS worksheet
2. Select columns: A (ts_halfhour) + column with `soc_end` (find position after script run)
3. Insert → Chart → Line chart
4. Position: Move to Dashboard E20:J30
5. Customize:
   - Title: "Battery State of Charge (MWh)"
   - X-axis: "Time"
   - Y-axis: "SoC (MWh)", range 0-5
   - Line: Smooth curve

**Chart 3: Battery Actions (Column Chart)**
1. In BESS worksheet, select:
   - Column A (ts_halfhour)
   - Column with `batt_charge_mwh_opt`
   - Column with `batt_discharge_mwh_opt`
2. Insert → Chart → Column chart
3. Position: Move to Dashboard E32:J42
4. Customize:
   - Title: "Battery Charge/Discharge Actions (MWh)"
   - Series 1 (charge): Red color
   - Series 2 (discharge): Green color
   - Y-axis: "MWh"

**Chart 4: Per-SP Gross Margin (Area Line Chart)**
1. In BESS worksheet, select:
   - Column A (ts_halfhour)
   - Column with `gross_margin_sp_gbp`
2. Insert → Chart → Area chart
3. Position: Move to Dashboard E44:J54
4. Customize:
   - Title: "Gross Margin per Settlement Period (£)"
   - Y-axis: "Margin (£)"
   - Add horizontal line at 0 (reference line)
   - Fill area with transparency

---

## Phase 6: Validation & Testing (Todos #19-22)

### Todo #19: Full-Period Run (7 Days)

Test with realistic timeframe (high-price event Oct 17-23):

```python
# In fetch_vlp_inputs(), modify WHERE clause:
WHERE settlementDate >= '2025-10-17'
  AND settlementDate <= '2025-10-23'
```

Run and validate:
```bash
python3 vlp_revenue_engine.py
```

**Expected Results**:
- 336 SPs processed (7 days × 48)
- Total gross margin: ~£65,000-80,000 (compare to £286k/month = £66k/week)
- Site margin: ~£45,000-56,000 (70% of gross minus £100k opex prorated)
- VLP margin: ~£19,500-24,000 (30% of gross)

**Sanity Checks**:
1. **SoC continuity**: `soc_end` of SP n = `soc_start` of SP n+1
2. **Energy balance**: Sum of all charges ≈ Sum of all discharges (accounting for efficiency)
3. **No boundary violations**: All `soc_end` values between 0.25 and 5.0 MWh
4. **Charts populate**: All 4 dashboard charts show data

### Todo #20: Apply Formatting

In Dashboard worksheet:

1. **Currency format**:
   - Select B5:B10 and D4:D6
   - Format → Number → Currency (£)
   - Decimal places: 0

2. **Conditional formatting** (negative margins):
   - Select D5:D6
   - Format → Conditional formatting
   - Format rule: "Less than 0"
   - Formatting style: Red background, white text

3. **Header styling**:
   - Select A4:B4 and D4:D4
   - Bold, background color: Light blue (#CFE2F3)
   - Text color: Dark grey (#434343)

4. **Borders**:
   - A4:B10 box: All borders (medium weight)
   - D4:D6 box: All borders (medium weight)

5. **Alignment**:
   - B5:B10: Right-align
   - A5:A10: Left-align

### Todo #21: Compare with Earlier Analysis

Cross-check VLP engine results against three-tier model (Battery_Revenue_Analysis rows 100-212):

| Revenue Stream | Three-Tier Base | VLP Engine Expected | Match? |
|----------------|-----------------|---------------------|--------|
| BM revenue | £113k/month | ~£110-120k/month | ✓ |
| Arbitrage (buy low/sell high) | £120k/month | N/A (split into PPA + avoided import) | - |
| DUoS avoidance | £75k/month | Part of avoided import | - |
| CM revenue | £66k/month | ~£60-70k/month | ✓ |
| ESO services (FR) | £42k/month | ~£40-50k/month | ✓ |
| **Total** | **£286k/month** | **~£280-300k/month** | **✓** |

**New VLP Engine Breakdown** (expected):
- BM revenue (`r_bm_gbp`): £110k/month
- ESO revenue (`r_eso_gbp`): £45k/month
- CM revenue (`r_cm_gbp`): £65k/month
- PPA export (`r_ppa_gbp`): £80k/month (battery + CHP)
- Avoided import (`r_avoided_import_gbp`): £60k/month (onsite consumption value)
- DSO flex (`r_dso_gbp`): £0/month (placeholder)
- **Gross**: ~£360k/month

**Less costs**:
- Battery import: -£40k/month
- CHP fuel: -£20k/month
- Fixed opex: -£8.3k/month (£100k/year)
- **Net margin**: ~£290k/month ✓

**If major discrepancies (>50%)**:
- Check BMU IDs correct in view (todo #1)
- Verify revenue stream calculations in view (todo #7)
- Compare individual SP margins with earlier model

### Todo #22: Edge Cases & Error Handling

Test robustness:

**Test 1: Empty View Result**
```python
# Modify fetch_vlp_inputs() to query non-existent date:
WHERE settlementDate = '2030-01-01'
```
Run and verify:
```bash
python3 vlp_revenue_engine.py
# Expected: "No data in v_vlp_site_revenue_stack" + clean exit
```

**Test 2: SoC Boundary Violations**
```python
# In optimise_bess_chp(), set invalid initial SoC:
INITIAL_SOC = 6.0  # Exceeds SOC_MAX
```
Add validation in function:
```python
def optimise_bess_chp(df_in: pd.DataFrame) -> RevenueResult:
    soc = INITIAL_SOC
    
    # Validate initial SoC
    if soc < SOC_MIN or soc > SOC_MAX:
        raise ValueError(f"Initial SoC {soc} outside bounds [{SOC_MIN}, {SOC_MAX}]")
```

**Test 3: All-Negative Margins**
```python
# Temporarily set PPA price very low:
ppa_price AS (SELECT 10.0 AS ppa_price_gbp_per_mwh)  # £10/MWh (below cost)
```
Verify battery stays idle (no charge/discharge if unprofitable).

**Test 4: NULL Values in View**
```sql
-- Check for NULLs in revenue columns:
SELECT 
  COUNTIF(r_bm_gbp IS NULL) as nulls_bm,
  COUNTIF(r_eso_gbp IS NULL) as nulls_eso,
  COUNTIF(r_cm_gbp IS NULL) as nulls_cm,
  COUNTIF(r_ppa_gbp IS NULL) as nulls_ppa,
  COUNTIF(import_cost_gbp_per_mwh IS NULL) as nulls_cost
FROM `inner-cinema-476211-u9.uk_energy_prod.v_vlp_site_revenue_stack`
```
All should be zero (COALESCE in view prevents NULLs).

---

## Phase 7: Documentation (Todo #23)

Create comprehensive documentation after implementation:

```markdown
# VLP Revenue Engine - Production Documentation

## System Overview
[Architecture diagram, component descriptions]

## Prerequisites
- BMU IDs: FBPGM002 (battery), XXCHP001 (CHP)
- Battery spec: 2.5 MW / 5.0 MWh / 85% efficiency
- Site ID: SITE_001
- Spreadsheet: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

## Data Dependencies
[Table schemas with actual column names and sample data]

## Running the Engine
```bash
# Full run (7 days):
python3 vlp_revenue_engine.py

# Custom date range:
# Edit fetch_vlp_inputs() WHERE clause, then run
```

## Interpreting Results
[Explain revenue breakdown, margin allocation, chart analysis]

## Troubleshooting
[Common errors with solutions]

## Future Enhancements
[Roadmap for greedy vs optimized, realistic CHP, webhook integration]
```

---

## Optional Enhancements (Todos #24-26)

### Todo #24: Greedy vs Optimized Comparison

Add two-mode optimizer:

```python
def optimise_bess_chp(df_in: pd.DataFrame, mode='optimized') -> RevenueResult:
    """
    mode: 'greedy' or 'optimized'
    
    Greedy: Always discharge at highest price, ignore future value
    Optimized: Forward-looking value, charge when future benefit > cost
    """
    if mode == 'greedy':
        # Discharge if PPA > cost, charge never
        if ppa_price > c_batt:
            batt_action = "DISCHARGE"
    else:  # optimized
        # Current logic (forward-looking)
        if margin_batt_discharge_per_mwh > 0:
            batt_action = "DISCHARGE"
        elif margin_import_ppa_per_mwh > 0:
            batt_action = "CHARGE"
```

Run both modes, calculate improvement:
```python
result_greedy = optimise_bess_chp(df, mode='greedy')
result_optimized = optimise_bess_chp(df, mode='optimized')
improvement_pct = (result_optimized.total_gross_margin - result_greedy.total_gross_margin) / result_greedy.total_gross_margin * 100
print(f"Optimized improves margin by {improvement_pct:.1f}%")
```

### Todo #25: Realistic CHP Model

Upgrade from simple on/off to:

```python
# Add state tracking
chp_state = "OFF"  # Track across SPs
chp_runtime = 0    # Count consecutive run SPs

for _, row in df.iterrows():
    # Heat demand constraint
    if row['site_heat_demand_mwh_th'] > 0:
        chp_must_run = True
    else:
        chp_must_run = False
    
    # Minimum runtime (4 SPs = 2 hours)
    if chp_state == "RUN" and chp_runtime < 4:
        chp_action = "RUN"  # Force continue
        chp_runtime += 1
    
    # Startup cost
    if chp_state == "OFF" and chp_action == "RUN":
        chp_action_margin -= 50.0  # £50 startup cost
    
    # Update state
    chp_state = chp_action
    if chp_action == "OFF":
        chp_runtime = 0
```

### Todo #26: Apps Script Webhook Integration

Create button-triggered execution:

**1. Python webhook server** (`vlp_webhook_server.py`):
```python
from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/refresh_vlp', methods=['POST'])
def refresh_vlp():
    data = request.get_json()
    date_start = data.get('date_start', '2025-10-17')
    date_end = data.get('date_end', '2025-10-23')
    
    # Modify vlp_revenue_engine.py date filter dynamically
    # Or pass dates as command-line args
    
    result = subprocess.run(['python3', 'vlp_revenue_engine.py'], capture_output=True)
    
    if result.returncode == 0:
        return jsonify({"status": "success", "message": "VLP analysis refreshed"})
    else:
        return jsonify({"status": "error", "message": result.stderr.decode()})

if __name__ == '__main__':
    app.run(port=5002)
```

**2. Apps Script button** (`vlp_refresh_button.gs`):
```javascript
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('VLP Analysis')
    .addItem('Refresh Data', 'refreshVlpAnalysis')
    .addToUi();
}

function refreshVlpAnalysis() {
  var ui = SpreadsheetApp.getUi();
  var response = ui.alert(
    'Refresh VLP Analysis',
    'This will update the dashboard with latest data. Continue?',
    ui.ButtonSet.YES_NO
  );
  
  if (response == ui.Button.YES) {
    var url = 'https://YOUR_NGROK_URL.ngrok.io/refresh_vlp';  // Update with actual webhook URL
    var payload = {
      date_start: '2025-10-17',
      date_end: '2025-10-23'
    };
    
    var options = {
      method: 'post',
      contentType: 'application/json',
      payload: JSON.stringify(payload)
    };
    
    try {
      var result = UrlFetchApp.fetch(url, options);
      var data = JSON.parse(result.getContentText());
      
      if (data.status === 'success') {
        ui.alert('Success', 'VLP analysis refreshed successfully!', ui.ButtonSet.OK);
      } else {
        ui.alert('Error', data.message, ui.ButtonSet.OK);
      }
    } catch (e) {
      ui.alert('Error', 'Failed to connect to VLP engine: ' + e.toString(), ui.ButtonSet.OK);
    }
  }
}
```

**3. Deploy webhook**:
```bash
# Terminal 1: Start Flask server
python3 vlp_webhook_server.py

# Terminal 2: Expose with ngrok
ngrok http 5002
# Copy https://xxxx.ngrok.io URL to Apps Script
```

---

## Implementation Checklist

Use this checklist to track progress:

### Phase 1: Prerequisites
- [ ] Todo #1: Gather BMU IDs, battery spec, site ID, spreadsheet ID
- [ ] Todo #2: Verify bmrs_boalf, bmrs_costs, check ESO/CM tables

### Phase 2: Data Preparation
- [ ] Todo #3: Create site_metered_flows table (CRITICAL)
- [ ] Todo #4: Create/verify esoservices_dc_site table
- [ ] Todo #5: Create/verify capacity_market_site table

### Phase 3: BigQuery View
- [ ] Todo #6: Create v_vlp_site_revenue_stack view (replace BMU IDs)
- [ ] Todo #7: Test view with validation query

### Phase 4: Python Engine
- [ ] Todo #8: Create vlp_revenue_engine.py (update config)
- [ ] Todo #9: Fix authentication (oauth2client)
- [ ] Todo #10: Test fetch_vlp_inputs()
- [ ] Todo #11: Test optimizer (1 day, 48 SPs)
- [ ] Todo #12: Validate optimizer logic (manual check)

### Phase 5: Dashboard
- [ ] Todo #13: Prepare Dashboard layout (headers)
- [ ] Todo #14: Test write_dashboard() (verify updates)
- [ ] Todo #15: Create Chart 1 (Revenue Stack)
- [ ] Todo #16: Create Chart 2 (SoC over time)
- [ ] Todo #17: Create Chart 3 (Battery Actions)
- [ ] Todo #18: Create Chart 4 (Per-SP Gross Margin)

### Phase 6: Validation
- [ ] Todo #19: Full-period run (7 days, 336 SPs)
- [ ] Todo #20: Apply conditional formatting
- [ ] Todo #21: Compare with earlier three-tier analysis
- [ ] Todo #22: Test edge cases & error handling

### Phase 7: Documentation
- [ ] Todo #23: Create VLP_IMPLEMENTATION_GUIDE.md

### Optional Enhancements
- [ ] Todo #24: Add greedy vs optimized comparison
- [ ] Todo #25: Implement realistic CHP model
- [ ] Todo #26: Apps Script webhook integration

---

## Quick Start (TL;DR)

If you want to get running ASAP:

```bash
# 1. Prerequisites
BMU_BATTERY="FBPGM002"  # Replace with your actual BMU
BMU_CHP="XXCHP001"      # Replace with your actual BMU

# 2. Create stub tables (for testing)
bq query --use_legacy_sql=false < create_stub_tables.sql

# 3. Create view (replace BMU IDs in SQL first)
bq query --use_legacy_sql=false < v_vlp_site_revenue_stack.sql

# 4. Install Python dependencies
pip3 install --user google-cloud-bigquery db-dtypes pyarrow pandas gspread oauth2client

# 5. Fix authentication in vlp_revenue_engine.py (use oauth2client)

# 6. Run engine
python3 vlp_revenue_engine.py

# 7. Check Google Sheets for updated Dashboard + BESS worksheet
```

---

## Support & Troubleshooting

**Common Issues**:

1. **"Table not found: site_metered_flows"**
   - Solution: Todo #3 - Create the table (critical dependency)

2. **"No access token in response"**
   - Solution: Todo #9 - Use oauth2client instead of google.oauth2

3. **"View returns zero rows"**
   - Solution: Check date range in source tables, verify BMU IDs

4. **"SoC violations (negative or exceeds max)"**
   - Solution: Check INITIAL_SOC, validate optimizer logic (todo #12)

5. **"All revenue streams showing £0"**
   - Solution: Verify stub tables have non-zero values, check JOIN conditions

**Getting Help**:
- Review `STOP_DATA_ARCHITECTURE_REFERENCE.md` for data issues
- Check `PROJECT_CONFIGURATION.md` for all settings
- Search earlier scripts for authentication patterns

---

## Estimated Timeline

| Phase | Tasks | Time | Blocker Risk |
|-------|-------|------|--------------|
| Phase 1: Prerequisites | 2 todos | 30 min | Low (data gathering) |
| Phase 2: Data Prep | 3 todos | 2-4 hours | **HIGH** (table creation) |
| Phase 3: BigQuery View | 2 todos | 1 hour | Medium (SQL debugging) |
| Phase 4: Python Engine | 5 todos | 3-4 hours | Medium (auth fix, testing) |
| Phase 5: Dashboard | 6 todos | 2-3 hours | Low (manual chart creation) |
| Phase 6: Validation | 4 todos | 2 hours | Low (verification only) |
| Phase 7: Documentation | 1 todo | 1 hour | Low (writeup) |
| **Core Total** | **23 todos** | **12-16 hours** | **2-3 days** |
| Optional Enhancements | 3 todos | 4-6 hours | Low (nice-to-have) |

**Critical Path**: Phase 2 (Data Prep) → Phase 3 (View) → Phase 4 (Engine) → Phase 5 (Dashboard)

**Blockers to Watch**:
- Todo #3 (site_metered_flows) - if no real meter data, must create stub
- Todo #9 (authentication) - critical for Google Sheets writes
- Todo #6 (view creation) - SQL syntax errors can be time-consuming

---

*Last Updated: 5 December 2025*  
*Version: 1.0*  
*Maintainer: George Major (george@upowerenergy.uk)*
