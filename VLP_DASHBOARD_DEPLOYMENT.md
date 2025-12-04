# VLP Revenue Dashboard - Complete Deployment Guide

## 🎯 Overview

Automated Google Sheets dashboard displaying real-time Virtual Lead Party (VLP) battery revenue analysis with:
- Live ticker updating every 5 minutes
- 8 revenue stream breakdown (PPA, DC, DM, DR, CM, BM, Triad, Negative Pricing)
- 4 stacking scenarios (Conservative → Aggressive)
- Profit analysis by DUoS band
- Service compatibility matrix
- 48-period forecast

**Data Source**: BigQuery unified view `v_btm_bess_inputs` combining:
- Historical: Jan 2022 - Oct 28, 2025 (`bmrs_costs`, `bmrs_boalf`, `bmrs_bod`)
- Real-time IRIS: Oct 29, 2025+ (`bmrs_mid_iris`, `bmrs_boalf_iris`, `bmrs_bod_iris`)

**Dashboard**: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit

---

## 📦 Prerequisites

### Required Software
```bash
# Node.js & CLASP
npm install -g @google/clasp

# Python dependencies
pip3 install google-cloud-bigquery gspread google-auth pandas db-dtypes pyarrow
```

### Required Files
- `inner-cinema-credentials.json` - Service account credentials
- `energy_dashboard_clasp/` - Apps Script code (VlpRevenue.gs, VlpDashboard.gs, Code.gs)
- `refresh_vlp_dashboard.py` - Python automation script

### Required Access
- Google Cloud Project: `inner-cinema-476211-u9`
- BigQuery dataset: `uk_energy_prod`
- Google Sheets: Edit access to spreadsheet

---

## 🚀 Automated Deployment

### Quick Start
```bash
./deploy_vlp_dashboard.sh
```

This script will:
1. ✅ Check prerequisites (CLASP, Python, credentials)
2. ✅ Install Python dependencies
3. ✅ Authenticate CLASP
4. ✅ Link to Google Sheets
5. ✅ Deploy Apps Script
6. ⚠️ Prompt for BigQuery Advanced Service setup
7. ✅ Test BigQuery view access
8. ✅ Run initial dashboard refresh
9. ⚠️ Prompt for auto-refresh trigger setup
10. ✅ Optionally set up cron job

**Manual steps required**:
- Step 6: Enable BigQuery Advanced Service in Apps Script
- Step 9: Enable auto-refresh triggers in Google Sheets

---

## 🛠 Manual Deployment (If Script Fails)

### Step 1: Deploy Apps Script with CLASP

```bash
cd energy_dashboard_clasp

# First time: Create new Apps Script project
clasp login
clasp create --type sheets --title "VLP Revenue Dashboard" --parentId "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

# Deploy code
clasp push

# View in browser
clasp open
```

### Step 2: Enable BigQuery Advanced Service

1. Open Apps Script editor: https://script.google.com
2. Select **VLP Revenue Dashboard** project
3. Click **Services** (+ icon in left sidebar)
4. Find **BigQuery API** and enable it
5. Also enable in GCP Console if prompted

**Why needed**: The `runBigQuery()` function requires BigQuery API access via Advanced Services.

### Step 3: Create Dashboard Sheet

1. Open Google Sheet: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit
2. Menu: **⚡ Energy Tools** → **💰 VLP Revenue** → **📊 Create VLP Dashboard**
3. Authorize script when prompted
4. Wait ~30 seconds for sheet creation

**Expected output**:
- New sheet "VLP Revenue" created
- Live ticker in A1 (merged A1:M3)
- Current period section (A5-B14)
- Service breakdown table (A17-E27)
- Cost breakdown (G5-H14)
- Stacking scenarios (A30-H35)
- Compatibility matrix (A38-I46)
- Profit analysis (K17-N20)

### Step 4: Manual Refresh Test

Menu: **⚡ Energy Tools** → **💰 VLP Revenue** → **🔄 Refresh VLP Data**

**Expected results**:
- Live ticker updates with current time
- Profit icon shows (🟢 green > £150, 🟡 yellow > £100, 🔴 red ≤ £100)
- All sections populate with live data
- No errors in Apps Script logs (View → Executions)

### Step 5: Enable Auto-Refresh

Menu: **⚡ Energy Tools** → **⏱ Enable Auto-Refresh**

**Creates 3 triggers**:
- `refreshDashboard` - Every 5 minutes (updates main dashboard)
- `updateLiveTicker` - Every 5 minutes (VLP ticker)
- `refreshVlpDashboard` - Every 30 minutes (full VLP refresh)

**Verify**:
- Menu: **⚡ Energy Tools** → **⏱ Disable Auto-Refresh** (shows "Currently enabled: 3 triggers")
- Check: Apps Script editor → Triggers section (clock icon)

### Step 6: Test Python Automation

```bash
python3 refresh_vlp_dashboard.py
```

**Expected output**:
```
VLP Revenue Dashboard Refresh - 2025-12-02 15:30:45

✅ BigQuery clients initialized
✅ Querying latest VLP data...
✅ Querying 48-period forecast...
✅ Querying profit by DUoS band...
✅ Live ticker updated
✅ Current period updated (9 values)
✅ Service breakdown updated (8 services)
✅ Stacking scenarios updated (4 scenarios)
✅ Profit analysis updated (3 bands)

✅ VLP Dashboard refresh complete!
  • Market Price: £72.56/MWh
  • Total Revenue: £342.07/MWh
  • Net Profit: £170.25/MWh
  • Trading Signal: DISCHARGE_HIGH
  • DUoS Band: GREEN
```

### Step 7: Schedule Python Refresh (Optional)

```bash
crontab -e
```

Add line:
```cron
# VLP Dashboard Refresh (every 30 minutes)
*/30 * * * * cd /Users/georgemajor/GB-Power-Market-JJ && /usr/bin/python3 refresh_vlp_dashboard.py >> logs/vlp_refresh.log 2>&1
```

**Why both Apps Script AND Python?**
- Apps Script: Real-time updates within Google Sheets (user-triggered, auto-refresh)
- Python: Scheduled batch updates, easier debugging, can run on servers

---

## 📊 Dashboard Layout Reference

### Live Ticker (A1:M3)
```
🟢 LIVE: GREEN | Market £72.56 | Revenue £342.07 | Profit £170.25/MWh | Signal: DISCHARGE_HIGH | 15:30:45
```

**Color coding**:
- 🟢 Green: Profit > £150/MWh
- 🟡 Yellow: Profit > £100/MWh
- 🔴 Red: Profit ≤ £100/MWh

### Current Period (A5-B14)
| Metric | Value |
|--------|-------|
| Settlement Date | 2025-12-02 |
| Settlement Period | 47 |
| Half-Hour Time | 23:00 |
| DUoS Band | GREEN |
| Market Price | £72.56/MWh |
| Total Revenue | £342.07/MWh |
| Total Cost | £171.82/MWh |
| Net Profit | £170.25/MWh |
| Trading Signal | DISCHARGE_HIGH |

### Service Breakdown (A17-E27)
| Service | £/MWh | % of Total | Annual (£) | Status |
|---------|-------|------------|------------|--------|
| PPA Discharge | 150.00 | 43.8% | 372,300 | 🟢 Active |
| Dynamic Containment (DC) | 78.75 | 23.0% | 195,458 | 🟢 Active |
| Dynamic Moderation (DM) | 40.29 | 11.8% | 100,000 | 🟢 Active |
| Dynamic Regulation (DR) | 60.44 | 17.7% | 150,000 | ⚪ Inactive |
| Capacity Market (CM) | 12.59 | 3.7% | 31,250 | 🟢 Active |
| Balancing Mechanism (BM) | 0.00 | 0.0% | 0 | ⚪ Inactive |
| Triad Avoidance | 0.00 | 0.0% | 0 | ⚪ Off-Season |
| Negative Pricing | 0.00 | 0.0% | 0 | ⚪ Inactive |
| **TOTAL** | **342.07** | **100%** | **848,858** | **4/8 Active** |

### Stacking Scenarios (A30-H35)
| Scenario | Services | Annual (£) | £/MWh | Risk | Active |
|----------|----------|------------|-------|------|--------|
| Conservative | DC + CM + PPA | 599,008 | 241.34 | Low 🟢 | Reliable |
| Balanced | DC + DM + CM + PPA + BM | 749,008 | 301.78 | Medium 🟡 | Multiple freq |
| Aggressive | All 7 services | 999,008 | 402.50 | High 🔴 | Max stack |
| Opportunistic | DC + CM + PPA + Negative | 624,008 | 251.41 | Low-Med 🟢 | Event capture |

### Compatibility Matrix (A38-I46)
|  | PPA | DC | DM | DR | CM | BM | Triad | Negative |
|---|-----|----|----|----|----|----|----|-------|
| **PPA** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **DC** | ✓ | ✓ | ✓ | ✗ | ✓ | ⚠ | ✓ | ✓ |
| **DM** | ✓ | ✓ | ✓ | ✗ | ✓ | ⚠ | ✓ | ✓ |
| **DR** | ✓ | ✗ | ✗ | ✓ | ✓ | ⚠ | ✓ | ✓ |
| **CM** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **BM** | ✓ | ⚠ | ⚠ | ⚠ | ✓ | ✓ | ✓ | ✓ |
| **Triad** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Negative** | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

**Legend**:
- ✓ = Fully compatible (can stack)
- ✗ = Incompatible (mutual exclusion)
- ⚠ = Conditional (depends on dispatch)

### Profit by DUoS Band (K17-N20)
| Band | Avg (£/MWh) | Min (£/MWh) | Max (£/MWh) |
|------|-------------|-------------|-------------|
| GREEN | 163.65 | 120.00 | 210.00 |
| AMBER | 150.38 | 110.00 | 195.00 |
| RED | 112.32 | 85.00 | 150.00 |

---

## 🔧 Troubleshooting

### Error: "BigQuery API not enabled"
**Solution**: Enable BigQuery Advanced Service (see Step 2 above)

### Error: "Access Denied: v_btm_bess_inputs"
**Cause**: Wrong project or dataset
**Solution**: Verify `PROJECT_ID = "inner-cinema-476211-u9"` in all scripts

### Error: "ModuleNotFoundError: gspread"
**Solution**: `pip3 install gspread google-cloud-bigquery`

### Ticker shows "⚠️ DATA UNAVAILABLE"
**Causes**:
1. IRIS feed down (check AlmaLinux server)
2. BigQuery view empty (query directly to test)
3. Network/auth issues

**Debug**:
```bash
# Test BigQuery access
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ Connected')"

# Query view directly
bq query --project_id=inner-cinema-476211-u9 --use_legacy_sql=false \
"SELECT COUNT(*) FROM \`inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs\`"
```

### Zero prices in Period 47
**Status**: Known data quality issue (see VLP_REVENUE_OUTPUT_SUMMARY.md)
**Action**: Investigating bmrs_mid_iris data source

### Auto-refresh not working
**Check**:
1. Triggers installed? Apps Script → Triggers section
2. Authorization granted? Re-run enableAutoRefresh()
3. Error logs? View → Executions

---

## 📖 Documentation Reference

| File | Purpose |
|------|---------|
| `PRICING_DATA_ARCHITECTURE.md` | Explains IRIS vs historical pricing, query patterns |
| `VLP_REVENUE_OUTPUT_SUMMARY.md` | Latest live data analysis, zero-price anomaly |
| `energy_dashboard_clasp/README.md` | Apps Script code documentation |
| `bigquery/v_btm_bess_inputs_unified.sql` | View definition with UNION pattern |
| `deploy_vlp_dashboard.sh` | This deployment guide |

---

## 🎯 Next Steps

1. ✅ Deploy dashboard (run script above)
2. ⏸️ Investigate zero-price anomaly in Period 47
3. ⏸️ Build 48-period forecast chart (Charts.gs update)
4. ⏸️ Create Help sheet with service definitions
5. ⏸️ Add data validation alerts
6. ⏸️ Export 7-day dataset for analysis
7. ⏸️ Set up monitoring dashboard

---

## 📞 Support

**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Status**: ✅ Production Ready (Dec 2025)

---

*Last Updated: December 2, 2025*  
*Version: 1.0.0*
