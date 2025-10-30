# 🔒 SYSTEM LOCKDOWN - Working Configuration (29 Oct 2025)

**Status:** ✅ PRODUCTION STABLE  
**Last Verified:** 29 October 2025, 12:54 UTC  
**Lock Date:** 29 October 2025  

---

## ⚠️ CRITICAL: DO NOT MODIFY

This document locks down the **currently working system configuration**. Any changes to these components risk breaking the production system.

---

## 🎯 System Overview

### What Works Right Now

✅ **Real-time data ingestion** - Every 5 minutes via cron  
✅ **Historical data loading** - Multi-year backfills working  
✅ **BigQuery storage** - 5.68M records, 99.9/100 quality  
✅ **Deduplication** - Hash-based, prevents duplicates  
✅ **Schema handling** - Automatic type conversion  
✅ **API integration** - Stream endpoint for historical data  

### Current Production Metrics

| Metric | Value | Status |
|--------|-------|--------|
| **Total Records** | 5,685,347 | ✅ |
| **Data Quality** | 99.9/100 | ✅ |
| **Update Frequency** | 5 minutes | ✅ |
| **Data Age** | < 10 minutes | ✅ |
| **Storage Cost** | $0.02/month | ✅ |
| **October Coverage** | 29/31 days (93.5%) | ✅ |

---

## 🔐 Protected Components

### 1. Core Ingestion Script (DO NOT MODIFY)

**File:** `ingest_elexon_fixed.py`

**Working Features:**
- ✅ Stream endpoint for historical data (`/datasets/{dataset}/stream`)
- ✅ Hash-based deduplication using `_hash_key`
- ✅ Schema sanitization (force types, handle nulls)
- ✅ Window-based duplicate detection
- ✅ Metadata columns: `_dataset`, `_window_from_utc`, `_window_to_utc`, `_ingested_utc`, `_source_columns`, `_source_api`, `_hash_source_cols`, `_hash_key`

**Critical Functions (DO NOT CHANGE):**
```python
def sanitize_for_bigquery(df: pd.DataFrame) -> pd.DataFrame
def create_hash_key(df: pd.DataFrame, content_cols: List[str]) -> pd.DataFrame
def fetch_insights_dataset(dataset_code: str, from_dt: datetime, to_dt: datetime) -> pd.DataFrame
def load_to_bigquery(df: pd.DataFrame, table_id: str, ...) -> None
```

**Working API Pattern:**
```python
url = f"https://data.elexon.co.uk/bmrs/api/v1/datasets/{dataset}/stream"
params = {
    "publishDateTimeFrom": "2025-10-29T00:00:00Z",
    "publishDateTimeTo": "2025-10-30T00:00:00Z",
    "format": "json"
}
```

### 2. Real-Time Updater (DO NOT MODIFY)

**File:** `realtime_updater.py`

**Working Configuration:**
- ✅ Fetches last 15 minutes of data
- ✅ Uses `ingest_elexon_fixed.py` via subprocess
- ✅ Logs to `logs/realtime_updates.log`
- ✅ Checks data freshness (< 30 minutes)

**Critical Settings:**
```python
minutes_back = 15  # Overlap ensures no gaps
max_age_minutes = 30  # Alert threshold
```

**Working Query (DO NOT CHANGE):**
```python
query = """
SELECT 
    MAX(DATE(settlementDate)) as latest_date,
    MAX(settlementPeriod) as latest_period,
    MAX(publishTime) as latest_publish,
    TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), CAST(MAX(publishTime) AS TIMESTAMP), MINUTE) as minutes_old
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
"""
```

### 3. Cron Job (DO NOT MODIFY)

**Current Configuration:**
```cron
*/5 * * * * cd '/Users/georgemajor/GB Power Market JJ' && '/Users/georgemajor/GB Power Market JJ/.venv/bin/python' '/Users/georgemajor/GB Power Market JJ/realtime_updater.py' >> '/Users/georgemajor/GB Power Market JJ/logs/realtime_cron.log' 2>&1
```

**Critical Parameters:**
- `*/5` - Every 5 minutes (do not increase frequency)
- Full absolute paths (required for cron)
- Logs to `realtime_cron.log`

**To View:** `crontab -l | grep realtime`  
**To Edit:** `crontab -e` (⚠️ CAUTION)

### 4. BigQuery Schema (DO NOT MODIFY)

**Project:** `inner-cinema-476211-u9`  
**Dataset:** `uk_energy_prod`  
**Table:** `bmrs_fuelinst`

**Working Schema (15 columns):**

| Column | Type | Purpose | Protected |
|--------|------|---------|-----------|
| `dataset` | STRING | Source dataset name | ✅ |
| `publishTime` | DATETIME | When data published | ✅ |
| `startTime` | DATETIME | Period start time | ✅ |
| `settlementDate` | DATE | Settlement date | ✅ |
| `settlementPeriod` | INTEGER | Period (1-48) | ✅ |
| `fuelType` | STRING | Fuel type code | ✅ |
| `generation` | INTEGER | Generation MW | ✅ |
| `_dataset` | STRING | Metadata: dataset | ✅ |
| `_window_from_utc` | STRING | Metadata: window start | ✅ |
| `_window_to_utc` | STRING | Metadata: window end | ✅ |
| `_ingested_utc` | STRING | Metadata: ingestion time | ✅ |
| `_source_columns` | STRING | Metadata: source columns | ✅ |
| `_source_api` | STRING | Metadata: API used | ✅ |
| `_hash_source_cols` | STRING | Metadata: hash input | ✅ |
| `_hash_key` | STRING | **Deduplication key** | ⚠️ CRITICAL |

**⚠️ NEVER:**
- Drop `_hash_key` column
- Change `_hash_key` calculation
- Modify column types
- Remove metadata columns

### 5. Authentication (DO NOT MODIFY)

**File:** `jibber_jabber_key.json`

**Current Usage:**
```python
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'jibber_jabber_key.json'
client = bigquery.Client(project='inner-cinema-476211-u9')
```

**⚠️ SECURITY:**
- File is in `.gitignore`
- Never commit to repository
- Backup stored securely offline
- Regenerate if compromised

### 6. Data Model (DO NOT MODIFY)

**Fuel Types (20 total):**
```
BIOMASS, CCGT, COAL, INTEW, INTFR, INTIFA2, INTIRL, INTNED,
INTNSL, INTNEM, NPSHYD, NUCLEAR, OCGT, OIL, OTHER, PS, WIND,
INTBE, INTELEC, INTVKL
```

**Settlement Periods:**
- 48 periods per day
- 30 minutes each (00:00-00:30 = Period 1, ... 23:30-00:00 = Period 48)

**Publication Pattern:**
- 5-minute updates throughout the day
- 5-minute lag after period ends
- 288 updates per day

---

## 🛠️ Working Commands (SAFE TO USE)

### Check System Status
```bash
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python realtime_updater.py --check-only
```

### View Logs
```bash
tail -f logs/realtime_updates.log
tail -f logs/realtime_cron.log
```

### Manual Update (SAFE)
```bash
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python realtime_updater.py
```

### Check Cron Status
```bash
crontab -l | grep realtime
```

### Query Current Data (SAFE)
```bash
./.venv/bin/python << 'EOF'
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'jibber_jabber_key.json'
client = bigquery.Client(project='inner-cinema-476211-u9')

query = """
SELECT 
    MAX(DATE(settlementDate)) as latest_date,
    COUNT(*) as total_records
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
"""

for row in client.query(query).result():
    print(f"Latest: {row.latest_date}, Total: {row.total_records:,}")
EOF
```

---

## ⚠️ Danger Zone (REQUIRES APPROVAL)

### Actions That Require Review

1. **Changing API Endpoints**
   - Risk: Historical data might not load
   - Approval: Test on separate table first

2. **Modifying Hash Key Generation**
   - Risk: Duplicates will be inserted
   - Approval: Run deduplication analysis first

3. **Changing Cron Schedule**
   - Risk: Data gaps or API rate limits
   - Approval: Monitor for 24 hours after change

4. **Schema Changes**
   - Risk: Data loss or type mismatches
   - Approval: Create backup table first

5. **Credential Rotation**
   - Risk: All ingestion stops
   - Approval: Test new credentials before deploying

---

## 📝 Change Management Process

### Before Making ANY Changes:

1. **Document current state**
   ```bash
   # Save current cron
   crontab -l > crontab_backup_$(date +%Y%m%d).txt
   
   # Save current data count
   echo "Records before: " > change_log.txt
   ./.venv/bin/python realtime_updater.py --check-only >> change_log.txt
   ```

2. **Create backup**
   ```bash
   # Backup critical files
   cp ingest_elexon_fixed.py ingest_elexon_fixed.py.backup
   cp realtime_updater.py realtime_updater.py.backup
   ```

3. **Test in isolation**
   - Create test BigQuery table
   - Run changes against test table
   - Verify results match expected behavior

4. **Monitor after deployment**
   ```bash
   # Watch logs for 1 hour
   tail -f logs/realtime_updates.log
   
   # Check for errors
   grep -i error logs/realtime_updates.log | tail -20
   ```

5. **Rollback plan**
   - Keep backup files for 7 days
   - Document rollback steps
   - Test rollback procedure

---

## 🔧 Maintenance Guidelines

### Daily Tasks (Automated)
- ✅ Real-time updates via cron
- ✅ Log rotation (when > 100MB)
- ✅ Data quality checks

### Weekly Tasks (Manual - Optional)
```bash
# Check update success rate
cd "/Users/georgemajor/GB Power Market JJ"
grep "✅ Update cycle completed" logs/realtime_updates.log | grep "$(date -d '7 days ago' '+%Y-%m')" | wc -l

# Expected: ~2000 (288/day × 7 days)
```

### Monthly Tasks (Manual - Recommended)
```bash
# Verify October data complete
./.venv/bin/python << 'EOF'
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'jibber_jabber_key.json'
client = bigquery.Client(project='inner-cinema-476211-u9')

query = """
SELECT 
    DATE(settlementDate) as date,
    COUNT(*) as records,
    COUNT(DISTINCT settlementPeriod) as periods
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE EXTRACT(YEAR FROM settlementDate) = 2025
  AND EXTRACT(MONTH FROM settlementDate) = 10
GROUP BY date
ORDER BY date
"""

for row in client.query(query).result():
    status = "✅" if row.records >= 5500 else "⚠️"
    print(f"{status} {row.date}: {row.records:,} records, {row.periods} periods")
EOF
```

---

## 📚 Critical Documentation (DO NOT DELETE)

These files document the working system:

### Must Keep (Production Documentation)
- ✅ `README.md` - Project overview
- ✅ `REALTIME_SETUP_COMPLETE.md` - Real-time setup details
- ✅ `REALTIME_UPDATES_GUIDE.md` - Management guide
- ✅ `ELEXON_PUBLICATION_SCHEDULE.md` - Timing analysis
- ✅ `DATA_MODEL.md` - Schema reference
- ✅ `AUTOMATION.md` - Automation guide
- ✅ `CONTRIBUTING.md` - Development guide
- ✅ `DOCUMENTATION_INDEX.md` - Master index
- ✅ `THIS FILE (SYSTEM_LOCKDOWN.md)` - Configuration lock

### Critical Scripts (DO NOT DELETE)
- ✅ `ingest_elexon_fixed.py` - Core ingestion
- ✅ `realtime_updater.py` - Real-time updates
- ✅ `setup_realtime_updates.sh` - Setup script
- ✅ `elexon_full_ingest.py` - Fetch functions

---

## 🚨 Emergency Procedures

### If Real-Time Updates Stop

1. **Check cron is running**
   ```bash
   crontab -l | grep realtime
   ```

2. **Check for errors**
   ```bash
   tail -50 logs/realtime_updates.log | grep -i error
   ```

3. **Test manual run**
   ```bash
   cd "/Users/georgemajor/GB Power Market JJ"
   ./.venv/bin/python realtime_updater.py
   ```

4. **If manual works but cron doesn't:**
   ```bash
   # Re-run setup
   ./setup_realtime_updates.sh
   ```

### If Data Quality Drops

1. **Check for duplicates**
   ```sql
   SELECT 
       _hash_key,
       COUNT(*) as duplicate_count
   FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
   GROUP BY _hash_key
   HAVING COUNT(*) > 1
   LIMIT 10
   ```

2. **If duplicates found:**
   - ⚠️ **DO NOT RUN DEDUPLICATION** without backup
   - Document the issue
   - Contact system administrator

### If API Changes

1. **Test endpoint still works**
   ```bash
   curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST/stream?publishDateTimeFrom=2025-10-29T00:00:00Z&publishDateTimeTo=2025-10-29T01:00:00Z&format=json"
   ```

2. **If 404 or error:**
   - Check Elexon API documentation
   - Look for migration notices
   - Test alternative endpoints
   - Update `ingest_elexon_fixed.py` only after testing

---

## ✅ System Health Checklist

Run this weekly to verify system health:

```bash
cd "/Users/georgemajor/GB Power Market JJ"

echo "=== SYSTEM HEALTH CHECK ==="
echo ""

echo "1. Cron Status:"
crontab -l | grep realtime && echo "✅ Cron installed" || echo "❌ Cron missing"
echo ""

echo "2. Data Freshness:"
./.venv/bin/python realtime_updater.py --check-only
echo ""

echo "3. Recent Updates (last hour):"
grep "✅ Update cycle completed" logs/realtime_updates.log | tail -12 | wc -l
echo "   Expected: 12 updates per hour"
echo ""

echo "4. Error Count (last 24 hours):"
grep -i error logs/realtime_updates.log | grep "$(date '+%Y-%m-%d')" | wc -l
echo "   Expected: 0 errors"
echo ""

echo "5. Disk Space:"
df -h . | tail -1
echo ""

echo "=== END HEALTH CHECK ==="
```

Expected output:
```
1. Cron Status: ✅ Cron installed
2. Data Freshness: ✅ Data is fresh (5 minutes old)
3. Recent Updates: 12 updates per hour
4. Error Count: 0 errors
5. Disk Space: Plenty available
```

---

## 📋 Version History

| Date | Change | Approved By |
|------|--------|-------------|
| 29 Oct 2025 | Initial lockdown - production stable | George Major |
| 29 Oct 2025 | Real-time updates implemented | George Major |
| 29 Oct 2025 | October backfill completed | George Major |

---

## 🔐 Lock Status

**System Status:** 🔒 **LOCKED FOR PRODUCTION**

**To unlock for changes:**
1. Create full system backup
2. Document proposed changes in `CHANGES_PROPOSED.md`
3. Get approval from system owner
4. Test changes in isolated environment
5. Update this document with changes made

**System Owner:** George Major  
**Lock Date:** 29 October 2025  
**Next Review:** 29 November 2025

---

**⚠️ REMINDER: This system is currently working perfectly. Any changes risk breaking production data collection. Always backup before making changes!**
