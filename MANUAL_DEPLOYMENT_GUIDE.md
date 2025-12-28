# 🚀 Manual Deployment Instructions - Apps Script Updates
**Date**: 23 December 2025  
**Purpose**: Deploy KPISparklines.gs and Data.gs updates to Google Apps Script

---

## ⚠️ CLASP CONNECTIVITY ISSUE

Clasp push failed due to network connectivity:
```
request to https://oauth2.googleapis.com/token failed
reason: connect EHOSTUNREACH
```

**Manual deployment required** via Google Sheets web interface.

---

## 📝 STEP-BY-STEP DEPLOYMENT

### **1. Open Apps Script Editor**

1. Open Google Sheets: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
2. Click **Extensions** → **Apps Script**
3. Script project ID: `1b2dOZ4lw-zJvKdZ4MaJ48f1NR7ewCtUbZOGWGb3n8O7P-kgnUsThs980`

---

### **2. Update Data.gs** ✅ (Disable Outages Section)

**File**: `Data.gs`  
**Lines to Change**: 228-244

**Find this code** (around line 228):
```javascript
  // Display Outages (v2 only)
  if (isV2 && data.outages && data.outages.length > 0) {
    // Outages start at row 32 (below Wind Analysis header at 30)
    // Move to Right Side (Column G) to avoid Chart on Left

    // Clear previous outages first
    sheet.getRange('G32:L50').clearContent();

    // Headers
    sheet.getRange('G31:J31').setValues([['Asset Name', 'Fuel Type', 'Unavail (MW)', 'Cause']]);
    sheet.getRange('G31:J31').setFontWeight('bold').setBackground('#ecf0f1');

    const outageData = data.outages.map(o => [o.assetName, o.fuelType, o.unavailMw, o.cause]);
    sheet.getRange(32, 7, outageData.length, 4).setValues(outageData);
  }
```

**Replace with**:
```javascript
  // Display Outages (v2 only) - DISABLED: Python manages G25:K41
  // NOTE: Active Outages are now managed by Python update_live_metrics.py at G25:K41
  // This section is disabled to prevent data conflicts and overlapping ranges (G31-41)
  // Python version has 5 columns (includes Normal Capacity) vs Apps Script's 4 columns
  /*
  if (isV2 && data.outages && data.outages.length > 0) {
    // Outages start at row 32 (below Wind Analysis header at 30)
    // Move to Right Side (Column G) to avoid Chart on Left

    // Clear previous outages first
    sheet.getRange('G32:L50').clearContent();

    // Headers
    sheet.getRange('G31:J31').setValues([['Asset Name', 'Fuel Type', 'Unavail (MW)', 'Cause']]);
    sheet.getRange('G31:J31').setFontWeight('bold').setBackground('#ecf0f1');

    const outageData = data.outages.map(o => [o.assetName, o.fuelType, o.unavailMw, o.cause]);
    sheet.getRange(32, 7, outageData.length, 4).setValues(outageData);
  }
  */
```

**What Changed**: Commented out entire outages section to prevent overlap with Python's G25:K41 range.

---

### **3. Verify KPISparklines.gs** ✅ (Already Updated Locally)

**File**: `KPISparklines.gs`  
**Lines to Verify**: 49-71

**This code should already be present** (with ymin/ymax parameters):
```javascript
  const kpiConfigs = [
    { cell: 'C4', dataRow: 22, label: 'Wholesale Price', color: '#e74c3c', chartType: 'column', ymin: null, ymax: null },
    { cell: 'E4', dataRow: 23, label: 'Grid Frequency', color: '#2ecc71', chartType: 'line', ymin: 49.8, ymax: 50.2 },
    { cell: 'G4', dataRow: 24, label: 'Total Generation', color: '#f39c12', chartType: 'column', ymin: 20, ymax: 45 },
    { cell: 'I4', dataRow: 25, label: 'Wind Output', color: '#4ECDC4', chartType: 'column', ymin: 5, ymax: 20 }
  ];

  kpiConfigs.forEach(config => {
    let options = `{"charttype","${config.chartType}";"color","${config.color}"`;
    if (config.ymin !== null && config.ymax !== null) {
      options += `;"ymin",${config.ymin};"ymax",${config.ymax}`;
    }
    options += `}`;
    const formula = `=SPARKLINE(Data_Hidden!$B$${config.dataRow}:$AW$${config.dataRow}, ${options})`;
    sheet.getRange(config.cell).setFormula(formula);
  });
```

**If this code is NOT present**, copy the entire function from:
`/home/george/GB-Power-Market-JJ/clasp-gb-live-2/src/KPISparklines.gs`

---

### **4. Save and Run**

1. Click **💾 Save** (Ctrl+S)
2. Click **▶️ Run** → Select `addKPISparklinesManual`
3. Authorize if prompted
4. Check execution log for success message

**Expected Output**:
```
✅ KPI sparklines installed:
• C4: Wholesale Price (column chart)
• E4: Grid Frequency (line chart)
• G4: Total Generation (column chart)
• I4: Wind Output (column chart)

Note: Data is provided by Python script update_live_metrics.py
```

---

### **5. Verify Results in Google Sheets**

Navigate back to the spreadsheet and check:

**Row 4 Sparklines** (Apps Script):
- ✅ **C4**: Wholesale Price sparkline (purple column chart)
- ✅ **E4**: Grid Frequency sparkline (green line, y-axis 49.8-50.2)
- ✅ **G4**: Total Generation sparkline (orange column, y-axis 20-45 GW)
- ✅ **I4**: Wind Output sparkline (teal column, y-axis 5-20 GW)

**Row 6 Values** (Python):
- ✅ **C6**: £90.00 (current wholesale price)
- ✅ **E6**: +0.015 Hz (frequency deviation)
- ✅ **G6**: 35.2 GW (total generation)
- ✅ **I6**: 12.8 GW (wind output)

**Active Outages** (Python):
- ✅ **G25**: Header with total units and offline MW
- ✅ **G27:K41**: Top 15 outages (5 columns including Normal MW)
- ❌ **G31:J50**: Should be empty (Apps Script section disabled)

**Cell AA1**:
- ✅ Should show: `PYTHON_MANAGED`

---

## ✅ PYTHON CHANGES (Already Deployed)

The following changes were made to `update_live_metrics.py`:

### **Change 1: Set PYTHON_MANAGED Flag**
```python
# Line ~845 (after A3 update)
cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'AA1', [['PYTHON_MANAGED']])
```

### **Change 2: Removed Redundant Sparkline Generation**
- **Removed**: Lines generating sparklines for row 7 (C7, E7, G7, I7, K7)
- **Kept**: Row 6 KPI values only (C6, E6, G6, I6, K6)
- **Reason**: Apps Script KPISparklines.gs now manages row 4 sparklines

### **Change 3: Updated Comments**
Added documentation explaining Apps Script manages sparklines in row 4, Python provides data in Data_Hidden.

---

## 🧪 TESTING CHECKLIST

After deployment, verify:

- [ ] Cell AA1 shows `PYTHON_MANAGED`
- [ ] Row 4 (C4, E4, G4, I4) has sparklines with proper y-axis scaling
- [ ] Row 6 (C6, E6, G6, I6) has current KPI values
- [ ] Row 7 is empty (no old sparklines from Python)
- [ ] G25:K41 shows Active Outages (Python managed)
- [ ] G31:J50 is empty (Apps Script outages disabled)
- [ ] No "Loading..." or error messages in cells

---

## 🔄 ROLLBACK PROCEDURE

If issues occur, revert Apps Script changes:

1. **Data.gs**: Uncomment outages section (remove `/*` and `*/`)
2. **KPISparklines.gs**: No changes needed (improvements are safe)
3. Refresh spreadsheet: Extensions → Apps Script → Run `refreshDashboard()`

For Python rollback:
```bash
cd /home/george/GB-Power-Market-JJ
git diff update_live_metrics.py  # Review changes
git checkout update_live_metrics.py  # Revert if needed
```

---

## 📞 SUPPORT

If deployment fails:
1. Check CODE_AUDIT_REPORT.md for detailed conflict analysis
2. Review execution logs in Apps Script (View → Logs)
3. Check Python logs: `tail -f logs/dashboard_updater.log`

---

*Deployment guide created: 23 December 2025*  
*Tested with: update_live_metrics.py (1366 lines), KPISparklines.gs (140 lines), Data.gs (290 lines)*
