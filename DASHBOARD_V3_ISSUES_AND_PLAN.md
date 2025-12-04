# Dashboard V3 - Issues & Action Plan

**Date:** 4 December 2025  
**Duration:** 20+ hours debugging  
**Status:** 🔴 DNO Map sidebar not working - HTML/Apps Script communication failing

---

## What Works ✅

1. **Dashboard V3 Sheet** - Fully created with:
   - Title: "⚡ GB ENERGY DASHBOARD – REAL-TIME"
   - 7 KPI metrics with formulas
   - 2 dropdowns (Time Range B3, DNO Selector F3)
   - 2 charts (combo chart + net margin chart)
   - Professional layout and formatting

2. **DNO_Map Sheet** - 14 UK DNO regions with correct data:
   - Columns: DNO Code, DNO Name, Latitude, Longitude, Net Margin, Total MWh, PPA Revenue
   - All 14 rows populated correctly
   - Column names match Apps Script expectations

3. **Apps Script Backend** - Functions work when tested directly:
   - `getDnoLocations()` returns 14 DNOs successfully (tested at 00:27:52)
   - `showDnoMap()` opens sidebar successfully
   - Menu "⚡ GB Energy V3" appears correctly
   - Authorization granted, scopes configured

4. **Data Pipeline** - BigQuery to Sheets working:
   - Historical data (bmrs_bod, bmrs_fuelinst, etc.)
   - Real-time IRIS data (bmrs_*_iris tables)
   - Chart Data sheet populated
   - KPIs calculating correctly

---

## What Doesn't Work ❌

### Critical Issue: DNO Map Sidebar Shows "Server Error"

**Symptom:**
- Sidebar opens with title "Select DNO Region" or "DNO Region Selector"
- But shows error: "❌ ERROR: We're sorry, a server error occurred. Please wait a bit and try again."

**What We Know:**
1. `getDnoLocations()` works perfectly when run directly in Apps Script editor
2. Returns 14 DNOs with correct data: `{"code":"10","name":"UKPN-EPN","lat":52.2053,"lng":0.1218,"netMargin":5.2}`
3. Fails ONLY when called from HTML sidebar via `google.script.run`
4. Execution log shows `showDnoMap` completes but NO `getDnoLocations` execution appears
5. This indicates the JavaScript in the HTML isn't successfully calling the Apps Script function

**Probable Root Cause:**
- **HTML/Apps Script sandboxing issue** - The HTML service cannot communicate with Apps Script functions
- OAuth scopes may not be taking effect (need re-authorization)
- Possible IFRAME security policy blocking the call
- Apps Script project may need to be recreated as container-bound script

---

## What We've Tried (Past 20 Hours)

### 1. Fixed Column Name Mismatches ✅
- Changed from `dno_code` → `DNO Code`
- Changed from `dno_name` → `DNO Name`
- Changed from `lat` → `Latitude`
- Changed from `lng` → `Longitude`
- **Result:** Backend now reads data correctly

### 2. Created New Apps Script Project ✅
- Old script ID was broken/inaccessible
- Created fresh container-bound project via `clasp create`
- Script ID: `1KlgBiFBGXfub87ACCfx7y9QugHbT46Mv3bgWtpQ38FvroSTsl8CEiXUz`
- **Result:** Can deploy code but HTML still fails

### 3. Added Error Handling & Logging ✅
- Added try/catch blocks
- Added detailed logging to `getDnoLocations()`
- Added success/failure handlers in HTML
- **Result:** Confirmed function works in isolation, fails from HTML

### 4. Created Simple Test Version (No Google Maps) ✅
- Created `DnoMapSimple.html` - just a list, no map
- Removed Google Maps API dependency
- Still fails with same server error
- **Result:** Proves it's not a Google Maps API issue

### 5. Fixed OAuth Scopes ✅
- Added to `appsscript.json`:
  ```json
  "oauthScopes": [
    "https://www.googleapis.com/auth/spreadsheets.currentonly",
    "https://www.googleapis.com/auth/script.container.ui"
  ]
  ```
- **Result:** Still fails (scopes may not be applying)

### 6. Changed ES6 Syntax to Apps Script Compatible ✅
- Changed `const` → `var`
- Changed arrow functions → `function()`
- Removed template literals
- **Result:** No change in behavior

---

## Action Plan: Get Dashboard V3 LIVE 🎯

### Phase 1: Bypass Apps Script Issue (IMMEDIATE - 2 hours)

**Option A: Python-Only Solution (RECOMMENDED)**

Create Python script to directly update F3 when user manually selects DNO from dropdown:

```python
# python/update_dashboard_v3_kpis.py
"""
Run this script after manually changing F3 DNO dropdown
Recalculates all KPIs based on selected DNO
"""

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from google.cloud import bigquery

SPREADSHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

def update_dashboard_kpis():
    # 1. Read F3 (selected DNO)
    # 2. Query BigQuery for that DNO's data
    # 3. Update F10:L10 with calculated KPIs
    # 4. Update charts if needed
    pass
```

**Pros:**
- Bypasses Apps Script completely
- Uses proven BigQuery → Sheets pipeline
- Can be triggered manually or via cron
- We know this works (current dashboard update scripts)

**Cons:**
- Not real-time interactive (need to run script)
- No map selector UI

**TODO:**
1. [ ] Create `python/update_dashboard_v3_kpis.py`
2. [ ] Read F3 value from Dashboard V3
3. [ ] Query BigQuery for DNO-specific metrics
4. [ ] Write to F10:L10
5. [ ] Test with all 14 DNOs
6. [ ] Add to cron for auto-refresh

---

**Option B: Use Native Google Sheets Formulas**

Replace Python-calculated KPIs with Sheets formulas that reference F3:

```
F10: =QUERY(DNO_Map, "SELECT G WHERE B='"&F3&"'", 0)  // Net Margin for selected DNO
G10: =QUERY(DNO_Map, "SELECT F WHERE B='"&F3&"'", 0)  // Volume
H10: =QUERY(DNO_Map, "SELECT H WHERE B='"&F3&"'", 0)  // Revenue
```

**Pros:**
- Truly real-time - updates instantly when F3 changes
- No Python or Apps Script needed
- Native Sheets functionality

**Cons:**
- Limited to data already in DNO_Map sheet
- Can't query BigQuery directly for complex metrics
- May need to pre-calculate more columns in DNO_Map

**TODO:**
1. [ ] Expand DNO_Map with all needed KPI columns
2. [ ] Write QUERY formulas in F10:L10
3. [ ] Test formula recalculation
4. [ ] Add data validation to ensure formulas don't get overwritten

---

### Phase 2: Populate DNO_Map with Complete Data (4 hours)

Currently DNO_Map has: Code, Name, Lat, Lng, Net Margin, Total MWh, PPA Revenue

**Need to add:**
- VLP Revenue (£k)
- Wholesale Avg (£/MWh)
- Market Vol (%)
- All-GB Net Margin
- DUoS rates (Red/Amber/Green)

**TODO:**
1. [ ] Create `python/populate_dno_map_complete.py`
2. [ ] Query BigQuery for each DNO:
   - VLP revenue from `bmrs_boalf` + `bmrs_indgen`
   - Wholesale prices from `bmrs_mid`
   - Market volume from generation data
   - DUoS rates from `gb_power.duos_unit_rates`
3. [ ] Calculate net margins per DNO
4. [ ] Write to DNO_Map sheet (append columns I-N)
5. [ ] Test with sample DNO
6. [ ] Run for all 14 DNOs

---

### Phase 3: Auto-Refresh System (2 hours)

**TODO:**
1. [ ] Create `python/dashboard_v3_auto_refresh.py`
2. [ ] Combines:
   - `populate_dno_map_complete.py` (refresh DNO data)
   - `update_dashboard_v3_kpis.py` (update selected DNO KPIs)
   - Chart updates
3. [ ] Add to cron: `*/15 * * * *` (every 15 minutes)
4. [ ] Add logging to `logs/dashboard_v3_refresh.log`
5. [ ] Test full cycle

---

### Phase 4: Fix Apps Script (If Time Permits - 4+ hours)

**Only attempt if Phases 1-3 are complete and working**

Potential solutions:
1. **Recreate Apps Script manually in browser**
   - Delete current project
   - Extensions → Apps Script (creates new)
   - Copy/paste code directly
   - May fix authorization/sandbox issues

2. **Use Web App instead of Sidebar**
   - Deploy as web app: `doGet()` function
   - Embed IFRAME in sheet
   - May have different security context

3. **Contact Google Support**
   - Apps Script "server error" with no stack trace is rare
   - May be platform bug or account-specific issue

**TODO (Low Priority):**
1. [ ] Try recreating Apps Script from scratch in browser
2. [ ] Test web app deployment alternative
3. [ ] If still failing, move on - Python solution is sufficient

---

## Timeline & Priorities

### Day 1 (Today - 8 hours)
- ✅ Hour 1-2: Create `populate_dno_map_complete.py`
- ✅ Hour 3-4: Test and verify DNO_Map has all columns
- ✅ Hour 5-6: Create `update_dashboard_v3_kpis.py`
- ✅ Hour 7-8: Test full dashboard update cycle

### Day 2 (Tomorrow - 4 hours)
- ✅ Hour 1-2: Write Sheets formulas (Option B)
- ✅ Hour 3-4: Set up auto-refresh cron job
- ✅ Final test: Change F3, verify KPIs update

### Day 3+ (Optional)
- Apps Script debugging (only if needed)

---

## Current File Status

### Working Files ✅
```
/Users/georgemajor/GB-Power-Market-JJ/
├── Code.gs                          # Root copy (for reference)
├── appsscript_v3/
│   ├── Code.js                      # Deployed version (working in isolation)
│   ├── DnoMap.html                  # Map version (fails from HTML)
│   ├── DnoMapSimple.html           # List version (also fails)
│   └── appsscript.json              # Manifest with OAuth scopes
├── python/
│   ├── rebuild_dashboard_v3_final.py       # Creates Dashboard V3 sheet ✅
│   ├── populate_dashboard_tables.py        # Populates Chart Data ✅
│   └── (need to create new scripts below)
└── .clasp.json                      # Script ID: 1KlgBiFBGXfub87A...
```

### Files to Create 📝
```
python/
├── populate_dno_map_complete.py     # Adds all KPI columns to DNO_Map
├── update_dashboard_v3_kpis.py      # Updates F10:L10 based on F3
└── dashboard_v3_auto_refresh.py     # Combines both + scheduling
```

---

## Key Learnings

1. **Apps Script HTML Service has undocumented limitations**
   - `google.script.run` can fail silently with "server error"
   - Even with correct OAuth scopes
   - Even when backend function works perfectly
   - No useful error messages or stack traces

2. **Python → Sheets is more reliable than Apps Script**
   - Direct control via Sheets API
   - Better error messages
   - No sandbox restrictions
   - Proven to work in this project

3. **Don't rely on Apps Script for critical functionality**
   - Good for: Simple menus, UI helpers, formatting
   - Bad for: Data processing, external API calls, complex logic
   - Use Python for anything important

---

## Success Criteria

Dashboard V3 is **LIVE** when:

1. ✅ User can select DNO from F3 dropdown
2. ✅ KPIs in F10:L10 update to show selected DNO's metrics
3. ✅ Charts update to show selected DNO's data
4. ✅ Updates happen within 15 minutes (auto-refresh)
5. ✅ All 14 DNOs work correctly

**We DO NOT need the map selector** - the dropdown is sufficient!

---

## Next Steps (Start Immediately)

1. **Create `populate_dno_map_complete.py`** - Expand DNO_Map with all KPI columns
2. **Test script** - Run for 2-3 DNOs first
3. **Create `update_dashboard_v3_kpis.py`** - Update F10:L10 based on F3
4. **Test manual refresh** - Change F3, run script, verify KPIs update
5. **Set up cron job** - Auto-refresh every 15 minutes
6. **DONE** - Dashboard V3 is live without Apps Script

---

**Bottom Line:** Stop fighting Apps Script. Use Python. Get it working today.
