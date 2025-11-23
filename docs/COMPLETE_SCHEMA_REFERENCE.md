# Complete BigQuery Schema Reference

**Project:** `inner-cinema-476211-u9`  
**Dataset:** `uk_energy_prod`  
**Location:** US  
**Generated:** 2025-11-23 16:51:26  

---

## 📋 Table Overview

| Table | Type | Date Range | Rows | Primary Use |
|-------|------|------------|------|-------------|
| `bmrs_mid` | Historical | 2022-01-01 → 2025-10-30 | 155,405 | Market prices (historical) |
| `bmrs_mid_iris` | Real-time | 2025-11-04 → present | 2,218+ | Market prices (live) |
| `bmrs_indo` | Historical | 2025-10-27 → 2025-10-28 | 241 | Demand (limited) |
| `bmrs_indo_iris` | Real-time | 2025-10-28 → present | 1,253+ | Demand (live) |
| `bmrs_fuelinst` | Historical | 2022-12-31 → 2025-10-30 | 5.7M | Generation (historical) |
| `bmrs_fuelinst_iris` | Real-time | 2025-10-31 → present | 131,600+ | Generation (live) |
| `bmrs_freq` | Historical | Empty | 0 | Frequency (unused) |
| `bmrs_freq_iris` | Real-time | 2025-10-28 → present | 121,992+ | Frequency (live) |
| `bmrs_bod` | Historical | 2022-01-01 → 2025-10-28 | 391M | Bid-offer data |
| `bmrs_bod_iris` | Real-time | 2025-10-28 → present | 2.8M+ | Bid-offer data (live) |

---

## 🔍 Detailed Schemas

### bmrs_mid (Market Prices - Historical)

**Date Range:** 2022-01-01 to 2025-10-30  
**Row Count:** 155,405  
**Update Pattern:** Historical batch load  

**Schema:**
```
dataset                        STRING          # Always 'MID'
startTime                      DATETIME        # Settlement period start
dataProvider                   STRING          # 'APXMIDP' for market price
settlementDate                 DATETIME        # Settlement date
settlementPeriod               INT64           # 1-48
price                          FLOAT64         # £/MWh
volume                         FLOAT64         # MWh
_dataset                       STRING          # Internal
_window_from_utc               STRING          # Internal
_window_to_utc                 STRING          # Internal
_ingested_utc                  STRING          # Internal
_source_columns                STRING          # Internal
_source_api                    STRING          # Internal
_hash_source_cols              STRING          # Internal
_hash_key                      STRING          # Internal
```

**Key Query Pattern:**
```sql
SELECT 
    settlementDate,
    settlementPeriod,
    AVG(price) as market_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
WHERE dataProvider = 'APXMIDP'  -- ⚠️ CRITICAL FILTER
  AND settlementDate >= '2025-01-01'
GROUP BY settlementDate, settlementPeriod
```

---

### bmrs_mid_iris (Market Prices - Real-time)

**Date Range:** 2025-11-04 to present  
**Row Count:** 2,218+  
**Update Pattern:** IRIS streaming (real-time)  

**Schema:**
```
dataset                        STRING          # Always 'MID'
sourceFileDateTime             TIMESTAMP       # File timestamp
sourceFileSerialNumber         STRING          # File serial
startTime                      TIMESTAMP       # Settlement period start
dataProvider                   STRING          # 'APXMIDP' for market price
settlementDate                 DATE            # ⚠️ DATE not DATETIME
settlementPeriod               INT64           # 1-48
price                          FLOAT64         # £/MWh
volume                         FLOAT64         # MWh
source                         STRING          # 'IRIS'
ingested_utc                   TIMESTAMP       # Ingestion time
```

**Key Differences from Historical:**
- `settlementDate` is **DATE** (not DATETIME)
- No underscore metadata columns
- Has `source` column = 'IRIS'

---

### bmrs_indo (Demand - Historical)

**Date Range:** 2025-10-27 to 2025-10-28 (⚠️ LIMITED COVERAGE)  
**Row Count:** 241  
**Update Pattern:** Historical batch load  

**Schema:**
```
dataset                        STRING          # 'INDO'
publishTime                    DATETIME        # Publication time
startTime                      DATETIME        # Period start
settlementDate                 DATETIME        # Settlement date
settlementPeriod               INT64           # 1-48
demand                         INT64           # MW (⚠️ INTEGER)
_dataset                       STRING          # Internal
_window_from_utc               STRING          # Internal
_window_to_utc                 STRING          # Internal
_ingested_utc                  STRING          # Internal
_source_columns                STRING          # Internal
_source_api                    STRING          # Internal
_hash_source_cols              STRING          # Internal
_hash_key                      STRING          # Internal
```

**⚠️ WARNING:** Very limited historical coverage. Use `bmrs_indo_iris` for recent data.

---

### bmrs_indo_iris (Demand - Real-time)

**Date Range:** 2025-10-28 to present  
**Row Count:** 1,253+  
**Update Pattern:** IRIS streaming (real-time)  

**Schema:**
```
dataset                        STRING          # 'INDO'
publishTime                    TIMESTAMP       # Publication time
startTime                      TIMESTAMP       # Period start
settlementDate                 DATE            # ⚠️ DATE not DATETIME
settlementPeriod               INT64           # 1-48
demand                         FLOAT64         # MW (⚠️ FLOAT not INT)
ingested_utc                   TIMESTAMP       # Ingestion time
source                         STRING          # 'IRIS'
```

**Key Differences:**
- `demand` is **FLOAT64** (not INT64 like historical)
- `settlementDate` is **DATE** (not DATETIME)

---

### bmrs_fuelinst (Generation - Historical)

**Date Range:** 2022-12-31 to 2025-10-30  
**Row Count:** 5,691,925  
**Update Pattern:** Historical batch load  

**Schema:**
```
dataset                        STRING          # 'FUELINST'
publishTime                    DATETIME        # Publication time
startTime                      DATETIME        # Period start
settlementDate                 DATETIME        # Settlement date
settlementPeriod               INT64           # 1-48
fuelType                       STRING          # e.g., 'WIND', 'CCGT', 'INTFR'
generation                     INT64           # MW (⚠️ NOT MWh!)
_dataset                       STRING          # Internal
_window_from_utc               STRING          # Internal
_window_to_utc                 STRING          # Internal
_ingested_utc                  STRING          # Internal
_source_columns                STRING          # Internal
_source_api                    STRING          # Internal
_hash_source_cols              STRING          # Internal
_hash_key                      STRING          # Internal
```

**⚠️ CRITICAL UNIT NOTE:**
```sql
-- ✅ CORRECT: generation is in MW
SELECT 
    SUM(generation) as total_mw,
    SUM(generation) / 1000.0 as total_gw
FROM bmrs_fuelinst

-- ❌ WRONG: Do NOT divide by 500 or treat as MWh
SELECT generation / 500 as gw  -- INCORRECT!
```

**Fuel Types:**
- Generation: `WIND`, `SOLAR`, `NUCLEAR`, `CCGT`, `COAL`, `BIOMASS`, `HYDRO`, `NPSHYD`, `PS`, `OTHER`
- Interconnectors: `INTFR`, `INTIRL`, `INTNED`, `INTEW`, `INTNEM`, `INTELEC`, `INTNSL` (prefix with `INT`)

**Query Pattern for Interconnectors:**
```sql
-- Filter interconnectors using LIKE pattern
SELECT fuelType, SUM(generation) as import_mw
FROM bmrs_fuelinst_iris
WHERE fuelType LIKE 'INT%'  -- ⚠️ Use LIKE, not psrType
GROUP BY fuelType
```

---

### bmrs_fuelinst_iris (Generation - Real-time)

**Date Range:** 2025-10-31 to present  
**Row Count:** 131,600+  
**Update Pattern:** IRIS streaming (real-time)  

**Schema:**
```
dataset                        STRING          # 'FUELINST'
publishTime                    TIMESTAMP       # Publication time
startTime                      TIMESTAMP       # Period start
settlementDate                 DATE            # ⚠️ DATE not DATETIME
settlementPeriod               INT64           # 1-48
generation                     FLOAT64         # MW (⚠️ FLOAT not INT)
fuelType                       STRING          # Fuel/interconnector type
source                         STRING          # 'IRIS'
ingested_utc                   TIMESTAMP       # Ingestion time
```

**Key Differences:**
- `generation` is **FLOAT64** (not INT64)
- `settlementDate` is **DATE** (not DATETIME)
- Column order different (generation before fuelType)

---

### bmrs_freq (Frequency - Historical)

**Date Range:** Empty (0 rows)  
**Row Count:** 0  
**Update Pattern:** Not populated  

**Schema:**
```
dataset                        STRING
measurementTime                DATETIME        # ⚠️ NOT settlementDate!
frequency                      FLOAT64         # Hz
_dataset                       STRING
_window_from_utc               STRING
_window_to_utc                 STRING
_ingested_utc                  STRING
_source_columns                STRING
_source_api                    STRING
_hash_source_cols              STRING
_hash_key                      STRING
```

**⚠️ NOTE:** This table is empty. Use `bmrs_freq_iris` for all frequency data.

---

### bmrs_freq_iris (Frequency - Real-time)

**Date Range:** 2025-10-28 14:20:00 to present  
**Row Count:** 121,992+  
**Update Pattern:** IRIS streaming (~1 reading per 30 seconds)  

**Schema:**
```
dataset                        STRING          # 'FREQ'
measurementTime                DATETIME        # ⚠️ NOT settlementDate!
frequency                      FLOAT64         # Hz (target: 50.0)
source                         STRING          # 'IRIS'
ingested_utc                   TIMESTAMP       # Ingestion time
```

**⚠️ CRITICAL DIFFERENCE:**
- Uses `measurementTime` (not `settlementDate`)
- High-frequency data (~120 readings/hour)
- Must aggregate to settlement periods

**Query Pattern:**
```sql
-- Aggregate to settlement periods
SELECT 
    CAST(measurementTime AS DATE) as date,
    CAST(EXTRACT(HOUR FROM measurementTime) * 2 + 
         FLOOR(EXTRACT(MINUTE FROM measurementTime) / 30) + 1 AS INT64) as sp,
    AVG(frequency) as avg_frequency
FROM bmrs_freq_iris
WHERE measurementTime >= TIMESTAMP('2025-11-23')
GROUP BY date, sp
```

---

### bmrs_bod (Bid-Offer Data - Historical)

**Date Range:** 2022-01-01 to 2025-10-28  
**Row Count:** 391,287,533 (391M)  
**Update Pattern:** Historical batch load  

**Schema:**
```
dataset                        STRING          # 'BOD'
settlementDate                 DATETIME        # Settlement date
settlementPeriod               INT64           # 1-48
timeFrom                       DATETIME        # Bid/offer valid from
levelFrom                      INT64           # Level from (MW)
timeTo                         DATETIME        # Bid/offer valid to
levelTo                        INT64           # Level to (MW)
pairId                         INT64           # Bid-offer pair ID
offer                          FLOAT64         # Offer price (£/MWh)
bid                            FLOAT64         # Bid price (£/MWh)
nationalGridBmUnit             STRING          # BMU ID (short)
bmUnit                         STRING          # BMU ID (long)
_dataset                       STRING          # Internal
_window_from_utc               STRING          # Internal
_window_to_utc                 STRING          # Internal
_ingested_utc                  STRING          # Internal
_source_columns                STRING          # Internal
_source_api                    STRING          # Internal
_hash_source_cols              STRING          # Internal
_hash_key                      STRING          # Internal
```

**⚠️ IMPORTANT NOTES:**
- This is **BID-OFFER DATA**, not acceptances!
- Use `bmUnit` or `nationalGridBmUnit` for BMU identification
- `offer` and `bid` are prices (£/MWh), NOT volumes
- For acceptances, use `bmrs_boalf` table (not documented here)

---

### bmrs_bod_iris (Bid-Offer Data - Real-time)

**Date Range:** 2025-10-28 to present  
**Row Count:** 2,800,663+  
**Update Pattern:** IRIS streaming (real-time)  

**Schema:**
```
dataset                        STRING          # 'BOD'
settlementDate                 DATETIME        # Settlement date
settlementPeriod               INT64           # 1-48
timeFrom                       STRING          # ⚠️ STRING not DATETIME
timeTo                         STRING          # ⚠️ STRING not DATETIME
levelFrom                      INT64           # Level from (MW)
levelTo                        INT64           # Level to (MW)
pairId                         INT64           # Bid-offer pair ID
offer                          FLOAT64         # Offer price (£/MWh)
bid                            FLOAT64         # Bid price (£/MWh)
nationalGridBmUnit             STRING          # BMU ID (short)
bmUnit                         STRING          # BMU ID (long)
source                         STRING          # 'IRIS'
ingested_utc                   TIMESTAMP       # Ingestion time
```

**Key Differences:**
- `timeFrom` and `timeTo` are **STRING** (not DATETIME)
- Must parse or cast if using for time filtering

---

## 🎯 Query Patterns & Best Practices

### 1. Union Historical + Real-time for Complete Timeline

```sql
WITH combined_prices AS (
    -- Historical
    SELECT 
        CAST(settlementDate AS DATE) as date,
        settlementPeriod as sp,
        AVG(price) as price
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
    WHERE dataProvider = 'APXMIDP'
      AND settlementDate < '2025-10-30'
    GROUP BY date, sp
    
    UNION ALL
    
    -- Real-time
    SELECT 
        settlementDate as date,
        settlementPeriod as sp,
        AVG(price) as price
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
    WHERE dataProvider = 'APXMIDP'
      AND settlementDate >= '2025-10-30'
    GROUP BY date, sp
)
SELECT * FROM combined_prices
ORDER BY date, sp
```

### 2. Today's Data Only (Current Day from 00:00)

```sql
-- Get today's data starting from 00:00
SELECT 
    settlementPeriod,
    AVG(price) as avg_price,
    AVG(demand) as avg_demand
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
WHERE settlementDate = CURRENT_DATE('Europe/London')
GROUP BY settlementPeriod
ORDER BY settlementPeriod
```

### 3. Interconnector Filtering

```sql
-- ✅ CORRECT: Use LIKE pattern for interconnectors
SELECT fuelType, SUM(generation) as mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE fuelType LIKE 'INT%'
GROUP BY fuelType

-- ❌ WRONG: psrType column doesn't exist
WHERE psrType = 'Interconnector'  -- INCORRECT!
```

### 4. Frequency Aggregation to Settlement Periods

```sql
-- Convert high-frequency measurements to SP averages
WITH freq_sp AS (
    SELECT 
        CAST(measurementTime AS DATE) as date,
        CAST(
            EXTRACT(HOUR FROM measurementTime) * 2 + 
            FLOOR(EXTRACT(MINUTE FROM measurementTime) / 30) + 1 
        AS INT64) as sp,
        AVG(frequency) as avg_freq
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
    WHERE measurementTime >= TIMESTAMP(CURRENT_DATE('Europe/London'))
    GROUP BY date, sp
)
SELECT * FROM freq_sp
ORDER BY date, sp
```

---

## ⚠️ Common Pitfalls

### 1. Wrong Column Names
| ❌ Incorrect | ✅ Correct | Table |
|-------------|-----------|-------|
| `systemSellPrice` | `price` (filter by `dataProvider='APXMIDP'`) | bmrs_mid* |
| `systemBuyPrice` | `price` (different dataProvider) | bmrs_mid* |
| `initialDemandOutturn` | `demand` | bmrs_indo* |
| `psrType` | Use `fuelType LIKE 'INT%'` | bmrs_fuelinst* |
| `quantity` | `generation` | bmrs_fuelinst* |
| `recordTime` | `measurementTime` | bmrs_freq* |
| `settlementDate` | `measurementTime` | bmrs_freq* |

### 2. Data Type Mismatches
- Historical: `settlementDate` = **DATETIME**
- IRIS: `settlementDate` = **DATE**
- **Fix:** Always cast to DATE for joins

```sql
-- ✅ CORRECT
WHERE CAST(h.settlementDate AS DATE) = i.settlementDate

-- ❌ WRONG
WHERE h.settlementDate = i.settlementDate  -- Type mismatch!
```

### 3. Unit Confusion
- `bmrs_fuelinst*.generation` = **MW** (NOT MWh)
- Convert to GW: `generation / 1000.0`
- Do NOT divide by 500 or treat as MWh

### 4. Empty Tables
- `bmrs_freq` (historical) = **0 rows** (use IRIS instead)
- `bmrs_indo` (historical) = **limited coverage** (use IRIS for recent)

### 5. Boolean Check with ID 0
```python
# ❌ WRONG: ID 0 evaluates to False
if dashboard_id:
    use_id(dashboard_id)

# ✅ CORRECT: Check for None explicitly
if dashboard_id is not None:
    use_id(dashboard_id)
```

---

## 📚 Related Documentation

- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Quick reference guide
- `PROJECT_CONFIGURATION.md` - All configuration settings
- `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md` - Pipeline architecture
- `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md` - IRIS setup guide

---

**Last Updated:** 2025-11-23  
**Maintained By:** George Major  
**Contact:** george@upowerenergy.uk
