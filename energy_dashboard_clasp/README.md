# GB Power Market - CLASP Dashboard Project

Google Apps Script dashboard for Behind-the-Meter BESS optimization and monitoring.

## 📁 Project Structure

```
energy_dashboard_clasp/
├── .clasp.json          # CLASP configuration (script ID)
├── appsscript.json      # Apps Script manifest
├── Code.gs              # Main menu and triggers
├── Dashboard.gs         # Dashboard refresh logic
├── Charts.gs            # Chart building functions
├── Utils.gs             # Utility functions
└── README.md            # This file
```

## 🚀 Deployment

### 1. Install CLASP

```bash
npm install -g @google/clasp
```

### 2. Login to Google

```bash
clasp login
```

### 3. Create New Apps Script Project

```bash
cd energy_dashboard_clasp
clasp create --type sheets --title "GB Energy Dashboard"
```

This creates a new Google Sheet with bound Apps Script.

### 4. Update Script ID

Copy the script ID from the output and paste into `.clasp.json`:

```json
{
  "scriptId": "PASTE_YOUR_SCRIPT_ID_HERE",
  "rootDir": "./"
}
```

### 5. Push Code

```bash
clasp push
```

### 6. Open in Browser

```bash
clasp open
```

## 📊 Google Sheets Setup

### Required Sheets

1. **BESS** - Time-series battery data
   - Row 1: Headers
   - Row 2+: Data (timestamps, SoC, charge, discharge, revenue, cost)
   - B3-B7: Summary KPIs

2. **Dashboard** - Visualization and KPIs
   - Row 1: Headers
   - Row 2: KPI values
   - Row 8+: Charts (auto-generated)
   - Row 99: Last updated timestamp

### KPI Locations (BESS Sheet)

- `B3`: Total Charged (MWh)
- `B4`: Total Discharged (MWh)
- `B5`: Total Revenue (£)
- `B6`: Total Cost (£)
- `B7`: EBITDA (£)

### Data Columns (BESS Sheet)

| Column | Field | Description |
|--------|-------|-------------|
| A | ts_halfhour | Timestamp |
| K | charge_mwh | Charge energy |
| L | discharge_mwh | Discharge energy |
| M | soc_end | State of charge |
| N | sp_cost | Settlement period cost |
| O | sp_revenue | Settlement period revenue |
| P | sp_net | Net profit per period |

## 🔧 Features

### Custom Menu: ⚡ Energy Tools

- **🔁 Refresh Dashboard** - Update KPIs from BESS data
- **📊 Rebuild Charts** - Regenerate all visualizations
- **⏱ Enable Auto-Refresh** - 5-minute automatic updates
- **❌ Disable Auto-Refresh** - Stop automatic updates

### Charts Generated

1. **State of Charge** (Row 8, Col 1)
   - Line chart showing battery SoC over time

2. **Charge/Discharge** (Row 8, Col 10)
   - Column chart comparing charge vs discharge

3. **Profit Per Period** (Row 25, Col 1)
   - Line chart showing profitability timeline

4. **Revenue vs Cost** (Row 25, Col 10)
   - Combo chart comparing revenue and cost

## 🔗 Integration with Python

The Python backend (`full_btm_bess_simulation.py`) writes data to the BESS sheet:

```python
from google.oauth2.service_account import Credentials
import gspread

# Connect to Google Sheets
gc = gspread.authorize(creds)
ss = gc.open_by_key(SPREADSHEET_ID)
bess = ss.worksheet("BESS")

# Write time-series data
bess.update("A2", rows)

# Write KPIs
bess.update("B3", [[charged_mwh]])
bess.update("B4", [[discharged_mwh]])
# ... etc
```

## 🎯 Usage Workflow

1. **Python simulation** runs → writes to BigQuery
2. **Python script** queries BigQuery → writes to Google Sheets BESS tab
3. **Apps Script** refreshes dashboard → updates visualizations
4. **Auto-refresh** keeps dashboard current (every 5 minutes)

## 🛠 Development

### Local Development

Edit `.gs` files locally, then:

```bash
clasp push
```

### View Logs

```bash
clasp logs
```

### Open Script Editor

```bash
clasp open
```

## 📋 Requirements

- Google Account with Apps Script enabled
- Node.js and npm (for CLASP)
- Python backend with BigQuery access
- Google Sheets API credentials (`inner-cinema-credentials.json`)

## 🔐 Permissions

The script requires these OAuth scopes (configured in `appsscript.json`):

- `spreadsheets` - Read/write sheet data
- `script.container.ui` - Show custom menus
- `drive` - Access Drive files
- `script.external_request` - Make external API calls

## 📝 Notes

- Auto-refresh creates a time-based trigger (every 5 minutes)
- All timestamps use Europe/London timezone
- Charts auto-scale based on data range (up to 20,000 rows)
- Dashboard formatting uses UK number format (#,##0.00)

## 🆘 Troubleshooting

**Issue**: "BESS sheet not found"
- Solution: Create a sheet named "BESS" with headers in row 1

**Issue**: "Dashboard sheet not found"
- Solution: Create a sheet named "Dashboard"

**Issue**: "Trigger not working"
- Solution: Disable and re-enable auto-refresh from menu

**Issue**: "Charts not updating"
- Solution: Run "Rebuild Charts" from menu

## 📞 Support

For issues, see main project: `GB-Power-Market-JJ`

---

**Last Updated**: December 2025  
**Project**: GB Power Market Behind-the-Meter BESS Optimization
