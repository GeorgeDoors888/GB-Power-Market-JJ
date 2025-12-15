# SPREADSHEET IDs - MASTER REFERENCE

**⚠️ CRITICAL: READ THIS BEFORE WRITING ANY SCRIPT ⚠️**

This file exists because the AI kept confusing two different spreadsheets with similar names.

---

## 🎯 PRIMARY ACTIVE SPREADSHEET (USE THIS!)

**Name:** Live Dashboard v2  
**Spreadsheet ID:** `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`  
**URL:** https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit  
**Script ID:** `1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980`

**Worksheets:**
- `Live Dashboard v2` - Main IRIS real-time dashboard
- `BtM` - Behind the meter analysis
- `BESS_Event` - Battery event tracking
- `BtM Calculator` - Cost calculations
- `BtM Daily` - Daily summaries
- `GB Live` - Legacy sheet (not primary)
- `Live Dashboard` - Legacy sheet

**Update Scripts:**
- ✅ `update_live_dashboard_v2.py` - Main updater (CURRENTLY ACTIVE via cron)
- ✅ `update_gb_live_complete.py` - Complete updater with sparklines (FIXED Dec 11, 2025)
- ✅ `auto_update_dashboard_v2.sh` - Cron wrapper

**Cron Schedule:**
```bash
*/5 * * * * /home/george/GB-Power-Market-JJ/auto_update_dashboard_v2.sh
```

**Apps Script:** Add sparklines with `add_gb_live_sparklines.gs`

**Status:** ✅ ACTIVE - Updates every 5 minutes with IRIS data

---

## ⚠️ SECONDARY SPREADSHEET (OLD - DO NOT USE FOR LIVE DATA!)

**Name:** GB Live / BtM Dashboard (OLD)  
**Spreadsheet ID:** `1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I`  
**URL:** https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/

**Worksheets:**
- `GB Live` - Old live dashboard
- `BtM` - Old BtM sheet
- `BESS` - BESS configuration
- Various other legacy sheets

**Update Scripts:**
- ⚠️ `update_gb_live_executive.py` - Old updater (DO NOT USE for live dashboard)
- ⚠️ `update_bg_live_dashboard.py` - Legacy script

**Status:** ⚠️ LEGACY - May still receive some updates but NOT the primary dashboard

**Documentation References (INCORRECT FOR LIVE DATA):**
- `GB_LIVE_DATA_SOURCES.md` - Documents THIS old spreadsheet
- Various other GB_LIVE_*.md files reference this ID

---

## 🚨 HOW TO AVOID CONFUSION

### When Creating a New Script:

1. **ALWAYS USE:** `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`
2. **NEVER USE:** `1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I` (unless specifically working on legacy sheet)

### Template for New Scripts:

```python
# Configuration - LIVE DASHBOARD V2
SPREADSHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'  # Live Dashboard v2
SHEET_NAME = 'Live Dashboard v2'
```

### Template for Apps Script:

```javascript
function myFunction() {
  // Live Dashboard v2 - CORRECT SPREADSHEET
  const ss = SpreadsheetApp.openById('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA');
  const sheet = ss.getSheetByName('Live Dashboard v2');
  // ...
}
```

---

## 📋 VERIFICATION CHECKLIST

Before committing any script that accesses Google Sheets:

- [ ] Does it use `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`?
- [ ] Does it reference `Live Dashboard v2` worksheet?
- [ ] Have you tested it opens the correct spreadsheet?
- [ ] Does the cron job log to the correct file?

---

## 🔍 QUICK IDENTIFICATION

**If you see this ID:** `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`  
→ ✅ CORRECT - Live Dashboard v2

**If you see this ID:** `1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I`  
→ ❌ WRONG - Old GB Live (unless specifically working on legacy features)

---

## 📊 OTHER IMPORTANT SPREADSHEET IDs

**VLP Analysis Dashboard:**
- ID: `12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8`
- URL: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
- Purpose: VLP revenue analysis, battery arbitrage
- Script: Various VLP analysis scripts

---

## 🐛 DEBUGGING WRONG SPREADSHEET ISSUES

If data isn't updating in Live Dashboard v2:

1. Check the script is using correct ID: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`
2. Check cron is running the correct script: `crontab -l | grep dashboard`
3. Check logs: `tail -f ~/dashboard_v2_updates.log`
4. Verify spreadsheet in browser matches the URL above
5. Check script output references correct URL in success message

---

## 📝 ERROR HISTORY

**December 11, 2025:**
- AI created `update_gb_live_complete.py` targeting WRONG spreadsheet
- Caused by referencing `GB_LIVE_DATA_SOURCES.md` which documents old spreadsheet
- Fixed by updating all hardcoded IDs to correct value
- Created this master reference document to prevent future confusion

**Root Cause:** Multiple documentation files reference the old spreadsheet ID, causing confusion when creating new scripts.

**Solution:** THIS FILE is the single source of truth. Ignore other references.

---

**Last Updated:** December 11, 2025, 23:05  
**Maintained By:** George Major  
**Status:** ✅ AUTHORITATIVE REFERENCE
