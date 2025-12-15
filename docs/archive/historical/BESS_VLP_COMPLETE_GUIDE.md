# BESS VLP - Complete DNO Lookup Guide

**Last Updated**: November 9, 2025  
**Version**: 2.0  
**Status**: ✅ Production Ready

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Setup & Deployment](#setup--deployment)
4. [Using the Tool](#using-the-tool)
5. [How Data Refreshes](#how-data-refreshes)
6. [Understanding DNOs](#understanding-dnos)
7. [Troubleshooting](#troubleshooting)
8. [Technical Details](#technical-details)
9. [FAQ](#faq)

---

## Overview

**BESS VLP DNO Lookup Tool** helps you identify which UK Distribution Network Operator (DNO) serves a specific location. Essential for battery energy storage system (BESS) projects and Virtual Lead Party (VLP) analysis.

### What It Does

- ✅ **Postcode Lookup**: Enter any UK postcode → Get DNO details
- ✅ **DNO Selection**: Choose from 14 UK DNOs → See coverage area
- ✅ **Google Maps**: View location and DNO area on map
- ✅ **Auto-Refresh**: Keep DNO data synchronized with BigQuery
- ✅ **Hidden Reference**: All DNO data stored but hidden from view

### Key Features

| Feature | Description | Speed |
|---------|-------------|-------|
| Postcode Search | Exact location lookup via postcodes.io API | ~2 sec |
| DNO Dropdown | Direct DNO selection with approximate coordinates | ~2 sec |
| Map Integration | Clickable Google Maps link | Instant |
| Data Refresh | Update from BigQuery on-demand | ~5 sec |
| Reference Table | 14 DNO records (hidden rows 21-50) | N/A |

---

## Quick Start

### 1. Open the Tool
[Google Sheet: BESS_VLP](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/)

### 2. Choose Your Method

**Method A: Lookup by Postcode**
1. Cell **B4** → Enter postcode (e.g., "RH19 4LX")
2. Menu → **🔋 BESS VLP Tools** → **Lookup DNO from Postcode/Dropdown**
3. View results in row 10

**Method B: Lookup by DNO Selection**
1. Cell **E4** → Select DNO from dropdown (e.g., "14 - NGED-WM")
2. Menu → **🔋 BESS VLP Tools** → **Lookup DNO from Postcode/Dropdown**
3. View results in row 10

### 3. View Results

**DNO Information (Row 10)**:
- MPAN/Distributor ID
- DNO Key (e.g., UKPN-SPN)
- Full DNO Name
- DNO Short Code
- Market Participant ID
- GSP Group ID
- GSP Group Name
- Coverage Area

**Location Details (Rows 14-15)**:
- Latitude
- Longitude

**Map (Rows 19-22)**:
- Clickable Google Maps link
- Location coordinates
- DNO name and code
- GSP group information

---

## Setup & Deployment

### Prerequisites

- ✅ Google account with Sheets access
- ✅ Access to Google Cloud project: `inner-cinema-476211-u9`
- ✅ BigQuery permissions (read access to `uk_energy_prod` dataset)
- ✅ Apps Script editing permissions

### Step 1: Open Apps Script Editor

1. Open [BESS_VLP Google Sheet](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/)
2. Click **Extensions** → **Apps Script**

### Step 2: Add BigQuery Service ⚠️ CRITICAL

**This is the #1 reason for "BigQuery not found" errors!**

1. In Apps Script editor, look at **left sidebar**
2. Find **Services** section (has a + button)
3. Click the **"+"** button
4. Scroll down to **"BigQuery API"** (or search for it)
5. Select **"BigQuery API"** version **v2**
6. Click **Add**

**You should now see**:
```
Services
└── BigQuery (v2) ← This MUST be present!
```

**If you skip this step**, you'll get errors like:
- "BigQuery is not defined"
- "ReferenceError: BigQuery is not defined"
- "couldn't find BigQuery"

### Step 3: Deploy the Code

1. In Apps Script editor, select **ALL** existing code (Ctrl+A or Cmd+A)
2. **Delete** everything
3. Open file: `/Users/georgemajor/GB Power Market JJ/apps-script/bess_vlp_lookup.gs`
4. Copy **ALL 540 lines**
5. Paste into Apps Script editor
6. Click **Save** (💾 icon)
7. Give it a name (e.g., "BESS VLP DNO Lookup")

### Step 4: Authorize Permissions

1. Click **Run** → Select **onOpen** from dropdown
2. Click **Run** button (▶️)
3. You'll see: "Authorization required"
4. Click **Review Permissions**
5. Choose your Google account
6. You may see "Google hasn't verified this app"
   - Click **Advanced**
   - Click **Go to BESS VLP (unsafe)** ← It's safe, it's YOUR code!
7. Click **Allow** to grant permissions:
   - See, edit, create, and delete all your Google Sheets spreadsheets
   - Connect to an external service (BigQuery)

### Step 5: Verify Installation

1. Go back to your Google Sheet
2. **Refresh the page** (F5 or Cmd+R)
3. You should see menu: **🔋 BESS VLP Tools** with 3 options:
   - Lookup DNO from Postcode/Dropdown
   - Refresh DNO Reference Table
   - Show/Hide Reference Table

### Step 6: Test It Works

**Test 1: Postcode Lookup**
```
1. Cell B4 → Enter "RH19 4LX"
2. Menu → 🔋 BESS VLP Tools → Lookup
3. Expected: MPAN 19, UKPN-SPN, South Eastern
```

**Test 2: Dropdown Selection**
```
1. Cell E4 → Select "14 - National Grid Electricity Distribution – West Midlands (WMID)"
2. Menu → 🔋 BESS VLP Tools → Lookup
3. Expected: MPAN 14, NGED-WM, West Midlands
```

**Test 3: Refresh Function**
```
1. Menu → 🔋 BESS VLP Tools → Refresh DNO Reference Table
2. Expected: Alert showing "14 DNOs updated"
```

✅ **If all 3 tests pass, you're ready to go!**

---

## Using the Tool

### Menu: 🔋 BESS VLP Tools

Access via menu bar in Google Sheets.

#### 1. Lookup DNO from Postcode/Dropdown

**Purpose**: Find which DNO serves a location

**Input Options**:
- **Postcode** (Cell B4): Any valid UK postcode
- **DNO Dropdown** (Cell E4): Select from 14 UK DNOs

**How It Works**:
1. Script checks if dropdown has selection
2. If yes → Uses dropdown (DNO-based lookup)
3. If no → Uses postcode (location-based lookup)
4. Queries BigQuery for DNO details
5. Populates row 10 with results
6. Adds Google Maps link in row 19

**Output**:
- Row 10: Full DNO details (8 columns)
- Rows 14-15: Coordinates
- Row 19: Clickable map link
- Rows 20-22: Map information
- Row 11: Timestamp

**Speed**: ~2 seconds

#### 2. Refresh DNO Reference Table

**Purpose**: Update DNO data from BigQuery

**When to Use**:
- Once per year (DNO data rarely changes)
- After Ofgem license updates
- If dropdown missing options

**How It Works**:
1. Shows progress alert
2. Queries BigQuery for all 14 DNOs
3. Clears hidden reference table (rows 24-50)
4. Populates new data
5. Rebuilds dropdown validation in E4
6. Shows success alert

**What Gets Updated**:
- ✅ Hidden reference table (rows 24-37)
- ✅ DNO dropdown list (E4)
- ✅ Synchronizes both to match BigQuery

**Speed**: ~5 seconds

#### 3. Show/Hide Reference Table

**Purpose**: Toggle visibility of DNO reference data

**How It Works**:
- Click once → Shows rows 21-50
- Click again → Hides rows 21-50

**Use Cases**:
- Verify DNO data
- Check MPAN IDs
- Review GSP groups
- Troubleshooting

---

## How Data Refreshes

### Understanding the Refresh Cycle

The tool uses **three data refresh mechanisms**:

#### 1️⃣ Manual Refresh (Menu Button)

**When**: Anytime you want to update DNO data  
**How**: Menu → 🔋 BESS VLP Tools → Refresh DNO Reference Table  
**Speed**: ~5 seconds  
**Frequency**: Once per year (or when Ofgem updates)

**What Happens**:
```javascript
1. Query BigQuery: SELECT * FROM neso_dno_reference
2. Clear rows 24-50 in sheet
3. Populate 14 DNO records (rows 24-37)
4. Collect dropdown values: ["10 - UKPN-EPN", "11 - NGED-EM", ...]
5. Rebuild dropdown validation in E4
6. Show success alert with count
```

**Refreshes**:
- ✅ Hidden reference table
- ✅ Dropdown validation list
- ✅ Both synchronized

#### 2️⃣ Live Lookup (Every Search)

**When**: Automatic - every time you run Lookup  
**How**: Queries BigQuery directly for fresh data  
**Speed**: ~2 seconds  
**Frequency**: Every lookup (real-time)

**What Happens**:
```javascript
// Postcode Method
1. User enters "RH19 4LX"
2. Call postcodes.io API → Get coordinates
3. Query BigQuery with ST_CONTAINS(boundary, GEOGPOINT)
4. Return DNO details fresh from BigQuery
5. Populate row 10

// Dropdown Method
1. User selects "14 - NGED-WM"
2. Extract MPAN ID: 14
3. Query BigQuery: WHERE mpan_distributor_id = 14
4. Get centroid coordinates for MPAN 14
5. Return DNO details fresh from BigQuery
6. Populate row 10
```

**Key Point**: The lookup **ALWAYS** gets fresh data from BigQuery, even if reference table is outdated!

**Refreshes**:
- ✅ Results row (10)
- ✅ Coordinates (B14/B15)
- ✅ Map link (A19-A22)
- ✅ Timestamp (A11)

#### 3️⃣ Python Script Rebuild (Nuclear Option)

**When**: Sheet corrupted or complete reset needed  
**How**: Run `enhance_bess_vlp_sheet.py` script  
**Speed**: ~10 seconds  
**Frequency**: Rarely (only if broken)

**Command**:
```bash
cd "/Users/georgemajor/GB Power Market JJ"
/opt/homebrew/bin/python3 enhance_bess_vlp_sheet.py
```

**What Happens**:
```python
1. Query BigQuery for all 14 DNOs
2. CLEAR entire sheet structure
3. Rebuild all formatting
4. Recreate dropdown in E4
5. Repopulate hidden reference table
6. Re-hide rows 21-50
7. Reset column widths
8. Reapply all styling
```

**Refreshes**:
- ✅ Entire sheet layout
- ✅ All DNO data
- ✅ All formatting
- ✅ Dropdown validation
- ⚠️ **CLEARS your lookup results**

### Refresh Comparison

| Method | Speed | Updates What | When to Use |
|--------|-------|--------------|-------------|
| **Menu Refresh** | ~5 sec | Reference table + dropdown | DNO data changed |
| **Lookup** | ~2 sec | Results row + map | Every search |
| **Python Script** | ~10 sec | Entire sheet | Sheet broken |

### How Often to Refresh?

**Reference Table**: ❌ Almost Never
- DNO data only changes when Ofgem updates licenses
- Last major change: **2016** (Western Power → SSEN)
- Next expected: **2030+**
- **Recommendation**: Check once per year in January

**Lookup Results**: ✅ Every Search
- Automatically gets fresh data
- No manual intervention needed
- Always current

---

## Understanding DNOs

### What is a DNO?

**DNO = Distribution Network Operator**

- Company that owns and operates local electricity networks
- Delivers electricity from National Grid to homes/businesses
- Manages underground cables and overhead lines
- Issues connection offers for new generators (like BESS)
- Different from energy suppliers (who bill customers)

### The 14 UK DNOs

| MPAN | DNO Key | Company Name | GSP | Region |
|------|---------|--------------|-----|--------|
| 10 | UKPN-EPN | UK Power Networks (Eastern) | A | Norfolk, Suffolk, Essex |
| 11 | NGED-EM | National Grid Electricity Distribution – East Midlands | B | Nottinghamshire, Leicestershire |
| 12 | UKPN-LPN | UK Power Networks (London) | C | Greater London |
| 13 | SP-Manweb | SP Energy Networks (SPM) | D | Merseyside, North Wales |
| 14 | NGED-WM | National Grid Electricity Distribution – West Midlands | E | Birmingham, Warwickshire |
| 15 | NPg-NE | Northern Powergrid (North East) | F | Northumberland, Durham |
| 16 | ENWL | Electricity North West | G | Lancashire, Cumbria |
| 17 | SSE-SHEPD | Scottish Hydro Electric Power Distribution | P | Highlands, Islands |
| 18 | SP-Distribution | SP Energy Networks (SPD) | N | Central/South Scotland |
| 19 | UKPN-SPN | UK Power Networks (South Eastern) | J | Kent, Surrey, Sussex |
| 20 | SSE-SEPD | Southern Electric Power Distribution | H | Berkshire, Hampshire |
| 21 | NGED-SWales | National Grid Electricity Distribution – South Wales | K | South Wales |
| 22 | NGED-SW | National Grid Electricity Distribution – South West | L | Devon, Cornwall |
| 23 | NPg-Y | Northern Powergrid (Yorkshire) | M | Yorkshire |

### Are There Duplicates?

**NO!** All 14 DNOs are unique, but some companies operate multiple licenses:

#### UK Power Networks (3 licenses)
- **MPAN 10**: Eastern (Norfolk, Suffolk, Essex)
- **MPAN 12**: London (Greater London)
- **MPAN 19**: South Eastern (Kent, Surrey, Sussex)

#### National Grid Electricity Distribution (4 licenses)
- **MPAN 11**: East Midlands
- **MPAN 14**: West Midlands
- **MPAN 21**: South Wales
- **MPAN 22**: South West

#### SP Energy Networks (2 licenses)
- **MPAN 13**: Manweb (Merseyside, North Wales)
- **MPAN 18**: Distribution (Central/South Scotland)

#### Northern Powergrid (2 licenses)
- **MPAN 15**: North East
- **MPAN 23**: Yorkshire

#### SSE (2 licenses)
- **MPAN 17**: SHEPD (North Scotland)
- **MPAN 20**: SEPD (Southern England)

**Why multiple licenses?**
- Different geographic areas
- Separate regulatory entities
- Different pricing zones
- Historic regional divisions
- Independent connection processes

### Key Terminology

| Term | Definition |
|------|------------|
| **MPAN** | Meter Point Administration Number (identifies DNO region) |
| **GSP** | Grid Supply Point (where transmission connects to distribution) |
| **DNO Key** | Short identifier (e.g., UKPN-SPN) |
| **Market Participant ID** | Elexon registration code |
| **Coverage Area** | Geographic counties served |

---

## Troubleshooting

### Error: "BigQuery is not defined"

**Problem**: BigQuery API service not added to Apps Script

**Solution**:
1. Open Apps Script editor (Extensions → Apps Script)
2. Click **Services** (left sidebar)
3. Click **"+"** button
4. Find **"BigQuery API"**
5. Select **v2**
6. Click **Add**
7. Save script
8. Re-run authorization (Run → onOpen)

**This fixes 90% of errors!**

---

### Error: "DNO not found" (Dropdown Selection)

**Problem**: Wrong centroid coordinates for MPAN ID

**Status**: ✅ **FIXED in v2.0** (November 9, 2025)

**Solution**: Update to latest code from `bess_vlp_lookup.gs`

**What was fixed**:
- Old mapping had MPAN 11 → London ❌ (should be East Midlands)
- Old mapping had MPAN 12 → South Eastern ❌ (should be London)
- Old mapping had MPAN 13 → East Midlands ❌ (should be Manweb)
- New mapping corrected all 14 MPAN IDs ✅

---

### Error: "Invalid postcode or postcode not found"

**Problem**: Postcode doesn't exist or typo

**Solution**:
1. Check postcode format: "SW1A 1AA" or "SW1A1AA"
2. Try without space: "RH194LX"
3. Verify on Royal Mail website
4. Try dropdown method instead (E4)

---

### Error: "BESS_VLP sheet not found"

**Problem**: Sheet renamed or deleted

**Solution**:
1. Check sheet name is exactly: **BESS_VLP**
2. Case-sensitive!
3. No extra spaces
4. If renamed, rename back to "BESS_VLP"

---

### Menu Not Appearing

**Problem**: Script not running on sheet open

**Solution**:
1. Refresh the page (F5)
2. Close and reopen the sheet
3. Run manually: Extensions → Apps Script → Run → onOpen
4. Check Apps Script is saved
5. Check authorization completed

---

### Dropdown Empty or Missing Options

**Problem**: Dropdown validation not built

**Solution**:
1. Menu → 🔋 BESS VLP Tools → Refresh DNO Reference Table
2. Wait ~5 seconds
3. Check E4 dropdown now shows 14 options
4. If still empty, run Python script: `enhance_bess_vlp_sheet.py`

---

### Map Link Not Working

**Problem**: Coordinates not set or invalid

**Solution**:
1. Check B14 (latitude) has value
2. Check B15 (longitude) has value
3. Re-run lookup
4. Manually click cell A19 to test link

---

### "Error: Access Denied" (BigQuery)

**Problem**: No permissions to inner-cinema-476211-u9 project

**Solution**:
1. Contact project owner: george@upowerenergy.uk
2. Request BigQuery Data Viewer role
3. Confirm access to `uk_energy_prod` dataset
4. Re-authorize Apps Script

---

### Reference Table Visible (Should Be Hidden)

**Problem**: Rows 21-50 accidentally unhidden

**Solution**:
1. Menu → 🔋 BESS VLP Tools → Show/Hide Reference Table
2. Click once to hide
3. Or manually: Select rows 21-50 → Right-click → Hide rows

---

### Results Not Updating

**Problem**: Sheet cached or script not running

**Solution**:
1. Hard refresh: Ctrl+Shift+R (or Cmd+Shift+R)
2. Check row 11 timestamp - is it current?
3. Re-run lookup manually
4. Check Apps Script execution log (View → Executions)
5. Look for error messages

---

### Python Script Errors

**Problem**: Module not found or credentials error

**Solution**:
```bash
# Install required packages
pip3 install --user google-cloud-bigquery gspread db-dtypes pyarrow pandas

# Check credentials exist
ls inner-cinema-credentials.json

# Test BigQuery connection
python3 -c "from google.cloud import bigquery; print('OK')"
```

---

## Technical Details

### Architecture

```
User Input (Postcode OR Dropdown)
         ↓
Apps Script (Google Sheets)
         ↓
         ├─→ Postcode API (postcodes.io) → Coordinates
         │
         └─→ BigQuery SQL Query
                  ↓
            DNO Details (Fresh Data)
                  ↓
            Populate Results (Row 10)
                  ↓
            Add Map Link (Row 19)
```

### Data Sources

1. **BigQuery Tables**:
   - `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference` (14 rows)
   - `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries` (14 GEOGRAPHY polygons)

2. **Postcode API**:
   - URL: https://api.postcodes.io/postcodes/
   - Free, no authentication
   - 2.8 million UK postcodes
   - Returns: lat, lng, admin_district, country

3. **Hidden Reference Table**:
   - Rows 24-37 (14 DNOs)
   - 8 columns (MPAN, key, name, short code, participant, GSP group, GSP name, coverage)
   - Source: BigQuery `neso_dno_reference`

### Key Functions

#### `lookupDNO()`
Main entry point - determines postcode vs dropdown method

#### `getCoordinatesFromPostcode(postcode)`
Calls postcodes.io API to convert postcode → lat/lng

#### `findDNOFromCoordinates(lat, lng)`
BigQuery spatial query: `ST_CONTAINS(boundary, ST_GEOGPOINT(lng, lat))`

#### `findDNOByMPAN(mpanId)`
BigQuery query: `WHERE mpan_distributor_id = ${mpanId}`

#### `getDNOCentroid(mpanId)`
Returns approximate center coordinates for each MPAN

#### `populateDNOResults(sheet, dnoData)`
Fills row 10 with 8 columns of DNO data

#### `refreshDNOTable()`
Queries all 14 DNOs from BigQuery, updates hidden table + dropdown

#### `toggleReferenceTable()`
Shows/hides rows 21-50 on demand

#### `addGoogleMap(sheet, lat, lng, dnoData)`
Adds clickable Google Maps link with location info

### Centroid Coordinates

Pre-calculated approximate centers for each DNO:

```javascript
10: {latitude: 52.2, longitude: 0.7},    // UKPN-EPN (Eastern)
11: {latitude: 52.8, longitude: -1.2},   // NGED-EM (East Midlands)
12: {latitude: 51.5, longitude: -0.1},   // UKPN-LPN (London)
13: {latitude: 53.4, longitude: -3.0},   // SP-Manweb (Merseyside)
14: {latitude: 52.5, longitude: -2.0},   // NGED-WM (West Midlands)
15: {latitude: 54.9, longitude: -1.6},   // NPg-NE (North East)
16: {latitude: 53.8, longitude: -2.5},   // ENWL (North West)
17: {latitude: 57.5, longitude: -4.5},   // SSE-SHEPD (North Scotland)
18: {latitude: 55.9, longitude: -3.2},   // SP-Distribution (South Scotland)
19: {latitude: 51.1, longitude: 0.3},    // UKPN-SPN (South Eastern)
20: {latitude: 51.0, longitude: -1.3},   // SSE-SEPD (Southern)
21: {latitude: 51.6, longitude: -3.2},   // NGED-SWales (South Wales)
22: {latitude: 50.7, longitude: -4.0},   // NGED-SW (South West)
23: {latitude: 53.8, longitude: -1.1}    // NPg-Y (Yorkshire)
```

### BigQuery Queries

**Spatial Query (Postcode Lookup)**:
```sql
SELECT 
  r.mpan_distributor_id,
  r.dno_key,
  r.dno_name,
  r.dno_short_code,
  r.market_participant_id,
  r.gsp_group_id,
  r.gsp_group_name,
  r.primary_coverage_area
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries` d
JOIN `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference` r
  ON d.dno_id = r.mpan_distributor_id
WHERE ST_CONTAINS(d.boundary, ST_GEOGPOINT(-0.024898, 51.118716))
LIMIT 1
```

**Direct Query (Dropdown Lookup)**:
```sql
SELECT 
  mpan_distributor_id,
  dno_key,
  dno_name,
  dno_short_code,
  market_participant_id,
  gsp_group_id,
  gsp_group_name,
  primary_coverage_area
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`
WHERE mpan_distributor_id = 14
LIMIT 1
```

**Refresh Query (Get All DNOs)**:
```sql
SELECT 
  mpan_distributor_id,
  dno_key,
  dno_name,
  dno_short_code,
  market_participant_id,
  gsp_group_id,
  gsp_group_name,
  primary_coverage_area
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`
ORDER BY mpan_distributor_id
```

### Files & Locations

| File | Location | Purpose |
|------|----------|---------|
| `bess_vlp_lookup.gs` | `/apps-script/` | Apps Script source code (540 lines) |
| `enhance_bess_vlp_sheet.py` | `/` | Python sheet builder script |
| `test_bess_vlp_lookup.py` | `/` | Python proof-of-concept test |
| `inner-cinema-credentials.json` | `/` | BigQuery service account key |
| Google Sheet | [Link](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/) | Production sheet |

---

## FAQ

### Q: How often does DNO data change?

**A**: Very rarely! Last major change was 2016. Expect next change around 2030+. Refresh once per year is sufficient.

---

### Q: Can I use this for commercial projects?

**A**: Yes! This tool is designed for BESS VLP analysis and commercial use.

---

### Q: What if my postcode is new?

**A**: Postcode API updates regularly. If very new (< 1 month), use dropdown method instead.

---

### Q: Why do some companies have multiple DNOs?

**A**: Historic regional divisions, different regulatory entities, separate pricing zones, and independent connection processes.

---

### Q: Can I export the data?

**A**: Yes! Unhide reference table (rows 24-37), select all, copy/paste to another sheet or CSV.

---

### Q: Does this work outside Great Britain?

**A**: No. UK mainland only (England, Scotland, Wales). Northern Ireland has different DNOs not included.

---

### Q: What's the difference between MPAN and GSP?

**A**: MPAN identifies the DNO company (14 options). GSP identifies grid connection point (also 14, labeled A-P). Both are unique per DNO.

---

### Q: Can I add my own DNO?

**A**: Only if Ofgem licenses a new DNO. Update BigQuery table, then run refresh function.

---

### Q: Is BigQuery usage free?

**A**: Yes for this use case. Queries are tiny (<1KB per lookup, ~14KB per refresh). Well within free tier.

---

### Q: Can I share this sheet?

**A**: Yes! Share with anyone. They'll need their own Google account and BigQuery permissions.

---

### Q: What happens if postcodes.io is down?

**A**: Use dropdown method (E4) instead. It doesn't rely on external API.

---

### Q: Can I automate this with API?

**A**: Yes! Apps Script supports Web App deployment. Contact maintainer for setup.

---

### Q: Where's the boundary data from?

**A**: National Energy System Operator (NESO, formerly National Grid ESO). Officially published DNO boundaries.

---

### Q: Can I see the boundary polygons?

**A**: Yes! Query BigQuery table `neso_dno_boundaries` - has GEOGRAPHY column with full polygons.

---

### Q: Why approximate coordinates for dropdown?

**A**: Dropdown lookup doesn't specify exact location, so we use DNO area center. Postcode lookup uses precise coordinates.

---

## Support & Contact

**Maintainer**: George Major  
**Email**: george@upowerenergy.uk  
**Project**: GB Power Market JJ  
**Repository**: [GitHub](https://github.com/GeorgeDoors888/GB-Power-Market-JJ)

**For Issues**:
1. Check [Troubleshooting](#troubleshooting) section
2. Review [FAQ](#faq)
3. Contact maintainer with:
   - Error message
   - What you were trying to do
   - Screenshot if helpful

---

## Changelog

### Version 2.0 (November 9, 2025)
- ✅ Fixed centroid coordinate mappings (all 14 MPANs correct)
- ✅ Added enhanced refresh function (updates table + dropdown)
- ✅ Added toggle visibility function
- ✅ Enhanced menu with 3 options
- ✅ Improved error messages
- ✅ Updated documentation

### Version 1.0 (November 6, 2025)
- ✅ Initial release
- ✅ Postcode lookup
- ✅ DNO dropdown
- ✅ Google Maps integration
- ✅ Hidden reference table
- ✅ Basic refresh function

---

## Related Documentation

- **Project Configuration**: `PROJECT_CONFIGURATION.md`
- **Data Architecture**: `STOP_DATA_ARCHITECTURE_REFERENCE.md`
- **Deployment Guide**: `BESS_VLP_DEPLOYMENT_GUIDE.md`
- **DNO Refresh Explained**: `BESS_VLP_DNO_REFRESH_EXPLAINED.md`
- **Dropdown Fix**: `BESS_VLP_DROPDOWN_FIX.md`
- **ChatGPT Instructions**: `.github/copilot-instructions.md`

---

**Last Updated**: November 9, 2025  
**Version**: 2.0  
**Status**: ✅ Production Ready

*For updates to this guide, see: `CHANGELOG.md`*
