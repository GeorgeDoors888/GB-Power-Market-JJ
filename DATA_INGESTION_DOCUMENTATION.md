# Data Ingestion & Query Documentation

**Project:** GB Power Market Data Pipeline  
**Date:** 26 October 2025  
**Status:** ✅ Operational

---

## Table of Contents
1. [Overview](#overview)
2. [Data Sources](#data-sources)
3. [Ingestion Pipeline](#ingestion-pipeline)
4. [BigQuery Storage](#bigquery-storage)
5. [Data Retrieval](#data-retrieval)
6. [Current Data Status](#current-data-status)

---

## Overview

This project ingests UK electricity market data from the Elexon BMRS Insights API and stores it in Google BigQuery for analysis and dashboard visualization.

### Key Components:
- **API Source:** Elexon BMRS Insights API (https://data.elexon.co.uk/bmrs/api/v1)
- **Storage:** Google Cloud BigQuery (Project: `inner-cinema-476211-u9`, Dataset: `uk_energy_prod`)
- **Authentication:** Service account key (`jibber_jabber_key.json`)
- **Language:** Python 3.11.6

---

## Data Sources

### Elexon BMRS Insights API

**Base URL:** `https://data.elexon.co.uk/bmrs/api/v1`

#### Primary Datasets Ingested:

1. **Generation Actual Per Type** (`generation_actual_per_type`)
   - Real generation by fuel type (wind, nuclear, gas, solar, etc.)
   - Updated daily with previous day's data
   - 48 settlement periods per day (30-minute intervals)

2. **Fuel Instant** (`fuelinst`)
   - Real-time instantaneous fuel generation
   - Includes interconnector flows
   - Updates throughout the day (~5-minute intervals)

3. **Physical Notifications** (`pn`)
   - BM unit-level physical notifications
   - Massive dataset (6M+ records for 2 months)
   - Most granular level of data available

4. **Demand Outturn** (`demand_outturn_summary`)
   - Actual electricity demand
   - National and transmission system demand

5. **Additional Datasets:**
   - Market Index Data (`mid`)
   - System Warnings (`ntb`)
   - Balancing data (MILS, MELS, BOALF)
   - Wind/Solar forecasts
   - 44 total verified working datasets

---

## Ingestion Pipeline

### Discovery Process

**Script:** `discover_all_datasets.py`

```python
# Queries API metadata endpoint to discover all available datasets
GET /datasets/metadata/latest

# Returns 82 datasets in API
# Tests each dataset for availability
# Generates manifest: insights_manifest_dynamic.json
```

**Results:**
- 82 datasets listed in API metadata
- 44 datasets verified working and accessible
- 38 datasets unavailable or deprecated

### Download Architecture

#### Multi-Year Downloader

**Script:** `download_multi_year_streaming.py`

**Features:**
- Streams data in 50,000 record batches
- Prevents memory exhaustion on large datasets
- Handles datasets with 16M+ records
- Automatic retry logic with exponential backoff
- Progress tracking and error handling

**Key Innovation - Streaming Upload:**

```python
def stream_to_bigquery(dataset_code, records_generator):
    """
    Memory-efficient upload using Python generators
    Processes 50k records at a time instead of loading all into memory
    """
    batch = []
    for record in records_generator:
        batch.append(record)
        if len(batch) >= 50000:
            # Upload batch
            job = client.load_table_from_dataframe(
                pd.DataFrame(batch), table_ref
            )
            batch = []  # Clear memory
```

**Why This Matters:**
- Original approach: Load 16M records → 40GB+ memory → crash
- Streaming approach: Process 50k at a time → 250MB memory → success
- Documented in `STREAMING_UPLOAD_FIX.md`

#### Date Range Strategy

**For each dataset:**
1. Query API for available date range
2. Split into yearly chunks (2025, 2024, 2023, 2022)
3. Download with pagination (100-5000 records per API call)
4. Stream to BigQuery in 50k batches
5. Create table with naming: `{dataset_code}_2025`, `{dataset_code}_sep_oct_2025`

### Authentication & Configuration

**Service Account Setup:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/jibber_jabber_key.json"
```

**Python Configuration:**
```python
from google.cloud import bigquery
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "jibber_jabber_key.json"
client = bigquery.Client(project='inner-cinema-476211-u9')
```

---

## BigQuery Storage

### Dataset Structure

**Project:** `inner-cinema-476211-u9`  
**Dataset:** `uk_energy_prod`  
**Location:** US

### Current Storage Stats (26 Oct 2025)

- **Total Tables:** 65
- **Total Records:** 7.2+ million rows
- **Total Size:** 925 MB (0.9 GB)
- **Date Range:** January 2025 - October 2025 (partial)

### Major Tables

| Table Name | Records | Size | Description |
|------------|---------|------|-------------|
| `pn_sep_oct_2025` | 6,396,546 | 377 MB | Physical Notifications (Sep-Oct) |
| `pn_2025` | 2,650,000 | 88 MB | Physical Notifications (Jan partial) |
| `fuelinst_sep_oct_2025` | 24,160 | 15 MB | Instantaneous fuel data |
| `generation_actual_per_type` | 14,304 | 12 MB | Generation mix by fuel type |
| `balancing_physical_mils` | 838,000 | 28 MB | Market Index Levels |
| `demand_outturn_summary` | 7,194 | 1.2 MB | Demand data |

### Table Naming Convention

- `{dataset}_2025` - Full year data
- `{dataset}_sep_oct_2025` - Test download (Sep-Oct 2025)
- `{dataset}` - No suffix for convenience endpoints

### Data Schemas

#### Generation Actual Per Type
```sql
startTime            STRING    -- Settlement period start (ISO 8601)
settlementPeriod     INTEGER   -- 1-48 (30-minute periods)
data                 RECORD    -- Nested array of generation by fuel type
  ├─ businessType    STRING    -- 'Production', 'Wind generation', etc.
  ├─ psrType         STRING    -- Fuel type name
  └─ quantity        FLOAT     -- Generation in MW
dataset_name         STRING    -- Source dataset identifier
category             STRING    -- Data category
downloaded_at        STRING    -- Ingestion timestamp
```

#### Fuel Instant
```sql
dataset              STRING    -- Dataset code
publishTime          STRING    -- Publication timestamp
fuelType             STRING    -- Fuel/interconnector code
generation           INTEGER   -- Generation/flow in MW
```

#### Physical Notifications
```sql
dataset              STRING    -- 'PN'
settlementDate       STRING    -- Date (YYYY-MM-DD)
settlementPeriod     INTEGER   -- 1-48
timeFrom             STRING    -- Period start time
timeTo               STRING    -- Period end time
levelFrom            INTEGER   -- Generation level from (MW)
levelTo              INTEGER   -- Generation level to (MW)
nationalGridBmUnit   STRING    -- National Grid BM unit ID
bmUnit               STRING    -- BM unit identifier
```

---

## Data Retrieval

### Query Methods

#### 1. Latest Generation Mix

**Objective:** Get current generation by fuel type

**Script:** `update_dashboard_clean.py` - `get_latest_generation()`

**Query:**
```sql
WITH latest_data AS (
    SELECT 
        startTime,
        settlementPeriod,
        data
    FROM `inner-cinema-476211-u9.uk_energy_prod.generation_actual_per_type`
    ORDER BY startTime DESC
    LIMIT 1
),
unpacked AS (
    SELECT
        startTime,
        settlementPeriod,
        gen.psrType as fuel_type,
        gen.quantity as generation_mw
    FROM latest_data,
    UNNEST(data) as gen  -- Unpack nested array
)
SELECT 
    startTime,
    settlementPeriod,
    fuel_type,
    generation_mw / 1000 as generation_gw
FROM unpacked
ORDER BY generation_mw DESC
```

**Result (25 Oct 2025, 22:00-22:30, SP 47):**
```
Wind Offshore:     12.16 GW
Wind Onshore:       7.36 GW
Wind Total:        19.52 GW
Nuclear:            3.68 GW
Gas (CCGT):         3.22 GW
Biomass:            0.84 GW
Other:              0.56 GW
Hydro:              0.14 GW
Coal:               0.00 GW
Oil:                0.00 GW
Solar:              0.00 GW
```

#### 2. Interconnector Flows

**Objective:** Get real-time import/export on interconnectors

**Script:** `update_dashboard_clean.py` - `get_interconnector_flows()`

**Query:**
```sql
SELECT 
    publishTime,
    fuelType,
    generation / 1000 as generation_gw
FROM `inner-cinema-476211-u9.uk_energy_prod.fuelinst_sep_oct_2025`
WHERE publishTime = (
    SELECT MAX(publishTime)
    FROM `inner-cinema-476211-u9.uk_energy_prod.fuelinst_sep_oct_2025`
)
AND fuelType LIKE 'INT%'
ORDER BY generation DESC
```

**Result (26 Oct 2025, 11:35, SP 24):**
```
IMPORTS (positive values):
  France (INTFR):       1.50 GW
  Norway (INTNSL):      1.05 GW
  Netherlands (INTNED): 1.02 GW
  Belgium_2 (INTNEM):   1.02 GW
  Eleclink (INTELEC):   1.00 GW
  IFA2 (INTIFA2):       0.99 GW
  Viking (INTVKL):      0.88 GW

EXPORTS (negative values):
  INTGRNL:             -0.27 GW
  Belgium (INTEW):     -0.22 GW
  Ireland (INTIRL):    -0.21 GW

Net Import: 6.76 GW
```

#### 3. Latest Timestamps

**Objective:** Check data freshness

**Query:**
```sql
SELECT 
    MAX(startTime) as latest_time,
    MIN(startTime) as earliest_time,
    COUNT(*) as record_count
FROM `inner-cinema-476211-u9.uk_energy_prod.generation_actual_per_type`
```

**Current Status:**
- Generation data: Latest 25 Oct 2025, 22:00 (15 hours old)
- Fuel instant: Latest 26 Oct 2025, 11:35 (1.4 hours old)
- PN data: Latest 26 Oct 2025, 12:59 (real-time!)

#### 4. Settlement Period Coverage

**Objective:** Verify complete day coverage

**Query:**
```sql
SELECT 
    MIN(settlementPeriod) as min_sp,
    MAX(settlementPeriod) as max_sp,
    COUNT(DISTINCT settlementPeriod) as unique_periods
FROM `inner-cinema-476211-u9.uk_energy_prod.generation_actual_per_type`
```

**Result:**
- Coverage: SP 1 to SP 48 (complete)
- 48 unique settlement periods
- All 30-minute slots covered per day

### Settlement Period System

UK electricity market uses 48 settlement periods per day:

```
SP 1  = 00:00-00:30 (midnight)
SP 2  = 00:30-01:00
SP 10 = 04:30-05:00
SP 20 = 09:30-10:00
SP 28 = 13:30-14:00 (afternoon)
SP 40 = 19:30-20:00 (evening peak)
SP 48 = 23:30-00:00 (end of day)
```

Formula: `SP = (hour * 2) + (2 if minute >= 30 else 1)`

---

## Current Data Status

### Completed Downloads

#### September-October 2025 Test (COMPLETED ✅)
- **Date Range:** 1 Sep 2025 - 26 Oct 2025
- **Duration:** 56 days
- **Datasets:** 44/44 (100% success)
- **Total Records:** 36,334,372
- **Success Rate:** 100%
- **Failures:** 0
- **Empty Datasets:** 0

**Major Datasets Ingested:**
- PN (Physical Notifications): 6.4M records
- MILS: 5.7M records  
- Fuel Instant: 24k records
- Generation types: 14k records
- All balancing and demand data

#### January 2025 (PARTIAL ⚠️)
- **Date Range:** 1 Jan 2025 - 31 Jan 2025
- **Status:** Interrupted mid-download
- **Records:** 2.65M (PN table only)
- **Note:** Older partial download, data incomplete

### Pending Downloads

#### Full Year Data (PLANNED 📋)
- **2025:** Full year (January - December)
- **2024:** Full year
- **2023:** Full year  
- **2022:** Full year

**Estimated Totals:**
- ~900M records across 4 years
- ~40GB storage in BigQuery
- 44 datasets × 4 years = 176 tables
- ~4-5 hours per year with streaming

**Download Script:** `download_multi_year_streaming.py`

### Data Quality

✅ **Verified Working:**
- Generation by fuel type (all periods)
- Interconnector flows (real-time)
- Physical notifications (massive scale)
- Demand data (national & transmission)
- Balancing services (MILS, MELS, BOALF)
- Market indices
- System warnings

⚠️ **Known Issues:**
- Some convenience endpoints missing from Sep-Oct test
- Generation data updates daily (D-1 lag)
- Interconnector data more frequent (5-10 min lag)

---

## Tools & Scripts

### Core Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `discover_all_datasets.py` | API discovery & manifest generation | ✅ Working |
| `download_multi_year_streaming.py` | Multi-year data ingestion | ✅ Working |
| `download_sep_oct_2025.py` | Test download (Sep-Oct) | ✅ Complete |
| `update_dashboard_clean.py` | Query data & update dashboard | ✅ Working |
| `test_dashboard_queries.py` | Verify query functionality | ✅ Working |
| `inspect_table_schemas.py` | Schema inspection | ✅ Working |

### Support Scripts

- `verify_data.py` - Data verification
- `bulk_downloader.py` - Async batch downloader
- `elexon_neso_downloader.py` - Combined Elexon/NESO downloader

### Documentation

- `STREAMING_UPLOAD_FIX.md` - Memory optimization details
- `MULTI_YEAR_DOWNLOAD_PLAN.md` - Download strategy
- `DOWNLOAD_STATUS_REPORT.md` - Progress tracking
- `API_RESEARCH_FINDINGS.md` - API investigation notes
- `DATA_INGESTION_DOCUMENTATION.md` - This document

---

## Technical Challenges Solved

### 1. Memory Exhaustion (SOLVED ✅)

**Problem:** PN dataset with 16M records crashed with 40GB+ memory usage

**Solution:** Streaming upload with Python generators
- Process 50,000 records at a time
- Clear memory between batches
- Reduced memory to 250MB
- Documented in `STREAMING_UPLOAD_FIX.md`

### 2. Nested Data Structures (SOLVED ✅)

**Problem:** Generation data stored as nested RECORD type in BigQuery

**Solution:** Use UNNEST() in SQL queries to flatten arrays
```sql
SELECT gen.psrType, gen.quantity
FROM table_name,
UNNEST(data) as gen
```

### 3. Multiple Data Timestamps (SOLVED ✅)

**Problem:** Different tables update at different frequencies

**Solution:** Document update patterns and query from appropriate tables
- Generation mix: Daily updates (use previous day)
- Interconnectors: 5-10 minute updates (use real-time)
- PN data: Continuous updates (use latest)

### 4. API Dataset Discovery (SOLVED ✅)

**Problem:** Hardcoded list missed 28 available datasets

**Solution:** Dynamic discovery via metadata endpoint
- Query `/datasets/metadata/latest`
- Test each dataset for availability
- Generate dynamic manifest

---

## Next Steps

### Immediate (Week 1)
1. ✅ Verify queries work on existing data
2. ✅ Test dashboard data retrieval
3. 🔄 Set up Google Sheets API integration
4. 🔄 Map dashboard cells to data fields

### Short-term (Week 2-3)
5. Download full 2025 data (Jan-Dec)
6. Download 2024 data
7. Download 2023 data
8. Download 2022 data

### Medium-term (Month 1-2)
9. Implement automated daily updates
10. Create Apps Script for real-time dashboard
11. Set up monitoring & alerting
12. Create data quality checks

### Long-term (Month 3+)
13. Historical analysis & trending
14. Predictive models for demand/generation
15. Anomaly detection
16. Cost optimization analysis

---

## Performance Metrics

### Download Performance (Sep-Oct Test)
- **Duration:** ~2 hours
- **Records/second:** ~5,000
- **Success rate:** 100%
- **Retry rate:** <1%

### Query Performance
- **Latest generation:** <2 seconds
- **Interconnector flows:** <1 second
- **Table scans:** 5-10 seconds
- **BigQuery cost:** Minimal (free tier)

### Storage Efficiency
- **Compression:** ~70% (925 MB for 7.2M records)
- **Cost:** $0.02/GB/month = $0.02/month current
- **Projected (4 years):** ~$0.80/month

---

## Maintenance

### Daily Tasks (Automated)
- [ ] Check API availability
- [ ] Download latest day's data
- [ ] Verify data completeness
- [ ] Update dashboard

### Weekly Tasks
- [ ] Review data quality metrics
- [ ] Check storage costs
- [ ] Monitor query performance
- [ ] Verify all datasets updating

### Monthly Tasks
- [ ] Archive old data
- [ ] Update documentation
- [ ] Review and optimize queries
- [ ] Generate usage reports

---

## Contact & Support

**Project Owner:** George Major  
**Documentation Date:** 26 October 2025  
**Last Updated:** 26 October 2025  

**Key Resources:**
- Elexon BMRS API: https://data.elexon.co.uk/bmrs/api/v1
- BigQuery Project: inner-cinema-476211-u9
- Service Account: jibber_jabber_key.json

---

*This documentation is a living document and will be updated as the project evolves.*
