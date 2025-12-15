# Google Sheet Project Information

## Analysis BI Enhanced Sheet

### Basic Information
- **Spreadsheet ID**: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`
- **Sheet URL**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
- **Sheet Name**: "Analysis BI Enhanced"
- **Purpose**: Unified GB Power Market analysis combining historical and IRIS real-time data

### Data Sources
- **BigQuery Project**: `inner-cinema-476211-u9`
- **Dataset**: `uk_energy_prod`
- **Tables Used**:
  - `bmrs_fuelinst` + `bmrs_fuelinst_iris` (Generation data)
  - `bmrs_freq` + `bmrs_freq_iris` (Frequency data)
  - `bmrs_mid` (Market Index Prices)
  - `bmrs_netbsad` (Balancing Services costs)

### Sheet Structure

#### Section 1: Generation Analysis (Rows 1-30)
- Fuel type breakdown
- Total generation (MWh)
- Renewable vs Non-renewable percentage
- Time period selector (Cell B5)

#### Section 2: Frequency Analysis (Rows 32-60)
- System frequency statistics
- Average frequency (Hz)
- Stability assessment
- Historical frequency trends

#### Section 3: Price Analysis (Rows 62-90)
- Market Index Data (MID) prices
- Average price (£/MWh)
- Price volatility
- Volume-weighted prices

#### Section 4: Balancing Costs (Rows 92-120)
- Net Balancing Services Adjustment Data (NETBSAD)
- Buy vs Sell price breakdown
- Cost adjustments
- Balancing energy volumes

### Interactive Features

#### Custom Menu: ⚡ Power Market
1. **🔄 Refresh Data Now** - Refreshes with current date range
2. **📊 Quick Refresh (1 Week)** - Sets 1-week range and refreshes
3. **📊 Quick Refresh (1 Month)** - Sets 1-month range and refreshes
4. **ℹ️ Help** - Shows usage instructions

#### Control Cells
- **Cell B5**: Date range selector (1 Day, 1 Week, 1 Month, 3 Months, 6 Months, 1 Year)
- **Cell L5**: Status indicator (✅ Ready, ⏳ Refreshing, ✅ Up to date, ❌ Error)
- **Cell M5**: Hidden trigger cell (used by automation)

### Automation System

#### Python Scripts
1. **create_analysis_bi_enhanced.py** - Initial sheet creation
2. **update_analysis_bi_enhanced.py** - Data refresh script
3. **watch_sheet_for_refresh.py** - Background watcher daemon

#### Google Apps Script
- **File**: `google_sheets_menu.gs`
- **Functions**: Menu creation, refresh trigger, status updates

#### Workflow
```
User clicks menu → Apps Script writes trigger → Python watcher detects → 
Runs update script → Updates data → Updates status → Complete
```

### Latest Data (as of Oct 31, 2025)
- **Total Generation**: 227,105 MWh
- **Renewable %**: 50.6%
- **Average Frequency**: 49.965 Hz
- **Average Price**: £37.46/MWh
- **Fuel Types**: 20 different sources

### Python Environment
- **Python Version**: 3.9.6 (system Python)
- **Key Packages**:
  - `gspread` (Google Sheets API)
  - `google-cloud-bigquery` (BigQuery client)
  - `gspread-formatting` (Cell formatting)
  - `google-auth` (Authentication)

### Authentication Files
- **Google Sheets**: `token.pickle` (OAuth token)
- **BigQuery**: Service account credentials in project settings

### Related Documentation
- `SHEET_REFRESH_COMPLETE.md` - Quick start guide
- `SHEET_REFRESH_MENU_GUIDE.md` - Complete documentation
- `ENHANCED_BI_SUCCESS.md` - Implementation details
- `QUICK_REFERENCE_BI_SHEET.md` - Command reference

### How to Use This Sheet

1. **View Data**: Open sheet URL above
2. **Change Date Range**: Select from dropdown in B5
3. **Refresh Data**: Click ⚡ Power Market > 🔄 Refresh Data Now
4. **Monitor Status**: Watch cell L5 for progress
5. **Manual Refresh**: Run `python3 update_analysis_bi_enhanced.py`

### Support Files in Project Directory
- `google_sheets_menu.gs` - Apps Script code
- `watch_sheet_for_refresh.py` - Watcher daemon
- `setup_sheet_refresh_menu.py` - Setup helper
- `SHEET_REFRESH_COMPLETE.md` - Documentation

---

**Last Updated**: October 31, 2025
**Status**: ✅ Fully operational with custom menu refresh system
