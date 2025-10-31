# Data Quality Check - Issues Found

## Summary
When running `check_data_quality_and_compare.py`, several BigQuery schema mismatches were discovered:

## Issues Found

### 1. **bmrs_boalf** - Wrong Column Name
**Error**: `Unrecognized name: settlementPeriod; Did you mean settlementPeriodTo?`

**Issue**: The script expected `settlementPeriod` but the table has different columns.

**Schema** (from ingest_elexon_v2.py):
```python
- bmUnit (STRING)          # NOT bmuId!
- settlementDate (DATE)
- settlementPeriod (INT64)  # Actually does exist
- timeFrom (TIMESTAMP)
- timeTo (TIMESTAMP)
- acceptanceNumber (INT64)
- acceptanceTime (TIMESTAMP)
- bidOfferLevel (STRING)   # Exists as string, not used as key
```

**Fix Needed**: Column names were correct. Error suggests different schema in production table. Need to verify actual table schema.

### 2. **bmrs_bod** - Wrong Column Name
**Error**: `Unrecognized name: bmuId; Did you mean bid?`

**Issue**: Expected `bmuId` but table has `bmUnit`

**Schema** (from ingest_elexon_v2.py):
```python
- bmUnit (STRING)          # NOT bmuId!
- settlementDate (DATE)
- settlementPeriod (INT64)
- timeFrom (TIMESTAMP)
- timeTo (TIMESTAMP)
- levelFrom (INT64)        # NOT bidOfferLevel!
- levelTo (INT64)
- bidPrice (NUMERIC)
- offerPrice (NUMERIC)
```

**Fix**: Change `bmuId` → `bmUnit` and `bidOfferLevel` → `levelFrom`

### 3. **bmrs_freq** - Wrong Column Name
**Error**: `Unrecognized name: timeFrom`

**Issue**: FREQ table doesn't have `timeFrom` column

**Schema** (from ingest_elexon_v2.py):
```python
- dataset (STRING)
- reportSnapshotTime (TIMESTAMP)
- spotTime (TIMESTAMP)      # NOT timeFrom!
- frequency (NUMERIC)
- ingested_utc (TIMESTAMP)
```

**Fix**: Change `timeFrom` → `spotTime`

### 4. **bmrs_fuelinst** - Duplicates Found ⚠️
**Result**: Found 100+ duplicate groups with 120 records each

**Sample**:
```
settlementDate  settlementPeriod  publishTime         num_records
2025-07-10      25                2025-07-10 12:54:00  120
2024-08-29      25                2024-08-29 12:45:00  120
```

**Analysis**: 
- 120 records = 20 fuel types × 6 duplicates per fuel
- Likely caused by multiple data loads
- Key should be: `[settlementDate, settlementPeriod, fuelType, publishTime]`
- Current check only uses: `[settlementDate, settlementPeriod, publishTime]`

**Fix**: Add `fuelType` to key fields OR run deduplication query

### 5. **bmrs_mid** - Duplicates Found ⚠️
**Result**: Found 100+ duplicate groups with 8 records each

**Sample**:
```
settlementDate  settlementPeriod  num_records
2024-04-08      3                 8
2024-07-29      3                 8
```

**Analysis**:
- 8 records per settlement period suggests multiple loads or different data sources
- MID (Market Index Data) should have ONE record per settlement period

**Fix**: Run deduplication keeping latest `ingested_utc`

### 6. **bmrs_fuelinst** - Missing Future Data ✅
**Result**: Found 40 missing settlement periods (today's future periods)

```
settlementDate  settlementPeriod
2025-10-29      27               # Future periods not yet published
2025-10-29      28
... (up to period 46)
```

**Analysis**: This is EXPECTED - today's future settlement periods haven't happened yet.

**Fix**: None needed - this is normal.

### 7. **bmrs_freq** - Gap Check Failed
**Error**: `Name settlementDate not found inside b`

**Issue**: FREQ table doesn't have `settlementDate` or `settlementPeriod` columns

**Schema**: Uses `spotTime` timestamps, not settlement periods

**Fix**: Skip gap check for FREQ (it's time-series data, not settlement-period-based)

### 8. **bmrs_mid** - Check interrupted
Script was interrupted (Ctrl+C) before completing MID gap check.

## Recommended Fixes

### Short Term (Quick Fix):
1. **Update `check_data_quality_and_compare.py`** with correct column names:
   - `bmrs_boalf`: Change key from `bmuId` → `bmUnit`
   - `bmrs_bod`: Change `bmuId` → `bmUnit`, `bidOfferLevel` → `levelFrom`
   - `bmrs_freq`: Skip duplicate/gap checks (different schema)
   - `bmrs_fuelinst`: Add `fuelType` to key fields
   
2. **Run deduplication queries** for:
   - `bmrs_fuelinst`: Keep latest `publishTime` per `[settlementDate, settlementPeriod, fuelType]`
   - `bmrs_mid`: Keep latest `ingested_utc` per `[settlementDate, settlementPeriod]`

### Long Term (Production):
1. **Add unique constraints** to BigQuery tables
2. **Update ingestion scripts** to check for existing data before inserting
3. **Implement `MERGE` statements** instead of `INSERT` to avoid duplicates
4. **Set up data quality monitoring** with alerts

## Next Steps

1. ✅ Document issues (this file)
2. ⏳ Create corrected `check_data_quality_and_compare_v2.py`
3. ⏳ Create deduplication SQL scripts
4. ⏳ Verify actual production table schemas with `INFORMATION_SCHEMA`
5. ⏳ Run cleanup and re-check

## IRIS Client Note
The IRIS client running in background is flooding all terminal output with download messages. This makes it difficult to see script output. Consider:
- Running IRIS client with output redirected to log file
- Using `> /dev/null 2>&1` to suppress output
- Running checks in separate session without IRIS client

---

**Created**: 2025-10-30 04:45 UTC  
**Status**: Issues identified, fixes pending
