# 🩺 Diagnostic Functions Added

## What's New

Added comprehensive diagnostic functions to help troubleshoot CLASP deployment issues:

### 1. **Full Diagnostics** (Apps Script Editor)
Run from Apps Script editor to get detailed environment report:

```javascript
function diagnostics()
```

**What it checks:**
- ✅ Current user and permissions
- ✅ Script ID and URLs
- ✅ Spreadsheet information
- ✅ Required sheets (GB Live, Data_Hidden, BtM, DNO)
- ✅ Active triggers
- ✅ Service availability (Drive, UrlFetch)
- ✅ Data_Hidden content (sample values)
- ✅ Sparkline formulas in C11 and F11
- ✅ GitHub GeoJSON accessibility

**How to run:**
1. Open Apps Script editor (Extensions → Apps Script)
2. Select `diagnostics` from function dropdown
3. Click Run ▶️
4. View results: View → Executions log

### 2. **Quick Health Check** (Google Sheets Menu)
Run directly from Google Sheets menu for instant status:

```
⚡ GB Live Dashboard → 🏥 Health Check
```

**Shows:**
- Sheet availability
- Sparkline formula status
- Data presence
- Active triggers count

**How to use:**
1. In Google Sheets, click: ⚡ GB Live Dashboard
2. Click: 🏥 Health Check
3. Read popup alert with results

## Deployment Information

From your message:

```
Deployment ID: AKfycbxwFCjNeh7YRiO46aSceM5D03XFa11dPosYsMkOdKg_9HgVxEK-PnTdoibMamKTmMsh
Web app URL: https://script.google.com/macros/s/AKfycbxwFCjNeh7YRiO46aSceM5D03XFa11dPosYsMkOdKg_9HgVxEK-PnTdoibMamKTmMsh/exec
Version: 3 (8 Dec 2025, 22:31)
Status: Successfully updated
```

✅ **Deployment is active!**

## Next Steps

### 1. Run Full Diagnostics
```
1. Open: Extensions → Apps Script
2. Select function: diagnostics
3. Click: Run ▶️
4. Check: View → Executions
```

### 2. Check Output
Look for these key indicators:

**✅ Good:**
```
✅ User: your-email@gmail.com
✅ Spreadsheet: BtM
✅ GB Live (ID: 1535990597)
✅ Data_Hidden (ID: 594163331)
✅ Drive API: Enabled
✅ GitHub accessible - 14 features
```

**❌ Problems:**
```
❌ GB Live - NOT FOUND
❌ Data_Hidden sheet not found
⚠️ Insufficient data (3 values)
❌ Column C missing formulas
❌ HTTP 404: Not Found
```

### 3. Test from Google Sheets
```
1. Refresh spreadsheet (F5)
2. Check menus appear:
   - ⚡ GB Live Dashboard
   - 🗺️ DNO Map
3. Click: ⚡ GB Live Dashboard → 🏥 Health Check
4. Read results popup
```

### 4. Test Sparkline Writer
```
1. Click: ⚡ GB Live Dashboard → ✨ Write Sparkline Formulas
2. Wait 5 seconds
3. Check columns C11-C20 and F11-F20 for charts
```

## Troubleshooting Common Issues

### Issue: "Data_Hidden not found"
**Solution:** Run Python script first:
```bash
cd /home/george/GB-Power-Market-JJ
python3 update_bg_live_dashboard.py
```

### Issue: "No menus appear"
**Solution:** 
1. Check deployment is active (you confirmed this ✅)
2. Refresh spreadsheet (Ctrl+R or F5)
3. Check execution log for errors

### Issue: "Sparklines show #N/A"
**Solution:**
1. Verify Data_Hidden has numeric values (not strings)
2. Run: ⚡ GB Live Dashboard → 🔍 Verify Data_Hidden
3. Check max value in config matches actual data

### Issue: "Permission denied"
**Solution:**
1. Run any function from Apps Script editor
2. Click "Review Permissions"
3. Select your Google account
4. Click "Allow"

## What the Deployment URL Does

Your web app URL can be called from external services:

```bash
# Test webhook endpoint
curl -X POST "https://script.google.com/macros/s/AKfycbxwFCjNeh7YRiO46aSceM5D03XFa11dPosYsMkOdKg_9HgVxEK-PnTdoibMamKTmMsh/exec"
```

**Expected response:**
```json
{
  "status": "success",
  "message": "Sparklines written successfully",
  "timestamp": "2025-12-08T22:31:00.000Z"
}
```

## Understanding the Diagnostics Output

### Script URL
```
Script URL: 1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I
Full URL: https://script.google.com/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/edit
```
This is your Apps Script project ID (same as spreadsheet ID in this case).

### Sheets Check
```
✅ GB Live (ID: 1535990597)
✅ Data_Hidden (ID: 594163331)
✅ BtM (ID: ...)
✅ DNO (ID: ...)
```
All required sheets present ✅

### Sparkline Formula Check
```
C11: ✅ Has formula
F11: ✅ Has formula
```
Means formulas are written and present.

```
C11: ❌ Empty
F11: ❌ Empty
```
Means sparklines need to be written (run Write Sparkline Formulas).

### Data Check
```
✅ Row 1 (Wind): 24 values
Sample: [14.2, 13.8, 15.1, 14.9, 15.3...]
```
Good - Data_Hidden has numeric data ✅

```
⚠️ Row 1 (Wind): 3 values
```
Problem - Need to run Python script to populate data.

### GitHub Check
```
✅ GitHub accessible - 14 features
```
GeoJSON file loads successfully from GitHub ✅

```
❌ HTTP 404: Not Found
```
GitHub URL incorrect or repo not accessible.

## Files Updated

1. **Code.gs** - Added 3 new functions:
   - `diagnostics()` - Full environment check
   - `checkSheet()` - Sheet existence validator
   - `quickHealthCheck()` - Menu-driven quick check

2. **Menu** - Added health check item:
   ```
   ⚡ GB Live Dashboard
   ├─ ✨ Write Sparkline Formulas
   ├─ 🔍 Verify Data_Hidden
   ├─ 🗑️ Clear Sparklines
   ├─ ───────────────
   └─ 🏥 Health Check  ← NEW
   ```

## Copy Updated Code.gs

The updated Code.gs file is ready at:
```
/home/george/GB-Power-Market-JJ/bg-sparklines-clasp/Code.gs
```

**To deploy:**
1. Copy entire file
2. Paste into Apps Script editor (overwrite existing)
3. Save (Ctrl+S)
4. Refresh spreadsheet

**Size:** ~900 lines (added ~180 lines of diagnostics)

---

**Status:** ✅ Diagnostic functions ready  
**Last Updated:** 8 Dec 2025, 22:40  
**Deployment:** Active (Version 3)
