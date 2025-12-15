# 🔍 IRIS Pipeline Diagnosis - November 11, 2025

**Time:** 21:25 UTC  
**Issue:** Dashboard showing stale data (outages, interconnectors, fuel generation)

---

## 🎯 Root Cause Found

### Primary Issue: BigQuery Uploader Crashed

**What Happened:**
- IRIS client: ✅ Running continuously since Nov 8
- BigQuery uploader: ❌ **CRASHED on Nov 10 at 08:56 UTC**
- Result: ~36 hours of data backlog (Nov 10 09:00 → Nov 11 21:15)

**Evidence:**
```bash
# Uploader logs stopped at:
2025-11-10 08:56:39,900 - Last successful upload
# Next log entry:
2025-11-11 21:17:12,216 - Restarted manually
```

### Secondary Issue: Table Name Confusion

**Dashboard queries wrong tables for real-time data:**

| Data Type | Dashboard Queries | Actual IRIS Table | Status |
|-----------|------------------|-------------------|---------|
| Fuel Generation | `bmrs_fuelinst_iris` | `bmrs_fuelinst_iris` | ✅ Correct |
| Interconnectors | `bmrs_indo_iris` | `bmrs_indo_iris` | ✅ Correct |
| Outages | `bmrs_remit_unavailability` | `bmrs_remit_unavailability` | ✅ Correct (not _iris!) |

**Key Finding:** REMIT messages go to `bmrs_remit_unavailability` (NOT `bmrs_remit_iris`)

---

## ✅ Actions Taken

### 1. Restarted IRIS Pipeline (21:16 UTC)

```bash
ssh root@94.237.55.234
cd /opt/iris-pipeline
./start_iris_pipeline.sh
```

**Result:**
- ✅ Both screen sessions running
- ✅ Client downloading messages
- ✅ Uploader processing backlog

### 2. Verified Data Flow

**IRIS Client (Downloading):**
```
✅ FUELINST messages - 21:20 UTC
✅ REMIT messages - 21:19 UTC  
✅ FREQ messages - 21:19 UTC
✅ INDO messages - continuous
✅ INDGEN messages - continuous
```

**BigQuery Uploader (Processing):**
```
Cycle 1: 50 records (bmrs_indo_iris)
Cycle 2: 31,667 records (bmrs_indgen_iris)  
Status: Processing backlog from Nov 10-11
```

### 3. Current Data Freshness in BigQuery

**As of 21:25 UTC:**

| Table | Latest Data | Rows Today | Status |
|-------|-------------|------------|--------|
| `bmrs_indo_iris` | 2025-11-11 21:00:00 | 43 | ✅ UPDATING |
| `bmrs_indgen_iris` | Catching up | TBD | 🔄 PROCESSING |
| `bmrs_fuelinst_iris` | 2025-11-10 08:55:00 | 0 | ⏳ IN QUEUE |
| `bmrs_remit_unavailability` | 2025-11-10 08:43:43 | 0 | ⏳ IN QUEUE |

---

## 📊 Why Dashboard Shows Stale Data

### Current Dashboard Query Logic

**`realtime_dashboard_updater.py` line 80:**
```python
query = f"""
SELECT fuelType, SUM(generation) as total_gen
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE DATE(settlementDate) = CURRENT_DATE()
  AND generation > 0
GROUP BY fuelType
ORDER BY total_gen DESC
"""
```

**Problem:** Queries `settlementDate` which filters for TODAY only  
**Issue:** Latest data is from Nov 10 (yesterday)  
**Result:** Query returns 0 rows → Dashboard shows "Retrieved 0 fuel types"

### fix_flags_and_outages.py Query

**Line 58:**
```python
query = f"""
SELECT DISTINCT
    assetName,
    affectedUnit, 
    unavailableCapacity,
    fuelType,
    eventStatus
FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
WHERE eventStatus = 'Active'
  AND eventStartTime <= CURRENT_TIMESTAMP()
  AND (eventEndTime IS NULL OR eventEndTime >= CURRENT_TIMESTAMP())
ORDER BY unavailableCapacity DESC
LIMIT 20
"""
```

**Problem:** Correct table, but latest data is Nov 10  
**Result:** Shows yesterday's outages (which you saw: 10 outages)

---

## 🔄 Expected Recovery Timeline

### Phase 1: Interconnectors (✅ DONE - 21:20 UTC)
- bmrs_indo_iris has fresh data (21:00 UTC)
- Dashboard should show correct interconnector flows NOW

### Phase 2: Individual Generation (🔄 IN PROGRESS)
- bmrs_indgen_iris processing 31k+ records
- ETA: ~5-10 minutes

### Phase 3: Fuel Generation (⏳ PENDING)
- bmrs_fuelinst_iris messages in queue
- ETA: ~15-30 minutes

### Phase 4: Outages (⏳ PENDING)  
- bmrs_remit_unavailability updates
- ETA: ~20-40 minutes

**Full Recovery ETA:** 21:45-22:00 UTC (20-35 minutes from now)

---

## 🛡️ Monitoring & Prevention

### Check If Uploader Is Running

```bash
ssh root@94.237.55.234 'screen -ls'

# Should show:
# iris_client (Detached)
# iris_uploader (Detached)
```

### Monitor Upload Progress

```bash
# Live logs
ssh root@94.237.55.234 'tail -f /opt/iris-pipeline/logs/iris_uploader.log'

# Check for FUELINST processing
ssh root@94.237.55.234 'grep -i fuelinst /opt/iris-pipeline/logs/iris_uploader.log | tail -5'
```

### Verify Data Freshness in BigQuery

```python
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')

query = """
SELECT 
    'bmrs_fuelinst_iris' as table_name,
    MAX(publishTime) as latest_time
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
"""
df = client.query(query).to_dataframe()
print(df)
```

### Restart If Needed

```bash
ssh root@94.237.55.234
cd /opt/iris-pipeline
./start_iris_pipeline.sh
```

---

## 📝 Dashboard Script Fixes Needed

### Issue: Query Filters by settlementDate = TODAY

**Current Code** (`realtime_dashboard_updater.py` line 80):
```python
WHERE DATE(settlementDate) = CURRENT_DATE()
```

**Problem:** If IRIS data is delayed by even 1 hour past midnight, query returns 0 rows

**Solution Option 1: Expand Time Window**
```python
WHERE DATE(settlementDate) >= CURRENT_DATE() - 1
  AND publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
```

**Solution Option 2: Use Latest Data Regardless of Date**
```python
WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
```

**Recommendation:** Option 2 (most resilient to timing issues)

### Updated Dashboard Query

```python
def update_dashboard():
    """Query IRIS tables with 2-hour lookback (handles midnight transitions)"""
    
    # Fuel Generation - Latest 2 hours
    query = f"""
    SELECT fuelType, SUM(generation) as total_gen
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
      AND generation > 0
    GROUP BY fuelType
    ORDER BY total_gen DESC
    """
    
    # Interconnectors - Latest 1 hour
    query_indo = f"""
    SELECT interconnectorId, 
           AVG(flow) as avg_flow
    FROM `{PROJECT_ID}.{DATASET}.bmrs_indo_iris`
    WHERE startTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
    GROUP BY interconnectorId
    ORDER BY interconnectorId
    """
    
    # Outages - Active now (no time window needed)
    query_outages = f"""
    SELECT assetName, affectedUnit, unavailableCapacity, fuelType
    FROM `{PROJECT_ID}.{DATASET}.bmrs_remit_unavailability`
    WHERE eventStatus = 'Active'
      AND eventStartTime <= CURRENT_TIMESTAMP()
      AND (eventEndTime IS NULL OR eventEndTime >= CURRENT_TIMESTAMP())
    ORDER BY unavailableCapacity DESC
    LIMIT 20
    """
```

---

## 🚨 Root Cause: Why Did Uploader Crash?

### Hypothesis 1: Memory/Resource Issue
- Uploader process: `python3 iris_to_bigquery_unified.py`
- Log file size: 123 MB (904,470 lines)
- Possible: Out of memory or disk space

### Hypothesis 2: BigQuery API Error
- Last successful upload: Nov 10 08:56:39
- Processing: bmrs_bod_iris (133,299 rows)
- Possible: API timeout/quota exceeded

### Hypothesis 3: Network Issue
- Server: 94.237.55.234 (UpCloud AlmaLinux)
- Possible: Temporary network disruption

### Investigation Needed

```bash
# Check system resources
ssh root@94.237.55.234 'free -h && df -h'

# Check for crash dumps
ssh root@94.237.55.234 'dmesg | grep -i kill | tail -20'

# Check system logs around crash time
ssh root@94.237.55.234 'journalctl --since "2025-11-10 08:00" --until "2025-11-10 09:00" | grep -i python'
```

---

## ✅ Immediate Actions Completed

1. ✅ Restarted IRIS pipeline (21:16 UTC)
2. ✅ Verified both client and uploader running
3. ✅ Confirmed data flow (IRIS → JSON files → BigQuery)
4. ✅ Identified table name mappings (REMIT → bmrs_remit_unavailability)
5. ✅ Documented recovery timeline
6. ✅ Provided dashboard query fixes

---

## 📋 Next Steps (Recommended)

### Immediate (Tonight)
1. ⏳ **Wait 30 minutes** for backlog to process (ETA: 22:00 UTC)
2. ✅ **Verify fresh data** in BigQuery tables
3. ✅ **Test dashboard** - should show current data

### Tomorrow (Nov 12)
1. 🔧 **Update dashboard scripts** with 2-hour lookback queries
2. 📊 **Test midnight transition** (dashboard at 23:50 and 00:10)
3. 📝 **Document query patterns** for future reference

### This Week
1. 🔍 **Investigate crash root cause** (memory/API/network)
2. 🛡️ **Add monitoring** (alert if uploader stops)
3. 🔄 **Add auto-restart** (systemd watchdog or cron health check)

---

## 🎯 Success Criteria

Dashboard will show fresh data when:
- ✅ bmrs_fuelinst_iris has data from last 2 hours
- ✅ bmrs_indo_iris has data from last 1 hour  
- ✅ bmrs_remit_unavailability has current active outages

**Check at:** 22:00 UTC (30 minutes from now)

---

## 📞 Contact & Support

**IRIS Pipeline Server:** 94.237.55.234  
**BigQuery Project:** inner-cinema-476211-u9  
**Dashboard:** https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

**This Document:** IRIS_PIPELINE_DIAGNOSIS_NOV11_2025.md

---

**Status:** 🟡 **RECOVERY IN PROGRESS**  
**ETA:** 22:00 UTC (Full data recovery)  
**Last Updated:** 2025-11-11 21:25 UTC
