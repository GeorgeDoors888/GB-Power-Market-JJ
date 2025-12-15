# Dashboard Status and Troubleshooting Guide

**Last Updated**: November 20, 2025  
**Dashboard**: [GB Energy Dashboard](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit)

---

## 📊 Current Dashboard Status

### ✅ **Working Components**
- Google Sheets: Accessible (29 tabs)
- BigQuery Connection: Working (155,405 rows in bmrs_mid)
- Google Drive API: Connected
- Vercel Proxy: Healthy (ChatGPT integration)
- Credentials: Valid (inner-cinema-476211-u9)

### ❌ **Issues to Fix**
1. **Dashboard data outdated** - Last updated: 2025-11-11 19:55:45
2. **UpCloud server issues** - Need to check deployment status
3. **BigQuery data freshness** - Verify IRIS pipeline on AlmaLinux server

---

## 🏗️ Dashboard Architecture

### **Current Layout (DO NOT MODIFY)**

```
Row 1-6:   Header Section
  - Title, Last Updated, Market Price, Generation Summary

Row 7-17:  Main Content (Two Columns)
  - LEFT:  Fuel Breakdown (WIND, CCGT, BIOMASS, NUCLEAR, etc.)
  - RIGHT: Interconnectors (ElecLink, IFA, BritNed, etc.)

Row 20-38: Outages Section
  - Individual outages with capacity bars
  - Total unavailable capacity

Row 40+:   GSP Analysis
  - Generation/Export data
```

---

## 🔍 Diagnostic Steps

### 1. Check BigQuery Data Freshness

```bash
# Test BigQuery connection
python3 -c "
from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

client = bigquery.Client(project='inner-cinema-476211-u9')

# Check latest data timestamp
query = '''
SELECT 
  MAX(settlementDate) as latest_date,
  COUNT(*) as row_count
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst\`
'''

result = client.query(query).result()
for row in result:
    print(f'Latest data: {row.latest_date}')
    print(f'Total rows: {row.row_count:,}')
"
```

**Expected**: Latest date should be today or yesterday  
**If outdated**: IRIS pipeline on AlmaLinux not running

### 2. Check IRIS Pipeline (AlmaLinux Server)

```bash
# Connect to AlmaLinux server
ssh root@94.237.55.234

# Check IRIS uploader status
systemctl status iris-uploader

# Check recent logs
tail -50 /opt/iris-pipeline/logs/iris_uploader.log

# Check if data is being downloaded
ls -lth /opt/iris-pipeline/iris_data/ | head -20

# Check last successful upload
grep "Successfully uploaded" /opt/iris-pipeline/logs/iris_uploader.log | tail -5
```

**Expected**: Service running, recent uploads in logs  
**If not running**: Restart with `systemctl restart iris-uploader`

### 3. Check UpCloud Server Status

```bash
# Check if UpCloud server is accessible
ping 94.237.55.15

# Check web server
curl http://94.237.55.15/gb_power_complete_map.html

# SSH into UpCloud (if accessible)
ssh root@94.237.55.15

# Check battery arbitrage service
systemctl status battery-arbitrage

# Check API Gateway
systemctl status api-gateway
```

**Expected**: Server responding, services running  
**If down**: Need to investigate hosting status

### 4. Check Dashboard Update Script

```bash
# Test dashboard updater locally
cd ~/GB\ Power\ Market\ JJ

# Set credentials
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/inner-cinema-credentials.json"

# Run dashboard updater
python3 update_analysis_bi_enhanced.py

# Check for errors
echo $?  # Should return 0 if successful
```

---

## 🔧 Common Issues and Fixes

### **Issue 1: Dashboard Not Updating**

**Symptoms**: Last updated timestamp is old, data stale

**Causes**:
1. IRIS pipeline not running on AlmaLinux
2. BigQuery not receiving new data
3. Dashboard update script not running
4. Credentials expired or missing

**Fix**:
```bash
# 1. Restart IRIS pipeline
ssh root@94.237.55.234 "systemctl restart iris-uploader"

# 2. Manually run dashboard update
cd ~/GB\ Power\ Market\ JJ
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/inner-cinema-credentials.json"
python3 update_analysis_bi_enhanced.py

# 3. Check credentials
python3 -c "
from google.oauth2 import service_account
creds = service_account.Credentials.from_service_account_file('inner-cinema-credentials.json')
print('✅ Credentials valid')
"
```

---

### **Issue 2: IRIS Pipeline Stopped**

**Symptoms**: No new data in BigQuery, bmrs_*_iris tables empty or stale

**Causes**:
1. Azure Service Bus connection lost
2. Service crashed
3. Disk space full
4. Network issues

**Fix**:
```bash
ssh root@94.237.55.234

# Check service status
systemctl status iris-uploader

# Check disk space
df -h

# Check network connectivity
ping azure.microsoft.com

# Restart service
systemctl restart iris-uploader

# Monitor logs in real-time
tail -f /opt/iris-pipeline/logs/iris_uploader.log

# Check if messages are being received
ls -lth /opt/iris-pipeline/iris_data/ | head -10
```

---

### **Issue 3: UpCloud Server Down**

**Symptoms**: Can't access 94.237.55.15, map not loading, API not responding

**Causes**:
1. Server powered off
2. Network configuration issue
3. Service crashed
4. Hosting account issue

**Fix**:
```bash
# 1. Check if server is reachable
ping 94.237.55.15

# 2. Try SSH access
ssh root@94.237.55.15

# 3. If accessible, check services
systemctl status nginx
systemctl status battery-arbitrage
systemctl status api-gateway

# 4. Restart services if needed
systemctl restart nginx
systemctl restart battery-arbitrage

# 5. Check logs
journalctl -u nginx -n 50
journalctl -u battery-arbitrage -n 50
```

**If server not accessible**: Contact UpCloud support or check hosting panel

---

### **Issue 4: BigQuery Permission Errors**

**Symptoms**: "Access Denied", "Permission denied on resource project"

**Causes**:
1. Wrong credentials file
2. Service account lacks permissions
3. Using wrong GCP project

**Fix**:
```bash
# Verify project ID
python3 -c "
import json
with open('inner-cinema-credentials.json') as f:
    data = json.load(f)
    print(f'Project: {data[\"project_id\"]}')
    print(f'Email: {data[\"client_email\"]}')
"

# Should show:
# Project: inner-cinema-476211-u9
# Email: all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com

# Test BigQuery access
python3 -c "
from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9')
query = 'SELECT COUNT(*) FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_mid\` LIMIT 1'
result = list(client.query(query).result())
print(f'✅ Access granted: {result[0][0]:,} rows')
"
```

---

## 📝 Manual Dashboard Update Process

If automated updates fail, manually update the dashboard:

### Step 1: Get Latest Data from BigQuery

```python
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9')

# Get latest fuel generation
query = """
SELECT 
  fuelType,
  SUM(generation) / 1000 as generation_gw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE settlementDate = CURRENT_DATE()
  AND settlementPeriod = (SELECT MAX(settlementPeriod) 
                          FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
                          WHERE settlementDate = CURRENT_DATE())
GROUP BY fuelType
ORDER BY generation_gw DESC
"""

result = client.query(query).result()
for row in result:
    print(f"{row.fuelType}: {row.generation_gw:.1f} GW")
```

### Step 2: Update Google Sheets

```python
from googleapiclient.discovery import build
from google.oauth2 import service_account

SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
creds = service_account.Credentials.from_service_account_file('inner-cinema-credentials.json')
sheets = build('sheets', 'v4', credentials=creds).spreadsheets()

# Update specific cell (example: WIND generation in B8)
values = [['13.5 GW']]  # Your new value
body = {'values': values}

sheets.values().update(
    spreadsheetId=SHEET_ID,
    range='Dashboard!B8',  # WIND row
    valueInputOption='USER_ENTERED',
    body=body
).execute()

print("✅ Dashboard updated")
```

---

## 🚀 Automated Update Scripts

### Primary Update Script
**File**: `update_analysis_bi_enhanced.py`  
**Purpose**: Main dashboard refresh  
**Run**: `python3 update_analysis_bi_enhanced.py`

### Real-time Updater (Auto-refresh)
**File**: `realtime_dashboard_updater.py`  
**Purpose**: Continuous updates every 5 minutes  
**Status**: Check with `ps aux | grep realtime_dashboard`  
**Logs**: `tail -f logs/dashboard_updater.log`

### Cron Job (if configured)
```bash
# Check if cron job exists
crontab -l | grep dashboard

# Add cron job for every 5 minutes
*/5 * * * * cd /Users/georgemajor/GB\ Power\ Market\ JJ && python3 update_analysis_bi_enhanced.py >> logs/dashboard_cron.log 2>&1
```

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Sources                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Elexon BMRS API     Azure Service Bus (IRIS)              │
│       │                      │                               │
│       │                      ↓                               │
│       │              AlmaLinux Server                        │
│       │              (94.237.55.234)                         │
│       │              iris-uploader service                   │
│       │                      │                               │
│       └──────────────┬───────┘                               │
│                      ↓                                       │
│              ┌─────────────────┐                            │
│              │   BigQuery      │                            │
│              │ inner-cinema-   │                            │
│              │  476211-u9      │                            │
│              │ uk_energy_prod  │                            │
│              └────────┬────────┘                            │
│                       │                                      │
│                       ↓                                      │
│              ┌─────────────────┐                            │
│              │  Python Scripts │                            │
│              │  (iMac/Dell)    │                            │
│              │  - update_      │                            │
│              │    analysis_    │                            │
│              │    bi_enhanced  │                            │
│              └────────┬────────┘                            │
│                       │                                      │
│                       ↓                                      │
│              ┌─────────────────┐                            │
│              │ Google Sheets   │                            │
│              │   Dashboard     │                            │
│              │  (29 tabs)      │                            │
│              └─────────────────┘                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Required Credentials

### Location
- **Primary**: `~/GB Power Market JJ/inner-cinema-credentials.json`
- **Backup**: `~/GB Power Market JJ/deploy_package/inner-cinema-credentials.json`

### Required Permissions
- BigQuery Data Viewer
- BigQuery Job User
- Google Sheets API access
- Google Drive API access

### Verification
```bash
python3 -c "
import json
with open('inner-cinema-credentials.json') as f:
    data = json.load(f)
    assert data['project_id'] == 'inner-cinema-476211-u9', 'Wrong project!'
    print('✅ Credentials correct')
"
```

---

## 📞 Quick Fix Checklist

When dashboard is not updating:

- [ ] **Check IRIS pipeline**: `ssh root@94.237.55.234 'systemctl status iris-uploader'`
- [ ] **Check BigQuery data**: Run diagnostic query for latest timestamp
- [ ] **Check credentials**: Verify `inner-cinema-credentials.json` exists
- [ ] **Run manual update**: `python3 update_analysis_bi_enhanced.py`
- [ ] **Check logs**: `tail -f logs/dashboard_updater.log`
- [ ] **Verify sheet access**: Open dashboard URL in browser
- [ ] **Check UpCloud server**: `ping 94.237.55.15`
- [ ] **Restart services if needed**: Run restart commands above

---

## 📚 Related Documentation

- `PROJECT_CONFIGURATION.md` - Full system configuration
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Data pipeline details
- `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md` - IRIS setup
- `.github/copilot-instructions.md` - System overview

---

## 🆘 Emergency Contact

**If all else fails:**

1. Check GitHub Issues: https://github.com/GeorgeDoors888/GB-Power-Market-JJ/issues
2. Check system status logs on servers
3. Verify GCP billing and quotas
4. Contact hosting providers (UpCloud, Azure)

---

**Last Verified**: November 20, 2025  
**Next Review**: Check after fixing current issues
