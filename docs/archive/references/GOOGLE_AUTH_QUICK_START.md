# 🚀 Google Auth Quick Start Guide

## ⚡ TL;DR - Most Important Info

### **Primary Credential File** ⭐
```bash
inner-cinema-credentials.json
```
- **Project**: inner-cinema-476211-u9
- **Used by**: 98 Python scripts
- **Permissions**: chmod 600 (secure)

---

## 🎯 Top 5 Production Scripts

### 1. **realtime_dashboard_updater.py** 🏆
**Auto-refreshes Google Sheets dashboard every 5 minutes**
```bash
python3 realtime_dashboard_updater.py
tail -f logs/dashboard_updater.log  # Monitor
```

### 2. **gsp_auto_updater.py** 🌬️
**Wind generation by Grid Supply Point region**
```bash
python3 gsp_auto_updater.py
```

### 3. **battery_profit_analysis.py** 🔋
**Battery revenue & ROI analysis (79 batteries)**
```bash
python3 battery_profit_analysis.py
```

### 4. **complete_vlp_battery_analysis.py** 💰
**VLP revenue tracking (104 batteries, £12.76M top earner)**
```bash
python3 complete_vlp_battery_analysis.py
```

### 5. **deploy_google_integration.sh** 🚀
**One-command deployment of all Google services**
```bash
./deploy_google_integration.sh  # Now executable!
```

---

## 🔑 Authentication Template

**Copy-paste this into any new script:**

```python
#!/usr/bin/env python3
import os
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import gspread

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
LOCATION = "US"
CREDENTIALS_FILE = "inner-cinema-credentials.json"
SHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"

# Set environment variable
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = CREDENTIALS_FILE

# Define scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/bigquery'
]

# Create credentials
creds = Credentials.from_service_account_file(
    CREDENTIALS_FILE,
    scopes=SCOPES
)

# Initialize clients
bq_client = bigquery.Client(project=PROJECT_ID, location=LOCATION, credentials=creds)
sheets_client = gspread.authorize(creds)

# Open your sheet
sheet = sheets_client.open_by_key(SHEET_ID)
worksheet = sheet.worksheet("Live Dashboard")

# Example: Read data
data = worksheet.get_all_values()
print(f"✅ Read {len(data)} rows from Google Sheets")

# Example: BigQuery query
query = f"""
SELECT * FROM `{PROJECT_ID}.uk_energy_prod.bmrs_mid`
WHERE settlementDate >= '2025-01-01'
LIMIT 10
"""
df = bq_client.query(query).to_dataframe()
print(f"✅ Retrieved {len(df)} rows from BigQuery")

# Example: Write to sheet
worksheet.update(range_name='A1', values=[['Last Updated', 'Now']])
print("✅ Updated Google Sheets")
```

---

## 🛠️ Common Tasks

### **Test Authentication**
```bash
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ Connected')"
```

### **View Dashboard**
```bash
open "https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/"
```

### **Check Cron Jobs**
```bash
crontab -l | grep -E "dashboard_updater|gsp_auto"
```

### **Monitor Auto-Updates**
```bash
tail -f logs/dashboard_updater.log
tail -f logs/gsp_updater.log
```

### **Manual Full Refresh**
```bash
python3 update_dashboard_complete.py
```

---

## ⚠️ Critical Configuration

### **ALWAYS Use These Settings**:
```python
PROJECT_ID = "inner-cinema-476211-u9"  # NOT jibber-jabber-knowledge!
LOCATION = "US"                         # NOT europe-west2!
CREDENTIALS_FILE = "inner-cinema-credentials.json"
```

### **DON'T Use**:
- ❌ `jibber-jabber-knowledge` project (limited permissions)
- ❌ `europe-west2` location (wrong region)
- ❌ OAuth tokens (expire, not suitable for automation)

---

## 📊 Key Resources

### **Google Sheets Dashboard**
- **ID**: 12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
- **URL**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/

### **BigQuery Console**
- **Project**: https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9
- **Dataset**: `uk_energy_prod` (174+ tables, 391M+ rows)

### **Service Account**
- **Email**: inner-cinema@inner-cinema-476211-u9.iam.gserviceaccount.com
- **Permissions**: BigQuery Admin, Sheets Editor

---

## 🔍 File Locations

```
~/GB Power Market JJ/
├── inner-cinema-credentials.json          # ⭐ Main credentials
├── deploy_google_integration.sh           # ⭐ Deployment script (NOW EXECUTABLE!)
├── GOOGLE_AUTH_FILES_REFERENCE.md         # ⭐ Full documentation
├── GOOGLE_AUTH_QUICK_START.md             # ⭐ This guide
│
├── realtime_dashboard_updater.py          # Auto-refresh (5 min)
├── gsp_auto_updater.py                    # GSP wind updates
├── battery_profit_analysis.py             # Battery ROI
├── complete_vlp_battery_analysis.py       # VLP revenue
│
└── logs/
    ├── dashboard_updater.log              # Dashboard logs
    └── gsp_updater.log                    # GSP logs
```

---

## 🆘 Quick Troubleshooting

### **Problem**: "Permission denied"
```bash
chmod 600 inner-cinema-credentials.json
export GOOGLE_APPLICATION_CREDENTIALS="inner-cinema-credentials.json"
```

### **Problem**: "Dataset not found in europe-west2"
```python
# Change location from europe-west2 to US
client = bigquery.Client(project="inner-cinema-476211-u9", location="US")
```

### **Problem**: "Access Denied: jibber-jabber-knowledge"
```python
# Use inner-cinema project instead
PROJECT_ID = "inner-cinema-476211-u9"
```

### **Problem**: "deploy_google_integration.sh not found"
```bash
chmod +x deploy_google_integration.sh
./deploy_google_integration.sh
```

---

## 📚 Full Documentation

**For complete details, see**:
- `GOOGLE_AUTH_FILES_REFERENCE.md` - Complete file listing (57 scripts)
- `PROJECT_CONFIGURATION.md` - All configuration settings
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Data schema

---

## ✅ Recent Updates (Nov 11, 2025)

1. ✅ **Fixed deprecation warnings** (9 locations in GSP scripts)
2. ✅ **Added error handling** (50+ try-except blocks)
3. ✅ **Created documentation** (GOOGLE_AUTH_FILES_REFERENCE.md)
4. ✅ **Made deploy script executable** (chmod +x)
5. ✅ **Created this quick start guide**

---

**Status**: ✅ **All 98 scripts using service account authentication**  
**Next Steps**: Run `./deploy_google_integration.sh` to verify setup

---

*Last Updated: November 11, 2025*
