# MPAN Details Extraction - Complete

## Overview
Successfully implemented comprehensive MPAN detail extraction and display in BESS sheet columns E10-J10.

## Sheet Layout

### Row 5: Headers
- **A5-H5**: DNO information (Postcode, MPAN ID, DNO Key, etc.)
- **I5**: Supplement (MPAN supplement letter)
- **J5**: MPAN Core (LLFC code)

### Row 6: Input/Output Data
- **A6**: Postcode (INPUT)
- **B6-H6**: DNO information (OUTPUT - auto-populated)
- **I6**: Supplement (INPUT - A/B/C/D/E/F/P/Q)
- **J6**: LLFC code (INPUT - 3-4 digits)

### Row 9: MPAN Detail Headers
- **E9**: Profile Class
- **F9**: Meter Registration
- **G9**: Voltage Level
- **H9**: DUoS Charging Class
- **I9**: Tariff ID
- **J9**: Loss Factor

### Row 10: MPAN Detail Values (AUTO-POPULATED)
- **E10**: Profile Class (e.g., "01-04" for LV, "00" for HH)
- **F10**: Meter Registration (e.g., "801 (Non-Domestic)")
- **G10**: Voltage Level (auto-detected from supplement/LLFC)
- **H10**: DUoS Charging Class (from BigQuery tariff lookup)
- **I10**: Tariff ID (the LLFC itself)
- **J10**: Loss Factor (e.g., "1.045" for ~4.5% line losses)

## How It Works

### 1. User Input
Enter MPAN details in I6 and/or J6:
- **I6**: Supplement letter (A, B, C, D, E, F, P, Q)
- **J6**: LLFC code (e.g., 0840, 3456)

### 2. Automatic Processing
When DNO refresh is triggered, the system:

1. **Reads supplement and LLFC** from I6/J6
2. **Auto-detects voltage** if not manually set in A10
3. **Extracts Profile Class** from supplement:
   - A/B → "01-04" or "05-08" (LV non-HH)
   - C/D/P/E/F/Q → "00" (HH metered)
4. **Determines Meter Registration**:
   - LV → "801 (Non-Domestic)"
   - HV/EHV → "851 (HH)"
5. **Queries DUoS Charging Class** from BigQuery
6. **Displays Tariff ID** (the LLFC itself)
7. **Calculates Loss Factor**:
   - Queries BigQuery `duos_unit_rates` table
   - Falls back to estimation based on voltage:
     - LV (0xxx-2xxx): 1.045 (~4.5% losses)
     - HV (3xxx-5xxx): 1.025 (~2.5% losses)
     - EHV (6xxx-7xxx): 1.015 (~1.5% losses)

### 3. Display
All 6 MPAN detail fields populate in E10:J10 with light yellow background.

## Code Architecture

### New Files Created

**setup_mpan_details_section.py** (87 lines):
- Sets up E9:J9 headers and E10:J10 data cells
- Formats headers with blue background, bold text
- Formats data cells with yellow background

**mpan_detail_extractor.py** (189 lines):
- `extract_mpan_details()` - Main extraction function
- `get_duos_charging_class()` - BigQuery tariff lookup
- `get_loss_factor()` - BigQuery loss factor lookup
- `estimate_loss_factor()` - Fallback estimation
- `generate_tou_description()` - TOU structure description

**test_mpan_details.py** (30 lines):
- Helper to add test MPAN data to sheet
- Used for testing extraction

**verify_mpan_display.py** (62 lines):
- Reads and displays MPAN section from sheet
- Verifies correct data population

### Updated Files

**dno_lookup_python.py**:
- Added MPAN detail extraction (after line 500)
- Calls `extract_mpan_details()` when I6 or J6 populated
- Populates E10:J10 with extracted details
- Prints summary of MPAN details extracted

## Example Test Case

### Input:
```
A6: rh19 4lx (postcode)
I6: A (LV supplement)
J6: 0840 (LV LLFC)
A10: LV (<1kV) (voltage dropdown)
```

### Output:
```
C6-H6: UKPN-SPN | UK Power Networks (South Eastern) | SPN | SEEB | J | South Eastern
B10-D10: 7.25 | 0.31 | 0.04 (Red/Amber/Green rates p/kWh)
E10-J10: 01-04 | 801 (Non-Domestic) | LV | Non-Domestic | 0840 | 1.045
```

## MPAN Component Reference

### Profile Classes
- **00**: Half-hourly metered (HH) - typically HV/EHV
- **01-04**: LV non-HH (various TOU structures)
- **05-08**: LV non-HH (domestic-style)

### Supplement Letters
- **A**: LV, Profile Class 01-04
- **B**: LV, Profile Class 05-08
- **C**: HV, usually Profile Class 00 (HH)
- **D**: HV, Profile Class 00 (HH)
- **E**: EHV, Profile Class 00 (HH)
- **F**: EHV, Profile Class 00 (HH)
- **P**: HV, Profile Class 00 (HH)
- **Q**: EHV, Profile Class 00 (HH)

### LLFC (Line Loss Factor Class)
- **0xxx-2xxx**: LV tariffs
- **3xxx-5xxx**: HV tariffs
- **6xxx-7xxx**: EHV tariffs

### Meter Timeswitch Codes (MTC)
- **801**: Non-Domestic standard
- **851**: Non-Domestic HH
- **491**: Domestic unrestricted
- **510**: Domestic Economy 7

### Loss Factors
Percentage adjustment for line losses:
- **LV**: 1.045 (4.5% losses)
- **HV**: 1.025 (2.5% losses)
- **EHV**: 1.015 (1.5% losses)

## Testing

### Manual Test:
```bash
# Add test data
python3 test_mpan_details.py

# Run DNO lookup
python3 dno_lookup_python.py

# Verify display
python3 verify_mpan_display.py
```

### Expected Output:
```
✅ Updated MPAN details in E10:J10
   Profile Class: 01-04
   Meter Registration: 801 (Non-Domestic)
   Voltage Level: LV
   DUoS Charging Class: Non-Domestic
   Tariff ID: 0840
   Loss Factor: 1.045
```

## Next Steps

1. **Update Apps Script webhook URL** to new ngrok tunnel
2. **Test button-triggered refresh** from Google Sheets
3. **Add validation** for supplement/LLFC format
4. **Enhance loss factor lookup** with real BigQuery data
5. **Add TOU structure description** to display

## Status

✅ MPAN details section created  
✅ Headers formatted in E9:J9  
✅ Data cells formatted in E10:J10  
✅ Extraction logic implemented  
✅ Profile Class detection working  
✅ Meter Registration display working  
✅ Voltage auto-detection working  
✅ DUoS Charging Class lookup working  
✅ Tariff ID display working  
✅ Loss Factor estimation working  
✅ Integration with DNO lookup complete  
✅ Tested with sample data  
✅ Verified in Google Sheet  

**Last Updated**: November 22, 2025  
**Files Modified**: 4 new files, 1 updated file  
**Total Lines Added**: ~400 lines
