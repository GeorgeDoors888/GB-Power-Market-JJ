# Wind Dashboard - Live Data Reader

**Created**: December 30, 2025
**Script**: `create_wind_analysis_dashboard_live.py`
**Purpose**: Read wind data DIRECTLY from Google Sheets dashboard instead of BigQuery cache

---

## 🎯 Key Difference from Original Script

### Original Script (`create_wind_analysis_dashboard.py`)
```python
# Reads from BigQuery cached views
def get_enhanced_wind_metrics(bq_client):
    query = """
    SELECT * FROM `uk_energy_prod.wind_forecast_error_daily`
    """
```

### New Live Script (`create_wind_analysis_dashboard_live.py`)
```python
# Reads DIRECTLY from Google Sheets Live Dashboard v2
def read_wind_data_from_sheets(sheets_service):
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range='Live Dashboard v2!A13:D22'  # Generation Mix section
    ).execute()
```

---

## 📊 Data Sources

| Data Type | Source | Update Frequency |
|-----------|--------|------------------|
| **Current Wind Output** | Google Sheets (A13-D22) | Every 5 min (Python cron) |
| Weather Alerts | BigQuery GFS forecasts | Every 6 hours |
| Forecast Errors | BigQuery views (NESO vs B1610) | Daily |
| Hourly Errors | BigQuery settlement periods | Real-time |

---

## 🔧 How It Works

### Step 1: Read Live Wind Data from Dashboard
```python
# Reads Generation Mix section (rows 13-22)
# Format: Column A = Fuel Type, Column B = MW value, Column C = "MW" unit
result = sheets_service.spreadsheets().values().get(
    spreadsheetId='1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA',
    range='Live Dashboard v2!A13:D22'
).execute()

# Example data returned:
# Row 13: ['🌬️ WIND', '4789', 'MW']
# Row 14: ['⚛️ NUCLEAR', '3982', 'MW']
```

**Parsing Logic**:
- Find row where Column A contains "WIND"
- Parse Column B as MW value (string number)
- Convert to GW: `gw = mw / 1000`

### Step 2: Weather Alerts from GFS
```python
# Still uses BigQuery for 6-hour GFS forecasts
query = """
SELECT
    farm_name,
    forecast_horizon_hours,
    wind_speed_100m,
    wind_direction_100m
FROM `uk_energy_prod.gfs_forecast_weather`
WHERE CAST(forecast_horizon_hours AS INT64) BETWEEN 1 AND 6
"""
```

**Alert Thresholds**:
- 🔴 CRITICAL: ≥25% wind change or ≥60° direction shift
- 🟡 WARNING: 10-25% wind change or 30-60° direction shift
- 🟢 STABLE: <10% wind change and <30° direction shift

### Step 3: Forecast Error Metrics
```python
# Uses BigQuery views (NESO forecasts vs B1610 actual)
daily_query = """
SELECT
    settlement_date,
    avg_actual_mw,
    avg_forecast_mw,
    wape_percent,
    bias_mw
FROM `uk_energy_prod.wind_forecast_error_daily`
WHERE settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
"""
```

---

## 📍 Dashboard Layout (Rows 25-48)

```
A25-G25: Header "💨 WIND FORECAST & WEATHER ALERTS (LIVE DATA)"
A26-G26: Current wind (LIVE) + Weather alert status

A27-D27: 📊 Forecast Error (WAPE) + 7-day sparkline
A28-D28: 📉 Forecast Bias + 7-day sparkline
A29-D29: ⚡ Actual vs Forecast + 7-day sparkline
A30-D30: ⚠️ Large Ramp Misses count

A31-G31: Header "🎯 MOST AFFECTED FARMS"
A32-G36: List of 5 farms at risk (from weather alerts)

A37-E37: Header "📈 RECENT HOURLY FORECAST ERRORS"
A38-E48: Last 10 settlement periods with actual/forecast/error
```

---

## 🚀 Running the Script

### Manual Run
```bash
cd /home/george/GB-Power-Market-JJ
python3 create_wind_analysis_dashboard_live.py
```

### Expected Output
```
======================================================================
💨 WIND ANALYSIS DASHBOARD - LIVE DATA VERSION
======================================================================
📊 Reading wind data DIRECTLY from Live Dashboard v2
🔄 No BigQuery cache used for current wind output
======================================================================

2025-12-30 14:11:19,416 - INFO - ✅ Read from dashboard: Wind = 4789 MW (4.79 GW)
2025-12-30 14:11:22,928 - INFO -   🟢 Status: STABLE - No significant weather changes detected
2025-12-30 14:11:29,189 - INFO -   WAPE: 40.0%
2025-12-30 14:11:29,900 - INFO - ✅ Dashboard updated: 132 cells

======================================================================
✅ DASHBOARD CREATED SUCCESSFULLY (LIVE DATA)
======================================================================
View at: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
Wind data: READ DIRECTLY from dashboard (no cache)
```

### Add to Cron (Optional)
```bash
# Refresh wind dashboard every 15 minutes
crontab -e

# Add this line:
*/15 * * * * cd /home/george/GB-Power-Market-JJ && python3 create_wind_analysis_dashboard_live.py >> logs/wind_dashboard_live.log 2>&1
```

---

## 🔍 Verification

### Check Wind Value is Live
```bash
# Read from dashboard
python3 << 'EOF'
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
sheets = build('sheets', 'v4', credentials=creds, cache_discovery=False)

result = sheets.spreadsheets().values().get(
    spreadsheetId='1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA',
    range='Live Dashboard v2!A13:C13'
).execute()

row = result['values'][0]
print(f"Fuel: {row[0]}")
print(f"MW: {row[1]}")
print(f"Unit: {row[2]}")
EOF
```

**Expected Output**:
```
Fuel: 🌬️ WIND
MW: 4789
Unit: MW
```

### Compare to BigQuery
```bash
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

query = '''
SELECT generation, publishTime
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris\`
WHERE fuelType = 'WIND'
ORDER BY publishTime DESC
LIMIT 1
'''

df = client.query(query).to_dataframe()
print(f'BigQuery wind: {df[\"generation\"][0]:.0f} MW')
print(f'Published: {df[\"publishTime\"][0]}')
"
```

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE SHEETS LIVE DASHBOARD                 │
│  (1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA)               │
│                                                                 │
│  Rows 13-22: Generation Mix                                    │
│    Row 13: 🌬️ WIND | 4789 | MW                               │
│                      ▲                                          │
└──────────────────────┼──────────────────────────────────────────┘
                       │
                       │ Google Sheets API (READ)
                       │
          ┌────────────┴──────────────┐
          │                           │
          ▼                           ▼
┌──────────────────┐        ┌─────────────────────┐
│  LIVE WIND DATA  │        │  BIGQUERY SOURCES   │
│  (Current MW)    │        │  (Historical Data)  │
└──────────────────┘        └─────────────────────┘
          │                           │
          │                           │
          │                           ▼
          │                  ┌────────────────────┐
          │                  │ GFS Weather        │
          │                  │ Forecast Errors    │
          │                  │ Hourly Metrics     │
          │                  └────────────────────┘
          │                           │
          └───────────┬───────────────┘
                      │
                      ▼
          ┌──────────────────────────┐
          │ create_wind_analysis_    │
          │ dashboard_live.py        │
          └──────────────────────────┘
                      │
                      │ Google Sheets API (WRITE)
                      │
                      ▼
          ┌──────────────────────────┐
          │  Dashboard Rows 25-48    │
          │  (Wind Analysis Section) │
          └──────────────────────────┘
```

---

## 🆚 When to Use Each Script

### Use `create_wind_analysis_dashboard_live.py` when:
- ✅ Want most recent wind output (updated every 5 min by cron)
- ✅ Need to verify dashboard automation is working
- ✅ Troubleshooting discrepancies between dashboard and BigQuery
- ✅ Creating reports with "as displayed" data

### Use `create_wind_analysis_dashboard.py` when:
- ✅ Want historical analysis (BigQuery has full archive)
- ✅ Need complex queries across multiple tables
- ✅ Dashboard data temporarily unavailable
- ✅ Running batch analysis scripts

---

## ⚠️ Important Notes

1. **Live data accuracy depends on dashboard updaters**:
   - Fast updater: Every 5 minutes (`update_all_dashboard_sections_fast.py`)
   - Comprehensive updater: Every 10 minutes (`update_live_metrics.py`)
   - If cron jobs stopped, live data will be stale

2. **API Rate Limits**:
   - Google Sheets API: 100 requests/100 seconds/user
   - This script makes 3 requests per run (Generation Mix + KPIs + Write)
   - Safe to run every 5-15 minutes

3. **Data Freshness Indicator**:
   - Dashboard has IRIS status in A3
   - Check timestamp to verify data recency

4. **Fallback Behavior**:
   - If live wind data read fails, script continues with forecast errors only
   - Weather alerts and historical metrics still populated from BigQuery

---

## 🔧 Troubleshooting

### Problem: "Could not read live wind data"
```bash
# Check if dashboard updaters are running
ps aux | grep -E "(update_live_metrics|update_all_dashboard)"

# Check logs
tail -50 logs/dashboard_auto_update.log
tail -50 logs/unified_update.log

# Manual update
python3 update_live_metrics.py
```

### Problem: "Wind value is stale"
```bash
# Check IRIS status
python3 -c "
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/spreadsheets']
)
sheets = build('sheets', 'v4', credentials=creds, cache_discovery=False)

result = sheets.spreadsheets().values().get(
    spreadsheetId='1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA',
    range='Live Dashboard v2!A3'
).execute()

print(f'IRIS Status: {result[\"values\"][0][0]}')
"
```

### Problem: "Weather alerts not showing"
```bash
# Check GFS forecast data exists
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

query = '''
SELECT COUNT(*) as cnt, MAX(forecast_time) as latest
FROM \`inner-cinema-476211-u9.uk_energy_prod.gfs_forecast_weather\`
'''

df = client.query(query).to_dataframe()
print(f'GFS records: {int(df[\"cnt\"][0]):,}')
print(f'Latest forecast: {df[\"latest\"][0]}')
"
```

---

## 📖 Related Documentation

- **DASHBOARD_MASTER_REFERENCE.md** - Complete dashboard system architecture
- **WIND_FORECASTING_COMPLETE_IMPLEMENTATION.md** - Wind forecasting project status
- **update_live_metrics.py** - Main dashboard updater script (2599 lines)
- **update_all_dashboard_sections_fast.py** - Fast updater (399 lines)

---

**Last Updated**: December 30, 2025
**Status**: ✅ Production Ready
**Tested**: Wind reading verified (4,789 MW = 4.79 GW)
