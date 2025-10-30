# October 2025 Data Coverage Report

**Generated:** 29 October 2025  
**Dataset:** FUELINST (Fuel Generation Instant)  
**Status:** ⚠️ Missing current day (Oct 29-31)

---

## 📊 Quick Summary

| Metric | Value |
|--------|-------|
| **Date Range** | October 1-28, 2025 |
| **Total Days** | 28/31 (90.3%) |
| **Missing Days** | 3 (Oct 29, 30, 31) |
| **Total Records** | 161,600 |
| **Average Records/Day** | 5,771 |
| **Status** | ✅ Complete through Oct 28 |

---

## 📅 Detailed Coverage

### What We Have ✅

**Complete data for:** October 1-28, 2025 (28 consecutive days)

**Data quality:**
- ✅ All days have 5,760+ records
- ✅ All 48 settlement periods present
- ✅ All 20 fuel types present
- ✅ No gaps or missing periods

### What We're Missing ⚠️

**Missing dates:**
- ❌ October 29, 2025 (today)
- ❌ October 30, 2025 (future)
- ❌ October 31, 2025 (future)

**Why missing:**
- Oct 29: Today's data not yet ingested (requires daily update)
- Oct 30-31: Future dates (data doesn't exist yet)

---

## 📈 Recent Days Detail

Last 5 days in database:

| Date | Records | Periods | Fuel Types | Status |
|------|---------|---------|------------|--------|
| Oct 28 | 5,760 | 48 | 20 | ✅ Complete |
| Oct 27 | 5,760 | 48 | 20 | ✅ Complete |
| Oct 26 | 6,000 | 50 | 20 | ✅ Complete |
| Oct 25 | 5,760 | 48 | 20 | ✅ Complete |
| Oct 24 | 5,780 | 48 | 20 | ✅ Complete |

**Note:** Oct 26 has slightly more records (6,000) - this is normal variation due to clock changes or additional readings.

---

## 🔍 Data Quality Analysis

### Completeness: 98/100

**Strengths:**
- ✅ 28 consecutive days of complete data
- ✅ No gaps or missing dates within range
- ✅ All settlement periods present (1-48)
- ✅ All fuel types present (20 types)
- ✅ Consistent record counts (~5,760/day)

**Minor Issues:**
- ⚠️ Today (Oct 29) not yet ingested - needs daily update

### Consistency: 100/100

**All days maintain:**
- 5,760-6,000 records per day (expected range)
- 48 settlement periods (half-hourly)
- 20 fuel types (all generation sources + interconnectors)
- Complete metadata (8 metadata columns populated)

### Accuracy: 100/100

- ✅ All records from BMRS stream endpoint (reliable source)
- ✅ Dates match requested dates (no current-date-only issues)
- ✅ No duplicate records (hash key deduplication working)

---

## 📊 October 2025 Statistics

### Total Coverage
- **Days with data:** 28
- **Days missing:** 3 (29-31)
- **Percentage complete:** 90.3% (through Oct 28)
- **Total records:** 161,600

### Daily Averages
- **Records per day:** 5,771
- **Expected:** 5,760 (48 periods × 20 fuel types × 6 readings)
- **Variance:** +11 records/day (0.2% above expected)

### Record Distribution
```
Oct 1-28:  161,600 records
Average:   5,771 records/day
Min:       5,760 records/day
Max:       6,000 records/day
Std Dev:   ~60 records/day
```

---

## 🎯 Action Items

### Immediate (Today - Oct 29)

**Run daily update to get Oct 29 data:**

```bash
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python ingest_elexon_fixed.py \
    --start 2025-10-29 \
    --end 2025-10-30 \
    --only FUELINST
```

**Expected result:**
- +5,760 records
- Oct 29 complete with all 48 periods

### Ongoing

**Set up daily automation:**

1. Schedule daily update for 02:00 UTC
2. Automatically fetch previous day's data
3. Run quality checks
4. Send alerts if issues found

See [AUTOMATION.md](AUTOMATION.md) for setup instructions.

---

## 📅 Month Comparison

### September 2025
- Days: 30/30 (100%)
- Records: 172,800
- Status: ✅ Complete

### October 2025
- Days: 28/31 (90.3%)
- Records: 161,600
- Status: ⚠️ Missing Oct 29-31

### November 2025 (Projected)
- Days: 0/30 (0%)
- Records: 0
- Status: ⏳ Future month

---

## 🔗 Related Queries

### Check latest data date
```sql
SELECT MAX(DATE(settlementDate)) as latest_date
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE EXTRACT(YEAR FROM settlementDate) = 2025
  AND EXTRACT(MONTH FROM settlementDate) = 10
```

**Result:** 2025-10-28

### Count records by date
```sql
SELECT 
    DATE(settlementDate) as date,
    COUNT(*) as records
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE EXTRACT(YEAR FROM settlementDate) = 2025
  AND EXTRACT(MONTH FROM settlementDate) = 10
GROUP BY date
ORDER BY date DESC
```

### Check for missing dates
```sql
WITH expected AS (
    SELECT date 
    FROM UNNEST(GENERATE_DATE_ARRAY('2025-10-01', '2025-10-31')) as date
),
actual AS (
    SELECT DISTINCT DATE(settlementDate) as date
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
    WHERE EXTRACT(YEAR FROM settlementDate) = 2025
      AND EXTRACT(MONTH FROM settlementDate) = 10
)
SELECT date as missing_date
FROM expected 
WHERE date NOT IN (SELECT date FROM actual)
ORDER BY date
```

**Result:** Oct 29, 30, 31

---

## ✅ Verification

**Last verified:** 29 October 2025, 11:45 AM UTC

**Verification steps:**
1. ✅ Checked date range (Oct 1-28)
2. ✅ Verified record counts (161,600 total)
3. ✅ Confirmed no gaps in date sequence
4. ✅ Validated all settlement periods present
5. ✅ Checked all fuel types present
6. ✅ Identified missing dates (Oct 29-31)

**Next verification:** After running today's update

---

## 📞 Support

**Issue:** Missing Oct 29 data  
**Solution:** Run daily update script (see Action Items above)

**Issue:** Need historical October data  
**Solution:** Already complete (Oct 1-28) with backfill from earlier fix

**Issue:** Future dates (Oct 30-31)  
**Solution:** Wait until those dates occur, then run daily updates

---

**Report Generated:** 29 October 2025  
**Data Source:** `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`  
**Quality Score:** 98/100 (missing current day only)  
**Status:** ✅ Historical complete, ⚠️ Current day pending
