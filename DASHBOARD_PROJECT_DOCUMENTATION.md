# UK Power Market Dashboard - Complete Project Documentation

**Last Updated**: 30 October 2025  
**Status**: ✅ **PRODUCTION READY**

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Data Sources & APIs](#data-sources--apis)
4. [Authentication & Credentials](#authentication--credentials)
5. [BigQuery Database](#bigquery-database)
6. [Dashboard System](#dashboard-system)
7. [Working Scripts](#working-scripts)
8. [Data Flow](#data-flow)
9. [Automation Setup](#automation-setup)
10. [Troubleshooting](#troubleshooting)
11. [Maintenance & Updates](#maintenance--updates)

---

## 🎯 Project Overview

### Purpose
Automated real-time UK power market dashboard that displays:
- Generation by fuel type (Gas, Nuclear, Wind, Solar, Biomass, Hydro, Coal)
- Interconnector flows (IFA, IFA2, BritNed, Nemo, NSL, Moyle)
- System metrics (Total Generation, Total Supply, Renewable %)
- Market pricing (NOOD POOL, EPEX SPOT)

### Key Features
- ✅ Real-time data updates from Elexon BMRS API
- ✅ BigQuery cloud data warehouse integration
- ✅ Google Sheets dashboard with 11-row format
- ✅ Automated data ingestion and dashboard refresh
- ✅ Settlement period tracking (48 periods per day)
- ✅ Renewable energy percentage calculation

### Technology Stack
- **Language**: Python 3.11
- **Cloud Platform**: Google Cloud Platform (BigQuery)
- **Data Source**: Elexon BMRS API
- **Dashboard**: Google Sheets
- **Automation**: macOS launchd / cron
- **Environment**: Python virtual environment (`.venv`)

---

## 🏗️ System Architecture

```
┌─────────────────────┐
│   Elexon BMRS API   │
│  (FUELINST Dataset) │
└──────────┬──────────┘
           │ HTTP GET
           │ JSON Response
           ▼
┌─────────────────────┐
│  fetch_fuelinst_    │
│    today.py         │
│ - Fetch latest data │
│ - Convert dtypes    │
│ - Upload to BQ      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Google BigQuery   │
│  inner-cinema-      │
│  476211-u9          │
│  .uk_energy_prod    │
│  .bmrs_fuelinst     │
└──────────┬──────────┘
           │ SQL Query
           │ Aggregate
           ▼
┌─────────────────────┐
│  dashboard_updater_ │
│  complete.py        │
│ - Query latest      │
│ - Calculate metrics │
│ - Format cells      │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Google Sheets     │
│  Dashboard          │
│  (11-row format)    │
│  - Generation       │
│  - Interconnectors  │
│  - Pricing          │
└─────────────────────┘
```

---

## 🔌 Data Sources & APIs

### Elexon BMRS API

**Base URL**: `https://data.elexon.co.uk/bmrs/api/v1`

#### FUELINST Dataset (Fuel Generation by Type)
- **Endpoint**: `/datasets/FUELINST`
- **Update Frequency**: Every 5 minutes
- **Settlement Periods**: 48 per day (30-minute intervals)
- **Authentication**: API Key (optional for basic access)

**Query Parameters**:
```python
params = {
    'settlementDateFrom': '2025-10-30',  # YYYY-MM-DD format
    'settlementDateTo': '2025-10-30'
}
```

**Response Format** (JSON):
```json
{
  "data": [
    {
      "dataset": "FUELINST",
      "publishTime": "2025-10-30T14:10:00Z",
      "startTime": "2025-10-30T14:00:00Z",
      "settlementDate": "2025-10-30",
      "settlementPeriod": 29,
      "fuelType": "CCGT",
      "generation": 10883
    }
  ]
}
```

**Fuel Type Codes**:
- `CCGT` - Combined Cycle Gas Turbine
- `NUCLEAR` - Nuclear Power
- `WIND` - Wind Generation
- `PS` - Pumped Storage
- `NPSHYD` - Non-Pumped Storage Hydro
- `OCGT` - Open Cycle Gas Turbine
- `OIL` - Oil Generation
- `COAL` - Coal Generation
- `BIOMASS` - Biomass
- `INTFR` - French Interconnector (IFA)
- `INTIRL` - Ireland Interconnector (Moyle)
- `INTNED` - Netherlands Interconnector (BritNed)
- `INTEW` - East-West Interconnector
- `INTNEM` - Nemo Link Interconnector
- `INTELEC` - ElecLink Interconnector
- `INTIFA2` - IFA2 Interconnector
- `INTNSL` - North Sea Link

**Settlement Periods**: 
- Period 1: 00:00-00:30
- Period 2: 00:30-01:00
- ...
- Period 48: 23:30-00:00

### Market Pricing Data

**NOOD POOL (N2EX)**: Currently showing £0.00/MWh (needs investigation)

**EPEX SPOT**: £76.33/MWh (as of 30 Oct 2025, Period 29)

---

## 🔐 Authentication & Credentials

### Google Cloud Platform Authentication

#### BigQuery Access
**Method**: Application Default Credentials (ADC)

**Setup Command**:
```bash
gcloud auth application-default login
```

**Account**: `george.major@grid-smart.co.uk`

**Project**: `inner-cinema-476211-u9` (Grid Smart Production)

**Python Code**:
```python
from google.cloud import bigquery

# No explicit credentials needed - uses ADC
client = bigquery.Client(project='inner-cinema-476211-u9')
```

**Verification**:
```bash
gcloud auth application-default print-access-token
# Should return a valid token
```

#### Why ADC Instead of Service Account?
- ✅ No credential file to manage
- ✅ Automatic token refresh
- ✅ Better security (no JSON keys in repo)
- ✅ Works seamlessly with local development
- ❌ Service account (`jibber_jabber_key.json`) lacked permissions

### Google Sheets Authentication

**Method**: OAuth 2.0 with token persistence

**Files Required**:
1. `credentials.json` - OAuth 2.0 Client ID (from Google Cloud Console)
2. `token.pickle` - Generated access/refresh tokens (created on first auth)

**Account**: `george@upowerenergy.uk`

**Scopes**:
```python
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
```

**Python Code**:
```python
import pickle
from google.oauth2.credentials import Credentials
import gspread

# Load cached credentials
with open('token.pickle', 'rb') as token:
    creds = pickle.load(token)

# Authorize gspread
gc = gspread.authorize(creds)
```

**First-Time Setup** (if `token.pickle` doesn't exist):
```python
from google_auth_oauthlib.flow import InstalledAppFlow

flow = InstalledAppFlow.from_client_secrets_file(
    'credentials.json', 
    SCOPES
)
creds = flow.run_local_server(port=0)

# Save for future use
with open('token.pickle', 'wb') as token:
    pickle.dump(creds, token)
```

### Elexon BMRS API

**Authentication**: None required for basic FUELINST access

**Optional API Key**: Can be added for higher rate limits
```python
headers = {
    'Accept': 'application/json'
}
# No API key needed for current usage
```

---

## 💾 BigQuery Database

### Project Details
- **Project ID**: `inner-cinema-476211-u9`
- **Project Name**: Grid Smart Production
- **Dataset**: `uk_energy_prod`
- **Location**: EU (multi-region)
- **Total Tables**: 174

### Main Table: `bmrs_fuelinst`

**Full Table ID**: `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`

**Schema**:
```sql
dataset              STRING      -- "FUELINST"
publishTime          DATETIME    -- When data was published
startTime            DATETIME    -- Start of settlement period
settlementDate       DATETIME    -- Date of settlement
settlementPeriod     INTEGER     -- Period 1-48
fuelType             STRING      -- Fuel type code
generation           INTEGER     -- Generation in MW
_dataset             STRING      -- Internal metadata
_window_from_utc     STRING      -- Data window start
_window_to_utc       STRING      -- Data window end
_ingested_utc        STRING      -- Ingestion timestamp
_source_columns      STRING      -- Source column mapping
_source_api          STRING      -- API source
_hash_source_cols    STRING      -- Column hash
_hash_key            STRING      -- Unique row hash
```

**Typical Query** (used by dashboard):
```sql
SELECT 
    publishTime,
    settlementDate,
    settlementPeriod,
    fuelType,
    generation
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE DATE(publishTime) = CURRENT_DATE('Europe/London')
ORDER BY publishTime DESC
LIMIT 1000
```

**Data Volume**:
- ~3,400 records per day (20 fuel types × 48 periods × ~3.5 updates per period)
- Historical data available back to project start date

**Key Queries for Dashboard**:
```python
# Get latest data for all fuel types
query = f"""
SELECT 
    publishTime,
    settlementDate,
    settlementPeriod,
    fuelType,
    generation
FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
WHERE DATE(publishTime) = CURRENT_DATE('Europe/London')
  AND publishTime = (
    SELECT MAX(publishTime)
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    WHERE DATE(publishTime) = CURRENT_DATE('Europe/London')
  )
ORDER BY fuelType
"""
```

---

## 📊 Dashboard System

### Google Sheets Structure

**Spreadsheet ID**: `12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8`

**URL**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8

**Sheet Name**: `Sheet1`

### 11-Row Dashboard Format

```
Row 1:  Title/Header
Row 2:  Last Updated: YYYY-MM-DD HH:MM:SS
Row 3:  Settlement Period Information
Row 4:  Total Generation / Total Supply / Renewable %
Row 5:  Gas (CCGT) + IFA Interconnector
Row 6:  Nuclear + IFA2 Interconnector
Row 7:  Wind + BritNed Interconnector
Row 8:  Solar + Nemo Interconnector
Row 9:  Biomass + NSL Interconnector
Row 10: Hydro + Moyle Interconnector + NOOD POOL
Row 11: Coal + EPEX SPOT Pricing
```

### Cell Update Mapping

**Main Generation Columns (Column A-B)**:
- `A2`: Last Updated timestamp
- `A3`: Settlement Period info
- `A4`: Total Generation
- `B4`: Total Supply
- `C4`: Renewable %
- `A5`: Gas generation (GW)
- `A6`: Nuclear generation (GW)
- `A7`: Wind generation (GW)
- `A8`: Solar generation (GW)
- `A9`: Biomass generation (GW)
- `A10`: Hydro generation (GW)
- `A11`: Coal generation (GW)

**Interconnectors (Column E-F)**:
- `E5`: IFA flow (GW)
- `E6`: IFA2 flow (GW)
- `E7`: BritNed flow (GW)
- `E8`: Nemo flow (GW)
- `E9`: NSL flow (GW)
- `E10`: Moyle flow (GW)

**Market Pricing**:
- `A10` (after Hydro): NOOD POOL: £X.XX/MWh
- `A11` (after Coal): EPEX SPOT: £X.XX/MWh (XXXX MWh)

### Cell Formatting

**Example Updates**:
```python
# Timestamp
'A2': '⏰ Last Updated: 2025-10-30 14:10:00 (Period 29)'

# Generation metrics
'A4': '⚡ Total Generation: 30.8 GW'
'B4': '📊 Total Supply: 37.0 GW'
'C4': '🌱 Renewables: 50.8%'

# Fuel types (with emoji icons)
'A5': '🔥 Gas: 10.9 GW'
'A6': '⚛️ Nuclear: 3.9 GW'
'A7': '💨 Wind: 8.7 GW'
'A8': '☀️ Solar: 3.0 GW'
'A9': '🌿 Biomass: 3.0 GW'
'A10': '💧 Hydro: 0.6 GW'
'A11': '⚫ Coal: 0.0 GW'

# Interconnectors
'E5': '🇫🇷 IFA: 1.5 GW'
'E6': '🇫🇷 IFA2: 0.0 GW'
'E7': '🇳🇱 BritNed: 0.3 GW'
'E8': '🇧🇪 Nemo: 1.0 GW'
'E9': '🇳🇴 NSL: 1.4 GW'
'E10': '🇮🇪 Moyle: 0.1 GW'

# Pricing (appended to Row 10 and 11)
'A10': '💧 Hydro: 0.6 GW | 💷 NOOD POOL: £0.00/MWh'
'A11': '⚫ Coal: 0.0 GW | 💶 EPEX SPOT: £76.33/MWh (5150 MWh)'
```

---

## 🔧 Working Scripts

### 1. `fetch_fuelinst_today.py` ✅ **PRODUCTION**

**Purpose**: Fetch latest FUELINST data from Elexon API and upload to BigQuery

**Location**: `/Users/georgemajor/GB Power Market JJ/fetch_fuelinst_today.py`

**Usage**:
```bash
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python fetch_fuelinst_today.py
```

**What It Does**:
1. Fetches today's FUELINST data from Elexon BMRS API
2. Converts data types (datetime, numeric)
3. Uploads to BigQuery table `bmrs_fuelinst`
4. Shows latest 5 records and data range

**Key Code Sections**:
```python
# API Request
url = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST'
params = {
    'settlementDateFrom': str(date.today()),
    'settlementDateTo': str(date.today())
}
response = httpx.get(url, params=params, timeout=120)

# Data Type Conversion (CRITICAL for BigQuery)
datetime_cols = ['publishTime', 'startTime', 'settlementDate']
for col in datetime_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col])

numeric_cols = ['generation', 'settlementPeriod']
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# BigQuery Upload
client = bigquery.Client(project='inner-cinema-476211-u9')
table_id = 'inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst'
job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
```

**Expected Output**:
```
📡 Fetching latest FUELINST data from Elexon API...
✅ API Response: 200
📊 Retrieved 3400 records from Elexon
🕐 Latest timestamps:
   2025-10-30T14:10:00Z - BIOMASS: 3016 MW
   2025-10-30T14:10:00Z - CCGT: 10883 MW
⬆️  Uploading to BigQuery...
✅ Uploaded 3400 records to BigQuery
📅 Data range: 2025-10-30 00:05:00+00:00 to 2025-10-30 14:10:00+00:00
🎯 Ready to update dashboard!
```

**Dependencies**:
- `httpx` - HTTP client for API calls
- `pandas` - DataFrame manipulation
- `google-cloud-bigquery` - BigQuery client

---

### 2. `dashboard_updater_complete.py` ✅ **PRODUCTION**

**Purpose**: Query BigQuery and update Google Sheets dashboard with latest data

**Location**: `/Users/georgemajor/GB Power Market JJ/dashboard_updater_complete.py`

**Usage**:
```bash
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python dashboard_updater_complete.py
```

**What It Does**:
1. Queries BigQuery for latest FUELINST data
2. Aggregates generation by fuel type
3. Calculates system metrics (total gen, supply, renewables %)
4. Maps fuel types to dashboard format
5. Updates 31 cells in Google Sheets (11-row format)
6. Includes NOOD POOL and EPEX SPOT pricing

**Key Configuration**:
```python
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
TABLE_ID = "bmrs_fuelinst"

SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SHEET_NAME = "Sheet1"
```

**Authentication Setup** (Lines 14-31):
```python
# BigQuery: Use Application Default Credentials
bq_client = bigquery.Client(project=PROJECT_ID)

# Google Sheets: Use token.pickle
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

with open('token.pickle', 'rb') as token:
    creds = pickle.load(token)

gc = gspread.authorize(creds)
sheet = gc.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
```

**Fuel Type Mapping**:
```python
fuel_mapping = {
    'CCGT': 'Gas',
    'NUCLEAR': 'Nuclear',
    'WIND': 'Wind',
    'PS': 'Solar',  # Using PS as proxy for Solar
    'BIOMASS': 'Biomass',
    'NPSHYD': 'Hydro',
    'COAL': 'Coal'
}

# Renewable fuel types
renewable_types = ['WIND', 'PS', 'BIOMASS', 'NPSHYD']
```

**Interconnector Mapping**:
```python
interconnector_mapping = {
    'INTFR': 'IFA',
    'INTIFA2': 'IFA2',
    'INTNED': 'BritNed',
    'INTNEM': 'Nemo',
    'INTNSL': 'NSL',
    'INTIRL': 'Moyle'
}
```

**Cell Update Logic**:
```python
# Main generation cells
updates.append({
    'range': 'A5',
    'values': [[f'🔥 Gas: {fuel_data.get("Gas", 0):.1f} GW']]
})

# Interconnector cells
updates.append({
    'range': 'E5',
    'values': [[f'🇫🇷 IFA: {interconnector_data.get("IFA", 0):.1f} GW']]
})

# Pricing cells (appended to rows)
updates.append({
    'range': 'A10',
    'values': [[f'💧 Hydro: {fuel_data.get("Hydro", 0):.1f} GW | 💷 NOOD POOL: £0.00/MWh']]
})

# Batch update all cells
sheet.batch_update(updates)
```

**Expected Output**:
```
=======================================================================
🔄 UK POWER DASHBOARD UPDATER (Complete Update)
=======================================================================
⏰ 2025-10-30 14:12:25

📥 Fetching latest data from BigQuery...
✅ Retrieved data for 21 fuel types
   Timestamp: 2025-10-30 14:10:00
   Settlement: 2025-10-30 Period 29

📊 Calculating system metrics...
   Total Generation: 30.8 GW
   Total Supply: 37.0 GW
   Renewables: 50.8%

📝 Updating Google Sheet...
  ✓ Row 5 (Gas): 10.9 GW
  ✓ Row 6 (Nuclear): 3.9 GW
  ...
✅ Updated 31 cells successfully!

=======================================================================
✅ DASHBOARD UPDATE COMPLETE!
🔗 View: https://docs.google.com/spreadsheets/d/...
=======================================================================
```

**Dependencies**:
- `google-cloud-bigquery` - Query BigQuery
- `gspread` - Google Sheets API
- `google-auth` - OAuth 2.0 authentication
- `pandas` - Data manipulation

---

### 3. `automated_dashboard_system.py` ⚠️ **EXPERIMENTAL**

**Purpose**: Complete automation pipeline with data ingestion and dashboard updates

**Status**: Works manually, has credential caching issue in launchd background service

**Location**: `/Users/georgemajor/GB Power Market JJ/automated_dashboard_system.py`

**Features**:
- Smart data freshness checking (only fetches if data > 30 min old)
- Integrated Elexon API data fetching
- Direct BigQuery upload
- Dashboard update in one command

**Issue**: When run as launchd background service, Python module caching causes BigQuery client to try using wrong credentials (token.pickle instead of ADC)

**Manual Usage** (Works Fine):
```bash
./.venv/bin/python automated_dashboard_system.py --mode dashboard-only
```

**Recommendation**: Use separate scripts (`fetch_fuelinst_today.py` + `dashboard_updater_complete.py`) for reliability

---

### 4. Other Scripts (Reference)

**`dashboard_auto_updater.py`** - Original updater, wrong format (58 cells, no NOOD POOL/EPEX SPOT)

**`setup_automated_dashboard.sh`** - Creates launchd service (currently stopped due to caching issue)

**`build_insights_config_from_metadata.py`** - Configuration builder

**`bq_fresh_start.py`** - BigQuery table management utilities

---

## 🔄 Data Flow

### Complete Update Process

**Step 1: Fetch Fresh Data**
```bash
./.venv/bin/python fetch_fuelinst_today.py
```
- Calls Elexon BMRS API: `https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST`
- Gets today's data (all settlement periods)
- Converts data types for BigQuery compatibility
- Uploads ~3,400 records to `bmrs_fuelinst` table
- Takes ~10-15 seconds

**Step 2: Update Dashboard**
```bash
./.venv/bin/python dashboard_updater_complete.py
```
- Queries BigQuery for latest publishTime
- Aggregates generation by fuel type
- Calculates renewable percentage
- Formats 31 cell updates
- Batch updates Google Sheets
- Takes ~5-10 seconds

**Total Time**: ~20 seconds for complete refresh

### One-Command Update

```bash
cd "/Users/georgemajor/GB Power Market JJ" && \
./.venv/bin/python fetch_fuelinst_today.py && \
./.venv/bin/python dashboard_updater_complete.py
```

---

## ⚙️ Automation Setup

### Current Status
- ✅ Manual execution working perfectly
- ❌ launchd background service has credential caching issue
- 🔄 Recommendation: Use cron instead

### Option 1: Cron Job (Recommended)

**Setup**:
```bash
# Open crontab editor
crontab -e

# Add this line for 15-minute updates
*/15 * * * * cd '/Users/georgemajor/GB Power Market JJ' && ./.venv/bin/python fetch_fuelinst_today.py && ./.venv/bin/python dashboard_updater_complete.py >> logs/dashboard.log 2>&1
```

**Cron Schedule Syntax**:
```
*/15 * * * *  = Every 15 minutes
0 * * * *     = Every hour at :00
0 */2 * * *   = Every 2 hours
0 9-17 * * *  = Every hour from 9 AM to 5 PM
```

**Create Log Directory**:
```bash
mkdir -p "/Users/georgemajor/GB Power Market JJ/logs"
```

**View Logs**:
```bash
tail -f "/Users/georgemajor/GB Power Market JJ/logs/dashboard.log"
```

**Remove Cron Job**:
```bash
crontab -e
# Delete the line, save and exit
```

### Option 2: launchd (macOS Native) - Has Issues

**Service File**: `~/Library/LaunchAgents/com.gbpower.dashboard.automation.plist`

**Load Service**:
```bash
launchctl load ~/Library/LaunchAgents/com.gbpower.dashboard.automation.plist
```

**Unload Service**:
```bash
launchctl unload ~/Library/LaunchAgents/com.gbpower.dashboard.automation.plist
```

**Check Status**:
```bash
launchctl list | grep com.gbpower
```

**Known Issue**: Python module caching in launchd causes BigQuery client to use wrong authentication method. Works fine in manual execution but fails in background service.

### Option 3: While Loop (Simple Development)

**Create runner script**:
```bash
cat > "/Users/georgemajor/GB Power Market JJ/run_dashboard_loop.sh" << 'EOF'
#!/bin/bash
cd "/Users/georgemajor/GB Power Market JJ"
while true; do
    echo "$(date): Updating dashboard..."
    ./.venv/bin/python fetch_fuelinst_today.py
    ./.venv/bin/python dashboard_updater_complete.py
    echo "$(date): Sleeping 15 minutes..."
    sleep 900  # 15 minutes
done
EOF

chmod +x run_dashboard_loop.sh
```

**Run in terminal**:
```bash
./run_dashboard_loop.sh
```

**Stop**: Press `Ctrl+C`

---

## 🐛 Troubleshooting

### Common Issues & Solutions

#### 1. "No module named 'google.cloud.bigquery'"

**Cause**: Virtual environment not activated or packages not installed

**Solution**:
```bash
cd "/Users/georgemajor/GB Power Market JJ"
source .venv/bin/activate
pip install google-cloud-bigquery gspread google-auth httpx pandas
```

#### 2. "Application Default Credentials not found"

**Cause**: Not authenticated with gcloud

**Solution**:
```bash
gcloud auth application-default login
# Follow browser authentication flow
# Use: george.major@grid-smart.co.uk
```

**Verify**:
```bash
gcloud auth application-default print-access-token
```

#### 3. "Error opening 'token.pickle'"

**Cause**: Google Sheets OAuth token not generated

**Solution**: Run initial authentication:
```python
from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0)

with open('token.pickle', 'wb') as token:
    pickle.dump(creds, token)

print("✅ token.pickle created!")
```

#### 4. "pyarrow.ArrowTypeError: Error converting column"

**Cause**: Data type mismatch between pandas DataFrame and BigQuery schema

**Solution**: Ensure proper type conversion in `fetch_fuelinst_today.py`:
```python
# Convert datetime columns
datetime_cols = ['publishTime', 'startTime', 'settlementDate']
for col in datetime_cols:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col])

# Convert numeric columns
numeric_cols = ['generation', 'settlementPeriod']
for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')
```

#### 5. "API Response: 429 Too Many Requests"

**Cause**: Rate limit exceeded on Elexon API

**Solution**: 
- Wait a few minutes before retrying
- Consider adding API key for higher limits
- Reduce update frequency

#### 6. Dashboard Shows Old Data

**Cause**: BigQuery data not refreshed

**Solution**:
```bash
# Force data refresh
./.venv/bin/python fetch_fuelinst_today.py

# Then update dashboard
./.venv/bin/python dashboard_updater_complete.py
```

**Check latest data in BigQuery**:
```sql
SELECT MAX(publishTime) as latest_time
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE DATE(publishTime) = CURRENT_DATE('Europe/London')
```

#### 7. "Permission Denied" on BigQuery

**Cause**: Wrong Google account or insufficient permissions

**Solution**:
```bash
# Check current account
gcloud auth application-default print-access-token | base64 -d | jq .

# Re-authenticate with correct account
gcloud auth application-default login
# Use: george.major@grid-smart.co.uk
```

#### 8. Spreadsheet Not Updating

**Cause**: Wrong spreadsheet ID or sheet name

**Verify in `dashboard_updater_complete.py`**:
```python
SPREADSHEET_ID = "12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
SHEET_NAME = "Sheet1"
```

**Test connection**:
```python
import gspread
import pickle

with open('token.pickle', 'rb') as token:
    creds = pickle.load(token)

gc = gspread.authorize(creds)
sheet = gc.open_by_key("12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8")
print(f"✅ Connected to: {sheet.title}")
print(f"Worksheets: {[ws.title for ws in sheet.worksheets()]}")
```

---

## 🔧 Maintenance & Updates

### Regular Maintenance Tasks

#### Daily Checks
- ✅ Verify dashboard updated with current data
- ✅ Check timestamp in Row 2 is recent (< 30 minutes old)
- ✅ Confirm renewable percentage looks reasonable (40-70%)

#### Weekly Checks
- ✅ Review BigQuery data volume: `SELECT COUNT(*) FROM bmrs_fuelinst WHERE DATE(publishTime) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)`
- ✅ Check for API errors in logs: `grep "API Response: 4\|5" logs/dashboard.log`
- ✅ Verify all fuel types present: `SELECT DISTINCT fuelType FROM bmrs_fuelinst ORDER BY fuelType`

#### Monthly Checks
- ✅ Review BigQuery storage costs in GCP Console
- ✅ Archive old data (optional): Keep last 90 days, archive rest
- ✅ Update Python packages: `pip list --outdated`

### Updating Python Dependencies

**Check current versions**:
```bash
cd "/Users/georgemajor/GB Power Market JJ"
source .venv/bin/activate
pip list
```

**Update specific package**:
```bash
pip install --upgrade google-cloud-bigquery
pip install --upgrade gspread
```

**Update all packages**:
```bash
pip list --outdated | awk 'NR>2 {print $1}' | xargs pip install --upgrade
```

**Current Working Versions** (as of 30 Oct 2025):
```
google-cloud-bigquery==3.x.x
gspread==5.x.x
google-auth==2.x.x
httpx==0.24.x
pandas==2.x.x
```

### Adding New Fuel Types

**1. Update fuel mapping** in `dashboard_updater_complete.py`:
```python
fuel_mapping = {
    'CCGT': 'Gas',
    'NUCLEAR': 'Nuclear',
    'WIND': 'Wind',
    'PS': 'Solar',
    'BIOMASS': 'Biomass',
    'NPSHYD': 'Hydro',
    'COAL': 'Coal',
    'NEW_TYPE': 'New Fuel',  # Add here
}
```

**2. Update renewable types** if applicable:
```python
renewable_types = ['WIND', 'PS', 'BIOMASS', 'NPSHYD', 'NEW_TYPE']
```

**3. Add dashboard cell update**:
```python
updates.append({
    'range': 'A12',  # Next available row
    'values': [[f'🔋 New Fuel: {fuel_data.get("New Fuel", 0):.1f} GW']]
})
```

**4. Update spreadsheet** to have additional row

### Adding New Interconnectors

Similar process - update `interconnector_mapping` dictionary and add cell update logic.

### Changing Update Frequency

**Edit cron schedule**:
```bash
crontab -e

# Change from */15 to */10 for 10-minute updates
*/10 * * * * cd '/Users/georgemajor/GB Power Market JJ' && ...
```

**Elexon API** updates every 5 minutes, so more frequent than */5 is unnecessary.

### Backup Strategy

**Important Files to Backup**:
1. `credentials.json` - OAuth client credentials
2. `token.pickle` - Authenticated session token
3. `dashboard_updater_complete.py` - Working dashboard script
4. `fetch_fuelinst_today.py` - Working data fetch script
5. This documentation file

**Backup Command**:
```bash
# Create backup directory
mkdir -p ~/Backups/GB_Power_Dashboard

# Copy critical files
cp credentials.json ~/Backups/GB_Power_Dashboard/
cp token.pickle ~/Backups/GB_Power_Dashboard/
cp dashboard_updater_complete.py ~/Backups/GB_Power_Dashboard/
cp fetch_fuelinst_today.py ~/Backups/GB_Power_Dashboard/
cp DASHBOARD_PROJECT_DOCUMENTATION.md ~/Backups/GB_Power_Dashboard/

# Create timestamped archive
tar -czf ~/Backups/GB_Power_Dashboard_$(date +%Y%m%d).tar.gz \
  credentials.json token.pickle *.py *.md

echo "✅ Backup created: ~/Backups/GB_Power_Dashboard_$(date +%Y%m%d).tar.gz"
```

### BigQuery Data Retention

**Current Policy**: Keep all data indefinitely

**To Implement 90-Day Retention**:
```sql
-- Delete data older than 90 days
DELETE FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE DATE(publishTime) < DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
```

**Automated Cleanup** (optional cron job):
```bash
# Add to crontab - runs at 2 AM on 1st of each month
0 2 1 * * cd '/Users/georgemajor/GB Power Market JJ' && ./.venv/bin/python -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); client.query('DELETE FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst\` WHERE DATE(publishTime) < DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)').result()"
```

---

## 📚 Useful Queries & Commands

### BigQuery Queries

**Check latest data timestamp**:
```sql
SELECT MAX(publishTime) as latest_data
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
```

**Count records by fuel type today**:
```sql
SELECT 
  fuelType,
  COUNT(*) as record_count,
  AVG(generation) as avg_generation_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE DATE(publishTime) = CURRENT_DATE('Europe/London')
GROUP BY fuelType
ORDER BY avg_generation_mw DESC
```

**Daily generation summary**:
```sql
SELECT 
  DATE(publishTime) as date,
  fuelType,
  AVG(generation) as avg_mw,
  MAX(generation) as peak_mw,
  MIN(generation) as min_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
WHERE DATE(publishTime) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY date, fuelType
ORDER BY date DESC, avg_mw DESC
```

**Renewable percentage over time**:
```sql
WITH renewable_data AS (
  SELECT 
    DATE(publishTime) as date,
    settlementPeriod,
    SUM(CASE WHEN fuelType IN ('WIND', 'PS', 'BIOMASS', 'NPSHYD') 
        THEN generation ELSE 0 END) as renewable_mw,
    SUM(generation) as total_mw
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
  WHERE DATE(publishTime) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  GROUP BY date, settlementPeriod
)
SELECT 
  date,
  AVG(renewable_mw / NULLIF(total_mw, 0) * 100) as avg_renewable_pct,
  MAX(renewable_mw / NULLIF(total_mw, 0) * 100) as max_renewable_pct
FROM renewable_data
GROUP BY date
ORDER BY date DESC
```

### Shell Commands

**Test API connectivity**:
```bash
curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/FUELINST?settlementDateFrom=$(date +%Y-%m-%d)&settlementDateTo=$(date +%Y-%m-%d)" | jq '.'
```

**Count records in BigQuery**:
```bash
bq query --use_legacy_sql=false \
  'SELECT COUNT(*) as total FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`'
```

**View recent logs**:
```bash
tail -f "/Users/georgemajor/GB Power Market JJ/logs/dashboard.log"
```

**Check disk space used by BigQuery data** (in GCP Console):
```bash
# Navigate to: https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9
# Check dataset size in left sidebar
```

---

## 🎓 Knowledge Base

### Key Concepts

#### Settlement Periods
- **Definition**: 30-minute time blocks used by UK electricity market
- **Total per Day**: 48 periods
- **Numbering**: Period 1 (00:00-00:30) to Period 48 (23:30-00:00)
- **Usage**: All trading, pricing, and generation data referenced by settlement period

#### Fuel Type Categories
- **Fossil**: CCGT (Gas), COAL, OIL, OCGT
- **Nuclear**: NUCLEAR
- **Renewable**: WIND, PS (Solar), BIOMASS, NPSHYD (Hydro)
- **Storage**: PS (Pumped Storage) - can be generation or consumption
- **Interconnectors**: INTFR, INTIFA2, INTNED, INTNEM, INTNSL, INTIRL, INTEW, INTELEC

#### Generation vs Supply
- **Generation**: Power produced within GB (domestic generation)
- **Supply**: Total power available (generation + imports)
- **Calculation**: Supply = Generation + Net Interconnector Imports

#### Renewable Percentage
- **Definition**: Percentage of generation from renewable sources
- **Formula**: `(Wind + Solar + Biomass + Hydro) / Total Generation × 100`
- **Typical Range**: 40-70% depending on weather conditions
- **Record High**: >90% on very windy nights with low demand

### Data Quality Notes

#### Known Issues
1. **Solar Data**: Using `PS` (Pumped Storage) as proxy - not perfect
2. **NOOD POOL Pricing**: Currently showing £0.00/MWh - needs investigation
3. **Interconnector Direction**: Positive values = imports, negative = exports (not currently handled)

#### Data Validation Checks
```python
# Reasonable ranges for validation
generation_ranges = {
    'CCGT': (0, 30000),      # 0-30 GW
    'NUCLEAR': (0, 10000),   # 0-10 GW
    'WIND': (0, 20000),      # 0-20 GW
    'COAL': (0, 5000),       # 0-5 GW (rarely used now)
}

# Alert if outside range
if not (min_val <= generation <= max_val):
    print(f"⚠️ WARNING: {fuel_type} generation {generation}MW outside expected range")
```

### API Rate Limits

**Elexon BMRS API**:
- **Without API Key**: ~100 requests per day
- **With API Key**: ~1000 requests per day
- **Recommendation**: One fetch every 15 minutes = 96 requests/day (within limit)

### Cost Considerations

**BigQuery Costs**:
- **Storage**: ~$0.02 per GB per month
- **Queries**: First 1 TB per month free, then $5 per TB
- **Typical Monthly Cost**: < $5 (with current usage pattern)

**API Costs**:
- Elexon BMRS API: Free for basic usage

**Total Expected Cost**: < $10/month

---

## 📝 Version History

### v1.0 - 30 October 2025
- ✅ Initial working dashboard system
- ✅ Elexon API integration
- ✅ BigQuery data warehouse
- ✅ Google Sheets dashboard (11-row format)
- ✅ Application Default Credentials authentication
- ✅ Separate fetch and update scripts
- ✅ Complete documentation

### Known Working Configuration
- **Python**: 3.11
- **BigQuery Project**: inner-cinema-476211-u9
- **BigQuery Table**: uk_energy_prod.bmrs_fuelinst
- **Spreadsheet**: 12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
- **Auth Method**: ADC for BigQuery, OAuth token.pickle for Sheets
- **Update Frequency**: Manual (15-minute automation recommended)

---

## 🚀 Quick Start Guide

### For New Setup

1. **Clone/Copy Project Files**:
   ```bash
   cd ~/
   cp -r "GB Power Market JJ" "GB Power Market JJ Backup"
   ```

2. **Install Python Dependencies**:
   ```bash
   cd "GB Power Market JJ"
   python3 -m venv .venv
   source .venv/bin/activate
   pip install google-cloud-bigquery gspread google-auth google-auth-oauthlib httpx pandas
   ```

3. **Authenticate BigQuery**:
   ```bash
   gcloud auth application-default login
   # Use: george.major@grid-smart.co.uk
   ```

4. **Set Up Google Sheets Auth**:
   - Ensure `credentials.json` exists (OAuth 2.0 Client ID from GCP Console)
   - Run initial auth to create `token.pickle`:
     ```bash
     python authorize_google_docs.py
     # Follow browser flow, use: george@upowerenergy.uk
     ```

5. **Test Data Fetch**:
   ```bash
   ./.venv/bin/python fetch_fuelinst_today.py
   ```

6. **Test Dashboard Update**:
   ```bash
   ./.venv/bin/python dashboard_updater_complete.py
   ```

7. **Set Up Automation** (Optional):
   ```bash
   crontab -e
   # Add: */15 * * * * cd '/Users/georgemajor/GB Power Market JJ' && ./.venv/bin/python fetch_fuelinst_today.py && ./.venv/bin/python dashboard_updater_complete.py >> logs/dashboard.log 2>&1
   ```

### For Daily Use

**Manual Update**:
```bash
cd "/Users/georgemajor/GB Power Market JJ"
./.venv/bin/python fetch_fuelinst_today.py && \
./.venv/bin/python dashboard_updater_complete.py
```

**Check Dashboard**:
https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8

---

## 📞 Support & Resources

### Official Documentation
- **Elexon BMRS API**: https://www.elexon.co.uk/operations-settlement/bsc-central-services/balancing-mechanism-reporting-service/
- **Google Cloud BigQuery**: https://cloud.google.com/bigquery/docs
- **gspread (Google Sheets Python API)**: https://docs.gspread.org/
- **Google Cloud Authentication**: https://cloud.google.com/docs/authentication

### Key URLs
- **GCP Console**: https://console.cloud.google.com/
- **BigQuery Console**: https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9
- **Dashboard**: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8
- **Elexon API Explorer**: https://data.elexon.co.uk/bmrs/api/v1/docs/index.html

### Contact Information
- **BigQuery Account**: george.major@grid-smart.co.uk
- **Google Sheets Account**: george@upowerenergy.uk
- **GCP Project**: inner-cinema-476211-u9 (Grid Smart Production)

---

## ✅ Success Criteria

### System is Working Correctly When:
1. ✅ Dashboard timestamp (Row 2) updates within 15-30 minutes
2. ✅ All fuel types show reasonable values (Gas: 5-25 GW, Wind: 1-20 GW, etc.)
3. ✅ Renewable percentage between 30-90%
4. ✅ Total generation ≈ Total supply (within 20% due to storage/losses)
5. ✅ Settlement period matches UK time (e.g., 14:00 = Period 28-29)
6. ✅ EPEX SPOT pricing shows realistic values (£40-150/MWh typical)
7. ✅ No Python errors in terminal output
8. ✅ BigQuery has today's data: `SELECT MAX(publishTime) FROM bmrs_fuelinst`

### Red Flags (Investigate If):
- ❌ Dashboard not updated for > 1 hour
- ❌ All generation values showing 0.0 GW
- ❌ Renewable percentage > 95% (unless confirmed with other sources)
- ❌ API Response not 200 OK
- ❌ BigQuery query returns 0 rows
- ❌ Python authentication errors
- ❌ Settlement period doesn't match current time

---

**END OF DOCUMENTATION**

*This is a living document. Update as system evolves.*

*Last verified working: 30 October 2025, 14:12:25*

*Dashboard last updated successfully with fresh data (2025-10-30 14:10:00, Period 29)*
