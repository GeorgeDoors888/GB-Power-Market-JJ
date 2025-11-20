# Dashboard Update Correction - November 20, 2025

## ⚠️ CRITICAL: Script Configuration Error Fixed

**Problem**: `update_analysis_bi_enhanced.py` was configured to update the main **Dashboard** tab, but it was designed for a different layout (Enhanced BI Analysis). When run, it overwrote the two-column fuel/interconnector layout with tabular data.

**Status**: ✅ **FIXED** - Script now targets `Enhanced_BI_Analysis` sheet instead

---

## 🎯 Correct Update Scripts for Each Sheet

### 1. **Dashboard Tab** (Main Real-Time Dashboard)
**Script**: `realtime_dashboard_updater.py`  
**Purpose**: Updates TODAY's generation data in the two-column layout  
**Schedule**: ✅ **Auto-runs every 5 minutes** via cron  
**Updates**:
- Last Updated timestamp (B2)
- Total Generation, Supply, Renewables (header row)
- Fuel Breakdown (left column): WIND, CCGT, BIOMASS, etc.
- Interconnectors (right column): ElecLink, IFA, BritNed, etc.
- Market Price (when available)
- Live_Raw_Gen tab

**DO NOT RUN MANUALLY** - It's automated and working perfectly

### 2. **Enhanced_BI_Analysis Sheet** (Historical Analysis)
**Script**: `update_analysis_bi_enhanced.py`  
**Purpose**: Detailed weekly/monthly analysis with tables and charts  
**Schedule**: ⚠️ **Manual only** (DO NOT add to cron)  
**Updates**:
- Generation Mix table (rows 18-34)
- Frequency table (rows 38-59)
- Market Prices table (rows 63-84)
- Balancing Costs table (rows 88-109)
- Uses dropdown selectors for date range

**When to Run**: Only when you need detailed historical analysis on a separate sheet

---

## 🚫 What Went Wrong

### Incident Timeline:
1. **Before**: Dashboard tab had correct two-column layout preserved from Nov 11
2. **15:13**: Ran `update_analysis_bi_enhanced.py` thinking it would refresh Dashboard data
3. **Result**: Script wrote tabular data to rows 18+ (where fuel breakdown should be)
4. **Effect**: Fuel/Interconnector layout corrupted with "CCGT 8098.01 14059.05..." data
5. **Recovery**: User manually restored correct layout from backup

### Root Cause:
```python
# WRONG (before fix)
SHEET_NAME = 'Dashboard'  # This is the main dashboard - has special layout!

# CORRECT (after fix)
SHEET_NAME = 'Enhanced_BI_Analysis'  # Separate sheet for tables
```

---

## ✅ Dashboard Layout (DO NOT MODIFY)

```
Row 1-6:   Header Section
  B2: ⏰ Last Updated: [timestamp] | ✅ FRESH
  Row 3-6: Total Generation, Supply, Renewables, Price

Row 7-17:  Two-Column Layout (THIS IS CRITICAL)
  LEFT COLUMN (A-C):         RIGHT COLUMN (D-F):
  🔥 Fuel Breakdown          🌍 Interconnectors
  💨 WIND      13.3 GW      🇫🇷 ElecLink    999 MW Import
  🔥 CCGT      11.0 GW      🇮🇪 East-West   0 MW Balanced
  🌱 BIOMASS   3.3 GW       🇳🇱 BritNed     833 MW Export
  ...                       ...

Row 20-38: Outages Section
  Individual generator outages with capacity bars

Row 40+:   GSP Analysis
  Grid Supply Point data
```

**NEVER write tabular data to rows 7-17** - This is the visual dashboard area!

---

## 🔄 Correct Update Procedures

### For Real-Time Dashboard (Normal Operations):
**DO NOTHING** - Automated cron job handles it every 5 minutes

### Check Dashboard Status:
```bash
cd /Users/georgemajor/GB\ Power\ Market\ JJ

# View last update time
python3 -c "
import pickle, gspread
with open('token.pickle', 'rb') as f:
    creds = pickle.load(f)
gc = gspread.authorize(creds)
sheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8').worksheet('Dashboard')
print(sheet.acell('B2').value)
"

# Check cron job status
tail -20 logs/dashboard_updater.log
```

### For Historical Analysis (Occasional Use):
```bash
# This creates/updates Enhanced_BI_Analysis sheet ONLY
GOOGLE_APPLICATION_CREDENTIALS=inner-cinema-credentials.json python3 update_analysis_bi_enhanced.py
```

---

## 📋 Sheet Structure Reference

| Sheet Name | Purpose | Update Script | Schedule |
|------------|---------|---------------|----------|
| **Dashboard** | Main real-time dashboard | `realtime_dashboard_updater.py` | Every 5 min (auto) |
| **Live_Raw_Gen** | Raw generation data | `realtime_dashboard_updater.py` | Every 5 min (auto) |
| **Enhanced_BI_Analysis** | Historical tables/charts | `update_analysis_bi_enhanced.py` | Manual only |
| **GSP_Analysis** | Grid supply points | `gsp_auto_updater.py` | Every 10 min (auto) |
| **Data** | Backend data | Various | As needed |

---

## 🛡️ Protection Measures Implemented

1. ✅ Changed `update_analysis_bi_enhanced.py` to target `Enhanced_BI_Analysis` sheet
2. ✅ Documented which script updates which sheet
3. ✅ Clarified that Dashboard has special layout requirements
4. ⚠️ **DO NOT add `update_analysis_bi_enhanced.py` to cron** - It's for manual analysis only

---

## 📝 If Dashboard Gets Corrupted Again

### Quick Recovery Steps:
1. **Stop any running updates**: Check `ps aux | grep dashboard`
2. **Check what changed**: Compare with `dashboard_current_structure.json`
3. **Restore from Google Sheets version history**:
   - File → Version History → See version history
   - Find last good version (before corruption)
   - Click "Restore this version"
4. **Verify correct script is running**:
   ```bash
   crontab -l | grep dashboard
   # Should show: realtime_dashboard_updater.py (NOT update_analysis_bi_enhanced.py)
   ```

---

## ✅ Current Status

- ✅ Dashboard tab: User manually restored to correct layout
- ✅ `realtime_dashboard_updater.py`: Running every 5 minutes (working correctly)
- ✅ `update_analysis_bi_enhanced.py`: Fixed to use different sheet (won't corrupt Dashboard anymore)
- ✅ Cron jobs: Correct scripts running on correct schedules

---

## 📚 Related Documentation

- **Dashboard Layout**: `read_dashboard_structure.py` output
- **Auto-Update**: `AUTO_REFRESH_COMPLETE.md`
- **Architecture**: `STOP_DATA_ARCHITECTURE_REFERENCE.md`
- **Previous Fix**: `DASHBOARD_UPDATE_FIXED.md` (for reference only - DO NOT follow those instructions!)

---

**Last Updated**: November 20, 2025, 15:40 UTC  
**Issue**: Dashboard layout corrupted by wrong update script  
**Resolution**: Script reconfigured, dashboard manually restored  
**Prevention**: Documentation updated with clear script purposes
