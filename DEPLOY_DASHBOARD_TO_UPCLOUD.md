# 🚀 Optional: Deploy Dashboard Updater to UpCloud

**Current Status**: Dashboard runs on your local Mac ✅  
**This Guide**: Optional deployment to UpCloud for 24/7 uptime

---

## ⚠️ When to Use This

Deploy to UpCloud ONLY if:
- ❌ Your Mac is frequently off/sleeping
- ❌ You want guaranteed 24/7 updates
- ✅ You're comfortable managing Google OAuth on remote server

**If your Mac runs 24/7:** No need to deploy! Current setup is perfect.

---

## 📋 Deployment Steps

### Option 1: Use Existing IRIS Server (94.237.55.234)

**Pros**: No extra cost, server already running  
**Cons**: Shares resources with IRIS pipeline

```bash
# 1. SSH to server
ssh root@94.237.55.234

# 2. Install Google packages (if not already installed)
pip3 install google-cloud-bigquery gspread google-auth

# 3. Create dashboard directory
mkdir -p /opt/dashboard-updater
cd /opt/dashboard-updater

# 4. Copy files from Mac
# (Run on your Mac)
cd "/Users/georgemajor/GB Power Market JJ"
scp realtime_dashboard_updater.py root@94.237.55.234:/opt/dashboard-updater/
scp inner-cinema-credentials.json root@94.237.55.234:/opt/dashboard-updater/

# 5. Setup Google OAuth on server
# (Run on server)
cd /opt/dashboard-updater
python3 -c "
import gspread
from google.oauth2.service_account import Credentials

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=scopes
)
client = gspread.authorize(creds)
print('✅ Authentication successful!')
"

# 6. Test manual run
python3 realtime_dashboard_updater.py

# 7. Setup cron job
crontab -e
# Add:
*/5 * * * * cd /opt/dashboard-updater && /usr/bin/python3 realtime_dashboard_updater.py >> logs/dashboard_updater.log 2>&1

# 8. Verify
crontab -l | grep dashboard
```

---

### Option 2: New Dedicated Server

**Pros**: Isolated, dedicated resources  
**Cons**: Extra cost (~$5-10/month)

```bash
# 1. Create new UpCloud server
# - OS: AlmaLinux 10
# - RAM: 1 GB (sufficient)
# - Location: London

# 2. Install Python and packages
ssh root@NEW_SERVER_IP
dnf install -y python3 python3-pip
pip3 install google-cloud-bigquery gspread google-auth

# 3. Follow steps 3-8 from Option 1 above
```

---

## 🔐 Security Considerations

### Service Account vs OAuth

**Current (Local Mac)**: Uses `token.pickle` (OAuth - your personal Google account)  
**Recommended (UpCloud)**: Use service account only (no token.pickle)

**To use service account only:**

1. **Grant service account access to spreadsheet:**
   - Open: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
   - Click "Share"
   - Add: Your service account email (from `inner-cinema-credentials.json`)
   - Permissions: Editor

2. **Modify script to skip OAuth token:**
   - Remove `token.pickle` logic
   - Use service account credentials only

---

## 🎯 Recommendation

**KEEP CURRENT SETUP** (Local Mac) ✅

**Reasons:**
- ✅ Already working perfectly (just fixed cron)
- ✅ Updates every 5 minutes successfully
- ✅ No additional costs
- ✅ More secure (credentials stay on your machine)
- ✅ Easier to debug/modify locally

**Deploy to UpCloud ONLY IF:**
- Your Mac is frequently offline
- You need guaranteed 24/7 operation

---

## 📊 Current vs UpCloud Comparison

| Feature | Local Mac (Current) | UpCloud Server |
|---------|---------------------|----------------|
| **Cost** | Free (Mac always on) | $5-10/month |
| **Uptime** | When Mac is on | 24/7 guaranteed |
| **Security** | Credentials local | Credentials remote |
| **Maintenance** | Easy (local access) | SSH required |
| **Performance** | 3 sec update time | 3 sec update time |
| **Setup** | ✅ Already done | Requires deployment |

---

## 🔄 Migration Back to Local

If you deploy to UpCloud but want to move back:

```bash
# 1. Stop UpCloud cron
ssh root@94.237.55.234 'crontab -r'

# 2. Re-enable local cron (already done!)
# Your current cron: ✅ ACTIVE
```

---

## ✅ Current Status (No Action Needed)

**Dashboard Updates:**
- **Where**: Your Mac (Local)
- **Frequency**: Every 5 minutes
- **Status**: ✅ WORKING (just fixed Python interpreter)
- **Next Update**: Next 5-minute mark (e.g., 18:40, 18:45, 18:50)

**UpCloud Servers:**
- **94.237.55.234**: IRIS pipeline (feeds BigQuery)
- **94.237.55.15**: Map generator (separate from dashboard)
- **Neither**: Runs dashboard updater (not needed!)

---

**Conclusion**: Everything is working optimally with current architecture. No need to deploy to UpCloud unless your Mac is frequently offline.
