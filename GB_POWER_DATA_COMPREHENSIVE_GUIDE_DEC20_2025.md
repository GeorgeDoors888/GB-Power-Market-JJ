# GB Power Market - Comprehensive Data Guide (Dec 20, 2025)

## Executive Summary

**Purpose**: Diagnose 5-year data completeness, understand what each dataset does, ensure no gaps/duplicates, and provide consistent analysis framework.

**Key Findings**:
- ✅ **11 primary datasets** operational (bmrs_bod, bmrs_boalf_complete, bmrs_costs, etc.)
- ⚠️ **Known permanent gaps**: bmrs_mid (24 days missing in 2024 - API confirmed unrecoverable)
- ✅ **Dual pipeline**: Historical (2020-2025) + Real-time IRIS (last 48h)
- 🔄 **Backfill status**: bmrs_bod in progress, bmrs_freq completing 2022-2025 backfill

---

## Table of Contents

1. [Two-Pipeline Architecture](#two-pipeline-architecture)
2. [Core Datasets (11 Tables)](#core-datasets-11-tables)
3. [Data Purpose & Business Context](#data-purpose--business-context)
4. [Known Data Gaps & Quality Issues](#known-data-gaps--quality-issues)
5. [Data Consistency Guidelines](#data-consistency-guidelines)
6. [Query Patterns for Complete Timeline](#query-patterns-for-complete-timeline)
7. [External Resources](#external-resources)

---

## Two-Pipeline Architecture

### 1. Historical Pipeline (Long-term Storage)
- **Source**: Elexon BMRS REST API (`https://data.elexon.co.uk/bmrs/api/v1/datasets/`)
- **Coverage**: 2020 → Present (when configured)
- **Update**: On-demand or 15-min cron (varies by table)
- **Tables**: NO suffix (e.g., `bmrs_bod`, `bmrs_costs`)
- **Use Case**: Multi-year analysis, trend identification, regulatory reporting

### 2. IRIS Pipeline (Real-time Streaming)
- **Source**: National Grid IRIS messages via Azure Service Bus
- **Coverage**: Last 24-48 hours (Azure queue retention)
- **Update**: Continuous streaming (every 2-5 minutes)
- **Tables**: `_iris` suffix (e.g., `bmrs_bod_iris`, `bmrs_fuelinst_iris`)
- **Use Case**: Live monitoring, current operations, recent events

### Key Difference: Time Horizon

```
|← Historical (2020-2025) →|← IRIS (last 48h) →|
|  bmrs_bod                 |  bmrs_bod_iris     |
|  bmrs_costs               |  bmrs_fuelinst_iris|
|  bmrs_mid                 |  bmrs_mid_iris     |
```

**CRITICAL**: To get complete recent timeline, UNION historical + IRIS tables (see [Query Patterns](#query-patterns-for-complete-timeline))

---

## Core Datasets (11 Tables)

### 1. Balancing Mechanism (Trading & Acceptances)

#### bmrs_bod
- **Full Name**: Bid-Offer Data
- **Elexon Code**: B1430 (BOD)
- **API Endpoint**: `/datasets/BOD`
- **Purpose**: Individual unit price submissions to balancing mechanism
- **Coverage**: 2022-01-01 → Present (403M+ rows, 1447 days as of Dec 17)
- **Key Columns**:
  - `bmUnitId` (string): Battery unit identifier (e.g., FBPGM002)
  - `settlementDate` (DATE): Trading date
  - `settlementPeriod` (int): Half-hour period (1-50)
  - `bid` (FLOAT64): Bid price (£/MWh) - for DECREASING generation
  - `offer` (FLOAT64): Offer price (£/MWh) - for INCREASING generation
  - `pairId` (int): Bid-offer pair identifier
- **Units**: £/MWh (prices), MW (volumes)
- **Business Use**: Battery arbitrage strategy, marginal price discovery, VLP revenue forecasting
- **CRITICAL**: This is SUBMITTED prices (not necessarily accepted - see bmrs_boalf_complete for acceptances)

#### bmrs_boalf (RAW - NO PRICES)
- **Full Name**: Balancing Acceptances (Level Format)
- **Elexon Code**: B1430 (BOALF)
- **API Endpoint**: `/datasets/BOALF`
- **Purpose**: Which bids/offers National Grid accepted (RAW format without prices)
- **Coverage**: 2022-01-01 → Present (11M+ rows)
- **Key Columns**:
  - `bmUnit` (string): Battery unit ID
  - `timeFrom` (DATETIME): Acceptance start time
  - `timeTo` (DATETIME): Acceptance end time
  - `levelFrom` (FLOAT64): Starting generation level (MW)
  - `levelTo` (FLOAT64): Target generation level (MW)
  - `acceptanceNumber` (int): Unique acceptance ID
- **Units**: MW (level changes), NO PRICE DATA
- **⚠️ CRITICAL LIMITATION**: Elexon BOALF API does NOT include `acceptancePrice`, `acceptanceVolume`, or `acceptanceType` fields
- **Business Use**: Acceptance tracking ONLY - **Use bmrs_boalf_complete for revenue analysis**

#### bmrs_boalf_complete ⭐ PREFERRED
- **Full Name**: Balancing Acceptances WITH PRICES (BOD-matched)
- **Elexon Code**: B1430 (BOALF + BOD derived)
- **API Endpoint**: Derived from `/datasets/BOALF` + `/datasets/BOD`
- **Purpose**: Acceptances with derived prices via BOD matching (Elexon B1610 methodology)
- **Coverage**: 2022-01-01 → Present (2.96M rows, 1446 days as of Dec 17)
- **Key Columns**:
  - `bmUnit` (string): Battery unit ID
  - `timeFrom` (DATETIME): Acceptance start
  - `acceptancePrice` (FLOAT64): Derived price (£/MWh) - **KEY FIELD**
  - `acceptanceVolume` (FLOAT64): Derived volume (MWh)
  - `acceptanceType` (string): 'BID' or 'OFFER'
  - `validation_flag` (string): 'Valid', 'SO_Test', 'Low_Volume', 'Price_Outlier', 'Unmatched'
- **Units**: £/MWh (prices), MWh (volumes)
- **Business Use**: **VLP revenue analysis**, battery arbitrage profitability, balancing mechanism earnings
- **Match Rate**: 85-95% (varies by month, ~71% in Oct 2025)
- **Valid Records**: ~42.8% after Elexon B1610 filtering (4.7M valid records)
- **⚠️ CRITICAL**: Filter to `validation_flag='Valid'` for regulatory-compliant analysis

**Validation Flag Taxonomy**:
| Flag | Meaning | % (Oct 2025) | Use? |
|------|---------|--------------|------|
| `Valid` | Passes Elexon B1610 filters | 42.8% | ✅ Yes |
| `SO_Test` | System Operator test record | 23.7% | ❌ No |
| `Low_Volume` | Volume <0.001 MWh | 15.9% | ❌ No |
| `Price_Outlier` | Price >±£1,000/MWh | ~0% | ❌ No |
| `Unmatched` | No BOD match found | 17.6% | ⚠️ No price |

#### bmrs_disbsad
- **Full Name**: Balancing Services Adjustment Data
- **Elexon Code**: B1780 (DISBSAD)
- **API Endpoint**: `/datasets/DISBSAD`
- **Purpose**: Settlement volume-weighted average prices for balancing services
- **Coverage**: 2022-01-01 → 2025-12-14 (510K rows, 1368 days)
- **Key Columns**:
  - `settlementDate` (DATE): Settlement date
  - `settlementPeriod` (int): Half-hour period
  - `price` (FLOAT64): Volume-weighted average (£/MWh)
  - `volume` (FLOAT64): Total volume (MWh)
- **Units**: £/MWh, MWh
- **Business Use**: Settlement price proxy, balancing cost analysis, use for **comparison** with bmrs_boalf_complete (not primary revenue source)

---

### 2. Pricing Data (System & Market Prices)

#### bmrs_costs ⭐ IMBALANCE PRICES
- **Full Name**: System Imbalance Prices (SSP/SBP)
- **Elexon Code**: B1770 (Imbalance Prices)
- **API Endpoint**: `/datasets/DETSYSPRICES`
- **Purpose**: System IMBALANCE prices for settlement (SSP=SBP since Nov 2015)
- **Coverage**: 2022-01-01 → 2025-12-05 (64.6K rows, 1348 days) - ✅ No gaps
- **Key Columns**:
  - `settlementDate` (DATE): Settlement date
  - `settlementPeriod` (int): Half-hour period
  - `systemSellPrice` (FLOAT64): SSP (£/MWh)
  - `systemBuyPrice` (FLOAT64): SBP (£/MWh) - **IDENTICAL to SSP since Nov 2015**
- **Units**: £/MWh
- **Business Use**: **Battery temporal arbitrage** (charge low, discharge high), imbalance exposure, settlement forecasting
- **⚠️ CRITICAL**: SSP = SBP since BSC Mod P305 (Nov 2015) - both columns exist but values IDENTICAL
  - Battery arbitrage is **TEMPORAL** (price variation over time)
  - NOT SSP/SBP spread (which is zero)
- **Duplicates**: Pre-Oct 27, 2025 data has ~55k duplicate settlement periods (use `GROUP BY` or `DISTINCT`)
- **Data Quality**: Post-Oct 29 data has zero duplicates (automated backfill improved)

#### bmrs_mid
- **Full Name**: Market Index Data (Wholesale Prices)
- **Elexon Code**: B1440 (MID)
- **API Endpoint**: `/datasets/MID`
- **Purpose**: **WHOLESALE** day-ahead and within-day market pricing
- **Coverage**: 2022-01-01 → 2025-12-17 (160K rows) - ⚠️ 24 days permanently missing
- **Key Columns**:
  - `settlementDate` (DATE): Trading date
  - `settlementPeriod` (int): Half-hour period
  - `price` (FLOAT64): Market index price (£/MWh)
  - `volume` (FLOAT64): Traded volume (MWh)
- **Units**: £/MWh (wholesale), MWh
- **Business Use**: Wholesale market analysis, forward curves, **NOT battery imbalance arbitrage**
- **⚠️ KNOWN PERMANENT GAPS**: 24 days missing in 2024:
  - Apr 16-21 (6 days)
  - Jul 16-21 (6 days)
  - Sep 10-15 (6 days)
  - Oct 08-13 (6 days)
  - Root Cause: API confirmed 0 records available
  - Status: **NOT RECOVERABLE** (genuine Elexon API outages)

**CRITICAL DISTINCTION**:
- **bmrs_costs**: System **IMBALANCE** prices (battery settlement)
- **bmrs_mid**: **WHOLESALE** market prices (day-ahead contracts)
- Use `bmrs_costs` for battery arbitrage, NOT `bmrs_mid`

---

### 3. Generation & Demand

#### bmrs_fuelinst ⭐
- **Full Name**: Generation by Fuel Type
- **Elexon Code**: B1620 (FUELINST)
- **API Endpoint**: `/datasets/FUELINST`
- **Purpose**: National-level fuel mix (wind, gas, nuclear, solar, etc.)
- **Coverage**: 2022-12-31 → 2025-12-17 (5.7M rows, 1039 days)
- **Key Columns**:
  - `startTime` (DATETIME): Generation period start
  - `fuelType` (string): 'WIND', 'CCGT', 'NUCLEAR', 'SOLAR', 'INTFR' (imports), etc.
  - `generation` (FLOAT64): **MW** - CRITICAL: NOT MWh!
- **Units**: **MW** (megawatts) - instantaneous power
- **Business Use**: Grid carbon intensity, renewable penetration, fuel mix analysis
- **⚠️ CRITICAL ERROR**: `generation` column is **MW NOT MWh**!
  - ❌ WRONG: `generation_mwh / 500` (treating as MWh)
  - ✅ CORRECT: `generation_mw / 1000` (convert MW → GW)
- **Reference**: See `update_dashboard_preserve_layout.py` lines 56-75 for correct implementation

#### bmrs_indgen_iris
- **Full Name**: Individual Generator Output (IRIS only)
- **Elexon Code**: B1610 (INDGEN)
- **API Endpoint**: IRIS only (no historical API)
- **Purpose**: Unit-level generation data in real-time
- **Coverage**: 2025-10-30 → Present (2M+ rows, 50 days) - Real-time only
- **Key Columns**:
  - `startTime` (DATETIME): Generation period start
  - `bmUnitId` (string): Battery/generator unit ID (e.g., FBPGM002, FFSEN005)
  - `generation` (FLOAT64): Unit output (MW)
- **Units**: MW
- **Business Use**: Specific generator tracking, capacity factor analysis, **VLP unit monitoring**
- **⚠️ NOTE**: Only available via IRIS (not in historical API) - last ~50 days only

#### bmrs_freq
- **Full Name**: System Frequency
- **Elexon Code**: FREQ
- **API Endpoint**: `/datasets/FREQ`
- **Purpose**: Grid stability monitoring (50Hz target)
- **Coverage**: 2025-12-16 → Present (294K rows) - ⚠️ Historical backfill in progress
- **Key Columns**:
  - `measurementTime` (DATETIME): Frequency measurement timestamp
  - `frequency` (FLOAT64): System frequency (Hz)
- **Units**: Hz (Hertz)
- **Business Use**: Frequency response revenue opportunities, grid stability analysis
- **⚠️ CRITICAL HISTORY**: Table was **EMPTY until Dec 16, 2025**
  - Historical API pipeline never configured for FREQ
  - Comprehensive 2022-2025 backfill now in progress
  - IRIS data (bmrs_freq_iris) available from Oct 28, 2025 onwards
  - For pre-Oct 28 data, currently limited availability

---

### 4. Outages & Unavailability

#### bmrs_remit (DEPRECATED)
- **Full Name**: REMIT Outages (Historical API - DEPRECATED)
- **Elexon Code**: REMIT
- **API Endpoint**: HTTP 404 (endpoint deprecated)
- **Purpose**: Unit unavailability notifications (historical)
- **Coverage**: N/A (API returns 404)
- **Status**: ❌ **Use bmrs_remit_iris instead**
- **⚠️ WARNING**: Historical REMIT API endpoint no longer functional

#### bmrs_remit_iris ⭐ ACTIVE
- **Full Name**: REMIT Outages (IRIS real-time)
- **Elexon Code**: REMIT
- **API Endpoint**: IRIS only
- **Purpose**: Current unit unavailability notifications
- **Coverage**: 2025-11-18 → Present (10.5K records, 177 unique assets)
- **Key Columns**:
  - `eventStart` (DATETIME): Outage start time
  - `eventEnd` (DATETIME): Outage end time
  - `unavailableCapacity` (FLOAT64): Capacity offline (MW)
  - `assetId` (string): Unit/asset identifier
  - `fuelType` (string): Generation type
- **Units**: MW (unavailable capacity)
- **Business Use**: Current outage tracking, generation forecasting, constraint analysis
- **⚠️ NOTE**: Real-time only (IRIS ~48h retention), no long-term historical data

---

## Data Purpose & Business Context

### Use Case 1: Battery Arbitrage (VLP Revenue Analysis)

**Objective**: Calculate revenue from balancing mechanism acceptances

**PRIMARY TABLES**:
```sql
-- Individual acceptance prices (most accurate)
SELECT * FROM bmrs_boalf_complete
WHERE validation_flag = 'Valid'  -- Elexon B1610 compliant
  AND bmUnit IN ('FBPGM002', 'FFSEN005')  -- VLP battery units
  AND acceptanceType = 'OFFER'  -- Discharge events
  AND acceptancePrice >= 70;  -- High-value offers only

-- System imbalance prices (settlement reference)
SELECT * FROM bmrs_costs
WHERE settlementDate >= '2025-10-01'
ORDER BY systemSellPrice DESC;  -- Highest imbalance prices
```

**SECONDARY TABLES**:
- `bmrs_bod`: Original bid/offer submissions (used to derive bmrs_boalf_complete)
- `bmrs_indgen_iris`: Real-time generation monitoring
- `bmrs_freq`: Frequency response revenue opportunities

**AVOID**:
- ❌ `bmrs_mid`: This is WHOLESALE pricing (day-ahead contracts), NOT imbalance settlement
- ❌ `bmrs_boalf`: Raw acceptances without prices (use bmrs_boalf_complete)
- ❌ `bmrs_disbsad`: Volume-weighted averages (use for validation, not primary analysis)

**Example Query**:
```sql
-- VLP Revenue Calculation (Oct 17-23, 2025 high-price event)
WITH vlp_acceptances AS (
  SELECT
    bmUnit,
    DATE(timeFrom) as date,
    acceptanceType,
    SUM(acceptanceVolume) as total_mwh,
    AVG(acceptancePrice) as avg_price_gbp_mwh,
    SUM(acceptanceVolume * acceptancePrice) as revenue_gbp
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
  WHERE validation_flag = 'Valid'
    AND bmUnit IN ('FBPGM002', 'FFSEN005')
    AND DATE(timeFrom) BETWEEN '2025-10-17' AND '2025-10-23'
  GROUP BY bmUnit, date, acceptanceType
)
SELECT
  bmUnit,
  acceptanceType,
  SUM(total_mwh) as total_energy_mwh,
  AVG(avg_price_gbp_mwh) as weighted_avg_price,
  SUM(revenue_gbp) as total_revenue_gbp
FROM vlp_acceptances
GROUP BY bmUnit, acceptanceType
ORDER BY total_revenue_gbp DESC;

-- Expected Oct 17-23 result:
-- £79.83/MWh average (system-wide)
-- FBPGM002: ~80% of total VLP revenue in 6-day high-price event
```

### Use Case 2: Grid Frequency Analysis

**Objective**: Monitor grid stability and frequency response opportunities

**PRIMARY TABLES**:
```sql
-- Historical frequency data (backfilled from Dec 16, 2025)
SELECT * FROM bmrs_freq
WHERE frequency < 49.8 OR frequency > 50.2;  -- Deviation events

-- Real-time frequency (last 48h)
SELECT * FROM bmrs_freq_iris
WHERE measurementTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR);
```

**⚠️ DATA LIMITATIONS**:
- Historical `bmrs_freq` was empty until Dec 16, 2025 backfill
- IRIS provides Oct 28, 2025 onwards (~50 days)
- For older historical data (pre-Oct 2025), limited availability

### Use Case 3: Generation Mix & Carbon Intensity

**Objective**: Analyze renewable penetration and carbon intensity

**PRIMARY TABLES**:
```sql
-- National fuel mix over time
SELECT
  DATE(startTime) as date,
  fuelType,
  SUM(generation) / 1000.0 as total_gw  -- Convert MW → GW
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE DATE(startTime) = '2025-12-17'
GROUP BY date, fuelType
ORDER BY total_gw DESC;

-- ⚠️ CRITICAL: generation is already in MW, NOT MWh!
-- ❌ WRONG: generation / 500 (treating as MWh)
-- ✅ CORRECT: generation / 1000 (MW → GW)
```

**Real-time monitoring**:
```sql
SELECT * FROM bmrs_fuelinst_iris
WHERE startTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
ORDER BY startTime DESC;
```

### Use Case 4: Market Price Analysis

**IMBALANCE PRICES** (Battery Trading):
```sql
-- System imbalance prices for battery arbitrage
SELECT
  settlementDate,
  settlementPeriod,
  systemSellPrice,  -- SSP = SBP since Nov 2015
  systemBuyPrice    -- Identical to SSP
FROM bmrs_costs
WHERE settlementDate >= '2025-10-01'
ORDER BY systemSellPrice DESC;  -- Highest imbalance prices
```

**WHOLESALE PRICES** (Forward Curves):
```sql
-- Day-ahead market index (NOT for battery arbitrage)
SELECT
  settlementDate,
  settlementPeriod,
  price as wholesale_price_gbp_mwh,
  volume as traded_volume_mwh
FROM bmrs_mid
WHERE settlementDate >= '2025-10-01'
ORDER BY price DESC;

-- ⚠️ WARNING: 24 days permanently missing (Apr/Jul/Sep/Oct 2024)
```

**BALANCING MECHANISM PRICES** (Unit-Specific):
```sql
-- Individual acceptance prices by unit
SELECT
  bmUnit,
  acceptanceType,
  AVG(acceptancePrice) as avg_price,
  SUM(acceptanceVolume) as total_volume
FROM bmrs_boalf_complete
WHERE validation_flag = 'Valid'
  AND DATE(timeFrom) = '2025-10-17'  -- High-price event day
GROUP BY bmUnit, acceptanceType
HAVING SUM(acceptanceVolume) > 10  -- Significant volume only
ORDER BY avg_price DESC;
```

### Use Case 5: Outage & Unavailability Tracking

**Objective**: Monitor generation unavailability and plan around outages

**PRIMARY TABLES**:
```sql
-- Current outages (IRIS real-time)
SELECT
  eventStart,
  eventEnd,
  assetId,
  fuelType,
  unavailableCapacity,
  TIMESTAMP_DIFF(eventEnd, eventStart, HOUR) as duration_hours
FROM bmrs_remit_iris
WHERE eventEnd >= CURRENT_TIMESTAMP()  -- Ongoing or future
ORDER BY unavailableCapacity DESC;
```

**⚠️ LIMITATIONS**:
- Historical REMIT API deprecated (returns 404)
- IRIS provides ~48h retention only
- For long-term unavailability analysis, limited historical data

---

## Known Data Gaps & Quality Issues

### 1. bmrs_mid (Market Index Data)
**Status**: ⚠️ 24 days PERMANENTLY missing

**Missing Periods**:
- Apr 16-21, 2024 (6 days)
- Jul 16-21, 2024 (6 days)
- Sep 10-15, 2024 (6 days)
- Oct 08-13, 2024 (6 days)

**Root Cause**: API confirmed 0 records available for these dates

**Impact**: Wholesale price analysis gaps in 2024

**Resolution**: **NOT RECOVERABLE** - genuine Elexon API outages, data never published

### 2. bmrs_freq (System Frequency)
**Status**: 🔄 Backfill in progress

**Historical Issue**: Table was **EMPTY until Dec 16, 2025**

**Root Cause**: Historical ingestion pipeline never configured for FREQ

**Current Status**:
- Historical backfill: 2022-2025 comprehensive backfill ongoing
- IRIS data: Oct 28, 2025 → Present (234K rows, 45 days)

**Impact**: Limited historical frequency data before Oct 2025

**Resolution**: Backfill in progress, will provide 2022-2025 coverage

### 3. bmrs_remit (REMIT Outages - Historical)
**Status**: ❌ API endpoint deprecated

**Issue**: Historical REMIT API returns HTTP 404

**Root Cause**: Elexon deprecated `/datasets/REMIT` endpoint

**Impact**: No historical outage data via API

**Resolution**: Use `bmrs_remit_iris` for current data (active since Nov 18, 2025)

### 4. bmrs_boalf vs bmrs_boalf_complete
**Status**: ✅ Workaround implemented

**Issue**: Elexon BOALF API lacks `acceptancePrice`, `acceptanceVolume`, `acceptanceType` fields

**Root Cause**: API limitation (not a bug, by design)

**Impact**: Raw BOALF data cannot be used for revenue analysis

**Resolution**: Created `bmrs_boalf_complete` via BOD matching
- Match rate: 85-95% (varies by month)
- Valid records: ~42.8% after Elexon B1610 filtering
- Always use `bmrs_boalf_complete` for price analysis

### 5. bmrs_costs: SSP = SBP since Nov 2015
**Status**: ✅ By design (not an issue)

**Fact**: Both `systemSellPrice` and `systemBuyPrice` columns exist but have **IDENTICAL values**

**Root Cause**: BSC Modification P305 (Nov 2015) merged SSP/SBP to single energy imbalance price

**Impact**: Battery arbitrage is **TEMPORAL** (charge low, discharge high over time)
- NOT SSP/SBP spread (which is zero)

**Resolution**: Use either column (they're identical), focus on temporal price variation

### 6. bmrs_fuelinst_iris.generation: MW not MWh
**Status**: ⚠️ Common misunderstanding

**Issue**: `generation` column is **MW** (instantaneous power), NOT MWh (energy)

**Impact**: Incorrect conversions (dividing by 500, treating as MWh) lead to wrong results

**Resolution**:
- ✅ CORRECT: `generation / 1000` to convert MW → GW
- ❌ WRONG: `generation / 500` (treating as MWh)

**Reference**: See `update_dashboard_preserve_layout.py` lines 56-75

### 7. bmrs_costs: Duplicate Settlement Periods
**Status**: ⚠️ Pre-Oct 27 data only

**Issue**: ~55k duplicate settlement periods in pre-Oct 27, 2025 data

**Root Cause**: Historical data loading process

**Impact**: Queries without `GROUP BY` or `DISTINCT` may return duplicate rows

**Resolution**:
- Post-Oct 29 data: Zero duplicates (automated backfill improved)
- Pre-Oct 27 data: Use `GROUP BY settlementDate, settlementPeriod` or `DISTINCT`

**Example**:
```sql
-- ✅ SAFE: Handles duplicates
SELECT
    DATE(settlementDate) as date,
    settlementPeriod,
    AVG(systemSellPrice) as price_sell  -- AVG handles duplicates
FROM bmrs_costs
GROUP BY date, settlementPeriod;

-- ⚠️ RISKY: May return duplicates for pre-Oct 27 data
SELECT DISTINCT settlementDate, settlementPeriod, systemSellPrice
FROM bmrs_costs;
```

---

## Data Consistency Guidelines

### 1. Always Check Table Coverage First

**Before writing ANY query**, verify date range:

```bash
# Quick CLI check
bq query --use_legacy_sql=false "
SELECT
  MIN(settlementDate) as min_date,
  MAX(settlementDate) as max_date,
  COUNT(DISTINCT settlementDate) as unique_dates
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_costs\`
"
```

**Or use helper script**:
```bash
./check_table_coverage.sh bmrs_costs
```

### 2. Use Correct Time Column Names

| Table | Time Column | Type |
|-------|-------------|------|
| bmrs_bod | `settlementDate` | DATE |
| bmrs_boalf_complete | `timeFrom` | DATETIME |
| bmrs_costs | `settlementDate` | DATE |
| bmrs_fuelinst | `startTime` | DATETIME |
| bmrs_freq | `measurementTime` | DATETIME |
| bmrs_mid | `settlementDate` | DATE |
| bmrs_indgen_iris | `startTime` | DATETIME |
| bmrs_remit_iris | `eventStart` | DATETIME |

**Common Error**: Using `settlementDate` for bmrs_freq (should be `measurementTime`)

### 3. Handle Data Type Differences

**Historical vs IRIS type mismatches**:
```sql
-- ❌ WRONG: Direct date comparison (type mismatch)
WHERE bmrs_costs.settlementDate = bmrs_fuelinst.startTime

-- ✅ CORRECT: Cast to same type
WHERE CAST(bmrs_costs.settlementDate AS DATE) = DATE(bmrs_fuelinst.startTime)
```

### 4. Filter for Valid Records (bmrs_boalf_complete)

**Always filter to Elexon B1610 compliant records**:
```sql
-- ✅ CORRECT: Regulatory-compliant records only
SELECT * FROM bmrs_boalf_complete
WHERE validation_flag = 'Valid';

-- ⚠️ RISKY: Includes test records, outliers, etc.
SELECT * FROM bmrs_boalf_complete;  -- No filter
```

### 5. Use UNION Pattern for Complete Timeline

**When you need recent + historical data**:
```sql
WITH combined AS (
  -- Historical data (long-term)
  SELECT
    CAST(settlementDate AS DATE) as date,
    systemSellPrice as price
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
  WHERE settlementDate < '2025-12-18'  -- Cutoff date

  UNION ALL

  -- IRIS data (real-time, last 48h)
  SELECT
    DATE(measurementTime) as date,
    price
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs_iris`
  WHERE measurementTime >= '2025-12-18'  -- Cutoff date
)
SELECT date, AVG(price) as avg_price
FROM combined
GROUP BY date
ORDER BY date DESC;
```

### 6. Handle Known Gaps Gracefully

**bmrs_mid gap-aware queries**:
```sql
-- Analyze wholesale prices with explicit gap handling
WITH date_series AS (
  SELECT date
  FROM UNNEST(GENERATE_DATE_ARRAY('2024-01-01', '2024-12-31')) as date
),
mid_data AS (
  SELECT DATE(settlementDate) as date, AVG(price) as avg_price
  FROM bmrs_mid
  WHERE DATE(settlementDate) BETWEEN '2024-01-01' AND '2024-12-31'
  GROUP BY date
)
SELECT
  ds.date,
  md.avg_price,
  CASE
    WHEN md.avg_price IS NULL THEN '⚠️ Gap'
    ELSE '✅ Data'
  END as status
FROM date_series ds
LEFT JOIN mid_data md ON ds.date = md.date
ORDER BY ds.date;
```

### 7. Unit Conversion Patterns

**MW to GW** (bmrs_fuelinst):
```python
# ✅ CORRECT
generation_gw = generation_mw / 1000.0

# ❌ WRONG
generation_gw = generation_mwh / 500.0  # Treating MW as MWh!
```

**Settlement Period to Time**:
```python
# Settlement period 1 = 00:00-00:30, period 2 = 00:30-01:00, etc.
def period_to_time(period: int) -> str:
    hour = (period - 1) // 2
    minute = 30 if period % 2 == 0 else 0
    return f"{hour:02d}:{minute:02d}"

# Example: period 17 = 08:00-08:30 (morning peak start)
```

---

## Query Patterns for Complete Timeline

### Pattern 1: Last 7 Days (IRIS + Historical)

```sql
WITH recent_costs AS (
  -- Historical (up to 2 days ago)
  SELECT settlementDate, settlementPeriod, systemSellPrice as price
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND settlementDate < CURRENT_DATE()

  UNION ALL

  -- IRIS (last 48h)
  SELECT
    DATE(measurementTime) as settlementDate,
    EXTRACT(HOUR FROM measurementTime) * 2 +
      CASE WHEN EXTRACT(MINUTE FROM measurementTime) >= 30 THEN 2 ELSE 1 END as settlementPeriod,
    price
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs_iris`
  WHERE measurementTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
)
SELECT
  settlementDate,
  AVG(price) as avg_daily_price,
  MAX(price) as peak_price,
  MIN(price) as trough_price
FROM recent_costs
GROUP BY settlementDate
ORDER BY settlementDate DESC;
```

### Pattern 2: Specific Date Range with Gap Detection

```sql
WITH date_series AS (
  SELECT date
  FROM UNNEST(GENERATE_DATE_ARRAY('2025-10-01', '2025-12-17')) as date
),
data_coverage AS (
  SELECT
    DATE(timeFrom) as date,
    COUNT(*) as records,
    COUNT(DISTINCT bmUnit) as unique_units
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
  WHERE validation_flag = 'Valid'
    AND DATE(timeFrom) BETWEEN '2025-10-01' AND '2025-12-17'
  GROUP BY date
)
SELECT
  ds.date,
  COALESCE(dc.records, 0) as records,
  COALESCE(dc.unique_units, 0) as units,
  CASE
    WHEN dc.records IS NULL THEN '❌ No Data'
    WHEN dc.records < 100 THEN '⚠️ Low Volume'
    ELSE '✅ Normal'
  END as status
FROM date_series ds
LEFT JOIN data_coverage dc ON ds.date = dc.date
ORDER BY ds.date DESC;
```

### Pattern 3: Monthly Aggregation with Validation

```sql
SELECT
  FORMAT_DATE('%Y-%m', DATE(timeFrom)) as month,
  validation_flag,
  COUNT(*) as records,
  SUM(acceptanceVolume) as total_volume_mwh,
  AVG(acceptancePrice) as avg_price_gbp_mwh,
  SUM(acceptanceVolume * acceptancePrice) as total_revenue_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
WHERE DATE(timeFrom) >= '2025-01-01'
  AND bmUnit IN ('FBPGM002', 'FFSEN005')  -- VLP units
GROUP BY month, validation_flag
ORDER BY month DESC, validation_flag;
```

---

## External Resources

### Elexon Official Documentation
- **BMRS Data Portal**: https://www.elexon.co.uk/bsc/data/
- **API Documentation**: https://developer.data.elexon.co.uk/
- **B1610 Guidance** (BOALF matching): Elexon Data Catalogue Section 4.3
- **BSC Mod P305** (SSP=SBP merge): https://www.elexonchange.co.uk/change-proposal/p305/

### GitHub Resources
- **Elexon Official GitHub**: https://github.com/elexon-data
- **OSUKED ElexonDataPortal**: https://github.com/OSUKED/ElexonDataPortal
  - Comprehensive BMRS API schema definitions
  - Python client library (`ElexonDataPortal` package)
  - API endpoint documentation and examples

### Internal Documentation
- **PROJECT_CONFIGURATION.md**: All configuration settings, credentials, project IDs
- **STOP_DATA_ARCHITECTURE_REFERENCE.md**: Quick reference to prevent recurring data issues
- **DATA_ARCHITECTURE_VERIFIED_DEC17_2025.md**: Detailed pipeline architecture and verification
- **UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md**: Dual-pipeline design patterns
- **DOCUMENTATION_INDEX.md**: Complete file index (22 documents categorized)

### Tools & Scripts
- `check_table_coverage.sh`: Quick CLI tool to verify table date ranges
- `backfill_gaps_only.py`: Targeted gap-filling for historical tables
- `iris_to_bigquery_unified.py`: IRIS uploader (continuous mode)
- `ingest_elexon_fixed.py`: Historical API ingestion (cron-ready)

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-12-20 | 1.0 | Initial comprehensive guide created |

---

**Last Updated**: December 20, 2025
**Maintainer**: George Major (george@upowerenergy.uk)
**Status**: ✅ Production (Nov 2025)
