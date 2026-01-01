# 🚀 Search API Auto-Execution - Setup Complete

**Date**: December 31, 2025  
**Status**: ✅ **READY FOR TESTING**

---

## 🎯 Problem Solved

**Before**: Apps Script showed command dialog → User manually copied command → User ran in terminal  
**After**: Apps Script calls Flask API → Search executes automatically → Results written directly to sheet ✨

---

## 📁 Files Created

### 1. **search_api_server.py** (Flask API Server)
- Endpoint: `http://localhost:5002/search`
- Accepts JSON search criteria from Apps Script
- Executes `advanced_search_tool_enhanced.py`
- Returns results in JSON format

### 2. **search_interface.gs** (Updated Apps Script)
- Added `API_ENDPOINT` configuration
- `onSearchButtonClick()` now tries API first
- New `executeSearchViaAPI()` function
- Falls back to manual command if API unavailable

### 3. **start_search_api.sh** (Quick Start Script)
- Installs Flask dependencies
- Starts API server on port 5002
- Runs in background with logging

---

## 🚀 Quick Start Guide

### Step 1: Start the API Server

```bash
# Make script executable (already done)
chmod +x start_search_api.sh

# Start server
./start_search_api.sh

# Output:
# ✅ Server started! PID: 12345
# 📊 Monitor logs: tail -f logs/search_api.log
```

**Verify Server Running**:
```bash
# Check health endpoint
curl http://localhost:5002/health

# Expected output:
# {"status":"ok","service":"Search API Server","timestamp":"2025-12-31T..."}
```

---

### Step 2: Update Apps Script (if needed)

If testing locally, no changes needed (already configured for `localhost:5002`).

For **remote access** (Google Apps Script runs on Google servers):

1. Install ngrok:
```bash
# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Start tunnel
ngrok http 5002
```

2. Update `search_interface.gs`:
```javascript
// Change this line (line ~12):
var API_ENDPOINT = 'http://localhost:5002/search';

// To your ngrok URL:
var API_ENDPOINT = 'https://abc123.ngrok.io/search';
```

---

### Step 3: Install Updated Apps Script

1. Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
2. Go to **Extensions > Apps Script**
3. Replace `Code.gs` with `search_interface.gs` content
4. Save (Ctrl+S)
5. Refresh spreadsheet

---

### Step 4: Test Automatic Search

1. In Search sheet, fill criteria:
   - **Record Type**: Generator (or Battery, Wind, etc.)
   - **CUSC/BSC Role**: Virtual Lead Party (VLP)
   - **Fuel Type**: Battery Storage

2. Click **🔍 Search Tools > 🔍 Run Search**

3. **Expected Behavior**:
   - Shows: "🔍 Executing search... Please wait"
   - API executes search automatically
   - Results written to rows 25+
   - Shows: "✅ Search Complete! Results: 15 records found"

4. **Fallback (if API unavailable)**:
   - Shows command dialog (old behavior)
   - User manually runs command in terminal

---

## 🔧 API Endpoints

### POST /search
Execute search with criteria

**Request**:
```json
{
  "party": "Drax",
  "type": "BM Unit",
  "role": "VLP",
  "bmu": "E_FARNB-1",
  "organization": "Flexgen",
  "from": "01/01/2025",
  "to": "31/12/2025",
  "cap_min": 10,
  "cap_max": 100,
  "gsp": "_A - Eastern (EPN)",
  "dno": "EPN - UK Power Networks Eastern",
  "voltage": "HV (11 kV)"
}
```

**Response**:
```json
{
  "success": true,
  "results": [
    {
      "type": "BM Unit",
      "id": "E_FARNB-1",
      "name": "Farnborough BESS",
      "role": "VLP",
      "organization": "Flexgen",
      "extra": "Battery Storage",
      "capacity": "49.9",
      "fuel": "Battery",
      "status": "Active",
      "source": "BigQuery",
      "score": "100"
    }
  ],
  "count": 1,
  "timestamp": "2025-12-31T10:30:00"
}
```

### GET /health
Health check

**Response**:
```json
{
  "status": "ok",
  "service": "Search API Server",
  "timestamp": "2025-12-31T10:30:00"
}
```

### POST /search/validate
Validate criteria without executing

**Response**:
```json
{
  "valid": true,
  "warnings": [],
  "command": "python3 advanced_search_tool_enhanced.py --party \"Drax\" --type \"BM Unit\""
}
```

---

## 📋 Next Todos

### ✅ TODO #24: Enable Automatic Search Execution ✅ **COMPLETE**
- ✅ Created Flask API server (`search_api_server.py`)
- ✅ Updated Apps Script to call API automatically
- ✅ Added fallback to manual command if API unavailable
- ✅ Created start script (`start_search_api.sh`)

---

### ⏳ TODO #25: Deploy Search API to Production Server
**Goal**: Make API accessible from Google Apps Script (which runs on Google servers)

**Options**:

**Option 1: ngrok Tunnel** (Quick, for testing)
```bash
# Install ngrok
ngrok http 5002

# Update Apps Script with ngrok URL:
var API_ENDPOINT = 'https://abc123.ngrok.io/search';
```

**Option 2: Deploy to AlmaLinux Server** (Production)
```bash
# SSH to server
ssh root@94.237.55.234

# Install dependencies
pip3 install flask flask-cors

# Copy files
scp search_api_server.py root@94.237.55.234:/opt/search-api/
scp advanced_search_tool_enhanced.py root@94.237.55.234:/opt/search-api/

# Create systemd service
sudo nano /etc/systemd/system/search-api.service

# Start service
sudo systemctl start search-api
sudo systemctl enable search-api

# Update Apps Script:
var API_ENDPOINT = 'http://94.237.55.234:5002/search';
```

**Option 3: Deploy to Vercel/Railway** (Serverless)
- More complex (requires FastAPI/async conversion)
- Better for scale
- See: VERCEL_DEPLOYMENT_GUIDE.md

---

### ⏳ TODO #26: Add GSP-DNO Dynamic Linking (from previous todos)
**Goal**: When user selects GSP Region, auto-select matching DNO AREA

**Implementation**:
1. Add `onEdit()` trigger to Apps Script
2. Extract DNO ID from GSP selection
3. Auto-populate DNO AREA dropdown
4. See: `SEARCH_ANALYSIS_INTEGRATION_TODOS.md` #19-23

---

### ⏳ TODO #27: Add Progress Indicator for Long Searches
**Goal**: Show progress bar while search executes

**Implementation**:
```javascript
// In search_interface.gs
function executeSearchViaAPI(criteria) {
  var ui = SpreadsheetApp.getUi();
  
  // Show progress sidebar
  var html = HtmlService.createHtmlOutput(
    '<div id="progress">' +
    '<h3>🔍 Searching...</h3>' +
    '<progress id="bar" max="100" value="0"></progress>' +
    '<p id="status">Initializing...</p>' +
    '</div>' +
    '<script>' +
    'setInterval(function() {' +
    '  document.getElementById("bar").value += 10;' +
    '  if (document.getElementById("bar").value > 100) {' +
    '    document.getElementById("bar").value = 0;' +
    '  }' +
    '}, 500);' +
    '</script>'
  );
  
  ui.showSidebar(html);
  
  // Execute search...
  
  // Close sidebar
  ui.close();
}
```

---

### ⏳ TODO #28: Add Search Result Caching
**Goal**: Cache recent searches to speed up repeated queries

**Implementation**:
```python
# In search_api_server.py
import hashlib
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(criteria_hash):
    # Execute search
    # Return results
    pass

@app.route('/search', methods=['POST'])
def execute_search():
    # Create hash of criteria
    criteria_str = json.dumps(request.get_json(), sort_keys=True)
    criteria_hash = hashlib.md5(criteria_str.encode()).hexdigest()
    
    # Check cache
    cached_result = cached_search(criteria_hash)
    if cached_result:
        return jsonify(cached_result)
    
    # Execute search...
```

---

### ⏳ TODO #29: Add Search History
**Goal**: Track recent searches in hidden sheet

**Implementation**:
1. Create "SearchHistory" hidden sheet
2. Log each search with timestamp, criteria, result count
3. Add "Recent Searches" dropdown to load previous queries

---

### ⏳ TODO #30: Add Export to CSV/Excel
**Goal**: Export search results to file

**Implementation**:
```javascript
function exportSearchResults() {
  var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Search');
  var lastRow = sheet.getLastRow();
  
  if (lastRow < 25) {
    SpreadsheetApp.getUi().alert('No results to export');
    return;
  }
  
  var data = sheet.getRange(24, 1, lastRow - 23, 11).getValues();
  
  // Create CSV
  var csv = data.map(function(row) {
    return row.map(function(cell) {
      return '"' + cell + '"';
    }).join(',');
  }).join('\n');
  
  // Download via blob
  var blob = Utilities.newBlob(csv, 'text/csv', 'search_results.csv');
  DriveApp.createFile(blob);
  
  SpreadsheetApp.getUi().alert('✅ Exported to Google Drive: search_results.csv');
}
```

---

## 🔧 Troubleshooting

### Issue 1: "API call failed: Failed to fetch"
**Cause**: API server not running or wrong endpoint  
**Fix**:
```bash
# Check server is running
curl http://localhost:5002/health

# If not, start it
./start_search_api.sh

# Check logs
tail -f logs/search_api.log
```

---

### Issue 2: "Search timeout (>30s)"
**Cause**: Large result set or slow BigQuery query  
**Fix**:
```python
# In search_api_server.py, increase timeout
result = subprocess.run(
    args,
    capture_output=True,
    text=True,
    timeout=60  # Increased from 30
)
```

---

### Issue 3: Apps Script shows command dialog instead of auto-executing
**Cause**: API endpoint not accessible (expected behavior for fallback)  
**Fix**:
1. Verify API running: `curl http://localhost:5002/health`
2. Check Apps Script console for error: **View > Logs**
3. Update `API_ENDPOINT` to correct URL
4. For Google Apps Script, use ngrok or deploy to public server

---

### Issue 4: Results not appearing in sheet
**Cause**: Wrong sheet name or range  
**Fix**:
```javascript
// In search_interface.gs, verify:
var sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName('Search');
// Should match your sheet name exactly (case-sensitive)
```

---

## 📊 Testing Checklist

- [ ] API server starts without errors
- [ ] Health endpoint returns OK
- [ ] Apps Script calls API successfully
- [ ] Search results written to rows 25+
- [ ] Timestamp updated in E22
- [ ] Result count shown in J22
- [ ] Fallback to manual command works if API down
- [ ] GSP/DNO filters working
- [ ] Generator type maps to BM Unit correctly
- [ ] Search with no criteria returns all results

---

## 🎯 Summary

**Before**: Manual workflow (copy command → terminal → wait)  
**After**: ✨ Automatic execution (click Search → results appear!)

**Next Steps**:
1. Start API server: `./start_search_api.sh`
2. Test from Google Sheets
3. Deploy to production server (ngrok/AlmaLinux)
4. Implement GSP-DNO dynamic linking (TODO #26)
5. Add progress indicator (TODO #27)

---

*Last Updated: December 31, 2025*  
*Implementation By: GitHub Copilot (Claude Sonnet 4.5)*  
*Project: GB Power Market JJ - Search Auto-Execution*
