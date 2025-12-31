# Dashboard Layout Conflict Resolution & Design Guide

**Date**: December 30, 2025  
**Issue**: Multiple cron jobs and scripts writing to overlapping row ranges  
**Solution**: Coordinated row allocation registry with safe update zones

---

## 🚨 Problem Summary

### Current Conflicts

1. **Rows 25-43, Columns A:F**: `update_live_metrics.py` **CLEARS** this zone every 10 minutes
   - **Impact**: Any data written here disappears within 10 minutes
   - **Originally affected**: Wind dashboard (rows 25-48)

2. **Rows 25-50, Columns G:O**: Apps Script writes outage data (manual trigger)
   - **Impact**: Overlaps with wind dashboard if placed at rows 25-48

3. **Overlapping owners**:
   - `update_all_dashboard_sections_fast.py` (every 5 min) - rows 13-22
   - `update_live_metrics.py` (every 10 min) - rows 1-6, 13-22, clears 25-43
   - Apps Script (manual) - rows 25-50
   - `create_wind_analysis_dashboard_live.py` (manual) - previously rows 25-48, **NOW rows 50-73**

---

## ✅ Solution: Row Allocation Registry

### Implementation

Created **`DASHBOARD_ROW_ALLOCATION.py`** - Single source of truth for all row assignments.

### Allocation Map

```
Rows 1-4:    Header & Status (update_live_metrics.py, every 10 min)
Rows 5-6:    Market KPIs (update_live_metrics.py, every 10 min)
Rows 10-12:  Section Headers (static)
Rows 13-22:  Generation Mix + Interconnectors + Market Dynamics (mixed)
Rows 23-24:  Reserved buffer (empty)
Rows 25-43:  ⚠️ CLEARING ZONE - DO NOT USE (cleared every 10 min)
Rows 25-50:  Active Outages (Apps Script, columns G:O only)
Rows 50-73:  ✅ Wind Dashboard (SAFE ZONE, columns A:G)
Rows 74-102: Available for future features
```

---

## 🔧 Fixes Applied

### 1. Wind Dashboard Moved
**Old location**: Rows 25-48 (conflicted with clearing zone)  
**New location**: Rows 50-73 (safe zone)  
**Script**: `create_wind_analysis_dashboard_live.py`

**Changes**:
```python
# OLD
'range': f'{SHEET_NAME}!A25:G25'

# NEW
'range': f'{SHEET_NAME}!A50:G50'
```

**Impact**: Wind dashboard data now persists between updates

---

### 2. Remove Legacy Clearing Code

**Location**: `update_live_metrics.py` line 1480-1482

**Current code** (PROBLEMATIC):
```python
# Clear legacy garbage in columns A-F (rows 25-43) - old Data_Hidden bleed-through
clear_garbage_rows = [['', '', '', '', '', ''] for _ in range(19)]  # 19 rows (25-43), 6 columns (A-F)
cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'A25:F43', clear_garbage_rows)
```

**Recommended action**: 
- **Option A**: Remove entirely if Data_Hidden bleed-through no longer occurs
- **Option B**: Reduce range to rows 36-43 (preserves outages in 25-35)
- **Option C**: Change to columns A:E only (preserves column F)

---

### 3. Wind Dashboard Range Update

**Before**:
```python
# Section 1: Header (A25:G25)
# Section 2: Current + Alert (A26:G26)
# Section 3: KPIs (A27:D30)
# ...continues to row 48
```

**After** (IMPLEMENTED):
```python
# Section 1: Header (A50:G50)  # +25 rows
# Section 2: Current + Alert (A51:G51)  # +25 rows
# Section 3: KPIs (A52:D55)  # +25 rows
# ...continues to row 73
```

---

## 📊 Automated Cron Jobs

### Current Schedule

```bash
# FAST UPDATER (Generation Mix, Interconnectors names)
*/5 * * * * cd /home/george/GB-Power-Market-JJ && python3 update_all_dashboard_sections_fast.py >> logs/dashboard_auto_update.log 2>&1

# COMPREHENSIVE UPDATER (KPIs, sparklines, market dynamics)
1,11,21,31,41,51 * * * * cd /home/george/GB-Power-Market-JJ && python3 update_live_metrics.py >> logs/unified_update.log 2>&1
```

### What Each Script Does

#### `update_all_dashboard_sections_fast.py` (Every 5 min)
- **Writes to**: Rows 13-22, Columns A:D (Generation Mix)
- **Writes to**: Rows 13-22, Column G (Interconnector names)
- **Technology**: Direct Google Sheets API v4
- **Speed**: 5-10 seconds

#### `update_live_metrics.py` (Every 10 min, staggered)
- **Writes to**: Rows 1-4 (Header/Status)
- **Writes to**: Rows 5-6 (Market KPIs)
- **Writes to**: Rows 13-22, Column H (Interconnector sparklines)
- **Writes to**: Rows 13-22, Columns K:N (Market dynamics)
- **CLEARS**: Rows 25-43, Columns A:F ⚠️
- **Technology**: CacheManager + BigQuery
- **Speed**: 30-60 seconds

---

## 🎨 Design Principles

### 1. Exclusive Row Ownership
Each row range has ONE owner script that writes to it.

**Exception**: Rows 13-22 (shared by multiple scripts, different columns)
- Column A-D: `update_all_dashboard_sections_fast.py`
- Column G: `update_all_dashboard_sections_fast.py`
- Column H: `update_live_metrics.py`
- Column K-N: `update_live_metrics.py`

### 2. Buffer Zones
Leave 1-2 empty rows between major sections to prevent visual crowding.

**Current buffers**:
- Rows 7-9: Empty (between KPIs and section headers)
- Rows 23-24: Empty (between interconnectors and outages)

### 3. Visual Hierarchy
```
HEADER (rows 1-4)
    ↓
KPIS (rows 5-6)
    ↓
[BUFFER] (rows 7-9)
    ↓
SECTION HEADERS (rows 10-12)
    ↓
DATA GRID (rows 13-22)
    ↓
[BUFFER] (rows 23-24)
    ↓
OUTAGES (rows 25-50, columns G:O)
    ↓
WIND DASHBOARD (rows 50-73, columns A:G)
    ↓
[FUTURE SECTIONS] (rows 74+)
```

### 4. Column Zones
```
A-D: Generation Mix
E-F: Reserved/empty
G-H: Interconnectors (names + sparklines)
I-J: Empty/outages
K-N: Market Dynamics
O-AA: Available
```

---

## 🚀 Usage Guide

### For Developers Adding New Dashboards

#### Step 1: Check Available Space
```bash
python3 DASHBOARD_ROW_ALLOCATION.py
```

Look for "Available" or "Unallocated" rows.

#### Step 2: Check Conflicts
```python
from DASHBOARD_ROW_ALLOCATION import check_row_conflict

conflicts = check_row_conflict(
    start_row=74,
    end_row=90,
    columns='A:G'
)

if conflicts:
    print(f"⚠️ Conflicts: {conflicts}")
else:
    print("✅ Safe to use rows 74-90")
```

#### Step 3: Register Your Section
Add to `ROW_ALLOCATION` dict in `DASHBOARD_ROW_ALLOCATION.py`:

```python
'my_new_dashboard': {
    'rows': (74, 90),
    'columns': 'A:G',
    'owner': 'my_dashboard_script.py',
    'frequency': 'Every 15 min',
    'description': 'My awesome new dashboard'
},
```

#### Step 4: Add to Cron (if automated)
```bash
crontab -e

# Add:
*/15 * * * * cd /home/george/GB-Power-Market-JJ && python3 my_dashboard_script.py >> logs/my_dashboard.log 2>&1
```

---

## 🔍 Conflict Detection Tools

### Check Before Writing
```python
from DASHBOARD_ROW_ALLOCATION import is_safe_to_write

safe, reason = is_safe_to_write(
    start_row=50,
    end_row=73,
    columns='A:G',
    script_name='create_wind_analysis_dashboard_live.py'
)

if safe:
    print(f"✅ Safe to write: {reason}")
    # Proceed with update
else:
    print(f"⚠️ NOT SAFE: {reason}")
    # Find alternative location
```

### Get Safe Range Helper
```python
from DASHBOARD_ROW_ALLOCATION import get_safe_range

range_str = get_safe_range('wind_forecast_dashboard')
# Returns: "Live Dashboard v2!A:G50:A:G73"

# Use in Sheets API call
result = sheets_service.spreadsheets().values().update(
    spreadsheetId=SPREADSHEET_ID,
    range=range_str,
    valueInputOption='USER_ENTERED',
    body={'values': my_data}
).execute()
```

---

## ⚠️ Critical Rules

### DO NOT:
1. ❌ Write to rows 25-43, columns A:F (clearing zone)
2. ❌ Write to column H rows 13-22 from Apps Script (Python sparklines)
3. ❌ Use rows without checking `DASHBOARD_ROW_ALLOCATION.py`
4. ❌ Overlap with existing automated updaters
5. ❌ Forget to update the registry when adding new sections

### ALWAYS:
1. ✅ Check row allocation registry before deploying
2. ✅ Test conflict detection: `python3 DASHBOARD_ROW_ALLOCATION.py`
3. ✅ Leave buffer rows between sections
4. ✅ Document your row range in the registry
5. ✅ Use descriptive range names in code comments

---

## 📝 Example: Safe Dashboard Addition

```python
#!/usr/bin/env python3
"""
New Battery Dashboard - Safe Implementation
Uses rows 74-85 (verified no conflicts)
"""

from DASHBOARD_ROW_ALLOCATION import check_row_conflict, is_safe_to_write
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SPREADSHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Live Dashboard v2"

# Define our row range
START_ROW = 74
END_ROW = 85
COLUMNS = 'A:G'
SCRIPT_NAME = 'battery_dashboard.py'

def main():
    # Step 1: Check for conflicts
    print(f"Checking rows {START_ROW}-{END_ROW}, columns {COLUMNS}...")
    conflicts = check_row_conflict(START_ROW, END_ROW, COLUMNS)
    
    if conflicts:
        print(f"⚠️ CONFLICTS FOUND: {conflicts}")
        return False
    
    # Step 2: Verify safe to write
    safe, reason = is_safe_to_write(START_ROW, END_ROW, COLUMNS, SCRIPT_NAME)
    if not safe:
        print(f"⚠️ NOT SAFE: {reason}")
        return False
    
    print(f"✅ Safe to proceed: {reason}")
    
    # Step 3: Prepare data
    dashboard_data = [
        ['🔋 BATTERY DASHBOARD', '', '', '', '', '', ''],
        ['KPI 1', 'Value 1', '', '', '', '', ''],
        # ... more rows
    ]
    
    # Step 4: Write to sheets
    creds = Credentials.from_service_account_file(
        'inner-cinema-credentials.json',
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )
    sheets_service = build('sheets', 'v4', credentials=creds, cache_discovery=False)
    
    result = sheets_service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range=f'{SHEET_NAME}!{COLUMNS}{START_ROW}:{COLUMNS}{END_ROW}',
        valueInputOption='USER_ENTERED',
        body={'values': dashboard_data}
    ).execute()
    
    print(f"✅ Updated {result.get('updatedCells')} cells")
    return True

if __name__ == "__main__":
    main()
```

---

## 🔧 Maintenance

### Monthly Review
1. Run `python3 DASHBOARD_ROW_ALLOCATION.py` to visualize layout
2. Check for unused allocated rows
3. Verify cron jobs are still running: `crontab -l`
4. Review logs for errors:
   ```bash
   tail -50 logs/dashboard_auto_update.log
   tail -50 logs/unified_update.log
   ```

### When Conflicts Arise
1. Check allocation registry: `python3 DASHBOARD_ROW_ALLOCATION.py`
2. Identify conflicting scripts
3. Move one section to available rows
4. Update registry and script code
5. Test thoroughly before deploying

---

## 📖 Related Files

- **`DASHBOARD_ROW_ALLOCATION.py`** - Row allocation registry (this system)
- **`DASHBOARD_MASTER_REFERENCE.md`** - Complete dashboard documentation
- **`update_live_metrics.py`** - Main comprehensive updater (2599 lines)
- **`update_all_dashboard_sections_fast.py`** - Fast updater (399 lines)
- **`create_wind_analysis_dashboard_live.py`** - Wind dashboard (rows 50-73)
- **`clasp-gb-live-2/src/Data.gs`** - Apps Script (outages rows 25-50)

---

## 🎯 Quick Reference Commands

```bash
# Check current allocation
python3 DASHBOARD_ROW_ALLOCATION.py

# View cron jobs
crontab -l | grep dashboard

# Check logs
tail -f logs/dashboard_auto_update.log  # Fast updater
tail -f logs/unified_update.log         # Comprehensive updater

# Test wind dashboard
python3 create_wind_analysis_dashboard_live.py

# Manual dashboard update
python3 update_live_metrics.py
```

---

**Status**: ✅ Wind dashboard fixed (moved to rows 50-73)  
**Next Step**: Consider removing clearing code from `update_live_metrics.py` line 1482  
**Last Updated**: December 30, 2025
