# 🔍 Search Interface - Quick Start Guide

## ✅ What's Complete (Stages 1 & 2)

1. **✅ Search Sheet Created** - 11-column results table, party details panel
2. **✅ Dropdowns Populated** - 2,718 BMU IDs, 351 organizations, CUSC roles
3. **✅ Python Script Executed** - `create_search_interface.py` ran successfully
4. **✅ Apps Script Ready** - `search_interface.gs` ready for installation

---

## 🚀 Install Apps Script (5 minutes)

### Step 1: Open Spreadsheet
https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

### Step 2: Open Apps Script
**Extensions > Apps Script**

### Step 3: Paste Code
1. Delete existing code in `Code.gs`
2. Copy **all** of `search_interface.gs`
3. Paste into editor
4. **Save** (Ctrl+S)

### Step 4: Refresh
1. Close Apps Script tab
2. Reload spreadsheet
3. See new menu: **🔍 Search Tools**

---

## 🎯 Test Your First Search (3 minutes)

### Example: Find Drax Assets

1. **Go to Search sheet**

2. **Fill in criteria** (Row 5):
   ```
   Party/Name Search: Drax
   Search Mode: OR
   ```

3. **Click menu**: 🔍 Search Tools > 🔍 Run Search

4. **Copy command from dialog**:
   ```bash
   python3 advanced_search_tool_enhanced.py --party "Drax"
   ```

5. **Run in terminal** (from `/home/george/GB-Power-Market-JJ`)

6. **See results** populate in rows 22+

---

## 📋 Search Criteria Reference

| Row | Field | Options | Example |
|-----|-------|---------|---------|
| **4** | Date Range | DD/MM/YYYY | 01/01/2025 to 31/12/2025 |
| **5** | Party/Name | Text search | Drax, EDF, Flexgen |
| **6** | Record Type | None, All, BSC Party, BM Unit, TEC Project | BM Unit |
| **7** | CUSC/BSC Role | VLP, VTP, Supplier, Embedded Power Station | Virtual Lead Party (VLP) |
| **8** | Fuel/Tech Type | Battery, Wind, Solar, Gas (multi-select) | Battery Storage, Solar |
| **9** | BM Unit ID | None, All, E_FARNB-1, E_HAWKB-1... | E_FARNB-1 |
| **10** | Organization | None, All, Drax, EDF, SSE... | Drax Power Limited |
| **11** | Capacity Range | Min to Max (MW) | 50 to 500 |
| **12** | TEC Project | Text search | Lower 48 BESS |
| **13** | Connection Site | None, All, Beauly, Drax, Grain... | Drax |
| **14** | Project Status | None, All, Active, Energised... | Energised |

---

## 🎨 11-Column Results Table

| Col | Header | Example |
|-----|--------|---------|
| **A** | Record Type | BSC Party, BM Unit, TEC Project |
| **B** | Identifier | P1234, E_FARNB-1, a0l4L0000005iPb |
| **C** | Name | EDF Trading Ltd, Farnborough BESS |
| **D** | Role | Virtual Lead Party (VLP) ⭐ NEW |
| **E** | Organization | Drax Power Limited ⭐ NEW |
| **F** | Extra Info | Qualified Person, Connection site |
| **G** | Capacity (MW) | 50, 660, 1200 |
| **H** | Fuel Type | Battery, Wind, Gas |
| **I** | Status | Active, Energised |
| **J** | Dataset Source | ELEXON, NESO, TEC |
| **K** | Match Score | 85, 92, 100 |

---

## 🎯 Example Searches

### 1. VLP Batteries
```
CUSC/BSC Role: Virtual Lead Party (VLP)
Fuel/Tech Type: Battery Storage
Search Mode: AND
```
**Expected**: Flexgen, Harmony Energy, Zenobe

### 2. Large Wind Farms
```
Fuel/Tech Type: Offshore Wind, Onshore Wind
Capacity Min: 100
Search Mode: OR
```
**Expected**: Dogger Bank, Hornsea, East Anglia

### 3. Specific BMU
```
BM Unit ID: E_FARNB-1
```
**Expected**: 1 result (Farnborough BESS, 50 MW, Flexgen)

---

## 📋 Party Details Panel (Columns L-M)

**How to use**:
1. Click any result row (row 22+)
2. Menu: 🔍 Search Tools > 📋 View Party Details
3. Panel populates with:
   - Party ID, Record Type, Role, Organization
   - BSC Roles, VLP/VTP status
   - Assets owned, total capacity
   - Last updated timestamp

---

## 🔑 CUSC/BSC Roles (Based on CUSC Section 1)

```
✅ Power Station (Directly Connected)
✅ Large Power Station
✅ Non-Embedded Customer
✅ Distribution System (DNO/IDNO)
✅ Supplier
✅ Embedded Power Station
✅ Embedded Exemptable Large Power Station
✅ Small Power Station Trading Party
✅ Virtual Lead Party (VLP) ⭐
✅ Virtual Trading Party (VTP) ⭐
✅ Interconnector User
```

---

## 🆘 Troubleshooting

**Menu not appearing?**
→ Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R)

**Dropdown shows "Loading..."?**
→ Re-run: `python3 create_search_interface.py`

**No results after search?**
→ Check terminal output for errors
→ Try simpler query: Party Name = "Drax"

**Party details not populating?**
→ Ensure row 22+ selected
→ Check Apps Script authorization

---

## 📁 Key Files

| File | Purpose | Status |
|------|---------|--------|
| **SEARCH_SHEET_ENHANCEMENT_TODOS.md** | Master todo list (20 tasks) | ✅ Complete |
| **create_search_interface.py** | Sheet creation script | ✅ Executed |
| **search_interface.gs** | Apps Script buttons | ⏳ Ready to install |
| **SEARCH_INTERFACE_IMPLEMENTATION_COMPLETE.md** | Full documentation | ✅ Complete |

---

## 📊 What Got Loaded

- ✅ **2,718 BMU IDs** (E_FARNB-1, E_HAWKB-1, etc.)
- ✅ **351 Organizations** (Drax, EDF, SSE, etc.)
- ✅ **21 Fuel Types** (Battery, Wind, Solar, Gas, etc.)
- ✅ **26 Connection Sites** (Beauly, Drax, Grain, etc.)
- ✅ **11 CUSC Roles** (VLP, VTP, Supplier, etc.)
- ✅ **9 Project Statuses** (Active, Energised, etc.)

**All dropdowns**: "None", "All" at top, rest alphabetically sorted ✅

---

## 🎉 Next Steps

1. **⏳ Install Apps Script** (5 min) - Follow steps above
2. **⏳ Test Search** (3 min) - Try "Drax" search
3. **⏳ Test Party Details** (2 min) - Click result row
4. **📋 Advanced Features** (Later):
   - TEC search integration
   - Real-time BigQuery lookup
   - Export to CSV
   - Search history

---

**Sheet URL**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

**Questions?** See: `SEARCH_INTERFACE_IMPLEMENTATION_COMPLETE.md` (full docs)

---

*Created: December 31, 2025 | GB Power Market JJ Project*
