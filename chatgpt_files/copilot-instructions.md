# GB Power Market JJ - AI Coding Agent Instructions

## Project Overview
UK energy market data platform with dual-pipeline architecture: historical batch data (Elexon BMRS API) + real-time streaming (IRIS/Azure Service Bus) → BigQuery → Google Sheets dashboards. Enables ChatGPT natural language queries via secure Vercel proxy.

**Core Mission**: Battery arbitrage analysis, VLP (Virtual Lead Party) revenue tracking, grid frequency monitoring, and market price analysis.

## Critical Configuration (Always Verify First)

### ⚠️ BEFORE ANY BIGQUERY OPERATION
```python
PROJECT_ID = "inner-cinema-476211-u9"  # NOT jibber-jabber-knowledge!
DATASET = "uk_energy_prod"             # Primary dataset
LOCATION = "US"                        # NOT europe-west2!
```

**Common Trap**: Two GCP projects exist but `jibber-jabber-knowledge` lacks `bigquery.jobs.create` permission. Always use `inner-cinema-476211-u9`.

### ⚠️ MPAN PARSING (Critical for DNO Lookup)
```python
# In dno_lookup_python.py - ALWAYS use these imports
from mpan_generator_validator import extract_core_from_full_mpan, mpan_core_lookup
MPAN_PARSER_AVAILABLE = True
```

**Common Trap**: Import from `mpan_parser` (doesn't exist) instead of `mpan_generator_validator`. This causes fallback to legacy parsing which extracts wrong distributor ID.

**Correct Parsing Flow**:
1. Full MPAN `00800999932 1405566778899` → Extract core `1405566778899`
2. Core first 2 digits `14` → NGED West Midlands
3. Query BigQuery for DNO details and rates
4. Update Google Sheets with correct information

**Test Command**:
```bash
python3 dno_lookup_python.py 14 HV  # Should return NGED West Midlands, Red: 1.764 p/kWh
```

### Python Environment
```bash
python3  # NOT `python` on macOS
pip3 install --user google-cloud-bigquery db-dtypes pyarrow pandas gspread
export GOOGLE_APPLICATION_CREDENTIALS="inner-cinema-credentials.json"
```

## Data Architecture: The Two-Pipeline System

### Historical Pipeline (Batch, 2020-present)
- **Tables**: `bmrs_bod`, `bmrs_fuelinst`, `bmrs_freq`, `bmrs_mid` (174+ tables)
- **Source**: Elexon BMRS REST API
- **Update**: On-demand via `ingest_elexon_fixed.py` or 15-min cron
- **Key table**: `bmrs_bod` = 391M+ rows of bid-offer data (NOT acceptances!)

### Real-Time Pipeline (IRIS, last 24-48h)
- **Tables**: `bmrs_*_iris` suffix (e.g., `bmrs_fuelinst_iris`)
- **Source**: Azure Service Bus streaming
- **Deployment**: AlmaLinux server (94.237.55.234)
- **Scripts**: `iris-clients/python/client.py` → `iris_to_bigquery_unified.py`

### Query Pattern for Complete Timeline
```sql
-- Always UNION historical + real-time for full coverage
WITH combined AS (
  SELECT CAST(settlementDate AS DATE) as date, ...
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
  WHERE settlementDate < '2025-10-30'  -- Adjust cutoff
  UNION ALL
  SELECT CAST(settlementDate AS DATE) as date, ...
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
  WHERE settlementDate >= '2025-10-30'
)
SELECT * FROM combined
```

## Schema Gotchas (Prevent Hours of Debugging)

### bmrs_bod - Bid-Offer Data
```sql
-- ❌ WRONG columns (doesn't exist): acceptanceId, acceptanceTime
-- ✅ CORRECT columns:
bmUnitId          -- NOT bmUnit!
pairId            -- Bid-offer pair ID
offer FLOAT64     -- Offer price (£/MWh)
bid FLOAT64       -- Bid price
```

### bmrs_freq - Frequency Data
```sql
-- ❌ WRONG: recordTime
-- ✅ CORRECT: measurementTime
SELECT measurementTime, frequency FROM bmrs_freq
```

### Data Type Incompatibilities
```sql
-- Historical: DATETIME
-- Hybrid tables (demand_outturn): STRING
-- Fix: CAST both to DATE for joins
CAST(settlementDate AS DATE) = CAST(demand_date AS DATE)
```

## Development Workflow

### Before Writing ANY Query
```bash
# 1. Check table date coverage first!
./check_table_coverage.sh bmrs_bod

# 2. Read the reference docs
open STOP_DATA_ARCHITECTURE_REFERENCE.md  # Prevents repeating data issues
open PROJECT_CONFIGURATION.md             # All config settings
```

### Script Template (Copy This)
```python
from google.cloud import bigquery
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
client = bigquery.Client(project=PROJECT_ID, location="US")

query = f"""
SELECT ... 
FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
WHERE settlementDate >= '2025-01-01'
LIMIT 1000  -- Always limit during dev!
"""

df = client.query(query).to_dataframe()
print(f"✅ Retrieved {len(df)} rows")
```

### Testing BigQuery Access
```bash
python3 -c 'from google.cloud import bigquery; client = bigquery.Client(project="inner-cinema-476211-u9"); print("✅ Connected")'
```

## Key Directories & Their Purpose

```
~/GB Power Market JJ/
├── PROJECT_CONFIGURATION.md          # ⭐ Read first - all settings
├── STOP_DATA_ARCHITECTURE_REFERENCE.md  # ⭐ Prevents data issues
├── UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md  # Pipeline design
│
├── update_analysis_bi_enhanced.py    # Main dashboard refresh script
├── advanced_statistical_analysis_enhanced.py  # Stats suite
│
├── iris_windows_deployment/          # IRIS real-time pipeline
│   ├── scripts/client.py             # Message downloader
│   └── scripts/iris_to_bigquery_unified.py  # Uploader
│
├── drive-bq-indexer/                 # Google Drive → BigQuery indexer
├── vercel-proxy/                     # ChatGPT proxy endpoint
└── codex-server/                     # FastAPI search server
```

## Deployment Architecture

### Live Services
- **Google Sheets Dashboard**: [12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8](https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/)
- **ChatGPT Proxy**: https://gb-power-market-jj.vercel.app/api/proxy-v2
- **IRIS Pipeline**: AlmaLinux server 94.237.55.234
- **Generator Map**: http://94.237.55.15/gb_power_comprehensive_map.html

### Deployment Commands
```bash
# Refresh Google Sheets dashboard (MANUAL)
python3 update_analysis_bi_enhanced.py

# Dashboard auto-refresh (AUTO - runs every 5 min via cron)
python3 realtime_dashboard_updater.py  # Test manual run
tail -f logs/dashboard_updater.log     # Monitor auto-updates

# Enhanced dashboard with charts (NEW)
python3 enhance_dashboard_layout.py    # Create professional layout
python3 format_dashboard.py            # Apply formatting
# Then install charts: Extensions → Apps Script → paste dashboard_charts.gs → Run

# Check IRIS pipeline status
ssh root@94.237.55.234 'ps aux | grep iris'

# Deploy to Vercel
cd vercel-proxy && vercel --prod

# Monitor IRIS uploads
ssh root@94.237.55.234 'tail -f /opt/iris-pipeline/logs/iris_uploader.log'
```

## Business Logic: Battery VLP Analysis

### Virtual Lead Party (VLP) Units
**What**: Battery operators submitting bids to National Grid balancing mechanism  
**Revenue Model**: Charge cheap → discharge expensive (system imbalance arbitrage)  
**Key Units**: FBPGM002 (Flexgen), FFSEN005 (likely Gresham House/Harmony Energy)

### High-Value Analysis Periods
- **Oct 17-23, 2025**: £79.83/MWh avg (6-day high-price event = 80% of VLP revenue)
- **Oct 24-25, 2025**: £30.51/MWh avg (price crash from wind surge)
- **Strategy**: Aggressive deploy at £70+/MWh, preserve cycles at £25-40/MWh

### Key Tables for VLP Analysis
```sql
-- Market prices
bmrs_mid (systemSellPrice, systemBuyPrice)

-- Balancing acceptances  
bmrs_boalf (acceptanceNumber, acceptanceTime)

-- Individual unit generation
bmrs_indgen_iris (bmUnitId, generation)

-- Frequency response
bmrs_freq (frequency)  -- Stability = revenue opportunity
```

## Common Pitfalls & Solutions

### 1. "Table not found in europe-west2"
```python
# ❌ Wrong
client = bigquery.Client(location="europe-west2")

# ✅ Correct
client = bigquery.Client(project="inner-cinema-476211-u9", location="US")
```

### 2. "Access Denied: jibber-jabber-knowledge"
**Root Cause**: Limited permissions on secondary project  
**Fix**: Always use `inner-cinema-476211-u9`

### 3. "Unrecognized name: recordTime"
**Root Cause**: Wrong column name in `bmrs_freq`  
**Fix**: Use `measurementTime` instead

### 4. Missing Recent Data
**Root Cause**: Historical tables lag ~24h, need IRIS tables  
**Fix**: UNION with `*_iris` tables (see query pattern above)

### 5. "ModuleNotFoundError: db_dtypes"
```bash
pip3 install --user db-dtypes pyarrow pandas-gbq
```

## Testing Strategy

### Quick Validation
```bash
# Health check
curl "https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/health"

# Query test
python3 -c 'from google.cloud import bigquery; client = bigquery.Client(project="inner-cinema-476211-u9"); print("OK")'

# IRIS data freshness
python3 check_iris_data.py
```

### Before Committing
1. Test query with `LIMIT 100` first
2. Verify date ranges: `./check_table_coverage.sh TABLE_NAME`
3. Check for schema issues: Read `STOP_DATA_ARCHITECTURE_REFERENCE.md`
4. Validate outputs exist in expected location

## External Integrations

### ChatGPT → BigQuery Flow
1. ChatGPT sends natural language query
2. Vercel Edge Function (`/api/proxy-v2`) receives request
3. SQL validation + execution via BigQuery client
4. JSON response back to ChatGPT
5. **Security**: SQL validation, project whitelist, rate limiting

### Google Sheets Apps Script
```javascript
// Correct endpoint usage
var url = 'https://gb-power-market-jj.vercel.app/api/proxy-v2?path=/query_bigquery_get';
var payload = { sql: 'SELECT ...' };
var response = UrlFetchApp.fetch(url, { method: 'post', payload: JSON.stringify(payload) });
```

## Documentation Navigation

**Start Here**: `PROJECT_CONFIGURATION.md` → `STOP_DATA_ARCHITECTURE_REFERENCE.md` → `README.md`

**Analysis**: `STATISTICAL_ANALYSIS_GUIDE.md`, `ENHANCED_BI_ANALYSIS_README.md`  
**Deployment**: `DEPLOYMENT_COMPLETE.md`, `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md`  
**ChatGPT Setup**: `CHATGPT_INSTRUCTIONS.md`, `CHATGPT_ACTUAL_ACCESS.md`  
**Full Index**: `DOCUMENTATION_INDEX.md` (22 files categorized)

## Performance & Cost Optimization

- **BigQuery**: Free tier sufficient (queries <<1TB/month)
- **Vercel**: Free tier (Edge Functions)
- **Railway**: Free tier (FastAPI backend)
- **IRIS Pipeline**: Self-hosted (AlmaLinux VPS ~$5/month)

### Query Optimization
```sql
-- ❌ Expensive: SELECT * on 391M rows
SELECT * FROM bmrs_bod

-- ✅ Cheap: Filter first, aggregate
SELECT bmUnitId, AVG(offer) as avg_offer
FROM bmrs_bod
WHERE settlementDate >= '2025-10-01'
GROUP BY bmUnitId
```

## DNO Lookup & DUoS Rates System

### Architecture
**Button Trigger → Webhook → Python → Google Sheets API**

1. **Apps Script Button** (`bess_auto_trigger.gs`): `manualRefreshDno()` function
2. **Webhook Server** (`dno_webhook_server.py`): Flask on port 5001, exposed via ngrok
3. **Python Script** (`dno_lookup_python.py`): BigQuery + postcodes.io + gspread
4. **Google Sheets**: BESS sheet with DNO info and DUoS rates

### BESS Sheet Layout

```
Row 6:  A6=Postcode | B6=MPAN ID | C6-H6=DNO Details
Row 9:  A9=Voltage  | B9=Red Rate | C9=Amber | D9=Green
Row 10: "Weekday Times:" header
Row 11: Red times   | Amber times | Green times
Row 12: (continued) | (continued) | (continued)
Row 13: (continued) | (continued) | Weekend note
```

### Example Output
```
UKPN-EPN (Eastern), HV voltage:
- Red: 4.837 p/kWh (16:00-19:30 weekdays)
- Amber: 0.457 p/kWh (08:00-16:00, 19:30-22:00 weekdays)
- Green: 0.038 p/kWh (00:00-08:00, 22:00-23:59 weekdays + all weekend)
```

### Running Services
```bash
# Webhook server (background)
python3 dno_webhook_server.py

# ngrok tunnel
ngrok http 5001
# Update webhook URL in bess_auto_trigger.gs

# Manual test
python3 dno_lookup_python.py 10 HV  # MPAN ID, voltage
```

### Key Files
- `dno_lookup_python.py` - Main lookup script (gspread + BigQuery)
- `dno_webhook_server.py` - Flask webhook receiver
- `bess_auto_trigger.gs` - Apps Script button handler
- BigQuery tables:
  - `uk_energy_prod.neso_dno_reference` - DNO details
  - `gb_power.duos_unit_rates` - DUoS rates by DNO/voltage
  - `gb_power.duos_time_bands` - Time periods for Red/Amber/Green

## Contact & Support

**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Status**: ✅ Production (Nov 2025)

---

*Last Updated: November 22, 2025*  
*For updates to this guide, see: `CHANGELOG.md`*
