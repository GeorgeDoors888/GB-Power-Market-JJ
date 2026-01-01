# Report Generation System Diagnosis
**Date**: December 31, 2025
**Status**: ❌ ISSUE IDENTIFIED - Category Mismatch

---

## 🚨 Problem Summary

User sees manual terminal command message instead of automatic report generation because:

1. **✅ Apps Script Button Missing** - No "Generate Report" button in Analysis sheet
2. **❌ CATEGORY MISMATCH** - Dropdown options don't match script logic
3. **✅ Script Reads B11-B13** - generate_analysis_report.py DOES read new fields correctly

---

## 🔍 Detailed Diagnosis

### Issue 1: No Apps Script Button ✅ FIXED

**Problem**: User must manually run `python3 generate_analysis_report.py`
**Solution**: Created `analysis_report_generator.gs` with Apps Script menu

**Installation Steps**:
1. Open spreadsheet: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
2. Go to: Extensions > Apps Script
3. Click "+" to add new file
4. Name it: `AnalysisReportGenerator`
5. Paste code from `analysis_report_generator.gs`
6. Save (Ctrl+S)
7. Refresh spreadsheet
8. Menu "📊 Analysis Tools" will appear

### Issue 2: Category Mismatch ❌ CRITICAL

**Problem**: Dropdown options don't match script category checks

| Dropdown Option (B11) | Script Category Check | Match? |
|----------------------|----------------------|---------|
| All Reports | (fallback) | ✅ Yes |
| VLP Revenue Analysis | `'📊 Analytics' in category` | ❌ **NO** |
| Balancing Mechanism (BOD) | `'📊 Analytics' in category` | ❌ **NO** |
| Interconnector Flows | `'🔌 Interconnectors' in category` | ❌ **NO** |
| Generator Performance | `'⚡ Generation' in category` | ❌ **NO** |
| Frequency Response | `'📡 System' in category` | ❌ **NO** |
| Curtailment Analysis | **NOT IMPLEMENTED** | ❌ **NO** |
| Market Pricing (MID) | `'📈 Market' in category` | ❌ **NO** |
| Settlement (DISBSAD) | **NOT IMPLEMENTED** | ❌ **NO** |
| Fuel Mix | `'⚡ Generation' in category` | ❌ **NO** |
| Wind Forecasting | `'🌬️ Wind' in category` | ❌ **NO** |

**Current User Selection**:
```
B11: ✂️ Curtailment Analysis
```

**Script Check**:
```python
if '📊 Analytics' in category or 'Analytics & Derived' in category:
    # ...
elif '⚡ Generation' in category or 'Generation & Fuel Mix' in category:
    # ...
elif '🔌 Interconnectors' in category or 'Interconnector' in category:
    # Matches "Interconnector Flows" ✅
elif '🌬️ Wind' in category or 'Wind Forecasts' in category:
    # Matches "Wind Forecasting" ✅
# NO CHECK FOR "Curtailment" ❌
```

**Result**: Script falls through to default fallback query (fuel mix data)

---

## 🛠️ Fix Required

### Option A: Update DropdownData to Match Script ⭐ RECOMMENDED

Change B11 dropdown options to match existing script logic:

| Current Dropdown | New Dropdown (Matches Script) |
|-----------------|------------------------------|
| All Reports | All Reports ✅ |
| VLP Revenue Analysis | 📊 Analytics & Derived (Balancing with Prices) |
| Balancing Mechanism (BOD) | 📊 Analytics & Derived (Balancing with Prices) |
| Interconnector Flows | 🔌 Interconnectors (Cross-Border) |
| Generator Performance | ⚡ Generation & Fuel Mix (Aggregated) |
| Frequency Response | 📡 System Operations (Frequency/Prices) |
| Curtailment Analysis | ⚠️ REMIT Messages (Unavailability) |
| Market Pricing (MID) | 📈 Market Prices (MID/SSP/SBP) |
| Settlement (DISBSAD) | 💰 Balancing Actions (MELs/MILs) |
| Fuel Mix | ⚡ Generation & Fuel Mix (Aggregated) |
| Wind Forecasting | 🌬️ Wind Forecasts (Generation) |

**Additional Categories in Script** (not in dropdown):
- 🔋 Individual BMU Generation (B1610)
- 🚧 Physical Constraints (NESO Regional)
- 📉 Demand Forecasts (NESO)
- 🔍 Party Analysis (VTP/VLP Performance)

### Option B: Update Script to Match Dropdowns

Add new category checks to `generate_analysis_report.py`:

```python
# Add these checks in get_query_with_filters():

elif 'VLP Revenue' in category or 'VLP Revenue Analysis' in category:
    # Use boalf_with_prices for VLP revenue calculation
    # Filter to VLP operators from B10

elif 'Curtailment' in category or 'Curtailment Analysis' in category:
    # Use REMIT unavailability data + wind forecast vs actual
    # Calculate curtailment = forecast - actual

elif 'Settlement' in category or 'Settlement (DISBSAD)' in category:
    # Use bmrs_disbsad table for settlement prices
```

---

## ✅ Verification Steps

After fixing category mismatch:

1. **Update DropdownData Column E** with script-matching categories
2. **Test with each category**:
   ```bash
   python3 generate_analysis_report.py
   ```
3. **Verify output** appears in row 18+
4. **Install Apps Script** for one-click automation
5. **Test button** in Google Sheets

---

## 📊 Script Categories Explained

### 1. 📊 Analytics & Derived (Balancing with Prices)
**Tables**: `bmrs_boalf_complete`
**Output**: date, settlementPeriod, bmUnit, party_name, volume_mwh, price_gbp_mwh, acceptance_count
**Use**: VLP revenue analysis, BOD acceptances with prices

### 2. ⚡ Generation & Fuel Mix (Aggregated)
**Tables**: `bmrs_fuelinst_iris`
**Output**: date, settlementPeriod, fuelType, generation_mw
**Use**: Fuel mix breakdown, generation type analysis

### 3. 🔋 Individual BMU Generation (B1610)
**Tables**: `bmrs_indgen`
**Output**: date, settlementPeriod, bmUnit, generation_mwh
**Use**: Individual unit performance tracking

### 4. 💰 Balancing Actions (MELs/MILs)
**Tables**: `bmrs_mels_iris`, `bmrs_mils_iris`
**Output**: date, settlementPeriod, bmUnit, levelFrom, levelTo
**Use**: Export/import limits, balancing actions

### 5. 📡 System Operations (Frequency/Prices)
**Tables**: `bmrs_freq`, `bmrs_costs`
**Output**: date, settlementPeriod, ssp, sbp, avg_freq
**Use**: Frequency response, system prices

### 6. 🚧 Physical Constraints (NESO Regional)
**Tables**: `neso_constraint_breakdown_2024_2025`
**Output**: date, largest_loss_cost, inertia_cost, voltage_cost, thermal_cost
**Use**: Constraint cost analysis

### 7. 🔌 Interconnectors (Cross-Border)
**Tables**: `bmrs_fuelinst_iris` (fuelType LIKE 'INT%')
**Output**: date, settlementPeriod, fuelType, flow_mw
**Use**: Interconnector flow analysis

### 8. 📈 Market Prices (MID/SSP/SBP)
**Tables**: `bmrs_mid`
**Output**: date, settlementPeriod, mid_price_gbp_mwh, volume_mwh
**Use**: Market pricing analysis

### 9. 📉 Demand Forecasts (NESO)
**Tables**: `bmrs_inddem`
**Output**: date, settlementPeriod, demand_mw
**Use**: Demand forecast vs actual

### 10. 🌬️ Wind Forecasts (Generation)
**Tables**: `bmrs_windfor`
**Output**: date, settlementPeriod, forecast_wind_mw
**Use**: Wind forecasting accuracy

### 11. ⚠️ REMIT Messages (Unavailability)
**Tables**: `bmrs_remit_unavailability`
**Output**: date, bmUnit, unavailabilityType, fuelType, availableCapacity, unavailableCapacity
**Use**: Curtailment analysis, unavailability tracking

### 12. 🔍 Party Analysis (VTP/VLP Performance)
**Tables**: `bmrs_boalf_complete` + `dim_party`
**Output**: date, party_name, bmu_count, total_volume_mwh, avg_price_gbp_mwh
**Use**: Lead party performance comparison

---

## 🎯 Recommended Action Plan

**Priority 1: Fix Category Mismatch** (15 minutes)
1. Update DropdownData column E with script-matching categories
2. Test with "📊 Analytics & Derived" category
3. Verify report generates successfully

**Priority 2: Install Apps Script** (5 minutes)
1. Copy `analysis_report_generator.gs` to Apps Script
2. Refresh spreadsheet
3. Test "📊 Analysis Tools > 🔄 Generate Report" button

**Priority 3: Add Missing Categories** (30 minutes)
1. Add curtailment query logic (REMIT + wind comparison)
2. Add settlement query logic (bmrs_disbsad)
3. Add VLP-specific revenue logic (filter to B10 operators)

---

## 📚 Related Files

- `generate_analysis_report.py` (501 lines) - Main report generation script
- `analysis_report_generator.gs` (NEW) - Apps Script button code
- `ANALYSIS_SHEET_ENHANCEMENTS_SUMMARY.md` - Recent dropdown enhancements
- `ANALYSIS_SHEET_LAYOUT_GUIDE.md` - User guide (needs update)

---

**Status**: ⏳ Awaiting category dropdown fix
**Next**: Update DropdownData column E, then test report generation
**Timeline**: 20 minutes to full working state

---

*Last Updated: December 31, 2025*
