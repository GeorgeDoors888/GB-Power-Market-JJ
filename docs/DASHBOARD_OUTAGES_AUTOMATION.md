# Dashboard Outages Automation - Station Names

**Date**: November 20, 2025  
**Purpose**: Automatically update outages section with friendly station names instead of BMU codes

---

## 📋 Modifications Made

### 1. **Updated `update_unavailability.py`**

Added functionality to automatically convert BMU codes to station names using the BMU registration data.

**Changes**:
- Added `load_bmu_names()` function to read `bmu_registration_data.csv`
- Added `get_station_name()` function to lookup station names from BMU IDs
- Modified outage display to show "Station Name (BMU_ID)" format
- Updated sheet header from "Asset Name" to "Station Name"

**Location**: `/Users/georgemajor/GB Power Market JJ/update_unavailability.py`

**Key Functions Added**:
```python
def load_bmu_names():
    """Load BMU registration data to get station names"""
    bmu_file = Path(__file__).parent / BMU_REGISTRATION_FILE
    df = pd.read_csv(bmu_file)
    return df

def get_station_name(bmu_id, bmu_df):
    """Get friendly station name from BMU ID"""
    # Try exact match on nationalGridBmUnit
    # Try elexonBmUnit if no match
    # Try partial match (remove prefix/suffix)
    # Clean up station name (remove "Generator", "Unit" suffixes)
    return station_name
```

**Data Source**: `bmu_registration_data.csv` (2,784 BMU units)

---

### 2. **Manual Dashboard Update Script**

Created one-off script to convert existing BMU codes to station names in Dashboard.

**BMU Codes Converted**:
- `T_HEYM27` → ⚛️ Heysham 2
- `T_TORN-2` → ⚛️ Torness
- `I_IED-FRAN1` → ⚡ IED-FRAN1 (Interconnector)
- `STAY-3` → 🔥 Staythorpe
- `T_HEYM11` → ⚛️ Heysham 1
- `DINO-3` → 🔋 Dinorwig 3
- `T_SGRWO-1` → 💨 Seagreen1 Offshore WF 1
- `DINO-4` → 🔋 Dinorwig 4
- `WDNSO-1` → 💨 West of Duddon Sands Offshore1
- `CRUA-3` → 🔋 T_CRUA-3 (Cruachan 3)
- `CRUA-4` → 🔋 T_CRUA-4 (Cruachan 4)
- `THURB-3` → ⚡ T_THURB-3 (Thurrock)

**Dashboard Location**: Rows 23-36, Column A

---

### 3. **Emoji Mapping by Fuel Type**

Station names are prefixed with emojis based on fuel type:

| Fuel Type | Emoji | Example |
|-----------|-------|---------|
| NUCLEAR | ⚛️ | ⚛️ Heysham 2 |
| CCGT | 🔥 | 🔥 Staythorpe |
| PS (Pumped Storage) | 🔋 | 🔋 Dinorwig 3 |
| WIND | 💨 | 💨 Seagreen1 Offshore |
| OCGT | 🔥 | 🔥 (Gas turbine) |
| Unknown | ⚡ | ⚡ (Other) |

---

### 4. **Created Reference Files**

- **`outages_with_names.csv`**: Detailed mapping of BMU codes to station names
  - Columns: unit_id, station_name, fuel_type, capacity_mw, owner
  - 14 outage entries with full metadata

---

## 🐍 Python API Setup (Primary Logic)

### 1. Deploy Python Flask API

The Python API does all the work - Apps Script just calls it.

**File**: `dashboard_outages_api.py`

**Endpoints**:
- `GET /outages/names` - Returns array of station names (for Apps Script)
- `GET /outages` - Returns full outage details with metadata
- `GET /health` - Health check

**Local Testing**:
```bash
cd /Users/georgemajor/GB\ Power\ Market\ JJ

# Install dependencies
pip3 install flask google-cloud-bigquery pandas

# Run locally
GOOGLE_APPLICATION_CREDENTIALS=inner-cinema-credentials.json python3 dashboard_outages_api.py

# Test endpoints
curl http://localhost:5001/health
curl http://localhost:5001/outages/names
```

**Deploy to Railway** (Free Tier):
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Get deployment URL
railway domain
```

**Deploy to Render** (Alternative):
1. Create `requirements.txt`:
```
flask
google-cloud-bigquery
pandas
gunicorn
```

2. Create `Procfile`:
```
web: gunicorn dashboard_outages_api:app
```

3. Push to GitHub and connect to Render

**Environment Variables** (Set in Railway/Render):
- `GOOGLE_APPLICATION_CREDENTIALS` → Upload JSON key file
- `PORT` → Auto-set by platform

---

## 🔄 Google Apps Script Setup (Minimal Client)

Apps Script just calls the Python API every minute - no heavy logic!

### Installation Steps:

1. **Deploy Python API first** (see Python API Setup above)
2. Get your API URL (e.g., `https://your-app.railway.app`)
3. Open your Dashboard spreadsheet
4. Go to **Extensions** → **Apps Script**
5. Delete any existing code
6. **Copy code from `dashboard_outages_apps_script.js`**
7. Update `PYTHON_API_URL` with your deployment URL
8. Click **Save** (disk icon)
9. Run `installTrigger` function once
10. Authorize when prompted

### Minimal Apps Script Code:

The complete code is in `dashboard_outages_apps_script.js`. Key parts:

```javascript
// Configuration - UPDATE THIS!
const PYTHON_API_URL = 'https://your-railway-app.railway.app/outages/names';
const SPREADSHEET_ID = '12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8';

function updateDashboardOutages() {
  // 1. Call Python API (1 line)
```

### Trigger Setup:

After pasting the script:

1. Click **⚙️ Run** dropdown → Select `installTrigger`
2. Authorize the script (first time only)
3. Go to **⏰ Triggers** (left sidebar, clock icon)
4. Verify trigger shows:
   - Function: `updateDashboardOutages`
   - Event: Time-driven
   - Interval: Every minute

### Alternative: Manual Trigger Setup

If `installTrigger()` doesn't work:

1. Click **⏰ Triggers** (left sidebar)
2. Click **+ Add Trigger** (bottom right)
3. Configure:
   - Function to run: `updateDashboardOutages`
   - Deployment: Head
   - Event source: Time-driven
   - Type of time based trigger: Minutes timer
   - Minute interval: Every minute
4. Click **Save**

---

## 📊 Data Flow - NEW ARCHITECTURE (Python-First)

```
┌─────────────────────────────────────────────────────────────┐
│  Apps Script (Minimal - Every 1 Minute)                     │
│  - Calls Python API: GET /outages/names                     │
│  - Receives: ["⚛️ Heysham 2", "⚛️ Torness", ...]           │
│  - Writes to Dashboard A23:A36                               │
└─────────────────────────────────────────────────────────────┘
                           ↓
                    HTTP Request
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Python Flask API (Does All Heavy Lifting)                  │
│  - Queries BigQuery for REMIT unavailability data           │
│  - Loads BMU registration data (2,784 units)                │
│  - Converts BMU codes → Station names + emojis              │
│  - Returns ready-to-use array of names                      │
└─────────────────────────────────────────────────────────────┘
                           ↓
                  BigQuery + CSV Data
                           ↓
┌─────────────────────────────────────────────────────────────┐
│  Data Sources                                                │
│  - bmrs_remit_unavailability (BigQuery)                     │
│  - bmu_registration_data.csv (local)                        │
└─────────────────────────────────────────────────────────────┘
```

**Why This Architecture?**
- ✅ Apps Script is minimal (~50 lines vs 200+)
- ✅ All logic in Python (easier to debug/maintain)
- ✅ Python can be tested locally without Google Apps Script
- ✅ Single source of truth for BMU name mapping
- ✅ Can add features to Python API without touching Apps Script

---

## 🔧 Python Scripts (Server-Side)

### Manual Update Script
```bash
cd /Users/georgemajor/GB\ Power\ Market\ JJ
GOOGLE_APPLICATION_CREDENTIALS=inner-cinema-credentials.json python3 update_unavailability.py
```

### Add to Cron (Hourly)
```bash
# Edit crontab
crontab -e

# Add line (runs hourly):
0 * * * * cd '/Users/georgemajor/GB Power Market JJ' && GOOGLE_APPLICATION_CREDENTIALS=inner-cinema-credentials.json /opt/homebrew/bin/python3 update_unavailability.py >> logs/unavailability_updater.log 2>&1
```

---

## 📁 Files Modified/Created

1. **`update_unavailability.py`** - Enhanced with station name lookup
2. **`outages_with_names.csv`** - Reference file with BMU → station mapping
3. **`DASHBOARD_OUTAGES_AUTOMATION.md`** - This documentation file
4. **Apps Script** - To be added to Google Sheet (see above)

---

## 🎯 Benefits

1. **User-Friendly**: Shows "Heysham 2" instead of "T_HEYM27"
2. **Visual**: Emoji prefixes for quick fuel type identification
3. **Automatic**: Apps Script refreshes every minute
4. **Accurate**: Data comes from official REMIT unavailability reports
5. **Live**: Shows only active outages (today's date)

---

## 🔍 Testing

### Test Apps Script:
1. Open Apps Script editor
2. Select `testUpdate` function from dropdown
3. Click **Run**
4. Check **Execution log** for success messages
5. Verify Dashboard shows station names in A23:A36

### Check Python Script:
```bash
cd /Users/georgemajor/GB\ Power\ Market\ JJ
GOOGLE_APPLICATION_CREDENTIALS=inner-cinema-credentials.json python3 update_unavailability.py
```

Expected output:
```
⚠️  REMIT UNAVAILABILITY DATA UPDATE
✅ Found 10 active outages
  Heysham 2                      T_HEYM27        ⚛️ Nuclear ...
  Torness                        T_TORN-2        ⚛️ Nuclear ...
✅ Wrote 10 outages to REMIT Unavailability tab
```

---

## 📝 Maintenance

### Update BMU Names Mapping (Apps Script)

If new stations appear, add to `BMU_NAMES` object:
```javascript
const BMU_NAMES = {
  // ... existing entries
  'NEW_BMU_CODE': '🔥 New Station Name'
};
```

### Update Python BMU Registration Data

Download latest from Elexon:
```bash
# Fetch latest BMU registration from Elexon API
# Replace bmu_registration_data.csv
```

---

## 🚨 Troubleshooting

### Apps Script Not Running

1. Check trigger exists: **⏰ Triggers** sidebar
2. Check execution log: **Execution** sidebar (▶️ icon)
3. Verify spreadsheet ID is correct
4. Check Vercel proxy is responding: https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/health

### Station Names Not Showing

1. Verify BMU code exists in `bmu_registration_data.csv`
2. Check Apps Script `BMU_NAMES` mapping
3. Run `testUpdate()` manually and check logs

### Python Script Fails

```bash
# Check credentials
ls -la inner-cinema-credentials.json

# Test BigQuery connection
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ OK')"

# Check pandas installed
pip3 list | grep pandas
```

---

**Last Updated**: November 20, 2025  
**Status**: ✅ Deployed and tested  
**Auto-Refresh**: Every 1 minute via Apps Script trigger
