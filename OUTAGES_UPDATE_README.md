# Dashboard Outages Update System

## Overview
This system automatically updates the GB Power Market Dashboard with live outages data from BigQuery, maintaining consistent formatting and providing comprehensive totals.

## What Was Updated (26 Nov 2025)

### ✅ Live Outages Data
- **Location**: Rows 31-42 in Dashboard sheet
- **Source**: BigQuery `bmrs_remit_unavailability` table
- **Filters**: Only ACTIVE outages (resolved ones automatically removed)
- **Deduplication**: Uses MAX(revisionNumber) per affected unit

### ✅ Row 44 - Total Outages Summary
**Format**: `📊 TOTAL OUTAGES: X,XXX MW (X.XX GW) | Count: XX | Status: 🔴 Critical | +XX more`

- **Total Capacity**: Displayed in both MW and GW
- **Count**: Number of active outages
- **Status Indicators**:
  - 🔴 Critical: > 5,000 MW
  - ⚠️ High: > 3,000 MW
  - 🟡 Moderate: > 1,000 MW
  - 🟢 Low: < 1,000 MW
- **Formatting**: Red background (#e43835), white bold text

### ✅ Consistent Formatting
All values follow this formatting standard:
- **Capacity**: `X,XXX MW` or `X,XXX MW (X.XX GW)` for values ≥ 100 MW
- **Percentages**: `XX.X%`
- **Money**: `£X,XXX` (for cost-related fields)
- **Fuel Types**: Emoji + name (🔥 CCGT, ⚛️ NUCLEAR, 💨 Wind, etc.)

## Current Status (Latest Run)
```
✅ 50 active outages found
✅ Total: 12,813 MW (12.81 GW)
✅ Top 12 displayed in rows 31-42
✅ Row 44 updated with totals and status
```

### Top Outages
1. 🔥 Didcot B main unit 6 - 666 MW (0.67 GW) - 94%
2. ⚛️ Heysham 2 Generator 7 - 660 MW (0.66 GW) - 100%
3. ⚛️ Hartlepool Generator 1 - 620 MW (0.62 GW) - 100%
4. ⚛️ Hartlepool Generator 2 - 620 MW (0.62 GW) - 100%
5. ⚛️ Heysham 1 Generator 2 - 585 MW (0.58 GW) - 100%

## How to Run

### Manual Update
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 update_outages_with_totals.py
```

### Automated Updates
To set up automatic updates every hour:
```bash
# Add to crontab
0 * * * * cd "/Users/georgemajor/GB Power Market JJ" && python3 update_outages_with_totals.py >> outages_update.log 2>&1
```

## File Structure

### Main Script
- `update_outages_with_totals.py` - Main update script with live data and totals

### Previous/Related Scripts
- `update_outages_enhanced.py` - Previous version (no row 44 totals)
- `fix_outages_display.py` - Older display fix script
- `auto_refresh_outages.py` - Auto-refresh variant
- `clear_duplicate_outages.py` - Utility for clearing duplicates

## Data Flow

```
BigQuery (bmrs_remit_unavailability)
    ↓
Filter: Status='Active', Current events only
    ↓
Deduplicate: MAX(revisionNumber) per unit
    ↓
Join: bmu_registration_data (for proper names)
    ↓
Format: GW/MW, %, emojis, status indicators
    ↓
Update: Dashboard rows 31-42 + Row 44 totals
```

## Outage Row Format (Rows 31-42)

| Column | Content | Format |
|--------|---------|--------|
| A | Unit Name | Status emoji + name (e.g., "🔴 Heysham 2") |
| B | Unit Code | NESO unit ID (e.g., "T_HEYM27") |
| C | Fuel Type | Emoji + type (e.g., "⚛️ NUCLEAR") |
| D | Normal Capacity | "X,XXX MW" |
| E | Unavailable Capacity | "X,XXX MW (X.XX GW)" |
| F | Visual Bar | 🟥🟥🟥⬜⬜⬜⬜⬜⬜⬜ (10 blocks) |
| G | Percentage | "XX.X%" |
| H | Cause | Reason for outage |
| I | Start Time | "DD/MM/YYYY HH:MM" |

## Fuel Type Emojis

| Fuel Type | Emoji | Example |
|-----------|-------|---------|
| NUCLEAR | ⚛️ | Heysham, Hartlepool |
| CCGT/Gas | 🔥 | Didcot, Pembroke |
| Wind Offshore | 💨 | Moray, Seagreen |
| Wind Onshore | 💨 | Kilgallioch, Whitelee |
| Hydro Pumped Storage | 💧 | Dinorwig, Cruachan |
| BIOMASS | 🌱 | Drax, Lynemouth |
| Battery Storage | 🔋 | Various batteries |
| Interconnector | 🔌 | IFA, BritNed |
| Solar | ☀️ | Cleve Hill |

## Status Indicators

### Severity (Individual Outages)
- 🔴 Critical: > 500 MW
- ⚠️ Warning: > 200 MW
- 🟡 Moderate: > 100 MW
- 🟢 Low: < 100 MW

### Overall Status (Row 44)
- 🔴 Critical: Total > 5,000 MW
- ⚠️ High: Total > 3,000 MW
- 🟡 Moderate: Total > 1,000 MW
- 🟢 Low: Total < 1,000 MW

## Configuration

### Spreadsheet
- **ID**: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`
- **Sheet**: `Dashboard`
- **Outages Range**: A31:I42 (12 rows max)
- **Totals Row**: Row 44

### BigQuery
- **Project**: `inner-cinema-476211-u9`
- **Dataset**: `uk_energy_prod`
- **Table**: `bmrs_remit_unavailability`
- **Join Table**: `bmu_registration_data`

### Thresholds
- Minimum outage size: 50 MW
- Display limit: Top 12 outages
- Status update: Active events only

## Maintenance

### Daily Tasks
1. Monitor the auto-update logs
2. Verify row 44 totals are accurate
3. Check for any new fuel types needing emojis

### Weekly Tasks
1. Review outage trends
2. Update FUEL_EMOJIS dict if new types appear
3. Verify BigQuery data freshness

### Monthly Tasks
1. Archive old outages data
2. Update generator name mappings
3. Review and optimize query performance

## Troubleshooting

### No outages displayed
- Check BigQuery connection
- Verify `eventStatus = 'Active'` filter
- Check `unavailableCapacity >= 50` threshold

### Wrong totals in row 44
- Re-run the script
- Check for duplicate entries (use `clear_duplicate_outages.py`)
- Verify revisionNumber deduplication logic

### Formatting issues
- Check gspread API version
- Verify color codes: Red = #e43835 (RGB: 0.89, 0.22, 0.21)
- Ensure named parameters: `dashboard.update(range_name=..., values=...)`

### Missing generator names
- Update `bmu_registration_data` table in BigQuery
- Check join conditions in query
- Add fallback to `assetName` or `affectedUnit`

## Dashboard Link
🌐 **View Live Dashboard**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

## Change Log

### 26 Nov 2025
- ✅ Created `update_outages_with_totals.py`
- ✅ Added row 44 total outages summary
- ✅ Implemented GW/MW dual formatting
- ✅ Added severity status indicators
- ✅ Automated resolved outages removal
- ✅ Fixed gspread API deprecation warnings
- ✅ Enhanced visual progress bars (🟥⬜)
- ✅ Added comprehensive fuel type emojis

### Previous Updates
- 24 Nov 2025: Enhanced deduplication logic
- 20 Nov 2025: Added Apps Script deployment
- 10 Nov 2025: Auto-refresh functionality

## Contact & Support
For issues or questions about this system:
1. Check this README
2. Review the script comments
3. Check BigQuery for data freshness
4. Verify Google Sheets API permissions

---
**Last Updated**: 26 November 2025
**Maintained by**: George Major / Upower Energy
**Dashboard**: GB Power Market JJ
