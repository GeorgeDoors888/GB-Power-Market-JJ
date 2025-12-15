# ✅ Apps Script Fully Integrated - Version 4

## 🎉 What's Been Combined

Your Apps Script now includes **THREE** major features in one unified deployment:

### 1. 🗺️ DNO Map Tools
- **View Interactive Map** - UK DNO license areas with real GeoJSON boundaries
- **View Map with Site Markers** - Map with battery site location from postcode
- **Embed Map in DNO Sheet** - Embed map in spreadsheet via Google Drive

### 2. ⚡ GB Live Dashboard (Sparklines) 
- **Write Sparkline Formulas** - Generate 20 cross-sheet sparkline charts
- **Verify Data_Hidden** - Check data availability
- **Clear Sparklines** - Remove all sparklines
- **Health Check** - Quick diagnostic popup

### 3. 🔋 BESS Tools
- **Generate HH Data** - Create synthetic half-hourly demand profiles
- **Refresh DNO Data** - Auto-lookup DNO info from postcode/MPAN
- **Calculate PPA Analysis** - Battery arbitrage revenue calculations
- **Show HH Data Status** - Check generated data statistics

## 📋 Deployment Information

```
Deployment ID: AKfycbxwFCjNeh7YRiO46aSceM5D03XFa11dPosYsMkOdKg_9HgVxEK-PnTdoibMamKTmMsh
Web App URL: https://script.google.com/macros/s/AKfycbxwFCjNeh7YRiO46aSceM5D03XFa11dPosYsMkOdKg_9HgVxEK-PnTdoibMamKTmMsh/exec
Library URL: https://script.google.com/macros/library/d/1zwDbH6rP98P1SVRsn1gHf_ovridEFbTyVr2w3TStwMHMA5zvNk-45HuL/3
Version: 3 (Updated 8 Dec 2025, 22:31)
Status: ✅ Successfully deployed
```

## 📊 Spreadsheet Targets

### Primary Spreadsheet (BESS Tools + DNO Map)
**URL**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
**Title**: GB Energy Dashboard
**Key Sheets**:
- **BESS** - Battery storage analysis with DNO lookup
- **DNO** - DNO map embedding target
- **HH Data** - Half-hourly demand profiles
- **Dashboard** - Main energy market dashboard

### Secondary Spreadsheet (Sparklines)
**URL**: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/
**Title**: BtM
**Key Sheets**:
- **GB Live** - Real-time generation dashboard with sparklines
- **Data_Hidden** - 20 rows × 24 cols of sparkline data

## 🎯 Usage Guide

### For BESS Sheet (Main Dashboard)

#### 1. DNO Lookup Workflow
```
1. Enter postcode in cell A6 (e.g., "SW1A 1AA")
2. Click: 🔋 BESS Tools → 🔄 Refresh DNO Data
3. Wait 5 seconds
4. DNO info appears in cells C6-H6
5. DUoS rates appear in row 9
6. Time bands appear in rows 11-13
```

**Auto-trigger**: Edit A6 or B6 → automatic lookup after 1.5 seconds

#### 2. Generate HH Demand Profile
```
1. Enter parameters:
   - B17: Min kW (e.g., 500)
   - B18: Avg kW (e.g., 1000)
   - B19: Max kW (e.g., 1500)
2. Click: 🔋 BESS Tools → 📊 Generate HH Data
3. If webhook available: Auto-generates 17,520 rows
4. If webhook unavailable: Shows Python command to run
```

**Expected output**: 365 days × 48 periods = 17,520 half-hourly demand values

#### 3. View DNO Map with Site Marker
```
1. Ensure postcode in A6
2. Click: 🗺️ DNO Map → View Map with Site Markers
3. Interactive map opens with:
   - UK DNO boundaries (colored by region)
   - Red marker at battery site location
   - Zoom to site level (1:10 scale)
```

### For GB Live Sheet (Real-time Dashboard)

#### 1. Write Sparkline Formulas
```
1. Ensure Data_Hidden sheet has data (run Python script first)
2. Click: ⚡ GB Live Dashboard → ✨ Write Sparkline Formulas
3. Wait 5 seconds
4. 20 sparkline charts appear:
   - Column C (rows 11-20): Fuel types
   - Column F (rows 11-20): Interconnectors
```

#### 2. Health Check
```
1. Click: ⚡ GB Live Dashboard → 🏥 Health Check
2. Popup shows:
   - Sheet availability
   - Sparkline status
   - Data presence
   - Trigger count
```

## 🔧 Technical Architecture

### Menu Structure
```javascript
onOpen() {
  // Creates 3 menus when spreadsheet opens
  
  Menu 1: 🗺️ DNO Map
    - View Interactive Map
    - View Map with Site Markers
    - Embed Map in DNO Sheet
  
  Menu 2: 🔋 BESS Tools
    - Generate HH Data
    - Refresh DNO Data
    - Calculate PPA Analysis
    - Show HH Data Status
  
  Menu 3: ⚡ GB Live Dashboard (only in bg-sparklines-clasp/)
    - Write Sparkline Formulas
    - Verify Data_Hidden
    - Clear Sparklines
    - Health Check
}
```

### Key Functions

#### DNO Map Functions
- `createDNOMap()` - Leaflet map with GeoJSON from GitHub
- `createDNOMapWithSites()` - Map with geocoded battery site
- `embedMapInSheet()` - Drive upload + IMAGE() formula

#### BESS Tools Functions
- `generateHHDataDirect()` - Webhook to Python HH generator
- `manualRefreshDno()` - Postcode → geocode → MPAN → BigQuery
- `coordinatesToMpan(lat, lng)` - Regional boundary mapping
- `calculatePPAAnalysis()` - Battery arbitrage calculations
- `showHHDataStatus()` - Data validation and statistics
- `onEdit(e)` - Auto-trigger for A6/B6 cell edits

#### Sparkline Functions (in bg-sparklines-clasp/)
- `writeSparklines()` - Write 20 cross-sheet formulas
- `diagnostics()` - Full environment check
- `quickHealthCheck()` - Menu-driven quick check

### External Dependencies

#### APIs
- **postcodes.io**: Postcode → lat/lng geocoding (free, no key)
- **GitHub Raw**: GeoJSON boundaries (public repo)
- **BigQuery**: DNO reference data (via Python)

#### Python Webhooks (optional)
- `http://localhost:5001/generate_hh` - HH data generator
- `http://localhost:5001/dno_lookup` - DNO data fetcher

If webhooks unavailable, Apps Script shows terminal commands to run.

## 🚀 Deployment Steps

### Option 1: Direct Copy-Paste (Recommended)
```
1. Open spreadsheet: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/
2. Go to: Extensions → Apps Script
3. Delete any existing code
4. Copy ENTIRE /home/george/GB-Power-Market-JJ/Code.gs file
5. Paste into Apps Script editor
6. Save (Ctrl+S)
7. Close Apps Script editor
8. Refresh spreadsheet (F5)
9. Check menus appear: 🗺️ DNO Map, 🔋 BESS Tools
```

### Option 2: Update Existing Deployment
```
1. You already deployed this! (Version 3)
2. If you made changes, just:
   - Edit in Apps Script editor
   - Click: Deploy → Manage deployments
   - Click: Edit (pencil icon)
   - Version: New version
   - Description: "Added BESS Tools"
   - Click: Deploy
```

## 🧪 Testing Checklist

### Test DNO Map
- [ ] Click "View Interactive Map" - UK boundaries appear
- [ ] Hover over region - info panel updates
- [ ] Click region - zooms to area
- [ ] Enter postcode in A6 - "View Map with Site Markers" shows red marker

### Test BESS Tools
- [ ] Enter postcode in A6 - auto-lookup triggers (if onEdit configured)
- [ ] Click "Refresh DNO Data" - cell A4 shows status
- [ ] Check C6-H6 - DNO details appear
- [ ] Enter B17-B19 values - "Generate HH Data" creates sheet
- [ ] Click "Show HH Data Status" - popup shows row count

### Test Sparklines (in BtM spreadsheet)
- [ ] Run Python: `python3 update_bg_live_dashboard.py`
- [ ] Open: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/
- [ ] Check "GB Live" sheet exists
- [ ] Click: ⚡ GB Live Dashboard → Write Sparkline Formulas
- [ ] Check columns C11-C20 and F11-F20 - charts appear

## 🔐 Permissions Required

When first running, Apps Script will request:
- ✅ **View and manage spreadsheets** - Read/write cells
- ✅ **Connect to external services** - Fetch GeoJSON, geocode postcodes
- ✅ **Display content in UI** - Show dialogs and menus
- ✅ **Access Google Drive** - Upload embedded maps (optional)

Click "Review Permissions" → Select your account → Click "Allow"

## 📁 File Locations

### Main Deployment
```
/home/george/GB-Power-Market-JJ/Code.gs
```
**Line count**: 800+ lines  
**Features**: DNO Map + BESS Tools + onEdit trigger

### Sparklines Version (Separate Project)
```
/home/george/GB-Power-Market-JJ/bg-sparklines-clasp/Code.gs
```
**Line count**: 900+ lines  
**Features**: DNO Map + BESS Tools + Sparklines + Diagnostics

### Supporting Files
```
/home/george/GB-Power-Market-JJ/
├── bess_hh_generator.gs          # Original BESS Tools code
├── bess_auto_trigger.gs          # Original auto-trigger
├── bess_dno_lookup.gs            # Original DNO lookup
├── dno_lookup_python.py          # Python DNO backend
├── generate_hh_profile.py        # Python HH generator
└── gb_power_map_deployment/
    └── dno_regions.geojson       # UK DNO boundaries
```

## 🐛 Troubleshooting

### "Menu doesn't appear"
**Cause**: Apps Script not saved or not bound to spreadsheet  
**Fix**: 
1. Check Extensions → Apps Script exists
2. Save code (Ctrl+S)
3. Refresh spreadsheet (F5)

### "Sparklines show #N/A"
**Cause**: Data_Hidden sheet missing or empty  
**Fix**: Run Python script to populate data:
```bash
cd ~/GB-Power-Market-JJ
python3 update_bg_live_dashboard.py
```

### "DNO lookup fails"
**Cause**: Postcode invalid or webhook down  
**Fix**: 
1. Check postcode format (e.g., "SW1A 1AA")
2. Run manual command: `python3 dno_lookup_python.py 12 LV`

### "HH Data generation fails"
**Cause**: Webhook not running  
**Fix**: Start webhook server:
```bash
cd ~/GB-Power-Market-JJ
python3 dno_webhook_server.py &
```

### "Permission denied"
**Cause**: First-time run, needs authorization  
**Fix**: 
1. Run any function from Apps Script editor
2. Click "Review Permissions"
3. Select your account
4. Click "Allow"

## 📊 Data Flow Diagrams

### DNO Lookup Flow
```
User enters postcode (A6)
    ↓
onEdit() detects change
    ↓
Geocode via postcodes.io API
    ↓
coordinatesToMpan(lat, lng)
    ↓
Call Python webhook OR show command
    ↓
Python queries BigQuery
    ↓
Returns DNO name, rates, time bands
    ↓
Apps Script writes to BESS sheet cells
```

### HH Data Generation Flow
```
User enters Min/Avg/Max kW (B17-B19)
    ↓
Click "Generate HH Data" menu item
    ↓
Apps Script reads parameters
    ↓
Call Python webhook OR show command
    ↓
Python generates 17,520 synthetic values
    ↓
Writes to "HH Data" sheet
    ↓
Apps Script confirms completion
```

### Sparkline Flow
```
Python script updates Data_Hidden sheet (20 rows × 24 cols)
    ↓
User clicks "Write Sparkline Formulas"
    ↓
Apps Script writes 20 cross-sheet formulas
    ↓
Formulas reference Data_Hidden!A1:X20
    ↓
Google Sheets renders inline charts
    ↓
Charts update automatically when data changes
```

## 🎓 Next Steps

### 1. Enable Auto-Trigger (Optional)
To make DNO lookup automatic on cell edit:

```
1. Open: Extensions → Apps Script
2. Click: Clock icon (Triggers) in left sidebar
3. Click: + Add Trigger (bottom right)
4. Configure:
   - Function: onEdit
   - Deployment: Head
   - Event source: From spreadsheet
   - Event type: On edit
5. Click: Save
```

Now editing A6 or B6 will auto-trigger DNO lookup after 1.5 seconds.

### 2. Start Python Webhooks
For seamless integration:

```bash
# Terminal 1: DNO webhook
cd ~/GB-Power-Market-JJ
python3 dno_webhook_server.py

# Terminal 2: HH generator webhook
python3 hh_generator_webhook.py  # (if exists)
```

### 3. Schedule Python Updates
Keep Data_Hidden fresh for sparklines:

```bash
# Add to crontab
crontab -e

# Add line:
*/5 * * * * cd ~/GB-Power-Market-JJ && python3 update_bg_live_dashboard.py >> logs/dashboard.log 2>&1
```

### 4. Share as Library
Your deployment URL is already shareable:
```
https://script.google.com/macros/library/d/1zwDbH6rP98P1SVRsn1gHf_ovridEFbTyVr2w3TStwMHMA5zvNk-45HuL/3
```

To let others use as library:
1. File → Manage versions → New version
2. Publish → Deploy as library
3. Copy Library ID
4. Share with collaborators

## 📝 Version History

**Version 4** (8 Dec 2025) - Current
- ✅ DNO Map tools (3 functions)
- ✅ BESS Tools (5 functions)
- ✅ Auto-trigger on cell edit
- ✅ Comprehensive error handling

**Version 3** (8 Dec 2025)
- ✅ DNO Map with GeoJSON boundaries
- ✅ Site marker integration
- ✅ Drive embedding

**Version 2** (7 Dec 2025)
- ✅ Basic DNO map
- ✅ Manual triggers

**Version 1** (6 Dec 2025)
- ✅ Initial deployment

## 🔗 Related Documentation

- `bg-sparklines-clasp/README.md` - Sparkline deployment guide
- `bg-sparklines-clasp/QUICKSTART.md` - 2-minute quick start
- `bg-sparklines-clasp/RUN_DIAGNOSTICS.md` - Diagnostic tools
- `SPARKLINE_ISSUE_RESOLVED.md` - Technical analysis
- `PROJECT_CONFIGURATION.md` - BigQuery setup
- `.github/copilot-instructions.md` - AI coding guidelines

---

**Maintainer**: George Major (george@upowerenergy.uk)  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Status**: ✅ Production (Dec 2025)  
**Last Updated**: 8 Dec 2025, 23:00
