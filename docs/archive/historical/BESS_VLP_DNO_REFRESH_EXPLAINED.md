# BESS VLP - DNO Data & Refresh Explained

**Date**: November 9, 2025  
**Topic**: DNO duplicates question & refresh mechanism

---

## ❓ Your Questions Answered

### Q1: "The DNOs are duplicated"

**Answer**: They're NOT duplicated - there are exactly 14 unique DNOs! ✅

Here's the complete list from BigQuery:

```
MPAN 10: UKPN-EPN             - UK Power Networks (Eastern)
MPAN 11: NGED-EM              - National Grid Electricity Distribution – East Midlands
MPAN 12: UKPN-LPN             - UK Power Networks (London)
MPAN 13: SP-Manweb            - SP Energy Networks (SPM)
MPAN 14: NGED-WM              - National Grid Electricity Distribution – West Midlands
MPAN 15: NPg-NE               - Northern Powergrid (North East)
MPAN 16: ENWL                 - Electricity North West
MPAN 17: SSE-SHEPD            - Scottish Hydro Electric Power Distribution (SHEPD)
MPAN 18: SP-Distribution      - SP Energy Networks (SPD)
MPAN 19: UKPN-SPN             - UK Power Networks (South Eastern)
MPAN 20: SSE-SEPD             - Southern Electric Power Distribution (SEPD)
MPAN 21: NGED-SWales          - National Grid Electricity Distribution – South Wales
MPAN 22: NGED-SW              - National Grid Electricity Distribution – South West
MPAN 23: NPg-Y                - Northern Powergrid (Yorkshire)
```

**Why it might look duplicated**:
- **UKPN has 3 separate license areas**: Eastern (10), London (12), South Eastern (19)
- **NGED has 4 separate license areas**: East Midlands (11), West Midlands (14), South Wales (21), South West (22)
- **SP Energy has 2 separate licenses**: Manweb (13), Distribution (18)
- **Northern Powergrid has 2**: North East (15), Yorkshire (23)
- **SSE has 2**: SHEPD Scotland (17), SEPD Southern (20)

These are **separate network operators** with different MPAN IDs, GSP groups, and geographic areas - not duplicates!

---

### Q2: "How does it refresh?"

**Answer**: Three ways to refresh DNO data:

## 🔄 Refresh Methods

### Method 1: Manual Refresh (Apps Script Menu)
**When**: Whenever you want to update DNO data from BigQuery

**Steps**:
1. Open BESS_VLP sheet
2. Menu: **🔋 BESS VLP Tools** → **Refresh DNO Reference Table**
3. Wait ~5 seconds (queries BigQuery)
4. Success message appears

**What it does**:
- ✅ Queries BigQuery `neso_dno_reference` table
- ✅ Updates hidden reference table (rows 24-50)
- ✅ Rebuilds DNO dropdown list in E4
- ✅ Keeps data synchronized

**When to use**: If BigQuery data changes (rare - only when Ofgem updates licenses)

---

### Method 2: Python Script Re-run
**File**: `enhance_bess_vlp_sheet.py`

**When**: If you want to reset the entire sheet structure

**Command**:
```bash
cd "/Users/georgemajor/GB Power Market JJ"
/opt/homebrew/bin/python3 enhance_bess_vlp_sheet.py
```

**What it does**:
- ✅ Recreates entire sheet structure
- ✅ Fetches all 14 DNOs from BigQuery
- ✅ Rebuilds dropdown validation
- ✅ Reapplies formatting
- ✅ Re-hides reference table

**When to use**: If sheet gets corrupted or you want to start fresh

---

### Method 3: Automatic (Future Enhancement)
**Not yet implemented**, but could add:
- Cron job to check BigQuery daily
- Automatic refresh if data changes detected
- Email notification of updates

---

## 📊 Where DNO Data Lives

### Source: BigQuery Table
```
Project: inner-cinema-476211-u9
Dataset: uk_energy_prod
Table: neso_dno_reference
Location: US region
Rows: 14 (one per DNO)
```

### Used In 3 Places:

1. **Hidden Reference Table** (Rows 24-37)
   - All 14 DNOs with full details
   - Hidden by default (rows 21-50)
   - Used by Apps Script for lookups
   - Can unhide: Menu → Show/Hide Reference Table

2. **DNO Dropdown** (Cell E4)
   - Data validation list
   - Format: "10 - UK Power Networks (Eastern)"
   - Built from reference table
   - Automatically updates when you refresh

3. **Apps Script Memory** (Function `findDNOByMPAN`)
   - Queries BigQuery directly for current lookup
   - Always gets latest data
   - Independent of reference table

---

## 🔧 New Menu Options

Updated menu with 3 options:

### 🔋 BESS VLP Tools Menu

1. **Lookup DNO from Postcode/Dropdown**
   - Main lookup function
   - Uses postcode (B4) OR dropdown (E4)
   - Populates results + map

2. **Refresh DNO Reference Table**
   - Updates DNO data from BigQuery
   - Rebuilds dropdown list
   - Takes ~5 seconds
   - Shows success message with count

3. **Show/Hide Reference Table** ← NEW
   - Toggles visibility of rows 21-50
   - Quick access to see full DNO data
   - Doesn't affect functionality

---

## 🎯 Dropdown List Contents

All 14 entries in dropdown (E4):

```
10 - UK Power Networks (Eastern)
11 - National Grid Electricity Distribution – East Midlands (EMID)
12 - UK Power Networks (London)
13 - SP Energy Networks (SPM)
14 - National Grid Electricity Distribution – West Midlands (WMID)
15 - Northern Powergrid (North East)
16 - Electricity North West
17 - Scottish Hydro Electric Power Distribution (SHEPD)
18 - SP Energy Networks (SPD)
19 - UK Power Networks (South Eastern)
20 - Southern Electric Power Distribution (SEPD)
21 - National Grid Electricity Distribution – South Wales (SWALES)
22 - National Grid Electricity Distribution – South West (SWEST)
23 - Northern Powergrid (Yorkshire)
```

**NO DUPLICATES** - Each MPAN ID is unique! ✅

---

## 🏢 Understanding Multi-License Companies

Some companies operate multiple DNO licenses:

### UK Power Networks (UKPN)
- **3 separate licenses**
- MPAN 10: Eastern (Norfolk, Suffolk, Essex, etc.)
- MPAN 12: London (Greater London)
- MPAN 19: South Eastern (Kent, Surrey, Sussex)
- **Why**: Different geographic areas acquired over time

### National Grid Electricity Distribution (NGED)
- **4 separate licenses**
- MPAN 11: East Midlands
- MPAN 14: West Midlands
- MPAN 21: South Wales
- MPAN 22: South West
- **Why**: Regional network operators, different pricing zones

### SP Energy Networks
- **2 separate licenses**
- MPAN 13: Manweb (Merseyside, North Wales)
- MPAN 18: Distribution (Central/South Scotland)
- **Why**: Different regulatory entities

### Northern Powergrid
- **2 separate licenses**
- MPAN 15: North East
- MPAN 23: Yorkshire
- **Why**: Historic regional divisions

### SSE (Scottish & Southern Energy)
- **2 separate licenses**
- MPAN 17: SHEPD (North Scotland)
- MPAN 20: SEPD (Southern England)
- **Why**: Geographic separation

---

## 📈 When Does DNO Data Change?

**Very rarely!** Only when:

1. **License Transfer** (e.g., company acquisition)
   - Last major change: 2016 (Western Power became SSEN)
   - Frequency: Once every 5-10 years

2. **Regulatory Changes** (e.g., boundary adjustments)
   - Very uncommon
   - Ofgem approval required

3. **GSP Group Updates** (e.g., new GSP added)
   - More common but minor
   - Doesn't affect MPAN IDs

**Bottom line**: You'll probably never need to refresh! But the option is there if Ofgem makes changes.

---

## 🧪 Testing Refresh Function

### Test Steps:

1. **Before Refresh**:
   - Note current dropdown list
   - Check hidden rows 24-37 (unhide if needed)

2. **Run Refresh**:
   - Menu: 🔋 BESS VLP Tools → Refresh DNO Reference Table
   - Wait for "Refreshing..." alert
   - Wait ~5 seconds
   - See "Success!" alert showing 14 DNOs updated

3. **After Refresh**:
   - Dropdown list should have same 14 entries
   - Reference table rows 24-37 updated
   - Timestamp in alert shows when refreshed

4. **Test Lookup**:
   - Select any DNO from dropdown
   - Run lookup
   - Should work identically

---

## 💡 Pro Tips

### Viewing Reference Table
```
Method 1: Menu → Show/Hide Reference Table
Method 2: Right-click rows 20 & 23 → Unhide rows
Method 3: Select rows 20-50 → Format → Unhide
```

### Dropdown Not Working?
```
1. Menu → Refresh DNO Reference Table
2. Check E4 has data validation (red triangle in corner)
3. If missing, run enhance_bess_vlp_sheet.py again
```

### Need to See All DNO Details?
```
1. Unhide reference table (rows 24-37)
2. All 8 columns visible:
   - MPAN, DNO Key, Full Name, Short Code
   - Participant ID, GSP Group, GSP Name, Coverage
3. Can copy/paste to other sheets
```

---

## 📊 Data Flow Diagram

```
BigQuery neso_dno_reference (14 rows)
         ↓
         ↓ (Manual: Refresh button OR Python script)
         ↓
Google Sheet Hidden Table (Rows 24-37)
         ↓
         ↓ (Auto-generated from table)
         ↓
Dropdown Validation (E4)
         ↓
         ↓ (User selects)
         ↓
Apps Script findDNOByMPAN()
         ↓
         ↓ (Queries BigQuery directly)
         ↓
Results Populated (Row 10)
```

**Key insight**: Dropdown uses cached data, but actual lookup queries BigQuery fresh each time!

---

## ✅ Summary

**DNO Duplication**: ❌ FALSE
- All 14 DNOs are unique
- Some companies have multiple licenses
- Each MPAN ID is different

**Refresh Options**: ✅ Three methods
1. Apps Script menu (manual, ~5 sec)
2. Python script (full rebuild, ~10 sec)
3. Automatic (not yet implemented)

**Refresh Frequency**: 🟢 Very Rare
- Only if Ofgem changes licenses
- Maybe once every 5-10 years
- Built-in option for future-proofing

**All Working**: ✅ YES
- Dropdown has all 14 DNOs
- Refresh function works
- Reference table correctly hidden
- Lookups work by postcode OR dropdown

---

**Need to refresh?** Menu → 🔋 BESS VLP Tools → Refresh DNO Reference Table  
**Need to see data?** Menu → 🔋 BESS VLP Tools → Show/Hide Reference Table

---

*Updated: November 9, 2025 21:20 GMT*  
*All 14 DNOs confirmed unique and correct*
