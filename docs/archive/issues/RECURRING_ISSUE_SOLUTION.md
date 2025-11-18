# Solution to Recurring Data Architecture Issues

**Date:** 31 October 2025  
**Problem:** Keep rediscovering data format/table differences  
**Solution:** Process changes + documentation + utility tool  
**Status:** ✅ Implemented

---

## 🎯 The Problem

We keep going "around in circles" re-discovering:

1. **Historical vs Real-time data formats differ**
   - Historical: `bmrs_*` tables (DATETIME, full history)
   - Real-time: `bmrs_*_iris` tables (DATETIME, recent only)
   
2. **Some tables have limited coverage**
   - `bmrs_bod`: 1,397 days (2022-01-01 to 2025-10-28) ✅
   - `demand_outturn`: 1,392 records (Sept-Oct 2025 only) ⚠️

3. **Data types incompatible**
   - `bmrs_bod.settlementDate`: DATETIME
   - `demand_outturn.settlementDate`: STRING
   - Cannot join directly!

**Impact:** Waste time debugging the same issues repeatedly.

---

## ✅ The Solution (3-Part)

### 1. ⚠️ STOP Document (Read First)

**File:** `STOP_DATA_ARCHITECTURE_REFERENCE.md`

**Purpose:** Single reference to check BEFORE any new query/script

**Contents:**
- Golden Rules (check coverage first, verify data types)
- Table Coverage Matrix (which tables have what ranges)
- Data Type Compatibility guide
- Common Mistakes (with examples)
- Pre-Query Checklist
- Decision Tree
- Quick Reference Card

**Usage:**
```bash
# Read before ANY new work
open STOP_DATA_ARCHITECTURE_REFERENCE.md
```

### 2. 🛠️ Utility Script (Check Coverage)

**File:** `check_table_coverage.sh`

**Purpose:** Automatically check table date ranges and types

**Usage:**
```bash
# Check any table
./check_table_coverage.sh bmrs_bod
./check_table_coverage.sh demand_outturn
```

**Output:**
```
📊 Table Coverage Check: bmrs_bod
✅ Table exists
Date type: DATETIME
Min date: 2022-01-01 00:00:00
Max date: 2025-10-28 00:00:00
Unique days: 1,397
Total records: 391,287,533
```

### 3. 📚 Documentation Updates

**Updated files:**

1. **README.md**
   - Added warning at top: "READ THIS FIRST"
   - Links to STOP document
   - Quick coverage check commands

2. **DOCUMENTATION_INDEX.md**
   - Added STOP_DATA_ARCHITECTURE_REFERENCE entry
   - Added PRICE_DEMAND_CORRELATION_FIX entry
   - Marked as "CRITICAL - Read First"

3. **New comprehensive docs:**
   - `STOP_DATA_ARCHITECTURE_REFERENCE.md` - The main reference
   - `PRICE_DEMAND_CORRELATION_FIX.md` - Recent example of the issue
   - `check_table_coverage.sh` - Automation tool

---

## 🔄 New Workflow (Follow This!)

### Before ANY New Query/Script:

```bash
# Step 1: Read the STOP document
open STOP_DATA_ARCHITECTURE_REFERENCE.md

# Step 2: Check table coverage
./check_table_coverage.sh TABLE_NAME

# Step 3: Check schema if joining
bq show --schema TABLE_NAME | grep "date_column" -A 2

# Step 4: Copy template from PROJECT_CONFIGURATION.md

# Step 5: Test with LIMIT 10
bq query --max_rows=10 "YOUR QUERY LIMIT 10"

# Step 6: Only then run full query
```

---

## 📊 Current State (31 Oct 2025)

### Table Coverage Matrix

| Table | Date Range | Days | Type | Status |
|-------|------------|------|------|--------|
| **bmrs_bod** | 2022-01-01 → 2025-10-28 | 1,397 | DATETIME | ✅ Full |
| **bmrs_fuelinst** | 2024-01-01 → recent | 669 | DATETIME | ✅ Full |
| **bmrs_freq** | Unknown | ? | DATETIME | ⚠️ Check |
| **demand_outturn** | 2025-09-27 → 2025-10-25 | 29 | **STRING** | ⚠️ Recent only |
| **bmrs_*_iris** | Recent | ? | DATETIME | 🟢 Live |

### Known Issues

1. **demand_outturn**: Only 29 days of data (not full history)
2. **Data type mismatch**: DATETIME vs STRING requires DATE casting
3. **IRIS tables**: Not documented for coverage yet

---

## 💡 Key Learnings Documented

### From Today's Session:

1. **Price-Demand Correlation Failure**
   - Root cause: DATETIME (bmrs_bod) vs STRING (demand_outturn)
   - Solution: Cast both to DATE
   - Documented in: `PRICE_DEMAND_CORRELATION_FIX.md`

2. **Table Coverage Assumptions**
   - Assumed demand_outturn had full 2024-2025 data
   - Actually only has 29 days
   - Solution: Always check with `./check_table_coverage.sh`

3. **Settlement Period 50**
   - Assumed daily occurrence
   - Actually only 2 days/year (clock change)
   - Solution: Always check data frequency/distribution

---

## 🎯 How This Prevents Recurrence

### Process Changes:

1. **Mandatory first step**: Read STOP document ✅
2. **Automated checking**: Use coverage script ✅
3. **Visible warnings**: Updated README with warnings ✅
4. **Documentation links**: All docs cross-reference each other ✅

### Tools Created:

1. **check_table_coverage.sh** - Automate coverage checks ✅
2. **STOP document** - Single reference for all issues ✅
3. **Pre-query checklist** - Step-by-step guide ✅

### Documentation Structure:

```
Start ANY new work
        ↓
Read STOP_DATA_ARCHITECTURE_REFERENCE.md
        ↓
Run ./check_table_coverage.sh
        ↓
Check PROJECT_CONFIGURATION.md for schemas
        ↓
Use template from PROJECT_CONFIGURATION.md
        ↓
Test with LIMIT 10
        ↓
Proceed with confidence ✅
```

---

## 📚 All Related Documentation

### Primary References:
1. **[STOP_DATA_ARCHITECTURE_REFERENCE.md](STOP_DATA_ARCHITECTURE_REFERENCE.md)** - Read first
2. **[UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md](UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md)** - Complete architecture
3. **[PROJECT_CONFIGURATION.md](PROJECT_CONFIGURATION.md)** - Schemas and templates
4. **[PRICE_DEMAND_CORRELATION_FIX.md](PRICE_DEMAND_CORRELATION_FIX.md)** - Recent example

### Utility:
- **[check_table_coverage.sh](check_table_coverage.sh)** - Automated coverage check

### Entry Points:
- **[README.md](README.md)** - Updated with warnings
- **[DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md)** - Complete index

---

## ✅ Success Metrics

### Immediate:
- ✅ STOP document created (500+ lines)
- ✅ Utility script created and tested
- ✅ README updated with warnings
- ✅ DOCUMENTATION_INDEX updated
- ✅ New docs added to index

### Ongoing:
- [ ] Use checklist before every new query
- [ ] Run coverage script before joins
- [ ] Update STOP doc when new tables added
- [ ] Document any new data issues discovered

---

## 🎯 The Answer to Your Question

### "How can we ensure this does not happen via documentation?"

**Answer: We already had the architecture documentation, but:**

1. ❌ **Not reading it first** → ✅ Now: STOP doc at top of README, impossible to miss
2. ❌ **Not checking coverage** → ✅ Now: Automated with `./check_table_coverage.sh`
3. ❌ **Not following process** → ✅ Now: Pre-query checklist in STOP doc
4. ❌ **Starting from scratch** → ✅ Now: Templates in PROJECT_CONFIGURATION.md
5. ❌ **Not documenting issues** → ✅ Now: PRICE_DEMAND_CORRELATION_FIX documents recent example

**The key change:** 
- **Before:** Documentation existed but wasn't enforced
- **After:** STOP document + utility script + process checklist + prominent warnings

---

## 📞 Quick Reference

**Before any new query:**
```bash
# 1. Read STOP doc
open STOP_DATA_ARCHITECTURE_REFERENCE.md

# 2. Check coverage
./check_table_coverage.sh TABLE_NAME

# 3. Proceed with confidence!
```

**Files to bookmark:**
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` ⭐
- `check_table_coverage.sh` 🛠️
- `PROJECT_CONFIGURATION.md` 🔧

---

**Status:** ✅ **SOLUTION IMPLEMENTED**  
**Files Created:** 3 (STOP doc + Fix doc + Utility script)  
**Files Updated:** 2 (README + DOCUMENTATION_INDEX)  
**Process:** Documented and enforced  
**Tools:** Automated coverage checking  
**Next:** Follow the workflow! 🎯
