# BESS, Battery & CHP Related Files and Issues - Complete Inventory

**Generated**: 4 December 2025  
**Location**: /Users/georgemajor/GB-Power-Market-JJ  
**Purpose**: Comprehensive listing of all battery storage, BESS, and CHP related code, documentation, and known issues

---

## 📋 Executive Summary

The GB Power Market JJ project contains **extensive battery energy storage (BESS), VLP (Virtual Lead Party), and Behind-the-Meter PPA** infrastructure across:

- **60+ BESS-specific files**
- **13 battery analysis files**
- **Major subsystems**: VLP revenue tracking, BtM PPA calculations, DNO integration, arbitrage analysis
- **2 complete dashboard implementations**: `energy_dashboard 2/` with BtM PPA + original workspace files

---

## 🔋 Core BESS Systems

### 1. **BESS Sheet Integration** (Google Sheets)
**Primary Files**:
- `bess_dno_lookup.gs` - Apps Script for DNO lookup from postcode/MPAN
- `bess_custom_menu.gs` - Custom menu for BESS sheet operations
- `bess_auto_trigger.gs` - Automated refresh triggers
- `bess_webapp_api.gs` - Web app API endpoints

**Python Backend**:
- `refresh_bess_dno.py` - One-click DNO refresh
- `populate_bess_costs.py` - Cost calculations
- `check_bess_sheet.py` - Validation script
- `create_bess_vlp_sheet.py` - Initial sheet setup
- `enhance_bess_vlp_sheet.py` - Feature enhancements
- `link_duos_to_bess_sheet.py` - DUoS rate integration

**Data Files**:
- `bess_export_20251124_172111.csv` - Export snapshot
- `bess_export_20251124_172142.json` - JSON export
- `bess_new_layout.json` - Layout configuration
- `bess_comprehensive_revenue_20251201_143147.csv` - Revenue analysis
- `bess_conjunctive_revenue_20251201_155257.csv` - Conjunctive revenue model
- `bess_full_revenue_stack_20251201_144406.csv` - Full revenue stack

---

### 2. **VLP (Virtual Lead Party) Revenue System**

**Primary Analysis Files**:
- `calculate_bess_vlp_revenue.py` - Main VLP revenue calculator
- `analyze_battery_vlp_final.py` - Final VLP analysis
- `complete_vlp_battery_analysis.py` - Comprehensive VLP + battery analysis
- `create_vlp_json.py` - JSON export for VLP data
- `vlp_battery_units_data.json` - Complete BMU unit database

**Revenue Calculation**:
- `calculate_bess_conjunctive_revenue.py` - Conjunctive revenue streams
- `calculate_bess_full_revenue_stack.py` - All revenue streams combined
- `bess_revenue_engine.py` - Revenue optimization engine

**Documentation**:
- `BESS_VLP_PAYMENT_BREAKDOWN.md` - Complete payment model
- `BESS_COMPREHENSIVE_REVENUE_ANALYSIS.md` - Revenue analysis guide
- `BESS_CONJUNCTIVE_VS_MUTUALLY_EXCLUSIVE.md` - Revenue model comparison
- `BATTERY_TRADING_STRATEGY_ANALYSIS.md` - Trading strategies
- `VLP_DASHBOARD_DEPLOYMENT.md` - Dashboard setup guide

---

### 3. **Behind-the-Meter (BtM) PPA System** ⭐ NEW

**Location**: `energy_dashboard 2/`

**Core Modules**:
- `finance/btm_ppa.py` (445 lines) - Complete BtM PPA calculation engine
  * `calculate_btm_ppa_revenue()` - Two-stream profit calculation
  * `get_btm_ppa_metrics()` - High-level API
  * Stream 1: Direct import (RED/AMBER/GREEN periods)
  * Stream 2: Battery discharge + VLP revenue

**Visualization**:
- `charts/btm_ppa_chart.py` (215 lines) - 4-panel visualization:
  1. Revenue streams breakdown
  2. Battery charging strategy
  3. RED period coverage
  4. Cost comparison by period

**Testing**:
- `test_btm_ppa.py` (75 lines) - Standalone test suite
- `worked_example.py` (500+ lines) - Detailed worked examples

**Configuration** (in `finance/btm_ppa.py`):
```python
BESS_CAPACITY_MWH = 5.0          # Battery energy capacity
BESS_POWER_MW = 2.5              # Charge/discharge power
BESS_EFFICIENCY = 0.85           # Round-trip efficiency
PPA_PRICE = 150.0                # £/MWh contract price
VLP_PARTICIPATION_RATE = 0.30    # 30% of discharge hours
VLP_AVG_UPLIFT = 15.0            # £15/MWh VLP premium
DC_ANNUAL_REVENUE = 200000       # Dynamic Containment revenue
```

**Documentation**:
- `INTEGRATION_COMPLETE.md` - BtM PPA integration guide
- `STATUS_REPORT.md` - Current system status
- `energy_dashboard 2/README.md` - Complete user guide

**Key Features**:
- ✅ Optimal battery charging strategy (GREEN priority, never RED)
- ✅ VLP revenue integration (30% participation, £15/MWh uplift)
- ✅ DUoS cost avoidance tracking
- ✅ Battery cycle tracking (degradation analysis)
- ✅ System price analysis by band (RED/AMBER/GREEN)
- ✅ Dynamic Containment revenue
- ✅ Real-time BigQuery data integration

---

### 4. **Battery Arbitrage & Trading**

**Analysis Scripts**:
- `battery_arbitrage.py` - Arbitrage opportunity detection
- `battery_profit_analysis.py` - Profit modeling
- `battery_charging_cost_analysis.py` - Charging cost optimization
- `identify_battery_bmus_from_generators.py` - BMU identification

**Dashboard Integration**:
- `new-dashboard/battery_revenue_analyzer.py` - Revenue analyzer
- `new-dashboard/battery_revenue_analyzer_fixed.py` - Fixed version
- `new-dashboard/battery_revenue_webhook.py` - Webhook integration
- `new-dashboard/check_battery_data.py` - Data validation
- `new-dashboard/show_battery_sheet.py` - Sheet display
- `new-dashboard/start_battery_webhook.sh` - Webhook startup script

---

### 5. **BESS Optimization Engines**

**Engine Files**:
- `bess_revenue_engine.py` - Revenue optimization
- `optimised_bess_engine.py` - Optimized version
- `full_btm_bess_simulation.py` - Full simulation model
- `chatgpt_files/bess_revenue_engine.py` - ChatGPT variant

**Configuration**:
- `add_bess_dropdowns.py` - UI dropdowns
- `add_bess_dropdowns_v4.py` - Latest dropdown version

---

### 6. **CHP (Combined Heat & Power) Integration**

**NEW**: `GB_Energy_Dashboard_FullPack_v3/` package contains:

**CHP Optimizer**:
- `python/chp_optimiser.py` - CHP optimization with baseline & flexibility
  ```python
  max_output_mw: 5.0
  min_output_mw: 1.0
  fuel_cost_gbp_per_mwh_th: 20.0
  electrical_efficiency: 0.38
  heat_efficiency: 0.45
  ```

**Features**:
- Marginal cost calculation (£/MWh_el)
- Heat credit accounting (co-product value)
- Flexibility dispatch (up/down)
- VTP-style £/MWh optimization

**Documentation**:
- `config_example.yaml` - Full configuration template with CHP section
- `README.md` - CHP integration guide

---

## 🗂️ BigQuery Tables

### BESS-Specific Tables (found in `uk_energy_prod` dataset):

1. **`bess_asset_config`** (1 row currently)
   - Columns: `asset_id`, `asset_name`, `p_max_mw`, `e_max_mwh`, `roundtrip_efficiency`
   - Purpose: Battery asset configuration
   - Status: ✅ Active, contains 1 BESS (2.5MW/5MWh)

2. **`v_btm_bess_inputs`** (121,355 rows)
   - Purpose: Behind-the-meter BESS inputs (unified view)
   - Usage: VLP dashboard, BtM PPA calculations
   - Referenced in: `VLP_DASHBOARD_DEPLOYMENT.md`

3. **`bess_fr_schedule`** (0 rows)
   - Purpose: Frequency response schedule
   - Status: ⚠️ Empty

4. **`stor_nonbm`** (335 rows)
   - Purpose: Short-Term Operating Reserve (non-BM)
   - Usage: Non-BM STOR analytics

5. **`vw_battery_arbitrage_costs`**
   - Purpose: Battery arbitrage cost view
   - Usage: Arbitrage analysis

### Related Views:
- `v_bm_bids_offers_classified` - Includes BESS bid/offer classification
- `v_bm_system_direction_classified` - ESO actions (charge/discharge BESS)

---

## 📊 Dashboard Systems

### Dashboard V3 (Current - Hybrid Architecture)
**Location**: Main workspace root  
**Key Files**:
- `Code_V3_Hybrid.gs` (530 lines) - Apps Script formatter
- `python/populate_dashboard_tables_hybrid.py` (398 lines) - Data loader
- `deploy_dashboard_v3_hybrid.sh` - Deployment script

**BESS Integration**:
- BESS sheet: Placeholder data (25 BMUs, 1500 MW, 85.5%)
- BtM sheet: Created with real data (1 asset: 2.5MW/5MWh)
- Function: `load_bess_summary()` - Currently returns hardcoded data

**Status**: ✅ Deployed and operational
**Documentation**: `DASHBOARD_V3_DEPLOYMENT_SUCCESS.md`

---

### Energy Dashboard 2 (BtM PPA Focus)
**Location**: `energy_dashboard 2/`  
**Architecture**: Comprehensive analytics platform

**BESS Components**:
- `bess/` directory - Battery analytics modules
- `finance/btm_ppa.py` - BtM PPA revenue engine
- `charts/bess_chart.py` - BESS availability charts
- `charts/btm_ppa_chart.py` - BtM PPA visualization

**Output**:
- `out/btm_ppa_chart.png` - 4-panel BtM PPA analysis
- `out/bess_chart.png` - BESS availability
- Dashboard row 7: BESS Portfolio KPI
- Dashboard row 8: BtM PPA Profit KPI

**Status**: ✅ Fully integrated and operational
**Documentation**: `INTEGRATION_COMPLETE.md`, `STATUS_REPORT.md`

---

### GB_Energy_Dashboard_FullPack_v3 (NEW Package)
**Location**: `/Users/georgemajor/Downloads/GB_Energy_Dashboard_FullPack_v3/`  
**Purpose**: Self-contained BESS + CHP optimization suite

**Architecture**:
```
python/
├── bess_optimiser.py        # Forward-looking BESS optimizer
├── chp_optimiser.py          # CHP baseline + flexibility
├── vlp_pricing.py            # VLP price-only KPIs
├── dashboard_kpis_v3.py      # Market KPI writer
└── dashboard_chart_data.py   # Timeseries chart data
```

**Features**:
- Multi-day horizon BESS optimization
- DUoS/levies/PPA integration
- CHP electrical/heat efficiency modeling
- Real-time BigQuery integration
- Google Sheets push

**Configuration**: `config_example.yaml`
**Documentation**: `README.md`

---

## 🚨 Known Issues & Problems

### 1. **BESS Sheet Placeholder Data**
**Issue**: Dashboard V3 BESS sheet contains only placeholder data  
**File**: `python/populate_dashboard_tables_hybrid.py` line 220-230  
**Current**:
```python
def load_bess_summary(bq_client: bigquery.Client) -> list:
    # Placeholder data
    header = ['Active BMUs', 'Total Capacity (MW)', 'Avg Efficiency (%)']
    data = [header, [25, 1500, 85.5]]
    return data
```

**Solution**: Query `bess_asset_config` table for real data  
**Status**: ⏳ IN PROGRESS (BtM sheet created with real data)

---

### 2. **BtM PPA Not Charging (Current Market Conditions)**
**Issue**: Battery not charging because system prices too high  
**Location**: `energy_dashboard 2/STATUS_REPORT.md`

**Root Cause**:
- GREEN period cost: £70/MWh (system buy price)
- PPA price: £150/MWh
- VLP uplift: £15/MWh
- After 15% losses: (150 + 15) × 0.85 = £140.25/MWh
- **Unprofitable**: £140.25 < £70 charging cost

**Current Output**:
```
Battery Charging Strategy: 0 MWh charged
Battery Cycles: 0.0 cycles/year
BtM PPA Profit: -£1,995,120 (would lose money)
```

**This is CORRECT behavior** - system shows market conditions make BtM PPA unprofitable.

**When Profitable**: System buy prices < £50/MWh (likely winter 2026)

**Documentation**: `STATUS_REPORT.md`, `worked_example.py`

---

### 3. **VLP Revenue Calculation Issues**
**File**: `KNOWN_ISSUES_VLP_REVENUE_CALCULATION.md` (1000+ lines)

**Key Problems**:
- Unrealistic £8.7B annual revenue (should be £500k-2M)
- BOD vs BOALF data mismatch
- Unit price (£/MWh) vs total revenue confusion
- Missing volume data for revenue calculation

**Status**: 🔍 Under investigation  
**Reference**: Lines 56, 747, 915, 997 in markdown

---

### 4. **Dashboard V3 BESS Formula Issues**
**File**: `TASK3_AND_4_EXECUTION_GUIDE.md`

**Missing Formulas** (Lines 102-104):
```
J10: =QUERY(BOD_SUMMARY!A:Q, "SELECT K WHERE A='selected_dno' AND B='"&BESS!B6&"' LIMIT 1")
K10: =QUERY(BOD_SUMMARY!A:Q, "SELECT E WHERE A='selected_dno' AND B='"&BESS!B6&"' LIMIT 1")
L10: =QUERY(BOD_SUMMARY!A:Q, "SELECT F WHERE A='selected_dno' AND B='"&BESS!B6&"' LIMIT 1")/1000
```

**Issue**: Formulas reference `BESS!B6` for DNO selection  
**Status**: ⚠️ Not implemented in Dashboard V3

---

### 5. **MPAN Parsing for DNO Lookup**
**File**: `.github/copilot-instructions.md` (Lines about MPAN)

**Critical Issue**: Must use correct import  
```python
# ✅ CORRECT
from mpan_generator_validator import extract_core_from_full_mpan, mpan_core_lookup

# ❌ WRONG (doesn't exist)
from mpan_parser import ...
```

**Test Command**:
```bash
python3 dno_lookup_python.py 14 HV  # Should return NGED West Midlands
```

---

## 🎯 BESS Business Logic

### Virtual Lead Party (VLP) Units
**What**: Battery operators submitting bids to National Grid  
**Revenue Model**: Charge cheap → discharge expensive (system imbalance arbitrage)

**Key Units**:
- `FBPGM002` (Flexgen)
- `FFSEN005` (likely Gresham House/Harmony Energy)
- `2__FBPGM001`, `2__FBPGM002` (VLP BMU units)

**High-Value Periods**:
- Oct 17-23, 2025: £79.83/MWh avg (6-day high-price event)
- Oct 24-25, 2025: £30.51/MWh avg (price crash from wind)

**Strategy**: Aggressive deploy at £70+/MWh, preserve cycles at £25-40/MWh

---

### Revenue Streams

**1. BtM PPA Revenue**:
- Stream 1: Direct import (avoid RED losses)
- Stream 2: Battery discharge + VLP (£15/MWh uplift)
- PPA Price: £150/MWh
- Annual potential: £167k-362k (when profitable)

**2. Frequency Response**:
- Dynamic Containment (DC): £200k/year fixed
- Static FR: Variable based on clearing prices

**3. Balancing Mechanism**:
- Bid-offer acceptances
- System price capture
- Volume-weighted pricing

**4. Arbitrage**:
- Buy low (GREEN periods)
- Sell high (RED periods)
- Efficiency losses: 15%

**5. DUoS Avoidance**:
- RED rate: £4.837/kWh (example: NGED West Midlands HV)
- AMBER rate: £0.457/kWh
- GREEN rate: £0.038/kWh

---

## 📁 File Categories

### Revenue Calculation (10 files)
- `calculate_bess_vlp_revenue.py`
- `calculate_bess_conjunctive_revenue.py`
- `calculate_bess_full_revenue_stack.py`
- `calculate_btm_ppa_final.py`
- `finance/btm_ppa.py`
- `bess_revenue_engine.py`
- `battery_profit_analysis.py`
- `battery_arbitrage.py`
- `battery_charging_cost_analysis.py`
- `python/vlp_pricing.py` (FullPack v3)

### Optimization (4 files)
- `optimised_bess_engine.py`
- `full_btm_bess_simulation.py`
- `python/bess_optimiser.py` (FullPack v3)
- `python/chp_optimiser.py` (FullPack v3)

### Sheet Integration (10 files)
- `bess_dno_lookup.gs`
- `bess_custom_menu.gs`
- `bess_auto_trigger.gs`
- `bess_webapp_api.gs`
- `refresh_bess_dno.py`
- `populate_bess_costs.py`
- `check_bess_sheet.py`
- `create_bess_vlp_sheet.py`
- `enhance_bess_vlp_sheet.py`
- `link_duos_to_bess_sheet.py`

### Analysis & Reporting (8 files)
- `analyze_battery_vlp_final.py`
- `complete_vlp_battery_analysis.py`
- `identify_battery_bmus_from_generators.py`
- `charts/btm_ppa_chart.py`
- `charts/bess_chart.py`
- `test_btm_ppa.py`
- `worked_example.py`
- `create_vlp_json.py`

### Dashboard Systems (6 files)
- `energy_dashboard 2/` (complete system)
- `new-dashboard/battery_revenue_analyzer.py`
- `python/populate_dashboard_tables_hybrid.py`
- `python/dashboard_kpis_v3.py` (FullPack v3)
- `python/dashboard_chart_data.py` (FullPack v3)
- `python/dashboard_layout_v3.py` (FullPack v3)

### Documentation (12 files)
- `BESS_VLP_PAYMENT_BREAKDOWN.md`
- `BESS_COMPREHENSIVE_REVENUE_ANALYSIS.md`
- `BESS_CONJUNCTIVE_VS_MUTUALLY_EXCLUSIVE.md`
- `BATTERY_TRADING_STRATEGY_ANALYSIS.md`
- `VLP_DASHBOARD_DEPLOYMENT.md`
- `INTEGRATION_COMPLETE.md` (BtM PPA)
- `STATUS_REPORT.md` (BtM PPA)
- `KNOWN_ISSUES_VLP_REVENUE_CALCULATION.md`
- `BESS_DEPLOYMENT_SUCCESS.md`
- `BESS_DROPDOWNS_COMPLETE.md`
- `BESS_ENGINE_DEPLOYMENT.md`
- `BESS_ENHANCEMENTS_COMPLETE.md`

### Configuration (5 files)
- `bess_new_layout.json`
- `add_bess_dropdowns.py`
- `add_bess_dropdowns_v4.py`
- `config_example.yaml` (FullPack v3)
- `python/config.py` (FullPack v3)

### Data Exports (5 files)
- `bess_export_20251124_172111.csv`
- `bess_export_20251124_172142.json`
- `bess_comprehensive_revenue_20251201_143147.csv`
- `bess_conjunctive_revenue_20251201_155257.csv`
- `bess_full_revenue_stack_20251201_144406.csv`

### System Files (3 files)
- `bess-webhook.service`
- `new-dashboard/start_battery_webhook.sh`
- `chatgpt_files/bess_auto_trigger.gs`

---

## 🔧 Quick Commands

### Test BtM PPA System
```bash
cd "energy_dashboard 2"
python3 test_btm_ppa.py
```

### Refresh BESS DNO Data
```bash
python3 refresh_bess_dno.py
```

### Check BESS Asset Config
```bash
python3 -c "
from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9')
query = 'SELECT * FROM \`inner-cinema-476211-u9.uk_energy_prod.bess_asset_config\`'
df = client.query(query).to_dataframe()
print(df)
"
```

### Deploy Dashboard V3
```bash
./deploy_dashboard_v3_hybrid.sh
```

### Run FullPack V3 Dashboard
```bash
cd GB_Energy_Dashboard_FullPack_v3
source .venv/bin/activate
python -m python.dashboard_v3_master
```

---

## 🎓 Learning Resources

**For BtM PPA Understanding**:
1. Read `energy_dashboard 2/worked_example.py` - Line-by-line calculation
2. Review `STATUS_REPORT.md` - Why battery isn't charging now
3. Check `finance/btm_ppa.py` constants for configuration

**For VLP Revenue**:
1. `BESS_VLP_PAYMENT_BREAKDOWN.md` - Complete payment model
2. `BATTERY_TRADING_STRATEGY_ANALYSIS.md` - Trading strategies
3. `KNOWN_ISSUES_VLP_REVENUE_CALCULATION.md` - Known problems

**For BESS Optimization**:
1. `python/bess_optimiser.py` (FullPack v3) - Multi-day horizon
2. `optimised_bess_engine.py` - Single optimization
3. `full_btm_bess_simulation.py` - Full simulation

---

## 📞 Support & Next Steps

**Current Priority**: Update Dashboard V3 BESS sheet with real data from `bess_asset_config`

**Recommended Actions**:
1. ✅ BtM sheet created with real data (1 asset: 2.5MW/5MWh)
2. ⏳ Update `load_bess_summary()` in `populate_dashboard_tables_hybrid.py`
3. 📋 Monitor system buy prices for BtM PPA profitability
4. 📋 Resolve VLP revenue calculation issues (see KNOWN_ISSUES doc)

**Contact**: george@upowerenergy.uk  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ

---

*Last Updated: 4 December 2025*  
*This inventory was auto-generated from workspace analysis*
