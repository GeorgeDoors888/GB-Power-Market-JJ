# MPAN Parsing Fix - Maintenance Guide

**Date Fixed**: 22 November 2025  
**Issue**: Wrong DNO extracted from full MPAN format  
**Status**: ✅ Fixed and tested

## The Problem

When entering full MPAN `00800999932 1405566778899` into BESS sheet:
- ❌ System showed: UKPN London (ID **12**), Red rate 2.313 p/kWh
- ✅ Should show: NGED West Midlands (ID **14**), Red rate 1.764 p/kWh

## Root Cause

`dno_lookup_python.py` was importing from non-existent `mpan_parser` module, causing:
1. Import failure (silently caught)
2. Fallback to legacy parsing
3. Legacy parser extracted digits from TOP LINE (`00800999932`) 
4. Used `08` instead of correct core `14`

## The Fix

**File**: `dno_lookup_python.py`

**Lines 13-17** (CRITICAL - Do Not Modify):
```python
# ⚠️ CRITICAL: Import MPAN parser for correct distributor ID extraction
from mpan_generator_validator import extract_core_from_full_mpan, mpan_core_lookup
MPAN_PARSER_AVAILABLE = True
```

**Lines 245-300** (`parse_mpan_input()` function):
```python
# ⚠️ CRITICAL: Detect full MPAN by spaces/dashes
if ' ' in mpan_str or '-' in mpan_str:
    core = extract_core_from_full_mpan(mpan_str)  # Extract 13-digit core
    # ...
info = mpan_core_lookup(core)  # Get DNO from first 2 digits of CORE
mpan_id = int(info['dno_id'])  # Return correct ID (14 not 08)
```

## MPAN Structure Reference

### Full 21-digit MPAN Format
```
00 801 0840 1405566778899
│  │   │    └─────────────── Core MPAN (13 digits)
│  │   │                     First 2 digits = Distributor ID
│  │   └────────────────── LLFC (Line Loss Factor Class)
│  └────────────────────── MTC (Meter Timeswitch Code)  
└───────────────────────── PC (Profile Class)
```

**CRITICAL**: Distributor ID is in the **CORE** (bottom line), NOT top line

### Examples
| Full MPAN | Core Extracted | Distributor ID | DNO |
|-----------|----------------|----------------|-----|
| `00800999932 1405566778899` | `1405566778899` | **14** | NGED West Midlands |
| `00801084012001234567890` | `1200123456789` | **12** | UKPN London |
| `00201165010001234567890` | `1000123456789` | **10** | UKPN Eastern |

## Testing

### Quick Test
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 test_mpan_parsing.py
```

**Expected Output**:
```
Test Results: 5 passed, 0 failed
✅ All tests passed! MPAN parsing is working correctly.
```

### Manual Test
```bash
python3 dno_lookup_python.py 14 HV
```

**Expected**:
- DNO: National Grid Electricity Distribution – West Midlands (WMID)
- Red Rate: 1.764 p/kWh

### Test in BESS Sheet
1. Open BESS sheet: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
2. Enter in B6: `00800999932 1405566778899`
3. Click "Refresh DNO Rates" button
4. Verify:
   - C6: `NGED-WM`
   - D6: `National Grid Electricity Distribution – West Midlands (WMID)`
   - B9: `1.764` (Red rate)

## When This Might Break

### Scenario 1: Module Rename
If someone renames `mpan_generator_validator.py`:
- Import will fail
- Falls back to legacy parsing
- Wrong DNO extracted

**Fix**: Update import in `dno_lookup_python.py` line 14

### Scenario 2: Function Rename
If `extract_core_from_full_mpan()` renamed:
- Import error
- Falls back to legacy parsing

**Fix**: Update function call in `parse_mpan_input()` line 268

### Scenario 3: Parser Logic Change
If `extract_core_from_full_mpan()` changes behavior:
- Might return wrong core
- DNO lookup fails or wrong

**Fix**: Run `test_mpan_parsing.py` after changes

## Files Modified

1. ✅ `dno_lookup_python.py` - Fixed imports and parsing function
2. ✅ `DNO_DUOS_LOOKUP_SYSTEM.md` - Added troubleshooting section
3. ✅ `.github/copilot-instructions.md` - Added critical config warning
4. ✅ `MPAN_DUOS_QUICKSTART.md` - Added troubleshooting guide
5. ✅ `test_mpan_parsing.py` - Created test suite (NEW)
6. ✅ `MPAN_PARSING_FIX_README.md` - This file (NEW)

## Related Issues

**None yet** - This is the initial fix and documentation

## Verification Checklist

Before deploying changes to production:
- [ ] Run `python3 test_mpan_parsing.py` - All tests pass
- [ ] Run `python3 dno_lookup_python.py 14 HV` - Shows NGED West Midlands
- [ ] Test in BESS sheet with full MPAN - Correct DNO shown
- [ ] Check imports at top of `dno_lookup_python.py` - Still correct
- [ ] Check `parse_mpan_input()` function - Uses `extract_core_from_full_mpan()`

## Contact

**Maintainer**: George Major (george@upowerenergy.uk)  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Documentation**: See `DNO_DUOS_LOOKUP_SYSTEM.md` for full system architecture

---

**Last Updated**: 22 November 2025  
**Status**: ✅ Fixed, tested, documented  
**Test Status**: 5/5 tests passing
