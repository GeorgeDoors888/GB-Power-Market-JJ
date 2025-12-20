# FULL DIAGNOSTIC REPORT - December 19, 2025

## 🚨 CRITICAL FAILURES IDENTIFIED

### Problem 1: AUTO_INGEST_REALTIME.PY - FAILING EVERY 15 MINUTES ❌

**Status**: **COMPLETELY BROKEN** - Runs every 15 min via cron, ZERO successful executions

**Root Cause**: Missing Google Cloud credentials

**Error**:
```
google.auth.exceptions.DefaultCredentialsError: Your default credentials 
were not found. To set up Application Default Credentials
```

**Evidence**: Log shows errors at 22:00, 22:15, 22:30 (every 15 minutes)

**Impact**:
- ❌ COSTS (system prices): Not updating via API
- ❌ FUELINST (fuel generation): Not updating via API
- ❌ FREQ (frequency): Not updating via API
- ❌ MID (market index): Not updating via API

**Fix Required**:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json"
echo 'export GOOGLE_APPLICATION_CREDENTIALS="/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json"' >> ~/.bashrc
```

---

### Problem 2: IRIS TABLES - SCHEMA MISMATCHES ❌

**Status**: Cannot query ANY IRIS table - wrong column names in all queries

**Tables Affected**: ALL 7 IRIS tables

**Errors**:
1. `bmrs_fuelinst_iris`: No column `timeFrom` (has `startTime`)
2. `bmrs_mid_iris`: No column `timeFrom` (has `settlementDate`)
3. `bmrs_freq_iris`: No column `settlementDate` (has `measurementTime`)
4. `bmrs_boalf_iris`: No column `startTime` (has `timeFrom`)
5. `bmrs_bod_iris`: No column `startTime` (has `timeFrom`)
6. `bmrs_costs_iris`: **TABLE DOESN'T EXIST** (not configured in IRIS)
7. `bmrs_remit_iris`: No column `settlementDate` (has event times)

**Why This Matters**:
- ❌ Dashboard queries fail (trying to UNION historical + IRIS)
- ❌ Cannot determine data freshness
- ❌ Dec 18 IRIS data exists but **cannot be accessed**

---

### Problem 3: IRIS PIPELINE STATUS - UNKNOWN ⚠️

**Server**: 94.237.55.234 (AlmaLinux)

**Status**: UNKNOWN - Cannot SSH to verify

**Expected Behavior**:
- Downloads IRIS messages from Azure Service Bus every 2-5 minutes
- Uploads to BigQuery tables (`bmrs_*_iris`)
- Auto-deletes processed files

**Likely Issues**:
1. IRIS client may have stopped (TLS cert error history)
2. Uploader may be failing on schema mismatches
3. Azure queue may have accumulated backlog
4. Systemd services may not be running

**Files to Check**:
- `/opt/iris-pipeline/logs/iris_client.log`
- `/opt/iris-pipeline/logs/iris_uploader.log`
- `/opt/iris-pipeline/data/` (check for file accumulation)

---

### Problem 4: DATA ARCHITECTURE CONFUSION ⚠️

**Issue**: Scripts assume IRIS tables have same schema as historical tables

**Reality**: IRIS tables have DIFFERENT schemas per table type:

| Table | Historical Timestamp | IRIS Timestamp | 
|-------|---------------------|----------------|
| FUELINST | `startTime` | `startTime` ✅ |
| MID | `settlementDate` | `settlementDate` ✅ |
| FREQ | `settlementDate` ❌ | `measurementTime` ✅ |
| BOALF | `settlementDate` | `timeFrom` |
| BOD | `settlementDate` | `timeFrom` |
| REMIT | N/A | `eventStart`/`eventEnd` |

**Impact**:
- ❌ UNION queries fail (column name mismatches)
- ❌ Cannot merge historical + IRIS data
- ❌ Dashboard shows Dec 13 instead of Dec 18

---

## 📊 ACTUAL DATA STATUS (What Data Exists)

### IRIS Tables (Dec 18 Data Confirmed):
```
✅ bmrs_fuelinst_iris: 6,086 records (Dec 18, 00:00-15:57)
✅ bmrs_mid_iris: Has Dec 18 data (schema: settlementDate + settlementPeriod)
✅ bmrs_boalf_iris: 66,292 records through Dec 18
✅ bmrs_freq_iris: Has Dec 18 data (schema: measurementTime, NOT settlementDate)
✅ bmrs_remit_iris: Has recent outage data
❌ bmrs_costs_iris: TABLE DOES NOT EXIST (IRIS doesn't stream system prices)
```

### Historical Tables:
```
⚠️  bmrs_boalf_complete: Stops at Dec 13 (price derivation lag)
⚠️  bmrs_fuelinst: Unknown freshness
⚠️  bmrs_mid: Unknown freshness  
⚠️  bmrs_freq: Manual backfill only (Dec 15-17)
```

---

## 🔧 WHY SYSTEMS ARE FAILING

### Cron Job Failures (Every 15 Minutes):

**auto_ingest_realtime.py**:
```bash
# Scheduled: */15 * * * * (every 15 min)
# Status: FAILING
# Reason: No credentials in cron environment
# Impact: API polling completely broken
```

**Other Cron Jobs** (every 30 min, every 5 min):
- May also be failing due to credential issues
- Need to check logs for ALL cron jobs

### IRIS Pipeline (AlmaLinux Server):

**Expected**: Continuous streaming, 2-5 min updates

**Reality**: UNKNOWN - need to SSH and check:
```bash
ssh root@94.237.55.234
systemctl status iris-client
systemctl status iris-uploader
tail -f /opt/iris-pipeline/logs/iris_uploader.log
```

### Query Failures:

**update_live_dashboard_v2.py**:
- Tries to UNION `bmrs_boalf_complete` + `bmrs_boalf_iris`
- ❌ FAILS: Uses `settlementDate` for both (IRIS has `timeFrom`)
- Result: Falls back to historical only (Dec 13)

**Dashboard auto-refresh**:
- Scheduled every 5 minutes via `bg_live_cron.sh`
- ❌ Likely failing on IRIS queries
- Result: Dashboard shows stale data

---

## 🛠️ FIX PRIORITY (Ordered by Impact)

### IMMEDIATE (Fix Today):

**1. Fix Cron Environment Credentials** ⭐⭐⭐
```bash
# Add to crontab header
GOOGLE_APPLICATION_CREDENTIALS=/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json

# Edit crontab
crontab -e
# Add line at top before all jobs:
GOOGLE_APPLICATION_CREDENTIALS=/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json
```

**2. Fix IRIS Schema in Queries** ⭐⭐⭐
- Update `get_bm_kpi_data()` to use correct IRIS column names:
  - BOALF IRIS: `timeFrom` (not `settlementDate`)
  - MID IRIS: `settlementDate` ✅ (already correct)
  - FREQ: Cannot use IRIS (wrong schema completely)

**3. Check IRIS Pipeline Status** ⭐⭐
```bash
ssh root@94.237.55.234 'systemctl status iris-client iris-uploader'
ssh root@94.237.55.234 'tail -100 /opt/iris-pipeline/logs/iris_uploader.log'
ssh root@94.237.55.234 'ls -la /opt/iris-pipeline/data/ | wc -l'  # Check backlog
```

### WITHIN 24 HOURS:

**4. Document Correct IRIS Schemas**
- Create IRIS_SCHEMA_REFERENCE.md
- Map all column names per table
- Update all scripts to use correct names

**5. Fix All Dashboard Queries**
- `update_live_dashboard_v2.py`
- `realtime_dashboard_updater.py`
- Any other scripts doing UNION queries

**6. Test Auto-Ingestion After Credential Fix**
```bash
# Run manually to verify
cd /home/george/GB-Power-Market-JJ
python3 auto_ingest_realtime.py

# Check logs
tail -f logs/auto_ingest_cron.log
```

### WITHIN 1 WEEK:

**7. Create Unified Views**
- BigQuery views that handle schema differences
- UNION historical + IRIS with correct column mapping
- Query views instead of raw tables

**8. Add Monitoring**
- Alert if cron jobs fail
- Alert if IRIS data >30 min old
- Alert if any table stops updating

---

## 📝 ACCURATE ARCHITECTURE

### Data Flow (How It SHOULD Work):

```
ELEXON IRIS (Azure Service Bus)
    ↓ every 2-5 min
AlmaLinux Server (94.237.55.234)
    ├→ iris-client (download messages)
    └→ iris-uploader (upload to BigQuery)
         ↓
    BigQuery IRIS tables (bmrs_*_iris)
         - bmrs_fuelinst_iris (startTime)
         - bmrs_mid_iris (settlementDate)
         - bmrs_freq_iris (measurementTime)
         - bmrs_boalf_iris (timeFrom)
         - bmrs_bod_iris (timeFrom)
         - bmrs_remit_iris (eventStart/End)

ELEXON REST API (data.elexon.co.uk)
    ↓ every 15 min (cron)
auto_ingest_realtime.py
    ↓
BigQuery Historical tables (bmrs_*)
    - bmrs_costs (API only, NO IRIS)
    - bmrs_fuelinst (startTime)
    - bmrs_mid (settlementDate)
    - bmrs_freq (measurementTime)
    - bmrs_boalf_complete (derived prices, 3-6 day lag)
```

### Why We Have Two Pipelines:

**IRIS Pipeline** (Real-time, <5 min lag):
- ✅ Frequency data
- ✅ Fuel generation
- ✅ Market prices
- ✅ BM acceptances (volume only, no prices)
- ✅ Bid-offer data
- ✅ REMIT outages
- ❌ System prices (not available via IRIS)

**API Pipeline** (15 min polling, ~30 min lag):
- ✅ System prices (COSTS)
- ✅ Backfill gaps in IRIS data
- ✅ Derived BOALF prices (separate process, 3-6 day lag)

---

## 🎯 WHY "TODAY'S DATA" IS MISSING

### The Truth:

**Dec 18 Data EXISTS** ✅ (in IRIS tables)
**Dec 18 Data INACCESSIBLE** ❌ (wrong column names in queries)

### What You're Seeing:

- Dashboard: "Dec 13" (last successful historical query)
- Reality: Dec 18 data sitting in `bmrs_boalf_iris`, `bmrs_mid_iris`, etc.
- Problem: Scripts use `settlementDate` for IRIS BOALF (should be `timeFrom`)

### Quick Test:

```sql
-- This WORKS:
SELECT COUNT(*), DATE(timeFrom) as date
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
WHERE DATE(timeFrom) = '2025-12-18'
GROUP BY date;

-- This FAILS (what scripts are using):
SELECT COUNT(*), DATE(settlementDate) as date  -- ❌ No such column!
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
```

---

## 💡 SUMMARY

**Root Causes**:
1. ❌ Cron environment missing credentials → API polling dead
2. ❌ Schema mismatches in UNION queries → IRIS data inaccessible
3. ⚠️  IRIS pipeline status unknown → need to verify AlmaLinux server

**Data Reality**:
- ✅ Dec 18 data EXISTS in IRIS tables
- ❌ Dec 18 data CANNOT BE QUERIED (wrong column names)
- ⚠️  Dec 19 data unknown (need to check IRIS pipeline)

**Fix Timeline**:
- Immediate: Fix cron credentials (5 min)
- Today: Fix IRIS schema in queries (30 min)
- Today: Verify IRIS pipeline running (15 min)
- Tomorrow: Test and monitor (ongoing)

---

**Generated**: December 19, 2025 23:10 UTC
