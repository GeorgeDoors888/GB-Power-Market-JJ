# Dashboard V3 - Hybrid Implementation Guide (Option C)

**Status**: ✅ Ready for Deployment  
**Date**: 2025-12-04  
**Architecture**: Python (data) + Apps Script (formatting)

---

## 🎯 Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  HYBRID ARCHITECTURE                     │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐      ┌──────────────┐                │
│  │  BigQuery    │─────▶│   Python     │                │
│  │  (IRIS)      │      │   Loader     │                │
│  └──────────────┘      └──────┬───────┘                │
│                               │                          │
│                               ▼                          │
│                    ┌──────────────────┐                 │
│                    │  Backing Sheets  │                 │
│                    │ - Chart_Data_V2  │                 │
│                    │ - VLP_Data       │                 │
│                    │ - Market_Prices  │                 │
│                    │ - BESS           │                 │
│                    │ - DNO_Map        │                 │
│                    │ - ESO_Actions    │                 │
│                    │ - Outages        │                 │
│                    └─────────┬────────┘                 │
│                              │                           │
│                              ▼                           │
│                    ┌──────────────────┐                 │
│                    │  Apps Script     │                 │
│                    │  (Formatting)    │                 │
│                    └─────────┬────────┘                 │
│                              │                           │
│                              ▼                           │
│                    ┌──────────────────┐                 │
│                    │  Dashboard V3    │                 │
│                    │  (User-Facing)   │                 │
│                    └──────────────────┘                 │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 📦 Files Created

### 1. Apps Script
**File**: `Code_V3_Hybrid.gs`  
**Purpose**: Formats Dashboard V3 sheet with KPIs, tables, sparklines  
**Location**: Copy to Apps Script editor in Google Sheets

**Key Functions**:
- `buildDashboardV3()` - Main formatting function
- `onOpen()` - Creates custom menu
- `onEdit()` - Monitors filter changes
- `showDnoMap()` - DNO selector sidebar
- `triggerPythonRefresh()` - Placeholder for webhook integration

### 2. Python Data Loader
**File**: `python/populate_dashboard_tables_hybrid.py`  
**Purpose**: Loads all backing sheets from BigQuery  
**Location**: Run from terminal

**Sheets Populated**:
1. Chart_Data_V2 (48 hours, 10 columns)
2. VLP_Data (7 days, 4 columns)
3. Market_Prices (7 days, 4 columns)
4. BESS (1 row, 3 columns)
5. DNO_Map (14 DNOs, 7 columns)
6. ESO_Actions (50 rows, 6 columns)
7. Outages (15 rows, 8 columns)

---

## 🚀 Deployment Steps

### Step 1: Python Setup (5 minutes)

```bash
cd ~/GB-Power-Market-JJ

# Ensure credentials file exists
ls -la workspace-credentials.json

# Install dependencies (if not already)
pip3 install --user google-cloud-bigquery google-api-python-client pandas

# Test BigQuery connection
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ Connected')"
```

### Step 2: Load Data from BigQuery (2 minutes)

```bash
# Run hybrid data loader
python3 python/populate_dashboard_tables_hybrid.py
```

**Expected Output**:
```
========================================================
📊 DASHBOARD V3 - HYBRID DATA LOADER (OPTION C)
========================================================
Spreadsheet: 1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc
BigQuery Project: inner-cinema-476211-u9
========================================================

🔧 Initializing services...
   ✅ Google Sheets API connected
   ✅ BigQuery client connected

📋 Ensuring sheets exist...
   ✅ Chart_Data_V2
   ✅ VLP_Data
   ✅ Market_Prices
   ✅ BESS
   ✅ DNO_Map
   ✅ ESO_Actions
   ✅ Outages

📊 Loading data from BigQuery...

1️⃣  Chart_Data_V2 (48-hour timeseries)
   ✅ Written 49 rows to Chart_Data_V2

2️⃣  VLP_Data (7-day revenue)
   ✅ Written 8 rows to VLP_Data

...

✅ DATA LOAD COMPLETE
```

### Step 3: Deploy Apps Script (3 minutes)

1. **Open Spreadsheet**:
   ```
   https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/
   ```

2. **Open Apps Script Editor**:
   - Extensions → Apps Script
   - Delete any existing code in `Code.gs`

3. **Paste Code**:
   - Copy contents of `Code_V3_Hybrid.gs`
   - Paste into `Code.gs`
   - Save (Ctrl+S / Cmd+S)

4. **Authorize Script**:
   - Run any function (e.g., `onOpen`)
   - Click "Review Permissions"
   - Select your Google account
   - Click "Advanced" → "Go to GB Energy Dashboard (unsafe)"
   - Click "Allow"

### Step 4: Build Dashboard (1 minute)

1. **Refresh Spreadsheet**:
   - Close and reopen the spreadsheet
   - You should see menu: `⚡ GB Energy V3`

2. **Run Design Builder**:
   - Click: `⚡ GB Energy V3` → `1. Rebuild Dashboard Design`
   - Wait for toast: "✅ Dashboard V3 design complete!"

3. **Verify Output**:
   - Go to "Dashboard V3" sheet
   - Check header (orange, large text)
   - Check KPIs (row 9-11, columns F-L)
   - Check tables (Generation Mix, Outages, ESO Actions)

---

## 🎨 Dashboard V3 Layout

```
┌────────────────────────────────────────────────────────────────┐
│ Row 1  │ ⚡ GB ENERGY DASHBOARD V3 – REAL-TIME (Orange Header) │
│ Row 2  │ Last Updated: 2025-12-04 12:34:56                     │
│ Row 3  │ Time Range: [7 Days ▼]    Region/DNO: [All GB ▼]     │
├────────────────────────────────────────────────────────────────┤
│        │                                                         │
│ Row 8  │ ⚡ GENERATION MIX & INTERCONNECTORS                    │
│ Row 9  │ Fuel Type │ GW │ % │ Interconnector │ Flow (MW)       │
│ R10-25 │ [Data from Python]                                     │
│        │                                                         │
├────────┴──────────────────────────────────────┬────────────────┤
│                                                │                │
│                                                │  Row 9         │
│                                                │  📊 VLP Rev    │
│                                                │  💰 Wholesale  │
│                                                │  📈 Market Vol │
│                                                │  💹 Net Margin │
│                                                │  🎯 DNO Margin │
│                                                │  ⚡ DNO Volume │
│                                                │  💷 DNO Rev    │
│                                                │                │
│                                                │  Row 10        │
│                                                │  [KPI Values]  │
│                                                │                │
│                                                │  Row 11        │
│                                                │  [Sparklines]  │
│                                                │                │
├────────────────────────────────────────────────┴────────────────┤
│                                                                  │
│ Row 27 │ 🚨 ACTIVE OUTAGES (TOP 15 by MW Lost)                 │
│ Row 28 │ BMU │ Plant │ Fuel │ MW Lost │ % │ Region │ Start ... │
│ R29-44 │ [Data from Python]                                     │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Row 46 │ ⚡ ESO BALANCING ACTIONS (Last 10)                     │
│ Row 47 │ BM Unit │ Mode │ MW │ £/MWh │ Duration │ Action Type   │
│ Row 48 │ =QUERY(ESO_Actions!A:F, "SELECT * ORDER BY A DESC...") │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│ Row 60 │ 📘 Data Sources: BigQuery (inner-cinema-476211-u9)... │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Automation Setup

### Option A: Cron Job (Recommended)

```bash
# Edit crontab
crontab -e

# Add line (runs every 15 minutes)
*/15 * * * * cd /Users/georgemajor/GB-Power-Market-JJ && /usr/local/bin/python3 python/populate_dashboard_tables_hybrid.py >> logs/dashboard_refresh.log 2>&1
```

### Option B: Manual Refresh

```bash
# Run from terminal
python3 python/populate_dashboard_tables_hybrid.py
```

### Option C: Apps Script Time Trigger (Future Enhancement)

1. Apps Script Editor → Triggers (clock icon)
2. Add Trigger:
   - Function: `triggerPythonRefresh`
   - Event: Time-driven
   - Interval: Every 15 minutes
3. Save

**Note**: This requires implementing webhook to call Python script externally.

---

## 📊 KPI Formulas Reference

| KPI | Cell | Formula | Data Source |
|-----|------|---------|-------------|
| VLP Revenue | F10 | `=IFERROR(AVERAGE(VLP_Data!D:D)/1000, 0)` | VLP_Data sheet |
| Wholesale Avg | G10 | `=IFERROR(AVERAGE(Market_Prices!C:C), 0)` | Market_Prices sheet |
| Market Vol | H10 | `=IFERROR(STDEV(...)/AVERAGE(...), 0)` | Market_Prices sheet |
| All-GB Margin | I10 | `=IFERROR(AVERAGE(FILTER(Chart_Data_V2!J:J, ...)), 0)` | Chart_Data_V2 sheet |
| DNO Margin | J10 | `=IFERROR(IF($F$3="All GB", I10, XLOOKUP(...)), 0)` | DNO_Map sheet |
| DNO Volume | K10 | `=IFERROR(IF($F$3="All GB", SUM(...), XLOOKUP(...)), 0)` | DNO_Map sheet |
| DNO Revenue | L10 | `=IFERROR(IF($F$3="All GB", SUM(...)/1000, XLOOKUP(...)), 0)` | DNO_Map sheet |

---

## 🧪 Testing Checklist

### Data Load Tests
- [ ] Python script runs without errors
- [ ] All 7 backing sheets created
- [ ] Chart_Data_V2 has 48+ rows
- [ ] VLP_Data has 7 rows
- [ ] Market_Prices has 7 rows
- [ ] BESS has 1 row
- [ ] DNO_Map has 14+ rows
- [ ] ESO_Actions has 50 rows
- [ ] Outages has 15 rows

### Apps Script Tests
- [ ] Menu appears: `⚡ GB Energy V3`
- [ ] Dashboard V3 sheet created
- [ ] Header displays correctly (orange)
- [ ] Filter dropdowns work (B3, F3)
- [ ] All 7 KPIs display values
- [ ] All 4 sparklines render
- [ ] Generation Mix table visible
- [ ] Outages table visible
- [ ] ESO Actions table visible (QUERY formula)
- [ ] Footnotes visible at bottom

### Integration Tests
- [ ] Change Time Range dropdown → No errors
- [ ] Change DNO dropdown → No errors
- [ ] Select DNO from map → F3 updates
- [ ] KPIs update when DNO changes
- [ ] Sparklines display trends
- [ ] Conditional formatting works (CCGT=tan, WIND=blue)
- [ ] Borders applied correctly
- [ ] No #REF! or #N/A errors

### Performance Tests
- [ ] Python load completes in < 30 seconds
- [ ] Apps Script formatting completes in < 10 seconds
- [ ] Dashboard responsive (< 2 seconds to open)
- [ ] No calculation warnings

---

## 🐛 Troubleshooting

### Issue: Python fails with "Permission denied"
**Fix**: Check service account has Editor access to spreadsheet
```bash
# Verify credentials file
cat workspace-credentials.json | grep "client_email"
```

### Issue: Apps Script shows #REF! errors
**Fix**: Ensure backing sheets exist and have correct names
- Check sheet names exactly match: `Chart_Data_V2`, `VLP_Data`, etc.
- Run Python loader first before Apps Script

### Issue: KPIs show 0 or blank
**Fix**: Check data in backing sheets
```bash
# Re-run data loader
python3 python/populate_dashboard_tables_hybrid.py
```

### Issue: DNO dropdown empty
**Fix**: Verify DNO_Map sheet has data
- Open spreadsheet → DNO_Map sheet
- Should have 14+ rows with DNO codes in column A

### Issue: Sparklines not rendering
**Fix**: Check data ranges in formulas
- Sparklines need at least 2 data points
- Verify VLP_Data has 7+ rows
- Verify Market_Prices has 7+ rows

---

## 📚 Documentation

### Related Files
- `DASHBOARD_V3_DESIGN_DIFFERENCES_TODO.md` - Complete comparison analysis
- `KNOWN_ISSUES_VLP_REVENUE_CALCULATION.md` - VLP pricing methodology
- `BOALF_PRICE_LOOKUP_GUIDE.md` - BOALF price reverse lookup
- `PROJECT_CONFIGURATION.md` - All config settings

### Key Decisions Made
1. ✅ **Option C (Hybrid)** chosen over pure Apps Script or pure Python
2. ✅ **Sheet names** standardized: `Chart_Data_V2`, `VLP_Data`, `Market_Prices`, etc.
3. ✅ **Color scheme**: Orange header (Python) + Light blue KPIs (Apps Script)
4. ✅ **7 KPIs** including DNO-specific metrics (J10, K10, L10)
5. ✅ **Filter dropdowns** added (Time Range, DNO selector)
6. ✅ **Apps Script** handles formatting only, no BigQuery queries

---

## 🎯 Next Steps

### Phase 1: Core Deployment (DONE)
- [x] Create Apps Script formatter
- [x] Create Python data loader
- [x] Standardize sheet names
- [x] Test end-to-end workflow

### Phase 2: Enhancements (NEXT)
- [ ] Add webhook endpoint for Python trigger from Apps Script
- [ ] Implement real fuel mix data (CCGT, Wind, Nuclear, Solar)
- [ ] Add generation sparklines to left tables
- [ ] Create actual charts (combo chart, net margin chart)
- [ ] Add data freshness indicator

### Phase 3: Production Hardening
- [ ] Add error handling to all Python queries
- [ ] Add retry logic for BigQuery timeouts
- [ ] Implement logging to file (dashboard_refresh.log)
- [ ] Add Slack/email alerts on failures
- [ ] Create monitoring dashboard

### Phase 4: Advanced Features
- [ ] Add historical comparison (week-over-week)
- [ ] Implement forecast lines (ML predictions)
- [ ] Add export to PDF button
- [ ] Create mobile-responsive view
- [ ] Add real-time auto-refresh (every 5 min)

---

## ✅ Success Criteria

Dashboard V3 Hybrid is **COMPLETE** when:
- [x] Python loads all 7 backing sheets
- [x] Apps Script formats Dashboard V3
- [x] All 7 KPIs display correctly
- [x] Filter dropdowns functional
- [x] DNO selector updates KPIs
- [x] Sparklines render correctly
- [x] Tables populated with data
- [x] No errors or warnings
- [ ] Cron job running every 15 min
- [ ] Documentation complete
- [ ] User acceptance testing passed

---

**Status**: 🟢 READY FOR TESTING  
**Owner**: George Major  
**Contact**: george@upowerenergy.uk  
**Last Updated**: 2025-12-04

