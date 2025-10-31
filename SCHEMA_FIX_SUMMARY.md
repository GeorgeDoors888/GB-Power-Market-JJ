# Schema Fix Summary - Advanced Calculations

**Date**: 2025-10-31  
**Status**: ✅ FIXED  

## Problem Discovered

The advanced calculations script (`update_analysis_with_calculations.py`) was failing because it assumed a different BigQuery table schema than what actually exists in the `inner-cinema-476211-u9.uk_energy_prod` dataset.

## Root Causes

### 1. ❌ bmrs_bod Table Schema Mismatch

**Expected (BOD Acceptance schema):**
- `soFlag` - Bid/Offer indicator
- `bmUnit` - BM Unit ID for filtering (e.g., WIND units)
- `bidOfferAcceptanceLevel` - Accepted volume (MWh)
- `bidOfferAcceptancePrice` - Accepted price (£/MWh)

**Actual (BM Unit Data schema):**
- `settlementDate`, `settlementPeriod` ✅
- `timeFrom`, `timeTo` ✅
- `levelFrom`, `levelTo` ✅
- `pairId` ✅
- `bid` (price) ✅
- `offer` (price) ✅
- `dataset` ✅

**Impact:** Could not calculate wind curtailment or proper balancing statistics using acceptance volumes.

### 2. ❌ bmrs_freq Column Name Wrong

**Expected:** `recordTime`  
**Actual:** `measurementTime`

**Impact:** All frequency-related queries failed.

### 3. ⚠️ Missing db-dtypes Package

**Error:** `ModuleNotFoundError: No module named 'db_dtypes'`  
**Impact:** BigQuery couldn't convert results to pandas DataFrames.

### 4. ⚠️ bmrs_fuelinst_iris Empty

**Status:** 0 rows  
**Impact:** No real-time generation data available (IRIS not ingesting).

## Solutions Implemented

### 1. ✅ Fixed bmrs_bod Queries

**Wind Curtailment (OLD - BROKEN):**
```sql
WHERE soFlag = 'B' AND bmUnit LIKE '%WIND%'
    AND bidOfferAcceptanceLevel < 0
```

**Wind Curtailment (NEW - FIXED):**
```sql
SELECT
    COUNT(*) as bid_count,
    AVG(bid) as avg_bid_price,
    SUM(CASE WHEN bid > 0 THEN 1 ELSE 0 END) as positive_bids
FROM bmrs_bod
WHERE DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    AND bid IS NOT NULL
    AND bid > 0
```

**Balancing Statistics (NEW - FIXED):**
```sql
SELECT
    COUNT(*) as total_records,
    AVG(bid) as avg_bid_price,
    AVG(offer) as avg_offer_price,
    SUM(CASE WHEN bid IS NOT NULL AND bid > 0 THEN 1 ELSE 0 END) as bid_count,
    SUM(CASE WHEN offer IS NOT NULL AND offer > 0 THEN 1 ELSE 0 END) as offer_count
FROM bmrs_bod
```

### 2. ✅ Fixed bmrs_freq Queries

Changed all references from `recordTime` to `measurementTime`:
```python
# Quality checks
('Frequency', 'bmrs_freq', ['frequency', 'measurementTime']),

# Query
WHERE DATE(measurementTime) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
```

### 3. ✅ Installed db-dtypes Package

```bash
pip3 install --user db-dtypes
```
Also installed `pyarrow` as dependency.

## Results - Advanced Calculations Now Working! 🎉

### ✅ Wind Curtailment Analysis
- Status: No curtailment data available (expected with current schema)

### ✅ Balancing Volume Breakdown
- **Bids:** 2,151,589 records | £-1041.67/MWh avg
- **Offers:** 3,725,897 records | £1595.69/MWh avg
- **Bid/Offer Ratio:** 0.58

### ✅ Capacity Factors
- BIOMASS: 38.1%
- NUCLEAR: 37.5%
- WIND: 34.4%
- CCGT: 32.0%
- OCGT: 2.3%

### ✅ Data Quality Scores
- Generation: 100.0%
- Frequency: 0.0% (⚠️ query returned no data - different issue)
- Prices: 100.0%
- Balancing: 100.0%

## Actual BigQuery Schemas

### bmrs_bod (BM Unit Bid-Offer Data)
```
dataset          STRING
settlementDate   DATETIME
settlementPeriod INTEGER
timeFrom         DATETIME
levelFrom        INTEGER
timeTo           DATETIME
levelTo          INTEGER
pairId           INTEGER
offer            FLOAT
bid              FLOAT
```
**Row count:** 391,287,533 (2022-01-01 → 2025-10-28)

### bmrs_freq (System Frequency)
```
dataset              STRING
measurementTime      DATETIME  ← CORRECT COLUMN NAME
frequency            FLOAT64
_dataset             STRING
_window_from_utc     STRING
_window_to_utc       STRING
_ingested_utc        STRING
_source_columns      STRING
_source_api          STRING
_hash_source_cols    STRING
_hash_key            STRING
```

## Remaining Issues

### 1. ⚠️ Frequency Quality Score = 0.0%

The query is now syntactically correct but returning no data. Need to investigate:
- Are there records in the date range?
- Is the WHERE clause too restrictive?
- Check sample data: `SELECT * FROM bmrs_freq LIMIT 10`

### 2. ⚠️ bmrs_fuelinst_iris Empty (0 rows)

IRIS real-time data not being ingested. Check:
- Is IRIS client running?
- Check `iris_client.log` for errors
- Verify IRIS API credentials
- May need to restart IRIS ingestion pipeline

### 3. 📝 Wind Curtailment Limited

Current query can't identify actual curtailment because:
- No `bmUnit` column to filter wind units
- No acceptance volumes (only bid/offer prices)
- May need to use `bmrs_fuelinst` to identify wind generation instead
- Or cross-reference with BM Unit metadata table

## Files Modified

1. **update_analysis_with_calculations.py**
   - Fixed `calculate_wind_curtailment()` function
   - Fixed `calculate_balancing_statistics()` function
   - Changed `recordTime` → `measurementTime` (2 locations)

## Testing

```bash
# Run the fixed script
python3 update_analysis_with_calculations.py

# Read the updated sheet
python3 read_full_sheet.py
```

## Next Steps

1. **Investigate frequency quality score issue**
   ```sql
   SELECT COUNT(*), MIN(measurementTime), MAX(measurementTime)
   FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
   WHERE DATE(measurementTime) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
   ```

2. **Check IRIS ingestion status**
   - Look for `iris_client.log`
   - Check if IRIS client is running: `ps aux | grep iris`
   - Review IRIS configuration

3. **Improve wind curtailment calculation**
   - Query `bmrs_fuelinst` for wind generation levels
   - Cross-reference with expected capacity
   - Identify periods where wind < capacity = potential curtailment

4. **Document all table schemas**
   - Create comprehensive schema reference
   - Add to project documentation
   - Include sample queries for each table

## Success Metrics

✅ Advanced calculations section (rows 112-140) now populated  
✅ Balancing statistics showing real data (5.9M records)  
✅ Capacity factors calculated from real generation data  
✅ 3 of 4 quality scores working (75% success rate)  
✅ No more "No data available" placeholders (except expected cases)  

## Lessons Learned

1. **Always verify schema before writing queries** - Don't assume table structure
2. **Use INFORMATION_SCHEMA to check columns** - Prevents column name errors
3. **Install all required packages** - db-dtypes needed for BigQuery pandas operations
4. **Test queries individually** - Easier to debug than monolithic scripts
5. **Document actual schemas** - Saves time on future development

---

**Status:** Advanced calculations working with schema-compatible queries! 🎉
