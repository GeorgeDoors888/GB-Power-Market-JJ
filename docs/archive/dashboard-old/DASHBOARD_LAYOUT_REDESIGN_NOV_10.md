# Dashboard Layout Redesign - November 10, 2025

## Problem Identified

The Dashboard had a **confusing mixed layout** where outage data appeared **inline** with settlement period rows (SP22-SP27), creating visual clutter:

```
SP22  38.6  50  £0.00  Normal (MW)  Unavail (MW)  % Unavailable  Cause
SP23  38.6  50  £0.00  2000         1500          🟥🟥🟥... 75.0%  DC Cable Fault
```

This made it unclear where settlement period data ended and outage data began.

## Root Cause

**File**: `tools/update_dashboard_display.py` (lines 305-350)

The script had code that attempted to **insert outage data into columns E-H of settlement period rows 22-27**, while a separate section also existed at row 69+. This created:

1. **Duplicate data** - Outages appeared twice
2. **Inconsistent formatting** - Inline vs. separate section
3. **Visual confusion** - Mixed data types in same rows
4. **Unclear boundaries** - Hard to distinguish sections

## Solution Implemented

### 1. Removed Inline Outage Code ✅

**File**: `tools/update_dashboard_display.py`

**Removed** (lines 305-350):
- Code that read from `Live_Raw_REMIT_Outages`
- Logic that inserted outage data into `sp_rows[21][4:8]` through `sp_rows[26][4:8]`
- Replaced with comment directing to new clean layout

### 2. Created Clean Layout Script ✅

**New File**: `redesign_dashboard_layout.py`

**Features**:
- Clears old mixed layout (rows 18-100)
- Builds clean settlement period section with **5 columns only**:
  - SP | Time | Generation (GW) | Frequency (Hz) | Price (£/MWh)
- Adds blank separator rows
- Creates **completely separate** outages section
- Applies color formatting:
  - 📈 Settlement Period header: Blue background, white text
  - Column headers: Light gray background, bold text

### 3. Applied Color Scheme ✅

Used Google Sheets API `batchUpdate` with `repeatCell` to apply:

```python
# Settlement Period header (row 19) - Blue
backgroundColor: rgb(0.2, 0.4, 0.8)
textFormat: bold, white

# Column headers (row 21) - Light gray
backgroundColor: rgb(0.9, 0.9, 0.9)
textFormat: bold
```

## New Dashboard Structure

```
Rows 1-17:    Header, fuel breakdown, interconnectors
Row 18:       Blank separator
Row 19:       📈 SETTLEMENT PERIOD DATA (Blue background)
Row 20:       Blank
Row 21:       Column headers (SP | Time | Gen | Freq | Price)
Rows 22-69:   SP01-SP48 data (CLEAN - only 5 columns)
Rows 70-71:   Blank separator
Row 72:       ⚠️ POWER STATION OUTAGES (Red/warning style)
Row 73:       Blank
Row 74:       Outage column headers
Rows 75+:     Active outages with visual indicators (🟥⬜ bars)
```

## Verification Results ✅

**Script**: `verify_clean_layout.py`

```
✅ LAYOUT VERIFICATION PASSED

📊 Clean Layout Confirmed:
   • Settlement periods: Rows 22-69 (clean 5-column format)
   • Separator: Rows 70-71
   • Outages section: Row 72+ (separate with visual indicators)

🧹 All settlement period rows are CLEAN (no outage data)
⚠️  Outages section found at row 72
🎨 Visual indicators present (🟥🟥🟥... bars)
```

## Key Improvements

### Before ❌
- Settlement periods mixed with outage data
- Columns E-H of SP22-27 had outage headers/data
- Confusing to read
- Duplicate information
- No visual separation

### After ✅
- Clean 5-column settlement period table
- Clear blank separators
- Completely separate outage section
- Color-coded headers
- Visual indicators (🟥⬜ bars) only in outage section
- Professional, uncluttered layout

## Files Modified

1. **tools/update_dashboard_display.py** - Removed inline outage code
2. **redesign_dashboard_layout.py** - NEW: Clean layout implementation
3. **verify_clean_layout.py** - NEW: Layout verification script

## Maintenance Notes

### Future Dashboard Updates

When updating the Dashboard, remember:

1. **Settlement Period section** (rows 18-69):
   - Only write to columns A-E
   - Keep columns F-H empty
   - Do NOT add outage data here

2. **Outage section** (rows 72+):
   - Completely separate
   - Starts with blank separator rows
   - Has its own header and columns
   - Use `redesign_dashboard_layout.py` to refresh

3. **To refresh both sections**:
   ```bash
   python3 redesign_dashboard_layout.py
   python3 verify_clean_layout.py  # Verify it worked
   ```

### Auto-Refresh Integration

The auto-refresh script `realtime_dashboard_updater.py` should:
- Update fuel breakdown (rows 7-17)
- Update interconnectors (rows 7-17, columns D-E)
- Update settlement periods (rows 22-69, columns A-E only)
- **NOT touch** outage section (rows 72+)

Outage data refreshes separately via BigQuery query in `redesign_dashboard_layout.py`.

## Color Scheme Reference

| Section | Background Color | Text Color | Text Style |
|---------|-----------------|------------|------------|
| Settlement Period header | Blue (0.2, 0.4, 0.8) | White (1, 1, 1) | Bold |
| Column headers | Light Gray (0.9, 0.9, 0.9) | Default | Bold |
| Data rows | White (default) | Default | Regular |
| Outages header | To be styled | Default | Bold |

## Visual Indicators

**Outage Percentage Bars**:
- 🟥 Red square = 10% unavailable
- ⬜ White square = 10% available
- Total of 10 squares = 100%

Example: `🟥🟥🟥🟥🟥🟥🟥🟥⬜⬜ 75.0%` = 75% unavailable

## Testing

**Manual Test**:
1. Open Dashboard: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
2. Check rows 22-69: Should only show SP, Time, Gen, Freq, Price
3. Check columns E-H in those rows: Should be EMPTY
4. Scroll to row 72+: Should see separate outage section
5. Outages should have visual bars (🟥⬜)

**Automated Test**:
```bash
python3 verify_clean_layout.py
```

Should output: `✅ LAYOUT VERIFICATION PASSED`

## Status

- ✅ Layout redesigned and implemented
- ✅ Inline outage code removed from update script
- ✅ Color formatting applied
- ✅ Verification tests passed
- ✅ Documentation complete

**Dashboard URL**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

---

*Last Updated: November 10, 2025, 09:30 GMT*  
*Issue Reported By: User (layout confusion)*  
*Resolved By: AI Agent*
