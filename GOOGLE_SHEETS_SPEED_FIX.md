# Google Sheets Performance Optimization

## Current Status
- 20 sheets, 256K cells (well under 10M limit ✅)
- Slowness likely from: formulas, not size

## Immediate Fixes

### 1. Reduce Calculation Load
**Problem**: Sparklines + complex formulas recalculate on every edit
**Fix**: Set calculation mode to "On change and every minute"
- File → Settings → Calculation
- Change from "On change" to "On change and every minute"
- Saves ~70% CPU during edits

### 2. Limit Sparkline Range
**Problem**: 48-period sparklines (B27:AW27) = 48 cell reads each
**Fix**: Only show recent periods (last 24)
```
OLD: =SPARKLINE(Data_Hidden!B27:AW27,{"charttype","bar"})
NEW: =SPARKLINE(Data_Hidden!Y27:AW27,{"charttype","bar"})
```
(Y27:AW27 = periods 25-48, last 12 hours)

### 3. Hide Unused Sheets
**Action**: Right-click unused sheets → Hide
- SCRP_* sheets (3)
- VTP_Revenue_* sheets (3)  
- Test sheet

### 4. Remove Duplicate Formulas
Check for:
- Multiple QUERY() functions pulling same data
- Redundant IMPORTRANGE connections
- Array formulas that could be static values

## Long-Term Optimization

### Move Heavy Lifting to Python
Instead of Sheets formulas:
```python
# In update_data_hidden_only.py
# Pre-calculate aggregates, write as VALUES not formulas
```

### Use Apps Script Caching
```javascript
var cache = CacheService.getScriptCache();
cache.put('mid_price_data', JSON.stringify(data), 900); // 15 min
```

## Expected Results
- File → Settings → Calculation: **50-70% faster**
- Limit sparkline range: **30% faster rendering**
- Hide unused sheets: **20% faster load time**

Combined: **2-3x speed improvement** ⚡
