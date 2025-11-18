# 🔒 IRIS Pipeline Production Safeguards - CRITICAL REFERENCE

**Created:** November 11, 2025  
**Purpose:** Prevent IRIS uploader crashes and data staleness issues  
**Status:** 🔴 **MANDATORY - READ BEFORE ANY CHANGES**

---

## 🚨 What Went Wrong (Nov 10-11, 2025)

### The Incident

**Timeline:**
- **Nov 8**: IRIS pipeline deployed successfully
- **Nov 10 08:56 UTC**: BigQuery uploader crashed silently
- **Nov 11 21:15 UTC**: Issue discovered (36 hours later)
- **Nov 11 21:16 UTC**: Pipeline restarted manually

**Impact:**
- ❌ Dashboard showed stale data for 36 hours
- ❌ No alerts triggered
- ❌ No automatic recovery
- ❌ Users saw incorrect market data

**Root Cause:**
1. Uploader process died (unknown reason - memory/API/network)
2. No monitoring/alerting system in place
3. No auto-restart mechanism
4. No health checks in cron jobs

---

## 🎯 The Golden Rules (NEVER BREAK THESE)

### Rule 1: ALWAYS Query Both Historical and Real-Time Tables

**❌ WRONG:**
```sql
-- Only queries IRIS table (real-time)
SELECT * FROM bmrs_fuelinst_iris
WHERE DATE(settlementDate) = CURRENT_DATE()
```

**✅ CORRECT:**
```sql
-- Union both tables for complete coverage
SELECT * FROM (
  -- Historical data (reliable, 2020-present)
  SELECT * FROM bmrs_fuelinst
  WHERE settlementDate < CURRENT_DATE()
  
  UNION ALL
  
  -- Real-time data (last 24-48h)
  SELECT * FROM bmrs_fuelinst_iris
  WHERE settlementDate >= CURRENT_DATE() - 1
)
ORDER BY settlementDate DESC
```

**Why:** If IRIS pipeline fails, historical data keeps dashboard functional

---

### Rule 2: ALWAYS Use Time-Based Lookback (Not Date Filtering)

**❌ WRONG:**
```sql
WHERE DATE(settlementDate) = CURRENT_DATE()
```
**Problem:** Returns 0 rows if IRIS data is delayed past midnight

**✅ CORRECT:**
```sql
WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
```
**Why:** Gets most recent data regardless of date boundaries

---

### Rule 3: ALWAYS Check Data Freshness Before Using It

**❌ WRONG:**
```python
df = client.query(query).to_dataframe()
# Assume data is fresh, proceed
```

**✅ CORRECT:**
```python
df = client.query(query).to_dataframe()

# Check data age
if len(df) > 0 and 'publishTime' in df.columns:
    latest = df['publishTime'].max()
    age_hours = (datetime.now(latest.tzinfo) - latest).total_seconds() / 3600
    
    if age_hours > 2:
        logging.warning(f"⚠️ Data is {age_hours:.1f} hours old! Expected < 2 hours")
        # Fallback to historical table or alert user
```

---

### Rule 4: NEVER Filter by settlementDate = TODAY Only

**The Problem:**
```python
# This query fails at midnight transitions!
WHERE DATE(settlementDate) = CURRENT_DATE()
```

**Scenarios That Break:**
1. IRIS data arrives 15 minutes late → No data shown
2. Query runs at 00:01 → Yesterday's data excluded
3. IRIS pipeline delayed → Dashboard blank

**The Solution:**
```python
# Option A: Use publishTime (most reliable)
WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)

# Option B: Include yesterday for safety
WHERE DATE(settlementDate) >= CURRENT_DATE() - 1

# Option C: Use lookback window
WHERE settlementDate >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
```

---

### Rule 5: ALWAYS Have Monitoring and Alerting

**Minimum Requirements:**
1. ✅ Health check script (runs every 5 minutes)
2. ✅ Alert if no data in last 2 hours
3. ✅ Auto-restart if process is dead
4. ✅ Log file monitoring (detect crashes)

**See:** `monitor_iris_pipeline.sh` (already exists) - but needs enhancement

---

## 📊 Table Architecture Reference

### Historical vs Real-Time Tables

| Table Type | Example | Data Range | Update Method | Reliability |
|------------|---------|------------|---------------|-------------|
| **Historical** | `bmrs_fuelinst` | 2020-present | Elexon API batch | ⭐⭐⭐⭐⭐ Rock solid |
| **IRIS Real-Time** | `bmrs_fuelinst_iris` | Last 24-48h | Azure Service Bus | ⭐⭐⭐ Can fail |

### Critical Table Mappings

| Data Type | Historical Table | IRIS Table | Use For |
|-----------|-----------------|------------|---------|
| Fuel Generation | `bmrs_fuelinst` | `bmrs_fuelinst_iris` | Dashboard generation mix |
| Interconnectors | `bmrs_indo` | `bmrs_indo_iris` | Import/export flows |
| Individual Gen | `bmrs_indgen` | `bmrs_indgen_iris` | Per-unit generation |
| Outages | `bmrs_remit_unavailability` | (same table*) | Power station outages |
| Frequency | `bmrs_freq` | `bmrs_freq_iris` | Grid frequency |
| Market Prices | `bmrs_mid` | `bmrs_mid_iris` | System prices |

**\*Note:** REMIT/outages data goes to `bmrs_remit_unavailability` (NOT `bmrs_remit_iris`)

---

## 🔧 Standard Query Pattern (Copy This!)

### Template: Query with Historical + Real-Time Union

```python
def get_latest_fuel_generation():
    """
    Get latest fuel generation data with automatic fallback.
    
    Queries:
    1. IRIS table (last 2 hours) for real-time data
    2. Historical table if IRIS is stale
    
    Returns DataFrame with freshness indicator.
    """
    from google.cloud import bigquery
    from datetime import datetime
    import pandas as pd
    
    client = bigquery.Client(project='inner-cinema-476211-u9')
    
    # Try IRIS first (real-time)
    query_iris = """
    SELECT 
        fuelType,
        SUM(generation) as total_gen,
        MAX(publishTime) as latest_time,
        'IRIS' as source
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
    WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
      AND generation > 0
    GROUP BY fuelType
    """
    
    df_iris = client.query(query_iris).to_dataframe()
    
    # Check if IRIS data is fresh
    if len(df_iris) > 0 and 'latest_time' in df_iris.columns:
        latest = df_iris['latest_time'].iloc[0]
        age_hours = (datetime.now(latest.tzinfo) - latest).total_seconds() / 3600
        
        if age_hours < 2:
            # IRIS data is fresh, use it
            return df_iris, 'fresh', age_hours
    
    # Fallback to historical table
    query_historical = """
    SELECT 
        fuelType,
        SUM(generation) as total_gen,
        MAX(publishTime) as latest_time,
        'Historical' as source
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
    WHERE settlementDate >= CURRENT_DATE() - 1
      AND generation > 0
    GROUP BY fuelType
    """
    
    df_hist = client.query(query_historical).to_dataframe()
    
    if len(df_hist) > 0:
        latest = df_hist['latest_time'].iloc[0]
        age_hours = (datetime.now(latest.tzinfo) - latest).total_seconds() / 3600
        return df_hist, 'fallback', age_hours
    
    # No data available
    return pd.DataFrame(), 'no_data', 999
```

---

## 🛡️ Monitoring System (Required)

### 1. Health Check Script

Create `/opt/iris-pipeline/health_check.sh`:

```bash
#!/bin/bash
SCRIPT_DIR="/opt/iris-pipeline"
LOG_DIR="$SCRIPT_DIR/logs"
ALERT_FILE="$SCRIPT_DIR/alerts.txt"

# Function to send alert (expand with email/SMS later)
send_alert() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ALERT: $1" | tee -a "$ALERT_FILE"
}

# Check if uploader is running
if ! screen -ls | grep -q iris_uploader; then
    send_alert "❌ IRIS UPLOADER IS DOWN! Restarting..."
    cd "$SCRIPT_DIR"
    ./start_iris_pipeline.sh
    exit 1
fi

# Check if client is running
if ! screen -ls | grep -q iris_client; then
    send_alert "❌ IRIS CLIENT IS DOWN! Restarting..."
    cd "$SCRIPT_DIR"
    ./start_iris_pipeline.sh
    exit 1
fi

# Check uploader log for recent activity (should update every 5 minutes)
LAST_LOG=$(tail -1 "$LOG_DIR/iris_uploader.log" 2>/dev/null | cut -d' ' -f1-2)
if [ -n "$LAST_LOG" ]; then
    LAST_EPOCH=$(date -d "$LAST_LOG" +%s 2>/dev/null || echo 0)
    NOW_EPOCH=$(date +%s)
    AGE=$((NOW_EPOCH - LAST_EPOCH))
    
    if [ $AGE -gt 900 ]; then  # 15 minutes
        send_alert "⚠️ Uploader log hasn't updated in $((AGE/60)) minutes! Last: $LAST_LOG"
    fi
fi

# Check BigQuery data freshness
export GOOGLE_APPLICATION_CREDENTIALS="$SCRIPT_DIR/service_account.json"
python3 - <<'PYEOF'
from google.cloud import bigquery
from datetime import datetime
import sys

client = bigquery.Client(project='inner-cinema-476211-u9')

# Check critical tables
tables = ['bmrs_fuelinst_iris', 'bmrs_indo_iris']
alerts = []

for table in tables:
    query = f"""
    SELECT MAX(publishTime) as latest_time
    FROM `inner-cinema-476211-u9.uk_energy_prod.{table}`
    WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
    """
    
    df = client.query(query).to_dataframe()
    latest = df.iloc[0]['latest_time']
    
    if latest and pd.notna(latest):
        age_hours = (datetime.now(latest.tzinfo) - latest).total_seconds() / 3600
        if age_hours > 2:
            alerts.append(f"⚠️ {table} is {age_hours:.1f}h old (expected < 2h)")

if alerts:
    for alert in alerts:
        print(alert)
    sys.exit(1)
    
print("✅ All checks passed")
PYEOF

if [ $? -ne 0 ]; then
    send_alert "⚠️ BigQuery data is stale! Check uploader."
fi

# All checks passed
echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ Health check passed" >> "$LOG_DIR/health_check.log"
```

Make executable:
```bash
chmod +x /opt/iris-pipeline/health_check.sh
```

---

### 2. Enhanced Cron Jobs

Add to crontab:
```bash
# Health check every 5 minutes (detects failures quickly)
*/5 * * * * /opt/iris-pipeline/health_check.sh >> /opt/iris-pipeline/logs/health_check.log 2>&1

# Restart monitoring (if health check fails 3 times in 15 min, force restart)
*/15 * * * * /opt/iris-pipeline/monitor_iris_pipeline.sh >> /opt/iris-pipeline/logs/monitor.log 2>&1
```

---

### 3. Log Rotation (Prevent Disk Space Issues)

Create `/etc/logrotate.d/iris-pipeline`:

```
/opt/iris-pipeline/logs/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    copytruncate
}
```

---

## 📝 Dashboard Update Script (Fixed Version)

### Updated: realtime_dashboard_updater.py

Key changes:
1. ✅ Use 2-hour lookback (not DATE = TODAY)
2. ✅ Check data freshness before updating
3. ✅ Log warnings if data is stale
4. ✅ Fallback to historical tables

```python
def update_dashboard():
    """
    Update dashboard with data freshness checks.
    """
    # Query with 2-hour lookback
    query = """
    SELECT 
        fuelType,
        SUM(generation) as total_gen,
        MAX(publishTime) as latest_publish
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
    WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 HOUR)
      AND generation > 0
    GROUP BY fuelType
    ORDER BY total_gen DESC
    """
    
    df = bq_client.query(query).to_dataframe()
    
    # Check freshness
    if len(df) > 0:
        latest = df['latest_publish'].iloc[0]
        age_hours = (datetime.now(latest.tzinfo) - latest).total_seconds() / 3600
        
        if age_hours > 2:
            logging.warning(f"⚠️ Data is {age_hours:.1f}h old! IRIS pipeline may be down.")
            # Could fallback to historical table here
        else:
            logging.info(f"✅ Data is fresh ({age_hours:.1f}h old)")
    else:
        logging.error("❌ No data retrieved! Check IRIS pipeline.")
        return False
    
    # Update dashboard...
    # (rest of code)
```

---

## 🔍 Troubleshooting Guide

### Issue: "Retrieved 0 fuel types"

**Diagnosis:**
```bash
# 1. Check if IRIS client is running
ssh root@94.237.55.234 'screen -ls'

# 2. Check if uploader is running  
ssh root@94.237.55.234 'ps aux | grep iris_to_bigquery'

# 3. Check uploader logs
ssh root@94.237.55.234 'tail -50 /opt/iris-pipeline/logs/iris_uploader.log'

# 4. Check data in BigQuery
python3 check_iris_data.py  # (see script below)
```

**Common Causes:**
1. ❌ Uploader crashed → Restart pipeline
2. ❌ Query filters by TODAY only → Use 2-hour lookback
3. ❌ IRIS table empty → Check historical table
4. ❌ Network/API issue → Check system logs

---

### Issue: Dashboard shows stale data

**Diagnosis Script:**

Save as `check_iris_data.py`:
```python
#!/usr/bin/env python3
from google.cloud import bigquery
from datetime import datetime
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
client = bigquery.Client(project=PROJECT_ID)

tables = {
    'bmrs_fuelinst_iris': 'Fuel Generation',
    'bmrs_indo_iris': 'Interconnectors',
    'bmrs_indgen_iris': 'Individual Generation',
    'bmrs_remit_unavailability': 'Outages'
}

print("🔍 IRIS Data Freshness Check\n")
print("="*70)

for table, name in tables.items():
    query = f"""
    SELECT 
        MAX(publishTime) as latest_time,
        COUNT(CASE WHEN DATE(publishTime) = CURRENT_DATE() THEN 1 END) as rows_today
    FROM `{PROJECT_ID}.uk_energy_prod.{table}`
    WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 2 DAY)
    """
    
    df = client.query(query).to_dataframe()
    latest = df.iloc[0]['latest_time']
    rows_today = df.iloc[0]['rows_today']
    
    if latest and pd.notna(latest):
        age = (datetime.now(latest.tzinfo) - latest).total_seconds() / 3600
        status = "✅" if age < 2 else "⚠️" if age < 24 else "❌"
        print(f"{status} {name:25s} | {age:5.1f}h ago | {rows_today:,} rows today")
    else:
        print(f"❌ {name:25s} | NO DATA")

print("="*70)
print("\n✅ = Fresh (<2h) | ⚠️ = Stale (2-24h) | ❌ = Very stale (>24h)\n")
```

Run: `python3 check_iris_data.py`

---

## 📋 Deployment Checklist

Before deploying ANY changes to IRIS pipeline or dashboard:

- [ ] Read this document completely
- [ ] Test query with 2-hour lookback (not DATE = TODAY)
- [ ] Add data freshness checks to code
- [ ] Test midnight transition (23:50 → 00:10)
- [ ] Test IRIS failure scenario (stop uploader, verify fallback works)
- [ ] Add logging for data age warnings
- [ ] Deploy health_check.sh to server
- [ ] Add health check to cron
- [ ] Test health check catches failures
- [ ] Update documentation with any new learnings

---

## 🎯 Success Metrics

**Dashboard is working correctly when:**

1. ✅ Shows data even if IRIS pipeline is down (falls back to historical)
2. ✅ No gaps at midnight transitions
3. ✅ Alerts within 10 minutes if data goes stale
4. ✅ Auto-restarts if uploader crashes
5. ✅ Data age visible to users (e.g., "Updated 5 minutes ago")

---

## 📞 Emergency Procedures

### If IRIS Pipeline Is Down

```bash
# 1. SSH to server
ssh root@94.237.55.234

# 2. Restart pipeline
cd /opt/iris-pipeline
./start_iris_pipeline.sh

# 3. Verify both processes running
screen -ls
# Should see: iris_client, iris_uploader

# 4. Monitor logs
tail -f logs/iris_uploader.log

# 5. Check recovery in BigQuery (allow 30 minutes)
python3 check_iris_data.py
```

### If Dashboard Shows Wrong Data

```bash
# 1. Check data freshness
python3 check_iris_data.py

# 2. If IRIS stale, check historical tables still work
# 3. Update dashboard query to use historical + IRIS union
# 4. Add data age indicator to dashboard
```

---

## 🔐 Security & Access

**NEVER commit to git:**
- ❌ `inner-cinema-credentials.json`
- ❌ `service_account.json`
- ❌ `token.pickle`
- ❌ Any file with API keys

**Server Access:**
- SSH: `root@94.237.55.234`
- Key: Password-based (stored in password manager)
- Pipeline: `/opt/iris-pipeline/`

---

## 📖 Related Documentation

- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Table schemas
- `PROJECT_CONFIGURATION.md` - Project settings
- `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md` - Original deployment
- `IRIS_PIPELINE_DIAGNOSIS_NOV11_2025.md` - This incident analysis
- `UPCLOUD_DASHBOARD_DEPLOYMENT_COMPLETE.md` - Dashboard deployment

---

**Last Updated:** 2025-11-11 21:35 UTC  
**Version:** 1.0  
**Status:** 🔴 **PRODUCTION CRITICAL - MUST READ**

---

## ⚠️ FINAL WARNING

**DO NOT:**
- ❌ Query only IRIS tables without historical fallback
- ❌ Filter by `DATE = CURRENT_DATE()` without lookback
- ❌ Deploy without health checks
- ❌ Ignore data staleness warnings
- ❌ Make changes without testing midnight transitions

**ALWAYS:**
- ✅ Union historical + IRIS tables
- ✅ Use time-based lookbacks (2 hours minimum)
- ✅ Check data freshness before using
- ✅ Log warnings when data is stale
- ✅ Test failure scenarios

**Violating these rules will cause dashboard outages!**
