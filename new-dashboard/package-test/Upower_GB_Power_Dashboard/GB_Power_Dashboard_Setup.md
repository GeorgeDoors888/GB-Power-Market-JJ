# Upower GB Energy Dashboard - Setup Guide

## Quick Start

### 1. Create Google Spreadsheet

1. Go to https://sheets.google.com
2. Create new spreadsheet
3. Name it "Upower GB Energy Dashboard"
4. Copy the Spreadsheet ID from URL:
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit
   ```

### 2. Deploy Apps Script

1. In your spreadsheet: **Extensions → Apps Script**
2. Delete default code
3. Open `apps_script_code.gs` from this package
4. Copy ALL contents
5. Paste into Apps Script editor
6. Update line 11 with your Spreadsheet ID:
   ```javascript
   SPREADSHEET_ID: 'YOUR_SPREADSHEET_ID_HERE',
   ```
7. **File → Save** (Ctrl+S)
8. Refresh spreadsheet - menus should appear!

### 3. Setup Python Auto-Updater (Optional)

**Prerequisites:**
- Python 3.9+
- GCP Project with BigQuery enabled
- Service Account credentials JSON

**Install dependencies:**
```bash
pip3 install google-cloud-bigquery gspread google-auth pandas db-dtypes pyarrow
```

**Configure:**
1. Copy your service account credentials to same folder
2. Edit `dashboard_updater.py`:
   - Line 24: Update `SPREADSHEET_ID`
   - Line 25-26: Update `PROJECT_ID` and `DATASET`
   - Line 27: Update `SA_FILE` filename
3. Share spreadsheet with service account email

**Test run:**
```bash
python3 dashboard_updater.py
```

**Setup auto-refresh (runs every 5 minutes):**
```bash
crontab -e

# Add this line:
*/5 * * * * cd /path/to/dashboard && python3 dashboard_updater.py >> logs/updater.log 2>&1
```

## Features

### 📊 Dashboard Sheets
- **Dashboard** - Main KPIs and generation data
- **BESS** - Battery storage analysis
- **Charts** - Price, demand, frequency charts
- **Outages** - Generator unavailability

### 🎨 Apps Script Menus

**🗺️ Maps**
- Constraint Map - Interactive transmission constraints
- Generator Map - UK power stations

**🔄 Data**
- Refresh All Data - Update all sheets
- Individual sheet refreshes

**🎨 Format**
- Apply Theme - Upower branding
- Format Numbers - Consistent formatting
- Auto-resize Columns

**🛠️ Tools**
- Clear Old Data - Cleanup
- Export to CSV - Data export
- About Dashboard - Info

## Data Sources

All data from **Elexon BMRS** (Balancing Mechanism Reporting Service):
- Real-time generation by fuel type
- System demand and prices
- Transmission constraints
- Generator outages
- Interconnector flows

## Architecture

```
BigQuery (Data Warehouse)
      ↓
Python Updater (Every 5 min)
      ↓
Google Sheets (Dashboard)
      ↓
Apps Script (Interactive features)
```

## Troubleshooting

**No menus appearing?**
- Refresh spreadsheet (F5)
- Check Apps Script deployed correctly
- Check browser console for errors

**Python updater failing?**
- Check credentials file exists
- Verify BigQuery project ID correct
- Check service account has Editor access to spreadsheet

**Charts not showing data?**
- Ensure data exists in chart source sheets
- Charts update automatically when data changes

## Support

**Repository:** https://github.com/GeorgeDoors888/GB-Power-Market-JJ

**Documentation:** See project README for detailed guides

**Contact:** george@upowerenergy.uk
