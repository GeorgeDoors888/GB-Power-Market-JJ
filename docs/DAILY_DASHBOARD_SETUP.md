# Daily Dashboard with Auto-Updating Charts

**Purpose**: Automated dashboard showing daily settlement period (SP) data from 00:00 (SP1) for System Sell Price, demand, generation, and interconnector imports.

**Last Updated**: November 23, 2025

---

## Overview

This system creates a self-updating dashboard with professional charts showing:
- **System Sell Price (SSP)** & **System Buy Price (SBP)** - Market prices (£/MWh)
- **GB Demand** - Total electricity demand (MW)
- **Total Generation** - All generation sources combined (MW)
- **Interconnector Imports** - Total imports from EU/Ireland (MW)
- **System Frequency** - Grid frequency stability (Hz)

**Data Granularity**: Every settlement period (48 per day) for the last 30 days

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  BIGQUERY (Data Source)                                       │
│  • bmrs_costs (SSP/SBP imbalance prices, SSP=SBP since 2015)  │
│  • bmrs_indod (Demand outturn)                                │
│  • bmrs_fuelinst (Generation + IC imports)                    │
│  • bmrs_freq (Frequency)                                      │
│  Combined: Historical + _iris (real-time) tables              │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────────────────────┐
│  PYTHON UPDATER (daily_dashboard_auto_updater.py)             │
│  • Runs every 30 minutes (cron)                               │
│  • Queries last 30 days from BigQuery                         │
│  • Writes to Google Sheets: Daily_Chart_Data                  │
│  • Updates today's KPIs in Dashboard                          │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────────────────────┐
│  GOOGLE SHEETS (Daily_Chart_Data)                             │
│  Columns:                                                     │
│  A: Date | B: SP | C: SSP | D: SBP | E: Demand |              │
│  F: Generation | G: IC Import | H: Frequency                  │
└────────────────┬─────────────────────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────────────────────┐
│  APPS SCRIPT (daily_dashboard_charts.gs)                      │
│  • Auto-triggers every 30 minutes                             │
│  • Deletes old chart sheets                                   │
│  • Creates 4 new chart sheets:                                │
│    - Chart_Prices (SSP & SBP line chart)                      │
│    - Chart_Demand_Gen (Demand vs Generation)                  │
│    - Chart_IC_Import (Interconnector imports area chart)      │
│    - Chart_Frequency (Grid frequency line chart)              │
└──────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
GB Power Market JJ/
├── daily_dashboard_auto_updater.py    # Python updater (30 min cron)
├── daily_dashboard_charts.gs          # Apps Script chart builder
└── DAILY_DASHBOARD_SETUP.md          # This file
```

---

## Setup Instructions

### Step 1: Deploy Python Updater

**On UpCloud Server** (or Dell for local testing):

```bash
# 1. Upload script
scp daily_dashboard_auto_updater.py root@94.237.55.234:/root/GB-Power-Market-JJ/

# 2. Test manually
ssh root@94.237.55.234
cd /root/GB-Power-Market-JJ
python3 daily_dashboard_auto_updater.py

# Expected output:
# ✅ Connected to BigQuery and Google Sheets
# 📊 Fetching data from 2025-10-24 to 2025-11-23
# ✅ Retrieved 1440 settlement periods across 30 days
# ✅ Updated Daily_Chart_Data with 1440 rows
# ✅ Updated today's KPIs in Dashboard
# ✅ UPDATE COMPLETE
```

### Step 2: Add Cron Job (UpCloud)

```bash
crontab -e

# Add this line (runs every 30 minutes)
*/30 * * * * cd /root/GB-Power-Market-JJ && /usr/bin/python3 daily_dashboard_auto_updater.py >> logs/daily_dashboard.log 2>&1
```

### Step 3: Install Apps Script Charts

1. **Open Google Sheets Dashboard**:
   - https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

2. **Open Apps Script Editor**:
   - Click `Extensions` → `Apps Script`

3. **Create New Script File**:
   - Click `+` next to Files
   - Name it `DailyDashboardCharts`
   - Copy entire contents of `daily_dashboard_charts.gs`
   - Paste into editor
   - Click `Save` (💾)

4. **Run Initial Setup**:
   ```
   - Select function: setupAutoRefreshTrigger
   - Click "Run" ▶️
   - Authorize the script (first time only)
   - Should see: "✅ Trigger Installed"
   ```

5. **Create Initial Charts**:
   ```
   - Select function: refreshAllCharts
   - Click "Run" ▶️
   - Wait ~10 seconds
   - Check new tabs: Chart_Prices, Chart_Demand_Gen, etc.
   ```

---

## Google Sheets Structure

### New Sheets Created

1. **Daily_Chart_Data** (Python writes here)
   ```
   Row 1: Headers
   Rows 2+: Data (Date, SP, SSP, SBP, Demand, Generation, IC Import, Frequency)
   Updates: Every 30 minutes via Python
   ```

2. **Chart_Prices** (Apps Script creates)
   - Line chart: SSP (green) and SBP (red)
   - X-axis: Date & Settlement Period
   - Y-axis: Price (£/MWh)

3. **Chart_Demand_Gen** (Apps Script creates)
   - Line chart: Demand (yellow) and Generation (blue)
   - X-axis: Date & Settlement Period
   - Y-axis: Power (MW)

4. **Chart_IC_Import** (Apps Script creates)
   - Area chart: Total imports (purple)
   - X-axis: Date & Settlement Period
   - Y-axis: Import (MW)

5. **Chart_Frequency** (Apps Script creates)
   - Line chart: Frequency (orange)
   - X-axis: Date & Settlement Period
   - Y-axis: Frequency (Hz, range 49.5-50.5)

### Dashboard KPIs (Rows 18-29)

Python updates these every 30 minutes with structured market summary:

```
Row 18: 📊 MARKET SUMMARY (header, centered, blue background)
Row 19: (blank spacing)
Row 20: TODAY'S AVERAGES | 30-DAY STATISTICS
Row 21: (blank spacing)
Row 22: 💰 Avg SSP: £XX.XX/MWh | 📈 30d Avg SSP: £XX.XX/MWh
Row 23: 💰 Avg SBP: £XX.XX/MWh | 📈 30d Avg SBP: £XX.XX/MWh
Row 24: ⚡ Avg Demand: XX,XXX MW | 📊 Max SSP (30d): £XX.XX/MWh
Row 25: ⚡ Avg Generation: XX,XXX MW | 📊 Min SSP (30d): £XX.XX/MWh
Row 26: 🔌 Avg IC Import: X,XXX MW
Row 27: 📊 Avg Frequency: 50.XXX Hz
Row 28: (blank spacing)
Row 29: 📈 View charts in: Chart_Prices | Chart_Demand_Gen | Chart_IC_Import | Chart_Frequency
```

**Layout**: 
- **Columns A-C**: Today's metrics (live updates)
- **Columns D-H**: 30-day statistics (trends)
- **Professional formatting**: Headers, spacing, color coding

---

## Usage

### Manual Chart Refresh

If you want to refresh charts manually (without waiting for trigger):

1. Open Google Sheets
2. Click `📊 Dashboard Charts` menu (top)
3. Click `🔄 Refresh All Charts`
4. Wait ~10 seconds
5. Charts updated!

### Viewing Charts

1. Click chart sheet tabs: `Chart_Prices`, `Chart_Demand_Gen`, etc.
2. Each chart is full-screen, professional quality
3. Hover over data points for exact values
4. Charts auto-update every 30 minutes

### Date Range

- **Default**: Last 30 days
- **To change**: Edit `daily_dashboard_auto_updater.py`:
  ```python
  # Line 189
  df = fetch_daily_data(bq_client, days_back=30)  # Change 30 to desired days
  ```

---

## Troubleshooting

### Python Script Not Running

**Check cron job**:
```bash
ssh root@94.237.55.234
crontab -l | grep daily_dashboard
tail -f logs/daily_dashboard.log
```

**Run manually**:
```bash
cd /root/GB-Power-Market-JJ
python3 daily_dashboard_auto_updater.py
```

**Common Issues**:
- ❌ `ModuleNotFoundError: pandas` → `pip3 install pandas`
- ❌ `Credentials not found` → Check `inner-cinema-credentials.json` exists
- ❌ `Table not found` → Verify BigQuery project ID is `inner-cinema-476211-u9`

### Charts Not Updating

**Check trigger**:
1. Open Apps Script Editor
2. Click `⏰` (Triggers) icon (left sidebar)
3. Should see: `autoRefreshCharts` runs every 30 minutes

**If missing trigger**:
1. Run function `setupAutoRefreshTrigger` again
2. Authorize if prompted

**Manual refresh**:
```
Dashboard Charts menu → Refresh All Charts
```

### Missing Data

**Check data sheet**:
```
1. Open sheet: Daily_Chart_Data
2. Should have 1440+ rows (30 days × 48 SP/day)
3. Check column headers: Date, SP, SSP (£/MWh), etc.
```

**If empty or wrong data**:
```bash
# Re-run Python script manually
python3 daily_dashboard_auto_updater.py
```

### Charts Show Old Data

**Force refresh**:
1. Python updates data → Wait 2 minutes
2. Apps Script detects new data → Rebuilds charts
3. If still old: Manual refresh via menu

---

## Monitoring

### Check UpCloud Cron Logs

```bash
ssh root@94.237.55.234
tail -f /root/GB-Power-Market-JJ/logs/daily_dashboard.log
```

**Expected output every 30 min**:
```
2025-11-23 12:00:02 - ✅ Retrieved 1440 settlement periods
2025-11-23 12:00:15 - ✅ Updated Daily_Chart_Data with 1440 rows
2025-11-23 12:00:18 - ✅ UPDATE COMPLETE
```

### Check Apps Script Execution Log

1. Open Apps Script Editor
2. Click `⚙️` (Executions) icon (left sidebar)
3. Should see `autoRefreshCharts` runs every 30 min
4. Status: ✅ Completed (green checkmark)

### Dashboard Health Check

### Quick verification**:
```
1. Open Dashboard sheet
2. Check rows 18-29 (MARKET SUMMARY section)
3. Values should be recent (within 30 min)
4. Today's metrics in columns A-C, 30-day stats in columns D-H
5. Open Chart_Prices tab
6. Last data point should be today's date
```

---

## Performance

### Resource Usage

**Python Script**:
- Runtime: ~15-30 seconds
- BigQuery: ~50-100 MB data scanned
- Memory: ~200 MB peak
- Network: ~2 MB download

**Apps Script**:
- Runtime: ~5-10 seconds
- Quota: ~30 executions/day (well within free tier)

**Google Sheets**:
- Data rows: ~1,500 (30 days × 48 SP)
- Charts: 4 embedded charts
- Load time: <2 seconds

### Cost

**All components are FREE** (within quotas):
- BigQuery: <1 GB/month queries (free tier: 1 TB/month)
- Apps Script: ~50 executions/day (free tier: 90 min runtime/day)
- Google Sheets: Unlimited (part of Google Workspace)

---

## Advanced Customization

### Change Chart Colors

Edit `daily_dashboard_charts.gs`:

```javascript
// Line 147 (Price chart)
.setOption('series', {
  0: {color: '#YOUR_COLOR_SSP', lineWidth: 2},
  1: {color: '#YOUR_COLOR_SBP', lineWidth: 2}
})
```

### Add More Charts

1. Add new function in `daily_dashboard_charts.gs`:
```javascript
function createCustomChart() {
  const ss = SpreadsheetApp.getActive();
  const dataSheet = ss.getSheetByName(CHART_DATA_SHEET);
  
  // Your chart code here
}
```

2. Call it in `refreshAllCharts()`:
```javascript
createCustomChart();
```

### Change Update Frequency

**Python (cron)**:
```bash
# Every 15 minutes
*/15 * * * * cd /root/GB-Power-Market-JJ && python3 daily_dashboard_auto_updater.py

# Every hour
0 * * * * cd /root/GB-Power-Market-JJ && python3 daily_dashboard_auto_updater.py
```

**Apps Script (trigger)**:
```javascript
// Edit setupAutoRefreshTrigger() function
ScriptApp.newTrigger('autoRefreshCharts')
  .timeBased()
  .everyMinutes(15)  // Change from 30 to 15
  .create();
```

---

## Integration with Existing System

This dashboard **complements** existing dashboards:

| Dashboard | Purpose | Update Freq |
|-----------|---------|-------------|
| **Main Dashboard** (rows 1-70) | Live fuel breakdown, outages | 5-10 min |
| **Live_Raw_Gen** sheet | Real-time generation by SP | 5 min |
| **Daily_Chart_Data** (NEW) | Historical SP data + charts | 30 min |

**No conflicts**: Uses separate sheets and row ranges.

---

## Support

**Documentation**: `DAILY_DASHBOARD_SETUP.md` (this file)  
**Main Docs**: `DUAL_SERVER_ARCHITECTURE.md`, `PROJECT_CONFIGURATION.md`  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ

---

## Changelog

**v1.0 - November 23, 2025**
- Initial release
- 30-day rolling window
- 4 auto-updating charts
- Integration with existing dashboard
- Cron + Apps Script automation

---

*Last Updated: November 23, 2025*  
*Status: ✅ Production Ready*
