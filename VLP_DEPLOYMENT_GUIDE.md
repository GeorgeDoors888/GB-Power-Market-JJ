# VLP Dashboard - Quick Deployment Guide

## 🚀 5-Minute Setup

### Prerequisites Checklist
- ✅ Python 3.9+ installed
- ✅ Google credentials: `/home/george/inner-cinema-credentials.json`
- ✅ BigQuery access: `inner-cinema-476211-u9.uk_energy_prod`
- ✅ Google Sheets: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`

### Step 1: Install Dependencies (30 seconds)
```bash
pip3 install --user google-cloud-bigquery db-dtypes pyarrow pandas gspread oauth2client flask
```

### Step 2: Test Connection (15 seconds)
```bash
cd /home/george/GB-Power-Market-JJ

# Test BigQuery
python3 -c 'from google.cloud import bigquery; client = bigquery.Client(project="inner-cinema-476211-u9"); print("✅ BigQuery OK")'

# Test Sheets
python3 -c 'import gspread; print("✅ gspread OK")'
```

### Step 3: Run Dashboard Pipeline (2-3 minutes)
```bash
# Full pipeline
python3 vlp_dashboard_simple.py && \
python3 format_vlp_dashboard.py && \
python3 create_vlp_charts.py
```

**Expected Output**:
```
🚀 VLP DASHBOARD - SIMPLE VERSION
======================================================
📊 Fetching data from 2025-10-17 to 2025-10-23...
   ✅ Loaded 336 settlement periods
💰 Calculating revenues...
   Total BM revenue: £447,777
   Total CM revenue: £49,327
   Total PPA revenue: £818,475
   Total gross margin: £2,311,556
📝 Writing to Google Sheets...
   ✅ BESS_VLP sheet updated (336 rows)
   ✅ Dashboard updated

📊 SUMMARY:
   Total Gross: £2,311,556
   Site (70%): £1,609,756
   VLP (30%): £693,467

✅ COMPLETE!
```

### Step 4: Verify Results (30 seconds)
Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

**Check**:
- ✅ Dashboard tab: Revenue breakdown table (A4:B10)
- ✅ Dashboard tab: KPIs (D4:E7) show £2.3M gross
- ✅ Dashboard tab: 4 charts visible (Revenue Stack, SoC, Actions, Margin)
- ✅ BESS_VLP tab: 336 rows of time series data
- ✅ Formatting applied: Currency (£), colors, borders

---

## 🔧 Optional: Apps Script Menu

### Step 5a: Deploy via CLASP (Advanced - 5 minutes)
```bash
# Install CLASP
npm install -g @google/clasp

# Login
clasp login

# Copy VLP menu to Apps Script folder
cp vlp_menu.gs appsscript_v3/

# Push to Google
clasp push

# Deploy
clasp deploy --description "VLP Dashboard v1.0"
```

### Step 5b: Manual Setup (Alternative - 3 minutes)
1. Open spreadsheet: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
2. Extensions → Apps Script
3. Paste contents of `vlp_menu.gs`
4. Save (Ctrl+S)
5. Reload spreadsheet
6. New menu: **🔋 VLP Dashboard** appears

### Step 6: Webhook Server (Optional - for menu button)
```bash
# Terminal 1: Run webhook
python3 vlp_webhook_server.py

# Terminal 2: Expose via ngrok
ngrok http 5002

# Copy ngrok URL and update vlp_menu.gs line 33:
# const webhookUrl = 'YOUR_NGROK_URL_HERE/refresh-vlp';
```

---

## 📅 Automation: Daily Refresh

### Option A: Cron Job
```bash
# Edit crontab
crontab -e

# Add line (runs at 8 AM daily):
0 8 * * * cd /home/george/GB-Power-Market-JJ && python3 vlp_dashboard_simple.py && python3 format_vlp_dashboard.py >> logs/vlp_daily.log 2>&1
```

### Option B: Systemd Timer (Similar to arbitrage.timer)
```bash
# Create service file
sudo nano /etc/systemd/system/vlp-dashboard.service
```
```ini
[Unit]
Description=VLP Dashboard Refresh
After=network.target

[Service]
Type=oneshot
User=george
WorkingDirectory=/home/george/GB-Power-Market-JJ
ExecStart=/usr/bin/python3 /home/george/GB-Power-Market-JJ/vlp_dashboard_simple.py
ExecStartPost=/usr/bin/python3 /home/george/GB-Power-Market-JJ/format_vlp_dashboard.py
```

```bash
# Create timer file
sudo nano /etc/systemd/system/vlp-dashboard.timer
```
```ini
[Unit]
Description=VLP Dashboard Daily Refresh
Requires=vlp-dashboard.service

[Timer]
OnCalendar=daily
OnCalendar=08:00
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
# Enable and start
sudo systemctl enable vlp-dashboard.timer
sudo systemctl start vlp-dashboard.timer

# Check status
sudo systemctl status vlp-dashboard.timer
```

---

## 🧪 Testing Different Date Ranges

### Change Date Range in vlp_dashboard_simple.py
Edit line 250:
```python
# Current (Oct 17-23 high-price week)
df = fetch_vlp_data(start_date='2025-10-17', end_date='2025-10-23')

# Test last 30 days
df = fetch_vlp_data(start_date='2025-10-01', end_date='2025-10-31')

# Test normal price week (Oct 24-30)
df = fetch_vlp_data(start_date='2025-10-24', end_date='2025-10-30')
```

Or modify `main()` function to accept command-line args:
```python
import sys

def main():
    start = sys.argv[1] if len(sys.argv) > 1 else '2025-10-17'
    end = sys.argv[2] if len(sys.argv) > 2 else '2025-10-23'
    
    df = fetch_vlp_data(start_date=start, end_date=end)
    df = calculate_revenues(df)
    write_to_sheets(df)
```

Then run:
```bash
python3 vlp_dashboard_simple.py 2025-10-01 2025-10-31
```

---

## 🔍 Monitoring & Logs

### Check Last Run Status
```bash
# View last run output
tail -100 logs/vlp_daily.log

# Monitor real-time
tail -f logs/vlp_daily.log
```

### Verify Data Freshness
Check "Last Updated" timestamp in Dashboard cell A20

### BigQuery Query Costs
```bash
# Check BigQuery usage
bq ls -j --max_results=10 inner-cinema-476211-u9
```

---

## 🆘 Common Issues

### Issue 1: "No module named 'google.cloud'"
```bash
pip3 install --user google-cloud-bigquery db-dtypes
```

### Issue 2: "Access Denied" on BigQuery
```bash
# Check credentials path
ls -la /home/george/inner-cinema-credentials.json

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/home/george/inner-cinema-credentials.json"
```

### Issue 3: Charts Not Appearing
```bash
# Re-run chart script
python3 create_vlp_charts.py
```

### Issue 4: Stale Data (missing recent periods)
**Cause**: Historical tables lag ~24h  
**Solution**: Modify query to UNION with IRIS tables (see VLP_SYSTEM_README.md)

---

## ✅ Success Criteria

After deployment, verify:
- ✅ Dashboard shows £2.3M gross margin (Oct 17-23)
- ✅ BESS_VLP has 336 rows (7 days × 48 SPs)
- ✅ 4 charts visible and populated
- ✅ Currency formatting applied (£#,##0)
- ✅ Last Updated timestamp within last run time
- ✅ Apps Script menu (optional) appears in Sheets

---

## 📞 Support

**Questions?** Contact george@upowerenergy.uk  
**Full Docs**: See `VLP_SYSTEM_README.md`  
**Troubleshooting**: See `STOP_DATA_ARCHITECTURE_REFERENCE.md`

---

*Deployment guide v1.0 - November 2025*
