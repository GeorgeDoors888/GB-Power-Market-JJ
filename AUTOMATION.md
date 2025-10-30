# Automation Guide

**Project:** UK Power Market Data Pipeline  
**Last Updated:** 29 October 2025  
**Status:** ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Daily Automation](#daily-automation)
3. [Historical Backfills](#historical-backfills)
4. [Monitoring & Alerts](#monitoring--alerts)
5. [Maintenance Tasks](#maintenance-tasks)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

### Automation Goals

1. **Daily Updates** - Fetch yesterday's data automatically
2. **Data Quality** - Verify completeness and accuracy
3. **Error Recovery** - Retry failed loads automatically
4. **Monitoring** - Alert on failures or data gaps
5. **Cost Optimization** - Minimize API calls and storage

### Current Automation Status

| Task | Status | Frequency | Last Run |
|------|--------|-----------|----------|
| Daily FUELINST ingestion | ✅ Ready | Daily 02:00 | - |
| Data quality checks | ✅ Ready | Daily 03:00 | - |
| Dashboard updates | ⚠️ Manual | On-demand | - |
| Historical backfills | ✅ Ready | As needed | Oct 29, 2025 |

---

## 🔄 Daily Automation

### Daily Data Ingestion Script

**Purpose:** Fetch yesterday's data for all datasets  
**Schedule:** Daily at 02:00 UTC  
**Duration:** ~10-15 minutes  
**Script:** `daily_update.sh`

#### Setup

Create the daily update script:

```bash
#!/bin/bash
# daily_update.sh - Daily data ingestion automation

set -e  # Exit on error

# Configuration
PROJECT_DIR="/Users/georgemajor/GB Power Market JJ"
LOG_DIR="${PROJECT_DIR}/logs"
VENV="${PROJECT_DIR}/.venv/bin/python"

# Calculate yesterday's date
YESTERDAY=$(date -v-1d '+%Y-%m-%d')
TODAY=$(date '+%Y-%m-%d')

# Create log directory
mkdir -p "${LOG_DIR}"

# Log file with timestamp
LOG_FILE="${LOG_DIR}/daily_update_${YESTERDAY}.log"

echo "========================================" | tee -a "${LOG_FILE}"
echo "Daily Update: ${YESTERDAY}" | tee -a "${LOG_FILE}"
echo "Started: $(date)" | tee -a "${LOG_FILE}"
echo "========================================" | tee -a "${LOG_FILE}"

# Activate virtual environment
cd "${PROJECT_DIR}"

# Run ingestion for key datasets
echo "" | tee -a "${LOG_FILE}"
echo "📥 Fetching FUELINST data..." | tee -a "${LOG_FILE}"
"${VENV}" ingest_elexon_fixed.py \
    --start "${YESTERDAY}" \
    --end "${TODAY}" \
    --only FUELINST \
    2>&1 | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "📥 Fetching FREQ data..." | tee -a "${LOG_FILE}"
"${VENV}" ingest_elexon_fixed.py \
    --start "${YESTERDAY}" \
    --end "${TODAY}" \
    --only FREQ \
    2>&1 | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "📥 Fetching BOD data..." | tee -a "${LOG_FILE}"
"${VENV}" ingest_elexon_fixed.py \
    --start "${YESTERDAY}" \
    --end "${TODAY}" \
    --only BOD \
    2>&1 | tee -a "${LOG_FILE}"

# Run data quality checks
echo "" | tee -a "${LOG_FILE}"
echo "🔍 Running quality checks..." | tee -a "${LOG_FILE}"
"${VENV}" -c "
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'jibber_jabber_key.json'
client = bigquery.Client(project='inner-cinema-476211-u9')

# Check yesterday's data
query = '''
SELECT 
    COUNT(*) as records,
    COUNT(DISTINCT fuelType) as fuel_types,
    COUNT(DISTINCT settlementPeriod) as periods
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst\`
WHERE DATE(settlementDate) = '${YESTERDAY}'
'''

result = list(client.query(query).result())[0]
print(f'✅ Records: {result.records}')
print(f'✅ Fuel Types: {result.fuel_types}/20')
print(f'✅ Periods: {result.periods}/48')

if result.records < 5000:
    print('❌ WARNING: Low record count!')
    exit(1)
if result.fuel_types < 19:
    print('⚠️ WARNING: Missing fuel types!')
if result.periods < 48:
    print('⚠️ WARNING: Missing periods!')
    
print('✅ Quality checks passed')
" 2>&1 | tee -a "${LOG_FILE}"

echo "" | tee -a "${LOG_FILE}"
echo "========================================" | tee -a "${LOG_FILE}"
echo "Daily Update Complete" | tee -a "${LOG_FILE}"
echo "Finished: $(date)" | tee -a "${LOG_FILE}"
echo "========================================" | tee -a "${LOG_FILE}"

# Send notification (optional)
# echo "Daily update completed for ${YESTERDAY}" | mail -s "Energy Data Update" your@email.com
```

#### Make Executable

```bash
chmod +x daily_update.sh
```

#### Test Manually

```bash
./daily_update.sh
```

---

### Scheduling with Cron

#### Edit Crontab

```bash
crontab -e
```

#### Add Daily Job

```cron
# Daily energy data update at 2:00 AM UTC
0 2 * * * cd "/Users/georgemajor/GB Power Market JJ" && ./daily_update.sh >> logs/cron.log 2>&1

# Weekly data quality report every Monday at 3:00 AM
0 3 * * 1 cd "/Users/georgemajor/GB Power Market JJ" && ./weekly_quality_report.sh >> logs/weekly_report.log 2>&1
```

#### Verify Cron Jobs

```bash
crontab -l
```

---

### Alternative: Systemd Timer (Linux)

#### Create Service File

`/etc/systemd/system/energy-data-update.service`:

```ini
[Unit]
Description=Energy Data Daily Update
After=network.target

[Service]
Type=oneshot
User=georgemajor
WorkingDirectory=/Users/georgemajor/GB Power Market JJ
ExecStart=/Users/georgemajor/GB Power Market JJ/daily_update.sh
StandardOutput=append:/Users/georgemajor/GB Power Market JJ/logs/systemd.log
StandardError=append:/Users/georgemajor/GB Power Market JJ/logs/systemd.log
```

#### Create Timer File

`/etc/systemd/system/energy-data-update.timer`:

```ini
[Unit]
Description=Run Energy Data Update Daily
Requires=energy-data-update.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

#### Enable and Start

```bash
sudo systemctl daemon-reload
sudo systemctl enable energy-data-update.timer
sudo systemctl start energy-data-update.timer
sudo systemctl status energy-data-update.timer
```

---

## 📚 Historical Backfills

### Full Historical Load (2022-2025)

**Purpose:** Load complete historical dataset  
**Duration:** ~6-8 hours for all datasets  
**Frequency:** One-time or after major data gaps

#### Backfill Script

```bash
#!/bin/bash
# backfill_historical.sh - Complete historical data load

PROJECT_DIR="/Users/georgemajor/GB Power Market JJ"
VENV="${PROJECT_DIR}/.venv/bin/python"

cd "${PROJECT_DIR}"

echo "Starting historical backfill..."
echo "This will take several hours..."

# Load 2022
echo "📥 Loading 2022..."
"${VENV}" ingest_elexon_fixed.py \
    --start 2022-01-01 \
    --end 2022-12-31 \
    --only FUELINST

# Load 2023
echo "📥 Loading 2023..."
"${VENV}" ingest_elexon_fixed.py \
    --start 2023-01-01 \
    --end 2023-12-31 \
    --only FUELINST

# Load 2024
echo "📥 Loading 2024..."
"${VENV}" ingest_elexon_fixed.py \
    --start 2024-01-01 \
    --end 2024-12-31 \
    --only FUELINST

# Load 2025 (Jan to current)
echo "📥 Loading 2025..."
"${VENV}" ingest_elexon_fixed.py \
    --start 2025-01-01 \
    --end $(date '+%Y-%m-%d') \
    --only FUELINST

echo "✅ Historical backfill complete"
```

### Incremental Backfill (Fill Gaps)

**Purpose:** Fill specific date ranges with missing data  
**Frequency:** As needed when gaps discovered

```bash
#!/bin/bash
# backfill_date_range.sh - Fill specific date range

START_DATE="2025-04-01"
END_DATE="2025-04-30"
DATASET="FUELINST"

echo "Backfilling ${DATASET} from ${START_DATE} to ${END_DATE}..."

cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python ingest_elexon_fixed.py \
    --start "${START_DATE}" \
    --end "${END_DATE}" \
    --only "${DATASET}"

echo "✅ Backfill complete"
```

---

## 🔍 Monitoring & Alerts

### Data Quality Monitoring Script

**File:** `check_data_quality.py`

```python
#!/usr/bin/env python3
"""
Data quality monitoring script.
Run daily to check for issues.
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'jibber_jabber_key.json'
client = bigquery.Client(project='inner-cinema-476211-u9')

def check_yesterday_data():
    """Check if yesterday's data is complete."""
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    query = f"""
    SELECT 
        COUNT(*) as total_records,
        COUNT(DISTINCT fuelType) as fuel_types,
        COUNT(DISTINCT settlementPeriod) as periods,
        COUNT(CASE WHEN generation IS NULL THEN 1 END) as null_values
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
    WHERE DATE(settlementDate) = '{yesterday}'
    """
    
    result = list(client.query(query).result())[0]
    
    issues = []
    
    if result.total_records < 5000:
        issues.append(f"❌ Low record count: {result.total_records} (expected ~5,760)")
    
    if result.fuel_types < 19:
        issues.append(f"⚠️ Missing fuel types: {result.fuel_types}/20")
    
    if result.periods < 48:
        issues.append(f"⚠️ Missing periods: {result.periods}/48")
    
    if result.null_values > 0:
        issues.append(f"❌ Null values found: {result.null_values}")
    
    if issues:
        print(f"\n🚨 Data Quality Issues for {yesterday}:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print(f"✅ Data quality checks passed for {yesterday}")
        print(f"  Records: {result.total_records}")
        print(f"  Fuel Types: {result.fuel_types}/20")
        print(f"  Periods: {result.periods}/48")
        return True

def check_data_freshness():
    """Check if data is up to date."""
    query = """
    SELECT MAX(DATE(settlementDate)) as latest_date
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
    """
    
    result = list(client.query(query).result())[0]
    latest_date = result.latest_date
    yesterday = (datetime.now() - timedelta(days=1)).date()
    
    days_behind = (yesterday - latest_date).days
    
    if days_behind > 1:
        print(f"❌ Data is {days_behind} days behind!")
        print(f"  Latest: {latest_date}")
        print(f"  Expected: {yesterday}")
        return False
    else:
        print(f"✅ Data is current (latest: {latest_date})")
        return True

def check_for_duplicates():
    """Check for duplicate records."""
    query = """
    SELECT 
        _hash_key,
        COUNT(*) as count
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
    GROUP BY _hash_key
    HAVING count > 1
    LIMIT 10
    """
    
    duplicates = list(client.query(query).result())
    
    if duplicates:
        print(f"❌ Found {len(duplicates)} duplicate hash keys!")
        for dup in duplicates[:5]:
            print(f"  Hash: {dup._hash_key[:20]}... (count: {dup.count})")
        return False
    else:
        print("✅ No duplicates found")
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("📊 Data Quality Report")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print()
    
    all_passed = True
    
    print("1. Checking yesterday's data completeness...")
    if not check_yesterday_data():
        all_passed = False
    print()
    
    print("2. Checking data freshness...")
    if not check_data_freshness():
        all_passed = False
    print()
    
    print("3. Checking for duplicates...")
    if not check_for_duplicates():
        all_passed = False
    print()
    
    print("=" * 60)
    if all_passed:
        print("✅ All checks passed!")
        exit(0)
    else:
        print("❌ Some checks failed - review issues above")
        exit(1)
```

#### Make Executable

```bash
chmod +x check_data_quality.py
```

#### Schedule Daily

Add to crontab:

```cron
# Run quality checks daily at 3:00 AM (after data update)
0 3 * * * cd "/Users/georgemajor/GB Power Market JJ" && ./.venv/bin/python check_data_quality.py >> logs/quality_check.log 2>&1
```

---

### Email Alerts

**Setup:**

```bash
# Install mail utilities (macOS)
brew install mailutils

# Configure SMTP (optional)
# Edit ~/.mailrc
```

**Alert Script:** `send_alert.sh`

```bash
#!/bin/bash
# send_alert.sh - Send email alert on failure

RECIPIENT="your@email.com"
SUBJECT="Energy Data Pipeline Alert"
LOG_FILE="logs/quality_check.log"

# Check if quality check failed
if [ $1 -ne 0 ]; then
    BODY="Data quality check failed. See attached log."
    
    echo "${BODY}" | mail -s "${SUBJECT}" \
        -a "${LOG_FILE}" \
        "${RECIPIENT}"
    
    echo "Alert sent to ${RECIPIENT}"
fi
```

**Update crontab:**

```cron
0 3 * * * cd "/Users/georgemajor/GB Power Market JJ" && ./.venv/bin/python check_data_quality.py >> logs/quality_check.log 2>&1 && ./send_alert.sh $?
```

---

## 🛠️ Maintenance Tasks

### Weekly Tasks

#### 1. Review Logs

```bash
#!/bin/bash
# weekly_log_review.sh - Review past week's logs

LOG_DIR="/Users/georgemajor/GB Power Market JJ/logs"

echo "📋 Weekly Log Review"
echo "===================="
echo ""

echo "Last 7 days of daily updates:"
ls -lh "${LOG_DIR}"/daily_update_*.log | tail -7

echo ""
echo "Recent errors:"
grep -i "error\|failed\|warning" "${LOG_DIR}"/daily_update_*.log | tail -20

echo ""
echo "Data quality summary:"
grep "Records:" "${LOG_DIR}"/quality_check.log | tail -7
```

#### 2. Storage Cleanup

```bash
#!/bin/bash
# cleanup_old_logs.sh - Remove logs older than 90 days

LOG_DIR="/Users/georgemajor/GB Power Market JJ/logs"

echo "🗑️ Cleaning up old logs..."

# Remove logs older than 90 days
find "${LOG_DIR}" -name "*.log" -mtime +90 -delete

echo "✅ Cleanup complete"
```

### Monthly Tasks

#### 1. Storage Audit

```python
#!/usr/bin/env python3
"""Monthly storage audit."""

from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'jibber_jabber_key.json'
client = bigquery.Client(project='inner-cinema-476211-u9')

dataset_ref = client.dataset('uk_energy_prod')
dataset = client.get_dataset(dataset_ref)

print("📊 Storage Audit Report")
print("=" * 60)

total_bytes = 0
total_rows = 0

tables = list(client.list_tables(dataset))

for table in tables:
    table_ref = dataset.table(table.table_id)
    table_obj = client.get_table(table_ref)
    
    total_bytes += table_obj.num_bytes
    total_rows += table_obj.num_rows
    
    print(f"{table.table_id}:")
    print(f"  Rows: {table_obj.num_rows:,}")
    print(f"  Size: {table_obj.num_bytes / 1024 / 1024:.2f} MB")

print("=" * 60)
print(f"Total Storage: {total_bytes / 1024 / 1024:.2f} MB")
print(f"Total Rows: {total_rows:,}")
print(f"Estimated Cost: ${total_bytes / 1024 / 1024 / 1024 * 0.02:.4f}/month")
```

#### 2. Data Validation

```bash
#!/bin/bash
# monthly_validation.sh - Comprehensive data validation

cd "/Users/georgemajor/GB Power Market JJ"

echo "📋 Monthly Data Validation"
echo "=========================="

./.venv/bin/python -c "
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'jibber_jabber_key.json'
client = bigquery.Client(project='inner-cinema-476211-u9')

# Check for missing dates
query = '''
WITH expected_dates AS (
  SELECT date
  FROM UNNEST(GENERATE_DATE_ARRAY('2023-01-01', CURRENT_DATE())) as date
),
actual_dates AS (
  SELECT DISTINCT DATE(settlementDate) as date
  FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst\`
)
SELECT COUNT(*) as missing_days
FROM expected_dates
WHERE date NOT IN (SELECT date FROM actual_dates)
'''

result = list(client.query(query).result())[0]
print(f'Missing days: {result.missing_days}')

if result.missing_days > 0:
    print('⚠️ Found missing dates - run backfill')
else:
    print('✅ All dates present')
"
```

---

## 🐛 Troubleshooting

### Common Issues

#### Issue 1: Cron Job Not Running

**Symptoms:** No log files created, data not updating

**Diagnosis:**
```bash
# Check cron service is running
sudo systemctl status cron  # Linux
launchctl list | grep cron  # macOS

# Check cron logs
tail -f /var/log/cron.log  # Linux
tail -f /var/log/system.log | grep cron  # macOS

# Verify crontab
crontab -l
```

**Fix:**
```bash
# Restart cron
sudo systemctl restart cron  # Linux
sudo launchctl kickstart -k system/com.viserion.cron  # macOS

# Check script permissions
chmod +x daily_update.sh

# Test script manually
./daily_update.sh
```

#### Issue 2: API Rate Limiting

**Symptoms:** "429 Too Many Requests" errors

**Fix:**
```bash
# Add delays between requests
# Edit ingest_elexon_fixed.py, add:
import time
time.sleep(1)  # 1 second delay between requests
```

#### Issue 3: BigQuery Quota Exceeded

**Symptoms:** "Quota exceeded" errors

**Diagnosis:**
```bash
# Check current usage
gcloud alpha billing accounts get-iam-policy BILLING_ACCOUNT_ID
```

**Fix:**
- Request quota increase
- Optimize queries to use less data
- Use streaming inserts instead of batch loads

#### Issue 4: Missing Data

**Symptoms:** Quality checks fail, gaps in data

**Fix:**
```bash
# Identify missing dates
./.venv/bin/python -c "
# (use monthly validation query above)
"

# Run backfill for missing dates
./backfill_date_range.sh
```

---

## 📊 Performance Optimization

### Ingestion Performance

**Current:** ~5-10 seconds per day of data  
**Target:** <5 seconds per day

**Optimizations:**
1. Use 7-day windows (not full year)
2. Parallel ingestion (multiple datasets at once)
3. Batch API requests (100-5000 records per call)
4. Stream to BigQuery (50k record batches)

### Query Performance

**Tips:**
1. Always filter on `settlementDate` (partitioned)
2. Use `DATE()` function for date filtering
3. Avoid `SELECT *` - specify columns needed
4. Use clustering for frequently filtered columns

**Example:**
```sql
-- Slow (full table scan)
SELECT * FROM bmrs_fuelinst
WHERE fuelType = 'WIND'

-- Fast (partition pruning)
SELECT fuelType, generation
FROM bmrs_fuelinst
WHERE DATE(settlementDate) = '2025-10-29'
  AND fuelType = 'WIND'
```

---

## 📞 Support

### Logs Location

```
logs/
├── daily_update_YYYY-MM-DD.log    # Daily ingestion logs
├── quality_check.log               # Quality check results
├── cron.log                        # Cron job execution log
└── weekly_report.log               # Weekly reports
```

### Emergency Recovery

```bash
# Stop all running processes
pkill -f ingest_elexon_fixed

# Clear locks if stuck
rm -f /tmp/ingest_*.lock

# Restart from scratch
./daily_update.sh
```

---

**Last Updated:** 29 October 2025  
**Version:** 1.0  
**Maintained by:** George Major
