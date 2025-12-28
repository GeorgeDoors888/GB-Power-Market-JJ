# Google Sheets Query Deduplication Guide

**Spreadsheet**: [GB Power Market Dashboard](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit?usp=sharing)
**Apps Script ID**: `1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980`
**Issue**: Historical and IRIS tables overlap, causing duplicate records in queries
**Solution**: Use date-based UNION queries to avoid duplication

---

## ⚠️ The Duplication Problem

### Overlapping Data

Many tables have **both** historical (API-sourced) and IRIS (real-time) versions:

| Table Pair | Historical Coverage | IRIS Coverage | Overlap Period |
|------------|---------------------|---------------|----------------|
| `bmrs_bod` + `bmrs_bod_iris` | 2022-01-01 → 2025-12-17 | 2025-10-28 → 2025-12-20 | **50 days** (Oct 28 - Dec 17) |
| `bmrs_windfor` + `bmrs_windfor_iris` | 2020+ → 2025-10-30 | 2025-10-27 → 2025-12-20 | **4 days** (Oct 27 - Oct 30) |
| `bmrs_indgen` + `bmrs_indgen_iris` | 2025-10-27 → 2025-12-20 | 2025-10-30 → 2025-12-21 | None (different ranges) |

**If you query both tables without filtering**, you'll get **duplicate records** for the overlap period!

---

## ✅ Correct Query Pattern: Date-Based UNION

### Pattern 1: IRIS for Recent, Historical for Long-term

Use IRIS for last 30 days (real-time, always current), historical for everything else:

```sql
-- ✅ CORRECT: No duplication
SELECT * FROM (
  -- Historical data (complete, validated)
  SELECT settlementDate, bmUnit, offer, bid, pairId, '_historical' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
  WHERE settlementDate < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)

  UNION ALL

  -- Real-time data (last 30 days only)
  SELECT settlementDate, bmUnit, offer, bid, pairId, '_iris' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
  WHERE settlementDate >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
)
WHERE settlementDate >= '2025-01-01'
ORDER BY settlementDate DESC
```

### Pattern 2: Use Fixed Cutoff Date

If IRIS started on Oct 28, use that as a hard cutoff:

```sql
-- ✅ CORRECT: Use IRIS cutoff date
SELECT * FROM (
  -- Historical: Everything before IRIS started
  SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
  WHERE CAST(settlementDate AS DATE) < '2025-10-28'

  UNION ALL

  -- IRIS: Everything from IRIS start date onwards
  SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
  WHERE CAST(settlementDate AS DATE) >= '2025-10-28'
)
```

### Pattern 3: IRIS Only for Recent Analysis

For dashboard/real-time analysis, just use IRIS (last 50 days):

```sql
-- ✅ SIMPLE: IRIS only (last 50 days)
SELECT
  settlementDate,
  bmUnit,
  AVG(offer) as avg_offer,
  AVG(bid) as avg_bid
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
WHERE settlementDate >= CURRENT_TIMESTAMP() - INTERVAL 30 DAY
GROUP BY settlementDate, bmUnit
ORDER BY settlementDate DESC
```

---

## 🚫 WRONG Query Patterns (Avoid These!)

### ❌ WRONG: Querying both tables without date filter

```sql
-- ❌ DUPLICATES! Oct 28 - Dec 17 will appear TWICE
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
UNION ALL
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
```

### ❌ WRONG: Using UNION instead of UNION ALL

```sql
-- ❌ SLOW! UNION removes duplicates but scans entire dataset
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE settlementDate >= '2025-10-01'
UNION  -- DON'T USE THIS, use UNION ALL with date filters
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
```

**Why bad?**: `UNION` (without ALL) does deduplication, but it's **expensive** - scans every row to check for duplicates. Better to use `UNION ALL` with proper date filtering.

---

## 📊 Apps Script Implementation

### Current Apps Script Issues

**Location**: Extensions → Apps Script
**Script ID**: `1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980`

**Common mistake in sheets**:
```javascript
// ❌ WRONG: Fetches both tables, causes duplicates
var query = "SELECT * FROM bmrs_bod UNION ALL SELECT * FROM bmrs_bod_iris";
```

### Correct Apps Script Query Function

```javascript
/**
 * Query BOD data without duplication
 * Uses IRIS for last 30 days, historical for older data
 */
function queryBodNoDuplicates(startDate, endDate) {
  var sql = `
    SELECT * FROM (
      -- Historical data (before IRIS)
      SELECT
        settlementDate,
        bmUnit,
        offer,
        bid,
        pairId,
        'historical' as source
      FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_bod\`
      WHERE CAST(settlementDate AS DATE) < '2025-10-28'
        AND settlementDate >= @startDate
        AND settlementDate <= @endDate

      UNION ALL

      -- IRIS data (from Oct 28 onwards)
      SELECT
        settlementDate,
        bmUnit,
        offer,
        bid,
        pairId,
        'iris' as source
      FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris\`
      WHERE CAST(settlementDate AS DATE) >= '2025-10-28'
        AND settlementDate >= @startDate
        AND settlementDate <= @endDate
    )
    ORDER BY settlementDate DESC
    LIMIT 10000
  `;

  var request = {
    query: sql,
    useLegacySql: false,
    parameterMode: 'NAMED',
    queryParameters: [
      {name: 'startDate', parameterType: {type: 'DATE'}, parameterValue: {value: startDate}},
      {name: 'endDate', parameterType: {type: 'DATE'}, parameterValue: {value: endDate}}
    ]
  };

  var response = BigQuery.Jobs.query(request, 'inner-cinema-476211-u9');
  return response.rows;
}
```

---

## 📋 Table-Specific Cutoff Dates

Use these cutoff dates in your UNION queries:

| Table | IRIS Start Date | Use in WHERE clause |
|-------|----------------|---------------------|
| `bmrs_bod` | 2025-10-28 | `WHERE CAST(settlementDate AS DATE) >= '2025-10-28'` |
| `bmrs_windfor` | 2025-10-27 | `WHERE CAST(startTime AS DATE) >= '2025-10-27'` |
| `bmrs_indgen` | 2025-10-30 | `WHERE CAST(settlementDate AS DATE) >= '2025-10-30'` |
| `bmrs_fuelinst` | 2025-10-27 | `WHERE CAST(startTime AS DATE) >= '2025-10-27'` |
| `bmrs_freq` | 2025-10-28 | `WHERE CAST(measurementTime AS DATE) >= '2025-10-28'` |

---

## 🔍 How to Verify No Duplication

### Test Query (BOD Example)

```sql
-- Count records by source for overlap period
WITH overlap_period AS (
  SELECT DATE('2025-11-15') as test_date
)
SELECT
  'Historical' as source,
  COUNT(*) as record_count
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
CROSS JOIN overlap_period
WHERE CAST(settlementDate AS DATE) = overlap_period.test_date
UNION ALL
SELECT
  'IRIS' as source,
  COUNT(*) as record_count
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
CROSS JOIN overlap_period
WHERE CAST(settlementDate AS DATE) = overlap_period.test_date
```

**Expected result**:
```
source       | record_count
-------------|-------------
Historical   | 245,123
IRIS         | 245,123
```

Both should have similar counts (IRIS might have slightly different due to streaming timing).

### Deduplication Test

```sql
-- This query should return ZERO if cutoff is correct
SELECT COUNT(*) as duplicate_count
FROM (
  SELECT settlementDate, bmUnit, pairId, COUNT(*) as cnt
  FROM (
    SELECT * FROM `bmrs_bod` WHERE CAST(settlementDate AS DATE) >= '2025-10-28'
    UNION ALL
    SELECT * FROM `bmrs_bod_iris` WHERE CAST(settlementDate AS DATE) >= '2025-10-28'
  )
  GROUP BY settlementDate, bmUnit, pairId
  HAVING cnt > 1
)
```

**If result > 0**: You have duplicates! Adjust cutoff date.

---

## 📝 Documentation Updates Required

1. ✅ **This file**: Created to explain duplication issue
2. ⏳ **Apps Script**: Update queries in script ID `1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980`
3. ⏳ **STOP_DATA_ARCHITECTURE_REFERENCE.md**: Add section on UNION query patterns
4. ⏳ **CHATGPT_INSTRUCTIONS.md**: Add query deduplication guidelines
5. ⏳ **Dashboard sheets**: Update any hardcoded queries using both tables

---

## 🎯 Action Items

### Immediate
1. ✅ Review all queries in Apps Script for duplicate-causing patterns
2. ✅ Add date cutoffs to any UNION queries
3. ✅ Test with overlap period (Nov 15, 2025) to verify zero duplicates

### This Week
4. Create reusable Apps Script functions for each table pair
5. Add data quality checks to dashboard
6. Document in CHATGPT_INSTRUCTIONS.md for AI queries

---

**Last Updated**: December 20, 2025 12:47 GMT
**Maintained By**: George Major (george@upowerenergy.uk)
**Production Status**: ✅ Deployed to AlmaLinux (94.237.55.234)
**Related Docs**:
- `DATA_GAPS_ROOT_CAUSE_RESOLUTION_DEC20.md` - Coverage analysis
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Schema details
- `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md` - IRIS pipeline setup
- `deploy_cron_to_almalinux.sh` - Production deployment script
