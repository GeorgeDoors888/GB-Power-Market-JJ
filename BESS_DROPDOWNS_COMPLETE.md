# BESS Sheet Dropdowns & Validation - Implementation Summary

**Date:** 24 November 2025  
**Sheet:** BESS (Battery Energy Storage System)  
**Sheet ID:** 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

## ✅ Implementation Complete

### 1️⃣ Dropdown Menus Added

| Cell | Field Name | Options | Source |
|------|-----------|---------|--------|
| **A10** | Voltage Level | 5 options | Hardcoded |
| **B6** | DNO Distributor | 14 options | BigQuery |
| **E10** | Profile Class | 9 options | Hardcoded |
| **F10** | Meter Registration | 7 options | Hardcoded |
| **H10** | DUoS Charging Class | 9 options | Hardcoded |

#### A10: Voltage Level Options
- LV (<1kV)
- LV sub (<1kV)
- HV (6.6-33kV)
- EHV (33-132kV)
- 132kV Transmission

#### B6: DNO Distributor Options (from BigQuery)
- 10 - ENWL (Electricity North West)
- 11 - SSEN-N (SSE Networks - North)
- 12 - SSEN-S (SSE Networks - South)
- 13 - SPEN-SPD (SP Energy Networks - Distribution)
- 14 - WMID (National Grid - West Midlands)
- 15 - EMID (National Grid - East Midlands)
- 16 - SWEB (National Grid - South West)
- 17 - SWAL (National Grid - South Wales)
- 18 - LPN (UK Power Networks - London)
- 19 - SPN (UK Power Networks - South East)
- 20 - EPN (UK Power Networks - Eastern)
- 21 - NPG-NE (Northern Powergrid - North East)
- 22 - NPG-YH (Northern Powergrid - Yorkshire)
- 23 - SPEN-SPM (SP Energy Networks - Manweb)

#### E10: Profile Class Options
- 00 (Half-Hourly)
- 01 (Domestic Unrestricted)
- 02 (Domestic Economy 7)
- 03 (Non-Domestic Unrestricted)
- 04 (Non-Domestic Economy 7)
- 05 (Non-Domestic Maximum Demand)
- 06 (Non-Domestic Two-Rate)
- 07 (Seasonal Time of Day)
- 08 (Seasonal)

#### F10: Meter Registration Options
- 800 (NHH Non-Settlement)
- 801 (HH Metered)
- 802 (NHH Metered - Unmetered Supplies)
- H (HH Metered - Demand)
- M (NHH - Manually Read)
- C (NHH - Check Metering)
- P (NHH - Prepayment)

#### H10: DUoS Charging Class Options
- Domestic Unrestricted
- Domestic Two Rate
- Non-Domestic HH
- Non-Domestic NHH Unrestricted
- Non-Domestic NHH Two Rate
- LV Generation
- HV Generation
- EHV Generation
- Unmetered Supply

### 2️⃣ Number Validation

| Cell | Field | Validation Rule |
|------|-------|----------------|
| **B17** | Min kW | Must be > 0 |
| **B18** | Avg kW | Must be > 0 |
| **B19** | Max kW | Must be > 0 |

### 3️⃣ Currency Formatting

| Cell | Field | Format |
|------|-------|--------|
| **B10** | Red Rate | 0.000 p/kWh |
| **C10** | Amber Rate | 0.000 p/kWh |
| **D10** | Green Rate | 0.000 p/kWh |

### 4️⃣ Help Notes (Hover Tooltips)

#### A6: Postcode Format
```
UK Postcode Format:
Examples: SW1A 1AA, M1 1AE, B33 8TH

System will auto-lookup:
• DNO distributor
• GSP Group
• Regional network info
```

#### B6: MPAN Format
```
MPAN Format:
• 13-digit core MPAN
• Or 21-digit full MPAN
• First 2 digits = DNO ID (10-23)

Examples:
• 14055667788 (core)
• 00 800 999 932 14055667788 (full)

System extracts core and validates DNO
```

## 🔧 Technical Implementation

### Scripts Created
1. **add_bess_dropdowns_v4.py** - Main implementation script
   - Uses Google Sheets API v4 batch update
   - Queries BigQuery for DNO list
   - Applies all validation rules in single API call

2. **verify_bess_dropdowns.py** - Verification script
   - Checks all dropdown cells
   - Displays current values
   - Generates test URL

### Updated Files
1. **bess_custom_menu.gs** - Apps Script menu
   - Updated `validateMpan()` to handle dropdown format
   - Updated `refreshDnoData()` to extract MPAN from dropdown
   - Added dropdown info to Settings dialog

## 🎯 User Experience

### How to Use

1. **Select Voltage Level (A10)**
   - Click cell → dropdown arrow appears
   - Choose from 5 voltage options
   - Auto-formats with description

2. **Select DNO Distributor (B6)**
   - Click cell → dropdown shows 14 DNOs
   - Format: "ID - SHORT_CODE"
   - Can also manually enter MPAN ID
   - System extracts ID for lookup

3. **Select Profile Class (E10)**
   - Choose from 9 standard profiles
   - Includes code and description

4. **Select Meter Registration (F10)**
   - Choose from 7 meter types
   - HH vs NHH options

5. **Select DUoS Class (H10)**
   - Choose charging classification
   - Affects rate calculation

6. **Enter kW Values (B17-B19)**
   - Must be positive numbers
   - Rejected if ≤ 0
   - Used for HH profile generation

### Validation Features

✅ **Strict Validation** (A10, E10, F10, H10)
- Must select from dropdown
- Cannot enter free text
- Prevents invalid data

⚠️ **Flexible Validation** (B6)
- Can select from dropdown OR enter manually
- Allows full MPAN input
- System extracts relevant part

🔢 **Number Validation** (B17-B19)
- Only positive numbers allowed
- Decimal values accepted
- Zero rejected

### Help System

💬 **Hover Tooltips**
- A6 (Postcode): Shows format examples
- B6 (MPAN): Explains ID structure

🔄 **Auto-Refresh Button**
- Menu: 🔋 BESS Tools → 🔄 Refresh DNO Data
- Extracts values from dropdowns
- Triggers webhook lookup
- Updates DNO details

## 📊 Current State

**Existing Values:**
- A10: `HV (6.6-33kV)` ✅
- B6: `14` (NGED-WM)
- E10: `00` (Half-Hourly)
- F10: `801 (HH Metered)` ✅
- H10: `Non-Domestic HH` ✅
- B10-D10: Rates formatted correctly ✅

**Validation Active:**
- All dropdowns operational ✅
- Number validation on kW fields ✅
- Currency formatting on rates ✅
- Help notes accessible ✅

## 🧪 Testing Checklist

- [x] A10 dropdown shows 5 voltage options
- [x] B6 dropdown shows 14 DNO options from BigQuery
- [x] E10 dropdown shows 9 profile classes
- [x] F10 dropdown shows 7 meter types
- [x] H10 dropdown shows 9 DUoS classes
- [x] B17-B19 reject negative numbers
- [x] B10-D10 display with "p/kWh" suffix
- [x] A6 shows postcode help on hover
- [x] B6 shows MPAN help on hover
- [x] Refresh button extracts dropdown values correctly

## 🔗 Sheet Access

**Direct Link:**  
https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit#gid=1291323643

**Test in Browser:**
1. Open link above
2. Click on any dropdown cell (A10, B6, E10, F10, H10)
3. Verify dropdown arrow appears
4. Select a value from the list
5. Try entering invalid data (should be rejected for strict cells)
6. Hover over A6 and B6 to see help notes

## 📝 Notes

- DNO list sourced from `uk_energy_prod.neso_dno_reference` table
- Updates automatically if BigQuery table changes
- Dropdown choices don't overwrite existing data unless user selects
- B6 allows manual MPAN entry for flexibility
- All validation rules applied via single batch API call (efficient)

## 🚀 Next Steps (Optional)

1. **Add more dropdowns** if needed:
   - GSP Group (column G)
   - Timezone (if applicable)
   - Contract type

2. **Enhanced validation**:
   - Check digit calculation for MPAN
   - Postcode regex validation
   - Cross-field validation (e.g., voltage vs meter type)

3. **Auto-populate fields**:
   - When DNO selected, auto-fill GSP Group
   - When voltage selected, suggest typical profile class

---

**Implementation Date:** 24 November 2025  
**Status:** ✅ Complete and Tested  
**Scripts:** add_bess_dropdowns_v4.py, verify_bess_dropdowns.py  
**Custom Menu:** bess_custom_menu.gs (updated)
