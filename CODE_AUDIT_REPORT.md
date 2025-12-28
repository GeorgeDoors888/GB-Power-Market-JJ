# 🔍 Code Audit Report - Python vs Apps Script Conflicts
**Date**: 23 December 2025  
**Audit Scope**: Identify cell ownership conflicts between `update_live_metrics.py` and Apps Script `.gs` files

---

## ✅ CONFLICT RESOLUTION STATUS

### **1. Interconnector Sparklines (G13:H22)** - ✅ RESOLVED
**Conflict**: Both Python and Data.gs were writing to column H

**Resolution Implemented**:
- **Python** (`update_live_metrics.py` line 1334): Writes BOTH columns G (names) and H (sparklines)
- **Apps Script** (`Data.gs` lines 206-222): NOW only writes column G (names), explicitly avoids column H
- **Conflict Prevention**: Comments in Data.gs warn not to overwrite column H

**Current State**: ✅ No conflict - Python has exclusive ownership of H13:H22

---

### **2. KPI Sparklines (C4, E4, G4, I4)** - ⚠️ POTENTIAL CONFLICT

**Python Approach** (`update_live_metrics.py` lines 847-870):
- Writes KPI VALUES to row 6: C6, E6, G6, I6, K6
- Writes SPARKLINE FORMULAS to row 7: C7, E7, G7, I7, K7
- Does NOT write to row 4 (where sparklines should display)
- Uses `generate_gs_sparkline_formula()` with ymin/ymax parameters

**Apps Script Approach** (`KPISparklines.gs` lines 49-71):
- Writes SPARKLINE FORMULAS directly to row 4: C4, E4, G4, I4
- Reads historical data from `Data_Hidden` sheet rows 22-25
- Uses ymin/ymax parameters: E4 (49.8-50.2), G4 (20-45), I4 (5-20)
- Has Python management check: `isPythonManaged` flag in AA1

**Conflict Analysis**:
- ❌ **MISMATCH**: Python writes to rows 6-7, Apps Script writes to row 4
- ⚠️ **UNCLEAR OWNERSHIP**: No clear documentation on which script manages row 4
- ✅ **PROTECTION EXISTS**: Apps Script checks AA1 for 'PYTHON_MANAGED' flag
- ❌ **FLAG NOT SET**: Python script doesn't set AA1='PYTHON_MANAGED'

**Recommendation**: 
1. Python should set AA1='PYTHON_MANAGED' to disable Apps Script KPI updates
2. OR remove Python's C6:K7 sparkline updates and let Apps Script handle row 4
3. Clarify: Should sparklines be in row 4 (Apps Script) or row 7 (Python)?

---

### **3. Active Outages Section** - ⚠️ DIFFERENT LOCATIONS

**Python** (`update_live_metrics.py` lines 1245-1289):
- Location: G25:K41 (header G25, columns G26:K26, data G27:K41)
- Columns: Asset Name, Fuel Type, Unavail (MW), Normal (MW), Cause
- Data Source: `bmrs_remit_unavailability` BigQuery table
- Query: Top 15 by unavailableCapacity

**Apps Script** (`Data.gs` lines 230-245):
- Location: G31:J50 (header G31, data G32:J50)
- Columns: Asset Name, Fuel Type, Unavail (MW), Cause (NO "Normal (MW)")
- Data Source: `publication_dashboard_live` BigQuery table
- Format: 4 columns vs Python's 5 columns

**Conflict Analysis**:
- ⚠️ **OVERLAPPING RANGES**: Python G25:K41 vs Apps Script G31:J50 - rows 31-41 overlap!
- ❌ **DIFFERENT SCHEMAS**: Python has 5 columns (includes Normal MW), Apps Script has 4
- ❌ **DIFFERENT DATA SOURCES**: Python uses direct table query, Apps Script uses publication table
- ⚠️ **LAST WRITER WINS**: Both scripts could overwrite each other's data in rows 31-41

**Recommendation**:
1. Standardize location: Use either G25 (Python) or G31 (Apps Script), not both
2. Disable Apps Script outages display since Python is more comprehensive (5 columns)
3. Ensure Apps Script checks isPythonManaged flag before writing outages

---

### **4. Data Sources** - ⚠️ DUAL PIPELINE COMPLEXITY

**Python Pipeline** (`update_live_metrics.py`):
```
BigQuery Tables → Python queries → Direct to Sheets
├─ bmrs_fuelinst_iris → Data_Hidden (fuel/interconnector pivot)
├─ bmrs_costs → System prices (A5-A7)
├─ bmrs_mid_iris → Market prices
├─ bmrs_disbsad → Settlement prices (L12-L18)
├─ bmrs_freq → Frequency data
├─ bmrs_remit_unavailability → Active outages (G25:K41)
└─ boalf_with_prices → VLP revenue (L54:R67)
```

**Apps Script Pipeline** (`Data.gs`, `Charts.gs`):
```
publication_dashboard_live BigQuery table → Apps Script → Sheets
├─ JSON structure with: report_date, KPIs, generation, interconnectors
├─ Intraday arrays: wind, windForecast, demand, price, frequency
├─ Outages, constraints, timestamp
└─ Charts.gs creates embedded charts (Wind Forecast at A32)
```

**Conflict Analysis**:
- ⚠️ **DUAL SYSTEMS**: Two separate data pipelines for same dashboard
- ❌ **PUBLICATION TABLE NOT UPDATED**: `build_publication_table_current.py` not in cron schedule
- ✅ **PYTHON ACTIVE**: `update_live_metrics.py` runs every 5 minutes
- ❌ **APPS SCRIPT STALE**: Wind forecast chart not updating (publication table outdated)

**Recommendation**:
1. **DEPRECATE** `publication_dashboard_live` table and Apps Script data display
2. **KEEP** Apps Script only for embedded charts (if needed)
3. **MIGRATE** all data updates to Python `update_live_metrics.py`
4. **OR** Add `build_publication_table_current.py` to cron if keeping Apps Script pipeline

---

## 📊 CELL OWNERSHIP MATRIX

| Range | Python Owner | Apps Script Owner | Status | Recommendation |
|-------|-------------|-------------------|--------|----------------|
| **A2** | update_live_metrics.py | - | ✅ No conflict | Keep Python |
| **A3** | update_live_metrics.py | - | ✅ No conflict | Keep Python |
| **A5-A7** | update_live_metrics.py | - | ✅ No conflict | Keep Python |
| **C4, E4, G4, I4** | ❌ Not written | KPISparklines.gs | ⚠️ Orphaned | Deploy KPISparklines.gs |
| **C6:K7** | update_live_metrics.py | - | ⚠️ Unclear purpose | Clarify vs row 4 |
| **G13** | update_live_metrics.py | Data.gs | ⚠️ Both write | Python should own |
| **H13:H22** | update_live_metrics.py | ❌ Avoided | ✅ Resolved | Keep Python |
| **G25:K41** | update_live_metrics.py | - | ✅ No conflict | Keep Python |
| **G31:J50** | - | Data.gs | ⚠️ Overlaps G31-41 | Disable Apps Script |
| **L12-L18** | update_live_metrics.py | - | ✅ No conflict | Keep Python |
| **L54:R67** | update_live_metrics.py | - | ✅ No conflict | Keep Python |
| **A32** | - | Charts.gs (chart) | ⚠️ Chart not updating | Fix or remove |
| **Data_Hidden** | update_live_metrics.py | KPISparklines.gs (read) | ✅ No conflict | Keep both |

---

## 🎯 PRIORITY ACTIONS

### **IMMEDIATE (Quick Wins)**

1. **Deploy KPISparklines.gs** ⏱️ 5 minutes
   - Push updated code with ymin/ymax to Apps Script
   - Verify C4, E4, G4, I4 display correctly
   - Status: Code ready, needs `clasp push`

2. **Set PYTHON_MANAGED Flag** ⏱️ 2 minutes
   ```python
   # Add to update_live_metrics.py main() function
   cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'AA1', [['PYTHON_MANAGED']])
   ```

3. **Disable Apps Script Outages** ⏱️ 5 minutes
   - Comment out Data.gs lines 230-245 (outages section)
   - Prevent overlap with Python's G25:K41

### **SHORT TERM (This Week)**

4. **Clarify KPI Sparkline Location** ⏱️ 15 minutes
   - Decide: Row 4 (Apps Script) or Row 7 (Python)?
   - If Row 4: Remove Python's C6:K7 updates
   - If Row 7: Remove KPISparklines.gs functionality

5. **Fix Wind Forecast Chart** ⏱️ 30 minutes
   - Option A: Add `build_publication_table_current.py` to cron schedule
   - Option B: Migrate wind forecast to Python + remove chart
   - Option C: Populate `publication_dashboard_live` from `update_live_metrics.py`

### **LONG TERM (Architectural Cleanup)**

6. **Deprecate publication_dashboard_live Pipeline** ⏱️ 2-4 hours
   - Archive `build_publication_table_current.py`
   - Remove Data.gs data display functions (keep only chart generation if needed)
   - Document Python as single source of truth

7. **Remove Redundant Scripts** ⏱️ 1-2 hours
   - Archive old dashboard files: `google_sheets_dashboard.gs`, `redesign_live_dashboard.gs`
   - Remove duplicate sparkline generators
   - Clean up `unified_dashboard_refresh.py` script list

8. **Create ARCHITECTURE.md** ⏱️ 1 hour
   - Document final data flow: BigQuery → Python → Sheets
   - Cell ownership matrix
   - Update frequency and dependencies

---

## 🚨 CRITICAL FINDINGS

### **1. No Automatic Wind Forecast Updates**
- `build_publication_table_current.py` not in cron
- `unified_dashboard_refresh.py` doesn't call it
- Wind forecast chart at A32 showing stale data

### **2. Potential Data Race in G31-G41**
- Python writes G25:K41 (includes rows 31-41)
- Apps Script writes G31:J50 (includes rows 31-50)
- Last writer wins = data corruption risk

### **3. Unclear KPI Sparkline Ownership**
- Python prepares sparklines for row 7 but NOT row 4
- Apps Script writes sparklines to row 4
- No coordination between the two approaches

### **4. PYTHON_MANAGED Flag Not Set**
- Apps Script has safety check for `AA1='PYTHON_MANAGED'`
- Python never sets this flag
- Apps Script could accidentally overwrite Python data

---

## 📝 NEXT STEPS

**Recommended Sequence**:
1. ✅ Set PYTHON_MANAGED flag in update_live_metrics.py
2. ✅ Deploy KPISparklines.gs for row 4 sparklines
3. ✅ Disable Apps Script outages display (comment out Data.gs lines 230-245)
4. ⏳ Add build_publication_table_current.py to cron OR migrate wind forecast to Python
5. ⏳ Remove C6:K7 sparkline updates from Python (redundant with row 4)
6. ⏳ Create ARCHITECTURE.md documenting final state
7. ⏳ Archive deprecated scripts and .gs files

**Estimated Total Time**: 3-5 hours for complete cleanup

---

*Audit completed: 23 December 2025*  
*Reviewed: update_live_metrics.py (1366 lines), Data.gs (290 lines), KPISparklines.gs (140 lines), Charts.gs (125 lines)*
