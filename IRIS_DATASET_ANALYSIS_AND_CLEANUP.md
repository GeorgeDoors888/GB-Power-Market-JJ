# IRIS Datasets Analysis and Cleanup Plan

**Date:** October 30, 2025  
**Purpose:** Identify unknown datasets and plan disk space management

---

## 📊 Current Disk Usage

| Category | Size | Files | Status |
|----------|------|-------|--------|
| **Total IRIS data** | **1.1 GB** | **54,055 files** | Growing |
| Workspace total | 6.6 GB | N/A | - |
| Mac disk | 170 GB used (85%) | N/A | 30 GB free |

---

## 🔍 Unknown Datasets Identified

### Large Unwanted Datasets (~700 MB)

#### 1. **UOU2T3YW** - Output Usable (3-Year Weekly Forecast)
- **Size:** 433 MB (largest!)
- **Files:** ~72,695 records per file
- **Fields:** fuelType, bmUnit, publishTime, week, year, outputUsable
- **Purpose:** Long-term generation capacity forecasts (weekly for 3 years)
- **Keep?** ❌ NO - Forecasts, not real-time operational data
- **Action:** DELETE

#### 2. **MILS** - Maximum Import Limit Schedule
- **Size:** 163 MB
- **Purpose:** Maximum import limits for BM units
- **Keep?** ✅ YES - We have a table for this (but schema issue - 0 records)
- **Action:** KEEP - Fix schema issue

#### 3. **MELS** - Maximum Export Limit Schedule  
- **Size:** 111 MB
- **Status:** ✅ Working (6,075 records ingested)
- **Keep?** ✅ YES
- **Action:** KEEP

#### 4. **DISPTAV** - Disputed Availability
- **Size:** 78 MB
- **Purpose:** Disputed availability declarations
- **Keep?** ❌ NO - Rare administrative data
- **Action:** DELETE

#### 5. **BOAV** - Bid-Offer Availability
- **Size:** 61 MB
- **Purpose:** Availability declarations for bid-offer units
- **Keep?** ⚠️ MAYBE - Could be useful but not core data
- **Action:** DELETE (for now - can recreate table if needed later)

#### 6. **UOU2T14D** - Output Usable (14-Day Daily Forecast)
- **Size:** 36 MB
- **Files:** ~6,097 records per file
- **Fields:** fuelType, bmUnit, publishTime, forecastDate, outputUsable
- **Purpose:** Short-term generation capacity forecasts (daily for 14 days)
- **Keep?** ❌ NO - Forecasts, not operational
- **Action:** DELETE

#### 7. **PN** - Physical Notifications
- **Size:** 36 MB
- **Purpose:** Physical notification data for BM units
- **Keep?** ⚠️ MAYBE - Operational data but not core
- **Action:** DELETE (for now)

#### 8. **QPN** - Quiescent Physical Notifications
- **Size:** 33 MB
- **Purpose:** Quiescent physical notification data
- **Keep?** ❌ NO - Derived from PN
- **Action:** DELETE

#### 9. **BEB** - Balancing Energy Bids
- **Size:** 31 MB
- **Status:** ⚠️ Table exists but schema mismatch
- **Keep?** ✅ YES - Core balancing data
- **Action:** KEEP - Fix schema

#### 10. **ISPSTACK** - Integrated Single Electricity Market Stack
- **Size:** 24 MB
- **Purpose:** ISEM (Ireland) market data
- **Keep?** ❌ NO - Not UK GB market
- **Action:** DELETE

---

## ✅ Datasets We Keep (Have Tables)

| Dataset | Size | Status | Records |
|---------|------|--------|---------|
| **BOD** | ? | ✅ Working | 82,050 |
| **BOALF** | ? | ✅ Working | 9,752 |
| **MELS** | 111 MB | ✅ Working | 6,075 |
| **FREQ** | ? | ✅ Working | 2,656 |
| **MILS** | 163 MB | ⚠️ Schema issue | 0 |
| **FUELINST** | ? | ⏳ Pending | 0 |
| **REMIT** | ? | ⏳ Pending | 0 |
| **MID** | ? | ⏳ Pending | 0 |
| **BEB** | 31 MB | ⚠️ Schema issue | 0 |

---

## 🗑️ Cleanup Plan

### Phase 1: Delete Unwanted Datasets (Recommended) ✅
**Space Freed:** ~600 MB  
**Files Deleted:** ~20,000-30,000  

```bash
# Dry run first (see what would be deleted)
./iris_cleanup_files.sh --dry-run

# Delete unwanted datasets
./iris_cleanup_files.sh --unwanted
```

**Deletes:**
- UOU2T3YW (433 MB) - 3-year forecasts
- UOU2T14D (36 MB) - 14-day forecasts
- DISPTAV (78 MB) - Disputed availability
- BOAV (61 MB) - Bid-offer availability
- ISPSTACK (24 MB) - Ireland market data
- PN (36 MB) - Physical notifications
- QPN (33 MB) - Quiescent notifications
- Plus ~15 other minor datasets

**Keeps:**
- All 9 datasets with BigQuery tables

### Phase 2: Auto-Delete After Upload (Now Implemented) ✅
**Processor Modified:** `iris_to_bigquery_unified.py`

**Changes:**
- Files deleted immediately after successful BigQuery upload
- Only deletes on success (keeps on error for retry)
- Logs deletion count: `🗑️ Deleted N processed JSON files`
- Tracks total: `Total files deleted: X`

**Effect:**
- Disk usage stays constant (~100-200 MB for pending files)
- No manual cleanup needed
- Data safe in BigQuery

### Phase 3: Restart Processor (Required)
```bash
# Stop old processor
kill 596

# Start new processor with auto-delete
nohup ./.venv/bin/python iris_to_bigquery_unified.py > iris_processor.log 2>&1 &
echo $! > iris_processor.pid
```

---

## 📈 Expected Results

### Before Cleanup
- IRIS data: 1.1 GB
- Files: 54,055
- Growing continuously

### After Cleanup + Auto-Delete
- IRIS data: ~100-200 MB (only pending files)
- Files: ~100-500 (processed within seconds)
- Stable (auto-deletes after upload)

### Disk Space Freed
- Immediate: ~600 MB (delete unwanted)
- Ongoing: ~900 MB (auto-delete processed files)
- **Total saved: ~1.5 GB** (reduces 1.1 GB to ~100 MB)

---

## 🎯 Execution Plan

### Step 1: Preview Cleanup (Safe) ✅
```bash
./iris_cleanup_files.sh --dry-run
```
Shows what would be deleted without actually deleting.

### Step 2: Delete Unwanted Datasets ✅
```bash
./iris_cleanup_files.sh --unwanted
```
Frees ~600 MB immediately.

### Step 3: Restart Processor with Auto-Delete ✅
```bash
# Stop old processor
kill 596

# Start new processor
nohup ./.venv/bin/python iris_to_bigquery_unified.py > iris_processor.log 2>&1 &
NEW_PID=$!
echo $NEW_PID > iris_processor.pid
echo "New processor PID: $NEW_PID"
```

### Step 4: Verify Auto-Delete Working
```bash
# Watch file count decrease as files are processed
watch -n 5 'find iris-clients/python/iris_data -name "*.json" | wc -l'

# Check processor logs for deletion messages
tail -f iris_processor.log | grep "Deleted"
```

### Step 5: Update Monitoring PID
```bash
# Update overnight monitor with new PID
# Edit iris_overnight_monitor.sh and change:
# PROCESSOR_PID=596
# to:
# PROCESSOR_PID=[new PID from step 3]
```

---

## 📊 Dataset Reference

### Core Operational Data (Keep)
- **BOD** - Bid-Offer Data
- **BOALF** - Bid-Offer Acceptance Levels and Flagging
- **MELS** - Maximum Export Limit Schedule
- **MILS** - Maximum Import Limit Schedule
- **FREQ** - System Frequency
- **FUELINST** - Instantaneous Generation by Fuel Type
- **BEB** - Balancing Energy Bids

### Market Data (Keep)
- **MID** - Market Index Data
- **REMIT** - REMIT Unavailability Messages

### Forecasts (Delete)
- **UOU2T3YW** - 3-year weekly forecasts
- **UOU2T14D** - 14-day daily forecasts
- **TSDF** - Transmission System Demand Forecast
- **ITSDO** - Initial Transmission System Demand Outturn

### Administrative (Delete)
- **DISPTAV** - Disputed Availability
- **CDN** - Credit Default Notice
- **SYSWARN** - System Warnings

### Minor Operational (Delete - can recreate if needed)
- **PN** - Physical Notifications
- **QPN** - Quiescent Physical Notifications
- **BOAV** - Bid-Offer Availability
- **ISPSTACK** - ISEM Stack (Ireland)

---

## 🔒 Safety Notes

### Data Safety ✅
- All ingested data safe in BigQuery
- Can always re-download from IRIS if needed
- Processor keeps files on upload failure (for retry)

### Rollback Plan
If auto-delete causes issues:
1. Stop new processor: `kill [new PID]`
2. Restore old processor code (backup in git)
3. Restart old processor: `git checkout iris_to_bigquery_unified.py`

### What Can't Be Recovered
- Files for deleted datasets (UOU2T3YW, etc.)
- But these have no tables anyway, so data wasn't being saved
- Can re-enable if needed by creating tables

---

## 📝 Summary

**Problems Solved:**
1. ✅ Identified 10+ unknown datasets
2. ✅ Created cleanup script for unwanted datasets
3. ✅ Modified processor to auto-delete after upload
4. ✅ Plan to free 1.5 GB disk space

**Actions Required:**
1. Run cleanup script: `./iris_cleanup_files.sh --unwanted`
2. Restart processor with new code: `kill 596 && nohup ./.venv/bin/python ...`
3. Update monitoring script with new PID
4. Verify auto-delete working

**Expected Outcome:**
- Disk usage: 1.1 GB → ~100 MB
- Files: 54,055 → ~100-500 (steady state)
- System: Stable, self-cleaning

---

**Ready to execute!** 🚀

See execution commands above.
