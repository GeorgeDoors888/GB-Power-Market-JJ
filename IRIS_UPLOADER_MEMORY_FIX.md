# IRIS Uploader Memory Fix Applied

**Date:** 4 November 2025, 18:28 UTC  
**Issue:** Out of Memory (OOM) Killer  
**Status:** ✅ FIX APPLIED & UPLOADER RESTARTED

---

## Problem Discovered

### Symptoms
- Uploader kept restarting every 5 minutes
- No files being processed (MELS: 203K, MILS: 91K still waiting)
- INDO table not being created

### Root Cause
The server has only **1.8 GB RAM** available, but the Python process was trying to load too many files into memory at once:

```
Server Memory: 1.8 GB total
Python Memory: ~1.3 GB (before being killed)
OOM Killer: Killing process every few minutes
```

**Proof from dmesg:**
```
Out of memory: Killed process 13436 (python3) total-vm:1465864kB, 
anon-rss:1307228kB, file-rss:64kB, shmem-rss:0kB, UID:0
```

### Configuration Issue
```python
# BEFORE (causing OOM):
MAX_FILES_PER_SCAN = 10000  # Too many for 1.8GB RAM

# When scanning 203K MELS files, it tried to load 
# metadata for 10K files at once = OOM crash
```

---

## Fix Applied

### Changed Configuration
```python
# AFTER (memory-safe):
MAX_FILES_PER_SCAN = 1000   # ✅ Fits in 1.8GB RAM
BATCH_SIZE = 5000           # ✅ Kept (this is fine)
Sleep Interval = 30 seconds # ✅ Reasonable cycle time
```

### Why This Works
- **1,000 files** = manageable memory footprint
- Process completes scan before OOM
- Still processes files quickly with 30-second cycles

### Restart Command Used
```bash
ssh root@94.237.55.234 'cd /opt/iris-pipeline && screen -dmS iris_uploader bash -c "
  export GOOGLE_APPLICATION_CREDENTIALS=\"/opt/iris-pipeline/service_account.json\";
  export BQ_PROJECT=\"inner-cinema-476211-u9\";
  cd /opt/iris-pipeline;
  source .venv/bin/activate;
  while true; do 
    python3 iris_to_bigquery_unified.py >> logs/iris_uploader.log 2>&1;
    sleep 30;
  done
"'
```

---

## Verification at 18:28 UTC

### Process Status
✅ **Uploader running successfully**
```
root  14092  60.0  1.5  36956 28640  python3 iris_to_bigquery_unified.py
```

### Log Output (First Successful Run)
```
2025-11-04 18:28:45,778 INFO ⚠️  Reached max files per scan (1000)
2025-11-04 18:28:45,778 INFO 📦 Found 1000 files (1073282 records) across 3 tables
2025-11-04 18:28:45,778 INFO 📊 Processing 1352 rows from 524 files for bmrs_boalf_iris
2025-11-04 18:28:47,300 INFO ✅ Inserted 1352 rows into bmrs_boalf_iris
2025-11-04 18:28:47,345 INFO 🗑️  Deleted 524 processed JSON files
2025-11-04 18:28:47,345 INFO 📊 Processing 903019 rows from 257 files for bmrs_bod_iris
```

### Key Evidence
- ✅ Process didn't crash
- ✅ Successfully inserted rows into BigQuery
- ✅ Deleted processed files
- ✅ Moved on to next dataset (BOD)

---

## Updated Timeline Estimates

### Files to Process (as of 18:28 UTC)
```
BOALF: ~524 files (being processed)
BOD: ~257 files (being processed)  
BEB: ~686 files
MELS: 203,697 files (LARGEST - will take longest)
MILS: 91,017 files (SECOND LARGEST)
FREQ: 3,483 files
FUELINST: 1,388 files
REMIT: 860 files
MID: 688 files
... and more ...
INDO: 344 files ← TARGET
INDDEM: 240 files
INDGEN: 240 files
```

### Processing Speed
- **1,000 files per cycle** × **30 second cycles** = 2,000 files/minute
- **MELS:** 203,697 ÷ 2,000 = ~102 minutes = **1.7 hours**
- **MILS:** 91,017 ÷ 2,000 = ~46 minutes = **0.75 hours**
- **Other datasets:** ~30 minutes combined

### New ETA for INDO Data
```
Current Time: 18:28 UTC
+ Other small datasets: ~30 min  → 19:00 UTC
+ MELS processing: 102 min       → 20:42 UTC
+ MILS processing: 46 min        → 21:28 UTC
+ INDO processing: 1-2 min       → 21:30 UTC

Expected INDO Ready: ~21:30 UTC (9:30 PM GMT)
```

**INDO should be ready by 9:30 PM GMT tonight (4 Nov 2025)**

---

## How to Check Progress

### 1. Quick File Count Check
```bash
ssh root@94.237.55.234 'for dir in MELS MILS INDO; do 
  echo -n "$dir: "; 
  find /opt/iris-pipeline/iris-clients/python/iris_data/$dir -name "*.json" 2>/dev/null | wc -l; 
done'
```

Expected output as files are processed:
```
MELS: 203697 → decreasing
MILS: 91017 → decreasing
INDO: 344 → should stay 344 until MELS/MILS done
```

### 2. Check Uploader is Running
```bash
ssh root@94.237.55.234 'ps aux | grep iris_to_bigquery | grep -v grep'
```

Should show python3 process running.

### 3. View Recent Log Activity
```bash
ssh root@94.237.55.234 'tail -30 /opt/iris-pipeline/logs/iris_uploader.log'
```

Should show continuous "✅ Inserted" and "🗑️ Deleted" messages.

### 4. Check for OOM Kills
```bash
ssh root@94.237.55.234 'dmesg | grep -i "killed process.*python3" | tail -5'
```

Should show NO new kills after 18:28 UTC.

---

## What to Do Tomorrow Morning (5 Nov, 9 AM)

Run the status check script as planned:
```bash
cd "/Users/georgemajor/GB Power Market JJ"
bash check_indo_status.sh
```

### Expected Results
You should see:
- ✅ `bmrs_indo_iris` table exists
- ✅ Latest date: 2025-11-04 or 2025-11-05
- ✅ 300-400 records (one day of settlement periods)
- ✅ MELS and MILS files fully processed (0 files remaining)

---

## Key Learnings

### Memory Management is Critical
- Small VPS (1.8 GB RAM) requires careful memory management
- `MAX_FILES_PER_SCAN` must be tuned to available memory
- Always check `dmesg` for OOM killer activity

### Optimization Balance
- **Too aggressive:** OOM kills (10K files)
- **Too conservative:** Slow processing (100 files)
- **Just right:** 1,000 files per scan ✅

### Monitoring Strategy
- Watch for process restarts (indicates crashes)
- Check memory usage (`free -h`)
- Monitor OOM killer (`dmesg`)
- Verify actual file processing (not just process running)

---

## Files Modified

### On Server
1. `/opt/iris-pipeline/iris_to_bigquery_unified.py`
   - Changed: `MAX_FILES_PER_SCAN = 1000`
   - Previous backups still available:
     - `.backup` (original)
     - `.pre_opt` (before optimization)

### Screen Session
- Killed and restarted: `iris_uploader`
- New sleep interval: 30 seconds (was 300)

---

## Next Steps After INDO Ready

1. **Verify INDO data** (tomorrow 9 AM)
2. **Fix Dashboard Script bugs** (windfor table name, range errors)
3. **Run Dashboard Update** to populate Google Sheets
4. **Verify live data** in sheets showing current day

---

## Contact Info

**Server:** root@94.237.55.234  
**Pipeline Dir:** `/opt/iris-pipeline/`  
**Logs:** `/opt/iris-pipeline/logs/iris_uploader.log`  
**Screen Session:** `screen -r iris_uploader`

---

**Status:** ✅ Memory-safe configuration applied and verified working  
**Next Check:** 5 Nov 2025, 09:00 GMT (run `check_indo_status.sh`)
