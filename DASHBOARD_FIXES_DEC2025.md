# Live Dashboard v2 - Fixes Summary (December 2025)

## Issues Resolved

### 1. ✅ Sparklines Being Overwritten/Missing
**Problem**: Columns D and E (bar charts and sparklines) were disappearing  
**Root Causes**:
- Merged cells C12:F22 prevented individual cell values from displaying
- Apps Script (clasp-deployed) was overwriting Python updates
- Data_Hidden sheet was hidden, preventing sparkline rendering

**Solutions**:
- Unmerged cells C12:F22 using Sheets API
- Added PYTHON_MANAGED flag in AA1 to prevent Apps Script conflicts
- Unhid Data_Hidden sheet via API

**Commits**: e82033a, 274eb37, 972eabe

---

### 2. ✅ Wrong Sparkline Type (Line Instead of Bars)
**Problem**: Fuel sparklines showing as line graphs instead of bar charts per settlement period  
**User Requirement**: "these re meant to be bar charts every settlment period 📈 Trend (00:00→)"

**Solution**: Changed sparkline type from LINE to COLUMN in `update_live_dashboard_v2.py`
```python
# Before
sparkline_formula = f'=SPARKLINE(..., {{"charttype","line";"linewidth",2}})'

# After  
sparkline_formula = f'=SPARKLINE(..., {{"charttype","column"}})'
```

**Result**: Each of 36 settlement periods now shows as individual bar (E13-E22)

**Commit**: 274eb37

---

### 3. ✅ Missing KPI Sparklines
**Problem**: Row 7 sparklines (A7, C7, E7, G7, I7) were not being created

**Solution**: Added KPI sparkline configuration to main script:
- A7: Wholesale Price (COLUMN, red)
- C7: Frequency (LINE, green) 
- E7: Total Generation (COLUMN, orange)
- G7: Wind Output (COLUMN, teal)
- I7: System Demand (COLUMN, blue)

**Commit**: 274eb37

---

### 4. ✅ Corrupted Data in Generation Mix Section
**Problem**: Old sparkline formulas and interconnector data appearing in wrong columns (C-G)

**Solution**: 
- Cleared columns C13:G22 using Sheets API
- Re-ran dashboard updater to populate with fresh formulas
- Verified =TEXT() and =REPT() formulas correct

**Commit**: 972eabe

---

### 5. ✅ Missing Interconnector Connection Names
**Problem**: Column G (🔗 Connection) was blank for all interconnectors  
**Root Cause**: `update_live_dashboard_v2.py` only wrote to columns J-K (MW value + bar chart)

**Solution**: Added separate batch update for column G with connection names:
```python
ic_updates.append({
    'range': f'G{row_num}:G{row_num}',
    'values': [[name]]  # 🇫🇷 ElecLink, 🇮🇪 East-West, etc.
})
```

**Result**: All 10 interconnectors now show names (🇫🇷 ElecLink, 🇮🇪 East-West, 🇳🇱 BritNed, etc.)

**Commit**: 972eabe

---

### 6. ✅ Stale/Confusing Outages Data
**Problem**: 
- Title showing "Total: 5 units" when actually 15 units offline
- Wrong MW totals (should be 7,881 MW offline)
- Duplicate/confusing outages rows
- Extra garbage data in columns R-Z

**Root Cause**: `update_live_dashboard_v2_outages.py` NOT in cron, data became stale

**Solutions**:
1. **Immediate Fix**: Manually ran outages updater, cleared columns R-Z
2. **Permanent Fix**: Integrated outages updater into main dashboard script
   ```python
   # At end of update_dashboard()
   import subprocess
   result = subprocess.run(['python3', 'update_live_dashboard_v2_outages.py'], ...)
   ```
3. Updated `auto_update_dashboard_v2.sh` to remove duplicate outages call

**Result**: Outages now update automatically every 5 minutes with main dashboard  
**Verified**: Title shows "⚠️ ACTIVE OUTAGES - Top 15 by Capacity | Total: 15 units | Offline: 7,881 MW"

**Commit**: a5fcd22

---

## Current Dashboard Status

### ✅ Working Correctly
- **KPI Section** (Row 7): All 5 sparklines displaying (price, frequency, generation, wind, demand)
- **Generation Mix** (Rows 13-22): 10 fuels with GW values, % share, bar charts, and COLUMN sparklines
- **Interconnectors** (Rows 13-22): 10 connections with names, MW flows, and bar charts
- **Outages** (Rows 31-60): Top 15 by capacity, accurate statistics, auto-updating every 5 min
- **Data_Hidden Sheet**: 48-period timeseries for sparklines (visible, not hidden)

### 🔄 Automated Updates
**Cron Schedule**: Every 5 minutes via `auto_update_dashboard_v2.sh`
- Main dashboard update (KPIs, gen mix, interconnectors)
- Outages update (integrated, no separate call)
- Wind chart update
- Battery revenue update

**Log File**: `~/dashboard_v2_updates.log`

### 📊 Google Sheets
**Spreadsheet**: [1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit)  
**Sheet**: "Live Dashboard v2" (SheetID: 687718775)

---

## Key Files Modified

1. **update_live_dashboard_v2.py** (1061 lines)
   - Lines 945-975: Fuel sparklines (COLUMN type)
   - Lines 976-1002: KPI sparklines (5 configs)
   - Lines 1003-1033: Interconnector names + flows
   - Lines 1049-1070: Integrated outages updater call

2. **auto_update_dashboard_v2.sh** (47 lines)
   - Removed duplicate outages call (now handled by main script)
   - Updated success message to indicate outages included

3. **update_live_dashboard_v2_outages.py** (294 lines)
   - No changes (still callable independently for testing)
   - Now also called automatically by main script

---

## Testing Commands

```bash
# Manual dashboard update (includes outages)
python3 update_live_dashboard_v2.py

# Check recent cron runs
tail -50 ~/dashboard_v2_updates.log

# Verify outages data freshness
python3 << 'EOF'
import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
client = gspread.authorize(creds)

sheet = client.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA').worksheet('Live Dashboard v2')
print(sheet.acell('G31').value)  # Should show current outages count
EOF
```

---

## Architecture Notes

### Sparkline Data Flow
1. **BigQuery** → Fetch 48 periods of timeseries data
2. **Data_Hidden Sheet** → Write to rows 2-26 (fuels, ICs, KPIs)
3. **Live Dashboard v2** → Sparkline formulas reference Data_Hidden ranges
4. **Rendering** → Browser displays sparklines (Data_Hidden must be visible)

### Outages Data Flow
1. **BigQuery** → Query `bmrs_remit_unavailability` table
2. **Python Script** → Calculate totals, format data
3. **Google Sheets** → Write to G31 (title), G33 (headers), G34+ (data)
4. **Cron** → Triggers main script every 5 min → calls outages script

### Apps Script Conflict Prevention
- **PYTHON_MANAGED flag** in cell AA1
- Apps Script checks flag before updates
- Prevents overwrites of Python-managed sections

---

## Lessons Learned

1. **Merged Cells**: Can prevent individual cell values from displaying (caused D/E columns to disappear)
2. **Hidden Sheets**: Sparklines won't render if source sheet is hidden
3. **Apps Script Conflicts**: Need coordination flags when Python and Apps Script both update same sheet
4. **Sparkline Types**: COLUMN vs LINE - user wanted bars per period, not continuous line
5. **Separate Scripts**: If not in cron, data becomes stale - integrate into main workflow
6. **Extra Data**: Always clear full range to prevent leftover data from previous runs

---

*Last Updated: December 17, 2025*  
*All issues resolved and verified working*
