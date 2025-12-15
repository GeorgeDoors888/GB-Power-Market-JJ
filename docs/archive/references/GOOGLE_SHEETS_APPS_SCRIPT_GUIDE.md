# Google Sheets Apps Script Installation Guide

## 📋 Overview

This guide shows you how to install the **GB Power Market Live Dashboard** Apps Script into your Google Sheet.

**What it does:**
- Pulls live balancing mechanism data from BigQuery via Vercel proxy
- Auto-refreshes every 5 minutes
- Creates interactive charts
- Writes data to multiple tabs for analysis

**Sheet:** https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit

---

## 🚀 Installation Steps

### Step 1: Open Apps Script Editor

1. Open your Google Sheet: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
2. Click **Extensions** → **Apps Script**
3. A new tab will open with the Apps Script editor

### Step 2: Replace Code

1. Delete any existing code in `Code.gs`
2. Open the file: `google_sheets_dashboard.gs` (in your workspace)
3. **Copy the entire contents** of that file
4. **Paste** into the Apps Script editor (replacing everything)
5. Click the **Save** icon (💾) or press `Cmd+S` (Mac) / `Ctrl+S` (Windows)

### Step 3: Authorize the Script

1. In the Apps Script editor, click **Run** → Select `testHealthCheck`
2. You'll see a dialog: **"Authorization required"**
3. Click **Review permissions**
4. Choose your Google account
5. Click **Advanced** → **Go to GB Power Market Dashboard (unsafe)**
   - This is safe - it's your own script
6. Click **Allow**

### Step 4: Test the Connection

1. The `testHealthCheck` function should complete
2. You'll see an alert showing the health check result:
   ```
   Health Check:
   Status: 200
   OK: true
   Response: {"status":"ok",...}
   ```
3. If you see errors, check the **Audit_Log** sheet in your spreadsheet

### Step 5: Run Initial Setup

**Option A: One-Click Setup (Recommended)**
1. Close the Apps Script tab
2. Refresh your Google Sheet
3. You'll see a new menu: **⚡ Power Market**
4. Click **⚡ Power Market** → **🚀 One-Click Setup**
5. Click **Yes** to confirm
6. Wait 10-30 seconds for setup to complete

**Option B: Manual Setup**
1. Click **⚡ Power Market** → **🔄 Refresh Now (today)**
2. Wait for data to load
3. Click **⚡ Power Market** → **📊 Rebuild Chart**
4. Click **⚡ Power Market** → **⏰ Set 5-min Auto-Refresh**

---

## 📊 What Gets Created

After setup, you'll have these tabs:

### 1. **Live Dashboard** (Main tab)
- Combined view of all metrics
- 48 rows (one per settlement period)
- Columns:
  - SP (Settlement Period 1-48)
  - Time (00:00 to 23:30)
  - SSP £/MWh (System Sell Price)
  - SBP £/MWh (System Buy Price)
  - Demand MW (National demand)
  - Generation MW (National generation)
  - BOALF Actions (Balancing actions count)
  - BOD Offer £/MWh (Bid-offer data - offer price)
  - BOD Bid £/MWh (Bid-offer data - bid price)
  - IC Net MW (Interconnector net flow)

### 2. **Chart Data**
- Same as Live Dashboard
- Used by the chart (via named range `NR_DASH_TODAY`)
- Auto-updates when refresh runs

### 3. **Live_Raw_Prices**
- Raw system prices data
- Columns: sp, ssp, sbp

### 4. **Live_Raw_Gen**
- Raw generation/demand data
- Columns: sp, gen_mw, demand_mw

### 5. **Live_Raw_BOA**
- Raw BOALF data
- Columns: sp, boalf_count, boalf_avg_mw

### 6. **Live_Raw_IC**
- Raw interconnector data
- Columns: sp, ic_net_mw

### 7. **Audit_Log**
- Activity log showing all refresh operations
- Timestamps, status, messages, user
- Last 1000 operations kept

---

## 🎛️ Menu Options

### ⚡ Power Market Menu

| Menu Item | Description | When to use |
|-----------|-------------|-------------|
| **🔄 Refresh Now (today)** | Pull latest data from BigQuery | Manually update data |
| **📊 Rebuild Chart** | Recreate the dashboard chart | Chart looks broken or missing |
| **⏰ Set 5-min Auto-Refresh** | Enable automatic updates every 5 min | Keep dashboard always current |
| **🛑 Stop Auto-Refresh** | Disable automatic updates | Save quota or stop background updates |
| **🚀 One-Click Setup** | Full setup: sheets + data + chart + auto-refresh | First-time setup or reset everything |

---

## 🔧 Configuration

The script is already configured for your setup:

```javascript
const VERCEL_PROXY = 'https://gb-power-market-jj.vercel.app/api/proxy-v2';
const PROJECT = 'inner-cinema-476211-u9';
const DATASET = 'uk_energy_prod';
const TZ = 'Europe/London';
```

**Tables used:**
- `bmrs_mid` - System prices (SSP/SBP)
- `bmrs_indgen_iris` - National generation
- `bmrs_inddem_iris` - National demand
- `bmrs_boalf` - Accepted balancing offers/bids
- `bmrs_bod` - Bid-offer data (price pairs)

---

## 🐛 Troubleshooting

### Error: "Authorization required"
**Solution:** Follow Step 3 above to authorize the script

### Error: "HTTP 500: FUNCTION_INVOCATION_FAILED"
**Problem:** Using wrong proxy endpoint
**Solution:** Check that `VERCEL_PROXY` uses `/api/proxy-v2` (not `/api/proxy`)

### Error: "Query failed: Table not found"
**Problem:** BigQuery table doesn't exist or wrong project/dataset
**Solution:** Verify you're querying `inner-cinema-476211-u9.uk_energy_prod`

### Chart shows "No data"
**Problem:** Named range not set or empty data
**Solution:** 
1. Run **🔄 Refresh Now (today)** first
2. Then run **📊 Rebuild Chart**

### Auto-refresh not working
**Problem:** Trigger not set or disabled
**Solution:**
1. Click **⚡ Power Market** → **🛑 Stop Auto-Refresh**
2. Click **⚡ Power Market** → **⏰ Set 5-min Auto-Refresh**
3. Check Apps Script editor → **Triggers** tab (clock icon) - should show 1 trigger

### Data shows zeros or nulls
**Problem:** No data for today's date in BigQuery
**Solution:**
- Check `Audit_Log` sheet for errors
- Verify data exists: Run Python dashboard refresh first
- Try a different date (edit `todayDateStr_YYYY_MM_DD()` function to hardcode a date)

---

## 📈 How It Works

### Data Flow

```
BigQuery (inner-cinema-476211-u9.uk_energy_prod)
    ↓
Vercel Edge Function (/api/proxy-v2)
    ↓
Apps Script (proxyGet function)
    ↓
Google Sheets (Live Dashboard)
    ↓
Chart (via named range NR_DASH_TODAY)
```

### Refresh Process

1. **Calculate today's date** in `Europe/London` timezone
2. **Query BigQuery** via Vercel proxy (5 queries in parallel):
   - System prices (SSP/SBP)
   - Generation + Demand
   - BOALF (balancing actions)
   - BOD (bid-offer prices)
   - Interconnector flows (derived)
3. **Index by settlement period** (SP 1-48)
4. **Write raw data** to separate tabs
5. **Combine into tidy table** (Live Dashboard)
6. **Update named range** `NR_DASH_TODAY` (A2:J49)
7. **Log to audit** with timestamp and status

### Auto-Refresh Trigger

When enabled, runs `refreshDashboardToday()` every 5 minutes:
- Uses Google Apps Script time-based triggers
- Persists across sessions
- Runs even when sheet is closed
- Check quota limits: https://developers.google.com/apps-script/guides/services/quotas

---

## 🔒 Security Notes

✅ **Safe:**
- Script only accesses BigQuery data (read-only via proxy)
- No credentials stored in the sheet
- Vercel proxy handles authentication
- All data transfers use HTTPS

⚠️ **Permissions Required:**
- `https://www.googleapis.com/auth/spreadsheets` - Read/write to this spreadsheet only
- Script cannot access other Google Drive files

---

## 🧪 Testing Functions

The script includes test functions for debugging:

### Test Health Check
```javascript
testHealthCheck()
```
- Pings `/api/proxy-v2?path=/health`
- Shows connection status
- Verifies Vercel proxy is working

### Test Single Query
```javascript
testSingleQuery()
```
- Runs system prices query for today
- Shows first result row
- Verifies BigQuery connection

**How to run:**
1. Open Apps Script editor
2. Select function from dropdown (top center)
3. Click **Run** ▶️
4. Check execution log (View → Logs)

---

## 📊 Chart Customization

The default chart shows:
- **Primary axis (left):** Demand, Generation, BOALF, IC Net (MW scale)
- **Secondary axis (right):** SSP, SBP, BOD Offer, BOD Bid (£/MWh scale)
- **Chart type:** Combo (lines + areas)
- **Time range:** 48 settlement periods (00:00 - 23:30)

**To customize:**
1. Edit `rebuildDashboardChart()` function
2. Modify `.setOption()` calls for colors, axes, series types
3. Save and run **📊 Rebuild Chart**

**Color scheme:**
- SSP: Red (#FF6B6B)
- SBP: Teal (#4ECDC4)
- Demand: Mint green area (#95E1D3)
- Generation: Pink area (#F38181)
- BOALF: Purple (#AA96DA)
- BOD Offer: Pink dashed (#FCBAD3)
- BOD Bid: Yellow dashed (#FFFFD2)
- IC Net: Blue (#A8D8EA)

---

## 🔄 Comparison with Python Dashboard

| Feature | Python (`tools/refresh_live_dashboard.py`) | Apps Script (`google_sheets_dashboard.gs`) |
|---------|-------------------------------------------|-------------------------------------------|
| **Data source** | Direct BigQuery API | Vercel proxy → BigQuery |
| **Authentication** | Service account JSON | Vercel handles auth |
| **Scheduling** | GitHub Actions / cron / manual | Apps Script time-based trigger |
| **Speed** | Faster (native BigQuery client) | Slower (HTTP proxy overhead) |
| **Quota** | BigQuery quota | Apps Script quota (6 min runtime/execution) |
| **Best for** | Server automation, CI/CD, bulk updates | Real-time user dashboard, interactive |

**Recommendation:** Use Python for bulk data loads, Apps Script for live user dashboard

---

## 📝 Next Steps

✅ **What's working:**
- Script installed and authorized
- Data refreshing from BigQuery
- Chart displaying correctly
- Auto-refresh enabled

🚀 **Enhancements you could add:**

1. **Historical data tab** - Store previous days for trend analysis
2. **Alerts** - Email notifications when SSP > threshold
3. **Forecast comparison** - Add wind forecast vs actual (if data available)
4. **VLP filter** - Show only VLP-operated battery activity
5. **Export to CSV** - Button to download data
6. **Dashboard for specific BMU** - Input BMU ID, show its BOD activity

**How to add features:**
1. Edit `google_sheets_dashboard.gs`
2. Add new functions
3. Add menu items in `onOpen()`
4. Save and refresh sheet

---

## 📚 Resources

- **Apps Script Docs:** https://developers.google.com/apps-script
- **BigQuery Schema:** Check `tools/refresh_live_dashboard.py` for column names
- **Vercel Proxy Docs:** See `GB_POWER_MARKET_JJ_DOCS.md` in your workspace
- **BMRS Data Guide:** https://www.bmreports.com/bmrs/?q=help/about-us

---

## ✅ Verification Checklist

After installation, verify:

- [ ] Menu **⚡ Power Market** appears when sheet is refreshed
- [ ] **Live Dashboard** tab exists with 48 rows of data
- [ ] **Chart** displays on Live Dashboard tab
- [ ] **SSP/SBP** columns show realistic prices (£30-150/MWh range)
- [ ] **Demand/Generation** show realistic values (20,000-50,000 MW range)
- [ ] **Audit_Log** shows successful refresh entries
- [ ] **Auto-refresh trigger** shows in Apps Script editor (Triggers tab)
- [ ] Named range **NR_DASH_TODAY** exists (Data → Named ranges)

If all boxes checked → **✅ Installation successful!**

---

## 🆘 Support

**If you get stuck:**

1. Check **Audit_Log** sheet for error messages
2. Run `testHealthCheck()` in Apps Script editor
3. Verify Vercel proxy is working: https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/health
4. Check Apps Script execution logs: Apps Script editor → View → Logs
5. Compare with Python dashboard output (`make today`)

**Common fixes:**
- Authorization issues → Re-authorize (Step 3)
- No data → Check date exists in BigQuery
- Chart broken → Run **📊 Rebuild Chart**
- Slow performance → Reduce auto-refresh frequency (10 min instead of 5 min)

---

**Last Updated:** 2025-11-07  
**Compatible with:** Google Sheets, Apps Script V8 Runtime  
**Requires:** Vercel proxy at `/api/proxy-v2` endpoint
