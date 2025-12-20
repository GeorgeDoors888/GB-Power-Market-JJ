# Automated Ingestion Setup Guide

**Created:** December 18, 2025
**Purpose:** Configure automated real-time data ingestion for GB Power Market platform

---

## 📋 Overview

Two-tier ingestion system:
1. **Real-time polling** (every 15 min) - API-based, <30 min lag
2. **IRIS streaming** (continuous) - WebSocket-based, <1 min lag (already running for REMIT)

---

## 🚀 Quick Setup (15-Minute Polling)

### Step 1: Test the Script

```bash
cd /home/george/GB-Power-Market-JJ
python3 auto_ingest_realtime.py
```

**Expected output:**
```
🚀 GB Power Market - Auto Real-Time Ingestion
📊 COSTS: Latest data at 2025-12-18 16:30:00
📥 COSTS: Fetched 6 records
✅ COSTS: Inserted 6 records
✅ Auto ingestion cycle complete
```

### Step 2: Setup Cron Job

```bash
crontab -e
```

Add this line:
```cron
*/15 * * * * cd /home/george/GB-Power-Market-JJ && python3 auto_ingest_realtime.py >> logs/auto_ingest_cron.log 2>&1
```

**What this does:**
- Runs every 15 minutes
- Logs to `logs/auto_ingest_cron.log`
- Fetches latest data for: COSTS, FUELINST, FREQ, MID

### Step 3: Verify Cron is Running

```bash
# Check cron service
systemctl status crond

# View cron logs
tail -f logs/auto_ingest_cron.log

# List active cron jobs
crontab -l
```

---

## 📊 Supported Datasets (Current)

| Dataset | Endpoint | Update Frequency | Lag | Table |
|---------|----------|------------------|-----|-------|
| **COSTS** | `/balancing/settlement/system-prices` | Every 30 min | ~15 min | `bmrs_costs` |
| **FUELINST** | `/generation/outturn/summary` | Every 5 min | ~5 min | `bmrs_fuelinst` |
| **FREQ** | `/system/frequency` | Every 1 min | ~1 min | `bmrs_freq` |
| **MID** | `/balancing/pricing/market-index` | Every 30 min | ~15 min | `bmrs_mid` |

---

## 🔧 Adding More Datasets

### Example: Add BOALF Real-Time Ingestion

Edit `auto_ingest_realtime.py`:

```python
PRIORITY_DATASETS = {
    # ... existing datasets ...
    'BOALF': {
        'endpoint': '/datasets/BOALF',
        'table': 'bmrs_boalf',
        'window': timedelta(hours=1),
        'param_format': 'from_to',
        'transform_func': transform_boalf_record,  # Custom transformer
    },
}

def transform_boalf_record(record):
    """Transform BOALF record with all 25 fields"""
    ingested_utc = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')

    def convert_datetime(dt_str):
        if dt_str:
            return dt_str.replace('T', ' ').replace('Z', '').split('.')[0]
        return None

    time_from = record.get('timeFrom', '')
    time_to = record.get('timeTo', '')

    return {
        # Core fields (17)
        'dataset': record.get('dataset', 'BOALF'),
        'settlementDate': convert_datetime(record.get('settlementDate')),
        'settlementPeriodFrom': record.get('settlementPeriodFrom'),
        'settlementPeriodTo': record.get('settlementPeriodTo'),
        'timeFrom': time_from,
        'timeTo': time_to,
        'levelFrom': record.get('levelFrom'),
        'levelTo': record.get('levelTo'),
        'acceptanceNumber': record.get('acceptanceNumber'),
        'acceptanceTime': convert_datetime(record.get('acceptanceTime')),
        'deemedBoFlag': record.get('deemedBoFlag', False),
        'soFlag': record.get('soFlag', False),
        'amendmentFlag': record.get('amendmentFlag'),
        'storFlag': record.get('storFlag', False),
        'rrFlag': record.get('rrFlag', False),
        'nationalGridBmUnit': record.get('nationalGridBmUnit'),
        'bmUnit': record.get('bmUnit'),

        # Metadata fields (8)
        '_dataset': 'BOALF',
        '_window_from_utc': time_from,
        '_window_to_utc': time_to,
        '_ingested_utc': ingested_utc,
        '_source_columns': None,
        '_source_api': 'AUTO_REALTIME',
        '_hash_source_cols': None,
        '_hash_key': None,
    }
```

---

## 🌊 IRIS Streaming Integration (Advanced)

**Current Status:** IRIS pipeline running on AlmaLinux server for REMIT only

### Expand IRIS to More Datasets

1. **Check IRIS availability:**
   ```bash
   ssh root@94.237.55.234
   cd /opt/iris-pipeline
   cat iris_streams_available.txt
   ```

2. **Add stream to client:**
   Edit `/opt/iris-pipeline/client.py`:
   ```python
   STREAMS_TO_MONITOR = [
       'REMIT',      # Already running
       'BOALF',      # Add if available
       'BOD',        # Add if available
       'FREQ',       # Add if available
   ]
   ```

3. **Restart IRIS services:**
   ```bash
   systemctl restart iris-client
   systemctl restart iris-uploader
   ```

### Expected Performance

- **Lag:** <60 seconds from publication
- **Volume:** Real-time WebSocket stream
- **Tables:** `bmrs_*_iris` (separate from historical)

---

## 📈 Monitoring & Alerts

### Check Ingestion Health

```bash
# Last 24 hours of ingestion
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')

for table in ['bmrs_costs', 'bmrs_fuelinst', 'bmrs_freq', 'bmrs_mid']:
    query = f'''
    SELECT
        MAX(CAST(settlementDate AS DATETIME)) as latest,
        COUNT(*) as last_24h_count
    FROM \`inner-cinema-476211-u9.uk_energy_prod.{table}\`
    WHERE CAST(settlementDate AS DATETIME) >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 24 HOUR)
    '''
    result = client.query(query).to_dataframe()
    print(f'{table}: Latest={result.latest[0]}, 24h count={result.last_24h_count[0]}')
"
```

### Expected Counts (24h)

- COSTS: ~48 records (every 30 min, 2/hour × 24h)
- FUELINST: ~288 records (every 5 min, 12/hour × 24h)
- FREQ: ~1440 records (every 1 min, 60/hour × 24h)
- MID: ~48 records (every 30 min, 2/hour × 24h)

### Alert if Stale Data

```bash
# Add to cron (check every hour)
0 * * * * python3 /home/george/GB-Power-Market-JJ/check_ingestion_health.py
```

Create `check_ingestion_health.py`:
```python
#!/usr/bin/env python3
from google.cloud import bigquery
from datetime import datetime, timedelta

client = bigquery.Client(project='inner-cinema-476211-u9')

ALERT_THRESHOLD = timedelta(hours=2)  # Alert if >2h stale

for table in ['bmrs_costs', 'bmrs_fuelinst', 'bmrs_freq']:
    query = f"SELECT MAX(CAST(settlementDate AS DATETIME)) as latest FROM `inner-cinema-476211-u9.uk_energy_prod.{table}`"
    result = client.query(query).to_dataframe()
    latest = result.latest[0]

    if latest:
        age = datetime.now() - latest.to_pydatetime()
        if age > ALERT_THRESHOLD:
            print(f"🚨 ALERT: {table} is {age} old (threshold: {ALERT_THRESHOLD})")
        else:
            print(f"✅ {table}: {age} old (healthy)")
    else:
        print(f"❌ {table}: NO DATA")
```

---

## 🔍 Troubleshooting

### Issue: Cron Job Not Running

**Check 1:** Is cron service running?
```bash
systemctl status crond
```

**Check 2:** View cron logs
```bash
grep CRON /var/log/cron | tail -20
```

**Check 3:** Test script manually
```bash
cd /home/george/GB-Power-Market-JJ
python3 auto_ingest_realtime.py
```

### Issue: "No new records (up to date)"

**Cause:** Already fetched latest data
**Fix:** Wait for next publishing cycle (5-30 min depending on dataset)

### Issue: BigQuery Insert Errors

**Check schema mismatch:**
```python
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')
table = client.get_table('inner-cinema-476211-u9.uk_energy_prod.bmrs_costs')
for field in table.schema:
    print(f'{field.name}: {field.field_type}')
```

---

## 📚 References

- **Elexon API Docs:** https://data.elexon.co.uk/bmrs/api/v1/swagger/index.html
- **IRIS Deployment:** `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md`
- **Project Config:** `PROJECT_CONFIGURATION.md`
- **Data Architecture:** `STOP_DATA_ARCHITECTURE_REFERENCE.md`

---

**Last Updated:** December 18, 2025
**Status:** ✅ Real-time polling ready, IRIS expansion pending
**Next:** Add BOALF/BOD to real-time polling, expand IRIS streams
