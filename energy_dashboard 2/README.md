# GB Energy Dashboard - Integrated System

**Comprehensive UK Energy Market Analysis Platform**  
Real-time analytics + Behind-the-Meter PPA Revenue + ML Forecasting + Interactive Maps

---

## 🎯 What This System Does

This is the **production-ready** GB Power Market dashboard that combines:

1. **VLP/Battery Revenue Analysis** - Frequency response, arbitrage, balancing mechanism tracking
2. **BtM PPA Revenue Calculations** ⭐ *NEW* - Behind-the-Meter PPA profit optimization with BigQuery
3. **Wind Forecasting** - ML-based deviation scoring and turbine-level predictions
4. **Grid Constraints** - ML probability models for constraint predictions
5. **System Price Spreads** - SSP-SBP analysis with BM price forecasting
6. **Interactive Maps** - Folium-based maps with GSP headroom, IC flows, DNO boundaries
7. **Long-term Projections** - 10-year revenue modeling with degradation
8. **Google Sheets Integration** - Auto-updating dashboard with KPIs

---

## 🏗️ Architecture

```
energy_dashboard 2/
├── dashboard.py           # Main orchestration (run this!)
├── bigquery/              # BigQuery data queries
│   ├── client.py
│   ├── queries.py         # VLP, wind, spreads, BESS, GSP, IC queries
│   ├── geo.py             # Geographic data for maps
│   └── filter_engine.py   # User filter resolution
├── finance/               # Revenue calculations
│   ├── btm_ppa.py         # ⭐ BtM PPA revenue (NEW)
│   └── long_term.py       # 10-year projections
├── ml/                    # Machine learning models
│   ├── wind_deviation.py
│   ├── gsp_forecast.py
│   ├── predict_constraints.py
│   ├── bm_price.py
│   └── turbine_forecast.py
├── bess/                  # Battery analytics
│   └── soh_model.py       # State of Health estimation
├── charts/                # Matplotlib visualizations
│   ├── vlp_chart.py
│   ├── bess_chart.py
│   ├── wind_chart.py
│   ├── spreads_chart.py
│   ├── bm_price_chart.py
│   ├── projections_chart.py
│   └── btm_ppa_chart.py   # ⭐ BtM PPA breakdown (NEW)
├── maps/                  # Interactive Folium maps
│   └── map_builder.py
├── sheets/                # Google Sheets writer
│   └── writer.py          # Updated with BtM PPA KPIs
├── api/                   # FastAPI server (optional)
│   └── server.py
└── requirements.txt
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd "energy_dashboard 2"
pip3 install -r requirements.txt
```

**Dependencies:**
- `google-cloud-bigquery` - BigQuery API
- `gspread` - Google Sheets API
- `pandas` - Data manipulation
- `matplotlib` - Charts
- `folium` - Interactive maps
- `fastapi` + `uvicorn` - Web API (optional)

### 2. Configure Environment

Create `.env` file in the `energy_dashboard 2/` directory:

```bash
# BigQuery
GOOGLE_APPLICATION_CREDENTIALS="/path/to/inner-cinema-credentials.json"
BIGQUERY_PROJECT_ID="inner-cinema-476211-u9"
BIGQUERY_DATASET="uk_energy_prod"

# Google Sheets
DASHBOARD_SPREADSHEET_ID="1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
DASHBOARD_SHEET_NAME="Dashboard"

# Optional: Override defaults
CM_PRICE="20"  # Capacity Market price (£/kW)
FR_REVENUE_FALLBACK="50000"  # Frequency response revenue fallback
ARB_REVENUE_FALLBACK="8000"  # Arbitrage revenue fallback
```

### 3. Run the Dashboard

```bash
python3 dashboard.py
```

Or with custom filters:

```python
from dashboard import run_dashboard

filters = {
    "dateRange": "30D",  # Last 30 days
    "gspGroup": None,    # All GSPs
    "fuelType": "WIND"   # Filter to wind only
}

run_dashboard(filters)
```

### 4. View Outputs

- **Charts**: `out/*.png` (7 charts including BtM PPA breakdown)
- **Map**: `out/map.html` (open in browser)
- **Google Sheets**: Auto-updated with latest KPIs

---

## 💰 BtM PPA Revenue System (NEW)

### What It Calculates

The **Behind-the-Meter Power Purchase Agreement** module calculates profit from:

1. **Stream 1 (Direct Import)**: Import energy when cost < PPA price (£150/MWh)
2. **Stream 2 (Battery + VLP)**: Charge battery during cheap periods, discharge during expensive
3. **Curtailment Revenue**: Track BM acceptances from ESO (taking generation offline)
4. **Dynamic Containment**: Frequency response service revenue

### Key Features

✅ **Real System Prices from BigQuery** (last 180 days)  
✅ **DUoS Band Classification** (RED/AMBER/GREEN periods)  
✅ **Optimal Battery Charging** (GREEN priority, never charge RED)  
✅ **Separate Levy Tracking** (TNUoS, BSUoS, CCL, RO, FiT)  
✅ **VLP Revenue** (£12/MWh realistic rate, 20% participation)  
✅ **100% RED Coverage Calculation**  
✅ **Battery Cycle Tracking** (degradation analysis)

### BtM PPA Chart

The `btm_ppa_chart.py` generates a **4-panel visualization**:

1. **Revenue Streams** - Profit breakdown by stream
2. **Charging Strategy** - GREEN/AMBER/RED charging pie chart
3. **RED Coverage** - Battery coverage of expensive RED periods
4. **Cost Breakdown** - System price + DUoS + Levies by band

### Configuration

Edit `finance/btm_ppa.py` constants:

```python
# BESS Configuration
BESS_CAPACITY_MWH = 5.0
BESS_POWER_MW = 2.5
BESS_EFFICIENCY = 0.85
MAX_CYCLES_PER_DAY = 4

# PPA Price
PPA_PRICE = 150.0  # £/MWh

# Fixed Levies
TNUOS_RATE = 12.50
BSUOS_RATE = 4.50
CCL_RATE = 7.75
RO_RATE = 61.90
FIT_RATE = 11.50

# DUoS Rates (NGED West Midlands example)
DUOS_RED = 17.64    # £/MWh
DUOS_AMBER = 2.05
DUOS_GREEN = 0.11

# VLP Revenue
VLP_AVG_UPLIFT = 12.0  # £/MWh
VLP_BM_UNITS = ["2__FBPGM001", "2__FBPGM002"]  # Your battery BMUs
```

### Example Output

```
═══════════════════════════════════════════════════════════
BtM PPA REVENUE SUMMARY
═══════════════════════════════════════════════════════════

STREAM 1 (Direct Import):
  - Volume: 15,400 MWh
  - Revenue: £2,310,000
  - Cost: £2,130,000
  - Profit: £180,000

STREAM 2 (Battery + VLP):
  - Charged: 1,083 MWh (217 cycles)
  - Discharged: 921 MWh
  - PPA Revenue: £138,150
  - VLP Revenue: £2,763
  - Charging Cost: £153,870
  - Profit: -£12,957

CURTAILMENT (BM):
  - Curtailment MWh: 450
  - Curtailment Revenue: £35,000
  - Total BM Revenue: £45,000

TOTAL ANNUAL PROFIT:
  - BtM PPA: £167,043
  - Dynamic Containment: £195,458
  - TOTAL: £362,501

BATTERY PERFORMANCE:
  - RED Coverage: 100.0%
  - Annual Cycles: 217
  - Efficiency: 85%
```

---

## 📊 Dashboard Output Structure

### Google Sheets Layout

**Row 6**: VLP Flexibility KPI  
```
💰 VLP FLEXIBILITY | ⚡ Units: 12 | ⚡ Capacity: 52 MW | 📊 FR Revenue: £50,000/yr | ⚡ Arbitrage: £8,000/yr | 💷 Total: £58,000/yr
```

**Row 7**: BESS Portfolio KPI  
```
🔋 BESS PORTFOLIO | Avg availability: 94.2% | Top unit: 2__FBPGM001 | SoH: 97.3% | Units: 12
```

**Row 8**: BtM PPA Profit KPI ⭐ *NEW*  
```
💰 BtM PPA PROFIT | Total Revenue: £2,448,150 | Total Costs: £2,283,870 | Net Profit: £362,501 | RED Coverage: 100%
```

**Rows 10+**: Insights Bullets  
- VLP revenue breakdown
- **BtM PPA profit summary** ⭐
- **Curtailment revenue** ⭐
- Wind forecast error
- System price spreads

---

## 🔌 API Server (Optional)

Deploy as FastAPI service:

```bash
cd api/
uvicorn server:app --host 0.0.0.0 --port 8000
```

**Endpoints:**
- `GET /health` - Health check
- `POST /run_dashboard` - Trigger dashboard run with filters
- `GET /latest_charts` - Retrieve generated charts
- `GET /map` - Serve interactive map

---

## 🧪 Testing

### Test BtM PPA Module Standalone

```python
from google.cloud import bigquery
from finance.btm_ppa import get_btm_ppa_metrics

client = bigquery.Client(
    project="inner-cinema-476211-u9",
    location="US"
)

btm_results, curtailment = get_btm_ppa_metrics(client)

print(f"Total Profit: £{btm_results['total_profit']:,.0f}")
print(f"RED Coverage: {btm_results['red_coverage']:.1f}%")
print(f"Battery Cycles: {btm_results['stream2']['cycles']:.1f}")
```

### Test Chart Generation

```python
from charts.btm_ppa_chart import build_btm_ppa_chart, build_btm_ppa_summary_text

chart_path = build_btm_ppa_chart(btm_results, curtailment, "test_btm_chart.png")
print(f"Chart saved: {chart_path}")

summary = build_btm_ppa_summary_text(btm_results, curtailment)
print(summary)
```

---

## 📦 Deployment Options

### 1. Local Cron Job

```bash
# Run every 15 minutes
*/15 * * * * cd /path/to/energy_dashboard\ 2 && python3 dashboard.py >> logs/dashboard.log 2>&1
```

### 2. Docker Container

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python3", "dashboard.py"]
```

### 3. Cloud Function (GCP)

Deploy `dashboard.py` as Cloud Function triggered by Pub/Sub or HTTP.

### 4. AlmaLinux Server (Existing)

```bash
scp -r "energy_dashboard 2" root@94.237.55.234:/opt/gb-energy-dashboard/
ssh root@94.237.55.234
cd /opt/gb-energy-dashboard/energy_dashboard\ 2
nohup python3 dashboard.py &
```

---

## 🔧 Troubleshooting

### "ModuleNotFoundError: No module named 'finance.btm_ppa'"

```bash
# Ensure you're in the energy_dashboard 2 directory
cd "energy_dashboard 2"
python3 dashboard.py
```

### "BigQuery: Table not found"

Check table exists:
```bash
bq ls inner-cinema-476211-u9:uk_energy_prod
```

Create missing views if needed (see `BIGQUERY_IMPLEMENTATION_GUIDE.md`).

### "Google Sheets: Insufficient Permission"

```bash
# Grant service account Editor access to spreadsheet
# Share: inner-cinema-credentials@inner-cinema-476211-u9.iam.gserviceaccount.com
```

### "Charts not generating"

Check matplotlib backend:
```python
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
```

### "BtM PPA profit is negative"

Check system prices are reasonable:
```python
from finance.btm_ppa import get_system_prices_by_band
prices = get_system_prices_by_band(client, "inner-cinema-476211-u9", "uk_energy_prod")
print(prices)  # Should be {'green': 30-50, 'amber': 50-70, 'red': 70-100}
```

---

## 📚 Related Documentation

- **`BIGQUERY_IMPLEMENTATION_GUIDE.md`** - BigQuery views setup
- **`BtM_PPA_REVENUE_CALCULATION_SUMMARY.md`** - Detailed BtM PPA logic
- **`BTM_PPA_DECISION_LOGIC.md`** - Business rules explanation
- **`STOP_DATA_ARCHITECTURE_REFERENCE.md`** - Data schema reference
- **`PROJECT_CONFIGURATION.md`** - Full system config

---

## 🚧 Future Enhancements

- [ ] Real-time WebSocket updates for live dashboard
- [ ] Historical backtesting for BtM PPA strategy optimization
- [ ] Multi-site portfolio analysis
- [ ] Enhanced ML models (LSTM for price forecasting)
- [ ] Automated alerts for high-profit opportunities
- [ ] Export to PDF reports

---

## 🤝 Contributing

This is a production system. Test changes thoroughly:

1. Fork the repo
2. Create feature branch
3. Test with `python3 -m pytest tests/`
4. Submit PR with clear description

---

## 📄 License

Proprietary - UPower Energy Ltd  
**Maintainer**: George Major (george@upowerenergy.uk)

---

**Last Updated**: December 2, 2025  
**Version**: 2.0 (with BtM PPA integration)
