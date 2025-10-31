# Automated IRIS Dashboard Guide

**Status:** Ready to use!  
**Purpose:** Automatically query BigQuery, update Google Sheets, and create charts - no manual work!

---

## 🎯 What It Does

The automated dashboard will:

1. ✅ **Query BigQuery** for latest IRIS data
2. ✅ **Update Google Sheets** with fresh data
3. ✅ **Create beautiful charts** automatically
4. ✅ **Run continuously** (every 5 minutes)
5. ✅ **No manual intervention** needed!

### Dashboards Created:

| Sheet | Data | Chart Type | Refresh |
|-------|------|------------|---------|
| **System Prices** | SSP, SBP, SMP (last 48h) | Line chart | Every 5 min |
| **Grid Frequency** | Frequency (last hour) | Line chart | Every 5 min |
| **Fuel Generation** | Generation by fuel type | Bar chart | Every 5 min |
| **Recent Activity** | Dataset update stats | Table | Every 5 min |

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
./.venv/bin/pip install google-cloud-bigquery google-api-python-client gspread
```

### 2. Ensure Service Account Ready

Make sure `service.json` exists in your workspace (you already have this!)

### 3. Start Dashboard

```bash
./start_automated_dashboard.sh
```

**That's it!** The dashboard will:
- Create a Google Sheet called "IRIS Real-Time Dashboard"
- Update it every 5 minutes with latest data
- Create charts automatically
- Run in the background

---

## 📊 Usage

### Start Dashboard (Continuous Updates)

```bash
./start_automated_dashboard.sh
```

This runs in background, updating every 5 minutes.

### Run Once (Single Update)

```bash
./.venv/bin/python automated_iris_dashboard.py
```

### Check Logs

```bash
# Watch live updates
tail -f automated_dashboard.log

# View recent activity
tail -50 automated_dashboard.log
```

### Stop Dashboard

```bash
# Get PID
cat automated_dashboard.pid

# Stop it
kill $(cat automated_dashboard.pid)
```

---

## 📈 What You'll See

### System Prices Chart
- **X-axis:** Time (last 48 hours)
- **Y-axis:** Price (£/MWh)
- **Lines:** SSP (red), SBP (blue), SMP (green)
- **Updates:** Every 5 minutes

### Grid Frequency Chart
- **X-axis:** Time (last hour)
- **Y-axis:** Frequency (Hz)
- **Line:** Real-time frequency measurements
- **Updates:** Every 5 minutes

### Fuel Generation Chart
- **X-axis:** Generation (MW)
- **Y-axis:** Fuel types (Gas, Wind, Nuclear, etc.)
- **Bars:** Average generation last hour
- **Updates:** Every 5 minutes

---

## ⚙️ Configuration

### Change Update Interval

```bash
# Update every 2 minutes
./.venv/bin/python automated_iris_dashboard.py --loop --interval 120

# Update every 10 minutes
./.venv/bin/python automated_iris_dashboard.py --loop --interval 600
```

### Customize Queries

Edit `automated_iris_dashboard.py` and modify the queries:

```python
# Example: Get last 200 periods instead of 100
query = f"""
SELECT ...
LIMIT 200  # Changed from 100
"""
```

### Add New Dashboards

Add a new method to the `IRISDashboard` class:

```python
def update_my_custom_dashboard(self):
    """Your custom dashboard"""
    query = f"""
    SELECT ...
    FROM `{BQ_PROJECT}.{BQ_DATASET}.your_table`
    """
    
    data = self.query_bigquery(query)
    self.update_sheet("My Dashboard", data)
    self.create_chart("My Dashboard", chart_config)
```

Then call it in `run_full_update()`:

```python
def run_full_update(self):
    ...
    self.update_my_custom_dashboard()  # Add this line
```

---

## 📊 Available Data

The dashboard can query any of your IRIS tables:

- `bmrs_boalf_iris` - Bid-Offer Acceptances
- `bmrs_bod_iris` - Bid-Offer Data
- `bmrs_mels_iris` - Max Export Limits
- `bmrs_mils_iris` - Max Import Limits
- `bmrs_freq_iris` - Grid Frequency
- `bmrs_fuelinst_iris` - Fuel Generation
- `bmrs_mid_iris` - Market Index Data (SSP, SBP, SMP)
- `bmrs_remit_iris` - REMIT Messages
- `bmrs_beb_iris` - Balancing Energy Bids

---

## 🔍 Monitoring

### Check Dashboard Status

```bash
# Is it running?
ps aux | grep automated_iris_dashboard

# View PID
cat automated_dashboard.pid

# Check recent updates
tail -20 automated_dashboard.log | grep "Dashboard updated"
```

### View Your Google Sheet

The log will show the URL:

```
📊 View at: https://docs.google.com/spreadsheets/d/[SPREADSHEET_ID]
```

Or open Google Sheets and search for "IRIS Real-Time Dashboard"

---

## 🐛 Troubleshooting

### "Service account file not found"

```bash
# Check if service.json exists
ls -lh service.json

# If not, copy it from your credentials location
cp /path/to/your/service-account-key.json service.json
```

### "No data returned from BigQuery"

```bash
# Check if IRIS data is flowing
bq query --use_legacy_sql=false \
'SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris` 
 WHERE ingested_utc >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)'
```

### "Dashboard not updating"

```bash
# Check if process is running
ps aux | grep automated_iris_dashboard

# Check logs for errors
tail -100 automated_dashboard.log | grep ERROR

# Restart
kill $(cat automated_dashboard.pid)
./start_automated_dashboard.sh
```

### "Charts not appearing"

Charts are created on first run. If missing:
1. Check logs for chart creation errors
2. Manually refresh the Google Sheet
3. Ensure data exists in the sheet

---

## 🎨 Customization Examples

### 1. Add Balancing Actions Chart

```python
def update_balancing_actions(self):
    """Balancing actions summary"""
    query = f"""
    SELECT 
        bmUnit,
        COUNT(*) as actions,
        SUM(acceptanceLevel) as total_mw
    FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_boalf_iris`
    WHERE acceptanceTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
    GROUP BY bmUnit
    ORDER BY actions DESC
    LIMIT 20
    """
    
    data = self.query_bigquery(query)
    self.update_sheet("Balancing Actions", data)
    # Add chart...
```

### 2. Add Price Volatility Alert

```python
def check_price_volatility(self):
    """Check for unusual price movements"""
    query = f"""
    SELECT 
        systemSellPrice,
        LAG(systemSellPrice) OVER (ORDER BY settlement_date) as prev_price
    FROM `{BQ_PROJECT}.{BQ_DATASET}.bmrs_mid_iris`
    ORDER BY settlement_date DESC
    LIMIT 1
    """
    
    data = self.query_bigquery(query)
    if data:
        current = data[0]['systemSellPrice']
        previous = data[0]['prev_price']
        change_pct = abs((current - previous) / previous * 100)
        
        if change_pct > 20:
            logging.warning(f"⚠️ Large price movement: {change_pct:.1f}%")
```

---

## 📅 Running on Schedule (Cron)

To run dashboard update on a schedule (e.g., every hour):

```bash
# Edit crontab
crontab -e

# Add line (runs every hour at :00)
0 * * * * cd /Users/georgemajor/GB\ Power\ Market\ JJ && ./.venv/bin/python automated_iris_dashboard.py >> automated_dashboard.log 2>&1
```

Or for continuous updates, just use:

```bash
./start_automated_dashboard.sh
```

---

## 🎉 Benefits

### Before (Manual)
- ❌ Manually query BigQuery
- ❌ Copy/paste into Google Sheets
- ❌ Create charts by hand
- ❌ Repeat every time you want fresh data
- ❌ Time-consuming and error-prone

### After (Automated)
- ✅ Automatic BigQuery queries
- ✅ Auto-update Google Sheets
- ✅ Charts created automatically
- ✅ Runs continuously (every 5 min)
- ✅ Always up-to-date, zero effort!

---

## 📊 Example Output

After running, you'll see:

```
🚀 Starting Dashboard Update
============================================================
📊 Updating System Prices...
✅ Query returned 96 rows
✅ Updated sheet 'System Prices' with 96 rows
✅ Created chart on 'System Prices'
⚡ Updating Grid Frequency...
✅ Query returned 180 rows
✅ Updated sheet 'Grid Frequency' with 180 rows
✅ Created chart on 'Grid Frequency'
🔥 Updating Fuel Generation...
✅ Query returned 12 rows
✅ Updated sheet 'Fuel Generation' with 12 rows
✅ Created chart on 'Fuel Generation'
📋 Updating Recent Activity...
✅ Updated sheet 'Recent Activity' with 4 rows
============================================================
✅ Dashboard updated in 8.3s
📊 View at: https://docs.google.com/spreadsheets/d/1ABC...XYZ
============================================================
```

---

## 🚀 Next Steps

1. **Start the dashboard**: `./start_automated_dashboard.sh`
2. **Open Google Sheets**: Find "IRIS Real-Time Dashboard"
3. **Enjoy live data**: Charts update every 5 minutes automatically!
4. **Customize**: Add your own dashboards and charts
5. **Share**: Share the Google Sheet with your team

---

**No more manual work! Set it and forget it!** 🎉

---

## 📞 Quick Commands Reference

```bash
# Start dashboard
./start_automated_dashboard.sh

# Check logs
tail -f automated_dashboard.log

# Check status
ps aux | grep automated_iris_dashboard

# Stop dashboard
kill $(cat automated_dashboard.pid)

# Run once (no loop)
./.venv/bin/python automated_iris_dashboard.py

# Custom interval (2 minutes)
./.venv/bin/python automated_iris_dashboard.py --loop --interval 120
```

---

**Created:** October 30, 2025  
**Status:** Ready to use!  
**Maintenance:** Zero - fully automated! 🚀
