# Python Dashboard Implementation - Complete Guide

## ✅ What's Been Implemented

### 1. **Dashboard Layout Builder** (`build_dashboard_python.py`)
Replaces Apps Script `setupDashboard()` and `formatBESSEnhanced()`

**Functions**:
- `setup_dashboard_layout()` - Creates complete Dashboard sheet with:
  - Header section (rows 1-5) with title and timestamp
  - KPI bar (F9:H11) for VLP Revenue, Wholesale Avg, Market Vol
  - Fuel Mix / Interconnectors table (A9:E21)
  - Outages section (A24:H25)
  - ESO Interventions (A37:F38)
  - All formatting (colors, fonts, backgrounds)

- `build_dashboard_charts()` - Documents 7 chart specifications:
  1. 💰 Revenue by Service (Column chart)
  2. 📈 BM Price Trend (Line chart)
  3. ⚡ BESS KPIs (Line chart - SoC/RTE/Cycles)
  4. 💹 Net Profit vs Revenue (Combo chart)
  5. 🔋 Battery Degradation & RUL (Dual-axis line)
  6. 💷 Revenue per Cycle (Line chart)
  7. 💹 Net Profit per MWh (Line chart)
  
  **Note**: Chart creation requires Google Sheets API v4 (not supported by gspread).
  Charts must be created via Apps Script or manually.

- `refresh_dashboard()` - Updates timestamp

- `create_named_ranges()` - Documents required named ranges

**Usage**:
```bash
python3 build_dashboard_python.py
```

---

### 2. **BESS Data Populator** (`populate_bess_enhanced.py`)
Replaces Python script from your examples

**Functions**:
- Fetches market data from BigQuery (prices, frequency)
- Calculates battery dispatch optimization (charge/discharge decisions)
- Computes 6-stream revenue breakdown:
  - Balancing Mechanism (40%)
  - Energy Arbitrage (25%)
  - Frequency Response (15%)
  - DUoS Avoidance (10%)
  - Capacity Market (7%)
  - Wholesale Trading (3%)
- Writes 337 rows of timeseries data to BESS!A61+
- Updates KPIs (T61:U67) and Revenue Stack (W61:Y67)

**Data Sources**:
- Tries to fetch real VLP data from BigQuery BOD/BOALF tables
- Falls back to industry-standard estimates when no data available
- Uses direct BigQuery Python client (no Railway dependency)

**Usage**:
```bash
python3 populate_bess_enhanced.py
```

---

### 3. **Complete Refresh Pipeline** (`refresh_dashboard_complete.py`)
Orchestrates full dashboard update

**Process**:
1. Run `populate_bess_enhanced.py` → Populate BESS data with calculations
2. Run `build_dashboard_python.py` → Build dashboard layout and timestamp

**Usage**:
```bash
python3 refresh_dashboard_complete.py
```

---

### 4. **Webhook Server** (`dno_webhook_server.py`)
Flask server with 4 endpoints

**Endpoints**:
- `POST /trigger-dno-lookup` - DNO data lookup
- `POST /generate-hh-profile` - Half-hourly profile generation
- `POST /refresh-dashboard` - **NEW**: Triggers complete dashboard refresh
- `GET /health` - Health check

**Usage**:
```bash
# Start server (runs in foreground)
python3 dno_webhook_server.py

# Or with ngrok for external access
ngrok http 5001
```

**Trigger refresh**:
```bash
curl -X POST http://localhost:5001/refresh-dashboard
```

---

## ⚠️ Limitations - What's NOT in Python

### 1. **Chart Creation**
**Why**: `gspread` library doesn't support chart creation. Google Sheets API v4 is required.

**Workaround**:
- Use Apps Script `buildDashboard()` function for charts
- Or create charts manually using specifications from `build_dashboard_python.py` output
- Or implement Google Sheets API v4 directly (more complex)

**Apps Script Code** (add to `Code.gs`):
```javascript
function buildDashboardCharts() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const dash = ss.getSheetByName("Dashboard");
  const bess = ss.getSheetByName("BESS");
  
  // Remove old charts
  dash.getCharts().forEach(c => dash.removeChart(c));
  
  // Chart 1: Revenue by Service
  dash.insertChart(
    dash.newChart()
      .setChartType(Charts.ChartType.COLUMN)
      .addRange(bess.getRange("A1:D"))
      .setPosition(13, 1, 0, 0)
      .setOption("title", "💰 Revenue by Service (£)")
      .build()
  );
  
  // ... (add other 6 charts)
}
```

---

### 2. **Named Ranges**
**Why**: `gspread` doesn't support named range creation. Requires Sheets API v4.

**Required Named Ranges**:
```
Live_Generation → Dashboard!B10
Live_Demand → Dashboard!C10
Live_Price → Dashboard!D10
Live_SSP → Dashboard!E10
Live_SBP → Dashboard!F10
VLP_Data → BESS!D:D
Market_Prices → Dashboard!C:C
```

**Manual Creation**:
1. Open sheet → Data → Named ranges
2. Add each range manually using names above

---

### 3. **Conditional Formatting Rules**
**Why**: `gspread_formatting` has limited conditional formatting support

**Workaround**:
- Create manually via Google Sheets UI
- Or use Apps Script `setConditionalFormatRules()`

**Example** (Apps Script):
```javascript
const rules = dash.getConditionalFormatRules();
rules.push(SpreadsheetApp.newConditionalFormatRule()
  .whenTextContains("← Import")
  .setFontColor("#2E7D32").setBold(true)
  .setRanges([dash.getRange("E10:E21")]).build());
dash.setConditionalFormatRules(rules);
```

---

## 🚀 Deployment Guide

### Option A: Python-Only (Recommended for Data Updates)
```bash
# One-time setup
pip3 install --user gspread gspread-formatting google-cloud-bigquery requests

# Regular dashboard refresh
python3 refresh_dashboard_complete.py

# Or individual steps
python3 populate_bess_enhanced.py  # Just data
python3 build_dashboard_python.py   # Just layout
```

### Option B: Python + Apps Script (Full Automation)
```bash
# 1. Run Python for data + layout
python3 refresh_dashboard_complete.py

# 2. Open Google Sheets → Extensions → Apps Script
# 3. Add buildDashboardCharts() function (see above)
# 4. Run buildDashboardCharts() from Apps Script editor
```

### Option C: Webhook-Triggered (Production)
```bash
# 1. Start webhook server
python3 dno_webhook_server.py

# 2. (Optional) Expose via ngrok
ngrok http 5001

# 3. Trigger from Apps Script button
function refreshDashboard() {
  const url = 'http://localhost:5001/refresh-dashboard';  // Or ngrok URL
  UrlFetchApp.fetch(url, { method: 'post' });
  SpreadsheetApp.getActive().toast("✅ Refresh triggered", "Dashboard", 3);
}
```

---

## 📊 Current Status

| Feature | Python | Apps Script | Status |
|---------|--------|-------------|--------|
| Dashboard layout | ✅ | ✅ | Both work |
| BESS data population | ✅ | ❌ | Python only |
| Header formatting | ✅ | ✅ | Both work |
| KPI formulas | ✅ | ✅ | Both work |
| Charts | ❌ | ✅ | Apps Script only |
| Named ranges | ❌ | ✅ | Manual/Apps Script |
| Conditional formatting | ⚠️ | ✅ | Limited in Python |
| Webhook refresh | ✅ | ❌ | Python only |
| Timestamp update | ✅ | ✅ | Both work |

**Legend**: ✅ Fully implemented | ⚠️ Partially implemented | ❌ Not implemented

---

## 🔧 Next Steps

1. **Create charts**: Use Apps Script `buildDashboardCharts()` or create manually
2. **Add named ranges**: Data → Named ranges (manual one-time setup)
3. **Test refresh**: Run `python3 refresh_dashboard_complete.py`
4. **Schedule updates**: Add to cron for automatic refreshes
5. **Monitor logs**: Check output for any VLP data fetch errors

---

## 📝 Why Python Instead of Apps Script?

**Advantages**:
1. **Direct BigQuery access** - No Railway proxy needed
2. **Better error handling** - Full Python debugging tools
3. **Version control** - Code in git, not locked in Google
4. **Testing** - Can run locally without sheet permissions
5. **Reusability** - Functions can be imported by other scripts
6. **Performance** - BigQuery Python client is faster than HTTP API

**Trade-offs**:
1. Charts require Apps Script or Sheets API v4
2. Named ranges require manual setup or API v4
3. No native "button" UI (use webhook instead)

---

## 🌐 Sheet URL
https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit

---

*Last Updated: December 5, 2025*
