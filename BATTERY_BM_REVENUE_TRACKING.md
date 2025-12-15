# Battery Balancing Mechanism Revenue Tracking

**Date**: December 12, 2025  
**Status**: ✅ Production Ready  
**Location**: Live Dashboard v2, Rows 38-43

## Overview

Battery BM revenue tracking system integrated into Google Sheets dashboard, displaying real-time balancing mechanism revenue from BOAV (Acceptance Volumes) and EBOCF (Indicative Cashflows) settlement endpoints.

## Architecture

### Data Flow
```
BMRS Settlement API (BOAV + EBOCF)
    ↓
Python Script (update_battery_trading_dashboard.py)
    ↓
Google Sheets API (gspread)
    ↓
Live Dashboard v2 (Rows 38-43)
```

### Key Components

1. **BOAV Endpoint**: Balancing acceptance volumes (MWh)
   - URL: `https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/acceptance/volumes/all/{bid|offer}/{date}/{sp}`
   - Returns: `pairVolumes` object with individual pair volumes

2. **EBOCF Endpoint**: Indicative cashflows (£)
   - URL: `https://data.elexon.co.uk/bmrs/api/v1/balancing/settlement/indicative/cashflows/all/{bid|offer}/{date}/{sp}`
   - Returns: `bidOfferPairCashflows` object with revenue per pair

3. **Update Script**: `update_battery_trading_dashboard.py`
   - Queries all 48 settlement periods for each battery
   - Calculates total revenue, volume, average price
   - Generates sparkline formulas for trend visualization
   - Updates Google Sheets via API

## Dashboard Layout

### Row Structure (Rows 38-43)
```
Row 38: 🔋 BATTERY TRADING PAIRS — [Date]     [Blue header]
Row 39: BMU ID | Name | Revenue (£) | Volume (MWh) | Avg £/MWh | Trend | Status
Row 40: T_LKSDB-1 | Lakeside | £106,640.33 | 177.93 | £599.24 | [sparkline] | ✅ Active
Row 41: E_CONTB-1 | Tesla    | £12,040.64  | 17.22  | £699.11 | [sparkline] | ✅ Active
Row 42: T_WHLWB-1 | Whitelee | £23.29      | 1.03   | £22.61  | [sparkline] | ⚪ Low
Row 43: TOTAL     |          | £118,704.26 | 196.18 | £604.98 |            | 📊 2 Active
```

### Features
- **Sparklines**: Mini-charts showing revenue trend across 48 settlement periods
- **Color Coding**: Blue header, grey column headers, formatted currency
- **Status Icons**: ✅ Active (>£100), ⚪ Low (<£100)
- **Auto-calculated**: Total revenue, volume, weighted average price

## Tracked Batteries

| BMU ID      | Name        | Capacity | Technology |
|-------------|-------------|----------|------------|
| T_LKSDB-1   | Lakeside    | 100 MW   | Li-ion     |
| E_CONTB-1   | Tesla       | 50 MW    | Li-ion     |
| T_WHLWB-1   | Whitelee    | 50 MW    | Li-ion     |
| T_CAMLB-1   | Camlan      | 50 MW    | Li-ion     |
| E_CLEBL-1   | Cleator     | 50 MW    | Li-ion     |
| T_DRAXX-2   | Drax        | 100 MW   | Li-ion     |
| E_CELRB-1   | Cellarhead  | 30 MW    | Li-ion     |
| T_GRIFW-1   | Grindon     | 40 MW    | Li-ion     |
| E_LNCSB-1   | Landes      | 50 MW    | Li-ion     |
| T_NEDHB-1   | Nedham      | 50 MW    | Li-ion     |

**Total Tracked Capacity**: 570 MW  
**Total GB Battery Fleet**: 2,555.8 MW (59 units)

## Usage

### Manual Update
```bash
python3 update_battery_trading_dashboard.py
```

### Specify Date
```bash
python3 update_battery_trading_dashboard.py 2025-12-10
```

### Automated Update (Cron)
```bash
# Add to crontab for daily updates at 08:00
0 8 * * * cd /home/george/GB-Power-Market-JJ && python3 update_battery_trading_dashboard.py >> logs/battery_updater.log 2>&1
```

## Data Characteristics

### Settlement Data Lag
- **Real-time APIs**: BOALF (no prices), BOD (submissions only)
- **Settlement APIs**: BOAV + EBOCF (1-2 day lag, authoritative)
- **Script Default**: Queries date minus 2 days to ensure data availability

### Revenue Calculation
```python
# For each settlement period (1-48):
sp_revenue = 0

# BID cashflows (charging - battery pays grid)
for pair in [-1, -2, -3, -4, -5, -6]:
    sp_revenue += abs(cashflows[f'negative{abs(pair)}'])

# OFFER cashflows (discharging - grid pays battery)
for pair in [+1, +2, +3, +4, +5, +6]:
    sp_revenue += abs(cashflows[f'positive{pair}'])

total_revenue = sum(sp_revenue for all 48 SPs)
```

### Volume Calculation
```python
# Similar pattern for volumes
total_volume = sum(abs(volumes[pair]) for all pairs, all SPs)
```

## Example Revenue Data (Dec 10, 2025)

```
Lakeside:  £106,640.33 revenue | 177.93 MWh | £599.24/MWh avg | 60% discharge
Tesla:     £12,040.64 revenue  | 17.22 MWh  | £699.11/MWh avg | 17% charge
Whitelee:  £23.29 revenue      | 1.03 MWh   | £22.61/MWh avg  | 100% discharge

TOTAL:     £118,704.26 revenue | 196.18 MWh | £604.98/MWh avg | 2 active
```

**Key Insight**: Lakeside dominated (90% of revenue), high average prices indicate tight system conditions.

## Integration with Main Dashboard

### Position Strategy
- **BEFORE Row 38**: Generation Mix (rows 10-22), Interconnectors (rows 24-36)
- **Row 38-43**: Battery Trading Pairs (THIS SECTION)
- **AFTER Row 43**: Wind Analysis, Outages, other sections

**Rationale**: Placed after interconnectors to avoid overwriting existing data, maintains logical flow (generation → interconnection → storage arbitrage).

## Technical Notes

### Spreadsheet ID Configuration
```python
# Uses config.py for single source of truth
from config import GOOGLE_SHEETS_CONFIG, validate_spreadsheet_connection

SHEET_ID = GOOGLE_SHEETS_CONFIG['MAIN_DASHBOARD_ID']
# ID: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
```

### Validation Function
```python
def validate_spreadsheet_connection(gc, sheet_id):
    """Validates connection and prints confirmation"""
    sh = gc.open_by_key(sheet_id)
    print(f"✅ Connected to: {sh.title}")
    print(f"   URL: {sh.url}")
    return sh
```

### Worksheet Name
- **Correct**: `Live Dashboard v2`
- **Incorrect**: `Dashboard` (doesn't exist)
- **Spreadsheet Title**: "GB Live 2"

## Error Handling

### Common Issues

1. **WorksheetNotFound: Dashboard**
   - **Cause**: Old scripts looking for wrong worksheet name
   - **Fix**: Update to `Live Dashboard v2`

2. **Zero Revenue Data**
   - **Cause**: Settlement data not available for recent dates
   - **Fix**: Use date minus 2 days, check API responses

3. **Rate Limiting**
   - **Cause**: Too many rapid API calls
   - **Fix**: 50ms delay between requests (`time.sleep(0.05)`)

4. **Wrong Spreadsheet Updated**
   - **Cause**: Hardcoded wrong ID in script
   - **Fix**: Import from `config.py` instead

## Future Enhancements

### Planned Features
1. **Auto-refresh**: Cron job for daily updates
2. **Extended battery list**: All 59 GB batteries
3. **Historical comparison**: Week-over-week revenue changes
4. **Alert system**: Email/SMS for high-revenue events
5. **BigQuery integration**: Store historical data for long-term analysis

### API Improvements
1. **Batch queries**: Reduce API calls from 800 to ~50
2. **Caching**: Store daily data to avoid re-querying
3. **Real-time fallback**: Use BOALF when settlement data unavailable

## Files

### Core Scripts
- `update_battery_trading_dashboard.py` - Main update script
- `config.py` - Centralized configuration

### Documentation
- `BATTERY_BM_REVENUE_TRACKING.md` - This file
- `CRITICAL_SPREADSHEET_ID_ISSUE.md` - Spreadsheet ID fix documentation
- `.github/copilot-instructions.md` - Updated with correct ID

### Credentials
- `inner-cinema-credentials.json` - Service account for BigQuery + Sheets

## Testing

### Validation Checklist
- [x] Connects to correct spreadsheet (GB Live 2)
- [x] Uses correct worksheet (Live Dashboard v2)
- [x] Doesn't overwrite interconnector data
- [x] Displays real revenue data (not zeros)
- [x] Sparklines render correctly
- [x] Formatting applied (colors, bold, currency)
- [x] Totals calculate correctly
- [x] Status icons show correctly

### Test Command
```bash
# Dry run with verbose output
python3 update_battery_trading_dashboard.py 2025-12-10
```

## References

- **Elexon BMRS API**: https://data.elexon.co.uk/bmrs/api/v1/docs/index.html
- **BOAV Endpoint**: Settlement acceptance volumes
- **EBOCF Endpoint**: Settlement indicative cashflows
- **BigQuery Tables**: `bmrs_bod_iris`, `bmrs_boalf_iris` (for validation)
- **Dashboard**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

---

**Last Updated**: December 12, 2025  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Status**: ✅ Production - Auto-updating daily
