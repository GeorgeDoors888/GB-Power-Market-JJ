# IRIS JSON Files - Issue Analysis

## Problem Summary

We have **63,792 JSON files** accumulated from IRIS, but they cannot be directly inserted into BigQuery due to **schema mismatches**.

## Root Cause

**Two different data sources with incompatible schemas:**

1. **Historic Data** (in BigQuery):
   - Source: Old BMRS API via `ingest_elexon_v2.py`
   - Schema: Custom ingestion schema
   - Example `bmrs_boalf`: `acceptanceTime` as DATETIME (no timezone)

2. **IRIS Real-Time Data** (JSON files):
   - Source: New Insights API via IRIS streaming
   - Schema: Insights API schema  
   - Example BOALF: `acceptanceTime` as ISO 8601 string with `.000Z`
   - Files contain **arrays** of records (not single objects)

## Specific Issues Found

### 1. **Datetime Format Mismatch**
```
BigQuery Error: Invalid datetime string "2025-10-28T08:59:00.000Z"
```

**IRIS sends**: `"2025-10-28T08:59:00.000Z"` (ISO 8601 with timezone)  
**BigQuery expects**: `2025-10-28 08:59:00` (DATETIME without Z)

### 2. **Column Name Differences** 
- IRIS: `settlementPeriodFrom`, `settlementPeriodTo`
- Historic: `settlementPeriod`

### 3. **Array vs Single Object**
- IRIS files contain arrays: `[{record1}, {record2}, ...]`
- Need to flatten before insertion

### 4. **Volume**
- **63,792 files** accumulated
- **~8,902 BOALF** files alone
- **~29,899 MILS** files  
- **~21,637 MELS** files

## Performance Test Results

✅ **Scanning Works Great:**
- Scanned 2,000 files in **0.28s** (7,139 files/sec)
- Extracted 242 records from 100 files

❌ **Insertion Blocked:**
- Schema/datetime incompatibility
- Need data transformation layer

## Options

### Option A: Transform IRIS Data (Complex)
**Pros:**
- Keep historic schema
- Integrate real-time with historic

**Cons:**
- Complex transformation logic
- Datetime parsing/conversion
- Column mapping required
- Schema evolution problems

**Effort:** 2-3 hours development + testing

### Option B: Separate IRIS Tables (Medium)
**Pros:**
- Clean separation
- Native IRIS schema
- Simpler code

**Cons:**
- Duplicate tables (`bmrs_boalf` vs `bmrs_boalf_iris`)
- Query complexity (need UNION)

**Effort:** 1 hour

### Option C: Delete JSON Files, Start Fresh (Simple)
**Pros:**
- **Immediate fix** - clears backlog
- Fresh start with proper integration
- Focus on historic data cleanup (Option B from earlier)

**Cons:**
- Lose 63K accumulated messages
- But they're mostly duplicates/old data anyway

**Effort:** 5 minutes

## Recommendation: **Option C**

### Reasoning:
1. **63,792 files are a problem**, not a solution
   - They're OLD messages (Oct 27-28)
   - We have historic data already
   - Taking up disk space

2. **Focus on what matters:**
   - Clean historic duplicates (63M+ records)
   - Fix data quality issues
   - Build dashboard

3. **IRIS will regenerate:**
   - Real-time messages continue
   - Fresh data with no backlog
   - Can implement proper integration later

4. **Disk space:**
   - 63,792 files × ~2KB each = ~127 MB
   - Not huge, but unnecessary

## Implementation: Clean Slate

### Step 1: Stop IRIS Client
```bash
pkill -f client.py
```

### Step 2: Archive or Delete JSON Files
```bash
# Option A: Archive (if you want backup)
cd "/Users/georgemajor/GB Power Market JJ"
tar -czf iris_data_backup_20251030.tar.gz iris-clients/python/iris_data/
rm -rf iris-clients/python/iris_data/*/

# Option B: Just delete (recommended)
rm -rf iris-clients/python/iris_data/*/*.json
```

### Step 3: Restart IRIS Client (Later)
```bash
cd iris-clients/python
python3 client.py > iris_client.log 2>&1 &
```

### Step 4: Implement Proper Integration (Future)
- Use BigQuery `LOAD DATA` jobs instead of streaming
- Transform datetime formats
- Handle arrays properly
- Add schema mapping

## Decision Point

**Q: What should we do with the 63,792 JSON files?**

**A: Delete them and move forward.**

**Rationale:**
1. They represent 2 days of old data (Oct 27-28)
2. We already have complete historic data in BigQuery (2022-2025)
3. Schema incompatibility requires significant development
4. Blocking progress on important work (data cleanup, dashboard)
5. IRIS will generate fresh data when we restart it

**Next Steps:**
1. ✅ Document findings (this file)
2. ⏳ Delete JSON files 
3. ⏳ Continue with Option B (Clean Data First):
   - Create deduplication SQL
   - Clean bmrs_fuelinst and bmrs_mid
   - Fix check_data_quality_and_compare.py
   - Re-run checks
4. ⏳ Build dashboard
5. ⏳ Implement proper IRIS integration later

---

**Created**: 2025-10-30 17:30 UTC  
**Recommendation**: Clean slate - delete JSON files, focus on historic data cleanup
