# Automated Daily Data Downloads - P114 & NESO

**Created**: 28 December 2025
**Status**: ✅ Production Ready
**Location**: Dell AlmaLinux Server (94.237.55.234)

---

## Overview

Automated daily ingestion for:
1. **P114 Settlement Data** (Elexon) - 342M+ records, all settlement runs
2. **NESO Constraint Costs** - 5 datasets, constraint analysis data

Both systems run automatically via cron jobs, no manual downloads needed.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DAILY AUTOMATION                         │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │  Cron Jobs   │
                    │  (AlmaLinux) │
                    └──────┬───────┘
                           │
            ┌──────────────┴──────────────┐
            │                             │
            ▼                             ▼
   ┌────────────────┐           ┌────────────────┐
   │ P114 Downloader│           │ NESO Downloader│
   │   (2am daily)  │           │   (3am daily)  │
   └────────┬───────┘           └────────┬───────┘
            │                             │
            ▼                             ▼
   ┌────────────────┐           ┌────────────────┐
   │ Elexon Portal  │           │  NESO API      │
   │ (II/SF/R1/R3)  │           │ (5 datasets)   │
   └────────┬───────┘           └────────┬───────┘
            │                             │
            └──────────────┬──────────────┘
                           ▼
                  ┌─────────────────┐
                  │    BigQuery     │
                  │ uk_energy_prod  │
                  └─────────────────┘
```

---

## 1. P114 Settlement Data (Elexon)

### What It Does
- Downloads **yesterday + today + tomorrow** settlement data (3-day window)
- Tries multiple settlement runs: **II** (T+1), **SF** (T+2), **R1** (T+5)
- Catches delayed publications automatically
- Appends to `elexon_p114_s0142_bpi` table (342M+ records)

### Script: `auto_download_p114_daily.py`

**Schedule**: Daily at **2:00 AM** (after Elexon publishes)

**Features**:
- Automatic retry for all settlement runs (II/SF/R1)
- 3-day rolling window (catches lag)
- Timeout protection (1 hour max)
- Comprehensive logging

**Manual Test**:
```bash
python3 /home/george/GB-Power-Market-JJ/auto_download_p114_daily.py
```

**Expected Output**:
```
================================================================================
🔄 P114 DAILY AUTO-INGESTION
================================================================================
📅 Date Range: 2025-12-27 to 2025-12-29

📊 Attempting II run (Initial Settlement)...
✅ Success: Loaded 144 records (2025-12-27 to 2025-12-29 II)

📊 Attempting SF run (Settlement Final)...
✅ Success: Loaded 96 records (2025-12-27 to 2025-12-28 SF)

📊 Attempting R1 run (Reconciliation 1)...
✅ Success: Loaded 48 records (2025-12-22 to 2025-12-23 R1)

================================================================================
📈 SUMMARY
================================================================================
II (Initial):        ✅ Success
SF (Final):          ✅ Success
R1 (Reconciliation): ✅ Success

✅ At least one settlement run succeeded
```

**Log Location**: `/home/george/GB-Power-Market-JJ/logs/p114_daily.log`

---

## 2. NESO Constraint Cost Data

### What It Does
- Downloads **5 key NESO datasets** via official API
- Automated discovery of latest resources
- Loads CSV data directly to BigQuery
- No manual portal navigation needed

### Script: `auto_download_neso_daily.py`

**Schedule**: Daily at **3:00 AM** (after NESO publishes previous day)

**Datasets Automated**:

| Dataset | BigQuery Table | Description |
|---------|---------------|-------------|
| **Constraint Breakdown** | `neso_constraint_breakdown` | Monthly Emergency Instructions costs |
| **MBSS** | `neso_mbss` | Daily Mandatory Balancing Services costs |
| **24-Month Forecast** | `neso_constraint_forecast` | Constraint cost forecast |
| **Modelled Costs** | `neso_modelled_costs` | Historical constraint analysis |
| **Skip Rate** | `neso_skip_rates` | Non-delivery tracking |

**Features**:
- NESO API integration (official CKAN API)
- Auto-detects latest CSV resources
- BigQuery schema auto-detection
- Append mode (preserves history)

**Manual Test**:
```bash
python3 /home/george/GB-Power-Market-JJ/auto_download_neso_daily.py
```

**Expected Output**:
```
================================================================================
🔄 NESO DAILY AUTO-INGESTION
================================================================================
📅 Date: 2025-12-28 03:00:15

================================================================================
📥 CONSTRAINT_BREAKDOWN: Monthly Emergency Instructions costs
================================================================================
📦 Fetching metadata for: historic-constraint-breakdown
   Latest: Dec_2025.csv (2025-12-27)
⬇️  Downloading: https://api.neso.energy/dataset/.../Dec_2025.csv
   Saved: neso_downloads/constraint_breakdown/constraint_breakdown_20251228.csv (2.45 MB)
📊 Loading to BigQuery: neso_constraint_breakdown
   Rows: 14,892
   ✅ Loaded 14,892 rows to neso_constraint_breakdown
✅ constraint_breakdown complete

[... 4 more datasets ...]

================================================================================
📈 SUMMARY
================================================================================
constraint_breakdown     ✅ Success
mbss                     ✅ Success
constraint_forecast      ✅ Success
modelled_costs           ✅ Success
skip_rate                ✅ Success

Total: 5/5 succeeded
```

**Log Location**: `/home/george/GB-Power-Market-JJ/logs/neso_daily.log`

---

## 3. Installation

### One-Command Setup

```bash
cd ~/GB-Power-Market-JJ
./install_daily_download_crons.sh
```

**What It Does**:
1. Makes scripts executable
2. Backs up existing crontab
3. Adds 2 new cron jobs:
   - P114 daily (2am)
   - NESO daily (3am)
4. Shows installation summary

**Output**:
```
==============================================
📦 Installing Daily Download Cron Jobs
==============================================

✅ Scripts are executable
✅ Backed up existing crontab to: crontab_backup_20251228_150432.txt

📝 Adding new cron jobs...
✅ Cron jobs installed successfully

==============================================
📋 INSTALLED CRON JOBS
==============================================

# ============================================
# GB Power Market - Daily Data Downloads
# Installed: 2025-12-28 15:04:32
# ============================================

# P114 Settlement Data - Daily at 2am (after Elexon publishes)
0 2 * * * /home/george/GB-Power-Market-JJ/auto_download_p114_daily.py >> /home/george/GB-Power-Market-JJ/logs/p114_daily.log 2>&1

# NESO Constraint Costs & Publications - Daily at 3am
0 3 * * * /home/george/GB-Power-Market-JJ/auto_download_neso_daily.py >> /home/george/GB-Power-Market-JJ/logs/neso_daily.log 2>&1

==============================================
✅ INSTALLATION COMPLETE
==============================================
```

---

## 4. Monitoring & Verification

### Check Cron Status
```bash
# View installed cron jobs
crontab -l | grep 'auto_download'

# Expected output:
0 2 * * * /home/george/GB-Power-Market-JJ/auto_download_p114_daily.py >> /home/george/GB-Power-Market-JJ/logs/p114_daily.log 2>&1
0 3 * * * /home/george/GB-Power-Market-JJ/auto_download_neso_daily.py >> /home/george/GB-Power-Market-JJ/logs/neso_daily.log 2>&1
```

### Monitor Logs (Real-Time)
```bash
# P114 downloads
tail -f ~/GB-Power-Market-JJ/logs/p114_daily.log

# NESO downloads
tail -f ~/GB-Power-Market-JJ/logs/neso_daily.log

# All logs
tail -f ~/GB-Power-Market-JJ/logs/*.log
```

### Verify Data Freshness
```bash
# Check P114 latest records
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')
query = '''
  SELECT
    MAX(settlement_date) as latest_date,
    COUNT(*) as total_records
  FROM \`inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi\`
'''
result = client.query(query).to_dataframe()
print('P114 Data:')
print(f'  Latest Date: {result[\"latest_date\"][0]}')
print(f'  Total Records: {result[\"total_records\"][0]:,}')
"

# Check NESO latest records
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')
for table in ['neso_constraint_breakdown', 'neso_mbss', 'neso_constraint_forecast']:
    query = f'SELECT COUNT(*) as cnt FROM \`inner-cinema-476211-u9.uk_energy_prod.{table}\`'
    result = client.query(query).to_dataframe()
    print(f'{table:30} {result[\"cnt\"][0]:>12,} rows')
"
```

---

## 5. Troubleshooting

### P114 Download Fails

**Symptom**: Log shows "❌ All settlement runs failed"

**Possible Causes**:
1. Elexon API rate limiting
2. Settlement runs not published yet (normal for recent dates)
3. Network issues

**Solution**:
```bash
# Wait for next scheduled run (data may not be published yet)
# Or test manually with specific date range:
python3 ingest_p114_s0142.py 2025-12-27 2025-12-27 II
```

### NESO Download Fails

**Symptom**: Log shows "❌ Failed" for NESO datasets

**Possible Causes**:
1. NESO API down
2. Dataset schema changed
3. Network timeout

**Solution**:
```bash
# Test API connectivity
curl -s "https://api.neso.energy/api/3/action/package_list" | head -20

# Test individual dataset
python3 -c "
import requests
url = 'https://api.neso.energy/api/3/action/package_show'
params = {'id': 'historic-constraint-breakdown'}
response = requests.get(url, params=params)
print(response.json()['result']['title'])
"
```

### Cron Not Running

**Symptom**: No new log entries after scheduled time

**Check**:
```bash
# Verify cron service running
systemctl status crond

# Check cron logs
journalctl -u crond -n 50

# Test script manually
python3 /home/george/GB-Power-Market-JJ/auto_download_p114_daily.py
```

---

## 6. Data Coverage Status

### P114 Settlement Data
- **Current Records**: 342,646,594 rows
- **Date Range**: 2021-10-13 to 2025-12-17
- **Coverage**: 1,148 days
- **Settlement Runs**: RF, R3, II (hybrid strategy)
- **Daily Additions**: ~300-500 records/day (II/SF/R1 combined)

### NESO Constraint Costs
- **Datasets**: 5 automated
- **Historical Coverage**: Jan 2022 - Present
- **Update Frequency**: Daily
- **Expected Additions**: 1-5 records/day per dataset

---

## 7. Integration with NGSEA Detection

### How This Enables NGSEA Analysis

**P114 Data** → VLP settlement revenue (FBPGM002, FFSEN005)
**NESO Constraint Costs** → Feature D validation (system stress events)

**Detection Flow**:
```
Daily Downloads (2-3am)
    ↓
BigQuery Tables Updated
    ↓
Run detect_ngsea_statistical.py
    ↓
Cross-validate with NESO reports
    ↓
Export to Google Sheets Dashboard
```

**Manual NGSEA Detection**:
```bash
# After daily downloads complete (after 3am)
python3 detect_ngsea_statistical.py --start 2025-12-01 --end 2025-12-31
```

---

## 8. Cost & Performance

### BigQuery Usage
- **P114 Daily**: ~300-500 rows × 3 runs = 1,500 rows/day (~40KB)
- **NESO Daily**: ~5-20 rows/day (~10KB)
- **Monthly Total**: ~1.5MB data/month
- **Cost**: Free tier (<<1GB/month)

### Cron Resource Usage
- **CPU**: <5% during download (30-60 seconds)
- **Memory**: ~200MB Python process
- **Network**: ~5-10MB/day downloads
- **Disk**: Logs ~1-2MB/day (auto-rotate weekly)

### Estimated Runtime
- **P114 Script**: 2-5 minutes (3 settlement runs)
- **NESO Script**: 5-10 minutes (5 datasets × API rate limits)
- **Total Daily**: ~15 minutes automation

---

## 9. Backup & Recovery

### Crontab Backup
Automatic backup created during installation:
```bash
ls -lh ~/GB-Power-Market-JJ/crontab_backup_*.txt
```

### Restore Crontab
```bash
# View backup
cat ~/GB-Power-Market-JJ/crontab_backup_20251228_150432.txt

# Restore if needed
crontab ~/GB-Power-Market-JJ/crontab_backup_20251228_150432.txt
```

### Manual Re-Installation
```bash
cd ~/GB-Power-Market-JJ
./install_daily_download_crons.sh
```

---

## 10. Future Enhancements

### Planned Improvements
- [ ] Email notifications on failure
- [ ] Slack/Discord webhook integration
- [ ] Google Sheets auto-update after downloads
- [ ] Historical backfill detection (auto-download missing dates)
- [ ] Download metrics dashboard

### Additional Datasets to Automate
- [ ] FPN (Final Physical Notifications)
- [ ] Interconnector flows (detailed)
- [ ] BMU capacity updates
- [ ] NESO weekly/monthly reports

---

## Summary

**Status**: ✅ Fully automated, zero manual downloads needed

**Daily Schedule**:
- 2:00 AM → P114 settlement data (II/SF/R1 runs)
- 3:00 AM → NESO constraint costs (5 datasets)

**Coverage**:
- P114: 342M+ records, 1,148 days, all settlement runs
- NESO: 5 key datasets, 2022-present

**Monitoring**:
```bash
# Quick health check
tail -20 ~/GB-Power-Market-JJ/logs/p114_daily.log
tail -20 ~/GB-Power-Market-JJ/logs/neso_daily.log
```

**Installation**: One command (`./install_daily_download_crons.sh`)

---

**Last Updated**: 28 December 2025
**Maintainer**: George Major (george@upowerenergy.uk)
**Server**: AlmaLinux 9.5, Dell PowerEdge, 94.237.55.234
