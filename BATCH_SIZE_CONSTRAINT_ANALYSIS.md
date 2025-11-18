# 🔍 Batch Size Constraint Analysis - November 13, 2025

## The Core Constraint

**The constraint is: TOTAL ROWS PER BATCH, not FILES per batch**

### BigQuery insertAll API Limits

```
✅ Recommended max: 10,000 rows per request
⚠️  Hard timeout: 600 seconds (10 minutes)
📦 Max request size: 10 MB
```

## The Problem with Fixed File Count

**Current implementation:** `MAX_FILES_PER_SCAN = 25` for ALL tables

This causes issues because **different tables have vastly different rows per file**:

| Table | Rows/File | 25 Files = | 50 Files = | Status |
|-------|-----------|------------|------------|--------|
| **MILS** | 1 | 25 rows | 50 rows | ✅ Way under limit |
| **MELS** | 1 | 25 rows | 50 rows | ✅ Way under limit |
| **FUELINST** | 20 | 500 rows | 1,000 rows | ✅ Well under limit |
| **BOALF** | ~50 | 1,250 rows | 2,500 rows | ✅ Under limit |
| **INDGEN** | ~900 | 22,500 rows | 45,000 rows | ❌ **TIMES OUT!** |

## Why INDGEN Caused 48-Hour Timeout Loop

**At MAX_FILES_PER_SCAN = 50:**
```
50 files × 900 rows/file = 45,000 rows
→ Takes 10+ minutes to upload
→ Exceeds 600 second timeout
→ Connection drops with SSL error
→ Files kept for retry
→ Infinite loop ♾️
```

**At MAX_FILES_PER_SCAN = 25:**
```
25 files × 900 rows/file = 22,500 rows
→ Takes ~5 minutes to upload
→ Within timeout limit (barely)
→ Success! ✅
```

**At MAX_FILES_PER_SCAN = 10:**
```
10 files × 900 rows/file = 9,000 rows
→ Takes ~2 minutes to upload
→ Well within timeout
→ Success with margin! ✅✅
```

## Why Processing is Slow Now

**Current situation:**
- MILS: 78,805 files @ 25 files/batch = 3,152 batches = 263 minutes
- MELS: 64,117 files @ 25 files/batch = 2,565 batches = 214 minutes
- BOALF: 23,814 files @ 25 files/batch = 953 batches = 79 minutes
- **FUELINST: 837 files waiting behind all of these** 😢

**The inefficiency:**
```
MILS processing:
- 25 files → only 25 ROWS (0.25% of safe limit!)
- Could safely do 100 files → 100 rows
- 4× slower than necessary

FUELINST processing:
- 25 files → only 500 ROWS (5% of safe limit!)
- Could safely do 100 files → 2,000 rows
- 4× slower than necessary
```

## Optimal Batch Sizes Per Table

| Table | Rows/File | Optimal Files/Batch | Rows/Batch | Reasoning |
|-------|-----------|---------------------|------------|-----------|
| **MILS** | 1 | 100 | 100 | Maximize throughput |
| **MELS** | 1 | 100 | 100 | Maximize throughput |
| **FUELINST** | 20 | 100 | 2,000 | Maximize throughput |
| **BOALF** | 50 | 100 | 5,000 | Maximize throughput |
| **INDGEN** | 900 | 10 | 9,000 | Stay under 10k limit |

## The Solution: Adaptive Batch Sizing

### Option 1: Quick Fix (Current Approach)
```python
# Use conservative fixed size that works for worst case
MAX_FILES_PER_SCAN = 25

# Works for: INDGEN (22,500 rows - borderline)
# Inefficient for: MILS, MELS, FUELINST (massively underutilized)
# Result: 9+ hours to clear backlog
```

### Option 2: Per-Table Configuration (Better)
```python
MAX_FILES_PER_TABLE = {
    'INDGEN': 10,      # 9,000 rows
    'BOALF': 100,      # 5,000 rows
    'FUELINST': 100,   # 2,000 rows
    'MILS': 100,       # 100 rows
    'MELS': 100,       # 100 rows
    'default': 25      # Safe fallback
}

# Result: 2-3 hours to clear backlog (3× faster)
```

### Option 3: Dynamic Calculation (Best)
```python
def calculate_optimal_batch_size(dataset_name, sample_files):
    """Calculate optimal batch size based on actual row counts"""
    
    # Sample first few files to estimate rows per file
    avg_rows_per_file = estimate_rows_per_file(sample_files)
    
    # Target: 8,000 rows per batch (20% safety margin)
    target_rows = 8000
    optimal_files = min(
        target_rows // avg_rows_per_file,
        100  # Cap at 100 files
    )
    
    return max(optimal_files, 10)  # Minimum 10 files

# Result: Automatic optimization for any table
```

## Current Status & ETAs

### With MAX_FILES_PER_SCAN = 25 (Current)

**Processing rate:** 300 files/minute

| Queue | Files | ETA | Cumulative |
|-------|-------|-----|------------|
| MILS | 78,805 | 4.4 hours | 4.4 hours |
| MELS | 64,117 | 3.6 hours | 8.0 hours |
| BOALF | 23,814 | 1.3 hours | 9.3 hours |
| **FUELINST** | **837** | **3 min** | **9.3 hours** ⬅️ Dashboard stuck until then |

### With Adaptive Sizing (Proposed)

**Processing rates:**
- MILS/MELS: 1,200 files/minute (4× faster)
- FUELINST: 1,200 files/minute (4× faster)
- INDGEN: 120 files/minute (same)

| Queue | Files | ETA | Cumulative |
|-------|-------|-----|------------|
| MILS | 78,805 | 1.1 hours | 1.1 hours |
| MELS | 64,117 | 0.9 hours | 2.0 hours |
| BOALF | 23,814 | 0.3 hours | 2.3 hours |
| **FUELINST** | **837** | **<1 min** | **2.3 hours** ⬅️ 4× faster! |

## Immediate Options

### Option A: Wait 9 Hours (No Action)
- ✅ Safe (no code changes)
- ❌ Dashboard fuel generation stale for 9+ more hours
- ❌ Inefficient use of resources

### Option B: Temporarily Skip Low-Priority Tables
```bash
# Move MILS/MELS aside temporarily
cd /opt/iris-pipeline/iris-clients/python/iris_data
mv MILS MILS_TEMP_SKIP
mv MELS MELS_TEMP_SKIP

# FUELINST processes immediately
# Move them back later to process backlog
```
- ✅ FUELINST data in 3 minutes
- ✅ Dashboard recovers immediately
- ⚠️ MILS/MELS backlog grows during skip period
- ⚠️ Need to move back later

### Option C: Implement Per-Table Batch Sizes (Best Long-Term)
```python
# Edit iris_to_bigquery_unified.py
MAX_FILES_PER_TABLE = {
    'INDGEN': 10,
    'BOALF': 100,
    'FUELINST': 100,
    'MILS': 100,
    'MELS': 100,
}

# Use in processing loop:
max_files = MAX_FILES_PER_TABLE.get(dataset_upper, 25)
```
- ✅ 4× faster processing
- ✅ Optimal for all table types
- ✅ No data loss
- ⚠️ Requires code change + testing
- ⚠️ 15 minutes to implement

### Option D: Let It Run Overnight (Pragmatic)
- Current time: 06:40 UTC
- ETA completion: 16:00 UTC (9 hours)
- ✅ No intervention needed
- ✅ Will complete during business hours
- ❌ Dashboard stale until afternoon

## Recommendation

**Short term (NOW):** Let current batch size (25) continue running

**Why:**
- Already processing successfully at 300 files/min
- Will complete by 16:00 UTC today
- Zero risk of breaking anything

**Long term (THIS WEEK):** Implement Option C (per-table batch sizes)

**Why:**
- Prevents this issue in future
- 4× faster recovery from any future downtime
- Optimizes resource usage

## Key Insights

1. **The constraint is row count, not file count**
   - BigQuery API limit: ~10,000 rows per request
   - Different tables have wildly different row counts per file
   
2. **One size does NOT fit all**
   - INDGEN needs small batches (10 files = 9k rows)
   - FUELINST can handle huge batches (100 files = 2k rows)
   
3. **Current fixed-size approach is safe but inefficient**
   - Works for worst case (INDGEN)
   - Massively underutilizes capacity for other tables
   
4. **The 48-hour timeout was caused by:**
   - MAX_FILES_PER_SCAN = 50
   - INDGEN files = 900 rows each
   - 50 × 900 = 45,000 rows → timeout
   
5. **The fix that worked:**
   - Reduced to MAX_FILES_PER_SCAN = 25
   - 25 × 900 = 22,500 rows → success
   - But left us with 9-hour processing time

## Lessons for Production

### Health Check Enhancement Needed

```bash
# Add to health_check.sh:

# Check for large file backlogs
for dir in iris_data/*/; do
    file_count=$(ls "$dir" 2>/dev/null | wc -l)
    if [ $file_count -gt 1000 ]; then
        echo "⚠️ ALERT: $dir has $file_count files waiting"
        # Could automatically adjust batch size
    fi
done
```

### Monitoring Metrics to Track

1. **Files waiting per table** (current: not monitored)
2. **Average processing time per batch** (detect timeouts early)
3. **Rows per batch by table** (detect inefficiency)
4. **Queue age** (alert if data >3 hours old)

### Documentation for Future

When troubleshooting upload issues:

1. ✅ Check: Are files being downloaded? (client.log)
2. ✅ Check: Are files being uploaded? (uploader.log)
3. ✅ Check: Are there timeout errors?
4. **NEW:** Check: How many rows per file for this table?
5. **NEW:** Check: Is batch size optimal for this table?
6. **NEW:** Check: How long has queue been backed up?

---

*Analysis Generated: 2025-11-13 06:40 UTC*  
*Context: Post-recovery from 48-hour timeout incident*  
*Current Status: Processing at 300 files/min, 9-hour backlog remaining*
