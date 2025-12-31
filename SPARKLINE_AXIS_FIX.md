# Sparkline Axis Fix - 29 December 2025

## 🔍 Issue Identified

**User Report**: Merged sparkline formula in Google Sheets includes `"axis",true;"axiscolor","#999"` but script wasn't generating these options.

**Your Formula** (from merged cell):
```
=IFERROR(LET(r,{1505,1504,...},x,FILTER(r,(r<>0)*(r<>"")),lo,MIN(x),hi,MAX(x),span,hi-lo,pad,MAX(1,span*0.15),
SPARKLINE(IF((r=0)+(r=""),NA(),r),{"charttype","column";"axis",true;"axiscolor","#999";"color","#34A853";"negcolor","#EA4335";"empty","ignore";"ymin",lo-pad;"ymax",hi+pad})),"")
```

**Code Generated** (before fix):
```python
sparkline_options = f'{"charttype","column";"color","{color}";"negcolor","{negcolor}";"empty","ignore";"ymin",lo-pad;"ymax",hi+pad}'
# ❌ Missing: "axis",true;"axiscolor","#999"
```

---

## ❌ Impact

**Without axis option**:
- Sparklines don't show the **zero baseline axis**
- Hard to distinguish positive vs negative values visually
- Especially important for **interconnectors** (can go negative) and **imbalance prices**

**Affected Charts**:
- ❌ Interconnector flows (G13:I22) - can be negative (imports vs exports)
- ❌ Pumped Storage (row 10) - negative = charging, positive = generating
- ❌ BM cashflow sparklines - can have negative settlement periods
- ❌ All column charts without clear zero reference

---

## ✅ Solution Implemented

**File**: `update_live_metrics.py`  
**Function**: `generate_gs_sparkline_with_let()` (Lines 101-141)

### Before Fix
```python
# Build sparkline options based on chart type
if charttype == "column" and negcolor:
    sparkline_options = f'{{"charttype","column";"color","{color}";"negcolor","{negcolor}";"empty","ignore";"ymin",lo-pad;"ymax",hi+pad}}'
else:
    sparkline_options = f'{{"charttype","{charttype}";"color","{color}";"empty","ignore";"ymin",lo-pad;"ymax",hi+pad}}'
```

### After Fix
```python
# Build sparkline options based on chart type
# ALWAYS include axis for column charts (shows zero baseline), use axiscolor #999 for subtle gray line
if charttype == "column" and negcolor:
    sparkline_options = f'{{"charttype","column";"axis",true;"axiscolor","#999";"color","{color}";"negcolor","{negcolor}";"empty","ignore";"ymin",lo-pad;"ymax",hi+pad}}'
elif charttype == "column":
    sparkline_options = f'{{"charttype","column";"axis",true;"axiscolor","#999";"color","{color}";"empty","ignore";"ymin",lo-pad;"ymax",hi+pad}}'
else:
    sparkline_options = f'{{"charttype","{charttype}";"color","{color}";"empty","ignore";"ymin",lo-pad;"ymax",hi+pad}}'
```

**Changes**:
1. ✅ Added `"axis",true` to ALL column charts (shows zero baseline)
2. ✅ Added `"axiscolor","#999"` for subtle gray axis line
3. ✅ Split into 3 branches: column+negcolor, column-only, other (line charts)
4. ✅ Line charts DON'T get axis (looks wrong with continuous lines)

---

## 🧪 Verification Tests

### Test 1: Column Chart with Negcolor (Interconnectors)
```python
generate_gs_sparkline_with_let([1505, 1504, -113, -114], color="#34A853", charttype="column", negcolor="#EA4335")
```
**Result**: ✅ PASS - Contains `"axis",true;"axiscolor","#999"`

### Test 2: Column Chart without Negcolor (Standard KPIs)
```python
generate_gs_sparkline_with_let([100, 200, 150, 180], color="#FFD700", charttype="column")
```
**Result**: ✅ PASS - Contains `"axis",true;"axiscolor","#999"`

### Test 3: Line Chart (Should NOT have axis)
```python
generate_gs_sparkline_with_let([50, 55, 52, 60], color="#4169E1", charttype="line")
```
**Result**: ✅ PASS - No axis option (correct for line charts)

---

## 📊 Affected Dashboard Elements

**Now Fixed** (will show zero baseline):
- ✅ Interconnector sparklines (G13:I22) - 10 interconnectors
- ✅ Fuel generation sparklines (A13:D22) - 10 fuel types
- ✅ KPI sparklines (N13:S31) - 10 consolidated KPIs
- ✅ EWAP sparklines (U13:U18) - 6 EWAP/imbalance KPIs (column charts only)
- ✅ Market metrics sparklines (L14:L18) - 5 spreads/volumes
- ✅ Weekly KPI sparklines (K33:L43) - 11 weekly metrics

**Already Had Axis** (no change needed):
- ✅ Pumped Storage symmetric sparkline (`generate_gs_sparkline_with_symmetric_let`) - Line 172 already includes `"axis",TRUE;"axiscolor","#999999"`

---

## 🎨 Visual Impact

**Before** (no axis):
```
█
  █
    █  █     (hard to see if values are positive or negative)
       █
```

**After** (with axis):
```
█
  █
─────────────  (gray zero baseline - clear reference)
    █  █
       █
```

**Axis Color**: `#999` = subtle medium gray, doesn't distract from data

---

## 🚀 Next Steps

**Recommended**:
1. **Test run**: `python3 update_live_metrics.py` to regenerate all sparklines
2. **Visual check**: Open dashboard, verify zero baseline appears on column charts
3. **Interconnectors**: Check rows G13:I22 - negative values (imports) should show below axis
4. **Pumped Storage**: Check row 10 - charging (negative) should show below axis clearly

**Expected Behavior**:
- Column charts: Zero baseline visible (gray line)
- Line charts: No axis (continuous flow, axis looks broken)
- Negative values: Clearly shown below zero baseline in red

---

## 📝 Related Functions

**Primary Function** (now fixed):
- `generate_gs_sparkline_with_let()` - Lines 101-141

**Other Sparkline Functions** (already correct or not affected):
- `generate_gs_sparkline_formula()` - Lines 54-99 (simple sparklines, no LET/auto-scale)
- `generate_gs_sparkline_posneg_bar()` - Lines 136-149 (wrapper, uses fixed function)
- `generate_gs_sparkline_with_symmetric_let()` - Lines 152-172 ✅ Already has axis

---

## ✅ Summary

**Problem**: Sparkline axis options missing from code-generated formulas  
**Root Cause**: `generate_gs_sparkline_with_let()` didn't include `"axis",true;"axiscolor","#999"`  
**Solution**: Added axis options to all column charts, excluded from line charts  
**Status**: ✅ FIXED - All tests pass

**Result**: Column sparklines now match your manually merged formula exactly ✅

---

*Fixed: 29 December 2025*  
*Function: generate_gs_sparkline_with_let() - Lines 101-141*
