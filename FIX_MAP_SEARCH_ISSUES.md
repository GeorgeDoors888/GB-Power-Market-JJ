# 🔧 MAP SIDEBAR & SEARCH FUNCTION - DIAGNOSIS & FIX GUIDE

## 📊 Summary

**Date**: 1 January 2026  
**Issues Reported**:
1. Map sidebar opens but buttons do nothing when clicked
2. Search function not working

---

## 🗺️ ISSUE 1: MAP SIDEBAR BUTTONS NON-FUNCTIONAL

### Current Status
✅ **Working**:
- Sidebar displays correctly
- HTML file complete (244 lines, 9,337 bytes)
- BigQuery API accessible (14 DNO regions, 333 GSP regions)
- API key stored in Script Properties
- All OAuth scopes authorized

❌ **Not Working**:
- Clicking "Show DNO Regions" → nothing happens
- Clicking "Show GSP Regions" → nothing happens
- No map displays
- No error messages visible

### Root Cause Analysis

**Most Likely**: Google Maps JavaScript API not enabled in Google Cloud Console

The sidebar HTML loads successfully, but when it tries to load the Maps JavaScript API:
```javascript
s.src = `https://maps.googleapis.com/maps/api/js?key=${key}&callback=initMap&v=weekly`;
```

If the Maps JavaScript API is not enabled, the script loads but the `initMap()` callback never fires, leaving the `map` variable undefined. When you click buttons, they call `loadLayer()` which tries to use the undefined `map`, causing silent failures.

### 🔍 DIAGNOSTIC STEPS

#### Step 1: Test Maps API URL Directly
Open this URL in your browser:
```
https://maps.googleapis.com/maps/api/js?key=AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0&v=weekly
```

**Expected Results**:
- ✅ **JavaScript code visible** → API is working (unlikely based on symptoms)
- ❌ **"ApiNotActivatedMapError"** → Maps JavaScript API not enabled (MOST LIKELY)
- ❌ **"RefererNotAllowedMapError"** → Domain restrictions blocking
- ❌ **"InvalidKeyMapError"** → API key wrong/expired

#### Step 2: Run Diagnostic Script
1. Open your Apps Script project
2. Copy `diagnostic_map_search.gs` to your project
3. Run function: `diagnosticComplete()`
4. Check **View > Execution Log** for full report

Quick tests:
- `testMapSidebarQuick()` - Opens sidebar and logs status
- `testMapsApiUrl()` - Tests Maps API URL directly from Apps Script
- `testSearchFunction()` - Tests search API endpoint

### ✅ FIXES

#### Fix 1: Enable Maps JavaScript API (PRIMARY FIX)

**Option A: Via Direct Links**
1. Open: https://console.cloud.google.com/apis/library/maps-javascript-api.googleapis.com?project=inner-cinema-476211-u9
2. Click **ENABLE** button
3. Wait 2-3 minutes for propagation

Also enable Maps Backend API:
1. Open: https://console.cloud.google.com/apis/library/maps-backend.googleapis.com?project=inner-cinema-476211-u9
2. Click **ENABLE** button

**Option B: Via Console Navigation**
1. Go to: https://console.cloud.google.com/apis/library?project=inner-cinema-476211-u9
2. Search: "Maps JavaScript API"
3. Click on "Maps JavaScript API"
4. Click **ENABLE**

#### Fix 2: Remove API Key Restrictions (IF Fix 1 doesn't work)

1. Open: https://console.cloud.google.com/apis/credentials?project=inner-cinema-476211-u9
2. Find API key: `AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0`
3. Click the key to edit

**API Restrictions**:
- Change from "Restrict key" to **"Don't restrict key"**
- OR select **"Maps JavaScript API"** from the dropdown

**Application Restrictions**:
- Change to **"None"**
- OR add `script.google.com/*` to "HTTP referrers (web sites)"

4. Click **SAVE**
5. Wait 2-3 minutes for changes to propagate

#### Fix 3: Check Browser Console (IF still not working)

1. Open Google Sheets with your spreadsheet
2. Press **F12** to open Developer Tools
3. Go to **Console** tab
4. Click: 🗺️ Geographic Map → Show DNO & GSP Boundaries
5. Look for errors (red text) or warnings (yellow text)
6. Copy ANY messages mentioning "google.maps" or "API"

Common errors:
```
Google Maps JavaScript API error: ApiNotActivatedMapError
Google Maps JavaScript API error: RefererNotAllowedMapError
google.maps is not defined
```

### 🧪 TESTING AFTER FIX

1. Refresh your Google Sheet (reload page)
2. Click: 🗺️ Geographic Map → Show DNO & GSP Boundaries
3. Wait 5-10 seconds for map to initialize
4. Click **"Show DNO Regions (14)"**
5. Expected result: Map displays with 14 colored regions

**What You Should See**:
- Interactive Google Map centered on UK (54.5°N, 3.5°W)
- 14 blue DNO regions with borders
- Info panel: "✅ Loaded 14 DNO features. Click any region for details."
- Clicking a region shows details (DNO name, code, GSP group)

---

## 🔍 ISSUE 2: SEARCH FUNCTION NOT WORKING

### Current Status
✅ **Working**:
- Search sheet exists in spreadsheet
- Search interface code deployed (`search_interface.gs`)
- Menu item "🔍 Search Tools" available
- Can read search criteria from cells

❌ **Not Working**:
- Search returns no results
- API endpoint not responding
- Button clicks produce errors or no action

### Root Cause Analysis

**Most Likely**: Backend API server not running or ngrok tunnel expired

The search interface relies on an external API endpoint:
```javascript
var API_ENDPOINT = 'https://a92f6deceb5e.ngrok-free.app/search';
```

Issues:
1. **ngrok tunnel expired** - Free ngrok tunnels expire after 2 hours or restart
2. **Backend server not running** - Python FastAPI/Flask server not started
3. **API endpoint changed** - New ngrok URL not updated in script

### 🔍 DIAGNOSTIC STEPS

#### Step 1: Check Backend Server Status

On your AlmaLinux server (94.237.55.234):
```bash
# Check if search backend is running
ps aux | grep -E "(api_gateway|codex-server|advanced_search)"

# Check if ngrok is running
ps aux | grep ngrok

# Check logs
tail -f /path/to/search/backend/logs/*.log
```

#### Step 2: Test API Endpoint Manually

Test the current endpoint:
```bash
curl -X GET https://a92f6deceb5e.ngrok-free.app/search

# Or test POST with sample data
curl -X POST https://a92f6deceb5e.ngrok-free.app/search \
  -H "Content-Type: application/json" \
  -d '{"party": "Drax", "type": "Generator"}'
```

Expected response: JSON with search results or error message

#### Step 3: Run Search Diagnostic in Apps Script

1. Open Apps Script project
2. Run function: `testSearchFunction()`
3. Check **View > Execution Log**

Look for:
- ✅ "Search API is accessible" → Backend working
- ❌ "Cannot reach search API" → Backend down or URL wrong
- ❌ "API returned: 404" → Endpoint not found

### ✅ FIXES

#### Fix 1: Start/Restart Backend Server

**If using FastAPI backend** (`api_gateway.py`):
```bash
cd /home/george/GB-Power-Market-JJ
python3 api_gateway.py
```

**If using codex-server**:
```bash
cd /home/george/GB-Power-Market-JJ/codex-server
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**If using Railway.app deployment**:
1. Check: https://railway.app/dashboard
2. Verify service is running
3. Check deployment logs for errors

#### Fix 2: Update ngrok Tunnel URL

**Start ngrok** (if using local server):
```bash
# For port 8000 (FastAPI default)
ngrok http 8000

# For port 5000 (Flask default)
ngrok http 5000
```

ngrok will output:
```
Forwarding   https://a92f6deceb5e.ngrok-free.app -> http://localhost:8000
```

**Update API endpoint in Apps Script**:
1. Open `search_interface.gs`
2. Find line ~12: `var API_ENDPOINT = 'https://...';`
3. Replace with new ngrok URL
4. Save and re-run search

#### Fix 3: Use Alternative Search Method (Fallback)

If API backend unavailable, search can run via command-line:

1. Click: 🔍 Search Tools → Run Search
2. Apps Script will show a dialog with the command to run
3. Copy command and run in terminal:
```bash
cd /home/george/GB-Power-Market-JJ
python3 advanced_search_tool_enhanced.py --party "Drax" --type "Generator"
```

Results will output to console or CSV file.

#### Fix 4: Direct BigQuery Search (Alternative)

If backend completely unavailable, query BigQuery directly:

```python
from google.cloud import bigquery

client = bigquery.Client(project="inner-cinema-476211-u9", location="US")

query = """
SELECT 
  party_name,
  bsc_party_id,
  effective_from,
  role_code
FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_bsc_parties`
WHERE party_name LIKE '%Drax%'
  AND effective_from <= CURRENT_DATE()
  AND (effective_to IS NULL OR effective_to >= CURRENT_DATE())
ORDER BY party_name
"""

df = client.query(query).to_dataframe()
print(df)
```

### 🧪 TESTING AFTER FIX

1. Open Google Sheets
2. Go to "Search" sheet
3. Enter search criteria:
   - Party Name: `Drax`
   - From Date: `01/01/2025`
   - To Date: `31/12/2025`
4. Click: 🔍 Search Tools → Run Search
5. Expected result: Results appear in rows 25+ with matching records

**What You Should See**:
- Results table populated (11 columns)
- Multiple rows for Drax (BSC Party, BM Units, generators)
- Match scores in column K
- Clicking a row updates Party Details panel (columns L-M)

---

## 📝 VERIFICATION CHECKLIST

### Map Sidebar
- [ ] Maps JavaScript API enabled in Google Cloud Console
- [ ] Maps Backend API enabled
- [ ] API key has no domain restrictions (or allows script.google.com)
- [ ] Browser console shows no "google.maps" errors
- [ ] Sidebar opens without errors
- [ ] Map displays with zoom controls
- [ ] "Show DNO Regions" button loads 14 blue regions
- [ ] "Show GSP Regions" button loads 333 green regions
- [ ] Clicking a region shows details in info panel

### Search Function
- [ ] Backend server running (ps aux shows process)
- [ ] ngrok tunnel active (if using ngrok)
- [ ] API endpoint URL is current in search_interface.gs
- [ ] Test curl shows API responding
- [ ] Apps Script can reach API endpoint
- [ ] Search sheet exists with correct layout
- [ ] Search criteria can be entered
- [ ] "Run Search" button executes without error
- [ ] Results populate in rows 25+
- [ ] Party Details panel updates when clicking results

---

## 🆘 STILL NOT WORKING?

### Get Help

**Collect diagnostic info**:
```javascript
// Run in Apps Script
diagnosticComplete()
```

**Copy from View > Execution Log**:
- All ✅ PASS and ❌ FAIL messages
- Any error messages
- API response codes

**Browser Console** (F12):
- Copy ALL red error messages
- Copy any yellow warnings mentioning "maps" or "google"
- Take screenshot of Console tab

**Backend Server**:
```bash
# Check server status
systemctl status api-gateway  # or your service name

# Check logs
journalctl -u api-gateway -n 100

# Test connectivity
curl -v http://localhost:8000/health
```

**Contact**:
- Email: george@upowerenergy.uk
- Include: Diagnostic output, browser console errors, server logs

---

## 📚 RELATED FILES

**Map Sidebar**:
- `/home/george/GB-Power-Market-JJ/map_sidebar.gs` - Backend functions
- `/home/george/GB-Power-Market-JJ/appsscript_v3/map_sidebarh.html` - Frontend HTML
- `/home/george/GB-Power-Market-JJ/diagnostic_map_search.gs` - Diagnostic script

**Search Interface**:
- `/home/george/GB-Power-Market-JJ/search_interface.gs` - Apps Script handlers
- `/home/george/GB-Power-Market-JJ/api_gateway.py` - Backend API server
- `/home/george/GB-Power-Market-JJ/codex-server/` - Alternative backend
- `/home/george/GB-Power-Market-JJ/advanced_search_tool_enhanced.py` - Command-line search

**Configuration**:
- Google Cloud Console: https://console.cloud.google.com/?project=inner-cinema-476211-u9
- Apps Script Project: 1KlgBiFBGXfub87ACCfx7y9QugHbT46Mv3bgWtpQ38FvroSTsl8CEiXUz
- Google Sheet: 1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc

---

**Last Updated**: 1 January 2026  
**Status**: Awaiting user action to enable Maps JavaScript API and start backend server
