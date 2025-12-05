# BESS Dashboard - Deployment Checklist (Option A: Integration)

## ✅ COMPLETED
Core implementation finished. **Option A selected**: Extend existing BESS tab with enhanced analysis starting at row 60.

### Integration Architecture

```
BESS Sheet Layout:
┌─────────────────────────────────────────────────────┐
│ Rows 1-14:   DNO Lookup (PRESERVED) ✅              │
│              - Postcode/MPAN inputs                  │
│              - Red/Amber/Green DUoS rates            │
│              - Time bands display                    │
│                                                       │
│ Rows 15-20:  HH Profile Generator (PRESERVED) ✅    │
│              - Min/Avg/Max kW inputs                 │
│              - Synthetic demand profile              │
│                                                       │
│ Rows 27-50:  BtM PPA Cost Analysis (PRESERVED) ✅   │
│              - Direct Flow (columns A-C)             │
│              - BESS Generation (columns F-I)         │
│              - Profitable periods, VLP revenue       │
│                                                       │
│ Row 58:      Divider ─────────────────              │
│                                                       │
│ Row 59:      "Enhanced Revenue Analysis" Header 🆕   │
│                                                       │
│ Rows 60+:    Enhanced 6-Stream Model (NEW) 🆕       │
│              - Per-SP timeseries (A60:Q)            │
│              - KPIs panel (T60:U67)                  │
│              - Revenue stack (W60:Y67)               │
│              - FR/VLP/BM/Arbitrage/BTM/CM breakdown  │
└─────────────────────────────────────────────────────┘
```

### 1. BigQuery Views Created
- `v_bess_cashflow_inputs.sql` - Unified per-SP cashflow with FR/BM/VLP/prices/levies/DUoS
- VLP/P444 economics with SCRP compensation fields
- **Status**: SQL written, needs deployment to BigQuery

### 2. Python Modules Implemented
- `bess_profit_model_enhanced.py` - 6 revenue streams + degradation costs (✅ Updated with start_row=60)
- `tcr_charge_model_enhanced.py` - 2025-2030 scenario forecasting
- `dashboard_pipeline.py` - Enhanced with BESS integration (✅ Calls both existing + enhanced)
- **Existing modules preserved**:
  - `update_btm_ppa_from_bigquery.py` - BtM PPA analysis (rows 27-50)
  - `dno_lookup_python.py` - DNO rates lookup (rows 1-14)
  - `generate_hh_profile.py` - Demand profiles (rows 15-20)
- **Status**: Code complete, integration tested

### 3. Apps Script Formatting
- `apps_script_enhanced/bess_integration.gs` - Enhanced section formatting (✅ Row 60+ only)
- `formatBESSEnhanced()` - Formats enhanced analysis without touching rows 1-50
- **Existing Apps Script preserved**:
  - `bess_auto_trigger.gs` - DNO auto-lookup on edit
  - `bess_hh_generator.gs` - HH profile button
  - `bess_custom_menu.gs` - Custom menu functions
- **Status**: Code complete, ready to deploy to Google Sheets

### 4. Sheet Layouts Designed
- **BESS Sheet (Integrated)**:
  - Rows 1-50: Existing DNO/HH/BtM PPA sections (PRESERVED ✅)
  - Row 59: Enhanced analysis title/divider
  - Rows 60+: Enhanced timeseries (A-Q), KPIs (T-U), Revenue stack (W-Y)
- **TCR_Model Sheet**: Inputs (A1-B10), Cost Breakdown (A15-D27), Scenario Forecasts
- **Status**: Integration layout documented, no conflicts

### 5. Documentation Complete
- `BESS_DASHBOARD_IMPLEMENTATION.md` - Full technical reference (13,000+ chars)
- Revenue streams explained with £ ranges
- VLP vs BMU distinction, P444 compensation mechanics
- Critical gotchas documented

### 6. Deployment Automation Ready
- `deploy_bess_dashboard.sh` - 200+ line automated setup script
- Made executable with chmod +x
- **Status**: Ready to run

---

## 🚀 DEPLOYMENT STEPS (Execute These Now)

### Step 1: Test Integration (Verify No Conflicts)
```bash
# Check existing BESS sections are intact
python3 test_bess_integration.py

# Expected output:
# ✅ Section 1: DNO Lookup (rows 1-14) - Populated/Empty
# ✅ Section 2: HH Profile (rows 15-20) - Populated/Empty  
# ✅ Section 3: BtM PPA (rows 27-50) - Populated/Empty
# ⚠️  Section 4: Enhanced (rows 60+) - Empty (not yet deployed)
```

### Step 2: Run Deployment Script
```bash
cd /home/george/GB-Power-Market-JJ
./deploy_bess_dashboard.sh
```

**What it does:**
- ✓ Checks Python 3 and credentials
- ✓ Installs dependencies (google-cloud-bigquery, gspread, pandas, etc.)
- ✓ Deploys BigQuery view v_bess_cashflow_inputs
- ✓ Tests Python imports
- ✓ Runs dashboard_pipeline.py
- ✓ Creates logs/ directory
- ✓ Generates cron entry
- ✓ Creates systemd service
- ✓ Generates health check script

### Step 2: Deploy Apps Script
Follow instructions in `APPS_SCRIPT_DEPLOY.txt`:
1. Open spreadsheet: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/
2. Go to Extensions → Apps Script
3. Paste contents of `apps_script_enhanced/Code.js`
4. Save and run `formatAllSheets()`
5. Authorize when prompted
6. Refresh sheet to see "⚡ GB Energy Dashboard" menu

### Step 3: Enable Automated Updates
Choose one:

**Option A - Cron (Recommended)**:
```bash
crontab -e
# Add line from deployment script output:
# */15 * * * * cd /home/george/GB-Power-Market-JJ && /usr/bin/python3 dashboard_pipeline.py >> logs/pipeline.log 2>&1
```

**Option B - Systemd**:
```bash
sudo cp bess-dashboard.service /etc/systemd/system/
sudo systemctl enable bess-dashboard.service
sudo systemctl start bess-dashboard.service
```

### Step 4: Verify
```bash
# Check logs
tail -f logs/pipeline.log

# Health check
./check_dashboard.sh

# BigQuery view data
bq query --use_legacy_sql=false "SELECT COUNT(*) FROM \`inner-cinema-476211-u9.uk_energy_prod.v_bess_cashflow_inputs\`"
```

---

## 📊 EXPECTED REVENUE RANGES (2.5MW/5MWh Battery)

| Stream | Annual £ | Notes |
|--------|----------|-------|
| **FR (DC/DR)** | £150-350k | Availability + utilization - penalties |
| **Wholesale Arbitrage** | £50-150k | Discharge revenue - charge cost |
| **BM/BOA** | £80-200k | Balancing mechanism acceptances |
| **VLP Flexibility** | £10-70k | DNO/DSO services (15% fee deducted) |
| **BTM Savings** | £140-360k | Avoided import × (levies + DUoS + BSUoS) |
| **Capacity Market** | £68k | 2.5MW × £30.59/kW × 89.5% availability |
| **Degradation Cost** | -£100-300k | £10/MWh × cycles |
| **NET PROFIT** | £300-800k | Varies by strategy and market conditions |

---

## ⚠️ CRITICAL CONFIGURATION

### BigQuery Settings (Must Use These)
```python
PROJECT_ID = "inner-cinema-476211-u9"  # NOT jibber-jabber-knowledge!
DATASET = "uk_energy_prod"
LOCATION = "US"  # NOT europe-west2!
```

### Credentials
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json"
```

### Google Sheets
```
SHEET_ID: 1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc
Tabs: Dashboard, BESS, TCR_Model
```

### Color Scheme
- Orange titles: #FF6600 (white text)
- Grey tables: #F5F5F5
- Light blue headers: #D9E9F7
- White backgrounds: #FFFFFF

---

## 🔧 OPTIONAL ENHANCEMENTS

### Add Charts (Manual or Apps Script)
- SoC timeseries (BESS A:M)
- Charge/Discharge profile (BESS A:K,L)
- Revenue waterfall (BESS F:G)
- Profit per SP (BESS A:P)
- TCR scenario forecasts (TCR_Model A15+)

### Monitoring
```bash
# Live log monitoring
tail -f logs/pipeline.log

# Error checking
grep -i error logs/pipeline.log

# Data freshness alert
watch -n 60 ./check_dashboard.sh
```

---

## 📚 KEY BUSINESS LOGIC

### VLP vs BMU Distinction
- **VLPs**: Get DFS/DNO flexibility payments, NOT BOAs
- **BMUs**: Get Balancing Mechanism BOAs, NOT DFS payments
- **P444**: VLPs receive direct compensation at SCRP rate from supplier

### CHP Integration
- CHP under VLP registration keeps supplier as balance-responsible
- Supplier pays network charges, VLP provides flexibility services
- CHPQA exemptions: CCL relief, enhanced capital allowances
- Behind-the-meter BESS stacks 6 revenue streams simultaneously

### TCR Charges (2025-2030)
- Fixed: TNUoS Demand Tariff + DUoS Residual Charge (£/kW/year)
- Volumetric: BSUoS + RO + FiT + CfD + CCL (p/kWh)
- DUoS RAG: Red/Amber/Green time-of-use charges
- PV+BESS reduces peak import → lowers fixed charges

---

## 🐛 TROUBLESHOOTING

### "Table not found in europe-west2"
**Fix**: Set `location="US"` in BigQuery client

### "Access Denied: jibber-jabber-knowledge"
**Fix**: Use `inner-cinema-476211-u9` project

### "Module not found: mpan_parser"
**Fix**: Import from `mpan_generator_validator` instead

### "Unrecognized name: recordTime"
**Fix**: Use `measurementTime` in bmrs_freq table

### "No data in BESS sheet"
**Fix**: Check v_bess_cashflow_inputs has data, verify bess_dispatch table populated

---

## 📞 SUPPORT

**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Documentation**: BESS_DASHBOARD_IMPLEMENTATION.md  
**Status**: ✅ Ready for Production (November 2025)

---

## ✅ NEXT ACTION

**Run this command now:**
```bash
./deploy_bess_dashboard.sh
```

Then follow Apps Script deployment instructions in `APPS_SCRIPT_DEPLOY.txt`.
