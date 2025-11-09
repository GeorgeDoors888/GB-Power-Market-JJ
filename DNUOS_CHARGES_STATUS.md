# DNUoS (DUoS) Charges - BigQuery Status Report

**Date**: 9 November 2025  
**Project**: GB Power Market JJ  
**BigQuery Project**: `inner-cinema-476211-u9`

---

## Executive Summary

| Category | Status | Rows | Details |
|----------|--------|------|---------|
| **DUoS Tariff Tables** | ⚠️ **EMPTY** | 0 rows | Structure exists, needs data |
| **DNO Reference Data** | ✅ **COMPLETE** | 14 rows | All UK DNOs mapped |
| **Market/System Data** | ✅ **COMPLETE** | 884M+ rows | Full BMRS data available |

### Quick Answer: **DUoS tariff data is NOT in BigQuery yet**
- ✅ Table schemas exist (well-designed, ready to use)
- ⚠️ All 3 DUoS tables are EMPTY (0 rows)
- ✅ DNO reference data is complete (14 license areas)
- 📊 Action needed: Import tariff data from DNO websites

---

## What are DNUoS/DUoS Charges?

**DNUoS** = Distribution Network Use of System  
**DUoS** = Distribution Use of System (same thing)

These are charges levied by the 14 Distribution Network Operators (DNOs) for using their local electricity networks.

### Key Characteristics:
- **Time-of-Day Dependent**: Red/Amber/Green bands (peak/off-peak pricing)
- **Voltage-Level Dependent**: EHV (22kV+), HV (6.6-22kV), LV (230/400V)
- **DNO-Specific**: Each of 14 DNOs has different tariff structures
- **Customer Category**: Domestic, commercial, industrial
- **Seasonal**: Some DNOs have winter/summer rates

### Different From:
- **TNUoS**: Transmission Network Use of System (National Grid charges)
- **BSUoS**: Balancing Services Use of System (system balancing)

---

## BigQuery Tables Found

### 1. DUoS Tariff Tables (`gb_power` dataset, EU region)

#### ⚠️ `gb_power.duos_tariff_definitions`
- **Status**: EMPTY (0 rows)
- **Schema**: 15 columns
- **Location**: EU
- **Purpose**: Define tariff codes, voltage levels, customer categories

**Schema** (ready for data):
```sql
tariff_id STRING
dno_key STRING
tariff_code STRING
tariff_name STRING
tariff_description STRING
voltage_level STRING          -- HV/LV/EHV
customer_category STRING      -- Domestic/Commercial/Industrial
metering_type STRING          -- Half-hourly/Non-half-hourly
profile_class INT64           -- Profile class 1-8
time_pattern STRING
effective_from DATE
effective_to DATE
source_document STRING
source_document_url STRING
extracted_date DATE
```

#### ⚠️ `gb_power.duos_time_bands`
- **Status**: EMPTY (0 rows)
- **Schema**: 11 columns
- **Purpose**: Define Red/Amber/Green time periods by DNO

**Schema**:
```sql
time_band_id STRING
dno_key STRING
time_band STRING              -- Red/Amber/Green
season STRING                 -- Winter/Summer/All-year
day_type STRING               -- Weekday/Weekend
start_time TIME
end_time TIME
start_month INT64
end_month INT64
effective_from DATE
effective_to DATE
```

#### ⚠️ `gb_power.duos_unit_rates`
- **Status**: EMPTY (0 rows)
- **Schema**: 13 columns
- **Purpose**: Store actual p/kWh rates by time band

**Schema**:
```sql
rate_id STRING
tariff_id STRING
dno_key STRING
tariff_code STRING
rate_component STRING         -- Generation/Demand/Fixed/Capacity
time_band STRING              -- Red/Amber/Green
unit_rate FLOAT64             -- Rate in p/kWh
unit STRING                   -- p/kWh, £/kVA/day
effective_from DATE
effective_to DATE
year INT64
season STRING
day_type STRING
```

---

### 2. DNO Reference Data (✅ POPULATED)

#### ✅ `gb_power.dno_license_areas`
- **Status**: POPULATED (14 rows)
- **Schema**: 13 columns
- **Purpose**: Complete list of UK DNO license areas

**All 14 UK DNOs**:

| MPAN | DNO Code | DNO Name | GSP | Group |
|------|----------|----------|-----|-------|
| 10 | UKPN-EPN | UK Power Networks (Eastern) | A | UKPN |
| 11 | NGED-EMID | National Grid ED (East Midlands) | B | NGED |
| 12 | UKPN-LPN | UK Power Networks (London) | C | UKPN |
| 13 | SPEN-SPM | SP Energy Networks (Manweb) | D | SPEN |
| 14 | NGED-WMID | National Grid ED (West Midlands) | E | NGED |
| 15 | NPg-NE | Northern Powergrid (North East) | F | NPg |
| 16 | ENWL | Electricity North West | G | ENWL |
| 17 | SSEN-SHEPD | Scottish Hydro | P | SSEN |
| 18 | SPEN-SPD | SP Energy Networks (Scotland) | N | SPEN |
| 19 | UKPN-SPN | UK Power Networks (South East) | J | UKPN |
| 20 | SSEN-SEPD | Southern Electric | H | SSEN |
| 21 | NGED-SWALES | National Grid ED (South Wales) | K | NGED |
| 22 | NGED-SWEST | National Grid ED (South West) | L | NGED |
| 23 | NPg-Y | Northern Powergrid (Yorkshire) | M | NPg |

#### ✅ `uk_energy_prod.neso_dno_reference`
- **Status**: POPULATED (14 rows)
- **Additional info**: Contact details, websites, market participant IDs

#### ✅ `uk_energy_prod.neso_dno_boundaries`
- **Status**: POPULATED (14 rows)
- **Type**: GEOGRAPHY
- **Purpose**: Geographic boundaries for mapping

---

## Typical DUoS Tariff Structure

### Example Time Bands (varies by DNO):

**Red Band** (Peak demand)
- Weekdays 16:00-19:00 (Nov-Feb)
- Highest rates: **15-25 p/kWh**

**Amber Band** (Shoulder periods)
- Weekdays 08:00-16:00, 19:00-20:00
- Medium rates: **3-8 p/kWh**

**Green Band** (Off-peak)
- Nights, weekends
- Lowest rates: **0.5-2 p/kWh**

### Charge Components:
1. **Unit Rate** (p/kWh) - Based on consumption
2. **Capacity Charge** (£/kVA/day) - Based on maximum demand
3. **Fixed Charge** (£/day) - Standing charge
4. **Reactive Power** (p/kVArh) - Power factor penalty

### Voltage Levels (affects pricing):
- **EHV** (22kV+): Cheapest (closer to transmission)
- **HV** (6.6-22kV): Medium pricing
- **LV** (230/400V): Most expensive (furthest from source)

---

## Data Sources for Population

### 1. Individual DNO Websites

**UK Power Networks (3 areas)**
- Website: https://www.ukpowernetworks.co.uk/charges
- Covers: Eastern, London, South Eastern
- Format: PDF charging statements + CSV

**National Grid Electricity Distribution (4 areas)**
- Website: https://www.nationalgridelectricity.com/
- Covers: East Midlands, West Midlands, South Wales, South West
- Format: CDCM/EDCM charging statements

**Scottish & Southern Electricity Networks (2 areas)**
- Website: https://www.ssen.co.uk/
- Covers: Southern, North Scotland (SHEPD)

**Northern Powergrid (2 areas)**
- Website: https://www.northernpowergrid.com/charges
- Covers: North East, Yorkshire

**Electricity North West (1 area)**
- Website: https://www.enwl.co.uk/

**SP Energy Networks (2 areas)**
- Website: https://www.spenergynetworks.co.uk/
- Covers: Scotland (SPD), Manweb (SPM)

### 2. Regulatory Sources

**Ofgem** (Energy Regulator)
- https://www.ofgem.gov.uk/
- Publishes approved charging methodologies
- Annual charging statements

**ELEXON** (Market Administrator)
- https://www.elexon.co.uk/
- Line Loss Factors (LLFs)
- Settlement data

### 3. Common Data Formats

- **CDCM**: Common Distribution Charging Methodology
- **EDCM**: Extra High Voltage Distribution Charging Methodology
- **LLFs**: Line Loss Factors by GSP
- **EHV/HV/LV Tariff Schedules**

---

## Example Queries (Once Data Populated)

### Get Current DUoS Rates for DNO:
```sql
SELECT 
    t.tariff_name,
    t.voltage_level,
    r.time_band,
    r.unit_rate,
    tb.start_time,
    tb.end_time
FROM `inner-cinema-476211-u9.gb_power.duos_tariff_definitions` t
JOIN `inner-cinema-476211-u9.gb_power.duos_unit_rates` r
    ON t.tariff_id = r.tariff_id
JOIN `inner-cinema-476211-u9.gb_power.duos_time_bands` tb
    ON r.dno_key = tb.dno_key AND r.time_band = tb.time_band
WHERE t.dno_key = 'UKPN-EPN'
  AND CURRENT_DATE() BETWEEN r.effective_from 
      AND COALESCE(r.effective_to, '2099-12-31')
ORDER BY r.time_band, tb.start_time;
```

### Calculate DUoS Cost for Settlement Period:
```sql
WITH settlement_period AS (
    SELECT 
        TIMESTAMP '2025-11-09 17:30:00' as period_time,
        100.0 as consumption_kwh,
        'UKPN-EPN' as dno_key
)
SELECT 
    sp.*,
    tb.time_band,
    r.unit_rate,
    (sp.consumption_kwh * r.unit_rate / 100) as duos_cost_gbp
FROM settlement_period sp
JOIN `inner-cinema-476211-u9.gb_power.duos_time_bands` tb
    ON sp.dno_key = tb.dno_key
    AND EXTRACT(TIME FROM sp.period_time) 
        BETWEEN tb.start_time AND tb.end_time
    AND EXTRACT(MONTH FROM sp.period_time) 
        BETWEEN tb.start_month AND tb.end_month
JOIN `inner-cinema-476211-u9.gb_power.duos_unit_rates` r
    ON tb.dno_key = r.dno_key AND tb.time_band = r.time_band
WHERE CURRENT_DATE() BETWEEN r.effective_from 
    AND COALESCE(r.effective_to, '2099-12-31');
```

### Compare Rates Across DNOs:
```sql
SELECT 
    d.dno_name,
    AVG(CASE WHEN r.time_band = 'Red' THEN r.unit_rate END) as red_rate,
    AVG(CASE WHEN r.time_band = 'Amber' THEN r.unit_rate END) as amber_rate,
    AVG(CASE WHEN r.time_band = 'Green' THEN r.unit_rate END) as green_rate
FROM `inner-cinema-476211-u9.gb_power.dno_license_areas` d
LEFT JOIN `inner-cinema-476211-u9.gb_power.duos_unit_rates` r
    ON d.dno_key = r.dno_key
WHERE r.year = 2025 AND r.voltage_level = 'HV'
GROUP BY d.dno_name
ORDER BY red_rate DESC;
```

---

## Next Steps to Populate

### Option 1: Simplified Representative Rates (RECOMMENDED FIRST)
**Fastest approach for analysis**:
1. Create typical Red/Amber/Green rates by voltage level
2. Average across all DNOs
3. Good enough for strategic battery arbitrage analysis
4. Can refine with specific DNO data later

**Example Insert**:
```sql
INSERT INTO `inner-cinema-476211-u9.gb_power.duos_unit_rates` VALUES
('rate_001', 'generic_hv', 'ALL', 'GENERIC-HV', 'Demand', 'Red', 18.5, 'p/kWh', '2025-01-01', '2025-12-31', 2025, 'All', 'All'),
('rate_002', 'generic_hv', 'ALL', 'GENERIC-HV', 'Demand', 'Amber', 4.2, 'p/kWh', '2025-01-01', '2025-12-31', 2025, 'All', 'All'),
('rate_003', 'generic_hv', 'ALL', 'GENERIC-HV', 'Demand', 'Green', 0.85, 'p/kWh', '2025-01-01', '2025-12-31', 2025, 'All', 'All');
```

### Option 2: Manual Data Entry
1. Download tariff tables from DNO websites
2. Parse PDF/Excel charging statements
3. Structure into BigQuery schema
4. Load using `bq load` or Python

### Option 3: Automated Scraping
1. Create scrapers for each DNO website
2. Extract tariff PDFs or HTML tables
3. Parse with pandas/pdfplumber
4. Transform to schema format
5. Automated upload to BigQuery

### Option 4: Commercial Data Service
- Subscribe to commercial tariff data feed
- ELEXON Portal Pro subscription
- Energy market data providers

---

## Use Cases (Why You Need This)

### 1. Battery Arbitrage Optimization
Calculate true profitability including DUoS costs:
```
Revenue = (High Price - Low Price) × Capacity × Efficiency
Cost = DUoS Red Band Charge + DUoS Green Band Charge + Losses
Net Profit = Revenue - Cost
```

### 2. Demand Response Profitability
Value of load shifting from Red to Green bands:
```
Savings = Consumption × (Red Rate - Green Rate)
```

### 3. Flexibility Service Valuation
Grid services value varies by DNO and time band

### 4. Network Constraint Modeling
High DUoS areas indicate network constraints

### 5. VLP Revenue Analysis
Virtual Lead Party units arbitrage across time bands

---

## Related Files in Repository

- **DNO Map**: `DNO_MAP_IMPLEMENTATION.md`
- **DNO Coverage**: `DNO_COVERAGE_COMPLETE.md`
- **Statistical Analysis**: `STATISTICAL_ANALYSIS_GUIDE.md`
- **VLP Analysis**: `HIGH_PRICE_ANALYSIS_AND_OWNERSHIP.md`

---

## Technical Notes

### BigQuery Dataset Locations:
- `gb_power`: **EU** region (London)
- `uk_energy_prod`: **US** region
- Must specify correct location when querying

### Connection Example:
```python
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

# For gb_power (DUoS tables)
client_eu = bigquery.Client(project='inner-cinema-476211-u9', location='EU')

# For uk_energy_prod (market data)
client_us = bigquery.Client(project='inner-cinema-476211-u9', location='US')
```

---

## Summary

### ✅ What You Have:
- Excellent table structure (ready for data)
- Complete DNO reference data (14 areas)
- World-class market data (884M+ rows)
- Geographic boundaries for mapping

### ⚠️ What You Need:
- Actual DUoS tariff rates from DNOs
- Red/Amber/Green time band definitions
- Current year charging data

### 💡 Recommendation:
**Start with Option 1** (simplified representative rates) to enable immediate battery arbitrage analysis. Refine with specific DNO data as needed.

---

**Report Generated**: 9 November 2025  
**Status**: Structure ready, data needed  
**Priority**: Medium (for advanced analysis)  
**Quick Win**: Use simplified rates for initial modeling

---

## Commands Reference

### List DNOs:
```bash
bq query --use_legacy_sql=false --location=EU "
SELECT dno_key, dno_name, gsp_group_name 
FROM \`inner-cinema-476211-u9.gb_power.dno_license_areas\`
ORDER BY mpan_id"
```

### Check Table Schemas:
```bash
bq show --schema --location=EU inner-cinema-476211-u9:gb_power.duos_tariff_definitions
bq show --schema --location=EU inner-cinema-476211-u9:gb_power.duos_time_bands
bq show --schema --location=EU inner-cinema-476211-u9:gb_power.duos_unit_rates
```

### Python Query:
```python
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='EU')
query = "SELECT * FROM `inner-cinema-476211-u9.gb_power.dno_license_areas`"
df = client.query(query).to_dataframe()
print(df)
```
