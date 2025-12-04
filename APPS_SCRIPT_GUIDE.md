# 🔌 Apps Script Guide

Complete reference for Google Apps Script integration in the BESS Dashboard system.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Deployment](#deployment)
- [Menu System](#menu-system)
- [Functions Reference](#functions-reference)
- [Auto-Triggers](#auto-triggers)
- [BigQuery Integration](#bigquery-integration)
- [Error Handling](#error-handling)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

### Purpose
Google Apps Script provides automation, data validation, and menu-driven functionality for the BESS Dashboard, eliminating the need for manual data entry and enabling real-time DNO lookups.

### Key Features
- **8-item menu** for user actions
- **Auto-triggers** on cell edits (MPAN, voltage)
- **BigQuery integration** via Vercel proxy
- **Data validation** (MPAN, postcode)
- **HH profile generation** (48 periods)

### File Information
- **Location:** `apps-script/Code.gs`
- **Lines:** 383
- **Runtime:** V8
- **Timezone:** Europe/London

---

## 🚀 Deployment

### Why Deployment Keeps Being Missed

**Root Causes:**
1. ❌ No automated CI/CD pipeline for Apps Script
2. ❌ Manual copy-paste required (error-prone)
3. ❌ Clasp authentication expires regularly
4. ❌ No deployment status indicator in dashboard

**Solutions Implemented:**
1. ✅ Created `apps-script/` directory structure
2. ✅ Added `.clasp.json` configuration
3. ✅ Function aliases for backward compatibility
4. ✅ Deployment checklist (this document)
5. ✅ Version control for Apps Script files

### Method 1: Clasp (Automated - Preferred)

#### Prerequisites
```bash
# Install Node.js 16+
node --version

# Install clasp globally
npm install -g @google/clasp

# Verify installation
clasp --version
```

#### Login to Clasp
```bash
cd "/Users/georgemajor/GB-Power-Market-JJ"

# Login (opens browser)
clasp login
# ✅ Grant permissions
# ✅ See "Authorization successful"
```

#### Deploy Script
```bash
# Push to Apps Script
clasp push

# Expected output:
# └─ apps-script/Code.gs
# └─ apps-script/appsscript.json
# Pushed 2 files.

# Open in browser to verify
clasp open
```

#### Troubleshooting Clasp

**Issue: Authentication Error**
```bash
# Clear credentials
rm ~/.clasprc.json

# Re-authenticate
clasp login
clasp push
```

**Issue: Script ID Not Found**
```bash
# Verify .clasp.json
cat .clasp.json
# Should show: "scriptId": "1svUewU3Q0n77ku0VJgtJ3GquVsSRii-pfOREpCQ9mG-v1x2oWtGZuiuz"

# List your projects
clasp list
```

**Issue: Permission Denied**
```bash
# Check Google account has Apps Script access
# Organization policies may block clasp
# Use Manual Method instead
```

### Method 2: Manual (Always Works)

#### Step-by-Step Process

1. **Open Apps Script Editor**
   ```
   https://script.google.com/d/1svUewU3Q0n77ku0VJgtJ3GquVsSRii-pfOREpCQ9mG-v1x2oWtGZuiuz/edit
   ```

2. **Clear Existing Code**
   - Click in editor
   - `Cmd+A` (Select All)
   - `Delete`

3. **Copy Local Code**
   ```bash
   # macOS
   cat apps-script/Code.gs | pbcopy
   
   # Linux
   cat apps-script/Code.gs | xclip -selection clipboard
   
   # Windows (Git Bash)
   cat apps-script/Code.gs | clip
   ```

4. **Paste in Editor**
   - Click in Apps Script editor
   - `Cmd+V` (Paste)
   - Verify: Should see 383 lines
   - Check first line: `/** BESS Complete Apps Script */`
   - Check last line: `return ContentService.createTextOutput('BESS Apps Script API');`

5. **Save**
   - Click 💾 Save button
   - Wait for "Saved" message
   - Should see: "All changes saved in Drive"

6. **Refresh Dashboard**
   ```
   https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit
   ```
   - `Cmd+R` to refresh page
   - Wait for page reload
   - Look for "🔋 BESS Tools" menu in menu bar

7. **Test Deployment**
   - Click "🔋 BESS Tools"
   - Should see 8 menu items
   - Click "📈 Show Status"
   - Should see popup with current settings

### Verification Checklist

- [ ] Apps Script editor shows 383 lines
- [ ] First line: `/** BESS Complete Apps Script */`
- [ ] Menu appears: "🔋 BESS Tools"
- [ ] 8 menu items visible
- [ ] Test function works (Show Status)
- [ ] No JavaScript errors in console
- [ ] onEdit trigger responds to changes

---

## 🎨 Menu System

### Menu Structure

```
🔋 BESS Tools
├─ 🔄 Refresh DNO Data          → refreshDnoLookup()
├─ ───────────────────────────
├─ ✅ Validate MPAN             → validateMpan()
├─ 📍 Validate Postcode         → validatePostcode()
├─ ───────────────────────────
├─ 📊 Generate HH Profile       → generateHhProfile()
├─ 💰 Calculate PPA Arbitrage   → calculatePpaArbitrage()
├─ 📈 Show Status               → showStatus()
├─ ───────────────────────────
└─ ℹ️ Help & Instructions        → showHelp()
```

### Menu Creation Code

```javascript
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  ui.createMenu('🔋 BESS Tools')
    .addItem('🔄 Refresh DNO Data', 'refreshDnoLookup')
    .addSeparator()
    .addItem('✅ Validate MPAN', 'validateMpan')
    .addItem('📍 Validate Postcode', 'validatePostcode')
    .addSeparator()
    .addItem('📊 Generate HH Profile', 'generateHhProfile')
    .addItem('💰 Calculate PPA Arbitrage', 'calculatePpaArbitrage')
    .addItem('📈 Show Status', 'showStatus')
    .addSeparator()
    .addItem('ℹ️ Help & Instructions', 'showHelp')
    .addToUi();
}
```

### Customizing Menu

**Add New Item:**
```javascript
.addItem('🔋 New Feature', 'myNewFunction')
```

**Add Submenu:**
```javascript
const submenu = ui.createMenu('⚙️ Advanced')
  .addItem('Option 1', 'option1Function')
  .addItem('Option 2', 'option2Function');

ui.createMenu('🔋 BESS Tools')
  // ... existing items
  .addSubMenu(submenu)
  .addToUi();
```

**Change Menu Name:**
```javascript
ui.createMenu('⚡ Battery Tools')  // Instead of '🔋 BESS Tools'
```

---

## 📚 Functions Reference

### 1. refreshDnoLookup()

**Purpose:** Fetch DNO data from BigQuery based on MPAN ID

**Trigger:** Menu or auto-trigger on B6 edit

**Input:** Cell B6 (MPAN ID: 10-23)

**Output:** Cells B6:H6 (DNO details)

**Process:**
```javascript
function refreshDnoLookup() {
  refreshDnoData();  // Alias calls main function
}

function refreshDnoData() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  
  // 1. Get MPAN from B6
  const mpanInput = sheet.getRange('B6').getValue();
  
  // 2. Validate MPAN (10-23)
  const mpanNum = parseInt(mpanId);
  if (isNaN(mpanNum) || mpanNum < 10 || mpanNum > 23) {
    sheet.getRange('A4').setValue('❌ Error: MPAN must be 10-23');
    return;
  }
  
  // 3. Query BigQuery via Vercel proxy
  const url = 'https://gb-power-market-jj.vercel.app/api/proxy-v2';
  const payload = {
    query: `SELECT * FROM neso_dno_reference WHERE mpan_id = '${mpanId}'`
  };
  const response = UrlFetchApp.fetch(url, {
    'method': 'post',
    'contentType': 'application/json',
    'payload': JSON.stringify(payload)
  });
  
  // 4. Parse response
  const data = JSON.parse(response.getContentText());
  const row = data.rows[0];
  
  // 5. Update sheet
  sheet.getRange('B6:H6').setValues([[
    row.mpan_id,
    row.dno_key,
    row.dno_name,
    row.dno_short_code,
    row.market_participant_id,
    row.gsp_group_id,
    row.gsp_group_name
  ]]);
  
  // 6. Auto-update DUoS rates
  updateDuosRates(row.dno_short_code);
  
  // 7. Update status
  sheet.getRange('A4').setValue('✅ DNO data updated successfully');
}
```

**Example:**
- Input B6: `14`
- Output B6:H6: `14, WMID, NGED-WM, NGED, 10T, 14, West Midlands`

**Error Handling:**
- Empty B6 → "❌ Error: Please enter MPAN ID"
- Invalid MPAN → "❌ Error: MPAN must be 10-23"
- BigQuery error → "❌ Error: [error message]"
- No data found → "❌ Error: No DNO found for MPAN X"

### 2. calculatePpaArbitrage()

**Purpose:** Prompt user to run Python PPA analysis script

**Trigger:** Menu only

**Input:** None

**Output:** Dialog box with instructions

**Code:**
```javascript
function calculatePpaArbitrage() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  
  Browser.msgBox(
    '⚙️ Calculating PPA Arbitrage', 
    'This will run the Python analysis script.\n\n' +
    'Please run this command in your terminal:\n\n' +
    'python3 calculate_ppa_arbitrage.py\n\n' +
    'Results will appear in rows 90+',
    Browser.Buttons.OK
  );
}

// Alias for compatibility
function calculate_ppa_arbitrage() {
  calculatePpaArbitrage();
}
```

**Why Not Run Python Directly?**
Apps Script cannot execute local Python scripts. It can only:
1. Call external APIs (e.g., Vercel proxy)
2. Run JavaScript code
3. Manipulate Google Sheets

### 3. generateHhProfile()

**Purpose:** Generate 48 half-hourly consumption periods

**Trigger:** Menu only

**Input:** 
- B17: Min kW (e.g., 500)
- B18: Avg kW (e.g., 1500)
- B19: Max kW (e.g., 2500)
- B13: RED time bands
- B14: AMBER time bands

**Output:** Rows 22-69 (48 periods)

**Code:**
```javascript
function generateHhProfile() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  
  // Get parameters
  const minKw = parseFloat(sheet.getRange('B17').getValue()) || 500;
  const avgKw = parseFloat(sheet.getRange('B18').getValue()) || 1500;
  const maxKw = parseFloat(sheet.getRange('B19').getValue()) || 2500;
  
  // Get time bands
  const redBands = parseTimeBand(sheet.getRange('B13').getValue());
  const amberBands = parseTimeBand(sheet.getRange('B14').getValue());
  
  // Generate 48 half-hourly periods
  const profile = [];
  for (let hh = 0; hh < 48; hh++) {
    const hour = Math.floor(hh / 2);
    const minute = (hh % 2) * 30;
    const timeStr = Utilities.formatString('%02d:%02d', hour, minute);
    
    // Determine band
    let band = 'GREEN';
    if (redBands.includes(hour)) band = 'RED';
    else if (amberBands.includes(hour)) band = 'AMBER';
    
    // Calculate consumption
    let consumption;
    if (band === 'RED') {
      consumption = avgKw + (maxKw - avgKw) * 0.7;  // 70% to max
    } else if (band === 'AMBER') {
      consumption = avgKw;
    } else {
      consumption = minKw + (avgKw - minKw) * 0.3;  // 30% to avg
    }
    
    profile.push([timeStr, band, consumption.toFixed(2)]);
  }
  
  // Write to sheet
  sheet.getRange(21, 1, 1, 3).setValues([['Time', 'Band', 'Consumption (kW)']]);
  sheet.getRange(22, 1, profile.length, 3).setValues(profile);
  
  Browser.msgBox('✅ HH Profile Generated', 
    '48 half-hourly periods generated\nSee rows 22-69', 
    Browser.Buttons.OK);
}

function parseTimeBand(bandStr) {
  if (!bandStr) return [];
  
  const hours = [];
  const ranges = bandStr.toString().split(',');
  
  for (const range of ranges) {
    const parts = range.trim().split('-');
    if (parts.length === 2) {
      const start = parseInt(parts[0].split(':')[0]);
      const end = parseInt(parts[1].split(':')[0]);
      for (let h = start; h <= end; h++) {
        hours.push(h);
      }
    }
  }
  
  return hours;
}
```

**Example Output:**
```
Time    Band    Consumption (kW)
00:00   GREEN   650.00
00:30   GREEN   650.00
...
16:00   RED     2150.00
16:30   RED     2150.00
...
```

### 4. validateMpan()

**Purpose:** Validate MPAN format and range

**Trigger:** Menu only

**Input:** Cell B6

**Output:** Dialog box with validation result

**Code:**
```javascript
function validateMpan() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  const mpan = sheet.getRange('B6').getValue();
  
  if (!mpan) {
    Browser.msgBox('❌ No MPAN', 
      'Please enter MPAN ID in B6', 
      Browser.Buttons.OK);
    return;
  }
  
  const mpanStr = mpan.toString().trim();
  const mpanNum = parseInt(mpanStr.split('-')[0].trim());
  
  if (mpanNum >= 10 && mpanNum <= 23) {
    Browser.msgBox('✅ MPAN Valid', 
      'MPAN: ' + mpanNum + '\nRange: 10-23', 
      Browser.Buttons.OK);
  } else {
    Browser.msgBox('❌ Invalid MPAN', 
      'MPAN must be 10-23\nGot: ' + mpanStr, 
      Browser.Buttons.OK);
  }
}
```

**MPAN Reference:**
| ID | DNO | Region |
|----|-----|--------|
| 10 | UKPN-EPN | Eastern |
| 11 | NGED-EM | East Midlands |
| 12 | UKPN-LPN | London |
| 13 | SP-Manweb | Merseyside & N Wales |
| 14 | NGED-WM | West Midlands |
| 15 | NPg-NE | North East |
| 16 | ENWL | North West |
| 17 | SSE-SHEPD | North Scotland |
| 18 | SP-Distribution | South Scotland |
| 19 | UKPN-SPN | South Eastern |
| 20 | SSE-SEPD | Southern |
| 21 | NGED-SWales | South Wales |
| 22 | NGED-SW | South Western |
| 23 | NPg-Y | Yorkshire |

### 5. validatePostcode()

**Purpose:** Validate UK postcode format

**Trigger:** Menu only

**Input:** Cell A6

**Output:** Dialog box with validation result

**Code:**
```javascript
function validatePostcode() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  const postcode = sheet.getRange('A6').getValue();
  
  if (!postcode) {
    Browser.msgBox('❌ No Postcode', 
      'Please enter postcode in A6', 
      Browser.Buttons.OK);
    return;
  }
  
  // UK postcode regex
  const regex = /^([A-Z]{1,2}\d{1,2}[A-Z]?)\s*(\d[A-Z]{2})$/i;
  const normalized = postcode.toString().trim().toUpperCase();
  
  if (regex.test(normalized)) {
    Browser.msgBox('✅ Postcode Valid', 
      'Normalized: ' + normalized, 
      Browser.Buttons.OK);
  } else {
    Browser.msgBox('❌ Invalid Postcode', 
      'Please check format\nExample: SW2 5UP', 
      Browser.Buttons.OK);
  }
}
```

**Valid Formats:**
- `SW2 5UP` (with space)
- `SW25UP` (without space)
- `EC1A 1BB`
- `W1A 0AX`
- `M1 1AE`
- `B33 8TH`

### 6. showStatus()

**Purpose:** Display current dashboard configuration

**Trigger:** Menu only

**Input:** Current sheet values

**Output:** Dialog box with status

**Code:**
```javascript
function showStatus() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  
  const status = {
    'MPAN': sheet.getRange('B6').getValue() || 'Not set',
    'DNO': sheet.getRange('C6').getValue() || 'Not set',
    'Voltage': sheet.getRange('A10').getValue() || 'Not set',
    'Red Rate': sheet.getRange('B10').getValue() || 'Not set',
    'PPA Price': sheet.getRange('B21').getValue() || 'Not set',
    'Time Period': sheet.getRange('L6').getValue() || 'Not set',
    'Last Update': sheet.getRange('A4').getValue() || 'Never'
  };
  
  let msg = '📊 BESS Sheet Status\n\n';
  for (const [key, val] of Object.entries(status)) {
    msg += key + ': ' + val + '\n';
  }
  
  Browser.msgBox('BESS Status', msg, Browser.Buttons.OK);
}
```

### 7. showHelp()

**Purpose:** Display comprehensive help documentation

**Trigger:** Menu only

**Input:** None

**Output:** HTML modal with documentation

**Code:**
```javascript
function showHelp() {
  const html = HtmlService.createHtmlOutput(`
    <style>
      body { font-family: Arial, sans-serif; padding: 20px; }
      h2 { color: #1a73e8; }
      h3 { color: #34a853; margin-top: 20px; }
      ul { line-height: 1.8; }
      code { background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }
      .mpan-table { border-collapse: collapse; width: 100%; margin: 20px 0; }
      .mpan-table td { border: 1px solid #ddd; padding: 8px; }
      .mpan-table th { background: #1a73e8; color: white; padding: 10px; }
    </style>
    
    <h2>🔋 BESS Tools Help</h2>
    
    <h3>Quick Start:</h3>
    <ol>
      <li>Enter MPAN ID (10-23) in cell <b>B6</b></li>
      <li>Click: <b>🔋 BESS Tools → 🔄 Refresh DNO Data</b></li>
      <li>Select voltage level in <b>A10</b> (LV/HV/EHV)</li>
      <li>DUoS rates auto-populate in <b>B10:D10</b></li>
      <li>Set battery parameters in <b>B17:B19</b></li>
      <li>Click: <b>🔋 BESS Tools → 📊 Generate HH Profile</b></li>
    </ol>
    
    <h3>MPAN IDs by Region:</h3>
    <table class="mpan-table">
      <tr><th>ID</th><th>DNO</th><th>Region</th></tr>
      <tr><td>10</td><td>UKPN-EPN</td><td>Eastern</td></tr>
      <tr><td>11</td><td>NGED-EM</td><td>East Midlands</td></tr>
      <tr><td>12</td><td>UKPN-LPN</td><td>London</td></tr>
      <tr><td>14</td><td>NGED-WM</td><td>West Midlands</td></tr>
      <!-- ... all 14 regions ... -->
    </table>
    
    <h3>Python Scripts:</h3>
    <ul>
      <li><code>python3 calculate_ppa_arbitrage.py</code> - 24-month analysis</li>
      <li><code>python3 calculate_bess_revenue.py</code> - Revenue breakdown</li>
      <li><code>python3 visualize_ppa_costs.py</code> - Generate charts</li>
    </ul>
    
    <p><small>Data source: NESO DNO Reference via BigQuery</small></p>
  `)
    .setWidth(600)
    .setHeight(700);
  
  SpreadsheetApp.getUi().showModalDialog(html, '🔋 BESS Tools Help');
}
```

---

## ⚡ Auto-Triggers

### onEdit Trigger

**Purpose:** Automatically execute functions when specific cells are edited

**Implementation:**
```javascript
function onEdit(e) {
  const sheet = e.source.getActiveSheet();
  if (sheet.getName() !== 'BESS') return;  // Only BESS sheet
  
  const range = e.range;
  const row = range.getRow();
  const col = range.getColumn();
  
  // Auto-refresh DNO data when MPAN changes (B6)
  if (row === 6 && col === 2) {
    const value = e.value;
    if (value && value.toString().trim()) {
      Utilities.sleep(1000);  // Let user finish typing
      refreshDnoData();
    }
  }
  
  // Auto-update DUoS rates when voltage changes (A10)
  if (row === 10 && col === 1) {
    const dnoShortCode = sheet.getRange('E6').getValue();
    if (dnoShortCode) {
      updateDuosRates(dnoShortCode);
    }
  }
}
```

**Trigger Locations:**
| Cell | Action | Function Called |
|------|--------|-----------------|
| B6 | MPAN ID changed | `refreshDnoData()` |
| A10 | Voltage changed | `updateDuosRates()` |

**Behavior:**
- ✅ Triggers only on user edits (not programmatic changes)
- ✅ 1-second delay to avoid triggering mid-typing
- ✅ Validates value exists before triggering
- ✅ Sheet name check (only BESS sheet)

**Debugging:**
```javascript
function testOnEdit() {
  // Simulate edit event
  const e = {
    source: SpreadsheetApp.getActive(),
    range: SpreadsheetApp.getActive().getRange('B6'),
    value: '14'
  };
  onEdit(e);
}
```

---

## 🔗 BigQuery Integration

### Vercel Proxy Architecture

**Why Proxy Needed:**
Apps Script cannot directly call BigQuery API due to:
1. CORS restrictions
2. Authentication complexity
3. Library limitations

**Solution: Vercel Edge Function**
```javascript
// Vercel: /api/proxy-v2.js
export default async function handler(req, res) {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  // Parse request
  const { query } = req.body;
  
  // Execute BigQuery query
  const { BigQuery } = require('@google-cloud/bigquery');
  const bigquery = new BigQuery({
    projectId: 'inner-cinema-476211-u9',
    credentials: JSON.parse(process.env.BIGQUERY_CREDENTIALS)
  });
  
  const [rows] = await bigquery.query(query);
  
  return res.json({ rows });
}
```

### Apps Script BigQuery Call

```javascript
function queryBigQuery(sqlQuery) {
  const url = 'https://gb-power-market-jj.vercel.app/api/proxy-v2';
  
  const options = {
    'method': 'post',
    'contentType': 'application/json',
    'payload': JSON.stringify({ query: sqlQuery }),
    'muteHttpExceptions': true
  };
  
  try {
    const response = UrlFetchApp.fetch(url, options);
    const statusCode = response.getResponseCode();
    
    if (statusCode !== 200) {
      throw new Error('HTTP ' + statusCode + ': ' + response.getContentText());
    }
    
    const data = JSON.parse(response.getContentText());
    return data.rows;
    
  } catch (error) {
    Logger.log('BigQuery error: ' + error);
    throw error;
  }
}
```

### Example Queries

**DNO Lookup:**
```javascript
const query = `
  SELECT 
    mpan_id,
    dno_key,
    dno_name,
    dno_short_code,
    market_participant_id,
    gsp_group_id,
    gsp_group_name
  FROM \`inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference\`
  WHERE mpan_id = '${mpanId}'
`;
```

**DUoS Rates:**
```javascript
const query = `
  SELECT 
    time_band,
    rate_p_per_kwh
  FROM \`inner-cinema-476211-u9.uk_energy_prod.duos_tariff_rates\`
  WHERE dno_code = '${dnoCode}'
    AND voltage_level = '${voltageLevel}'
  ORDER BY time_band
`;
```

---

## 🚨 Error Handling

### Try-Catch Pattern

```javascript
function robustFunction() {
  const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
  
  try {
    // Main logic
    const value = sheet.getRange('B6').getValue();
    
    if (!value) {
      throw new Error('B6 is empty');
    }
    
    // Process value
    const result = processValue(value);
    
    // Update sheet
    sheet.getRange('A4').setValue('✅ Success');
    
  } catch (error) {
    // Error handling
    Logger.log('Error in robustFunction: ' + error);
    sheet.getRange('A4').setValue('❌ Error: ' + error.message);
    
    // Optional: Show dialog
    Browser.msgBox('Error', error.message, Browser.Buttons.OK);
  }
}
```

### Common Errors

**1. Range Not Found**
```javascript
// ❌ BAD: Will throw if sheet doesn't exist
const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
const value = sheet.getRange('B6').getValue();

// ✅ GOOD: Check sheet exists
const sheet = SpreadsheetApp.getActive().getSheetByName('BESS');
if (!sheet) {
  Browser.msgBox('Error', 'BESS sheet not found', Browser.Buttons.OK);
  return;
}
```

**2. URL Fetch Timeout**
```javascript
// Add timeout to options
const options = {
  'method': 'post',
  'contentType': 'application/json',
  'payload': JSON.stringify(data),
  'muteHttpExceptions': true,
  'timeout': 30000  // 30 seconds
};
```

**3. Invalid JSON**
```javascript
try {
  const data = JSON.parse(response.getContentText());
} catch (error) {
  Logger.log('Invalid JSON: ' + response.getContentText());
  throw new Error('Invalid response from API');
}
```

---

## 🐛 Troubleshooting

### Menu Not Appearing

**Symptom:** "🔋 BESS Tools" menu doesn't show

**Solutions:**
1. Refresh page (Cmd+R)
2. Check Apps Script deployed
3. Verify `onOpen()` function exists
4. Check for JavaScript errors:
   - View → Logs
   - Look for error messages

### Function Not Found Error

**Symptom:** "Script function refreshDnoLookup could not be found"

**Cause:** Function name mismatch or not deployed

**Solution:**
```javascript
// Ensure function exists and matches menu
function refreshDnoLookup() {  // ← Must match menu item
  refreshDnoData();
}
```

### Auto-Trigger Not Working

**Symptom:** Editing B6 doesn't trigger DNO lookup

**Debug Steps:**
1. Check `onEdit()` function exists
2. Test manually:
   ```javascript
   function testTrigger() {
     refreshDnoData();
   }
   ```
3. Check execution log:
   - View → Executions
   - Look for `onEdit` entries

### BigQuery Timeout

**Symptom:** "Request timed out" when fetching DNO data

**Solutions:**
1. Increase timeout in UrlFetchApp options
2. Check Vercel proxy is running
3. Verify BigQuery project accessible
4. Use simpler query

### Rate Limit Exceeded

**Symptom:** "429 Too Many Requests"

**Solutions:**
1. Add delays between requests:
   ```javascript
   Utilities.sleep(1000);  // 1 second delay
   ```
2. Batch operations
3. Cache results when possible

---

## 📝 Best Practices

### 1. Use Status Indicator
Always update cell A4 with operation status:
```javascript
sheet.getRange('A4').setValue('⏳ Processing...');
// ... do work ...
sheet.getRange('A4').setValue('✅ Complete');
```

### 2. Validate Inputs
```javascript
if (!value || value === '') {
  throw new Error('Value required');
}

if (typeof value !== 'number') {
  throw new Error('Number expected');
}
```

### 3. Use Flush for Real-time Updates
```javascript
sheet.getRange('A4').setValue('⏳ Loading...');
SpreadsheetApp.flush();  // Force immediate display
// ... long operation ...
```

### 4. Log Important Events
```javascript
Logger.log('DNO lookup started for MPAN: ' + mpanId);
Logger.log('Response received: ' + JSON.stringify(data));
```

### 5. Handle Async Operations
```javascript
// Use Utilities.sleep() for delays
Utilities.sleep(1000);  // Wait 1 second

// Don't block UI unnecessarily
// Keep operations under 30 seconds
```

---

**Next Steps:**
- [API Reference](API_REFERENCE.md) - Detailed function signatures
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues & fixes
- [Architecture](ARCHITECTURE.md) - System design
