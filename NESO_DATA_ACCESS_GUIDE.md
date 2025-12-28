# NESO Data Portal Access Guide
**Generated**: 28 December 2025
**Status**: API Unavailable - Manual Access Required

---

## Current Status

### NESO CKAN API Issue ⚠️
The NESO Data Portal CKAN API at `https://data.nationalgrideso.com/api/3/` is currently returning empty results:
- `package_list`: 0 datasets
- `package_search`: Empty results for "constraint", "interconnector", etc.

**Possible causes**:
1. API temporarily down for maintenance
2. API endpoint changed (CKAN version upgrade)
3. Authentication now required
4. Domain migration in progress

### Alternative Access Methods

#### Method 1: Web Browser (RECOMMENDED)
1. Navigate to https://data.nationalgrideso.com/
2. Use search bar for keywords: "constraint", "interconnector", "forecast"
3. Manually download CSV/JSON files
4. Note resource IDs from dataset URLs

#### Method 2: Direct Dataset URLs
If you know the dataset name, try:
```bash
https://data.nationalgrideso.com/dataset/DATASET_NAME
```

Common dataset patterns:
- `historic-gb-system-constraints`
- `interconnector-flows`
- `day-ahead-wind-forecast`
- `demand-outturn`

#### Method 3: Check for New API Documentation
- Visit: https://data.nationalgrideso.com/support
- Look for API documentation or developer guides
- May have moved to GraphQL or REST API v2

---

## Existing NESO Data in BigQuery

We already have NESO reference data:

```sql
-- DNO (Distribution Network Operator) reference
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`

-- DNO geographical boundaries
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries`

-- GSP (Grid Supply Point) groups
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.neso_gsp_groups`

-- GSP geographical boundaries
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.neso_gsp_boundaries`
```

**Source**: These were likely ingested from earlier NESO portal access or manual uploads.

---

## Priority NESO Datasets for VLP Analysis

### 1. System Constraints (HIGH PRIORITY)
**Why needed**: Understand when grid constraints trigger VLP dispatch

**Dataset**: Historic GB System Constraints
- **Columns**: Timestamp, constraint type, location, volume (MW), cost (£)
- **Usage**: Correlate VLP revenue spikes with constraint events
- **BigQuery table**: `neso_system_constraints`

### 2. Interconnector Flows (MEDIUM PRIORITY)
**Why needed**: Cross-border flows affect UK imbalance prices

**Dataset**: Interconnector Physical Flows
- **Columns**: Timestamp, interconnector name, flow (MW), direction
- **Interconnectors**: IFA, IFA2, ElecLink, BritNed, Nemo Link, Moyle, EWIC, NSL
- **Usage**: Explain price volatility when imports/exports change suddenly
- **BigQuery table**: `neso_interconnector_flows`

### 3. Wind Forecasts (MEDIUM PRIORITY)
**Why needed**: Forecast errors drive imbalance and VLP opportunity

**Dataset**: Day-Ahead Wind Forecast vs Actual
- **Columns**: Timestamp, forecast (MW), actual (MW), error (MW)
- **Usage**: Identify high-variance periods = high VLP revenue opportunity
- **BigQuery table**: `neso_wind_forecast`

### 4. Demand Outturn (LOW PRIORITY)
**Why needed**: Demand forecast errors also drive imbalance

**Dataset**: Demand Outturn (National)
- **Columns**: Timestamp, forecast (MW), actual (MW)
- **Status**: May already have this from BMRS INDDEM/MELIMBALNGC
- **BigQuery table**: Check existing `bmrs_inddem` or `demand_outturn`

---

## Manual Ingestion Workflow (Until API Fixed)

### Step 1: Identify Dataset URLs
1. Search NESO portal via web browser
2. Find dataset page (e.g., `https://data.nationalgrideso.com/dataset/historic-gb-system-constraints`)
3. Note resource ID from download button

### Step 2: Download CSV/JSON
```bash
# Example pattern (adjust based on actual dataset structure)
wget "https://data.nationalgrideso.com/resource/RESOURCE_ID.csv" -O neso_constraints.csv
```

### Step 3: Upload to BigQuery
```python
from google.cloud import bigquery
import pandas as pd
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

# Read CSV
df = pd.read_csv('neso_constraints.csv')

# Upload to BigQuery
table_id = 'inner-cinema-476211-u9.uk_energy_prod.neso_system_constraints'
job = client.load_table_from_dataframe(df, table_id)
job.result()
print(f"✅ Uploaded {len(df)} rows")
```

### Step 4: Document Resource ID
Create `NESO_RESOURCE_IDS.json`:
```json
{
  "system_constraints": {
    "dataset_url": "https://data.nationalgrideso.com/dataset/historic-gb-system-constraints",
    "resource_id": "RESOURCE_ID_HERE",
    "last_updated": "2025-12-28",
    "bigquery_table": "neso_system_constraints"
  }
}
```

---

## Automated Ingestion Scripts (For When API Fixed)

### Script 1: Constraints Ingestion
**File**: `ingest_neso_constraints.py` (to be created)
- Poll NESO API for constraint events
- Parse timestamp, type, location, cost
- Upload to BigQuery partitioned by date
- Run daily via cron

### Script 2: Interconnector Ingestion
**File**: `ingest_neso_interconnectors.py` (to be created)
- Fetch real-time interconnector flows
- 8 interconnectors × 48 settlement periods = 384 rows/day
- Track flow direction (import/export)
- Upload to BigQuery

### Script 3: Wind Forecast Reconciliation
**File**: `reconcile_wind_forecast.py` (to be created)
- Fetch day-ahead wind forecast
- Compare vs actual from BMRS `bmrs_windfor` + `bmrs_fuelinst`
- Calculate forecast error (MW and %)
- Upload error analysis to BigQuery

---

## Next Steps

1. **Immediate**: Try manual web browser access to locate datasets
2. **Short-term**: Contact NESO support about API status
3. **Medium-term**: Create scraping scripts if API unavailable
4. **Long-term**: Automate with proper API once restored

---

## API Troubleshooting Checklist

- [ ] Try CKAN API v2 endpoints (different path?)
- [ ] Check for authentication requirements (API key?)
- [ ] Test with different HTTP headers (User-Agent, Accept)
- [ ] Use wget/curl with verbose flags to see redirects
- [ ] Check NESO Twitter/blog for API maintenance notices
- [ ] Email NESO data team: data@nationalgrideso.com

---

**Last Updated**: 28 December 2025
**Status**: Awaiting API restoration or manual dataset identification
