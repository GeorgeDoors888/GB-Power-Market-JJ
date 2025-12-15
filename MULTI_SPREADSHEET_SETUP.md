# 🎯 Multi-Spreadsheet Apps Script - Complete Setup

## ✅ Problem Solved!

You have **TWO spreadsheets**, and the Code.gs now **automatically detects** which one it's in and shows the appropriate menus!

## 📊 Your Two Spreadsheets

### 1. **BtM Spreadsheet** (Main - Sparklines)
```
ID: 1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I
URL: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/
Title: BtM
```

**Key Sheets:**
- `GB Live` - Real-time generation dashboard
- `Data_Hidden` - 20 rows × 24 cols of sparkline data
- `BESS` - Battery storage analysis (yes, it has one too!)
- `BtM` - Battery site info
- `DNO` - DNO map display

**Menus Available:**
- ✅ 🗺️ DNO Map (3 functions)
- ✅ 🔋 BESS Tools (4 functions)
- ✅ ⚡ GB Live Dashboard (4 sparkline functions) **← ONLY HERE**
- ✅ 🔧 Diagnostics (2 functions)

---

### 2. **GB Energy Dashboard** (Secondary - Primary BESS)
```
ID: 12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
URL: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
Title: GB Energy Dashboard
```

**Key Sheets:**
- `BESS` - Primary battery storage analysis
- `HH Data` - Half-hourly demand profiles
- `Dashboard` - Main energy dashboard
- `DNO` - DNO info
- 60+ other analysis sheets

**Menus Available:**
- ✅ 🗺️ DNO Map (3 functions)
- ✅ 🔋 BESS Tools (4 functions)
- ❌ ⚡ GB Live Dashboard (not available - no GB Live/Data_Hidden sheets)
- ✅ 🔧 Diagnostics (2 functions)

---

## 🚀 Updated Code.gs Features

**File:** `/home/george/GB-Power-Market-JJ/Code.gs`  
**Lines:** 1,256 (updated from 829)  
**Functions:** 19 total

### Smart Detection System

```javascript
function onOpen() {
  var ssId = SpreadsheetApp.getActiveSpreadsheet().getId();
  
  // Automatically detects which spreadsheet
  var isBtMSpreadsheet = (ssId === '1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I');
  
  // Shows appropriate menus for each spreadsheet
  if (isBtMSpreadsheet) {
    // Add sparkline menu (only for BtM)
  }
  // Always add DNO Map and BESS Tools (both have these features)
}
```

### Complete Function List

#### 🗺️ DNO Map (3 functions - both spreadsheets)
1. `createDNOMap()` - Interactive UK DNO boundaries
2. `createDNOMapWithSites()` - Map with battery site markers
3. `embedMapInSheet()` - Embed map in DNO sheet

#### 🔋 BESS Tools (6 functions - both spreadsheets)
4. `generateHHDataDirect()` - Generate 17,520 HH demand rows
5. `manualRefreshDno()` - Postcode → DNO lookup
6. `coordinatesToMpan()` - Lat/lng → MPAN ID mapping
7. `calculatePPAAnalysis()` - Battery arbitrage analysis
8. `showHHDataStatus()` - Validate HH Data sheet
9. `onEdit()` - Auto-trigger on A6/B6 edits

#### ⚡ GB Live Dashboard (6 functions - BtM only!)
10. `writeSparklines()` - Write 20 cross-sheet sparkline formulas
11. `writeFuelSparklines()` - Column C fuel sparklines
12. `writeInterconnectorSparklines()` - Column F IC sparklines
13. `verifyDataHidden()` - Check Data_Hidden content
14. `clearSparklines()` - Remove all sparklines
15. `quickHealthCheck()` - Quick status popup

#### 🔧 Diagnostics (4 functions - both spreadsheets)
16. `diagnostics()` - Comprehensive environment check
17. `checkSheetDiagnostic()` - Sheet existence validator
18. `showSpreadsheetInfo()` - Display spreadsheet type
19. *Additional constants: FUEL_SPARKLINES, IC_SPARKLINES*

---

## 📋 Deployment Instructions

### Step 1: Deploy to BtM Spreadsheet (Primary - Has Sparklines)

```
1. Open: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/

2. Go to: Extensions → Apps Script

3. Delete ALL existing code

4. Copy ENTIRE file:
   /home/george/GB-Power-Market-JJ/Code.gs

5. Paste into Apps Script editor

6. Save (Ctrl+S)

7. Deploy:
   - Deploy → New deployment
   - Type: Web app
   - Description: "Multi-spreadsheet v5"
   - Execute as: Me
   - Who has access: Anyone
   - Click: Deploy
   - Copy deployment ID

8. Close Apps Script, refresh spreadsheet (F5)

9. Check menus appear:
   ✅ 🗺️ DNO Map
   ✅ 🔋 BESS Tools
   ✅ ⚡ GB Live Dashboard ← Should appear!
   ✅ 🔧 Diagnostics
```

### Step 2: Deploy to GB Energy Dashboard (Secondary - No Sparklines)

```
1. Open: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/

2. Go to: Extensions → Apps Script

3. Delete ALL existing code

4. Copy SAME file:
   /home/george/GB-Power-Market-JJ/Code.gs

5. Paste into Apps Script editor

6. Save (Ctrl+S)

7. Deploy (same as above)

8. Close Apps Script, refresh spreadsheet (F5)

9. Check menus appear:
   ✅ 🗺️ DNO Map
   ✅ 🔋 BESS Tools
   ❌ ⚡ GB Live Dashboard ← Should NOT appear (correct!)
   ✅ 🔧 Diagnostics
```

---

## 🧪 Testing Checklist

### Test in BtM Spreadsheet

**DNO Map:**
- [ ] Open spreadsheet: 1MSl8fJ0...
- [ ] Check menu exists: 🗺️ DNO Map
- [ ] Click "View Interactive Map" - UK boundaries appear
- [ ] Enter postcode in BtM sheet A6 or BESS sheet A6
- [ ] Click "View Map with Site Markers" - red marker appears

**BESS Tools:**
- [ ] Check menu exists: 🔋 BESS Tools
- [ ] Go to BESS sheet
- [ ] Enter postcode in A6 (e.g., "SW1A 1AA")
- [ ] Click "Refresh DNO Data" - status appears in A4
- [ ] Enter values in B17-B19 (Min/Avg/Max kW)
- [ ] Click "Generate HH Data" - shows webhook or command

**Sparklines (BtM ONLY!):**
- [ ] Check menu exists: ⚡ GB Live Dashboard ✅ SHOULD APPEAR
- [ ] Go to GB Live sheet
- [ ] Run Python first: `python3 update_bg_live_dashboard.py`
- [ ] Click "Write Sparkline Formulas"
- [ ] Check columns C11-C20 and F11-F20 - charts appear
- [ ] Click "Health Check" - popup shows status

**Diagnostics:**
- [ ] Check menu exists: 🔧 Diagnostics
- [ ] Click "Show Spreadsheet Info" - shows "BtM Spreadsheet"
- [ ] Click "Run Full Diagnostics" - check Executions log

---

### Test in GB Energy Dashboard

**DNO Map:**
- [ ] Open spreadsheet: 12jY0d4j...
- [ ] Check menu exists: 🗺️ DNO Map
- [ ] All 3 functions work identically

**BESS Tools:**
- [ ] Check menu exists: 🔋 BESS Tools
- [ ] All 4 functions work identically
- [ ] BESS sheet is primary here (more comprehensive)

**Sparklines:**
- [ ] Check menu: ⚡ GB Live Dashboard ❌ SHOULD NOT APPEAR
- [ ] This is correct! GB Energy Dashboard doesn't have GB Live/Data_Hidden sheets

**Diagnostics:**
- [ ] Check menu exists: 🔧 Diagnostics
- [ ] Click "Show Spreadsheet Info" - shows "GB Energy Dashboard"
- [ ] Click "Run Full Diagnostics" - notes missing GB Live/Data_Hidden

---

## 🐛 Troubleshooting

### Issue: "Menu doesn't appear"
**Cause:** Code not saved or spreadsheet not refreshed  
**Fix:**
1. Save in Apps Script (Ctrl+S)
2. Refresh spreadsheet (F5)
3. Wait 5-10 seconds for menus to load

### Issue: "Wrong menus showing"
**Cause:** Copied to wrong spreadsheet or old deployment active  
**Fix:**
1. Check spreadsheet ID matches
2. Run: 🔧 Diagnostics → Show Spreadsheet Info
3. Verify spreadsheet type detected correctly

### Issue: "Sparkline menu missing in BtM"
**Cause:** GB Live or Data_Hidden sheet not found  
**Fix:**
1. Run diagnostics to check sheets
2. Verify sheets named exactly: "GB Live" and "Data_Hidden"
3. Re-save Code.gs and refresh

### Issue: "Sparkline menu showing in GB Energy Dashboard"
**Cause:** Shouldn't happen with smart detection  
**Fix:**
1. Run: 🔧 Diagnostics → Show Spreadsheet Info
2. Check spreadsheet ID detection logic
3. Re-deploy with correct Code.gs

### Issue: "Functions fail with errors"
**Cause:** Missing sheets or Python webhooks down  
**Fix:**
1. Run full diagnostics
2. Check execution log for errors
3. Most functions show manual commands if webhooks unavailable

---

## 📊 Menu Structure Reference

### BtM Spreadsheet (1MSl8fJ0...)
```
🗺️ DNO Map
├─ View Interactive Map
├─ View Map with Site Markers
└─ Embed Map in DNO Sheet

🔋 BESS Tools
├─ 📊 Generate HH Data
├─ ───────────
├─ 🔄 Refresh DNO Data
├─ ───────────
├─ 💰 Calculate PPA Analysis
├─ ───────────
└─ 📈 Show HH Data Status

⚡ GB Live Dashboard  ← ONLY IN BtM!
├─ ✨ Write Sparkline Formulas
├─ 🔍 Verify Data_Hidden
├─ 🗑️ Clear Sparklines
├─ ───────────
└─ 🏥 Health Check

🔧 Diagnostics
├─ Run Full Diagnostics
└─ Show Spreadsheet Info
```

### GB Energy Dashboard (12jY0d4j...)
```
🗺️ DNO Map
├─ View Interactive Map
├─ View Map with Site Markers
└─ Embed Map in DNO Sheet

🔋 BESS Tools
├─ 📊 Generate HH Data
├─ ───────────
├─ 🔄 Refresh DNO Data
├─ ───────────
├─ 💰 Calculate PPA Analysis
├─ ───────────
└─ 📈 Show HH Data Status

🔧 Diagnostics
├─ Run Full Diagnostics
└─ Show Spreadsheet Info

(No ⚡ GB Live Dashboard - correct!)
```

---

## 🎯 Key Differences

| Feature | BtM Spreadsheet | GB Energy Dashboard |
|---------|----------------|---------------------|
| **Sparklines** | ✅ Yes (GB Live + Data_Hidden) | ❌ No (sheets missing) |
| **BESS Tools** | ✅ Yes | ✅ Yes (primary) |
| **DNO Map** | ✅ Yes | ✅ Yes |
| **Diagnostics** | ✅ Yes | ✅ Yes |
| **HH Data** | ⚠️ Can generate | ✅ Primary location |
| **Purpose** | Real-time dashboard + sparklines | Comprehensive BESS analysis |

---

## 📝 Python Integration

Both spreadsheets can trigger Python scripts:

### For Sparklines (BtM only):
```bash
cd ~/GB-Power-Market-JJ
python3 update_bg_live_dashboard.py
```
Updates Data_Hidden sheet every 5 minutes (cron job)

### For BESS Tools (both):
```bash
# DNO Lookup
python3 dno_lookup_python.py 12 LV

# HH Data Generation
python3 generate_hh_profile.py

# PPA Analysis
python3 calculate_btm_ppa_analysis.py
```

### Webhook Server (optional):
```bash
python3 dno_webhook_server.py
```
Enables Apps Script to call Python directly

---

## 🔐 Permissions

When first running, Apps Script will request:
- ✅ View and manage spreadsheets
- ✅ Connect to external services (postcodes.io, GitHub)
- ✅ Display content in UI
- ✅ Access Google Drive (for map embedding)

Click "Review Permissions" → Select account → Allow

---

## 📁 File Locations

### Main Deployment
```
/home/george/GB-Power-Market-JJ/Code.gs (1,256 lines)
```
**Deploy to BOTH spreadsheets** - auto-detects which one it's in!

### Supporting Files
```
/home/george/GB-Power-Market-JJ/
├── Code.gs                          # Multi-spreadsheet version
├── bg-sparklines-clasp/Code.gs      # Separate sparklines version (obsolete)
├── MULTI_SPREADSHEET_SETUP.md       # This file
├── APPS_SCRIPT_INTEGRATED.md        # Previous integration guide
├── QUICK_REFERENCE.txt              # Quick reference card
└── gb_power_map_deployment/
    └── dno_regions.geojson          # UK DNO boundaries
```

---

## ✅ Success Criteria

### BtM Spreadsheet:
- ✅ 4 menus appear (DNO Map, BESS Tools, GB Live Dashboard, Diagnostics)
- ✅ Sparklines write successfully to GB Live
- ✅ DNO lookup works from BESS sheet
- ✅ Diagnostics show "BtM Spreadsheet"

### GB Energy Dashboard:
- ✅ 3 menus appear (DNO Map, BESS Tools, Diagnostics)
- ✅ NO sparkline menu (correct - sheets missing)
- ✅ DNO lookup works from BESS sheet
- ✅ Diagnostics show "GB Energy Dashboard"

---

**Status:** ✅ Ready for deployment  
**Version:** 5 (Multi-spreadsheet)  
**Last Updated:** 8 Dec 2025, 23:30  
**Maintainer:** George Major (george@upowerenergy.uk)
