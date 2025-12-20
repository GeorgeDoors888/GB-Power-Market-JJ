# Complete IRIS Pipeline Diagnosis - Dec 20, 2025 00:40

## 🎯 ROOT CAUSE IDENTIFIED

### **Critical Bug: Wrong Directory Scanning**

**The Problem:**
- Script scans: `/opt/iris-pipeline/data/*.json` (flat structure)
- Files are in: `/opt/iris-pipeline/data/BOALF/*.json` (subdirectories)
- Result: Uploader says "No files" while 336+ files accumulating

**Before Fix:**
```python
json_files = list(DATA_DIR.glob('*.json'))  # Only top level
```

**After Fix:**
```python
json_files = list(DATA_DIR.glob('**/*.json'))  # Recursive scan
```

**Additional Fix:**
```python
DATA_DIR = Path('/opt/iris-pipeline/data')  # Was: /opt/iris-pipeline/iris-clients/python/iris_data
```

---

## ✅ FIXES APPLIED

### 1. Script Path Configuration
- ✅ Changed DATA_DIR from `/opt/iris-pipeline/iris-clients/python/iris_data` → `/opt/iris-pipeline/data`
- ✅ Fixed glob pattern from `*.json` → `**/*.json` (recursive)
- ✅ Deployed to `/opt/iris-pipeline/scripts/iris_to_bigquery_unified.py`

### 2. Process Management
- ✅ Killed old uploader processes (were looking in wrong place)
- ⏳ Need to restart with fixed script (commands interrupted)

### 3. Systemd Services
- ✅ Created `/etc/systemd/system/iris-client.service`
- ✅ Created `/etc/systemd/system/iris-uploader.service`
- ❌ Not yet enabled (systemctl commands failing - need investigation)

### 4. Cron Credentials
- ✅ Added `GOOGLE_APPLICATION_CREDENTIALS` to crontab
- ⏳ Testing at next :15 mark (e.g., 00:45)

---

## 📊 CURRENT STATUS

### IRIS Client
- **Status:** ✅ RUNNING (PID 4081716)
- **Connection:** ✅ Azure Service Bus connected
- **Download Rate:** ~33 files/minute
- **Recent Files:** BOALF (Dec 20 00:35-00:38), MELS, MILS, INDGEN
- **Working Directory:** `/opt/iris-pipeline/scripts`

### IRIS Uploader
- **Status:** ❌ NEEDS RESTART (old process killed, fixed script deployed)
- **Last Run:** Multiple attempts, all said "No files" (wrong path)
- **Fix Applied:** ✅ Script now scans subdirectories
- **Next Action:** Restart with: `cd /opt/iris-pipeline/scripts && export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json && python3 iris_to_bigquery_unified.py &`

### BigQuery Uploads
- **Status:** ❌ ZERO uploads today (Dec 20)
- **Last Upload:** Dec 18, 14:39 (2 days ago)
- **Reason:** Uploader couldn't find files (directory mismatch)
- **Expected After Fix:** Should immediately start processing 336+ pending files

### Files Pending
- **Count:** 336+ JSON files (as of 00:36)
- **Location:** `/opt/iris-pipeline/data/BOALF/`, `/opt/iris-pipeline/data/MELS/`, etc.
- **Growth Rate:** +33 files/minute
- **Disk Impact:** ~100KB per file = ~33MB in 10 min

---

## 🚀 NEXT STEPS (IN ORDER)

### Step 1: RESTART UPLOADER (IMMEDIATE - 2 MIN)
```bash
# Kill any old processes
pkill -f "iris_to_bigquery_unified.py"

# Start with fixed script
cd /opt/iris-pipeline/scripts
export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json
python3 iris_to_bigquery_unified.py &>> /opt/iris-pipeline/logs/iris_uploader_fixed.log &
UPLOADER_PID=$!
echo "Uploader PID: $UPLOADER_PID"

# Verify it finds files
sleep 5
tail -20 /opt/iris-pipeline/logs/iris_uploader_fixed.log
# Should see: "Found 336 files to process" (NOT "No files")
```

### Step 2: VERIFY UPLOADS (5 MIN LATER)
```bash
# Check log for successful uploads
tail -50 /opt/iris-pipeline/logs/iris_uploader_fixed.log | grep "Uploaded"

# Check BigQuery
python3 -c "
from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9')
result = client.query('''
    SELECT MAX(ingested_utc) as latest, COUNT(*) as today_count
    FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris\`
    WHERE DATE(ingested_utc) = CURRENT_DATE()
''').to_dataframe()
print(result)
"
# Should show: latest > 00:40, today_count > 0
```

### Step 3: FIX SYSTEMD (30 MIN)
```bash
# Validate service files
sudo systemd-analyze verify /etc/systemd/system/iris-client.service
sudo systemd-analyze verify /etc/systemd/system/iris-uploader.service

# If validation passes, force enable
sudo systemctl daemon-reload
sudo ln -sf /etc/systemd/system/iris-client.service /etc/systemd/system/multi-user.target.wants/
sudo ln -sf /etc/systemd/system/iris-uploader.service /etc/systemd/system/multi-user.target.wants/

# Check status
systemctl list-unit-files | grep iris
# Should show "enabled" not "bad"

# Test auto-restart (DON'T DO UNTIL VERIFIED WORKING)
# sudo systemctl start iris-client iris-uploader
# pkill -f client.py  # Should auto-restart in 30 sec
```

### Step 4: TEST CRON (AT NEXT :15)
```bash
# Wait for next quarter hour (e.g., 00:45)
# Then check if auto_ingest_realtime.py runs successfully
tail -30 /home/george/GB-Power-Market-JJ/logs/auto_ingest_cron.log

# Should see successful BigQuery connection, NOT credential errors
```

### Step 5: FIX DASHBOARD SCHEMAS (TODAY)
Edit `/home/george/GB-Power-Market-JJ/update_live_dashboard_v2.py`:
- Find BOALF query using `settlementDate`
- Change to `DATE(timeFrom) = '{date}'`
- Test: `python3 update_live_dashboard_v2.py`

---

## 📋 COMPLETE CHECKLIST

| Task | Status | Priority | ETA |
|------|--------|----------|-----|
| Fix uploader script (directory scan) | ✅ DONE | P0 | Complete |
| Deploy fixed script | ✅ DONE | P0 | Complete |
| Restart uploader process | ⏳ PENDING | P0 | 2 min |
| Verify BigQuery uploads | ⏳ PENDING | P0 | 10 min |
| Fix systemd enable | ⏳ PENDING | P1 | 30 min |
| Test cron at :15 | ⏳ PENDING | P1 | At :45 |
| Fix dashboard schemas | ⏳ PENDING | P2 | Today |
| Add monitoring | ⏳ PENDING | P2 | This week |
| Cleanup unmapped files | ⏳ PENDING | P3 | This week |

---

## 🔍 ANSWERS TO USER'S QUESTIONS

### Q: Please diagnose setup etc?

**A: Complete diagnosis completed. Found critical bug:**

**The Bug:**
- Uploader script configured for flat directory structure
- Actual deployment uses subdirectories (BOALF/, MELS/, etc.)
- Script glob pattern `*.json` only scanned top level
- Result: "No files to process" despite 336+ files present

**The Fix:**
1. ✅ Changed glob from `*.json` → `**/*.json` (recursive)
2. ✅ Fixed DATA_DIR path
3. ✅ Deployed to server
4. ⏳ Need to restart uploader (commands interrupted by Ctrl-C)

**Why It Was Failing:**
1. Dec 14: Uploader crashed on REMIT schema errors
2. Dec 18: Manually restarted but with wrong directory config
3. Dec 20 00:20: Restarted again, still wrong directory
4. Dec 20 00:36: Discovered directory mismatch bug
5. Dec 20 00:40: Fixed script, ready to restart

**Current State:**
- Client: ✅ Working (downloading files)
- Uploader: ❌ Needs restart (fixed script deployed)
- Systemd: ⚠️ Created but not enabled
- BigQuery: ❌ No uploads today (uploader issue)
- Cron: ⚠️ Credentials added, testing pending

---

## 🎯 SUCCESS CRITERIA

### Minimal (Next 10 Minutes)
- [ ] Uploader restarted with fixed script
- [ ] Log shows "Found 336 files" (NOT "No files")
- [ ] First successful BigQuery uploads
- [ ] File count starts decreasing

### Medium (Next Hour)
- [ ] All 336+ files processed and deleted
- [ ] BigQuery has today's data (ingested_utc = Dec 20)
- [ ] Systemd services enabled
- [ ] Cron tested at :15 mark

### Long-Term (This Week)
- [ ] Auto-restart working (systemd)
- [ ] Monitoring configured
- [ ] Dashboard schemas fixed
- [ ] No manual interventions needed

---

## 🚨 CRITICAL COMMANDS TO RUN NOW

```bash
# 1. Start uploader with fixed script
cd /opt/iris-pipeline/scripts
export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json
python3 iris_to_bigquery_unified.py &>> /opt/iris-pipeline/logs/uploader_$(date +%H%M).log &
echo "Uploader PID: $!"

# 2. Monitor startup (wait 5 seconds)
sleep 5
tail -30 /opt/iris-pipeline/logs/uploader_*.log | tail -20

# 3. Should see output like:
# "Found 336 files to process"
# "Processing BOALF/BOALF_202512200025_39768.json"
# "Uploaded 1 rows to bmrs_boalf_iris"

# 4. Watch file queue decrease
watch -n 10 'find /opt/iris-pipeline/data -name "*.json" | wc -l'
# Should decrease from 336 → 0 over next few minutes

# 5. Verify BigQuery uploads
# (Run after 2-3 minutes of processing)
python3 -c "
from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9')
print(client.query('SELECT MAX(ingested_utc) FROM uk_energy_prod.bmrs_boalf_iris').to_dataframe())
"
# Should show timestamp > 00:40
```

---

**Status:** 🔴 UPLOADER DOWN (fixed script ready, needs restart)
**Root Cause:** Directory scanning bug (now fixed)
**Impact:** Zero uploads for 2+ days
**Next Action:** Restart uploader with fixed script
**ETA to Resolution:** 10 minutes

---

*Diagnosis Complete: Dec 20, 2025 00:42*
*Fixed Script: /opt/iris-pipeline/scripts/iris_to_bigquery_unified.py*
*Ready for Production Restart*
