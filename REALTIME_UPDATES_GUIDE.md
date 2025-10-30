# Real-Time Data Updates - Quick Guide

**Status:** ✅ Configured for 5-minute updates  
**Last Setup:** 29 October 2025

---

## 🚀 Quick Start

### 1. Setup Real-Time Updates (One-Time)

```bash
cd "/Users/georgemajor/GB Power Market JJ"
./setup_realtime_updates.sh
```

This will:
- ✅ Create logs directory
- ✅ Test the updater script
- ✅ Offer to install cron job automatically
- ✅ Configure 5-minute updates

---

## 📊 Current Status

### What's Running

**Real-Time Updates:** Every 5 minutes
- **Cron:** `*/5 * * * *`
- **Script:** `realtime_updater.py`
- **Fetches:** Last 15 minutes of data
- **Expected:** ~120 new records every 5 minutes

### October Data Status

✅ **Complete:** Oct 1-29 (backfill completed)
- Oct 1-28: Full historical data (5,760 records/day)
- Oct 29: Real-time data (ongoing collection)
- Oct 30-31: Will collect automatically

---

## 🛠️ Management Commands

### Check Current Status
```bash
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python realtime_updater.py --check-only
```

**Output:**
```
📊 Current data status:
   Latest date: 2025-10-29
   Latest period: 25
   Data age: 3 minutes
✅ Data is fresh (3 minutes old)
```

### Manual Update (Test)
```bash
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python realtime_updater.py
```

### View Live Logs
```bash
# Real-time updates log
tail -f "/Users/georgemajor/GB Power Market JJ/logs/realtime_updates.log"

# Cron execution log
tail -f "/Users/georgemajor/GB Power Market JJ/logs/realtime_cron.log"
```

### View Cron Jobs
```bash
crontab -l
```

### Edit Cron Jobs
```bash
crontab -e
```

### Remove Cron Job
```bash
crontab -e
# Delete the line containing "realtime_updater.py"
```

---

## 📅 Update Schedule

### Every 5 Minutes (Real-Time)
```
12:00 → Fetch data from 11:45-12:00
12:05 → Fetch data from 11:50-12:05
12:10 → Fetch data from 11:55-12:10
12:15 → Fetch data from 12:00-12:15
...
```

**Why 15-minute windows?**
- Ensures overlap to catch any delayed publications
- Deduplication handled by hash keys
- More resilient to transient network issues

---

## 📊 Expected Data Flow

### Typical 5-Minute Update

**Input:**
- Time window: Last 15 minutes
- Expected records: 60-180 records
  - 1 settlement period = 120 records (20 fuel types × 6 readings)
  - 15 minutes = ~0.5 periods
  - Overlap ensures completeness

**Output:**
```
✅ Successfully loaded 120 rows to bmrs_fuelinst
```

### Daily Accumulation

**Per Day:**
- Updates: 288 (every 5 minutes × 12 per hour × 24 hours)
- Records: 5,760+ (48 periods × 120 records)
- Periods: 48 (every 30 minutes)
- Fuel types: 20

---

## 🔍 Monitoring & Alerts

### Check Data Freshness

**Healthy Status:**
```bash
./.venv/bin/python realtime_updater.py --check-only
```

**Expected:**
- Data age: < 30 minutes
- Latest period: Current or recent
- No error messages

**Unhealthy Status:**
```
⚠️ Data is 65 minutes old (expected < 30)
```

**Action:** Check logs, verify cron is running

### Monitor Logs

**Check for errors:**
```bash
grep -i error logs/realtime_updates.log | tail -20
```

**Check recent updates:**
```bash
tail -50 logs/realtime_updates.log
```

**Count successful updates today:**
```bash
grep "✅ Update cycle completed" logs/realtime_updates.log | grep "$(date '+%Y-%m-%d')" | wc -l
```

Expected: ~288 per day (12 per hour)

---

## 🚨 Troubleshooting

### Problem: No new data appearing

**Check 1: Is cron running?**
```bash
crontab -l | grep realtime_updater
```

**Check 2: Any errors in logs?**
```bash
tail -50 logs/realtime_updates.log
```

**Check 3: Test manual run**
```bash
./.venv/bin/python realtime_updater.py
```

### Problem: Cron job not executing

**Check cron logs:**
```bash
# macOS
log show --predicate 'process == "cron"' --last 1h

# Check system log
grep CRON /var/log/system.log
```

**Verify cron service:**
```bash
# Cron is part of launchd on macOS
ps aux | grep cron
```

### Problem: Script runs but data not loading

**Check BigQuery credentials:**
```bash
ls -la jibber_jabber_key.json
```

**Test connection:**
```bash
./.venv/bin/python -c "
from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'jibber_jabber_key.json'
client = bigquery.Client(project='inner-cinema-476211-u9')
print('✅ BigQuery connection works!')
"
```

---

## 📈 Performance Metrics

### Expected Metrics (Healthy System)

| Metric | Expected Value | Alert Threshold |
|--------|---------------|-----------------|
| **Data age** | < 10 minutes | > 30 minutes |
| **Updates/hour** | 12 | < 10 |
| **Records/update** | 60-180 | < 30 |
| **Update duration** | 3-5 seconds | > 30 seconds |
| **Cron execution** | 288/day | < 250/day |

### Query Performance

```sql
-- Check today's update count
SELECT 
    DATE(_ingested_utc) as date,
    COUNT(DISTINCT _ingested_utc) as unique_updates,
    COUNT(*) as total_records
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE DATE(_ingested_utc) = CURRENT_DATE()
GROUP BY date
```

---

## 🎯 Success Criteria

### Daily Health Check

Run each morning:

```bash
# 1. Check data is fresh
./.venv/bin/python realtime_updater.py --check-only

# 2. Verify yesterday is complete
./.venv/bin/python << 'EOF'
from google.cloud import bigquery
import os
from datetime import datetime, timedelta

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'jibber_jabber_key.json'
client = bigquery.Client(project='inner-cinema-476211-u9')

yesterday = (datetime.utcnow() - timedelta(days=1)).strftime('%Y-%m-%d')

query = f"""
SELECT 
    COUNT(*) as records,
    COUNT(DISTINCT settlementPeriod) as periods,
    COUNT(DISTINCT fuelType) as fuel_types
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE DATE(settlementDate) = '{yesterday}'
"""

result = list(client.query(query).result())[0]

print(f"Yesterday ({yesterday}):")
print(f"  Records: {result.records} (expected: 5,760)")
print(f"  Periods: {result.periods} (expected: 48)")
print(f"  Fuel types: {result.fuel_types} (expected: 20)")

if result.records >= 5500 and result.periods == 48:
    print("✅ Yesterday's data is complete!")
else:
    print("⚠️ Yesterday's data incomplete - may need backfill")
EOF

# 3. Check cron log for errors
grep -i error logs/realtime_cron.log | tail -10
```

### Weekly Health Check

Run each Monday:

```bash
# Count updates from last 7 days
grep "✅ Update cycle completed" logs/realtime_updates.log | grep -E "$(date -d '7 days ago' '+%Y-%m-%d')|$(date -d '6 days ago' '+%Y-%m-%d')|$(date -d '5 days ago' '+%Y-%m-%d')|$(date -d '4 days ago' '+%Y-%m-%d')|$(date -d '3 days ago' '+%Y-%m-%d')|$(date -d '2 days ago' '+%Y-%m-%d')|$(date -d '1 day ago' '+%Y-%m-%d')" | wc -l
```

Expected: ~2,000 (288 × 7 days)

---

## 📝 Configuration Details

### Cron Entry
```cron
*/5 * * * * cd '/Users/georgemajor/GB Power Market JJ' && '/Users/georgemajor/GB Power Market JJ/.venv/bin/python' '/Users/georgemajor/GB Power Market JJ/realtime_updater.py' >> '/Users/georgemajor/GB Power Market JJ/logs/realtime_cron.log' 2>&1
```

### Script Parameters

**realtime_updater.py:**
- `--minutes-back N`: Fetch last N minutes (default: 15)
- `--check-only`: Only check status, don't fetch

**Examples:**
```bash
# Fetch last 30 minutes
./.venv/bin/python realtime_updater.py --minutes-back 30

# Just check status
./.venv/bin/python realtime_updater.py --check-only
```

---

## 🔄 Alternative: Manual Daily Updates

If you prefer daily batch updates instead of 5-minute updates:

### Disable Real-Time Updates
```bash
crontab -e
# Comment out or delete the realtime_updater line
```

### Enable Daily Batch (02:00 UTC)
```bash
crontab -e
# Add this line:
0 2 * * * cd '/Users/georgemajor/GB Power Market JJ' && './.venv/bin/python' 'ingest_elexon_fixed.py' --start "$(date -d 'yesterday' '+%Y-%m-%d')" --end "$(date '+%Y-%m-%d')" --only FUELINST >> '/Users/georgemajor/GB Power Market JJ/logs/daily_update.log' 2>&1
```

---

## 📞 Support

### Documentation
- **Publication schedule:** See `ELEXON_PUBLICATION_SCHEDULE.md`
- **Data model:** See `DATA_MODEL.md`
- **Automation guide:** See `AUTOMATION.md`

### Common Issues
- **Contributing guide:** See `CONTRIBUTING.md` → Troubleshooting section
- **Quick reference:** See `QUICK_REFERENCE.md`

---

**Last Updated:** 29 October 2025  
**Setup By:** George Major  
**Status:** ✅ Active and running
