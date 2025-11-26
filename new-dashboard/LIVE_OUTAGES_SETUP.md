# Live Outages Sheet - Setup Complete ✅

## What Was Created

### 1. Live Outages Sheet
- **Location**: Dashboard V2 spreadsheet
- **URL**: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit\#gid\=1861051601
- **Data**: 141 active outages (43,321 MW total unavailable)

### 2. Filter Controls (Rows 5-7)
- **A7**: BM Unit dropdown (160 units + "All Units")
- **C7**: Asset Name text search
- **E7**: Start Date picker (calendar dropdown)
- **G7**: End Date picker (calendar dropdown)

### 3. Summary Statistics (J6:K8)
- Total Active Outages: 141
- Total Unavailable (MW): 43,321
- Avg Outage Size (MW): 307

### 4. Python Auto-Updater
**File**: `live_outages_updater.py`

**Usage**:
```bash
cd "/Users/georgemajor/GB Power Market JJ/new-dashboard"
python3 live_outages_updater.py
```

**What it does**:
- Fetches all active outages from BigQuery
- Updates timestamp, summary stats, and full outages table
- Applies proper asset names (database + manual mappings)
- Logs to `logs/live_outages_updater.log`

### 5. Apps Script for Button
**File**: `live_outages_apps_script.gs`

**To install**:
1. Open spreadsheet
2. Go to **Extensions → Apps Script**
3. Copy contents of `live_outages_apps_script.gs` into Code.gs
4. Save the script
5. Your button is already assigned to `refresh_all_outages()`

**Functions available**:
- `refresh_all_outages()` - Full refresh (requires webhook setup)
- `refresh_all_outages_manual()` - Updates timestamp only (use for now)

## How to Use

### For Users (Google Sheets)
1. Click **A7** dropdown to filter by BM Unit
2. Type in **C7** to search asset names
3. Click **E7** to select Start Date (calendar appears)
4. Click **G7** to select End Date (calendar appears)
5. Use **Data → Create a filter view** for live filtering
6. Click **Refresh button** to update data (runs `refresh_all_outages_manual()`)

### For Auto-Refresh (Python)
Run the updater manually or via cron:
```bash
python3 live_outages_updater.py
```

**Cron example** (every 15 minutes):
```bash
*/15 * * * * cd "/Users/georgemajor/GB Power Market JJ/new-dashboard" && python3 live_outages_updater.py >> logs/outages_cron.log 2>&1
```

### For Webhook Integration (Optional)
If you want the button to trigger Python refresh:
1. Set up ngrok or permanent webhook endpoint
2. Update `webhookUrl` in `live_outages_apps_script.gs`
3. Create Flask endpoint that calls `live_outages_updater.py`

## Files Created

```
new-dashboard/
├── create_live_outages_sheet.py       # Initial sheet creator
├── add_live_outages_dropdowns.py      # Adds dropdown validation
├── fix_date_dropdowns.py              # Configures date pickers
├── setup_outages_refresh.py           # Generates Apps Script
├── live_outages_updater.py            # ⭐ Main updater script
├── live_outages_apps_script.gs        # Apps Script for button
└── LIVE_OUTAGES_SETUP.md              # This file
```

## Data Schema

### Outages Table (A10+)
| Column | Name | Type | Example |
|--------|------|------|---------|
| A | Asset Name | Text | 🔥 Peterhead Power Station |
| B | BM Unit | Text | T_PEHE-1 |
| C | Fuel Type | Text | Fossil Gas |
| D | Normal (MW) | Number | 1,180 |
| E | Unavail (MW) | Number | 1,180 |
| F | Visual | Bar | 🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 100.0% |
| G | Cause | Text | Planned Outage |
| H | Start Time | DateTime | 2029-08-17 22:00 |
| I | End Time | DateTime | Ongoing |
| J | Status | Text | Active |

### Hidden Data (Column L)
- BM Units list for dropdown validation
- Not visible to users

## Current Status

✅ **Sheet created** with 141 outages  
✅ **Dropdowns configured** (BM Unit + Date pickers)  
✅ **Python updater working** (tested successfully)  
✅ **Apps Script ready** (needs manual paste)  
✅ **Button assigned** to `refresh_all_outages`  

## Next Steps (Optional)

1. **Add Chart**: Create line chart showing Demand/Generation/Outages trend
2. **Webhook**: Set up Flask endpoint for button → Python automation
3. **Cron Job**: Automate refresh every 15 minutes
4. **Filter Views**: Create saved filter views for common queries

---

*Last Updated: 2025-11-26*  
*Created by: Dashboard V2 Auto-Setup*
