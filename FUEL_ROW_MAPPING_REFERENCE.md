# Fuel Row Mapping Reference - Live Dashboard v2

**Spreadsheet ID:** `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`
**Date Created:** December 17, 2025
**Purpose:** Definitive mapping of fuel types to sheet rows

## ⚠️ CRITICAL: Two Sheets Exist

### 1. "Live Dashboard v2" (CORRECT - Has Sparklines)
- Row 2: Timestamp
- Row 13: 🌬️ WIND (correct emoji)
- Row 14: ⚛️ NUCLEAR
- Row 15: 🏭 CCGT (correct emoji)
- Row 16: 🌿 BIOMASS
- Row 17: 💧 NPSHYD
- Row 18: ❓ OTHER
- Row 19: 🛢️ OCGT
- Rows 20-22: BLANK (no fuel names in column A)

### 2. "GB Live" (WRONG - Being Updated by update_bg_live_dashboard.py)
- Row 2: Timestamp
- Rows 11-22: ALL BLANK in column A (no fuel names!)
- Has GW values in column B but NO labels

## The Problem

**update_bg_live_dashboard.py** is currently:
1. Using wrong spreadsheet ID: `1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I` (OLD)
2. Updating sheet name: `'GB Live'` instead of `'Live Dashboard v2'`
3. Writing to rows 11-20 when it should write to rows 13-22

## Correct Configuration

```python
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'  # Live Dashboard v2
SHEET_NAME = 'Live Dashboard v2'  # NOT 'GB Live'

FUEL_ROW_MAPPING = {
    'WIND': 13,      # 🌬️ WIND (not 💨)
    'NUCLEAR': 14,   # ⚛️ NUCLEAR
    'CCGT': 15,      # 🏭 CCGT (not 🔥)
    'BIOMASS': 16,   # 🌿 BIOMASS
    'NPSHYD': 17,    # 💧 NPSHYD
    'OTHER': 18,     # ❓ OTHER
    'OCGT': 19,      # 🛢️ OCGT
    # Rows 20-22 currently blank - TBD if needed
}

TIMESTAMP_ROW = 2  # NOT row 1
```

## Emoji Reference

### ❌ WRONG Emojis (Old Scripts)
- 💨 Wind (small wind face)
- 🔥 CCGT (fire)

### ✅ CORRECT Emojis (Current Dashboard)
- 🌬️ WIND (wind blowing face)
- 🏭 CCGT (factory)

## Column Layout (Live Dashboard v2)

```
Row 12: Header row
        A: "🛢️ Fuel Type"
        B: "⚡ GW"
        D: "📊 Bar"

Row 13-19: Fuel data
        A: Fuel name with emoji
        B: Generation in GW
        D: Bar chart visualization
```

## Scripts That Need Updating

1. **update_bg_live_dashboard.py**
   - Line 23: Fix SPREADSHEET_ID
   - Line 24: Fix SHEET_NAME to 'Live Dashboard v2'
   - Fix row offsets (11-20 → 13-22)
   - Fix emojis (💨→🌬️, 🔥→🏭)

2. **Any timestamp updaters**
   - Must write to row 2, NOT row 1

## What About Rows 20-22?

Currently BLANK in "Live Dashboard v2" sheet. Options:
1. Leave blank (most likely - only 7 fuel types needed)
2. Add more fuel types if needed (PS, COAL, etc.)
3. Remove them from update scripts

**Recommendation:** Leave blank, only update rows 13-19 (7 fuel types)

---

*Last Updated: December 17, 2025*
