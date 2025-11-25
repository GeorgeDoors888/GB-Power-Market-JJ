# 🚨 DEPLOYMENT ISSUE: Version 10 vs Version 11

## Problem
You deployed **Version 10** at 01:03, but that was **BEFORE** the percentage parsing fix was committed at 01:06.

## Timeline
- **01:03** - Version 10 deployed (OLD CODE without parsePercent fix)
- **01:06** - Percentage parsing fix committed to GitHub (LOCAL CODE updated)
- **Now** - Map still using Version 10 with bug

## Solution: Deploy Version 11

### Step 1: Copy Updated Code
The local file `/Users/georgemajor/GB Power Market JJ/dashboard/apps-script/constraint_map.gs` has the fix.

Open Apps Script and **replace the ENTIRE `getConstraintData()` function** (lines ~36-88) with:

```javascript
/**
 * Get constraint data from BigQuery via Dashboard sheet
 */
function getConstraintData() {
  try {
    const ss = SpreadsheetApp.getActive();
    const dashboard = ss.getSheetByName('Dashboard');
    
    if (!dashboard) {
      throw new Error('Dashboard sheet not found');
    }
    
    // Read boundary data from rows 116-126
    const boundaryData = dashboard.getRange('A116:H126').getValues();
    
    const constraints = [];
    for (let i = 1; i < boundaryData.length; i++) {
      if (boundaryData[i][0]) {
        // Helper function to parse percentage strings like "25.2%" to 25.2
        function parsePercent(value) {
          if (typeof value === 'number') return value;
          if (typeof value === 'string') {
            return parseFloat(value.replace('%', '')) || 0;
          }
          return 0;
        }
        
        // Helper function to parse numbers that might be strings
        function parseNumber(value) {
          if (typeof value === 'number') return value;
          return parseFloat(value) || 0;
        }
        
        constraints.push({
          boundary_id: String(boundaryData[i][0]),
          name: String(boundaryData[i][1] || 'Unknown'),
          flow_mw: parseNumber(boundaryData[i][2]),
          limit_mw: parseNumber(boundaryData[i][3]),
          util_pct: parsePercent(boundaryData[i][4]),
          margin_mw: parseNumber(boundaryData[i][5]),
          status: String(boundaryData[i][6] || 'Unknown'),
          direction: String(boundaryData[i][7] || 'N/A')
        });
      }
    }
    
    Logger.log('Retrieved ' + constraints.length + ' constraints');
    return constraints;
    
  } catch (error) {
    Logger.log('Error in getConstraintData: ' + error.toString());
    throw new Error('Failed to load data: ' + error.message);
  }
}
```

### Step 2: Deploy Version 11
1. **Save** (Ctrl+S)
2. **Deploy → Manage deployments**
3. Click **Edit** (pencil icon) next to Version 10
4. Change "Version" to **New version**
5. Description: `Fixed percentage parsing (parsePercent function)`
6. **Deploy**
7. You should see **Version 11** created

### Step 3: Test
1. Close Apps Script editor
2. Refresh Dashboard spreadsheet
3. Click: **🗺️ Constraint Map → 📍 Show Interactive Map**
4. Should work now!

## How to Verify Fix is Applied

Check Apps Script execution log:
1. Apps Script Editor → **Executions** (⏱️ clock icon)
2. Look for recent `getConstraintData` execution
3. Should show: `Retrieved 10 constraints` (not an error)

## Key Difference

**Version 10 (BROKEN):**
```javascript
util_pct: parseFloat(boundaryData[i][4]) || 0,  // ❌ Fails on "25.2%"
```

**Version 11 (FIXED):**
```javascript
util_pct: parsePercent(boundaryData[i][4]),  // ✅ Strips % then parses
```

The parsePercent function removes the `%` symbol before calling parseFloat.

---

**The code is correct locally, but Apps Script is still running the old Version 10!**
