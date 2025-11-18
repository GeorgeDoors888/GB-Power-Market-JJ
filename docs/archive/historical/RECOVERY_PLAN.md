# IRIS Uploader - Recovery Plan (Process Stalled)

**Time:** 19:33 UTC (7:33 PM GMT), 4 Nov 2025  
**Status:** ❌ PROCESS APPEARS TO HAVE CRASHED  
**Evidence:** No data progress for 33+ minutes

---

## 🔍 Evidence of Crash

### Timeline
- **18:28 UTC:** Uploader restarted with 1000 files/scan limit
- **18:28-19:00 UTC:** Processing successfully (179,602 rows inserted)
- **19:00 UTC:** Last verified progress
- **19:10 UTC:** No change (still 179,602 rows)
- **19:33 UTC:** Still no change - **33 minutes stalled**

### Current State
```
MELS rows: 179,602 (FROZEN since 19:00)
Server SSH: Not responding (timeouts)
Process status: Unknown (can't check)
```

### Most Likely Cause
**Another OOM (Out of Memory) Kill**

The 1.8 GB server RAM is still insufficient:
- 1000 files × 6.5 rows = 6,500 rows per batch
- Plus JSON parsing + metadata = memory overflow
- Process killed by Linux OOM killer

---

## 🔧 Recovery Steps (For Tomorrow Morning)

### Step 1: Verify Process Status
```bash
ssh root@94.237.55.234 'ps aux | grep iris_to_bigquery | grep -v grep'
```

**Expected:** No output (process dead)

### Step 2: Check for OOM Kills
```bash
ssh root@94.237.55.234 'dmesg | grep -i "killed process.*python3" | tail -10'
```

**Expected:** New kills after 18:28 UTC timestamp

### Step 3: Review Last Log Entries
```bash
ssh root@94.237.55.234 'tail -50 /opt/iris-pipeline/logs/iris_uploader.log'
```

**Look for:** Last successful insert, then silence

---

## 🛠️ Fix: Reduce Memory Usage Even More

### Option 1: Much Smaller Batch Size (RECOMMENDED)

**Current config causing OOM:**
```python
MAX_FILES_PER_SCAN = 1000  # Too much for 1.8 GB RAM
BATCH_SIZE = 5000          # Also might be too large
```

**New config (memory-safe):**
```python
MAX_FILES_PER_SCAN = 500   # Half the files
BATCH_SIZE = 2000          # Smaller batches
```

**Apply the fix:**
```bash
ssh root@94.237.55.234 "cd /opt/iris-pipeline && \
  cp iris_to_bigquery_unified.py iris_to_bigquery_unified.py.pre_500 && \
  sed -i 's/MAX_FILES_PER_SCAN = 1000/MAX_FILES_PER_SCAN = 500/' iris_to_bigquery_unified.py && \
  sed -i 's/BATCH_SIZE = 5000/BATCH_SIZE = 2000/' iris_to_bigquery_unified.py && \
  grep -E 'MAX_FILES_PER_SCAN|BATCH_SIZE' iris_to_bigquery_unified.py"
```

### Option 2: Process One Dataset at a Time

Modify script to skip MELS temporarily and process smaller datasets first:
```bash
ssh root@94.237.55.234 "cd /opt/iris-pipeline && \
  mv iris-clients/python/iris_data/MELS iris-clients/python/iris_data/MELS_SKIP && \
  echo 'MELS temporarily moved aside'"
```

Then process INDO and other small datasets, then bring MELS back.

### Option 3: Upgrade Server RAM (BEST LONG-TERM)

Upgrade UpCloud server from 1.8 GB → 4 GB RAM
- Cost: ~$5-10/month more
- Would handle all datasets easily
- No more OOM issues

---

## 🚀 Restart Process (After Applying Fix)

```bash
ssh root@94.237.55.234 'cd /opt/iris-pipeline && \
  screen -S iris_uploader -X quit 2>/dev/null; \
  screen -dmS iris_uploader bash -c "
    export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/service_account.json;
    export BQ_PROJECT=inner-cinema-476211-u9;
    source .venv/bin/activate;
    while true; do 
      python3 iris_to_bigquery_unified.py >> logs/iris_uploader.log 2>&1;
      sleep 30;
    done
  " && \
  echo "Uploader restarted with new settings"'
```

---

## 📊 Updated Timeline (With 500 File Limit)

### Processing Rate (Adjusted)
- **500 files per scan** (safer for memory)
- **30 second cycles**
- **Rate: ~1000 files/minute** (conservative)

### New Estimates
```
MELS remaining: 176,066 files ÷ 1000 = 176 minutes = 2.9 hours
MILS total: 91,017 files ÷ 1000 = 91 minutes = 1.5 hours
INDO: < 1 minute

Total from restart: ~4.5 hours
```

### If Fixed Tomorrow at 9 AM:
```
Start: 09:00 GMT (9 AM)
MELS done: 11:54 GMT (noon)
MILS done: 13:24 GMT (1:30 PM)
INDO done: 13:30 GMT (1:30 PM)
```

**INDO ready by lunch time tomorrow!**

---

## 🎯 Alternative: Skip MELS for Now

If you need INDO urgently:

### Temporarily Disable MELS
```bash
ssh root@94.237.55.234 "
  cd /opt/iris-pipeline/iris-clients/python/iris_data
  mv MELS MELS_SKIP
  mv MILS MILS_SKIP
"
```

### Process INDO and Others First
This would complete in **~1 hour** since smaller datasets will process quickly.

### Come Back to MELS Later
```bash
ssh root@94.237.55.234 "
  cd /opt/iris-pipeline/iris-clients/python/iris_data
  mv MELS_SKIP MELS
  mv MILS_SKIP MILS
"
```

---

## ✅ Tomorrow Morning Action Plan

### 1. Check Server Status (9:00 AM)
```bash
bash quick_indo_check.sh
```

### 2. SSH Should Work Now (Server Idle)
```bash
ssh root@94.237.55.234
```

### 3. Verify Process Dead
```bash
ps aux | grep iris_to_bigquery
# Should show nothing
```

### 4. Check OOM Kills
```bash
dmesg | grep -i "killed process.*python3" | tail -10
# Should show recent kills
```

### 5. Apply Fix (Option 1)
```bash
cd /opt/iris-pipeline
sed -i 's/MAX_FILES_PER_SCAN = 1000/MAX_FILES_PER_SCAN = 500/' iris_to_bigquery_unified.py
sed -i 's/BATCH_SIZE = 5000/BATCH_SIZE = 2000/' iris_to_bigquery_unified.py
```

### 6. Restart Uploader
```bash
screen -dmS iris_uploader bash -c "
  export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/service_account.json;
  export BQ_PROJECT=inner-cinema-476211-u9;
  source .venv/bin/activate;
  while true; do 
    python3 iris_to_bigquery_unified.py >> logs/iris_uploader.log 2>&1;
    sleep 30;
  done
"
```

### 7. Verify It's Running
```bash
ps aux | grep iris_to_bigquery
tail -f /opt/iris-pipeline/logs/iris_uploader.log
# Watch for "✅ Inserted" messages
```

### 8. Check Progress After 15 Minutes
```bash
bq query --use_legacy_sql=false "
SELECT COUNT(*) as row_count 
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_mels_iris\`
"
# Should be > 179,602
```

---

## 🔑 Key Lessons

### Memory Management Critical
- 1.8 GB RAM is very tight for this workload
- Each 100-file reduction helps significantly
- Need to find sweet spot: 500 files seems right

### Monitoring is Essential
- BigQuery data is truth (SSH may lie)
- Check row counts every 30 minutes during processing
- If no progress = process crashed

### Conservative Settings Win
- Slower but steady > fast but crashes
- 500 files × 30s cycles = still 1000 files/min
- Will complete, just takes longer

---

## 💡 Bottom Line

**Current Status:** Process crashed ~19:00-19:10 UTC  
**Data Safe:** 179,602 rows successfully uploaded ✅  
**Fix Required:** Reduce to 500 files + 2000 batch size  
**Tomorrow:** Apply fix at 9 AM, INDO ready by 1:30 PM  

**Your data is safe, just need to restart with better settings!**

---

## 📞 Commands Summary

**Quick progress check (anytime):**
```bash
bq query --use_legacy_sql=false "SELECT COUNT(*) as cnt FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_mels_iris\`"
```

**Full recovery (tomorrow 9 AM):**
```bash
# 1. SSH to server
ssh root@94.237.55.234

# 2. Apply memory fix
cd /opt/iris-pipeline
sed -i 's/MAX_FILES_PER_SCAN = 1000/MAX_FILES_PER_SCAN = 500/' iris_to_bigquery_unified.py
sed -i 's/BATCH_SIZE = 5000/BATCH_SIZE = 2000/' iris_to_bigquery_unified.py

# 3. Restart
screen -dmS iris_uploader bash -c 'export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/service_account.json; export BQ_PROJECT=inner-cinema-476211-u9; source .venv/bin/activate; while true; do python3 iris_to_bigquery_unified.py >> logs/iris_uploader.log 2>&1; sleep 30; done'

# 4. Verify
tail -f logs/iris_uploader.log
```

---

**Status:** Ready for recovery tomorrow ✅
