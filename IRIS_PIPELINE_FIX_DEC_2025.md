# IRIS Pipeline Fix - December 2025

**Date:** 11 December 2025  
**Issue:** Data showing as "stale" (Dec 8th) instead of live  
**Root Cause:** IRIS pipeline server (94.237.55.234) is unreachable

---

## 🔍 Diagnosis Summary

### What We Found

1. **IRIS Tables ARE Being Updated** ✅
   - `bmrs_fuelinst_iris`: Latest = Dec 10 (218,640 rows)
   - `bmrs_mid_iris`: Latest = Dec 10 (20 rows on Dec 10, 96 rows on Dec 9)
   - `bmrs_bod_iris`: Latest = Dec 10 (5.3M rows)
   - `bmrs_boalf_iris`: Latest = Dec 10 (615K rows)

2. **BigQuery View Was Stale** ❌ → ✅ FIXED
   - `v_btm_bess_inputs` was showing Dec 8th data (1,302 rows)
   - **Solution Applied:** Recreated the view using `v_btm_bess_inputs_unified.sql`
   - **Result:** Now shows Dec 10th data (66,395 rows)

3. **IRIS Server is Unreachable** ❌ NEEDS FIX
   - SSH connection to 94.237.55.234 times out
   - This means the IRIS pipeline stopped mid-day on Dec 10th
   - Explains why Dec 10th only has partial data (20 rows vs expected 96)

---

## ✅ Immediate Fix Applied

### 1. BigQuery View Refreshed

```bash
# Executed on local machine
cd /home/george/GB-Power-Market-JJ
python3 << 'EOF'
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')
with open('bigquery/v_btm_bess_inputs_unified.sql', 'r') as f:
    view_sql = f.read()
client.query(view_sql).result()
print('✅ View recreated')
EOF
```

**Result:**
- Before: 1,302 rows (max date: Dec 8)
- After: 66,395 rows (max date: Dec 10)

### 2. Sync Script Updated

The hourly cron job will now pull the latest Dec 10th data into your Google Sheet.

**Next scheduled run:** Every hour at :15 (e.g., 11:15, 12:15, etc.)

---

## ⚠️ Outstanding Issue: IRIS Server Down

### The Problem

The IRIS pipeline server at **94.237.55.234** is not responding:
- SSH connection times out
- IRIS data collection stopped mid-day Dec 10th
- Dec 10th has only 20 data points (instead of 96 for a full day)

### Why This Matters

- **bmrs_mid_iris** stopped updating after ~10 AM on Dec 10th
- Once the server is back online, it should backfill missing data
- Your sheet will update automatically once new data arrives in BigQuery

### How to Check IRIS Server Status

From any machine with SSH access:

```bash
# Test connectivity
ssh root@94.237.55.234 'uptime'

# If accessible, check IRIS processes
ssh root@94.237.55.234 'ps aux | grep -E "(iris|client\.py)" | grep -v grep'

# Check IRIS logs
ssh root@94.237.55.234 'tail -50 /opt/iris-pipeline/logs/iris_uploader.log'
```

### How to Restart IRIS Pipeline (if server accessible)

```bash
# Connect to server
ssh root@94.237.55.234

# Restart IRIS services
sudo systemctl restart iris-client
sudo systemctl restart iris-uploader

# Verify they're running
sudo systemctl status iris-client
sudo systemctl status iris-uploader

# Monitor logs for errors
tail -f /opt/iris-pipeline/logs/iris_uploader.log
```

---

## 📊 Current Data Status (as of Dec 11, 2025)

| Data Source | Latest Date | Status | Notes |
|-------------|-------------|--------|-------|
| **v_btm_bess_inputs** | Dec 10 | ✅ Live | 66,395 rows |
| **bmrs_mid_iris** | Dec 10 | ⚠️ Partial | Only 20 rows (stopped mid-day) |
| **bmrs_fuelinst_iris** | Dec 10 | ✅ Good | 218,640 rows |
| **bmrs_bod_iris** | Dec 10 | ✅ Good | 5.3M rows |
| **bmrs_boalf_iris** | Dec 10 | ✅ Good | 615K rows |
| **Google Sheet (BtM Daily)** | Dec 8 | 🔄 Updating | Will sync to Dec 10 at next cron run |

---

## 🔧 Automated Sync Status

### Hourly Sync Script

**Location:** `/home/george/GB-Power-Market-JJ/run_btm_sync.sh`

**Schedule:** Every hour at :15 (configured via crontab)

**What it does:**
1. Queries `v_btm_bess_inputs` for the last 5 days
2. Writes the latest date's data to "BtM Daily" sheet (columns B-K)
3. "GB Live" sheet updates automatically via formulas

**To check logs:**
```bash
tail -f /home/george/GB-Power-Market-JJ/logs/btm_sync.log
```

**To run manually:**
```bash
/home/george/GB-Power-Market-JJ/run_btm_sync.sh
```

---

## 📝 Action Items

### For You (User)

1. ✅ **BigQuery View** - FIXED (now showing Dec 10th data)
2. ✅ **Sync Script** - WORKING (will auto-update sheet hourly)
3. ⏳ **Google Sheet** - Will update to Dec 10th at next sync (within 1 hour)

### For Server Admin

1. ❌ **IRIS Server** - NEEDS ATTENTION
   - Server 94.237.55.234 is unreachable
   - IRIS pipeline needs to be restarted
   - Check with UpCloud if server is down/suspended

---

## 🎯 Expected Behavior Going Forward

Once the IRIS server is back online:

1. IRIS pipeline will resume downloading messages from Azure Service Bus
2. Missing data for Dec 10th (afternoon) and Dec 11th will be backfilled
3. `bmrs_mid_iris` will catch up to current time
4. Your hourly sync script will automatically pull the new data
5. Google Sheet will show live data within 1 hour of IRIS catching up

**No manual intervention needed once IRIS is back online.**

---

## 📚 Reference Documentation

- **IRIS Setup:** `docs/IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md`
- **Data Architecture:** `docs/UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`
- **Sync Script:** `/home/george/GB-Power-Market-JJ/sync_btm_bess_to_sheets.py`
- **BigQuery View:** `/home/george/GB-Power-Market-JJ/bigquery/v_btm_bess_inputs_unified.sql`

---

**Status:** ✅ Partial Fix Complete (BigQuery view refreshed, sync script working)  
**Next Step:** Restore IRIS server connectivity to resume live data ingestion
