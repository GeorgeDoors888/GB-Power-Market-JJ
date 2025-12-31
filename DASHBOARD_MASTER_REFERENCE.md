# GB Power Market Dashboard - Complete Technical Reference

**Dashboard URL**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit?usp=sharing  
**Apps Script ID**: `1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980`  
**API**: Google Sheets API v4  
**Sheet Name**: "Live Dashboard v2"  
**Last Updated**: December 30, 2025

---

## 🏗️ System Architecture

### **Hybrid Update System: Python + Apps Script**

```
┌─────────────────────────────────────────────────────────────┐
│                    GOOGLE SHEETS DASHBOARD                  │
│  (1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA)           │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌─────────────┐   ┌──────────────┐
│   PYTHON    │   │ APPS SCRIPT  │
│  UPDATERS   │   │   (Manual)   │
└──────┬──────┘   └──────┬───────┘
       │                 │
       │                 │
       ▼                 ▼
┌─────────────────────────────────┐
│         BIGQUERY DATA           │
│   (inner-cinema-476211-u9)      │
│      uk_energy_prod             │
└─────────────────────────────────┘
```

---

## 📊 Dashboard Layout Map

### **Live Dashboard v2** (102 rows × 27 columns)

| Rows | Columns | Section | Updated By | Frequency |
|------|---------|---------|------------|-----------|
| 1-4 | A-AA | Header & Status | Python | Every 10 min |
| 5-6 | A-K | Market Overview KPIs | Python | Every 10 min |
| 10-12 | A-N | Section Headers | Static | - |
| 13-22 | A-D | Generation Mix | Python | Every 5 min |
| 13-22 | E-F | *Reserved* | - | - |
| 13-22 | G-H | Interconnectors | Python + Apps Script | Mixed |
| 13-22 | K-N | Market Dynamics KPIs | Python | Every 10 min |
| 25-35 | G-J | Active Outages | Apps Script | Manual trigger |
| 26-33 | A-G | **Wind Forecast Alerts** | Python | Manual/Pending |
| 53-62 | A-G | **Per-Farm Accuracy** | Python | Manual/Pending |
| 63-72 | A-G | **Revenue Impact** | Python | Manual/Deployed |
| 73-82 | A-G | **Hour-of-Day Patterns** | Python | Manual/Deployed |

---

## 🤖 Python Update Scripts (Cron Automated)

### **1. Fast Updates** (Every 5 minutes)
```bash
*/5 * * * * cd /home/george/GB-Power-Market-JJ && \
  /usr/bin/python3 update_all_dashboard_sections_fast.py >> logs/dashboard_auto_update.log 2>&1
```

**Script**: `update_all_dashboard_sections_fast.py`  
**Technology**: Direct Google Sheets API v4 (298x faster than gspread)  
**Updates**:
- Generation Mix (A13-D22)
- Demand metrics
- Interconnectors (G13-G22 names only)
- Wind output
- Basic KPIs

**Key Functions**:
```python
from fast_sheets_api import FastSheetsAPI
sheets_api = FastSheetsAPI('inner-cinema-credentials.json')

def update_generation_mix():
    query = f"""
    SELECT fuelType, generation
    FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst_iris`
    ORDER BY publishTime DESC
    LIMIT 50
    """
    # Updates A13-D22 with fuel types, GW, share %, bar charts
```

---

### **2. Comprehensive Updates** (Every 10 minutes, staggered)
```bash
1,11,21,31,41,51 * * * * cd /home/george/GB-Power-Market-JJ && \
  /usr/bin/python3 update_live_metrics.py >> logs/unified_update.log 2>&1
```

**Script**: `update_live_metrics.py` (2599 lines)  
**Technology**: Google Sheets API v4 + BigQuery  
**Updates**:
- **Data_Hidden sheet**: 48 settlement periods of historical data
- **Live Dashboard v2**: All dynamic sparklines, KPIs, spreads
- **IRIS status indicator** (A3)
- **Market Overview KPIs** (A5-K6)
- **Interconnector sparklines** (H13-H22) - Time-series with win/loss coloring

**Critical Sparkline Function**:
```python
def generate_gs_sparkline_formula(data, options, add_spacing=True):
    """
    Generates native Google Sheets =SPARKLINE() formula with correctly formatted options.
    Shows only current settlement periods (1 to current), not padded to 48.
    
    VERIFIED WORKING VERSION (from test_sparkline_formula.py)
    """
    clean_data = [item if isinstance(item, (int, float)) else 0 for item in data]
    
    # Disable spacing for line charts (looks choppy)
    charttype = options.get('charttype', 'column')
    if charttype == 'line':
        add_spacing = False
    
    # Build options string: {"option1","value1";"option2","value2"}
    option_pairs = []
    for key, value in options.items():
        if isinstance(value, str):
            option_pairs.append(f'"{key}","{value}"')
        else:
            option_pairs.append(f'"{key}",{value}')
    
    options_string = ";".join(option_pairs)
    
    # Final formula: =SPARKLINE({data},{options})
    formula = f'=SPARKLINE({{{",".join(map(str, clean_data))}}},{{{options_string}}})'
    return formula
```

**Sparkline Color Scheme**:
```python
SPARKLINE_COLORS = {
    # Fuel Types
    'WIND': "#00A86B",      # Emerald Green
    'NUCLEAR': "#FFD700",   # Gold
    'CCGT': "#FF6347",      # Tomato Red
    'BIOMASS': "#228B22",   # Forest Green
    # Interconnectors
    '🇫🇷 ElecLink': "#0055A4",
    '🇮🇪 East-West': "#169B62",
    '🇫🇷 IFA': "#0055A4",
    # ... (full list in update_live_metrics.py lines 28-50)
}
```

---

### **3. Dynamic LET Sparklines** (Auto-scaling)
```python
def generate_gs_sparkline_with_let(data, color, charttype="column", negcolor=None):
    """
    Generates =LET() formula with SPARKLINE that auto-scales using MIN/MAX with 15% padding.
    Better visual scaling than hardcoded ymin/ymax values.
    """
    clean_data = [float(item) if isinstance(item, (int, float)) and item is not None else 0 
                  for item in data]
    data_str = ",".join(map(str, clean_data))
    
    # LET formula with 15% padding
    formula = f'''=IFERROR(LET(r,{{{data_str}}},x,FILTER(r,(r<>0)*(r<>"")),lo,MIN(x),hi,MAX(x),span,hi-lo,pad,MAX(1,span*0.15),SPARKLINE(IF((r=0)+(r=""),NA(),r),{{"charttype","{charttype}";"axis",true;"axiscolor","#999";"color","{color}"'''
    
    if negcolor:
        formula += f''';"negcolor","{negcolor}"'''
    
    formula += ''';"empty","ignore";"ymin",lo-pad;"ymax",hi+pad}})),"")'''
    return formula
```

---

## 📱 Apps Script Components

### **Location**: `/home/george/GB-Power-Market-JJ/clasp-gb-live-2/src/`

### **Key Files**:

#### **1. Data.gs** (FIXED - DO NOT MODIFY)
```javascript
// Line 207-222: Display interconnectors
// IMPORTANT: Only write to column G (names)
// Python update_live_metrics.py manages sparklines in column H

function displayInterconnectors(sheet, data) {
  // v2 Layout:
  // Col G: Connection Name
  // Col H: Sparkline Graphic (DO NOT OVERWRITE - managed by Python)
  // Col I: Current Flow Value (MW)
  
  // Only write Names to G - Python script manages sparklines in H
  const v2InterData = data.interconnectors.map(row => [row[0]]); // G only
  sheet.getRange(13, 7, v2InterData.length, 1).setValues(v2InterData);
  
  // Note: Sparklines in column H are managed by Python script update_live_metrics.py
  // which creates time-series sparklines with proper positive/negative coloring
  // DO NOT write to column H here to avoid overwriting them
}
```

**⚠️ CRITICAL**: Never add sparkline code to Data.gs column H. Python owns this column.

#### **2. Dashboard.gs**
- Sheet layout setup
- Cell merging for headers
- Initial formatting

#### **3. KPISparklines.gs**
- Row 4 KPI sparklines only (not interconnectors)
- Fuel generation mini-charts
- Market overview visualizations

#### **4. Charts.gs**
- Chart object management
- Not used for sparklines (uses formulas instead)

#### **5. Menu.gs**
- Custom menu items
- Manual refresh buttons

#### **6. Code.gs**
- Menu initialization
- Version checking

---

## 🔄 Data Pipeline Architecture

### **Data Flow**:
```
ELEXON BMRS API
     ↓
IRIS Stream (AlmaLinux 94.237.55.234)
     ↓
BigQuery Ingestion (every 15 min)
     ↓
BigQuery Tables (uk_energy_prod dataset)
     ↓
Python Scripts Query (every 5-10 min)
     ↓
Google Sheets API v4
     ↓
Live Dashboard v2 Sheet
```

### **BigQuery Tables** (Primary):
- `bmrs_fuelinst_iris` - Fuel generation (real-time)
- `bmrs_windfor_iris` - Wind forecasts (real-time)
- `bmrs_freq` - Grid frequency
- `bmrs_costs` - Imbalance prices
- `bmrs_mid` - Market index
- `demand_outturn` - System demand
- `wind_forecast_error_sp` - Wind forecast errors
- `wind_forecast_error_daily` - Daily wind accuracy

### **Cron Jobs Summary**:
| Frequency | Script | Purpose |
|-----------|--------|---------|
| Every 5 min | `update_all_dashboard_sections_fast.py` | Fast UI updates |
| Every 10 min | `update_live_metrics.py` | Comprehensive + sparklines |
| Every 15 min | `auto_ingest_realtime.py` | IRIS data download |
| Every 15 min | `auto_ingest_windfor.py` | Wind forecast ingest |
| Every 15 min | `download_realtime_wind.py` | Open-Meteo wind data |
| Every 6 hours | `download_gfs_forecasts.py` | GFS weather forecasts |
| Daily 3am | `download_era5_weather_incremental.py` | ERA5 weather data |
| Daily 2am | `download_remit_messages_incremental.py` | REMIT notifications |

---

## 🎨 Sparkline Implementation Guide

### **Formula Syntax** (VERIFIED WORKING)

#### **Column Chart** (Fuel Generation):
```javascript
=SPARKLINE({10,20,30,25,35},{"charttype","column";"color","#4682B4"})
```

#### **Win/Loss Chart** (Interconnectors):
```javascript
=SPARKLINE({100,-50,200,-100,150},{"charttype","winloss";"color","#34A853";"negcolor","#EA4335"})
```

#### **Line Chart** (Market Prices):
```javascript
=SPARKLINE({80,85,82,90,88},{"charttype","line";"color","#DA70D6";"linewidth",2})
```

### **Common Mistakes to Avoid**:

❌ **WRONG** (Flat array for options):
```javascript
=SPARKLINE({data},{"a","b","c","d"})
```

✅ **CORRECT** (Two-column array):
```javascript
=SPARKLINE({data},{"a","b";"c","d"})
```

❌ **WRONG** (Using semicolon between data and options):
```javascript
=SPARKLINE({data};{options})  // English locale needs comma
```

✅ **CORRECT** (Comma between data and options):
```javascript
=SPARKLINE({data},{options})
```

---

## 🚨 Wind Forecasting Dashboard (INCOMPLETE)

### **Status**: Data deployed, visuals missing

#### **Deployed Sections** (Manual scripts):
- ✅ A26-A33: Wind change alerts (data only)
- ✅ A53-A62: Per-farm accuracy (no data available)
- ✅ A63-A72: Revenue impact (£1.88B calculated)
- ✅ A73-A82: Hour-of-day patterns (57 periods analyzed)

#### **Missing Components**:
1. **Traffic Light Conditional Formatting** (🔴🟡🟢)
   - Script created: `apply_traffic_light_formatting.py`
   - Status: API timeout issues
   - Workaround: Use Apps Script (see code below)

2. **Sparkline Graphs** (24h wind trends)
   - Not implemented
   - Need: `=SPARKLINE()` formulas with historical wind speed data

3. **Ice Risk Alerts** (❄️)
   - Blocked: ERA5 weather data still downloading
   - Script: `download_era5_weather_fixed.py` (background process)

4. **Grid Summary Section**
   - Not implemented
   - Needs: Total offshore GW, top 5 farms, capacity factor

#### **Apps Script Solution for Traffic Lights**:
```javascript
function applyWindTrafficLights() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet()
    .getSheetByName("Live Dashboard v2");
  
  // Wind change % column (D27:D33)
  var range = sheet.getRange("D27:D33");
  
  var rules = [
    // 🔴 Critical (60%+)
    SpreadsheetApp.newConditionalFormatRule()
      .whenNumberGreaterThanOrEqualTo(60)
      .setBackground("#FF4444")
      .setBold(true)
      .setRanges([range])
      .build(),
    
    // 🟡 Warning (40-60%)
    SpreadsheetApp.newConditionalFormatRule()
      .whenNumberBetween(40, 59)
      .setBackground("#FFA500")
      .setBold(true)
      .setRanges([range])
      .build(),
    
    // 🟡 Caution (20-40%)
    SpreadsheetApp.newConditionalFormatRule()
      .whenNumberBetween(20, 39)
      .setBackground("#FFEB3B")
      .setRanges([range])
      .build()
  ];
  
  var existingRules = sheet.getConditionalFormatRules();
  sheet.setConditionalFormatRules(existingRules.concat(rules));
  
  Logger.log("✅ Traffic lights applied to wind alerts");
}
```

**Deploy**: Extensions → Apps Script → Paste function → Run

---

## 🔧 Development & Debugging

### **Check Current Dashboard State**:
```bash
cd /home/george/GB-Power-Market-JJ

# View logs
tail -50 logs/dashboard_auto_update.log  # Fast updates
tail -50 logs/unified_update.log         # Comprehensive updates

# Force manual update
python3 update_live_metrics.py 2>&1 | tail -30
```

### **Verify Apps Script Code**:
```bash
# View local copy of Data.gs
cat clasp-gb-live-2/src/Data.gs | grep -A 20 "Display interconnectors"

# Should NOT have: sheet.getRange(13, 8, ...)
# Should say: "DO NOT OVERWRITE - managed by Python"
```

### **Test Sparkline Formula**:
```python
# Test sparkline generation
cd /home/george/GB-Power-Market-JJ
python3 << 'EOF'
from update_live_metrics import generate_gs_sparkline_formula

data = [100, -50, 200, -100, 150]
options = {
    "charttype": "winloss",
    "color": "#34A853",
    "negcolor": "#EA4335"
}

formula = generate_gs_sparkline_formula(data, options)
print("Generated formula:")
print(formula)
print("\nCopy this to a Google Sheet cell to test")
EOF
```

### **Check Cron Status**:
```bash
# View active cron jobs
crontab -l | grep -E "(dashboard|update)" | head -10

# Check if processes are running
ps aux | grep -E "(update_live_metrics|update_all_dashboard)" | grep -v grep
```

---

## 📖 Documentation Reference

### **Key Files to Read**:
1. **DASHBOARD_UPDATE_SYSTEM_COMPLETE.md** - This file, master reference
2. **dashboard_sparkline_enhancement_summary.md** - Sparkline implementation history
3. **INTERCONNECTOR_SPARKLINE_FIX_GUIDE.md** - Apps Script fix for column H
4. **live_dashboard_v2_layout_analysis.md** - Detailed layout map
5. **WIND_FORECASTING_COMPLETE_IMPLEMENTATION.md** - Wind forecasting project status

### **Related Scripts**:
- `update_live_metrics.py` - Main comprehensive updater (2599 lines)
- `update_all_dashboard_sections_fast.py` - Fast updater (399 lines)
- `create_wind_analysis_dashboard_enhanced.py` - Wind sections creator (612 lines)
- `apply_traffic_light_formatting.py` - Conditional formatting (334 lines)

---

## 🎯 Quick Reference Commands

### **Refresh Dashboard Manually**:
```bash
cd /home/george/GB-Power-Market-JJ

# Fast update (5-10 seconds)
python3 update_all_dashboard_sections_fast.py

# Full update with sparklines (30-60 seconds)
python3 update_live_metrics.py
```

### **Deploy Apps Script Changes**:
```bash
cd /home/george/GB-Power-Market-JJ/clasp-gb-live-2

# Push to Apps Script
clasp push

# Or deploy manually via web UI:
# https://script.google.com/home/projects/1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980
```

### **Check Data Downloads**:
```bash
# ERA5 weather (for ice alerts)
ps -ef | grep download_era5 | grep -v grep
tail -50 era5_fixed_download.log

# GFS forecasts
ps -ef | grep download_gfs | grep -v grep

# REMIT messages
ps -ef | grep download_remit | grep -v grep
```

---

## ⚠️ Critical Notes

### **DO NOT**:
1. ❌ Add sparkline code to Data.gs column H (Python owns it)
2. ❌ Use gspread library (298x slower than direct API v4)
3. ❌ Run `update_live_metrics.py` more than once per 10 minutes (API limits)
4. ❌ Modify sparkline formulas in dashboard manually (will be overwritten)

### **ALWAYS**:
1. ✅ Test sparkline formulas in isolation before deploying
2. ✅ Check logs after cron runs
3. ✅ Verify API credentials: `inner-cinema-credentials.json`
4. ✅ Use correct project ID: `inner-cinema-476211-u9` (NOT jibber-jabber-knowledge)

---

## 🆘 Troubleshooting

### **Problem: Sparklines not showing**
```bash
# Check if Python script is running
tail -20 logs/unified_update.log

# Verify sparkline syntax
python3 -c "from update_live_metrics import generate_gs_sparkline_formula; print(generate_gs_sparkline_formula([1,2,3], {'charttype':'column','color':'blue'}))"
```

### **Problem: Apps Script overwriting column H**
```bash
# Check Data.gs for incorrect code
grep -n "getRange(13, 8" clasp-gb-live-2/src/Data.gs

# If found, follow INTERCONNECTOR_SPARKLINE_FIX_GUIDE.md
```

### **Problem: API timeout**
- Cause: Google Sheets API rate limiting or network issues
- Solution: Wait 60 seconds and retry
- Alternative: Use Apps Script for formatting

---

**Last Updated**: December 30, 2025  
**Maintained By**: AI Coding Agent  
**Status**: ✅ Production (automated updates running)  
**Traffic Lights**: ⏳ Pending (Apps Script deployment needed)
