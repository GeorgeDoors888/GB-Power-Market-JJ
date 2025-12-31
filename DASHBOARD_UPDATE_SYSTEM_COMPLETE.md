# Google Sheets Dashboard - Update System Documentation

**Dashboard URL**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit  
**Sheet Name**: "Live Dashboard v2"  
**Last Updated**: December 30, 2025

---

## 📋 Current Dashboard Sections

### **Live Dashboard v2** Layout (102 rows × 27 columns)

#### **Rows 1-12: Header & Market Overview**
- A1: Main title "⚡ GB LIVE ENERGY VIEW"
- A2: Timestamp (auto-updated by cron)
- A3: IRIS status indicator
- A5-K6: Market Overview KPIs (6 metrics with sparklines)

#### **Rows 13-22: Core Data (3-Column Layout)**
| Section | Columns | Content |
|---------|---------|---------|
| **Generation Mix** | A-D | 10 fuel types with GW, share %, bar charts |
| **Interconnectors** | G-H | 10 connections with flow trends |
| **Market Dynamics** | K-N | 10 KPIs with values, descriptions |

#### **Rows 25-35: Wind Forecasting (NEW)**
- **A26-A33**: Wind change alerts (farms with significant forecast errors)
  - Shows: Farm, Current Wind, Forecast Wind, Change %, Direction Δ, Lead Time, Asset
  - Example data: Robin Rigg 60% change, Beatrice 57%, etc.

#### **Rows 36-52: Outages**
- G25-J35: Active outages (15 units, 5,738 MW offline)

#### **Rows 53-82: Enhanced Wind Analysis (NEWLY ADDED)**
- **A53-A62**: Per-Farm Forecast Accuracy (Top 8 worst performers)
  - Currently shows "No data available"
- **A63-A72**: Revenue Impact Analysis (Last 7 days)
  - **£1,879,649,000 total lost revenue identified**
  - Shows worst 20 settlement periods with error severity
- **A73-A82**: Hour-of-Day Accuracy Pattern (30-day analysis)
  - 57 time periods analyzed
  - Identifies worst hours: Wed 01:00 (67.0%), Thu 00:00 (67.0%)

---

## 🤖 Automated Update System (Cron Jobs)

### **Primary Dashboard Updaters**

#### 1. **Fast Updates** (Every 5 minutes)
```bash
*/5 * * * * cd /home/george/GB-Power-Market-JJ && \
  /usr/bin/python3 update_all_dashboard_sections_fast.py >> logs/dashboard_auto_update.log 2>&1
```
**Script**: `update_all_dashboard_sections_fast.py`  
**Updates**: Generation mix, demand, interconnectors, wind, outages, KPIs  
**Speed**: 298x faster than gspread (uses direct Sheets API v4)

#### 2. **Comprehensive Updates** (Every 10 minutes, staggered)
```bash
1,11,21,31,41,51 * * * * cd /home/george/GB-Power-Market-JJ && \
  /usr/bin/python3 update_live_metrics.py >> logs/unified_update.log 2>&1
```
**Script**: `update_live_metrics.py`  
**Updates**:
- Data_Hidden sheet: Fuel generation, interconnectors, market metrics (48 settlement periods)
- Live Dashboard v2: IRIS freshness, KPIs, market metrics, spreads
- Sparkline formulas with dynamic scaling (LET functions)

---

## 🔄 Data Pipeline Cron Jobs

### **IRIS Real-Time Data** (Every 15 minutes)
```bash
*/15 * * * * cd /home/george/GB-Power-Market-JJ && \
  /usr/bin/python3 auto_ingest_realtime.py >> logs/realtime_ingest.log 2>&1
*/15 * * * * cd /home/george/GB-Power-Market-JJ && \
  /usr/bin/python3 auto_ingest_windfor.py >> logs/windfor_ingest.log 2>&1
*/15 * * * * cd /home/george/GB-Power-Market-JJ && \
  /usr/bin/python3 auto_ingest_indgen.py >> logs/indgen_ingest.log 2>&1
*/15 * * * * cd /home/george/GB-Power-Market-JJ && \
  /usr/bin/python3 build_publication_table_current.py >> logs/publication_table.log 2>&1
```
**Purpose**: Fetch latest IRIS data from AlmaLinux server → BigQuery → Dashboard

### **Wind Forecasting Data** (Every 15 minutes)
```bash
*/15 * * * * cd /home/george/GB-Power-Market-JJ && \
  python3 download_realtime_wind.py >> logs/realtime_wind.log 2>&1
```
**Purpose**: Download Open-Meteo wind data for forecasting models

### **Weather Data Downloads** (Daily/Regular)
```bash
# ERA5 weather data (daily at 3am)
0 3 * * * cd /home/george/GB-Power-Market-JJ && \
  python3 download_era5_weather_incremental.py >> logs/era5_weather_daily.log 2>&1

# GFS forecasts (every 6 hours)
15 */6 * * * cd /home/george/GB-Power-Market-JJ && \
  python3 download_gfs_forecasts.py >> logs/gfs_forecasts.log 2>&1

# REMIT messages (daily at 2am)
0 2 * * * cd /home/george/GB-Power-Market-JJ && \
  python3 download_remit_messages_incremental.py >> logs/remit_messages.log 2>&1

# Data freshness check (hourly)
0 * * * * cd /home/george/GB-Power-Market-JJ && \
  python3 check_data_freshness.py >> logs/data_freshness.log 2>&1
```

### **Market Data Ingestion**
```bash
# BOD data (bid-offer) - every 30 minutes
*/30 * * * * cd /home/george/GB-Power-Market-JJ && \
  /usr/bin/python3 auto_ingest_bod.py >> logs/bod_ingest.log 2>&1

# Settlement data - every 2 hours
25 */2 * * * cd /home/george/GB-Power-Market-JJ && \
  /usr/bin/python3 ingest_bm_settlement_data.py --recent 1 >> logs/bm_settlement.log 2>&1

# Cost backfill - twice hourly
15,45 * * * * cd /home/george/GB-Power-Market-JJ && \
  /usr/bin/python3 auto_backfill_costs_daily.py >> logs/costs_backfill.log 2>&1
```

### **Daily Pipelines**
```bash
# Full data pipeline - daily at 3am
0 3 * * * cd /home/george/GB-Power-Market-JJ && \
  /usr/bin/python3 daily_data_pipeline.py >> logs/daily_pipeline.log 2>&1

# BM revenue history - daily at 5am
0 5 * * * /home/george/GB-Power-Market-JJ/auto_update_bm_revenue_full_history.sh

# BM KPI pipeline - daily at 5:30am
30 5 * * * cd /home/george/GB-Power-Market-JJ && \
  python3 parallel_bm_kpi_pipeline.py --days 7
```

### **Monitoring & Health Checks**
```bash
# DISBSAD freshness monitor - every 15 minutes
8,23,38,53 * * * * /usr/bin/python3 /home/george/GB-Power-Market-JJ/monitor_disbsad_freshness.py >> \
  logs/disbsad_monitor.log 2>&1

# Resource monitoring - every 5 minutes
*/5 * * * * /usr/bin/python3 /home/george/GB-Power-Market-JJ/monitor_dell_resources.py >> \
  logs/resource_monitor.log 2>&1
```

---

## 🎯 What's MISSING: Wind Traffic Light System

### **Your Original Request (Not Yet Implemented)**

You wanted a **traffic light alert system** with:

1. **🔴🟡🟢 Conditional Formatting**
   - Red: 60%+ wind forecast error (Critical)
   - Orange: 40-60% error (Warning)
   - Yellow: 20-40% error (Caution)
   - Green: <20% error (Stable)

2. **Sparkline Graphs**
   - 24-hour wind speed trends per farm
   - Visual mini-charts in dashboard cells

3. **Ice Risk Alerts** (❄️)
   - Temperature: -3°C to +2°C
   - Humidity: >92%
   - Precipitation: >0 mm
   - **Status**: Waiting for ERA5 weather data (currently downloading)

4. **Grid-Level Summary**
   - Total offshore wind GW
   - Top 5 wind sites by current output
   - Aggregate capacity factor

5. **Embedded Charts**
   - Proper Google Charts objects (not just formulas)
   - Interactive visualizations

### **Why It Wasn't Completed**

1. **Data Deployed, Visuals Missing**
   - Rows A26-A82 have RAW DATA but no conditional formatting
   - Script `create_wind_analysis_dashboard_enhanced.py` failed on formatting:
     ```
     ERROR - Failed to apply enhanced formatting: <HttpError 400... No grid with id: 0>
     ```

2. **API Timeout Issues**
   - Google Sheets API hanging on `.get()` calls
   - Script `apply_traffic_light_formatting.py` created but won't execute

3. **Sparklines Not Added**
   - Require `=SPARKLINE()` formulas in cells
   - Need historical wind speed data queries

4. **Ice Alerts Blocked**
   - ERA5 weather data still downloading (background process)
   - Table `era5_weather_icing` not fully populated

---

## 📊 Current Data Status

### **Wind Forecast Error Data (✅ AVAILABLE)**
- Table: `wind_forecast_error_sp` (settlement period level)
- Table: `wind_forecast_error_daily` (daily aggregates)
- Coverage: 2023-2025
- Metrics: WAPE, MAPE, Bias, RMSE, Ramp misses

### **Revenue Impact (✅ CALCULATED)**
- **£1.88 billion** lost over 7 days due to forecast errors
- Worst period: Dec 30, 2025 SP 1 (69.7% error, £862,158 impact)
- Data in dashboard rows A63-A72

### **Per-Farm Accuracy (❌ NO DATA)**
- Requires proportional forecast allocation
- Current method insufficient
- Shows "No data available" in A53-A62

### **Ice Risk (⏳ DOWNLOADING)**
- ERA5 weather download in progress
- Script: `download_era5_weather_fixed.py` (background)
- Log: `era5_fixed_download.log`
- Status: Check with `ps -ef | grep download_era5`

---

## 🔧 Key Scripts Reference

### **Dashboard Update Scripts**
1. `update_live_metrics.py` - Comprehensive updater (every 10 min)
2. `update_all_dashboard_sections_fast.py` - Fast updater (every 5 min)
3. `create_wind_analysis_dashboard_enhanced.py` - Wind sections creator (MANUAL)
4. `apply_traffic_light_formatting.py` - Conditional formatting (BROKEN)

### **Wind Forecasting Scripts**
1. `create_wind_analysis_dashboard.py` - Original wind dashboard (612 lines)
2. `realtime_wind_forecasting.py` - Multi-hour predictions
3. `wind_drop_alerts.py` - Alert monitoring system
4. `add_wind_forecasting_dashboard.py` - Sheets integration

### **Data Download Scripts**
1. `download_realtime_wind.py` - Open-Meteo wind (every 15 min)
2. `download_era5_weather_fixed.py` - ERA5 weather (daily, RUNNING)
3. `download_gfs_forecasts.py` - GFS forecasts (every 6 hours)
4. `download_remit_messages_incremental.py` - REMIT data (daily)

---

## 📍 Next Steps to Complete Traffic Lights

### **Option 1: Fix Python API (Recommended)**
```bash
# Debug and retry formatting
python3 apply_traffic_light_formatting.py
```
**Issue**: Google Sheets API timing out on `.get()` calls  
**Fix**: May need network troubleshooting or retry logic

### **Option 2: Apps Script (Fastest)**
Create Apps Script directly in Google Sheets to apply conditional formatting:

```javascript
function applyWindTrafficLights() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet()
    .getSheetByName("Live Dashboard v2");
  
  // Wind change alerts (A27-A33, Column D = Change %)
  var changeRange = sheet.getRange("D27:D33");
  
  // Critical: 60%+ (RED)
  var criticalRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberGreaterThanOrEqualTo(60)
    .setBackground("#FF4444")
    .setBold(true)
    .setRanges([changeRange])
    .build();
    
  // Warning: 40-60% (ORANGE)
  var warningRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberBetween(40, 59)
    .setBackground("#FFA500")
    .setBold(true)
    .setRanges([changeRange])
    .build();
    
  // Caution: 20-40% (YELLOW)
  var cautionRule = SpreadsheetApp.newConditionalFormatRule()
    .whenNumberBetween(20, 39)
    .setBackground("#FFEB3B")
    .setRanges([changeRange])
    .build();
  
  var rules = sheet.getConditionalFormatRules();
  rules.push(criticalRule, warningRule, cautionRule);
  sheet.setConditionalFormatRules(rules);
  
  Logger.log("✅ Traffic lights applied");
}
```

### **Option 3: Manual Formatting (Temporary)**
1. Open dashboard: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
2. Select range D27:D33 (Change % column)
3. Format → Conditional formatting
4. Add rules:
   - ≥60: Red background
   - 40-59: Orange background
   - 20-39: Yellow background

---

## 📖 Related Documentation

- `WIND_FORECASTING_COMPLETE_IMPLEMENTATION.md` - Full wind forecasting project status
- `live_dashboard_v2_layout_analysis.md` - Detailed layout documentation
- `ERA5_INTEGRATION_RESULTS.md` - Weather data integration
- `COPILOT_INSTRUCTIONS_GAP_ANALYSIS.md` - Configuration reference

---

**Status**: Dashboard updates automated ✅ | Traffic lights missing ❌ | Ice alerts pending data ⏳

**Estimated Time to Complete**:
- Apps Script approach: 15 minutes
- Fix Python API: 1-2 hours (debugging required)
- Ice alerts: 2-4 hours (waiting for ERA5 download)
