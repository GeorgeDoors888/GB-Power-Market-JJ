# GB ENERGY DASHBOARD V3 – Complete Deployment

This directory contains the complete V3 implementation for the GB Energy Dashboard.

**Spreadsheet**: [1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc](https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/)

## Structure

```
python/
  ├── apply_dashboard_design.py       # Dashboard layout & formatting
  ├── populate_dashboard_tables.py    # BigQuery data loading
  ├── rebuild_dashboard_v3_final.py   # Master rebuild script
  └── requirements.txt                # Python dependencies

appsscript_v3/
  ├── Code.gs                         # Apps Script menu & functions
  ├── DnoMap.html                     # DNO Map selector UI
  └── appsscript.json                 # Apps Script configuration
```

## Quick Start

### 1. Python Setup

```bash
cd python
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Full Rebuild

```bash
python rebuild_dashboard_v3_final.py
```

This will:
1. Populate all backing tables from BigQuery (Chart Data, Outages, ESO Actions, DNO Map, Market Prices, VLP Data)
2. Apply the complete V3 dashboard design
3. Create combo chart + net margin chart

### 3. Apps Script Deployment

The Apps Script files are already deployed via clasp to script project:
`1z1xjMlA_vJd14IC3VtIUA2894Rv-RyBtQ5B2kUOVwfnL_ApoPYHxiUt2`

To update:
```bash
cd appsscript_v3
clasp push
```

## Features

### Dashboard Components

1. **Header Section** (Rows 1-5)
   - Real-time title with timestamp
   - Time range and DNO region filters

2. **KPI Strip** (Rows 9-11, Columns F-L)
   - VLP Revenue (£k)
   - Wholesale Avg Price (£/MWh)
   - Market Volatility (%)
   - All-GB Net Margin
   - Selected DNO Net Margin
   - Selected DNO Volume (MWh)
   - Selected DNO Revenue (£k)
   - Sparklines showing trends

3. **Fuel Mix Table** (Rows 9+, Columns A-E)
   - Current generation by fuel type
   - Interconnector flows with conditional formatting

4. **Active Outages** (Row 27+)
   - Real-time plant outages from REMIT data
   - Shows BM Unit, Plant, Fuel, MW Lost, Region, Start/End times

5. **ESO Balancing Actions** (Row 42+)
   - Recent balancing mechanism activity
   - Shows BM Unit, Mode (Increase/Decrease), MW, Price, Duration

6. **Charts**
   - Combo chart: System overview with prices, demand, generation
   - Net margin line chart: Portfolio profitability over time

### Apps Script Features

- **DNO Map Selector**: Interactive Google Maps sidebar
- Click markers to select DNO regions
- Automatically updates Dashboard!F3 to show DNO-specific KPIs

## Configuration

### Python (workspace-credentials.json)
- Service Account: `jibber-jabber-knowledge@appspot.gserviceaccount.com`
- Impersonates: `george@upowerenergy.uk`
- Project: jibber-jabber-knowledge (Google Workspace)

### BigQuery (inner-cinema-476211-u9)
- Project: inner-cinema-476211-u9
- Dataset: uk_energy_prod
- Tables: bmrs_mid_iris, bmrs_boalf_iris, bmrs_remit_unavailability

## Data Flow

```
BigQuery (IRIS real-time) 
    → Python Scripts
        → Google Sheets Backing Tables
            → Dashboard Formulas & Charts
                → User-Facing Dashboard
```

## Maintenance

### Daily Refresh
```bash
python python/rebuild_dashboard_v3_final.py
```

### Add to Cron
```bash
# Add to crontab for 15-minute refresh
*/15 * * * * cd /Users/georgemajor/GB-Power-Market-JJ && /path/to/venv/bin/python python/rebuild_dashboard_v3_final.py
```

## Troubleshooting

### "Permission denied" errors
- Check service account has Editor access to spreadsheet
- Verify workspace-credentials.json is in python/ directory

### BigQuery errors
- Confirm inner-cinema-476211-u9 project access
- Check IRIS tables exist: bmrs_mid_iris, bmrs_boalf_iris

### Apps Script not showing
- Run clasp push from appsscript_v3/
- Refresh spreadsheet and check "⚡ GB Energy" menu

## Support

**Maintainer**: George Major (george@upowerenergy.uk)  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Status**: ✅ Production (December 2025)
