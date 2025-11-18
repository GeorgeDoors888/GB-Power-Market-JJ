# BigQuery Dataset Reference - BOD & VLP Analysis
**Dataset**: `inner-cinema-476211-u9.uk_energy_prod`  
**Last Updated**: November 10, 2025

## ⚡ Overview

**185 tables** divided into two categories:

### Historical Tables (`bmrs_*`)
- **Period**: 2020-2025
- **Coverage**: Complete historical records
- **Update**: Batch loads, typically 24-48h lag
- **Use**: Long-term analysis, backtesting, statistical studies

### Near-Real-Time Tables (`bmrs_*_iris`)
- **Period**: Last 48-72 hours
- **Coverage**: Live operational data
- **Update**: Event-driven or sub-hourly (2-30 min)
- **Use**: Live trading, VLP arbitrage, balancing decisions

---

## 📊 Key Tables for BOD & VLP Analysis

### 1. **Market Pricing Tables**

#### `bmrs_mid_iris` - Market Index Data (Day-Ahead Price)
```sql
-- Structure
settlementDate DATE
settlementPeriod INT64
marketIndexPrice FLOAT64      -- £/MWh (day-ahead auction price)
marketIndexVolume FLOAT64     -- MWh (volume traded)
publishTime TIMESTAMP
```

**Update Frequency**: 30 minutes  
**Units**: £/MWh, MWh  
**Status**: ✅ Live  
**Use Case**: VLP arbitrage opportunity detection (compare day-ahead vs imbalance)

**Example Query**:
```sql
-- Latest market prices
SELECT 
  settlementDate,
  settlementPeriod,
  marketIndexPrice,
  marketIndexVolume,
  publishTime
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
WHERE DATE(settlementDate) = CURRENT_DATE()
ORDER BY publishTime DESC
LIMIT 48;
```

---

#### `bmrs_imbalngc` - Imbalance Prices (System Buy/Sell)
```sql
-- Structure
settlementDate DATE
settlementPeriod INT64
systemSellPrice FLOAT64       -- £/MWh (system selling to market)
systemBuyPrice FLOAT64        -- £/MWh (system buying from market)
netImbalanceVolume FLOAT64    -- MWh (positive = long, negative = short)
publishTime TIMESTAMP
```

**Update Frequency**: 30 minutes  
**Units**: £/MWh, MWh  
**Status**: ✅ Current  
**Use Case**: Real-time arbitrage spread calculation

**Example Query - Arbitrage Opportunities**:
```sql
-- Find arbitrage spreads (VLP vs BM)
SELECT
  m.settlementDate,
  m.settlementPeriod,
  m.marketIndexPrice AS day_ahead,
  i.systemBuyPrice AS imbalance_buy,
  i.systemSellPrice AS imbalance_sell,
  m.marketIndexPrice - i.systemBuyPrice AS buy_spread,
  i.systemSellPrice - m.marketIndexPrice AS sell_spread,
  i.netImbalanceVolume
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris` m
JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_imbalngc` i
  USING(settlementDate, settlementPeriod)
WHERE DATE(m.settlementDate) = CURRENT_DATE()
ORDER BY ABS(m.marketIndexPrice - i.systemBuyPrice) DESC
LIMIT 20;
```

---

### 2. **Balancing Mechanism Tables**

#### `bmrs_boalf_iris` - Bid-Offer Acceptances (Dispatch Instructions)
```sql
-- Structure
bmUnit STRING                 -- BMU ID (e.g., T_DRAXX-1)
acceptanceNumber STRING       -- Unique acceptance ID
levelFrom FLOAT64             -- MW (starting level)
levelTo FLOAT64               -- MW (target level)
timeFrom TIMESTAMP            -- Start time
timeTo TIMESTAMP              -- End time
acceptancePrice FLOAT64       -- £/MWh
publishTime TIMESTAMP
```

**Update Frequency**: Event-driven (real-time dispatch)  
**Units**: MW, £/MWh  
**Status**: ✅ Live  
**Use Case**: Real-time dispatch validation, BOD execution tracking

**Example Query - Recent Acceptances**:
```sql
-- Recent bid-offer acceptances (last hour)
SELECT 
  bmUnit,
  acceptanceNumber,
  levelFrom,
  levelTo,
  (levelTo - levelFrom) AS delta_mw,
  acceptancePrice,
  timeFrom,
  timeTo
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
WHERE timeFrom >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY timeFrom DESC;
```

---

#### `bmrs_bod_iris` - Bid-Offer Data (Offers Submitted by BMUs)
```sql
-- Structure
bmUnitId STRING               -- BMU ID
pairId STRING                 -- Bid-offer pair ID
timeFrom TIMESTAMP
timeTo TIMESTAMP
bid FLOAT64                   -- £/MWh (bid price)
offer FLOAT64                 -- £/MWh (offer price)
bidVolume FLOAT64             -- MW
offerVolume FLOAT64           -- MW
publishTime TIMESTAMP
```

**Update Frequency**: Daily batch  
**Units**: MW, £/MWh  
**Status**: ⚠️ Partially skipped (607K rows per batch)  
**Use Case**: BOD strategy analysis, price stack analysis

**Note**: Large batches may be skipped due to memory limits. Recommended to query historical `bmrs_bod` table for complete records.

**Example Query - BMU Offer Stack**:
```sql
-- Current offer stack for specific BMU
SELECT 
  bmUnitId,
  pairId,
  bid,
  offer,
  bidVolume,
  offerVolume,
  timeFrom,
  timeTo
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
WHERE bmUnitId = 'T_DRAXX-1'
  AND DATE(timeFrom) = CURRENT_DATE()
ORDER BY offer ASC;
```

---

### 3. **System Monitoring Tables**

#### `bmrs_freq_iris` - System Frequency
```sql
-- Structure
measurementTime TIMESTAMP     -- NOT recordTime!
frequency FLOAT64             -- Hz (50 Hz nominal)
publishTime TIMESTAMP
```

**Update Frequency**: 2 minutes  
**Units**: Hz  
**Status**: ⚠️ Lagging (~4-7 days)  
**Use Case**: Imbalance forecasting, system stress indicator

**Example Query**:
```sql
-- Recent frequency readings
SELECT 
  measurementTime,
  frequency,
  (frequency - 50.0) AS deviation_hz,
  CASE 
    WHEN frequency < 49.8 THEN '🔴 LOW'
    WHEN frequency > 50.2 THEN '🔴 HIGH'
    WHEN frequency < 49.9 THEN '⚠️ Low'
    WHEN frequency > 50.1 THEN '⚠️ High'
    ELSE '✅ Normal'
  END AS status
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
WHERE DATE(measurementTime) = CURRENT_DATE()
ORDER BY measurementTime DESC
LIMIT 100;
```

---

#### `bmrs_fuelinst_iris` - Instantaneous Generation by Fuel Type
```sql
-- Structure
settlementDate DATE
settlementPeriod INT64
fuelType STRING               -- WIND, CCGT, NUCLEAR, INTFR, etc.
generation FLOAT64            -- MW
publishTime TIMESTAMP
```

**Update Frequency**: 5 minutes  
**Units**: MW  
**Status**: ⚠️ Lagging (~4-7 days)  
**Use Case**: Real-time fuel mix monitoring, renewables tracking

**Critical Note**: `fuelType` includes interconnectors (INTFR, INTELEC, etc.) with negative values for exports. Filter with `WHERE fuelType NOT LIKE 'INT%'` for actual generation.

**Example Query - Current Fuel Mix**:
```sql
-- Latest fuel generation (excluding interconnectors)
WITH latest_data AS (
  SELECT fuelType, generation, publishTime
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
  WHERE DATE(settlementDate) = CURRENT_DATE()
  ORDER BY publishTime DESC
  LIMIT 1000
),
current_sp AS (
  SELECT MAX(publishTime) as latest_time FROM latest_data
)
SELECT 
  ld.fuelType,
  ROUND(SUM(ld.generation), 1) as total_generation_mw,
  ROUND(SUM(ld.generation) / 1000, 2) as total_generation_gw
FROM latest_data ld
CROSS JOIN current_sp cs
WHERE ld.publishTime = cs.latest_time
  AND ld.fuelType NOT LIKE 'INT%'  -- EXCLUDE interconnectors
  AND ld.generation > 0
GROUP BY ld.fuelType
ORDER BY total_generation_mw DESC;
```

---

### 4. **Availability & Constraint Tables**

#### `bmrs_mels_iris` / `bmrs_mils_iris` - Export/Import Limits
```sql
-- Structure (MELS - Export Limits)
bmUnitId STRING
mels FLOAT64                  -- MW (maximum export limit)
validFrom TIMESTAMP
validTo TIMESTAMP
publishTime TIMESTAMP

-- Structure (MILS - Import Limits)
bmUnitId STRING
mils FLOAT64                  -- MW (maximum import limit)
validFrom TIMESTAMP
validTo TIMESTAMP
publishTime TIMESTAMP
```

**Update Frequency**: Event-driven  
**Units**: MW  
**Status**: ⚠️ Delayed (~days)  
**Use Case**: Constraint tracking, availability monitoring

**Example Query**:
```sql
-- Current export limits for battery units
SELECT 
  bmUnitId,
  mels AS max_export_mw,
  validFrom,
  validTo
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mels_iris`
WHERE bmUnitId LIKE '%BESS%'
  AND validTo > CURRENT_TIMESTAMP()
ORDER BY validFrom DESC;
```

---

## 📐 Common Units and Conversions

| Measurement | Symbol | Typical Field | Unit | Notes |
|-------------|--------|---------------|------|-------|
| **Price** | £/MWh | `marketIndexPrice`, `systemBuyPrice` | £/MWh | Used for arbitrage calculations |
| **Volume** | MWh | `marketIndexVolume`, `netImbalanceVolume` | MWh | Aggregated per settlement period |
| **Power** | MW | `quantity`, `generation`, `levelFrom/To` | MW | Instantaneous or accepted bid level |
| **Frequency** | Hz | `frequency` | Hz | System balancing signal (50 Hz nominal) |
| **Time** | - | `publishTime`, `settlementDate/Period` | UTC, integer period | Settlement-aligned timing |

### Key Conversions
```
1 Settlement Period = 30 minutes
48 Settlement Periods = 1 day (unless clocks change)
1 GW = 1000 MW
1 MWh = 1 MW × 1 hour
```

---

## 🔴 Operational Notes & Known Issues

### 1. **Real-Time Ingestion Lag**
- **Current Status**: 4-7 days behind real-time
- **Cause**: Single-threaded uploader on 1 vCPU UpCloud server
- **Impact**: `_iris` tables show stale data for freq, fuelinst, mels, mils
- **Mitigation**: Use historical tables for complete data, monitor `publishTime`

### 2. **BOD Table Processing**
- **Issue**: `bmrs_bod_iris` processing skipped intermittently
- **Cause**: 607K rows per batch exceeds memory limits
- **Recommendation**: Offload large batches to UpCloud for parsing, or query historical `bmrs_bod` table

### 3. **Interconnector Pollution in Fuel Data**
- **Issue**: `bmrs_fuelinst_iris` includes interconnector flows as "fuel types"
- **Examples**: INTFR (France), INTELEC (ElecLink), INTIRL (Ireland)
- **Solution**: Always filter with `WHERE fuelType NOT LIKE 'INT%'`
- **Negative Values**: Exports show as negative generation

### 4. **Settlement Period Count**
- **Normal Days**: 48 settlement periods (00:00-23:30)
- **Clock Change Days**: 46 periods (spring forward) or 50 periods (fall back)
- **Important**: Always check actual data, don't assume 48

### 5. **Timestamp Conventions**
- **All timestamps**: UTC (not BST)
- **Settlement Date**: Date in local UK time (can differ from UTC date)
- **Join Key**: Use `(settlementDate, settlementPeriod)` not timestamps

---

## 🎯 VLP Use Case Examples

### Battery Arbitrage Analysis
```sql
-- Find profitable charge/discharge windows
WITH prices AS (
  SELECT 
    settlementDate,
    settlementPeriod,
    marketIndexPrice AS mip,
    systemBuyPrice AS sbp,
    systemSellPrice AS ssp
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris` m
  JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_imbalngc` i
    USING(settlementDate, settlementPeriod)
  WHERE DATE(settlementDate) = CURRENT_DATE()
),
windows AS (
  SELECT 
    settlementPeriod,
    mip,
    sbp,
    ssp,
    LAG(ssp, 1) OVER (ORDER BY settlementPeriod) AS prev_sell,
    LEAD(sbp, 1) OVER (ORDER BY settlementPeriod) AS next_buy
  FROM prices
)
SELECT 
  settlementPeriod,
  ROUND(ssp, 2) AS charge_price,
  ROUND(next_buy, 2) AS discharge_price,
  ROUND(next_buy - ssp, 2) AS profit_per_mwh,
  ROUND((next_buy - ssp) * 50, 2) AS profit_50mw_unit
FROM windows
WHERE next_buy - ssp > 10  -- £10/MWh minimum spread
ORDER BY profit_per_mwh DESC;
```

### VLP Revenue Tracking
```sql
-- Track VLP unit dispatch and revenue
SELECT 
  b.bmUnit,
  DATE(b.timeFrom) AS dispatch_date,
  COUNT(*) AS num_acceptances,
  SUM(b.levelTo - b.levelFrom) AS total_mwh_dispatched,
  AVG(b.acceptancePrice) AS avg_price,
  SUM((b.levelTo - b.levelFrom) * b.acceptancePrice) AS estimated_revenue_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris` b
WHERE b.bmUnit LIKE '%FBPGM%'  -- Flexgen battery
  OR b.bmUnit LIKE '%FFSEN%'   -- Another VLP battery
GROUP BY b.bmUnit, DATE(b.timeFrom)
ORDER BY dispatch_date DESC;
```

---

## 📚 Related Documentation

- **STOP_DATA_ARCHITECTURE_REFERENCE.md** - Schema details and gotchas
- **PROJECT_CONFIGURATION.md** - BigQuery credentials and settings
- **UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md** - Pipeline design
- **CHATGPT_INSTRUCTIONS.md** - Query patterns and best practices

---

## ✅ Summary

**For Balancing Mechanism (BOD) and VLP analytics:**

✅ **Focus Tables**: 
- `bmrs_mid_iris` (prices)
- `bmrs_boalf_iris` (acceptances)
- `bmrs_freq_iris` (frequency)
- `bmrs_fuelinst_iris` (generation)
- `bmrs_mels_iris` / `bmrs_mils_iris` (limits)

✅ **Unit Standards**:
- Monetary: £/MWh
- Energy: MWh
- Power: MW
- Frequency: Hz

✅ **Data Freshness**:
- Event-driven: BOALF, MELS (real-time when caught up)
- 30 min: MID, IMBALNGC
- 2-5 min: FREQ, FUELINST (when caught up)

✅ **Primary Dataset**: `inner-cinema-476211-u9.uk_energy_prod` (US region, BigQuery)

⚠️ **Current Limitation**: 4-7 day ingestion lag on some `_iris` tables due to server capacity

---

**Last Updated**: November 10, 2025  
**Dataset Location**: BigQuery US region  
**Project ID**: inner-cinema-476211-u9
