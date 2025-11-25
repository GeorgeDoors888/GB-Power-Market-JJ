# 🔍 CRITICAL CHECKLIST: Is Apps Script Actually Updated?

## The Issue
Data parsing works perfectly locally, but map still shows "server error".

## Most Likely Cause
**The Apps Script code in the editor might not be saved properly.**

## Verification Steps

### 1. Check Apps Script Editor
Open: Extensions → Apps Script

**Look for these lines** in the `getConstraintData()` function:

```javascript
// THIS SHOULD BE THERE (around line 50):
function parsePercent(value) {
  if (typeof value === 'number') return value;
  if (typeof value === 'string') {
    return parseFloat(value.replace('%', '')) || 0;
  }
  return 0;
}
```

**If you see this instead**, the code is NOT updated:
```javascript
// OLD CODE (WRONG):
util_pct: parseFloat(boundaryData[i][4]) || 0,
```

### 2. Check Apps Script Executions Log
1. Apps Script Editor → Click **Executions** (⏱️ clock icon on left)
2. Find most recent execution of `getConstraintData`
3. Click on it to see details

**If it shows an error**, that's the actual problem!

### 3. Manual Fix (If Code Looks Wrong)

Replace lines 36-88 in `constraint_map.gs` with:

```javascript
function getConstraintData() {
  try {
    const ss = SpreadsheetApp.getActive();
    const dashboard = ss.getSheetByName('Dashboard');
    
    if (!dashboard) {
      throw new Error('Dashboard sheet not found');
    }
    
    const boundaryData = dashboard.getRange('A116:H126').getValues();
    
    // IMPORTANT: Define helper functions OUTSIDE the loop
    function parsePercent(value) {
      if (typeof value === 'number') return value;
      if (typeof value === 'string') {
        return parseFloat(value.replace('%', '')) || 0;
      }
      return 0;
    }
    
    function parseNumber(value) {
      if (typeof value === 'number') return value;
      return parseFloat(value) || 0;
    }
    
    const constraints = [];
    for (let i = 1; i < boundaryData.length; i++) {
      if (boundaryData[i][0]) {
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

**KEY DIFFERENCE**: Helper functions are now OUTSIDE the loop (better practice).

### 4. After Updating Code

1. **Save** (Ctrl+S)
2. **Test it**: Run → `getConstraintData` (dropdown at top)
3. Check **Execution log** (View → Logs or Ctrl+Enter)
4. Should see: `Retrieved 10 constraints`
5. **Then deploy**: Deploy → Manage deployments → Edit → New version

### 5. Browser Console Check

Open map sidebar, press **F12**, look for:
- ❌ "Failed to load script" = Maps API key issue
- ❌ "ReferenceError: google is not defined" = Maps API not loaded
- ❌ "Server error" with details = Apps Script execution error

## Quick Test Command

Run this in Apps Script editor (Tools → Script editor):

```javascript
function testGetConstraintData() {
  var result = getConstraintData();
  Logger.log('Constraints: ' + JSON.stringify(result));
}
```

Click **Run** → `testGetConstraintData`

If it works → Code is fine, issue is elsewhere
If it fails → You'll see the actual error

---

**Most common issue**: Code looks correct in editor but wasn't saved or deployed properly!
