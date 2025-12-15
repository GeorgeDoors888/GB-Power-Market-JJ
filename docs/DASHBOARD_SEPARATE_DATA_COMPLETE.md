# Dashboard with Separate Chart Data - Complete! ✅

## What Changed

Your dashboard now has a **clean separation** between display and chart data:

### Sheet Structure
1. **Dashboard** - Clean display visible to users
   - KPIs (Total MW, Renewable %, Price)
   - Generation mix table (20 fuel types)
   - Professional formatting with colors and emojis

2. **ChartData** - Hidden sheet for chart source data
   - 80 rows of 24-hour trend data (48 settlement periods)
   - Columns: Settlement Period, Wind, Solar, Nuclear, Gas, Total
   - ✅ **HIDDEN** - Won't clutter your spreadsheet view

## Files Updated

### 1. `enhance_dashboard_layout.py` ✅ 
**Changes:**
- Creates separate `ChartData` sheet
- Hides the ChartData sheet automatically
- Dashboard shows only KPIs and generation mix (clean!)
- Chart data written to ChartData sheet (hidden!)

**Run to refresh data:**
```bash
python3 enhance_dashboard_layout.py
```

### 2. `dashboard_charts_v2.gs` ✅
**Changes:**
- Reads trend data from hidden `ChartData` sheet
- Reads generation mix from `Dashboard` sheet (for pie/column charts)
- 4 interactive charts:
  - Line: 24h trend from ChartData
  - Pie: Current mix from Dashboard
  - Area: Stacked generation from ChartData
  - Column: Top sources from Dashboard

**Deployed to Apps Script:**
- Script ID: `1fILya0xmSWkwXHtY9ulWDTVqFnPQqblpCmKLsa5A-y4dHeOOdU5q1N5A`
- Location: Container-bound to your spreadsheet

## How to Create Charts (30 seconds)

### Option 1: Via Apps Script Editor ⭐ RECOMMENDED
1. **Open**: https://script.google.com/d/1fILya0xmSWkwXHtY9ulWDTVqFnPQqblpCmKLsa5A-y4dHeOOdU5q1N5A/edit

2. **Select function**: `createDashboardCharts` (from dropdown)

3. **Click**: ▶️ Run button

4. **First time permissions**:
   - Click "Review permissions"
   - Select your Google account
   - Click "Advanced" → "Go to Dashboard Charts (unsafe)"
   - Click "Allow"

5. **Wait 5-10 seconds** → Success! ✅

6. **Return to spreadsheet** → 4 charts appear!

### Option 2: Via Spreadsheet Menu
1. Open your [Dashboard](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/)

2. Reload page (Cmd+R / Ctrl+R) to activate menu

3. Look for: **📊 Dashboard** menu (top menu bar)

4. Click: **📊 Dashboard** → **🔄 Create/Update Charts**

## Data Flow

```
BigQuery (bmrs_fuelinst_iris, bmrs_mid_iris)
         ↓
enhance_dashboard_layout.py
         ↓
    ┌─────────────────┐
    │   Dashboard     │ ← Clean display (visible)
    │   - KPIs        │
    │   - Gen Mix     │
    └─────────────────┘
         +
    ┌─────────────────┐
    │   ChartData     │ ← Trend data (HIDDEN)
    │   - 80 rows     │
    │   - 5 series    │
    └─────────────────┘
         ↓
  dashboard_charts_v2.gs
         ↓
    4 Interactive Charts
    - Line (24h trend)
    - Pie (current mix)
    - Area (stacked)
    - Column (top sources)
```

## Auto-Refresh Setup

### Dashboard Data (Every 5 minutes)
```bash
crontab -e
```

Add:
```bash
*/5 * * * * cd '/Users/georgemajor/GB Power Market JJ' && python3 enhance_dashboard_layout.py >> logs/dashboard_enhance.log 2>&1
```

### Charts (After first manual run)
Charts auto-update when data refreshes! No additional cron needed.

## Current Status

✅ **Dashboard sheet** - Clean layout with KPIs  
✅ **ChartData sheet** - Hidden with 80 data points  
✅ **Apps Script** - Deployed with updated code  
⏳ **Charts** - Ready to create (run script once)

## Summary Stats (Current Data)

- **Total Generation**: 32,075 MW
- **Renewable Share**: 32.8%
- **Current Price**: £0.00/MWh (check bmrs_mid_iris data)
- **Chart Data Points**: 80 (48 settlement periods × 5 series)
- **Dashboard Rows**: 30 (compact display)

## Benefits

✅ **Clean Dashboard** - No cluttered trend data tables  
✅ **Hidden Data** - ChartData sheet invisible to viewers  
✅ **Auto-Update** - Charts update when data refreshes  
✅ **Professional** - Separation of display vs data  
✅ **Performance** - Charts read from optimized data structure  

## Troubleshooting

### "ChartData sheet not found"
Run: `python3 enhance_dashboard_layout.py`

### Charts show wrong data
1. Verify ChartData has 80 rows
2. Re-run: `python3 enhance_dashboard_layout.py`
3. Re-create charts via Apps Script

### ChartData is visible
The script hides it automatically. If visible:
```python
python3 -c "
import gspread
gc = gspread.service_account(filename='inner-cinema-credentials.json')
ss = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
chart_data = ss.worksheet('ChartData')
ss.batch_update({'requests': [{
    'updateSheetProperties': {
        'properties': {'sheetId': chart_data.id, 'hidden': True},
        'fields': 'hidden'
    }
}]})
print('✅ ChartData hidden')
"
```

## Next Steps

1. **Create charts** (30 seconds) via Apps Script link above
2. **Test auto-refresh** - Wait 5 minutes, check dashboard updates
3. **Customize charts** - Edit `dashboard_charts_v2.gs` for styling
4. **Add more charts** - Frequency, prices, interconnectors

## Links

- **Dashboard**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/
- **Apps Script**: https://script.google.com/d/1fILya0xmSWkwXHtY9ulWDTVqFnPQqblpCmKLsa5A-y4dHeOOdU5q1N5A/edit

---

**Implementation Date**: November 9, 2025  
**Status**: ✅ Ready for chart creation  
**Next Action**: Click Apps Script link → Run createDashboardCharts()
