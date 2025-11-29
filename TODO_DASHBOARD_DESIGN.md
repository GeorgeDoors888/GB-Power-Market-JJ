# TODO: Implement Dashboard Design (apply_dashboard_design.py)

## 📋 Overview
Implement professional dashboard design with colors, dropdowns, conditional formatting, and interactive filters for Dashboard V2.

**Target Spreadsheet:** `1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc`  
**Status:** Planning Phase

---

## ✅ Prerequisites (Check First)

- [ ] **Verify `gspread-formatting` is installed**
  ```bash
  cd ~/GB-Power-Market-JJ
  pip install gspread-formatting
  # or
  pip list | grep gspread-formatting
  ```

- [ ] **Check service account credentials exist**
  ```bash
  ls -la ~/GB-Power-Market-JJ/inner-cinema-credentials.json
  ```

- [ ] **Verify current Dashboard sheet structure**
  - Open: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/
  - Check if "Dashboard" sheet exists
  - Note current column layout (A-L expected)

- [ ] **Create backup of current dashboard**
  ```bash
  # Manual: File > Make a copy in Google Sheets
  # Or use Python script to export current state
  ```

---

## 📝 Implementation Todos

### **Phase 1: Setup & Validation** 

- [ ] **1.1: Create the script file**
  ```bash
  cd ~/GB-Power-Market-JJ
  nano apply_dashboard_design.py
  # Paste the provided code
  ```

- [ ] **1.2: Review and customize color scheme**
  - [ ] Title bar: Currently `Color(0.0, 0.30, 0.59)` (dark blue)
  - [ ] KPI strip: Currently `Color(0.89, 0.95, 0.99)` (light blue)
  - [ ] Fuel header: Currently `Color(1.0, 0.98, 0.77)` (light yellow)
  - [ ] Interconnector header: `Color(0.78, 0.90, 0.79)` (light green)
  - [ ] Financial header: `Color(0.88, 0.75, 0.91)` (light purple)
  - [ ] Decision: Keep these colors or customize?

- [ ] **1.3: Verify column mappings match current dashboard**
  - [ ] A-C: Fuel/Generation data
  - [ ] E-F: Interconnectors
  - [ ] H-L: Financial/pricing data
  - [ ] M: Wind deviation % (for conditional formatting)

- [ ] **1.4: Review dropdown values for accuracy**
  - [ ] Time ranges: "Real-Time (10 min)", "24 h", "48 h", "7 days", "30 days"
  - [ ] Regions: Update with actual GB regions if different
  - [ ] Alerts: Customize alert types as needed

---

### **Phase 2: Test Script Safely**

- [ ] **2.1: Create test spreadsheet first**
  ```python
  # Modify script to use TEST_SPREADSHEET_ID
  # Make copy of dashboard and test on copy first
  ```

- [ ] **2.2: Test on copy spreadsheet**
  - [ ] Make a copy of Dashboard V2
  - [ ] Update SPREADSHEET_ID in script to copy ID
  - [ ] Run: `python apply_dashboard_design.py`
  - [ ] Verify formatting applies correctly
  - [ ] Check for errors

- [ ] **2.3: Review test results**
  - [ ] Title formatting looks good?
  - [ ] Column widths appropriate?
  - [ ] Dropdowns work correctly?
  - [ ] Colors match expectations?
  - [ ] Conditional formatting triggers properly?

---

### **Phase 3: Adapt to Current Dashboard Structure**

- [ ] **3.1: Review current Dashboard V2 layout**
  ```bash
  cd ~/GB-Power-Market-JJ
  cat LIVE_OUTAGES_AUTOMATION_DOCUMENTATION.md
  # Check current row/column structure
  ```

- [ ] **3.2: Map script formatting to actual dashboard**
  - Current structure has:
    - Row 1: Title
    - Row 9-18: Generation data (A-B columns)
    - Row 9-18: Interconnectors (C-D columns)
    - Row 31+: Live Outages section
  
  - [ ] Update row numbers in script to match
  - [ ] Update column ranges to match
  - [ ] Adjust header formatting ranges

- [ ] **3.3: Decide on new sections to add**
  - [ ] Add KPI strip at row 5? (or different location)
  - [ ] Add filter bar at row 3?
  - [ ] Keep existing sections or reorganize?

---

### **Phase 4: Enhance Script for Dashboard V2**

- [ ] **4.1: Modify title to reflect current version**
  ```python
  dash.update("A1", "⚡ GB ENERGY DASHBOARD V2 – REAL-TIME MARKET INSIGHTS")
  # or keep V3.5 if upgrading
  ```

- [ ] **4.2: Add formatting for Live Outages section**
  - [ ] Header formatting for outages table
  - [ ] Conditional formatting for critical outages (>500 MW)
  - [ ] Color coding by status (Critical=Red, Warning=Orange, etc.)

- [ ] **4.3: Add formatting for Battery Trading section**
  - [ ] If battery trading data exists
  - [ ] Format profit/loss cells (green=profit, red=loss)

- [ ] **4.4: Preserve existing Apps Script functionality**
  - [ ] Ensure formatting doesn't break existing scripts
  - [ ] Check if clasp-deployed code needs updates

---

### **Phase 5: Create Supporting Sheets**

- [ ] **5.1: Energy_Map sheet**
  ```python
  # Script already creates this
  # But need to populate with data
  ```
  - [ ] Define what goes in Energy_Map
    - [ ] DNO boundary coordinates?
    - [ ] GSP point locations?
    - [ ] Offshore wind farm coordinates?
  - [ ] Create data pipeline to populate it
  - [ ] Decide on visualization approach

- [ ] **5.2: Wind_Warnings sheet**
  - [ ] Create formulas for wind deviation warnings
  - [ ] Formula: `=IF(ABS((B2-C2)/C2)>0.15,"⚠️ Wind Shortfall","✅ Normal")`
  - [ ] Link to BigQuery wind forecast data
  - [ ] Create automation to update forecasts

---

### **Phase 6: Integration with Current Automation**

- [ ] **6.1: Review current automation scripts**
  - [ ] `realtime_dashboard_updater.py` - Does it conflict?
  - [ ] `update_outages_enhanced.py` - Preserve outages formatting
  - [ ] `update_summary_for_chart.py` - Coordinate with KPI strip
  - [ ] `update_iris_dashboard.py` - Check for overlaps

- [ ] **6.2: Decide when to run design script**
  - Option A: Run once manually (one-time setup)
  - Option B: Run daily to refresh formatting
  - Option C: Integrate into automation pipeline
  - [ ] Decision: _____________

- [ ] **6.3: Test with live automation**
  - [ ] Run design script
  - [ ] Let cron jobs run (wait 5-10 min)
  - [ ] Verify data updates don't break formatting
  - [ ] Verify formatting doesn't break data updates

---

### **Phase 7: Advanced Features**

- [ ] **7.1: Implement wind warning conditional formatting**
  - [ ] Identify column with wind deviation %
  - [ ] Test conditional format triggers correctly
  - [ ] Adjust threshold (currently >15%) if needed

- [ ] **7.2: Add more conditional formatting rules**
  - [ ] Price spike alerts (>£200/MWh?)
  - [ ] Outage severity (by MW capacity)
  - [ ] Interconnector flow direction (import=green, export=blue)
  - [ ] Battery profit/loss (profit=green, loss=red)

- [ ] **7.3: Enhance dropdowns with data validation**
  - [ ] Time range → triggers data refresh?
  - [ ] Region filter → filters visible data?
  - [ ] Alert type → highlights relevant rows?
  - [ ] Implement Apps Script handlers for dropdowns

- [ ] **7.4: Add date pickers functionality**
  - [ ] Start date (cell I3)
  - [ ] End date (cell K3)
  - [ ] Link to data filtering logic
  - [ ] Create Apps Script to handle date range changes

---

### **Phase 8: Testing & Validation**

- [ ] **8.1: Visual testing**
  - [ ] All colors render correctly
  - [ ] No overlapping formats
  - [ ] Text is readable (contrast check)
  - [ ] Dropdowns are user-friendly
  - [ ] Mobile view works (if applicable)

- [ ] **8.2: Functional testing**
  - [ ] Dropdowns trigger correctly
  - [ ] Date pickers accept valid dates
  - [ ] Conditional formatting updates live
  - [ ] Data updates preserve formatting
  - [ ] No performance issues

- [ ] **8.3: Integration testing**
  - [ ] Run all 4 automation scripts
  - [ ] Verify no conflicts
  - [ ] Check logs for errors
  - [ ] Monitor for 24 hours

---

### **Phase 9: Documentation & Deployment**

- [ ] **9.1: Document the design system**
  ```markdown
  Create: DASHBOARD_DESIGN_GUIDE.md
  - Color palette reference
  - Column layout diagram
  - Dropdown options
  - Conditional formatting rules
  - Maintenance instructions
  ```

- [ ] **9.2: Update existing documentation**
  - [ ] Update `LIVE_OUTAGES_AUTOMATION_DOCUMENTATION.md`
  - [ ] Update `DASHBOARD_UPDATE_COMPLETE.md`
  - [ ] Update `README.md` with new design info

- [ ] **9.3: Create rollback plan**
  ```bash
  # Keep backup of old dashboard
  # Document how to restore if needed
  # Keep old formatting in version control
  ```

- [ ] **9.4: Deploy to production**
  - [ ] Run on actual Dashboard V2
  - [ ] Update SPREADSHEET_ID to production ID
  - [ ] Run: `python apply_dashboard_design.py`
  - [ ] Verify in browser immediately

---

### **Phase 10: Post-Deployment**

- [ ] **10.1: Monitor for issues**
  - [ ] Check logs after next cron run
  - [ ] Verify data updates work
  - [ ] Check for user feedback (if others use it)

- [ ] **10.2: Performance check**
  - [ ] Spreadsheet loads quickly?
  - [ ] Formatting doesn't slow updates?
  - [ ] API quota usage reasonable?

- [ ] **10.3: Iterate and improve**
  - [ ] Collect improvement ideas
  - [ ] Plan v3.6 enhancements
  - [ ] Document lessons learned

---

## 🚀 Quick Start (When Ready)

```bash
# 1. Install dependencies
cd ~/GB-Power-Market-JJ
pip install gspread gspread-formatting google-auth

# 2. Create the script
nano apply_dashboard_design.py
# Paste the provided code

# 3. Customize (optional)
# - Edit colors
# - Adjust dropdown values
# - Update ranges to match your layout

# 4. Test on copy first!
# Make copy of dashboard, update SPREADSHEET_ID

# 5. Run
python apply_dashboard_design.py

# 6. Verify in browser
open "https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/"
```

---

## ⚠️ Risks & Considerations

### **Potential Issues:**
- [ ] Formatting may conflict with existing automation
- [ ] Conditional formatting rules can slow down large sheets
- [ ] Dropdown changes might require Apps Script handlers
- [ ] Color changes might break user muscle memory

### **Mitigation:**
- [ ] Always test on copy first
- [ ] Keep backup of original
- [ ] Document all changes
- [ ] Deploy during low-usage time

---

## 📊 Success Criteria

- ✅ Dashboard has professional, consistent design
- ✅ All dropdowns work and are intuitive
- ✅ Conditional formatting highlights important data
- ✅ Existing automation continues to work
- ✅ No performance degradation
- ✅ User feedback is positive

---

## 📝 Notes

**Current Dashboard Status:**
- Version: V2
- URL: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/
- Last updated: Nov 26, 2025
- Has: Live Outages, Generation, Interconnectors, Battery Trading

**Questions to Answer:**
1. Should this be V3.5 or keep as V2?
2. Where exactly should filter bar go?
3. What geospatial data for Energy_Map?
4. Which wind forecast source for warnings?

---

**Created:** 29 November 2025  
**Next Review:** After Phase 1 completion  
**Owner:** Dashboard Team
