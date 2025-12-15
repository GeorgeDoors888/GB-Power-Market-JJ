# Dashboard Structure - Locked Reference Guide

**Last Verified**: November 10, 2025  
**Sheet ID**: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`  
**Status**: ✅ Production-locked structure

---

## Overview

This document defines the **locked structure** of the GB DASHBOARD - Power Google Sheet. All automated update scripts MUST preserve this structure.

---

## Section 1: Header & Status (Rows 1-6)

### Row 1: Title
- **Cell A1**: `"File: Dashboard"`
- **Format**: Bold
- **Purpose**: Sheet identification

### Row 2: Timestamp
- **Cell A2**: `"⏰ Last Updated: YYYY-MM-DD HH:MM:SS | ✅ Auto-refresh enabled"`
- **Format**: Bold, background color
- **Update**: Every script run (automatic)
- **Components**:
  - Timestamp in GMT
  - Auto-refresh status indicator

### Row 3: Data Freshness Legend
- **Cell A3**: `"Data Freshness: ✅ <10min | ⚠️ 10-60min | 🔴 >60min"`
- **Format**: Bold, background color spans A3:F3
- **Purpose**: Visual key for data age indicators
- **Fixed**: Never changes

### Row 4: System Metrics Header
- **Cell A4**: `"📊 SYSTEM METRICS"`
- **Format**: Bold, background color
- **Purpose**: Section divider

### Row 5: System Summary
- **Cell A5**: `"Total Generation: X.X GW | Supply: X.X GW | Demand: X.X GW | Imbalance: ±X.X GW | Freq: XX.XX Hz | Price: £X.XX/MWh"`
- **Format**: Bold, background color spans A5:F5
- **Update**: Every script run (automatic)
- **Data Source**: BigQuery `bmrs_fuelinst_iris`, `bmrs_freq_iris`, `bmrs_mid_iris`

### Row 6: Blank
- **Purpose**: Spacing

---

## Section 2: Fuel Breakdown & Interconnectors (Rows 7-17)

### Row 7: Section Headers
- **Cell A7**: `"🔥 Fuel Breakdown"`
  - Format: Bold, background color
  - Spans: A7:C7
- **Cell D7**: `"🌍 Interconnectors"`
  - Format: Bold, background color
  - Spans: D7:F7

### Rows 8-17: Dual-Column Data

#### Left Column (A-C): Fuel Types
```
A: Fuel Type (emoji + name)
B: Generation (X.X GW)
C: (blank)
```

**Fixed Order (MUST NOT CHANGE)**:
1. Row 8: 💨 WIND
2. Row 9: 🔥 CCGT
3. Row 10: 🌱 BIOMASS
4. Row 11: ⚛️ NUCLEAR
5. Row 12: 💧 NPSHYD
6. Row 13: ⚡ OTHER
7. Row 14: 🔥 OCGT
8. Row 15: 🛢️ OIL
9. Row 16: ⛏️ COAL
10. Row 17: 🔋 PS (Pumped Storage)

#### Right Column (D-F): Interconnectors
```
D: Country flag + Name
E: Flow (XXX MW Import/Export/Balanced)
F: (blank)
```

**Fixed Order (MUST NOT CHANGE)**:
1. Row 8: 🇫🇷 ElecLink (France)
2. Row 9: 🇮🇪 East-West (Ireland)
3. Row 10: 🇫🇷 IFA (France)
4. Row 11: 🇮🇪 Greenlink (Ireland)
5. Row 12: 🇫🇷 IFA2 (France)
6. Row 13: 🇮🇪 Moyle (N.Ireland)
7. Row 14: 🇳🇱 BritNed (Netherlands)
8. Row 15: 🇧🇪 Nemo (Belgium)
9. Row 16: 🇳🇴 NSL (Norway)
10. Row 17: 🇩🇰 Viking Link (Denmark)

**Critical Rules**:
- ✅ Country flags MUST be 2-character Unicode sequences (e.g., 🇫🇷 = U+1F1EB + U+1F1F7)
- ✅ Always write using `valueInputOption='RAW'` to preserve flags
- ✅ Auto-verification runs after every update via `flag_utils.py`
- ❌ NEVER use `valueInputOption='USER_ENTERED'` for flag cells

---

## Section 3: Outage Data (Rows 32+)

### Row 32: Outage Table Header
```
A: Asset Name
B: BMU ID
C: Fuel Type
D: Normal (MW)
E: Unavail (MW)
F: % Unavailable
```
- **Format**: Bold headers
- **Purpose**: Column labels for outage table

### Rows 33-48: Outage Data (Dynamic)
- **Update**: Every 30 minutes via `auto_refresh_outages.py`
- **Data Source**: BigQuery `bmrs_remit_iris`
- **Sort**: Largest unavailable capacity first
- **Format**:
  - Column F: Visual bar chart using 🟥 (red) and ⬜ (white) squares
  - 10 squares represent 0-100% unavailability

### Row 49: Outage Summary
- **Cell A49**: `"TOTAL UNAVAILABLE CAPACITY: XXXX MW"`
- **Cell C49**: `"(XX outages)"`
- **Format**: Bold
- **Purpose**: Summary statistics

---

## Layout Constraints

### Column Widths (Recommended)
```
A: 200px  (Fuel/Asset names)
B: 120px  (Generation/BMU ID)
C: 120px  (Fuel Type)
D: 200px  (Interconnectors/Capacity)
E: 150px  (Flow/Unavailable)
F: 180px  (% Unavailable)
```

### Row Heights
- Rows 1-6: Standard (21px)
- Rows 7-17: Standard (21px)
- Row 32+: Standard (21px)

### Formatting Rules
1. **Headers** (Rows 2, 3, 4, 5, 7): Bold + background color
2. **Data Rows**: Normal text, no background
3. **Summary Row** (49): Bold

---

## Data Update Schedule

| Section | Update Frequency | Script | Data Source |
|---------|-----------------|---------|-------------|
| System Metrics (Row 5) | Every 5 minutes | `realtime_dashboard_updater.py` | `bmrs_fuelinst_iris`, `bmrs_freq_iris`, `bmrs_mid_iris` |
| Fuel Breakdown (Rows 8-17) | Every 5 minutes | `realtime_dashboard_updater.py` | `bmrs_fuelinst_iris` |
| Interconnectors (Rows 8-17) | Every 5 minutes | `realtime_dashboard_updater.py` | `bmrs_fuelinst_iris` |
| Outage Data (Rows 33-48) | Every 30 minutes | `auto_refresh_outages.py` | `bmrs_remit_iris` |

---

## Automatic Flag Verification

After **every update**, the following verification runs:

```python
from flag_utils import verify_and_fix_flags
from googleapiclient.discovery import build

sheets_service = build('sheets', 'v4', credentials=creds)
sheet_id = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"

all_complete, num_fixed = verify_and_fix_flags(sheets_service, sheet_id, verbose=False)

if not all_complete:
    print(f"⚠️ Fixed {num_fixed} broken flags")
```

**What it does**:
1. Reads Interconnector cells D8:E17
2. Checks if each flag is complete (2 characters)
3. If broken, cleans and re-adds correct flag
4. Writes using `RAW` mode
5. Verifies all complete

**See**: `AUTO_FLAG_VERIFICATION_COMPLETE.md` for full details

---

## BigQuery Table Mapping

### System Metrics Sources

| Metric | Table | Column | Notes |
|--------|-------|--------|-------|
| Total Generation | `bmrs_fuelinst_iris` | `generation` | SUM(generation) WHERE latest publishTime |
| Frequency | `bmrs_freq_iris` | `frequency` | Latest record |
| Price | `bmrs_mid_iris` | `marketIndexPrice` | Latest settlement period |

### Fuel Breakdown Source

**Table**: `bmrs_fuelinst_iris`  
**Query**:
```sql
SELECT fuelType, SUM(generation) as total_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE publishTime = (SELECT MAX(publishTime) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`)
GROUP BY fuelType
```

**Fuel Type Mapping**:
```python
FUEL_MAP = {
    'WIND': '💨 WIND',
    'CCGT': '🔥 CCGT',
    'BIOMASS': '🌱 BIOMASS',
    'NUCLEAR': '⚛️ NUCLEAR',
    'NPSHYD': '💧 NPSHYD',
    'OTHER': '⚡ OTHER',
    'OCGT': '🔥 OCGT',
    'OIL': '🛢️ OIL',
    'COAL': '⛏️ COAL',
    'PS': '🔋 PS'
}
```

### Interconnector Source

**Table**: `bmrs_fuelinst_iris`  
**Filter**: `fuelType = 'INTFR'`, `'INTIRL'`, `'INTNED'`, `'INTEW'`, etc.  
**Note**: Interconnectors appear as fuel types with special prefixes

**Flag Mapping**:
```python
FLAG_MAP = {
    'ElecLink': '🇫🇷', 'IFA': '🇫🇷', 'IFA2': '🇫🇷',
    'East-West': '🇮🇪', 'Greenlink': '🇮🇪', 'Moyle': '🇮🇪',
    'BritNed': '🇳🇱', 'Nemo': '🇧🇪', 'NSL': '🇳🇴', 'Viking': '🇩🇰'
}
```

### Outage Data Source

**Table**: `bmrs_remit_iris`  
**Query**:
```sql
SELECT
  assetName,
  bmuId,
  fuelType,
  normalCapacity,
  availableCapacity,
  (normalCapacity - availableCapacity) AS unavailable_mw,
  ROUND(((normalCapacity - availableCapacity) / normalCapacity) * 100, 1) AS pct_unavailable
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_iris`
WHERE unavailable_mw > 0
ORDER BY unavailable_mw DESC
LIMIT 15
```

---

## Update Scripts Reference

### Primary Scripts

1. **realtime_dashboard_updater.py** (Every 5 minutes)
   - Updates System Metrics (Row 5)
   - Updates Fuel Breakdown (Rows 8-17, Cols A-B)
   - Updates Interconnectors (Rows 8-17, Cols D-E)
   - Runs flag verification
   - Logs to: `logs/dashboard_updater.log`

2. **auto_refresh_outages.py** (Every 30 minutes)
   - Updates Outage Table (Rows 33-48)
   - Updates Summary (Row 49)
   - Runs flag verification (silent mode)
   - Logs to: `logs/outage_refresh.log`

3. **update_dashboard_preserve_layout.py** (Manual)
   - Full dashboard refresh
   - Preserves all layout elements
   - Runs flag verification
   - Use for: Manual updates or testing

### Verification Scripts

1. **verify_flags.py** (Manual)
   - Standalone flag verification
   - Reports broken flags
   - Option to auto-fix

2. **check_dashboard_health.py** (Manual)
   - Validates entire Dashboard structure
   - Checks data freshness
   - Verifies formatting

---

## Common Issues & Solutions

### Issue 1: Broken Country Flags
**Symptoms**: Flags showing as single character (🇫 instead of 🇫🇷)

**Root Cause**: Using `valueInputOption='USER_ENTERED'` corrupts 2-character Unicode

**Solution**: 
- All scripts now use `valueInputOption='RAW'`
- Automatic verification runs after every update
- See: `FLAG_FIX_TECHNICAL_GUIDE.md`

### Issue 2: Data Gaps in Fuel Breakdown
**Symptoms**: Missing fuel types or zero values

**Root Cause**: `bmrs_fuelinst_iris` lag (up to 7 days)

**Solution**:
- Union with historical `bmrs_fuelinst` table
- See: `STOP_DATA_ARCHITECTURE_REFERENCE.md`

### Issue 3: Outage Table Duplicates
**Symptoms**: Same asset appearing multiple times

**Root Cause**: Multiple REMIT messages for same outage

**Solution**:
- Use `DISTINCT ON (bmuId)` in query
- Sort by latest `messageCreationTime`

---

## Development Guidelines

### When Adding New Sections

1. **Choose Row Range**: Use rows 18-31 (currently unused buffer)
2. **Update This Document**: Add new section definition
3. **Preserve Existing**: Never modify rows 1-17 or 32+
4. **Test Flag Preservation**: Run flag verification after changes
5. **Update Auto-Refresh**: Add to `realtime_dashboard_updater.py` if needed

### When Modifying Scripts

**MUST DO**:
- ✅ Import `flag_utils` module
- ✅ Call `verify_and_fix_flags()` after every write
- ✅ Use `valueInputOption='RAW'` for flag cells
- ✅ Preserve row/column positions
- ✅ Test on non-production sheet first

**NEVER DO**:
- ❌ Change fuel type order (rows 8-17)
- ❌ Change interconnector order (rows 8-17)
- ❌ Remove header rows (1-7)
- ❌ Use `USER_ENTERED` for cells with emojis

---

## Testing Checklist

Before deploying Dashboard updates:

- [ ] Verify fuel types in correct order (8-17)
- [ ] Verify interconnectors in correct order (8-17)
- [ ] All country flags are 2 characters
- [ ] System metrics show latest data (<10 min old)
- [ ] Outage table sorted by unavailable capacity
- [ ] Row 49 summary matches table data
- [ ] Headers (rows 2, 3, 4, 5, 7) are bold
- [ ] Background colors preserved
- [ ] No extra blank rows inserted
- [ ] Flag verification passed (0 fixes needed)

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2025-11-10 | 1.0 | Initial locked structure documentation |
| 2025-11-10 | 1.1 | Added flag verification automation |
| 2025-11-10 | 1.2 | Added BigQuery table mapping |

---

## Related Documentation

- **Configuration**: `PROJECT_CONFIGURATION.md`
- **BigQuery Tables**: `BIGQUERY_DATASET_REFERENCE.md`
- **Flag Verification**: `AUTO_FLAG_VERIFICATION_COMPLETE.md`
- **Technical Details**: `FLAG_FIX_TECHNICAL_GUIDE.md`
- **Master Index**: `DOCUMENTATION_MASTER_INDEX.md`

---

## Contact & Support

**Maintainer**: George Major (george@upowerenergy.uk)  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Sheet**: [GB DASHBOARD - Power](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/)

---

**🔒 This structure is production-locked. Any changes require updating this document first.**
