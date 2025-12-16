# 🔧 Project Configuration Reference

**Last Updated**: 31 October 2025  
**Purpose**: Single source of truth for all project configuration, credentials, and environment settings

---

## 📋 Quick Reference Card

```yaml
Project Name: GB Power Market JJ (Jibber Jabber)
Repository: https://github.com/GeorgeDoors888/jibber-jabber-24-august-2025-big-bop
Local Path: ~/GB Power Market JJ
Python Version: 3.9.6
Shell: zsh (macOS)
```

---

## 🗄️ BigQuery Configuration

### Primary Project: `inner-cinema-476211-u9`

**⚠️ CRITICAL**: This is the MAIN project for all data operations.

```yaml
Project ID: inner-cinema-476211-u9
Region: US  # ⚠️ NOT europe-west2!
Primary Dataset: uk_energy_prod
Dataset Location: US  # ⚠️ Must match for all queries!
```

#### Available Datasets
| Dataset | Location | Purpose | Tables |
|---------|----------|---------|--------|
| `uk_energy_prod` | US | Main BMRS data (Historical + IRIS) | 174+ tables |
| `uk_energy_prod_eu` | europe-west2 | EU mirror (if exists) | TBD |
| `gb_power` | US | Additional power data | TBD |
| `companies_house` | US | Companies House data | TBD |

### Secondary Project: `jibber-jabber-knowledge`

**⚠️ ISSUE**: You do NOT have `bigquery.jobs.create` permission on this project.

```yaml
Project ID: jibber-jabber-knowledge
Region: europe-west2
Status: ❌ Limited access - cannot create query jobs
Use Case: Legacy scripts only (DO NOT USE for new work)
```

**Action Required**: Always use `inner-cinema-476211-u9` for BigQuery operations.

---

## 📊 Database Schema Reference

### Table Naming Conventions

Your project uses **BMRS naming** (not Elexon naming):

#### Historical Tables (Batch Data)
```
bmrs_bod              # Bid-Offer Data (391M+ rows)
bmrs_fuelinst         # Generation by fuel type (5.7M rows)
bmrs_freq             # System frequency measurements
bmrs_mid              # Market Index Data (prices)
bmrs_netbsad          # Net Balancing System Adjustment Data
bmrs_disbsad          # Disaggregated Balancing Services Data
bmrs_qas              # Quality assurance statistics
bmrs_mels             # Maximum Export Limit
bmrs_mils             # Maximum Import Limit
... (174 total tables)
```

#### Real-Time Tables (IRIS Streaming)
```
bmrs_fuelinst_iris    # Real-time generation (last 24-48h)
bmrs_freq_iris        # Real-time frequency (last 24-48h)
bmrs_mid_iris         # Real-time prices (last 24-48h)
... (8+ IRIS tables)
```

### Key Schema Details

#### `bmrs_bod` (Bid-Offer Data)
**⚠️ IMPORTANT**: This table uses **bid/offer pairs**, NOT acceptance data!

**Actual Columns**:
```sql
-- Correct schema (verified Oct 31, 2025)
timeFrom          TIMESTAMP
timeTo            TIMESTAMP
settlementDate    DATE
settlementPeriod  INT64
bmUnitId          STRING  -- ⚠️ Called bmUnitId, not bmUnit!
pairId            INT64
levelFrom         FLOAT64
levelTo           FLOAT64
offer             FLOAT64  -- Offer price (£/MWh)
bid               FLOAT64  -- Bid price (£/MWh)
```

**❌ WRONG Schema** (don't use):
```sql
-- This schema does NOT exist in your tables
soFlag                    # ❌ No such column
bmUnit                    # ❌ It's called bmUnitId
bidOfferAcceptanceLevel   # ❌ No acceptance columns
bidOfferAcceptancePrice   # ❌ No acceptance columns
```

#### `bmrs_boalf_complete` (Balancing Acceptance Prices) 🆕
**⚠️ DERIVED TABLE**: Created by joining `bmrs_boalf` + `bmrs_bod` to derive missing price fields.

**Background**: Elexon BOALF API returns acceptance records but lacks `acceptancePrice`, `acceptanceVolume`, and `acceptanceType` fields. This table derives these fields by matching with BOD submissions.

**Actual Columns**:
```sql
-- Primary data
acceptanceNumber    STRING      -- Unique acceptance ID
acceptanceTime      TIMESTAMP   -- When acceptance occurred
bmUnit              STRING      -- BM Unit (e.g., FBPGM002)
settlementDate      TIMESTAMP   -- Settlement date
settlementPeriod    INTEGER     -- Settlement period (1-48)

-- Level changes
levelFrom           INTEGER     -- Starting MW level
levelTo             INTEGER     -- Ending MW level

-- Derived price fields (from BOD matching)
acceptancePrice     FLOAT       -- £/MWh (from BOD offer/bid)
acceptanceVolume    FLOAT       -- MWh (ABS of level change)
acceptanceType      STRING      -- BID | OFFER | UNKNOWN

-- Elexon B1610 Section 4.3 compliance
validation_flag     STRING      -- Valid | SO_Test | Low_Volume | Price_Outlier | Unmatched

-- Metadata flags
soFlag              BOOLEAN     -- System Operator test record (TRUE = exclude)
storFlag            BOOLEAN     -- STOR flag
rrFlag              BOOLEAN     -- Replacement Reserve flag
deemedBoFlag        BOOLEAN     -- Deemed Bid-Offer flag

-- Source tracking
_price_source       STRING      -- BOD_MATCH | BOD_REALTIME | UNMATCHED
_matched_pairId     STRING      -- BOD pairId used for matching
_ingested_utc       TIMESTAMP   -- Upload timestamp
```

**Data Quality** (as of Dec 2025):
- Total records: ~11M acceptances (2022-2025)
- Match rate: 85-95% (varies by month)
- Valid records: ~42.8% after Elexon B1610 filtering
- Partitioned: Daily by `settlementDate`
- Clustered: By `bmUnit` (optimized for VLP battery queries)

**Validation Flag Taxonomy**:
- `Valid`: Passes all Elexon B1610 filters (±£1,000/MWh, volume ≥0.001 MWh, soFlag=FALSE)
- `SO_Test`: System Operator test record (soFlag=TRUE) - excluded per B1610
- `Low_Volume`: Acceptance volume <0.001 MWh - below regulatory threshold
- `Price_Outlier`: Price exceeds ±£1,000/MWh - non-physical/test pricing
- `Unmatched`: No matching BOD submission found

**Usage**: For battery arbitrage analysis, filter to `validation_flag='Valid'` or use the `boalf_with_prices` view.

#### `bmrs_freq` (Frequency)
**⚠️ IMPORTANT**: Timestamp column is `measurementTime`, NOT `recordTime`!

**Actual Columns**:
```sql
measurementTime   TIMESTAMP  -- ⚠️ NOT recordTime!
frequency         FLOAT64    -- Hz
```

#### `bmrs_fuelinst` (Generation)
```sql
publishTime       TIMESTAMP
settlementDate    DATE
settlementPeriod  INT64
fuelType          STRING     -- WIND, CCGT, NUCLEAR, etc.
generation        FLOAT64    -- MW
```

#### `bmrs_mid` (Market Prices)
```sql
settlementDate    DATE
settlementPeriod  INT64
price             FLOAT64    -- £/MWh
```

---

## 🐍 Python Environment

### System Python
```bash
Python: /usr/bin/python3  # Python 3.9.6
Command: python3          # ⚠️ NOT "python" on macOS!
```

### Virtual Environment (if using)
```bash
Venv Path: ./.venv
Activation: source .venv/bin/activate
Python: ./.venv/bin/python
```

### Required Packages
```bash
# Core BigQuery
google-cloud-bigquery==3.38.0
google-cloud-storage
db-dtypes==1.4.3          # ⚠️ Required for BigQuery DataFrame conversion
pyarrow==21.0.0

# Data processing
pandas==2.3.2
numpy==2.0.2
pandas-gbq==0.29.2

# Statistical analysis
scipy==1.13.1
statsmodels==0.14.5
matplotlib==3.9.4

# Google Sheets
gspread
gspread-formatting
oauth2client

# IRIS (Azure Service Bus)
dacite
azure-servicebus
azure-identity
```

### Installation Commands
```bash
# Install all at once
pip3 install --user google-cloud-bigquery google-cloud-storage db-dtypes pyarrow pandas numpy pandas-gbq scipy statsmodels matplotlib gspread gspread-formatting oauth2client

# Or install specific packages
pip3 install --user db-dtypes            # If missing
pip3 install --user matplotlib scipy statsmodels  # For statistical analysis
```

---

## 📂 Project Structure

```
~/GB Power Market JJ/
├── PROJECT_CONFIGURATION.md              # ⭐ THIS FILE
├── UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md  # Architecture master doc
├── ENHANCED_BI_ANALYSIS_README.md        # Google Sheets dashboard docs
├── STATISTICAL_ANALYSIS_GUIDE.md         # Statistical analysis operational guide
│
├── Core Scripts (Data Refresh)
│   ├── update_analysis_bi_enhanced.py    # Main dashboard refresh
│   ├── update_analysis_with_calculations.py  # Advanced calculations
│   ├── create_analysis_bi_enhanced.py    # Initial sheet setup
│   └── read_full_sheet.py                # Sheet validator
│
├── Statistical Analysis
│   ├── advanced_statistical_analysis_enhanced.py  # ⚠️ Needs schema updates
│   └── statistical_analysis_output/      # Output directory for plots
│
├── Historical Pipeline
│   ├── ingest_elexon_fixed.py            # Batch download
│   ├── fetch_fuelinst_today.py           # Today's generation
│   └── update_graph_data.py              # Legacy dashboard
│
├── IRIS Pipeline (Real-Time)
│   ├── iris-clients/python/client.py     # Message downloader
│   ├── iris_to_bigquery_unified.py       # Processor → BigQuery
│   └── automated_iris_dashboard.py       # IRIS dashboard
│
└── Configuration Files
    ├── .gcloud_credentials.json          # GCP service account (if exists)
    ├── api.env                           # API keys
    └── requirements.txt                  # Python dependencies
```

---

## 🔐 Authentication & Credentials

### Google Cloud (BigQuery)

**Default Authentication**: User credentials via `gcloud`

```bash
# Check current authentication
gcloud auth list

# Login if needed
gcloud auth login

# Set default project
gcloud config set project inner-cinema-476211-u9
```

### Google Sheets API

**Credentials File**: `~/.config/gspread/service_account.json`

**Sheet ID**: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`

**URL**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

### IRIS (Azure Service Bus)

**Configuration**: Stored in IRIS client config (see `iris-clients/python/client.py`)

---

## ⚙️ Script Configuration Templates

### Template 1: BigQuery Query Script

```python
"""
Template for BigQuery query scripts
Save as: my_analysis_script.py
"""
from google.cloud import bigquery
import pandas as pd

# ============================================
# CONFIGURATION - UPDATE THESE VALUES
# ============================================
PROJECT_ID = "inner-cinema-476211-u9"           # ⚠️ ALWAYS use inner-cinema
LOCATION = "US"                                  # ⚠️ Dataset location is US
DATASET = "uk_energy_prod"                       # Main dataset
OUTPUT_DATASET = "uk_energy_prod"                # Or create separate analytics dataset

# ============================================
# INITIALIZATION
# ============================================
client = bigquery.Client(project=PROJECT_ID, location=LOCATION)

# ============================================
# QUERY
# ============================================
query = f"""
SELECT 
    settlementDate,
    fuelType,
    SUM(generation) as total_generation
FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
WHERE settlementDate >= '2025-10-01'
GROUP BY settlementDate, fuelType
ORDER BY settlementDate, fuelType
"""

# ============================================
# EXECUTE & PROCESS
# ============================================
df = client.query(query).to_dataframe()
print(f"Retrieved {len(df)} rows")
print(df.head())
```

### Template 2: Google Sheets Update Script

```python
"""
Template for Google Sheets update scripts
Save as: my_sheet_updater.py
"""
import gspread
from google.oauth2.service_account import Credentials
from google.cloud import bigquery
import pandas as pd

# ============================================
# CONFIGURATION
# ============================================
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
SHEET_NAME = "Analysis BI Enhanced"              # Or your sheet name
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# ============================================
# GOOGLE SHEETS AUTH
# ============================================
scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]
creds = Credentials.from_service_account_file(
    '~/.config/gspread/service_account.json',
    scopes=scopes
)
gc = gspread.authorize(creds)
sheet = gc.open_by_key(SHEET_ID).worksheet(SHEET_NAME)

# ============================================
# BIGQUERY SETUP
# ============================================
bq_client = bigquery.Client(project=PROJECT_ID)

# ============================================
# YOUR CODE HERE
# ============================================
# 1. Query BigQuery
# 2. Process data
# 3. Update sheet
```

### Template 3: UNION Query (Historical + IRIS)

```sql
-- Template for combining Historical + IRIS data
-- Use this pattern for all time-series queries

WITH combined AS (
  -- Historical data (older records)
  SELECT 
    publishTime as ts,
    fuelType,
    generation,
    'historical' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
  WHERE publishTime >= '2025-10-01'
  
  UNION ALL
  
  -- Real-time IRIS data (last 24-48 hours)
  SELECT 
    publishTime as ts,
    fuelType,
    generation,
    'iris' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
  WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 48 HOUR)
)

SELECT 
  ts,
  fuelType,
  SUM(generation) as total_generation,
  COUNTIF(source='historical') as hist_count,
  COUNTIF(source='iris') as iris_count
FROM combined
GROUP BY ts, fuelType
ORDER BY ts
```

---

## 🚨 Common Pitfalls & Solutions

### Issue 1: "command not found: python"
**Problem**: macOS doesn't have `python` command, only `python3`

**Solution**: Always use `python3` in commands
```bash
# ❌ Wrong
python my_script.py

# ✅ Correct
python3 my_script.py
```

### Issue 2: "Access Denied: Project jibber-jabber-knowledge"
**Problem**: You don't have permissions on jibber-jabber-knowledge project

**Solution**: Use `inner-cinema-476211-u9` instead
```python
# ❌ Wrong
PROJECT_ID = "jibber-jabber-knowledge"

# ✅ Correct
PROJECT_ID = "inner-cinema-476211-u9"
```

### Issue 3: "Dataset not found in location europe-west2"
**Problem**: Dataset is in US region, not europe-west2

**Solution**: Set location to "US"
```python
# ❌ Wrong
LOCATION = "europe-west2"

# ✅ Correct
LOCATION = "US"
```

### Issue 4: "Table elexon_* not found"
**Problem**: Script uses wrong table naming (elexon_* instead of bmrs_*)

**Solution**: Use bmrs_* table names
```sql
-- ❌ Wrong
FROM elexon_bid_offer_acceptances

-- ✅ Correct
FROM bmrs_bod
```

### Issue 5: "Unrecognized name: recordTime"
**Problem**: bmrs_freq uses `measurementTime`, not `recordTime`

**Solution**: Use correct column name
```sql
-- ❌ Wrong
WHERE recordTime >= '2025-10-01'

-- ✅ Correct
WHERE measurementTime >= '2025-10-01'
```

### Issue 6: "Unrecognized name: bmUnit"
**Problem**: bmrs_bod uses `bmUnitId`, not `bmUnit`

**Solution**: Use correct column name
```sql
-- ❌ Wrong
SELECT bmUnit

-- ✅ Correct
SELECT bmUnitId
```

### Issue 7: "ModuleNotFoundError: No module named 'db_dtypes'"
**Problem**: Missing required package for BigQuery DataFrame conversion

**Solution**: Install db-dtypes
```bash
pip3 install --user db-dtypes pyarrow
```

---

## 📋 Pre-Flight Checklist

Before running any new script, verify:

- [ ] **Python command**: Using `python3` (not `python`)
- [ ] **Project ID**: Set to `inner-cinema-476211-u9` (not jibber-jabber-knowledge)
- [ ] **Location**: Set to `"US"` (not europe-west2)
- [ ] **Dataset**: Using `uk_energy_prod` (not uk_energy)
- [ ] **Table names**: Using `bmrs_*` (not elexon_*)
- [ ] **Column names**: 
  - bmrs_bod → `bmUnitId` (not bmUnit)
  - bmrs_freq → `measurementTime` (not recordTime)
  - bmrs_bod → `offer`, `bid` columns (not acceptance columns)
- [ ] **Required packages**: Installed (google-cloud-bigquery, pandas, db-dtypes)
- [ ] **Authentication**: Logged in via `gcloud auth login`

---

## 🔗 Quick Links

| Resource | Link |
|----------|------|
| Google Sheet Dashboard | https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/ |
| GitHub Repository | https://github.com/GeorgeDoors888/jibber-jabber-24-august-2025-big-bop |
| BigQuery Console (inner-cinema) | https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9 |
| GCP IAM & Admin | https://console.cloud.google.com/iam-admin/iam?project=inner-cinema-476211-u9 |

---

## 📝 Change Log

| Date | Change | Author |
|------|--------|--------|
| 2025-10-31 | Created PROJECT_CONFIGURATION.md with all critical settings | GitHub Copilot |
| 2025-10-30 | Two-Pipeline Architecture implemented (Historical + IRIS) | - |
| 2025-10-31 | Schema fixes: bmrs_bod columns, bmrs_freq measurementTime | GitHub Copilot |

---

## 🎯 Next Steps After Reading This

1. **Bookmark this file** - Refer to it before starting any new script
2. **Update existing scripts** - Fix any hardcoded project IDs, locations, or table names
3. **Create script templates** - Use templates from this doc for new scripts
4. **Test BigQuery access**:
   ```bash
   python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ BigQuery access working!')"
   ```
5. **Verify dataset location**:
   ```bash
   python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); ds = client.get_dataset('uk_energy_prod'); print(f'Dataset location: {ds.location}')"
   ```

---

**Remember**: When in doubt, check this file first! 🎯
