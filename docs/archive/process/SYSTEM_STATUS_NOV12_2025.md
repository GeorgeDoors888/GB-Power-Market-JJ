# 🚨 System Status Report - November 12, 2025 09:35 UTC

---

## ⚠️ CURRENT STATUS: PARTIAL FUNCTIONALITY

### Quick Summary
- ✅ **IRIS Client**: Running, downloading messages
- ⚠️ **IRIS Uploader**: Running but experiencing BigQuery API errors
- ⚠️ **Dashboard Updates**: STALE (last updated Nov 11 19:55)
- ✅ **Interconnectors**: Fresh data (0.6h old)
- ❌ **Fuel Generation**: NO DATA in IRIS table
- ❌ **Individual Generation**: 35h old (upload failing)
- ❌ **Outages**: NO DATA

---

## 🔍 Detailed Analysis

### IRIS Pipeline Status

**Processes Running:**
```
✅ iris_client (screen session 52465) - ACTIVE
✅ iris_uploader (screen session 52483) - ACTIVE (but with errors)
```

**Current Issue:**
```
ERROR: Timeout of 600.0s exceeded
ERROR: SSLError - EOF occurred in violation of protocol
ERROR: Failed to insert batch into bmrs_indgen_iris
```

**What's Happening:**
- Uploader is trying to upload 45,216 rows (50 files) to `bmrs_indgen_iris`
- BigQuery API timing out after 10 minutes (600s)
- SSL connection errors
- Files kept for retry (good - data not lost)

### Data Freshness

| Table | Status | Latest Data | Rows Today | Issue |
|-------|--------|-------------|------------|-------|
| **bmrs_indo_iris** | ✅ GOOD | 0.6h ago | 19 | Working |
| **bmrs_fuelinst_iris** | ❌ NO DATA | N/A | 0 | Not uploading |
| **bmrs_indgen_iris** | ❌ OLD | 35.3h ago | 0 | Upload failing |
| **bmrs_remit_unavailability** | ❌ NO DATA | N/A | 0 | Not uploading |

### Dashboard Status

**Last Updated:** November 11, 19:55:45 (13+ hours ago!)

**Dashboard Updater Status:**
- Running on UpCloud server (cron every 5 minutes)
- Running on local Mac (cron every 5 minutes)
- BUT: Not updating because retrieving "0 fuel types"

**Why Dashboard Isn't Updating:**
```python
# Dashboard query returns 0 rows because:
WHERE DATE(settlementDate) = CURRENT_DATE()  # Looking for Nov 12 data
# But bmrs_fuelinst_iris has NO Nov 12 data!
```

---

## 🎯 Root Causes

### Issue 1: BigQuery API Timeouts/SSL Errors

**Problem:** Large batch uploads (45k rows) timing out

**Possible Causes:**
1. Network issues between UpCloud → Google Cloud
2. BigQuery API having issues
3. Batch size too large (45,216 rows at once)
4. SSL/TLS handshake problems

**Impact:** Individual generation data can't upload, backs up queue

### Issue 2: Fuel Generation Not Uploading

**Problem:** `bmrs_fuelinst_iris` has NO data today

**Possible Causes:**
1. FUELINST messages not being downloaded by IRIS client
2. FUELINST files in queue but not being processed
3. Upload failing silently (no errors shown in recent logs)

**Impact:** Dashboard can't show generation mix

### Issue 3: Dashboard Query Pattern

**Problem:** Dashboard uses `DATE(settlementDate) = CURRENT_DATE()`

**Why It Fails:**
- Looks for today's data only
- If IRIS has no today's data → returns 0 rows
- Dashboard shows "Retrieved 0 fuel types"

**Solution Already Documented:**
- Should use 2-hour lookback
- Should fall back to historical tables
- See: `IRIS_PIPELINE_SAFEGUARDS_MANDATORY.md`

---

## ✅ What's Working

1. ✅ **IRIS Client** - Downloading messages from Azure Service Bus
2. ✅ **Interconnector Data** - Fresh and updating (0.6h old)
3. ✅ **Health Checks** - Running every 5 minutes, detecting issues
4. ✅ **Auto-Restart** - If processes die, they restart automatically
5. ✅ **Screen Sessions** - Both preserved and running

---

## 🔧 Immediate Actions Needed

### Action 1: Check IRIS Data Queue

```bash
# See how many files are waiting
ssh root@94.237.55.234 'find /opt/iris-pipeline/iris_data -name "*.json" | wc -l'

# Check for FUELINST files specifically
ssh root@94.237.55.234 'find /opt/iris-pipeline/iris_data -name "FUELINST*.json" | wc -l'
```

### Action 2: Reduce Batch Size

**Current:** Processing 50 files at once (can be 45k+ rows)  
**Recommended:** Reduce to 25 files max

Edit `/opt/iris-pipeline/iris_to_bigquery_unified.py`:
```python
# Find line with MAX_FILES_PER_SCAN
MAX_FILES_PER_SCAN = 25  # Reduce from 50
```

### Action 3: Update Dashboard Query Pattern

**Critical:** Dashboard needs to use 2-hour lookback, not DATE = TODAY

Edit `realtime_dashboard_updater.py`:
```python
# OLD (line ~80):
WHERE DATE(settlementDate) = CURRENT_DATE()

# NEW:
WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
```

### Action 4: Restart Uploader (Clear SSL Error)

```bash
ssh root@94.237.55.234 'cd /opt/iris-pipeline && screen -S iris_uploader -X quit && sleep 3 && screen -dmS iris_uploader bash -c "export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/service_account.json && export BQ_PROJECT=inner-cinema-476211-u9 && cd /opt/iris-pipeline && source .venv/bin/activate && while true; do echo \"\$(date +\"%Y-%m-%d %H:%M:%S\") - Starting batch upload...\" >> logs/iris_uploader.log && python3 iris_to_bigquery_unified.py >> logs/iris_uploader.log 2>&1 && sleep 300; done"'
```

---

## 📊 Recovery Plan

### Phase 1: Fix Uploader (15 minutes)
1. Reduce batch size from 50 to 25 files
2. Restart uploader to clear SSL errors
3. Monitor logs for successful uploads
4. Verify data starts appearing in BigQuery

### Phase 2: Fix Dashboard (5 minutes)
1. Update query to use 2-hour lookback
2. Add fallback to historical tables
3. Test manually: `python3 realtime_dashboard_updater.py`
4. Verify dashboard timestamp updates

### Phase 3: Verify Recovery (30 minutes)
1. Check all IRIS tables have fresh data (<2h)
2. Check dashboard shows current data
3. Verify health checks pass
4. Monitor for any new errors

**Total ETA:** 50 minutes

---

## 🚨 Why This Happened

### The BigQuery API Timeout Issue

**What We Know:**
- Started happening Nov 12 morning
- Trying to upload 45k rows at once
- Timing out after 10 minutes
- SSL errors indicate network/connection issues

**What Changed:**
- Nothing in our code
- Possibly BigQuery API having issues
- Possibly network congestion
- Possibly rate limiting kicking in

**The Fix:**
- Reduce batch size (less stress on API)
- Add retry logic with exponential backoff
- Add connection pooling/reuse

### Why Dashboard Stopped Updating

**Root Cause:** Query pattern looking for TODAY's data only

**The Trap:**
```
1. IRIS uploader fails → No Nov 12 data in tables
2. Dashboard queries: WHERE DATE = '2025-11-12'
3. Query returns 0 rows
4. Dashboard shows "Retrieved 0 fuel types"
5. Timestamp doesn't update (skips update when no data)
```

**The Solution:**
- Use time-based lookback (last 2 hours)
- Fall back to historical tables if IRIS stale
- Always show SOMETHING (even if old data with warning)

---

## 🎯 Long-Term Fixes Needed

### 1. Implement Batch Size Auto-Tuning
```python
# Start with 50 files
# If timeout, reduce to 25
# If timeout again, reduce to 10
# Auto-adjust based on success rate
```

### 2. Add BigQuery Streaming Inserts
```python
# Instead of large batches, stream continuously
# More resilient to network issues
# Real-time data appearance
```

### 3. Dashboard Query Resilience
```python
# ALWAYS query historical + IRIS with union
# ALWAYS use time lookback, not date filtering
# ALWAYS show data age indicator to users
```

### 4. Enhanced Monitoring
```python
# Alert on:
# - Upload failures (>3 in 15 minutes)
# - Data staleness (>2 hours)
# - Dashboard not updating (>15 minutes)
# - BigQuery API errors
```

---

## 📞 Immediate Actions (Now)

**Do This First:**
```bash
# 1. Check file queue size
ssh root@94.237.55.234 'find /opt/iris-pipeline/iris_data -name "*.json" | wc -l'

# 2. Check for stuck large batches
ssh root@94.237.55.234 'tail -50 /opt/iris-pipeline/logs/iris_uploader.log | grep -E "Processing|Error|Failed"'

# 3. Restart uploader (clears SSL error state)
ssh root@94.237.55.234 'cd /opt/iris-pipeline && ./start_iris_pipeline.sh'
```

**Then Monitor:**
```bash
# Watch for successful uploads
ssh root@94.237.55.234 'tail -f /opt/iris-pipeline/logs/iris_uploader.log | grep -E "Inserted|Failed"'

# Should see:
# ✅ Inserted X rows into bmrs_indgen_iris
# ✅ Inserted Y rows into bmrs_fuelinst_iris
```

---

## 📋 Summary

| Component | Status | Action Required |
|-----------|--------|-----------------|
| IRIS Client | ✅ Working | None |
| IRIS Uploader | ⚠️ Errors | Reduce batch size + restart |
| BigQuery Data | ❌ Stale | Wait for uploader fix |
| Dashboard | ❌ Not Updating | Fix query pattern |
| Health Checks | ✅ Working | None |
| Interconnectors | ✅ Fresh | None |

**Priority:** 🔴 HIGH - Dashboard showing 13+ hour old data

**ETA to Fix:** 1 hour (if actions taken now)

---

**Next Steps:**
1. Run the immediate actions above
2. Reduce batch size in uploader config
3. Update dashboard query pattern
4. Monitor recovery for 30 minutes

**Status:** 🟡 **DEGRADED - NEEDS ATTENTION**

*Report Generated: 2025-11-12 09:35 UTC*
