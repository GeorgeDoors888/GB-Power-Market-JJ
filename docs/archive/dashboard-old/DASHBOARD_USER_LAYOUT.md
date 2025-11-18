# Dashboard User Layout - November 10, 2025

## ✅ User's Formatting Changes Captured

### Key Changes Made by User:

1. **Title Changed** (Row 1):
   - **Before**: `File: Dashboard`
   - **After**: `GB DASHBOARD - Power`
   - ✅ Bold formatting applied

2. **ALL Fuel Types in Main Section** (Rows 8-17):
   - User **removed the "Other Generators" separator**
   - All fuel types now listed together in one continuous section
   - **No separate section for "other" generators**

3. **Flags Issue Detected** (Column D):
   - Showing `🇫 ElecLink` instead of `🇫🇷 ElecLink`
   - Flags are being broken/stripped (missing second emoji character)
   - Affects all interconnectors

4. **Background Colors Added**:
   - Rows 2-5: Header section has background color
   - Row 7: Section headers have background color
   - Row 14: OCGT row has background color highlighting

5. **Outages Section** (Row 32+):
   - Outages are showing (good!)
   - Starting at row 32 with headers
   - 15 outages listed with visual indicators
   - Total capacity shown: 5133 MW

## Current Dashboard Structure (User's Layout)

```
Row 1:   GB DASHBOARD - Power                                    [BOLD]
Row 2:   ⏰ Last Updated: 2025-11-10 13:28:22 | ✅ FRESH         [COLORED BG, BOLD]
Row 3:   Data Freshness: ✅ <10min | ⚠️ 10-60min | 🔴 >60min    [COLORED BG, BOLD]
Row 4:   📊 SYSTEM METRICS                                       [COLORED BG, BOLD]
Row 5:   Total Generation: 31.8 GW | Supply: 32.7 GW ...        [COLORED BG, BOLD]
Row 6:   (blank)
Row 7:   🔥 Fuel Breakdown  |  🌍 Interconnectors                [COLORED BG, BOLD]

FUEL & INTERCONNECTOR SECTION (Rows 8-17):
Row 8:   💨 WIND      13.3 GW    |  🇫 ElecLink (France)      999 MW Import
Row 9:   🔥 CCGT      11.0 GW    |  🇮 East-West (Ireland)     0 MW Balanced
Row 10:  🌱 BIOMASS    3.3 GW    |  🇫 IFA (France)          1509 MW Import
Row 11:  ⚛️ NUCLEAR   3.2 GW    |  🇮 Greenlink (Ireland)    513 MW Export
Row 12:  💧 NPSHYD     0.6 GW    |  🇫 IFA2 (France)            1 MW Export
Row 13:  ⚡ OTHER      0.4 GW    |  🇮 Moyle (N.Ireland)      201 MW Export
Row 14:  🔥 OCGT       0.0 GW    |  🇳 BritNed (Netherlands)  833 MW Export  [HIGHLIGHTED]
Row 15:  🛢️ OIL        0.0 GW    |  🇧 Nemo (Belgium)         378 MW Export
Row 16:  ⛏️ COAL       0.0 GW    |  🇳 NSL (Norway)          1397 MW Import
Row 17:  🔋 PS        -0.0 GW    |  🇩 Viking Link (Denmark) 1090 MW Export

Row 18-31: (blank/unused)

OUTAGES SECTION (Rows 32+):
Row 32:  Asset Name | BMU ID | Fuel Type | Normal (MW) | Unavail (MW) | % Unavailable
Row 33:  T_HEYM27   | T_HEYM27 | Nuclear | 660 | 660 | 🟥🟥🟥🟥🟥🟥🟥🟥🟥🟥 100.0%
...
Row 49:  TOTAL UNAVAILABLE CAPACITY: 5133 MW (15 outages)
```

## User Preferences Identified:

✅ **Clean single section** - No "Other Generators" separator  
✅ **All fuel types together** - Easier to scan  
✅ **Visual hierarchy** - Bold headers, background colors  
✅ **Custom title** - "GB DASHBOARD - Power" instead of generic "File: Dashboard"  
✅ **Highlighted rows** - OCGT has special formatting  
❌ **Broken flags** - Need to fix emoji rendering  

## Issues to Fix:

### 1. **Broken Country Flags** (CRITICAL)
**Current**: `🇫 ElecLink` (showing half flag)  
**Should be**: `🇫🇷 ElecLink` (complete flag)

**Cause**: Flag emojis are being split or stripped during write

**Fix**: Need to use RAW_INPUT instead of USER_ENTERED for interconnector column

### 2. **Maintain User's Layout**
The update script should:
- ✅ Keep "GB DASHBOARD - Power" title
- ✅ Keep all fuel types in single section (rows 8-17)
- ✅ NOT add "Other Generators" separator
- ✅ Write all 10 fuel types continuously
- ✅ Match interconnectors to same rows

## Updated Script Requirements:

```python
# Header should write:
header_data = [
    ['GB DASHBOARD - Power', '', '', '', '', ''],  # User's custom title
    [f'⏰ Last Updated: {timestamp} | {age_display}', '', '', '', '', ''],
    ['Data Freshness: ✅ <10min | ⚠️ 10-60min | 🔴 >60min', '', '', '', '', ''],
    ['📊 SYSTEM METRICS', '', '', '', '', ''],
    [f'Total Generation: {total_gen:.1f} GW | Supply: {total_supply:.1f} GW | Renewables: {renewable_pct:.0f}% | {price_display}', '', '', '', '', ''],
    ['', '', '', '', '', ''],
    ['🔥 Fuel Breakdown', '', '', '🌍 Interconnectors', '', '']
]

# Then rows 8-17: ALL fuel types (no separation)
# Then outages section starts around row 32
```

## Formatting Notes:

**Bold Text Applied To**:
- Row 1: Title
- Row 2: Last updated
- Row 3: Data freshness
- Row 4: System metrics header
- Row 5: System metrics values
- Row 7: Section headers
- Row 14: OCGT (special highlight)

**Background Colors Applied To**:
- Rows 2-5: Header section (light blue/gray?)
- Row 7: Section headers (blue?)
- Row 14: OCGT row (yellow/highlight?)

**User kept these formatting choices - preserve them in updates!**

---

**Status**: ✅ User layout captured and documented  
**Next Action**: Update script to match user's layout preferences  
**Priority Fix**: Restore complete country flag emojis (🇫🇷 not 🇫)  
**Date**: November 10, 2025, 13:28
