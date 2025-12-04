# GB Power Market - Complete Optimization Engine Deployment Guide

## 🎉 Project Complete!

You now have a **complete Behind-the-Meter BESS optimization system** with:

✅ **CLASP Apps Script Dashboard** (`energy_dashboard_clasp/`)  
✅ **BigQuery Unified View** (`bigquery/v_btm_bess_inputs.sql`)  
✅ **Forward-Looking Optimizer** (`optimised_bess_engine.py`)  
✅ **Full Simulation Engine** (`full_btm_bess_simulation.py`)  
✅ **Google Sheets Integration**  

---

## 📁 Files Created

```
GB-Power-Market-JJ/
│
├── energy_dashboard_clasp/          # Google Apps Script project
│   ├── .clasp.json                  # CLASP config (needs script ID)
│   ├── appsscript.json              # Apps Script manifest
│   ├── Code.gs                      # Main menu & triggers
│   ├── Dashboard.gs                 # Dashboard refresh logic
│   ├── Charts.gs                    # Chart building
│   ├── Utils.gs                     # Helper functions
│   └── README.md                    # CLASP deployment guide
│
├── bigquery/
│   └── v_btm_bess_inputs.sql        # Unified data view
│
├── optimised_bess_engine.py         # 48-period look-ahead optimizer
├── full_btm_bess_simulation.py      # Complete simulation pipeline
└── OPTIMIZATION_ENGINE_GUIDE.md     # This file
```

---

## 🚀 Deployment Steps

### Step 1: Create BigQuery View

```bash
# Copy SQL from bigquery/v_btm_bess_inputs.sql
# Paste into BigQuery Console: https://console.cloud.google.com/bigquery

# Or run via bq CLI:
bq query --use_legacy_sql=false < bigquery/v_btm_bess_inputs.sql
```

**What it does**: Creates unified view combining:
- System Buy Prices (bmrs_costs)
- DUoS rates (RED/AMBER/GREEN)
- All levies (£98.15/MWh)
- PPA price (£150/MWh)
- BM/VLP revenue
- Dynamic Containment revenue
- Capacity Market revenue

### Step 2: Deploy Apps Script to Google Sheets

```bash
# Install CLASP
npm install -g @google/clasp

# Login
clasp login

# Navigate to CLASP folder
cd energy_dashboard_clasp

# Create new project
clasp create --type sheets --title "GB Energy Dashboard"

# This creates a new Google Sheet with bound Apps Script
# Copy the script ID from output and paste into .clasp.json

# Push code
clasp push

# Open in browser
clasp open
```

**What it creates**:
- Google Sheet with BESS and Dashboard tabs
- Custom menu: "⚡ Energy Tools"
- Auto-refresh trigger (every 5 minutes)
- 4 charts (SoC, Charge/Discharge, Profit, Revenue vs Cost)

### Step 3: Run Python Simulation

```bash
# Ensure credentials file exists
ls inner-cinema-credentials.json

# Run simulation
python3 full_btm_bess_simulation.py
```

**What it does**:
1. Fetches last 30 days from BigQuery view
2. Applies 48-period look-ahead optimization
3. Simulates SoC time-series
4. Calculates EBITDA
5. Writes results to Google Sheets

---

## 🔧 Configuration

### Battery Parameters

Edit in `optimised_bess_engine.py`:

```python
BATTERY_POWER_MW = 2.5       # Power rating
BATTERY_ENERGY_MWH = 5.0     # Capacity
EFFICIENCY = 0.85            # Round-trip efficiency
SOC_MIN = 0.05 * 5.0         # Minimum SoC (5%)
SOC_MAX = 5.0                # Maximum SoC (100%)
HORIZON = 48                 # Look-ahead periods (24h)
```

### Financial Parameters

Edit in `full_btm_bess_simulation.py`:

```python
INITIAL_SOC = 2.5                # Starting charge (MWh)
FIXED_OPEX_ANNUAL = 100_000      # Annual fixed costs (£)
VARIABLE_OPEX_PER_MWH = 3.0      # Variable cost per MWh (£)
DAYS_TO_ANALYZE = 30             # Analysis period
```

### Google Sheets

Edit in both Python files:

```python
SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
```

---

## 📊 How It Works

### 1. Optimization Logic

**Charge Decision**:
```
η * max(future_R) > cost_now
```
- Only charge if future discharge value (after efficiency losses) exceeds current cost
- Looks ahead 48 periods (24 hours)

**Discharge Decision**:
```
R_now > min(future_cost)
```
- Only discharge if current revenue exceeds best future charging opportunity
- Prevents premature discharge before high-value periods

### 2. Data Flow

```
BigQuery View (v_btm_bess_inputs)
    ↓
Python Optimizer (optimised_bess_engine.py)
    ↓
SoC Simulation (full_btm_bess_simulation.py)
    ↓
Google Sheets (BESS + Dashboard tabs)
    ↓
Apps Script Visualization (energy_dashboard_clasp/)
```

### 3. Revenue Streams

1. **PPA Discharge**: £150/MWh (when discharging to site)
2. **BM/VLP Uplift**: £12/MWh (20% of discharge in balancing mechanism)
3. **Dynamic Containment**: £195,458/year (grid stability services)
4. **Capacity Market**: £5/MWh (contract payments)

### 4. Cost Components

1. **System Buy Price**: Variable (market rate)
2. **DUoS Charges**: RED £17.64, AMBER £2.05, GREEN £0.11 per MWh
3. **Fixed Levies**: £98.15/MWh (TNUoS + BSUoS + CCL + RO + FiT)
4. **Variable OpEx**: £3/MWh discharged
5. **Fixed OpEx**: £100,000/year

---

## 📈 Dashboard Features

### KPI Strip (Row 2)
- Charged (MWh)
- Discharged (MWh)
- Revenue (£)
- Cost (£)
- EBITDA (£)

### Charts (Auto-generated)

1. **State of Charge** (Row 8, Col 1)
   - Shows battery SoC over time
   - 5 MWh capacity with min/max limits

2. **Charge/Discharge** (Row 8, Col 10)
   - Green bars = charging
   - Red bars = discharging

3. **Profit Per Period** (Row 25, Col 1)
   - Shows settlement period profitability
   - Identifies best/worst periods

4. **Revenue vs Cost** (Row 25, Col 10)
   - Compares revenue and cost streams
   - Shows gross margin

### Custom Menu: ⚡ Energy Tools

- 🔁 **Refresh Dashboard** - Update KPIs from BESS data
- 📊 **Rebuild Charts** - Regenerate visualizations
- ⏱ **Enable Auto-Refresh** - 5-minute updates
- ❌ **Disable Auto-Refresh** - Stop automation

---

## 🧪 Testing

### Test Optimization Engine

```python
from optimised_bess_engine import optimize_bess, simulate_soc_optimized

# Load sample data
df = pd.read_csv("sample_data.csv")

# Optimize
df_opt = optimize_bess(df)

# Simulate
df_sim = simulate_soc_optimized(df_opt, initial_soc=2.5)

# View results
print(df_sim[['ts_halfhour', 'action', 'soc_end', 'sp_net']].head(20))
```

### Test Google Sheets Connection

```python
from full_btm_bess_simulation import get_sheets_client

gc = get_sheets_client()
ss = gc.open_by_key("YOUR_SPREADSHEET_ID")
print(f"✅ Connected to: {ss.title}")
```

### Test BigQuery View

```sql
-- Run in BigQuery Console
SELECT *
FROM `inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs`
WHERE settlementDate >= CURRENT_DATE() - 7
ORDER BY ts_halfhour DESC
LIMIT 100;
```

---

## 🔍 Monitoring

### Check Simulation Logs

```bash
# View execution output
python3 full_btm_bess_simulation.py | tee simulation.log

# Monitor real-time
tail -f simulation.log
```

### Check Apps Script Logs

```bash
# In terminal
clasp logs

# Or in browser: Extensions → Apps Script → Executions
```

### Check BigQuery View

```bash
# Count records
bq query "SELECT COUNT(*) FROM uk_energy_prod.v_btm_bess_inputs"

# Check latest data
bq query "SELECT MAX(settlementDate) FROM uk_energy_prod.v_btm_bess_inputs"
```

---

## 🆘 Troubleshooting

### Issue: "View not found"
**Solution**: Run `bigquery/v_btm_bess_inputs.sql` in BigQuery Console

### Issue: "BESS sheet not found"
**Solution**: Manually create sheets named "BESS" and "Dashboard" in Google Sheets

### Issue: "Credentials error"
**Solution**: Ensure `inner-cinema-credentials.json` exists and has correct permissions:
- BigQuery Data Viewer
- BigQuery Job User
- Google Sheets Editor

### Issue: "No data in date range"
**Solution**: Adjust `DAYS_TO_ANALYZE` or check BigQuery data availability

### Issue: "Charts not updating"
**Solution**: In Google Sheets menu: ⚡ Energy Tools → Rebuild Charts

---

## 📚 Next Steps

### Option 1: Add Degradation Model

Track battery health:
- Cycle count
- Depth of discharge
- Throughput degradation
- Capex amortization

### Option 2: Add ML Forecasting

Predict future prices:
- Wind output forecast
- System stress indicators
- Price spike prediction

### Option 3: Add Real-Time API

Deploy Cloud Run endpoint:
- Current SoC
- Next action recommendation
- Live profitability

### Option 4: Add Constraints

Operational limits:
- Minimum uptime
- Frequency response requirements
- Grid constraints

---

## 📞 Support

For issues or questions:
- Main project: `GB-Power-Market-JJ`
- Developer: george@upowerenergy.uk
- Status: ✅ Production Ready (December 2025)

---

**Last Updated**: 2 December 2025  
**Version**: 1.0  
**License**: Proprietary - UPower Energy
