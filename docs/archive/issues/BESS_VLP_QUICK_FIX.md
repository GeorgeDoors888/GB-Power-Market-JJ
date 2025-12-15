# 🚨 BESS VLP - Quick Fix (4 Minutes)

## ✅ Good News: Everything Works!

I just tested your postcode "rh19 4lx" with Python and got perfect results:

```
✅ Postcode: RH19 4LX (Mid Sussex)
✅ Coordinates: 51.118716, -0.024898
✅ DNO Found: UK Power Networks (South Eastern)
   - MPAN: 19
   - Key: UKPN-SPN  
   - GSP: J (South Eastern)
   - Participant: SEEB
✅ Sheet Updated: Row 10 filled with all 8 columns
```

**View it live**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit#gid=244875982

---

## 🔧 The One Thing Missing

Your Apps Script needs **BigQuery API v2** service enabled.

### How To Fix (2 Minutes):

1. **Open Apps Script**
   - Google Sheets → Extensions → Apps Script

2. **Add BigQuery Service** ← THIS IS THE FIX
   - Left sidebar: Look for "Services"
   - Click the **+** (plus sign) next to "Services"
   - Search box: Type "BigQuery"
   - Click on: "BigQuery API"
   - Version: Select "v2"
   - Click: "Add"
   
3. **Authorize**
   - Top dropdown: Select "onOpen"
   - Click "Run" ▶️
   - Click "Review permissions"
   - Choose your account
   - Click "Advanced" → "Go to [Project] (unsafe)" → "Allow"

4. **Test It**
   - Refresh your Google Sheets
   - Go to BESS_VLP tab
   - Menu: 🔋 BESS VLP Tools → Lookup DNO
   - Row 10 should populate with DNO info!

---

## What You Should See

After clicking "Lookup DNO":

**Row 10** (A10 to H10):
```
19 | UKPN-SPN | UK Power Networks (South Eastern) | SPN | SEEB | J | South Eastern | Kent Surrey Sussex...
```

**Row 11**:
```
Last updated: [timestamp]
```

**Row 14-15** (coordinates):
```
B14: 51.118716
B15: -0.024898
```

Green highlight on row 10.

---

## Why This Happened

Apps Script runs in a sandbox. Even though your GCP project has BigQuery, Apps Script needs explicit permission to use it. That's what adding the "Service" does - it gives Apps Script access to BigQuery APIs.

---

## If Still Not Working

Check the execution log for errors:
- Apps Script editor
- View → Logs (or Ctrl+Enter)
- Look for red error messages

Common errors:
- "BigQuery is not defined" → BigQuery service not added
- "Unauthorized" → Need to re-authorize
- "Sheet not found" → Check tab name is "BESS_VLP" (exact)

---

## Quick Reference

**What works**: ✅ Python test, ✅ Sheets API, ✅ Postcode API, ✅ BigQuery query  
**What's missing**: BigQuery service in Apps Script  
**Time to fix**: 2-4 minutes  
**Detailed guide**: See `BESS_VLP_COMPLETE_FIX_GUIDE.md`

---

*Your postcode lookup is working perfectly - just needs Apps Script authorization!*
