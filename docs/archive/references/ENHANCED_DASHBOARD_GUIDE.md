# 📊 Enhanced Dashboard Setup - Complete Guide

## 🎯 Overview
Your Dashboard sheet now features:
- **📈 Professional KPI Layout** - Current generation, prices, renewable %
- **🎨 Color-Coded Sections** - Easy visual navigation
- **📊 Interactive Charts** - 4 auto-updating visualizations
- **🔄 Auto-Refresh** - Updates every 5 minutes via cron

---

## ✅ What Was Created

### 1. Enhanced Data Layout (`enhance_dashboard_layout.py`)
```
Dashboard Structure:
┌─────────────────────────────────────────────┐
│  🔋 GB POWER MARKET - LIVE DASHBOARD        │ ← Header
│  Last Updated: 2025-11-09 14:31:06 | SP 29 │ ← Timestamp
├─────────────────────────────────────────────┤
│  📊 CURRENT METRICS    💰 MARKET PRICES     │ ← KPI Section
│  • Total Generation    • Sell Price         │
│  • Renewable Share     • Renewable MW       │
├─────────────────────────────────────────────┤
│  ⚡ GENERATION BY FUEL TYPE                  │ ← Data Table
│  💨 Wind: 8,743 MW (42.3%) 🟢              │
│  ⚛️ Nuclear: 3,892 MW (18.8%) 🟢           │
│  🔥 Gas: 5,234 MW (25.3%) 🟢               │
│  ...                                        │
├─────────────────────────────────────────────┤
│  📈 24-HOUR GENERATION TREND (MW)            │ ← Chart Data
│  SP 1:  Wind | Solar | Nuclear | Gas | Total│
│  SP 2:  ...                                 │
│  ...                                        │
└─────────────────────────────────────────────┘
```

**Features**:
- ✅ Current generation by fuel type with emojis
- ✅ Percentage calculations
- ✅ Status indicators (🟢 Active / 🔴 Offline)
- ✅ Last 24 hours trend data for charting
- ✅ Color-coded sections (blue headers, highlight KPIs)

### 2. Professional Formatting (`format_dashboard.py`)
- **Headers**: Blue background (#2B4D99), white text, 16pt bold
- **KPIs**: Light blue/yellow backgrounds for visual separation
- **Tables**: Gray headers with borders
- **Column Widths**: Optimized (250px for labels, 150px for values)

### 3. Interactive Charts (`dashboard_charts.gs`)
Four auto-updating charts:

#### Chart 1: ⚡ 24-Hour Generation Trend (Line Chart)
- **Location**: Column H, Row 1
- **Data**: Wind, Solar, Nuclear, Gas, Total generation
- **Purpose**: Track generation patterns over last 24 hours

#### Chart 2: 🥧 Current Generation Mix (Pie Chart)
- **Location**: Column Q, Row 1
- **Data**: All fuel types with MW values
- **Purpose**: Visual breakdown of current generation sources

#### Chart 3: 📊 Stacked Generation by Source (Area Chart)
- **Location**: Column H, Row 26
- **Data**: Wind, Solar, Nuclear, Gas (stacked)
- **Purpose**: Show contribution of each source over time

#### Chart 4: 📊 Top Generation Sources (Column Chart)
- **Location**: Column Q, Row 26
- **Data**: Top 15 fuel types by MW
- **Purpose**: Quick comparison of generation capacity

---

## 🚀 Installation Steps

### Step 1: Install Google Apps Script for Charts

1. **Open Your Spreadsheet**:
   ```
   https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
   ```

2. **Open Apps Script Editor**:
   - Extensions → Apps Script

3. **Replace Code.gs Content**:
   - Delete existing code
   - Paste contents from `dashboard_charts.gs`
   - Save (💾 icon or Ctrl+S)

4. **Run Chart Creator**:
   - Select function: `createDashboardCharts`
   - Click Run ▶️
   - Grant permissions when prompted
   - Wait for "✅ Dashboard Charts Created!" alert

5. **Access via Menu**:
   - Return to spreadsheet
   - New menu appears: `📊 Dashboard`
   - Options:
     - 🔄 Create/Update Charts
     - 🗑️ Remove All Charts

### Step 2: Verify Current Setup

Dashboard should now show:
```bash
# Check current data
cd "/Users/georgemajor/GB Power Market JJ"
python3 -c "
import pickle, gspread
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)
gc = gspread.authorize(creds)
ss = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
dashboard = ss.worksheet('Dashboard')
print('Dashboard last update:', dashboard.acell('A2').value)
print('Total rows:', dashboard.row_count)
print('Total cols:', dashboard.col_count)
"
```

---

## 🔄 Auto-Refresh Setup

### Current Auto-Refresh (Already Installed)
```bash
# Check cron status
crontab -l | grep dashboard

# Output should show:
*/5 * * * * cd '/Users/georgemajor/GB Power Market JJ' && /usr/local/bin/python3 realtime_dashboard_updater.py >> logs/dashboard_updater.log 2>&1
```

**Note**: The existing cron job updates `Live_Raw_Gen` sheet. To also refresh the enhanced Dashboard layout:

### Add Enhanced Dashboard Refresh

1. **Test Manual Refresh**:
   ```bash
   cd "/Users/georgemajor/GB Power Market JJ"
   python3 enhance_dashboard_layout.py
   ```

2. **Install Enhanced Cron** (runs every 15 minutes):
   ```bash
   crontab -e
   ```

   Add line:
   ```
   */15 * * * * cd '/Users/georgemajor/GB Power Market JJ' && /usr/local/bin/python3 enhance_dashboard_layout.py >> logs/dashboard_enhance.log 2>&1
   ```

3. **Verify Cron**:
   ```bash
   crontab -l
   ```

4. **Monitor Logs**:
   ```bash
   tail -f logs/dashboard_enhance.log
   ```

---

## 📊 Usage Guide

### View Dashboard
```
🔗 https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit#gid=0
```

### Manual Data Refresh
```bash
# Update layout + data
python3 enhance_dashboard_layout.py

# Reformat only (no data change)
python3 format_dashboard.py
```

### Update Charts
Two methods:

**Method 1: Via Spreadsheet Menu**
1. Open spreadsheet
2. Click `📊 Dashboard` menu
3. Click `🔄 Create/Update Charts`

**Method 2: Via Apps Script Editor**
1. Extensions → Apps Script
2. Select `createDashboardCharts`
3. Click Run ▶️

---

## 🎨 Customization

### Change Color Scheme

Edit `format_dashboard.py`:
```python
# Header colors
dashboard.format('A1:F1', {
    'backgroundColor': {'red': 0.2, 'green': 0.3, 'blue': 0.6},  # Change RGB values
    'textFormat': {
        'foregroundColor': {'red': 1, 'green': 1, 'blue': 1},
        'fontSize': 16,
        'bold': True
    }
})
```

### Add More Charts

Edit `dashboard_charts.gs`:
```javascript
// Example: Add gauge chart for renewable percentage
const gaugeChart = dashboard.newChart()
  .setChartType(Charts.ChartType.GAUGE)
  .addRange(dashboard.getRange(6, 3, 1, 1)) // Renewable % cell
  .setPosition(50, 8, 0, 0) // Row 50, Column H
  .setOption('title', '♻️ Renewable Generation %')
  .setOption('greenFrom', 40)
  .setOption('greenTo', 100)
  .setOption('yellowFrom', 20)
  .setOption('yellowTo', 40)
  .setOption('redFrom', 0)
  .setOption('redTo', 20)
  .build();

dashboard.insertChart(gaugeChart);
```

### Modify Data Range

Edit `enhance_dashboard_layout.py`:
```python
# Change trend data period (currently 24 hours)
trend_query = f"""
...
WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)  # Change to 2 days
...
```

---

## 🔧 Troubleshooting

### Issue: Charts Not Appearing

**Solution 1: Check Data Range**
```bash
python3 -c "
import pickle, gspread
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)
gc = gspread.authorize(creds)
ss = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
dashboard = ss.worksheet('Dashboard')
all_values = dashboard.get_all_values()
for i, row in enumerate(all_values[:50]):
    if row and '24-HOUR' in str(row[0]):
        print(f'Trend data starts at row {i+1}')
        break
"
```

**Solution 2: Re-run Chart Creator**
1. Open spreadsheet
2. `📊 Dashboard` menu → `🗑️ Remove All Charts`
3. `📊 Dashboard` menu → `🔄 Create/Update Charts`

### Issue: Formatting Lost

**Solution**: Re-apply formatting
```bash
python3 format_dashboard.py
```

### Issue: Old Data Showing

**Solution**: Check cron logs
```bash
# Check last update
tail -20 logs/dashboard_enhance.log

# Force immediate update
python3 enhance_dashboard_layout.py

# Verify cron is running
ps aux | grep cron
```

### Issue: BigQuery Errors

**Solution**: Check credentials
```bash
# Test BigQuery connection
python3 -c "
from google.cloud import bigquery
from google.oauth2 import service_account
creds = service_account.Credentials.from_service_account_file('inner-cinema-credentials.json')
client = bigquery.Client(project='inner-cinema-476211-u9', credentials=creds, location='US')
print('✅ BigQuery connected')
"
```

---

## 📁 Files Created

| File | Purpose | Usage |
|------|---------|-------|
| `enhance_dashboard_layout.py` | Create enhanced layout + data | Manual: `python3 enhance_dashboard_layout.py` |
| `format_dashboard.py` | Apply formatting only | Manual: `python3 format_dashboard.py` |
| `dashboard_charts.gs` | Google Apps Script for charts | Install in Extensions → Apps Script |
| `ENHANCED_DASHBOARD_GUIDE.md` | This documentation | Reference guide |

---

## 🎯 Next Steps

### Recommended Enhancements

1. **Add Price Chart**:
   - Query `bmrs_mid_iris` for historical prices
   - Create line chart showing price trends
   - Position at Row 50, Column H

2. **Add Battery VLP Tracking**:
   - Query `bmrs_indgen_iris` for VLP units (FBPGM002, FFSEN005)
   - Create stacked bar chart showing charge/discharge
   - Highlight revenue opportunities

3. **Add Interconnector Flow**:
   - Query interconnector data
   - Create horizontal bar chart
   - Show import/export by link

4. **Add Frequency Monitor**:
   - Query `bmrs_freq` for grid frequency
   - Create gauge chart (49.8-50.2 Hz range)
   - Color-code: green (49.9-50.1), yellow (49.8-49.9, 50.1-50.2), red (outside)

5. **Add Weather Correlation**:
   - Integrate weather API data
   - Show wind speed vs wind generation
   - Solar irradiance vs solar generation

---

## 📚 Related Documentation

- **Architecture**: `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`
- **Data Reference**: `STOP_DATA_ARCHITECTURE_REFERENCE.md`
- **Configuration**: `PROJECT_CONFIGURATION.md`
- **Auto-Refresh**: `DASHBOARD_AUTO_REFRESH_COMPLETE.md`
- **Apps Script**: `APPS_SCRIPT_DEPLOYMENT_GUIDE.md`

---

## 🆘 Support

**Test Commands**:
```bash
# 1. Check Python environment
python3 --version

# 2. Test Google Sheets access
python3 -c "import pickle, gspread; print('✅ Sheets OK')"

# 3. Test BigQuery access
python3 -c "from google.cloud import bigquery; print('✅ BigQuery OK')"

# 4. View current dashboard
python3 -c "
import pickle, gspread
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)
gc = gspread.authorize(creds)
ss = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8')
dashboard = ss.worksheet('Dashboard')
print(dashboard.acell('A1').value)
print(dashboard.acell('A2').value)
print(dashboard.acell('A5').value)
"
```

**Contact**: george@upowerenergy.uk  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ

---

*Last Updated: November 9, 2025*  
*Status: ✅ Operational - Auto-updating every 5 minutes*
