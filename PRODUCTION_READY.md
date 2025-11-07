# 🚀 Production-Ready BigQuery Analysis Pipeline

## 🎉 Deployment Status: **LIVE & HARDENED**

Your automated GB Power Market analysis is now running in production with enterprise-grade features!

---

## 📊 System Overview

### Infrastructure
- **Server**: UpCloud VM (94.237.55.15)
- **OS**: AlmaLinux (RHEL-based)
- **Python**: 3.12.9
- **Scheduling**: systemd timer (more robust than cron)
- **Authentication**: GCP Service Account (arbitrage-bq-sa)

### Schedule
- **Runs**: Daily at **04:00 UTC**
- **Next run**: 2025-11-07 04:00:00 UTC (18 hours from now)
- **Persistent**: Timer survives reboots

---

## 🔒 Security Hardening Complete

### ✅ Service Account Permissions
```bash
# Verified minimal IAM roles:
roles/bigquery.dataViewer
roles/bigquery.jobUser
```

### ✅ File Permissions
```bash
-rw-------. 1 root root 2394 /opt/arbitrage/service-account.json
# chmod 600 - only root can read
```

### ✅ Cost Safety Belt
- **Dry-run check** before every query
- **Limit**: 2TB processed per query
- **Current usage**: ~0.01 GB per run (5.7 MB)
- **Monthly estimate**: ~0.3 GB = **$0.0015/month**

---

## 📁 File Locations

```
/opt/arbitrage/
├── battery_arbitrage.py          # Main analysis script
├── service-account.json          # GCP credentials (chmod 600)
├── reports/
│   └── data/
│       ├── price_data_*.csv      # Daily price data
│       ├── summary_*.json        # Daily summary stats
│       └── health.json           # Health check file (latest)
└── logs/
    └── arbitrage.log             # All execution logs

/etc/systemd/system/
├── arbitrage.service             # Service definition
└── arbitrage.timer               # Schedule timer

/etc/logrotate.d/
└── arbitrage                     # Log rotation config
```

---

## 🏥 Health Check & Monitoring

### Real-Time Health Status
```bash
# Check health file (updated after each run)
ssh root@94.237.55.15 "cat /opt/arbitrage/reports/data/health.json"
```

**Sample Output:**
```json
{
  "ok": true,
  "last_run_utc": "2025-11-06T10:07:36.388078+00:00",
  "last_run_status": "success",
  "rows_retrieved": 275,
  "date_range": "2025-10-23 to 2025-10-30",
  "next_run_due_utc": "2025-11-07T04:00:00+00:00"
}
```

### Monitoring Commands
```bash
# Check timer status
ssh root@94.237.55.15 "systemctl list-timers | grep arbitrage"

# View recent logs
ssh root@94.237.55.15 "tail -50 /opt/arbitrage/logs/arbitrage.log"

# Check service status
ssh root@94.237.55.15 "systemctl status arbitrage.service"

# View last run via journald
ssh root@94.237.55.15 "journalctl -u arbitrage.service --no-pager -n 50"
```

### Optional: External Monitoring
To set up external health checks (UptimeRobot, StatusCake, etc.):

1. **Install web server to serve health.json:**
```bash
ssh root@94.237.55.15
cd /opt/arbitrage/reports
python3 -m http.server 8080 --directory /opt/arbitrage/reports &
```

2. **Or use Caddy (recommended):**
```bash
# Install Caddy
dnf install -y caddy

# Create Caddyfile
cat > /etc/caddy/Caddyfile <<'EOF'
:8080 {
    root * /opt/arbitrage/reports
    file_server
}
EOF

systemctl enable --now caddy
```

3. **Point your monitoring service to:**
   - URL: `http://94.237.55.15:8080/data/health.json`
   - Check frequency: Every 30 minutes
   - Alert if: `last_run_utc` is older than 26 hours

---

## 🎯 What Gets Analyzed

### Current Query
- **Table**: `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
- **Time Window**: Last 14 days (automatic backfill)
- **Aggregation**: By date, settlement period, and dataset
- **Metrics**: Average price, total volume, record count

### Sample Results (Last Run)
- **Rows**: 275
- **Date Range**: 2025-10-23 to 2025-10-30
- **Average Price**: £22.85/MWh
- **Price Range**: £-7.78 to £93.70/MWh
- **Total Volume**: 766,762 MWh

---

## 🛠️ Manual Operations

### Force a Run (Testing)
```bash
# Start the service manually
ssh root@94.237.55.15 "systemctl start arbitrage.service"

# Watch logs in real-time
ssh root@94.237.55.15 "tail -f /opt/arbitrage/logs/arbitrage.log"
```

### Update the Script
```bash
# From your Mac
scp battery_arbitrage.py root@94.237.55.15:/opt/arbitrage/

# Test the new version
ssh root@94.237.55.15 "systemctl start arbitrage.service"
```

### Change Schedule
```bash
# Edit timer (currently 04:00 UTC daily)
ssh root@94.237.55.15 "vi /etc/systemd/system/arbitrage.timer"

# Example: Run every 6 hours
# Change line: OnCalendar=*-*-* 04:00:00 UTC
# To: OnCalendar=*-*-* 00/6:00:00 UTC

# Reload and check
systemctl daemon-reload
systemctl list-timers | grep arbitrage
```

---

## 📦 Outputs Explained

### 1. Price Data CSV (`price_data_YYYYMMDD_HHMMSS.csv`)
Contains raw aggregated data:
- `date`: Trading date
- `sp`: Settlement period (1-48 or 1-50 on clock change days)
- `dataset`: Data source identifier
- `avg_price`: Average price (£/MWh)
- `total_volume`: Total traded volume (MWh)
- `records`: Number of records aggregated

### 2. Summary JSON (`summary_YYYYMMDD_HHMMSS.json`)
High-level statistics:
- `run_time`: Execution timestamp
- `rows`: Number of rows retrieved
- `date_from`, `date_to`: Data range
- `avg_price_£_per_mwh`: Mean price
- `min_price_£_per_mwh`, `max_price_£_per_mwh`: Price range
- `total_volume_mwh`: Cumulative volume
- `bytes_processed`: Query size
- `query_cost_gb`: Cost metric

### 3. Health JSON (`health.json`)
Always shows latest run status:
- `ok`: Boolean success flag
- `last_run_utc`: Timestamp of last execution
- `last_run_status`: "success" or error message
- `rows_retrieved`: Data quality check
- `date_range`: Coverage verification
- `next_run_due_utc`: Expected next execution

---

## 🔧 Log Rotation

Logs are automatically rotated to prevent disk fill:
- **Frequency**: Weekly
- **Retention**: 8 weeks
- **Compression**: Yes (gzip)
- **Config**: `/etc/logrotate.d/arbitrage`

---

## 💰 Cost Analysis

### BigQuery Costs
- **Query size**: ~5.7 MB per run
- **Frequency**: Daily
- **Monthly**: ~0.17 GB processed
- **Cost**: ~$0.0009/month (first 1TB free)

### UpCloud Server
- **Instance**: 1 vCPU, 1GB RAM
- **Cost**: ~$5-10/month (your existing server)
- **Utilization**: <1% CPU, <80 MB RAM per run

### Total
- **~$5-10/month** (just the server, BigQuery is negligible)

---

## 🚀 Next Steps & Enhancements

### Option 1: Add More Tables
Expand analysis to include:
- `bmrs_fuelinst` - Fuel mix data
- `bmrs_freq` - Frequency data
- `bmrs_bod` - Bid-offer data

### Option 2: Export to Google Drive
Auto-upload results to Google Sheets or Drive folder:
```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Add to battery_arbitrage.py
def upload_to_drive(file_path):
    creds = service_account.Credentials.from_service_account_file(
        'service-account.json',
        scopes=['https://www.googleapis.com/auth/drive.file']
    )
    service = build('drive', 'v3', credentials=creds)
    # ... upload logic
```

### Option 3: Email Alerts
Send summary email after each run:
```bash
# Install sendmail
dnf install -y sendmail

# Add to service file
ExecStartPost=/bin/bash -c 'tail -20 /opt/arbitrage/logs/arbitrage.log | mail -s "Arbitrage Run Complete" your@email.com'
```

### Option 4: Add IRIS Generation Data
Include generation mix for arbitrage context:
```python
# Query generation data alongside prices
gen_query = f"""
SELECT DATE(trading_date) d, settlement_period sp,
       SUM(wind_mw) wind, SUM(solar_mw) solar,
       SUM(ccgt_mw) gas, SUM(coal_mw) coal
FROM `{PROJECT}.your_gen_table`
WHERE DATE(trading_date) >= DATE_SUB(CURRENT_DATE(), INTERVAL 14 DAY)
GROUP BY d, sp
"""
```

---

## 🆘 Troubleshooting

### Timer Not Running
```bash
# Check timer is active
systemctl status arbitrage.timer

# Re-enable if needed
systemctl enable --now arbitrage.timer
```

### Service Failing
```bash
# Check detailed logs
journalctl -xeu arbitrage.service

# Test authentication
ssh root@94.237.55.15 "cd /opt/arbitrage && GOOGLE_APPLICATION_CREDENTIALS=/opt/arbitrage/service-account.json python3 -c 'from google.cloud import bigquery; print(bigquery.Client().project)'"
```

### No Data Retrieved
```bash
# Check BigQuery table status
ssh root@94.237.55.15 "cd /opt/arbitrage && GOOGLE_APPLICATION_CREDENTIALS=/opt/arbitrage/service-account.json python3 <<'PY'
from google.cloud import bigquery
c = bigquery.Client()
result = c.query('SELECT COUNT(*) cnt FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`').to_dataframe()
print(result)
PY"
```

### Disk Space Issues
```bash
# Check disk usage
ssh root@94.237.55.15 "df -h /opt"

# Clean old reports (keep last 30 days)
ssh root@94.237.55.15 "find /opt/arbitrage/reports/data -name 'price_data_*.csv' -mtime +30 -delete"
```

---

## 📞 Support Reference

### Service Account
- **Email**: arbitrage-bq-sa@inner-cinema-476211-u9.iam.gserviceaccount.com
- **Key Location**: /opt/arbitrage/service-account.json
- **Roles**: BigQuery Data Viewer, BigQuery Job User

### GCP Project
- **Project ID**: inner-cinema-476211-u9
- **Dataset**: uk_energy_prod
- **Table**: bmrs_mid (155,405 rows, 2022-01-01 to 2025-10-30)

### GitHub Repository
- **Repo**: gb-power-market-jj
- **Owner**: GeorgeDoors888
- **Branch**: main

---

## ✅ Completed Checklist

- [x] ✅ Service account created with minimal permissions
- [x] ✅ Systemd timer configured (replaces cron)
- [x] ✅ Log rotation enabled (weekly, 8 weeks retention)
- [x] ✅ File permissions hardened (chmod 600)
- [x] ✅ Cost safety belt (2TB query limit)
- [x] ✅ Health check file (health.json)
- [x] ✅ Timezone-aware timestamps (UTC)
- [x] ✅ Automatic backfill (14-day window)
- [x] ✅ Dry-run cost check before queries
- [x] ✅ Comprehensive logging
- [x] ✅ Production testing complete

---

## 🎓 Key Improvements from Initial Setup

| Feature | Before | After |
|---------|--------|-------|
| **Scheduling** | cron | systemd timer (persistent, better logging) |
| **Timestamps** | `datetime.utcnow()` (deprecated) | `datetime.now(timezone.utc)` |
| **Cost Control** | None | Dry-run check, 2TB limit |
| **Monitoring** | Manual log checks | health.json + systemd status |
| **Log Management** | Unbounded | Weekly rotation, 8-week retention |
| **Security** | Key file 644 | Key file 600 (root only) |
| **Error Handling** | Basic try/catch | Cost checks, health tracking |
| **Documentation** | Basic setup notes | Full production guide |

---

## 🎯 Production Status

**System Status**: ✅ **PRODUCTION READY**

- First automated run: **Tomorrow (2025-11-07) at 04:00 UTC**
- All safety checks: **PASSED**
- All monitoring: **ACTIVE**
- All hardening: **COMPLETE**

You can now sit back and let it run! 🚀

---

*Last Updated: 2025-11-06 10:10 UTC*
*System Version: v2.0 (Production Hardened)*
