# Energy Tariff Data - BigQuery Ingestion Plan

**Date**: 21 November 2025  
**Status**: 🔴 CRITICAL - Data exists in Google Sheets but NOT in BigQuery  
**Priority**: HIGH - Required for battery arbitrage cost modeling

---

## Executive Summary

Six critical UK energy tariff datasets exist in **Google Sheets** but need to be ingested into **BigQuery** for analysis. These tariffs represent significant operating costs for battery storage and generation assets.

**Current Status**:
- ✅ Data exists in Google Sheets: `GB Energy Dashboard` (ID: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`)
- ❌ NOT in BigQuery (tables don't exist)
- ⚠️ Missing from cost modeling calculations

---

## Data Inventory

### 1. TNUoS (Transmission Network Use of System) - TDR Bands

**Purpose**: Fixed daily charges for connection to transmission network  
**Impact**: £0.10-£366/site/day depending on voltage level and demand

#### Sheet 1: `TNUos_TDR_Bands_2024-25`
- **Rows**: 23
- **Columns**: 6
- **Period**: 1 April 2024 - 31 March 2025
- **Structure**:
  ```
  Band          | £/site/day (2024/25) | Unit        | Notes | £/site/year | £/site/month
  Domestic      | £0.10               | £/site/day  |       | £38.17      | £3.18
  LV_NoMIC_1    | £0.07               | £/site/day  |       | £25.48      | £2.12
  LV_NoMIC_2    | £0.25               | £/site/day  |       | £92.42      | £7.70
  ... (20 more bands)
  ```

#### Sheet 2: `TNUoS_TDR_Bands_2025-26`
- **Rows**: 23
- **Columns**: 6
- **Period**: 1 April 2025 - 31 March 2026
- **Changes**: +35% increase (Domestic: £0.10 → £0.135)
- **Structure**: Same as 2024-25

**BigQuery Target**: `inner-cinema-476211-u9.uk_energy_prod.tnuos_tdr_bands`

**Schema**:
```sql
CREATE TABLE `inner-cinema-476211-u9.uk_energy_prod.tnuos_tdr_bands` (
    tariff_year STRING,           -- '2024-25' or '2025-26'
    band STRING,                  -- 'Domestic', 'LV_NoMIC_1', etc.
    rate_gbp_per_site_day FLOAT64,
    unit STRING,                  -- '£/site/day'
    notes STRING,
    rate_gbp_per_site_year FLOAT64,
    rate_gbp_per_site_month FLOAT64,
    effective_from DATE,          -- 2024-04-01 or 2025-04-01
    effective_to DATE,            -- 2025-03-31 or 2026-03-31
    data_source STRING            -- 'Google Sheets GB Energy Dashboard'
);
```

---

### 2. FiT (Feed-in Tariff) - Levelisation Fund

**Purpose**: Consumer levy to fund small-scale renewable generation payments  
**Impact**: 0.53-0.727 p/kWh passed to all electricity consumers

#### Sheet: `Copy of FiT_Rates_Pa`
- **Rows**: 7 (6 data rows + header)
- **Columns**: 5
- **Period**: Scheme Years 9-14 (2018/19 - 2023/24)
- **Structure**:
  ```
  Scheme Year | Period (FY) | Levelisation Fund (£) | Total Relevant Electricity (MWh) | Implied p/kWh
  SY9         | 2018/19     | 1,414,741,502        | 266,803,867                     | 0.53
  SY10        | 2019/20     | 1,539,682,298        | 254,557,039                     | 0.605
  SY11        | 2020/21     | 1,603,008,386        | 237,715,812                     | 0.674
  SY12        | 2021/22     | 1,273,114,642        | 241,566,051                     | 0.527
  SY13        | 2022/23     | 1,452,953,030        | 231,809,253                     | 0.627
  SY14        | 2023/24     | 1,754,915,050        | 241,516,154                     | 0.727
  ```

**Source**: Ofgem FiT Annual Reports  
**Contact**: fitstatistics@energysecurity.gov.uk  
**Notes**: 
- FiT scheme closed to new applicants 31 March 2019
- Existing generators receive payments for up to 20 years
- SY15 (2024/25) data expected Apr-Jul 2025

**BigQuery Target**: `inner-cinema-476211-u9.uk_energy_prod.fit_levelisation_rates`

**Schema**:
```sql
CREATE TABLE `inner-cinema-476211-u9.uk_energy_prod.fit_levelisation_rates` (
    scheme_year STRING,              -- 'SY9', 'SY10', etc.
    fiscal_year STRING,              -- '2018/19', '2019/20', etc.
    levelisation_fund_gbp INT64,     -- Total £ collected
    total_relevant_electricity_mwh INT64,  -- Total MWh supplied
    implied_rate_p_per_kwh FLOAT64,  -- p/kWh levy
    effective_from DATE,             -- 2018-04-01, etc.
    effective_to DATE,               -- 2019-03-31, etc.
    data_source STRING,
    notes STRING
);
```

---

### 3. RO (Renewables Obligation) - ROC Rates

**Purpose**: Main renewable energy support scheme (closed 31 March 2017, legacy obligations continue)  
**Impact**: Variable p/kWh based on ROC buyout price and obligation level

#### Sheet: `Ro_Rates`
- **Rows**: 68 (67 data rows + header)
- **Columns**: 6
- **Period**: 2016/17 onwards
- **Structure**:
  ```
  Year    | Buyout_£perROC | Obligation_ROCperMWh | Recycle_£perROC | Override_p_per_kWh | Notes
  2016/17 | 44.77         | 0.348                | 0               |                    | Ofgem table
  2017/18 | 45.58         | 0.409                | 0               |                    | Ofgem table
  2018/19 | 47.22         | 0.468                | 0               |                    | Ofgem table
  2019/20 | 48.78         | 0.468                | 0               |                    | Ofgem table
  2020/21 | 50.05         | 0.470                | 0               |                    | Ofgem table
  2021/22 | 51.40         | 0.478                | 0               |                    | Ofgem table
  2022/23 | 52.40         | 0.487                | 0               |                    | Ofgem table
  2023/24 | 53.41         | 0.497                | 0               |                    | Ofgem table
  ... (59 more rows)
  ```

**Calculation**: `Cost (p/kWh) = (Buyout + Recycle) × Obligation / 10`

**BigQuery Target**: `inner-cinema-476211-u9.uk_energy_prod.ro_rates`

**Schema**:
```sql
CREATE TABLE `inner-cinema-476211-u9.uk_energy_prod.ro_rates` (
    obligation_year STRING,          -- '2016/17', '2017/18', etc.
    buyout_gbp_per_roc FLOAT64,      -- ROC buyout price
    obligation_roc_per_mwh FLOAT64,  -- ROCs required per MWh
    recycle_gbp_per_roc FLOAT64,     -- Recycle fund value
    override_p_per_kwh FLOAT64,      -- Manual override if specified
    notes STRING,
    effective_from DATE,
    effective_to DATE,
    data_source STRING
);
```

---

### 4. BSUoS (Balancing Services Use of System) - Fixed Tariffs

**Purpose**: Cost of balancing supply and demand in real-time  
**Impact**: £7.63-£14.03 per MWh (significant for high-volume traders)

#### Sheet: `BSUoS_Rates`
- **Rows**: 12 (11 data rows + header)
- **Columns**: 6
- **Period**: April 2023 onwards (6-month tariff periods)
- **Structure**:
  ```
  Publication | Fixed Tariff Title | Published Date | Start Date  | End Date    | Fixed Tariff £/MWh
  Final       | Fixed Tariff 1     | 31/01/2023    | 01/04/2023  | 30/09/2023  | 13.41
  Final       | Fixed Tariff 2     | 31/01/2023    | 01/10/2023  | 31/03/2024  | 14.03
  Final       | Fixed Tariff 3     | 30/06/2023    | 01/04/2024  | 30/09/2024  | 7.63
  Final       | Fixed Tariff 4     | 30/06/2023    | 01/10/2024  | 31/03/2025  | 7.93
  ... (7 more rows)
  ```

**Source**: National Grid ESO (now NESO)  
**Notes**: Changed from half-hourly variable to fixed 6-month tariffs in April 2023

**BigQuery Target**: `inner-cinema-476211-u9.uk_energy_prod.bsuos_rates`

**Schema**:
```sql
CREATE TABLE `inner-cinema-476211-u9.uk_energy_prod.bsuos_rates` (
    publication_status STRING,       -- 'Final' or 'Provisional'
    tariff_title STRING,             -- 'Fixed Tariff 1', etc.
    published_date DATE,
    effective_from DATE,
    effective_to DATE,
    rate_gbp_per_mwh FLOAT64,
    data_source STRING,
    notes STRING
);
```

---

### 5. CCL (Climate Change Levy) - Energy Tax Rates

**Purpose**: Environmental tax on business energy use  
**Impact**: 0.559-0.775 p/kWh for electricity (reduced rate for CCAs)

#### Sheet: `CCL_Rates`
- **Rows**: 12 (11 data rows + header)
- **Columns**: 11
- **Period**: 2016/17 onwards
- **Structure**:
  ```
  Year    | Effective_From | Electricity_£_per_kWh | Gas_£_per_kWh | LPG_£_per_kg | Other_£_per_kg | CCA_Discount_Electricity_pct | CCA_Discount_Gas_pct | ...
  2016/17 | 2016-04-01    | 0.00559              | 0.00195      | 0.01251     | 0.01526       | 90%                         | 65%                  |
  2017/18 | 2017-04-01    | 0.00568              | 0.00198      | 0.01272     | 0.01551       | 90%                         | 65%                  |
  2018/19 | 2018-04-01    | 0.00583              | 0.00203      | 0.01304     | 0.01591       | 90%                         | 65%                  |
  2019/20 | 2019-04-01    | 0.00811              | 0.00339      | 0.02175     | 0.02653       | 92%                         | 77%                  |
  2020/21 | 2020-04-01    | 0.00775              | 0.00406      | 0.02175     | 0.02653       | 92%                         | 77%                  |
  ... (6 more rows)
  ```

**Source**: HMRC  
**Notes**: 
- CCA (Climate Change Agreement) holders get discounted rates
- Exemptions for renewable generation and certain industries

**BigQuery Target**: `inner-cinema-476211-u9.uk_energy_prod.ccl_rates`

**Schema**:
```sql
CREATE TABLE `inner-cinema-476211-u9.uk_energy_prod.ccl_rates` (
    fiscal_year STRING,              -- '2016/17', etc.
    effective_from DATE,
    electricity_gbp_per_kwh FLOAT64,
    gas_gbp_per_kwh FLOAT64,
    lpg_gbp_per_kg FLOAT64,
    other_gbp_per_kg FLOAT64,
    cca_discount_electricity_pct FLOAT64,
    cca_discount_gas_pct FLOAT64,
    cca_electricity_gbp_per_kwh FLOAT64,  -- Calculated discounted rate
    cca_gas_gbp_per_kwh FLOAT64,          -- Calculated discounted rate
    data_source STRING,
    notes STRING
);
```

---

## Financial Impact Analysis

### Battery Storage Example (50 MW, 100 MWh, 2-cycle/day operation)

**Annual Volume**: 
- Discharge: 36,500 MWh/year (50 MW × 2 cycles × 365 days)
- Charge: 36,500 MWh/year

**Annual Costs** (2024/25 rates):

| Tariff   | Rate           | Annual Cost   | Notes |
|----------|----------------|---------------|-------|
| TNUoS    | £0.25/site/day | £91           | Small for large sites |
| FiT      | 0.727 p/kWh    | £26,532       | On discharge only |
| RO       | ~2.5 p/kWh     | £91,250       | On discharge only |
| BSUoS    | £7.93/MWh      | £289,445      | On charge AND discharge |
| CCL      | 0.775 p/kWh    | £28,288       | If not exempt |
| **TOTAL**| **-**          | **£435,606**  | **~£12/MWh all-in** |

**Impact on Arbitrage**:
- Average spread needed: £45/MWh (to cover £12/MWh tariffs + losses + O&M)
- Reduces tradeable settlement periods significantly
- Makes frequency response/ancillary services more attractive

---

## Implementation Plan

### Phase 1: Create BigQuery Tables (Week 1)

**Script**: `create_tariff_tables.py`

```python
from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

client = bigquery.Client(project=PROJECT_ID, location="US")

# Create all 6 tables with schemas defined above
# ...
```

### Phase 2: Ingest Historical Data (Week 1)

**Script**: `ingest_tariff_data_from_sheets.py`

```python
import pickle
import gspread
from google.cloud import bigquery
import pandas as pd
from datetime import datetime

# 1. Read from Google Sheets
# 2. Transform to schema format
# 3. Upload to BigQuery
# 4. Verify row counts
```

**Source Sheet**: `GB Energy Dashboard`  
**Sheet ID**: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`

**Worksheets to Process**:
1. `TNUos_TDR_Bands_2024-25` → `tnuos_tdr_bands` (23 rows, tariff_year='2024-25')
2. `TNUoS_TDR_Bands_2025-26` → `tnuos_tdr_bands` (23 rows, tariff_year='2025-26')
3. `Copy of FiT_Rates_Pa` → `fit_levelisation_rates` (6 rows)
4. `Ro_Rates` → `ro_rates` (67 rows)
5. `BSUoS_Rates` → `bsuos_rates` (11 rows)
6. `CCL_Rates` → `ccl_rates` (11 rows)

**Total Rows**: 141

### Phase 3: Create Cost Calculation Views (Week 2)

**View**: `vw_current_tariffs` - Get current rates for all tariffs

```sql
CREATE VIEW `inner-cinema-476211-u9.uk_energy_prod.vw_current_tariffs` AS
SELECT 
    CURRENT_DATE() as query_date,
    
    -- TNUoS (latest year)
    (SELECT rate_gbp_per_site_day FROM tnuos_tdr_bands 
     WHERE band = 'LV_NoMIC_1' 
     ORDER BY effective_from DESC LIMIT 1) as tnuos_gbp_site_day,
    
    -- FiT (latest year)
    (SELECT implied_rate_p_per_kwh FROM fit_levelisation_rates
     ORDER BY effective_from DESC LIMIT 1) as fit_p_per_kwh,
    
    -- RO (current obligation year)
    (SELECT (buyout_gbp_per_roc + recycle_gbp_per_roc) * obligation_roc_per_mwh / 10 
     FROM ro_rates
     WHERE CURRENT_DATE() BETWEEN effective_from AND effective_to
     LIMIT 1) as ro_p_per_kwh,
    
    -- BSUoS (current period)
    (SELECT rate_gbp_per_mwh FROM bsuos_rates
     WHERE CURRENT_DATE() BETWEEN effective_from AND effective_to
     LIMIT 1) as bsuos_gbp_per_mwh,
    
    -- CCL (current year, full rate)
    (SELECT electricity_gbp_per_kwh FROM ccl_rates
     WHERE CURRENT_DATE() >= effective_from
     ORDER BY effective_from DESC LIMIT 1) as ccl_gbp_per_kwh;
```

**View**: `vw_battery_arbitrage_costs` - Calculate all-in costs

```sql
CREATE VIEW `inner-cinema-476211-u9.uk_energy_prod.vw_battery_arbitrage_costs` AS
WITH current_rates AS (
    SELECT * FROM vw_current_tariffs
)
SELECT
    -- Per MWh discharge
    (fit_p_per_kwh * 10) + 
    (ro_p_per_kwh * 10) + 
    bsuos_gbp_per_mwh + 
    (ccl_gbp_per_kwh * 1000) as total_cost_gbp_per_mwh_discharge,
    
    -- Per MWh charge (BSUoS only)
    bsuos_gbp_per_mwh as total_cost_gbp_per_mwh_charge,
    
    -- Fixed daily cost
    tnuos_gbp_site_day as fixed_cost_gbp_per_day
FROM current_rates;
```

### Phase 4: Integrate with Arbitrage Analysis (Week 2)

**Update**: `battery_arbitrage.py` to include tariff costs

```python
# Query current tariff rates
tariff_query = """
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.vw_current_tariffs`
"""
tariffs = client.query(tariff_query).to_dataframe()

# Add to P&L calculation
revenue = (sell_price - buy_price) * volume_mwh
tariff_costs = (
    tariffs['fit_p_per_kwh'][0] * volume_mwh * 10 +  # p/kWh to £/MWh
    tariffs['ro_p_per_kwh'][0] * volume_mwh * 10 +
    tariffs['bsuos_gbp_per_mwh'][0] * volume_mwh * 2 +  # Charge + discharge
    tariffs['ccl_gbp_per_kwh'][0] * volume_mwh * 1000
)
profit = revenue - tariff_costs - losses - fixed_costs
```

### Phase 5: Monitoring & Updates (Ongoing)

**Update Frequency**:
- **TNUoS**: Annually (April) - Manual update from National Grid ESO
- **FiT**: Annually (July) - Contact fitstatistics@energysecurity.gov.uk
- **RO**: Annually (April) - Ofgem publications
- **BSUoS**: Every 6 months (April, October) - NESO publications
- **CCL**: Annually (April) - HMRC Budget announcements

**Alert Script**: `check_tariff_staleness.py`

```python
# Check if rates are >1 year old and alert
# Send email if TNUoS rates effective_to < CURRENT_DATE
```

---

## Data Quality & Validation

### Pre-Ingestion Checks

1. **Date Consistency**: Ensure effective_from < effective_to
2. **No Gaps**: Verify continuous coverage (each tariff's end date = next start date - 1 day)
3. **Rate Reasonableness**: 
   - FiT: 0.4-1.0 p/kWh
   - RO: 1.5-3.0 p/kWh
   - BSUoS: 5-20 £/MWh
   - CCL: 0.5-1.0 p/kWh
4. **Duplicate Detection**: No overlapping periods for same tariff type

### Post-Ingestion Validation

```sql
-- Check row counts match source
SELECT 
    'tnuos_tdr_bands' as table_name, COUNT(*) as rows 
FROM tnuos_tdr_bands
UNION ALL
SELECT 'fit_levelisation_rates', COUNT(*) FROM fit_levelisation_rates
UNION ALL
SELECT 'ro_rates', COUNT(*) FROM ro_rates
UNION ALL
SELECT 'bsuos_rates', COUNT(*) FROM bsuos_rates
UNION ALL
SELECT 'ccl_rates', COUNT(*) FROM ccl_rates;

-- Expected: 46 + 6 + 67 + 11 + 11 = 141 rows
```

---

## Related Documentation

- `DUOS_DATA_STATUS_SUMMARY.md` - DUoS tariff tables (currently empty, needs population)
- `DNUOS_CHARGES_STATUS.md` - Detailed DUoS implementation guide
- `battery_arbitrage.py` - Battery P&L calculator (needs tariff integration)
- `advanced_statistical_analysis_enhanced.py` - Market analysis (could benefit from cost context)

---

## External Resources

### Data Sources

1. **TNUoS**: https://www.nationalgrideso.com/industry-information/charging/transmission-network-use-system-tnuos-charges
2. **FiT**: https://www.gov.uk/government/collections/feed-in-tariff-statistics
3. **RO**: https://www.ofgem.gov.uk/environmental-and-social-schemes/renewables-obligation-ro
4. **BSUoS**: https://www.nationalgrideso.com/industry-information/balancing-services/balancing-services-use-system-bsuos-charges
5. **CCL**: https://www.gov.uk/guidance/climate-change-levy-rates

### Regulatory Bodies

- **Ofgem**: https://www.ofgem.gov.uk/
- **DESNZ**: https://www.gov.uk/government/organisations/department-for-energy-security-and-net-zero
- **NESO** (National Energy System Operator): https://www.nationalgrideso.com/
- **HMRC**: https://www.gov.uk/government/organisations/hm-revenue-customs

---

## Action Items

### Immediate (This Week)
- [ ] Create BigQuery table schemas
- [ ] Write ingestion script (`ingest_tariff_data_from_sheets.py`)
- [ ] Test ingestion with one table (FiT - smallest dataset)
- [ ] Validate data quality
- [ ] Ingest all 6 tariff tables

### Short-term (Next 2 Weeks)
- [ ] Create `vw_current_tariffs` view
- [ ] Create `vw_battery_arbitrage_costs` view
- [ ] Update `battery_arbitrage.py` to include tariff costs
- [ ] Recalculate historical battery P&L with true costs
- [ ] Update dashboard to show tariff impact

### Medium-term (Next Month)
- [ ] Create tariff monitoring dashboard in Google Sheets
- [ ] Set up alerts for stale data (>12 months old)
- [ ] Document update procedures for each tariff type
- [ ] Contact DESNZ for SY15 (2024/25) FiT data
- [ ] Investigate automation options for future updates

### Long-term (Next Quarter)
- [ ] Populate DUoS tables (distribution charges)
- [ ] Create unified cost model for all generation/storage assets
- [ ] Build scenario analysis tool (tariff sensitivity)
- [ ] API integration with Ofgem/NESO for automatic updates

---

**Priority**: 🔴 CRITICAL  
**Estimated Effort**: 2-3 days for full implementation  
**Business Impact**: Enables accurate battery arbitrage profitability analysis

**Last Updated**: 21 November 2025  
**Next Review**: After Phase 1 completion
