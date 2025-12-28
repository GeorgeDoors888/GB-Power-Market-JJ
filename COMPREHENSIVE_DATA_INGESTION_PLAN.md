# Comprehensive Elexon & NESO Data Ingestion Plan

**Date**: 27 December 2025
**Objective**: Ingest ALL 100+ Elexon and NESO published datasets
**Timeline**: Q1-Q4 2026
**Storage**: 1-2 TB BigQuery (estimated)

---

## Phase 1: Complete Historical Backfill (Q1 2026)
**Goal**: Get ALL existing datasets back to 2016

### 1.1 COSTS Backfill ✅ IN PROGRESS
```bash
# RUNNING NOW: backfill_historical_2016_2021.py
# Target: bmrs_costs (2016-2021)
# Expected: ~105,000 records (6 years × 365 days × 48 periods)
# Status: Processing 2016...
```

### 1.2 BOD Backfill 🚀 NEXT
```python
# Script: backfill_bod_2016_2021.py
# API: /bmrs/api/v1/datasets/BOD?from=2016-01-01&to=2016-12-31
# Expected: ~200k rows/day × 365 days × 6 years = ~438M rows
# Storage: ~50 GB (partitioned by settlementDate)
# Runtime: ~3-4 hours (0.05s per day × 2,190 days)

def backfill_bod(year):
    url = f'{BMRS_BASE}/BOD'
    for each day:
        params = {'from': date_str, 'to': date_str}
        response = requests.get(url, params=params)
        # Upload in chunks of 10,000 rows
```

**Critical**: BOD is HUGE (391M existing + 438M historical = 829M rows total)

### 1.3 MID Backfill
```python
# Script: backfill_mid_2016_2021.py
# API: /bmrs/api/v1/datasets/MID
# Expected: 48 rows/day × 365 × 6 = ~105,000 rows
# Storage: <1 GB
# Runtime: ~20 minutes
```

### 1.4 DISBSAD Backfill
```python
# Script: backfill_disbsad_2016_2021.py
# API: /bmrs/api/v1/balancing/disbsad/{date}
# Expected: Variable rows/day (balancing actions)
# Storage: ~5 GB
# Runtime: ~1 hour
```

### 1.5 Other Historical Tables
Extend backfill to ALL 174 existing tables:
- FREQ, FUELINST, FUELHH (fuel/frequency)
- INDGEN, WINDFOR (generation/wind)
- PN, QPN, RDRE, RDRI, RURE, RURI (notifications)
- TEMP, B1770, B1610, B1630 (temperatures, transparency)

**Automation**:
```bash
# Master backfill script
python3 backfill_all_tables.py --start 2016-01-01 --end 2021-12-31 --tables ALL
```

---

## Phase 2: ~~Per-BM-Unit Granularity~~ Settlement & Reference Data (Q2 2026)
**CRITICAL UPDATE**: Per-unit BOD already exists! (bmUnit column in bmrs_bod table)

### 2.1 ~~Individual BM Unit BOD~~ ✅ ALREADY HAVE THIS!
**DISCOVERY (27 Dec 2025)**: `bmrs_bod` table ALREADY contains per-BM-unit data!
- ✅ bmUnit column exists (column 12 of 20)
- ✅ 407M rows of per-unit bid-offer data (2022-2025, now backfilling 2020-2021)
- ✅ derive_boalf_prices.py already joins by bmUnit (line 195)
- ✅ VLP revenue calculations ALREADY use per-unit pricing

**No action needed** - this "gap" was documentation error!

**Sample Data** (bmrs_bod):
```sql
SELECT bmUnit, settlementDate, settlementPeriod, offer, bid, levelFrom, levelTo, pairId
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE bmUnit = '2__FBPGM002' AND settlementDate = '2025-10-17' AND settlementPeriod = 37
-- Returns: FBPGM002 offers £129.08-£140.49/MWh, bids £71.27-£78.77/MWh
```

### 2.2 Per-Unit Settlement Data (P114) 🚨 HIGH PRIORITY
**Problem**: We have system-level settlement, but not per-BM-unit charges

**Elexon P114 License** required for full SAA-I014 reports:
- ~370 data items per BM Unit per Settlement Period
- Metered volumes, imbalance charges, transmission losses
- BSC Parties get own data free
- Non-parties need license (fee)

**Alternative**: Use **Open Settlement Data** (aggregated)
- Available on Elexon Portal (free)
- Aggregate Party Day Charges
- Trading Unit Period Information
- System Period Data

**Implementation**:
```python
# Script: ingest_open_settlement_data.py
# Download monthly CSV files from Elexon Portal
# Tables: settlement_party_charges, settlement_trading_unit, settlement_system
```

---

## Phase 3: ENTSO-E Transparency (Q2 2026)
**Goal**: Get generation unit availability, outages, installed capacity

### 3.1 Generation Unit Outages (B1510/B1520)
**Elexon BMRS API - ENTSO-E Transparency Platform**

**Datasets**:
- **B1510**: Installed Generation Capacity Aggregated (by fuel type)
- **B1520**: Installed Generation Capacity per Unit (individual generators)
- **B1530**: Actual Generation Output per Generation Unit
- **B1610**: Actual Generation Output per Production Type
- **B1620**: Day-Ahead Aggregated Generation
- **B1630**: Actual Aggregated Generation per Type

**New Tables**:
```sql
-- B1520: Per-unit installed capacity
CREATE TABLE bmrs_b1520_installed_capacity (
  settlementDate DATE,
  bmUnitId STRING,
  registeredResourceEICCode STRING,
  installedCapacity FLOAT64,  -- MW
  effectiveDate DATE,
  _ingested_utc TIMESTAMP
);

-- B1510: Aggregated by fuel type
CREATE TABLE bmrs_b1510_capacity_agg (
  settlementDate DATE,
  fuelType STRING,
  installedCapacity FLOAT64,  -- MW
  _ingested_utc TIMESTAMP
);
```

**API**:
```python
# Check if ingest_elexon_fixed.py already handles these
# If not, add to CHUNK_RULES and dataset list

CHUNK_RULES['B1510'] = '7d'
CHUNK_RULES['B1520'] = '7d'
CHUNK_RULES['B1530'] = '1d'
CHUNK_RULES['B1610'] = '1d'
CHUNK_RULES['B1620'] = '1d'
CHUNK_RULES['B1630'] = '1d'

# Then run ingest_elexon_fixed.py with these datasets
python3 ingest_elexon_fixed.py --start 2022-01-01 --end 2025-12-27 --only B1510,B1520,B1530,B1610,B1620,B1630
```

**Use Cases**:
- Generator outage impact on prices
- Capacity margin analysis (available vs installed)
- Maintenance schedule correlation
- Forced outage frequency

---

## Phase 4: NESO Data Portal Integration (Q3 2026)
**Goal**: Ingest 50+ NESO-exclusive datasets

### 4.1 NESO Constraint Management
**Datasets**:
1. Day-Ahead Constraint Flows & Limits
2. 24-Month Ahead Constraint Cost Forecast
3. Thermal Constraint Costs
4. Intertrip Constraint Information

**NESO CKAN API**:
```python
# Base URL: https://data.nationalgrideso.com/api/3/action
# Example: datastore_search?resource_id=<RESOURCE_ID>

def fetch_neso_dataset(resource_id):
    url = 'https://data.nationalgrideso.com/api/3/action/datastore_search'
    params = {'resource_id': resource_id, 'limit': 32000}
    response = requests.get(url, params=params)
    return response.json()['result']['records']

# Resource IDs (find on NESO Data Portal)
CONSTRAINT_COSTS_ID = '<find on portal>'
CONSTRAINT_FLOWS_ID = '<find on portal>'
```

**New Tables**:
```sql
CREATE TABLE neso_constraint_costs (
  date DATE,
  constraintType STRING,
  cost FLOAT64,  -- £
  volume FLOAT64,  -- MWh
  _ingested_utc TIMESTAMP
);

CREATE TABLE neso_constraint_flows (
  settlementDate DATE,
  settlementPeriod INT64,
  constraintId STRING,
  forecastFlow FLOAT64,  -- MW
  flowLimit FLOAT64,     -- MW
  _ingested_utc TIMESTAMP
);
```

**Use Cases**:
- Predict constraint-driven high prices
- Regional price analysis
- Network congestion arbitrage

### 4.2 Interconnector Flows (Per-Interconnector)
**Datasets** (6 interconnectors):
1. IFA (France)
2. IFA2 (France)
3. BritNed (Netherlands)
4. NemoLink (Belgium)
5. NSL (Norway)
6. Viking (Denmark)

**NESO Data Portal**:
- CSV downloads per interconnector
- CKAN API access

**New Table**:
```sql
CREATE TABLE neso_interconnector_flows (
  timestamp DATETIME,
  interconnector STRING,  -- IFA, IFA2, BritNed, etc.
  flow FLOAT64,           -- MW (positive=import, negative=export)
  capacity FLOAT64,       -- MW
  status STRING,          -- Operating, Outage, etc.
  _ingested_utc TIMESTAMP
);
```

**Implementation**:
```python
# Script: ingest_neso_interconnectors.py
INTERCONNECTORS = ['IFA', 'IFA2', 'BritNed', 'NemoLink', 'NSL', 'Viking']

for ic in INTERCONNECTORS:
    resource_id = INTERCONNECTOR_RESOURCE_IDS[ic]
    data = fetch_neso_dataset(resource_id)
    upload_to_bigquery(data, 'neso_interconnector_flows')
```

**Use Cases**:
- Cross-border arbitrage analysis
- Import dependency tracking
- Price impact of interconnector flows

### 4.3 NESO Forecasts (Long-Term)
**Datasets**:
1. 7-day ahead demand forecast
2. Long-term 2–52 weeks demand forecast
3. Weekly Wind Availability
4. 14 Days Ahead Operational Metered Wind Forecasts

**New Tables**:
```sql
CREATE TABLE neso_demand_forecast_longterm (
  forecastDate DATE,
  targetDate DATE,
  horizonDays INT64,  -- How many days ahead
  forecastDemand FLOAT64,  -- MW
  _ingested_utc TIMESTAMP
);

CREATE TABLE neso_wind_availability_weekly (
  week DATE,
  availableCapacity FLOAT64,  -- MW
  installedCapacity FLOAT64,  -- MW
  availabilityFactor FLOAT64, -- %
  _ingested_utc TIMESTAMP
);
```

**Use Cases**:
- Long-term capacity planning
- Renewable integration forecasting
- Maintenance scheduling optimization

### 4.4 Carbon Intensity
**Dataset**: National Carbon Intensity Forecast

**NESO Data Portal**:
- Half-hourly forecasts (gCO₂/kWh)
- Updated regularly

**New Table**:
```sql
CREATE TABLE neso_carbon_intensity (
  timestamp DATETIME,
  forecast FLOAT64,  -- gCO₂/kWh
  actual FLOAT64,    -- gCO₂/kWh (if available)
  index STRING,      -- Low, Medium, High, Very High
  _ingested_utc TIMESTAMP
);
```

**Use Cases**:
- Decarbonization tracking
- Green energy dispatch optimization
- Carbon cost forecasting

### 4.5 System Inertia
**Dataset**: System inertia and inertia cost

**New Table**:
```sql
CREATE TABLE neso_system_inertia (
  timestamp DATETIME,
  inertia FLOAT64,  -- GVA·s
  cost FLOAT64,     -- £
  _ingested_utc TIMESTAMP
);
```

**Use Cases**:
- Grid stability analysis
- Frequency response valuation

---

## Phase 5: Balancing Services & Markets (Q3-Q4 2026)

### 5.1 Balancing Services Auctions
**Datasets**:
1. FFR (Firm Frequency Response) - Phase 2 auction results
2. STOR (Short-Term Operating Reserve) - day-ahead results
3. Dynamic Containment/Moderation/Regulation requirements
4. Stability Pathfinder utilization

**New Tables**:
```sql
CREATE TABLE neso_ffr_auctions (
  auctionDate DATE,
  serviceWindow STRING,
  clearedPrice FLOAT64,  -- £/MW/h
  clearedVolume FLOAT64, -- MW
  _ingested_utc TIMESTAMP
);

CREATE TABLE neso_stor_auctions (
  auctionDate DATE,
  deliveryDate DATE,
  clearedPrice FLOAT64,  -- £/MW/h
  clearedVolume FLOAT64, -- MW
  _ingested_utc TIMESTAMP
);

CREATE TABLE neso_dynamic_services (
  date DATE,
  serviceType STRING,  -- DC, DM, DR
  requirement FLOAT64, -- MW
  clearedPrice FLOAT64, -- £/MW/h
  _ingested_utc TIMESTAMP
);
```

**Use Cases**:
- Ancillary service revenue tracking
- Battery storage revenue optimization
- Frequency response market analysis

### 5.2 BSUoS (Balancing Services Use of System)
**Datasets**:
1. Current BSUoS data (daily costs)
2. Daily balancing costs
3. BSUoS forecast tariffs (monthly/fixed)

**New Table**:
```sql
CREATE TABLE neso_bsuos (
  date DATE,
  totalCost FLOAT64,     -- £
  totalVolume FLOAT64,   -- MWh
  tariff FLOAT64,        -- £/MWh
  forecastTariff FLOAT64, -- £/MWh
  _ingested_utc TIMESTAMP
);
```

**Use Cases**:
- Balancing charge forecasting
- System cost analysis

### 5.3 Capacity Market & CfD
**Datasets** (STATIC - update quarterly/annually):
1. Capacity Market Register (generators with CM agreements)
2. Contract for Difference (CfD) allocation data

**New Tables**:
```sql
CREATE TABLE neso_capacity_market_register (
  unitName STRING,
  capacity FLOAT64,  -- MW
  agreementType STRING,
  agreementDuration INT64,  -- years
  auctionYear INT64,
  deliveryYear INT64,
  status STRING,
  _updated_date DATE
);

CREATE TABLE neso_cfd_contracts (
  projectName STRING,
  technology STRING,
  capacity FLOAT64,  -- MW
  strikePrice FLOAT64, -- £/MWh
  contractLength INT64, -- years
  deliveryYear INT64,
  _updated_date DATE
);
```

**Use Cases**:
- Future capacity tracking
- Policy analysis
- Market entry/exit monitoring

---

## Phase 6: Reference Data & Charges (Q4 2026)

### 6.1 Market Domain Data (MDD)
**Elexon Portal** (monthly release):
- Master reference data (Suppliers, DNOs, GSPs)
- Grid Supply Point identifiers
- LLF classes, profile classes
- Essential for interpreting other datasets

**New Tables**:
```sql
CREATE TABLE elexon_mdd_gsp (
  gspGroupId STRING,
  gspName STRING,
  dnoName STRING,
  regionName STRING,
  _release_date DATE
);

CREATE TABLE elexon_mdd_suppliers (
  supplierId STRING,
  supplierName STRING,
  effectiveFrom DATE,
  effectiveTo DATE,
  _release_date DATE
);

CREATE TABLE elexon_mdd_llf_classes (
  llfClassId STRING,
  dno STRING,
  voltageLevel STRING,
  description STRING,
  _release_date DATE
);
```

**Implementation**:
```python
# Script: ingest_mdd_monthly.py
# Download MDD release (CSV) from Elexon Portal
# Parse and upload to BigQuery
# Run monthly (on MDD release schedule)
```

**Use Cases**:
- Data validation
- Reference lookups
- Market structure analysis

### 6.2 TNUoS Tariffs
**NESO Data Portal** (annual):
- Transmission Network Use of System charges
- Generator and supplier tariffs
- Transmission loss factors

**New Table**:
```sql
CREATE TABLE neso_tnuos_tariffs (
  year INT64,
  zone STRING,
  generatorTariff FLOAT64,  -- £/kW/year
  supplierTariff FLOAT64,   -- £/kW/year
  lossFactor FLOAT64,
  _publication_date DATE
);
```

**Use Cases**:
- Transmission cost forecasting
- Generator location optimization

### 6.3 Line Loss Factors (LLF)
**Elexon Portal** (seasonal):
- Seasonal coefficients for distribution losses
- Per DNO and voltage level

**New Table**:
```sql
CREATE TABLE elexon_llf (
  bscSeason INT64,  -- BSC Year & Season
  dno STRING,
  voltageLevel STRING,
  llfClass STRING,
  lossFactor FLOAT64,
  _effective_date DATE
);
```

**Use Cases**:
- Settlement reconciliation
- Distribution loss analysis

---

## Implementation Timeline

### Q1 2026: Historical Backfill
- ✅ COSTS 2016-2021 (in progress)
- 🚀 BOD 2016-2021 (3-4 hours)
- 🚀 MID, DISBSAD, FREQ, FUELINST 2016-2021 (1-2 hours each)
- 🚀 All other 170+ tables 2016-2021 (automate)

### Q2 2026: Per-Unit Granularity
- Per-BM-Unit BOD (bmrs_bod_per_unit) - 146M rows
- ENTSO-E Transparency (B1510/B1520/B1530) - Outages & capacity
- Open Settlement Data (aggregate)

### Q3 2026: NESO Data Portal
- Constraint Management (costs, flows, limits)
- Interconnector Flows (6 interconnectors)
- Long-Term Forecasts (7-52 weeks)
- Carbon Intensity
- System Inertia

### Q4 2026: Services & Reference
- Balancing Services Auctions (FFR, STOR, DC/DM/DR)
- BSUoS Data & Forecasts
- Capacity Market & CfD Registers
- Market Domain Data (MDD)
- TNUoS Tariffs
- Line Loss Factors

---

## Technical Architecture

### Storage Estimate
```
Current:     ~50 GB  (2022-2025, 174 tables)
+ 2016-2021: ~150 GB (6 years historical)
+ Per-unit:  ~20 GB  (bmrs_bod_per_unit)
+ NESO:      ~30 GB  (50+ datasets)
+ Reference: ~5 GB   (MDD, tariffs, etc.)
-----------------------------------------
Total:       ~255 GB BigQuery storage
Cost:        ~£5-10/month (active + long-term)
```

### Ingestion Services
```
1. Historical Batch (Elexon BMRS)
   - Script: ingest_elexon_fixed.py
   - Cron: */15 * * * *
   - Tables: 174+ (expanding to 200+)

2. Real-Time (IRIS/Azure Service Bus)
   - Script: iris_to_bigquery_unified.py
   - Server: AlmaLinux 94.237.55.234
   - Tables: 15+ (*_iris tables)

3. NESO Data Portal
   - Script: ingest_neso_*.py (NEW)
   - Cron: Daily or weekly
   - Tables: 50+ (neso_* tables)

4. Per-Unit BOD
   - Script: ingest_bm_unit_bod.py (NEW)
   - Cron: Daily (backfill then maintain)
   - Table: bmrs_bod_per_unit

5. Reference Data
   - Script: ingest_mdd_monthly.py (NEW)
   - Cron: Monthly
   - Tables: MDD, LLF, TNUoS
```

### Query Architecture
```sql
-- Example: Full bid-offer stack for FBPGM002
SELECT
  b.settlementDate,
  b.settlementPeriod,
  b.bmUnitId,
  b.offerPrice,
  b.offerVolume,
  b.acceptedOfferVolume,
  a.acceptanceTime,
  c.systemSellPrice
FROM bmrs_bod_per_unit b  -- Per-unit BOD
LEFT JOIN bmrs_boalf a USING (bmUnitId, settlementDate, settlementPeriod)
LEFT JOIN bmrs_costs c USING (settlementDate, settlementPeriod)
WHERE b.bmUnitId = 'FBPGM002'
  AND b.settlementDate = '2025-10-17'
ORDER BY b.settlementPeriod, b.offerPrice;

-- Example: Constraint cost impact on prices
SELECT
  c.date,
  c.constraintCost,
  AVG(p.systemSellPrice) as avg_price,
  CORR(c.constraintCost, p.systemSellPrice) as correlation
FROM neso_constraint_costs c
JOIN bmrs_costs p ON c.date = p.settlementDate
GROUP BY c.date, c.constraintCost
ORDER BY c.date DESC;
```

---

## Monitoring & Validation

### Daily Health Checks
```bash
# Check latest data dates
python3 check_all_table_coverage.sh

# Verify row counts
python3 audit_table_counts.py

# Check for gaps
python3 find_data_gaps.py --start 2016-01-01 --end 2025-12-27
```

### Alerts
- Email if data missing >24 hours
- Slack notification for ingestion failures
- BigQuery quota monitoring (>80% usage)

---

## Next Steps (Immediate)

1. ✅ Monitor 2016-2021 COSTS backfill (running now)
2. 🚀 Create `backfill_bod_2016_2021.py` (next priority)
3. 🚀 Audit `ingest_elexon_fixed.py` - verify which datasets active
4. 🚀 Design `bmrs_bod_per_unit` schema (partition strategy)
5. 🚀 Map NESO Data Portal resources (find resource IDs)
6. 🚀 Create `ingest_neso_constraints.py` (extend existing script)
7. 📝 Update documentation with new tables

---

**Last Updated**: 27 Dec 2025 18:00 GMT
**Status**: Phase 1 in progress (COSTS backfill running)
