# System Architecture: UK Power Market Data Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         DATA INGESTION PIPELINE                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌───────────────────┐
│  ELEXON BMRS API  │  https://data.elexon.co.uk/bmrs/api/v1
│                   │
│  82 Datasets      │  • Generation data
│  44 Working       │  • Interconnector flows
│  38 Unavailable   │  • Physical notifications
│                   │  • Demand/supply data
│  Public API       │  • Balancing services
│  No auth required │  • Market indices
└─────────┬─────────┘
          │
          │ HTTP GET requests
          │ JSON responses
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PYTHON INGESTION SCRIPTS                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. DISCOVERY PHASE                                                          │
│     ┌──────────────────────────────────────┐                                │
│     │  discover_all_datasets.py            │                                │
│     ├──────────────────────────────────────┤                                │
│     │  • Queries /datasets/metadata/latest │                                │
│     │  • Tests each dataset for access     │                                │
│     │  • Generates manifest JSON           │                                │
│     │  • Output: 44 working datasets       │                                │
│     └────────────┬─────────────────────────┘                                │
│                  │                                                           │
│                  ▼                                                           │
│     insights_manifest_dynamic.json                                           │
│                  │                                                           │
│  ────────────────┼──────────────────────────────────────────────────        │
│                  │                                                           │
│  2. DOWNLOAD PHASE                                                           │
│     ┌────────────▼─────────────────────────┐                                │
│     │  download_multi_year_streaming.py    │                                │
│     ├──────────────────────────────────────┤                                │
│     │  • Reads manifest                    │                                │
│     │  • Loops through datasets            │                                │
│     │  • Queries date range                │                                │
│     │  • Fetches data (paginated)          │                                │
│     │  • STREAMS to BigQuery               │                                │
│     │    └─> 50,000 records/batch          │                                │
│     │  • Automatic retries                 │                                │
│     └────────────┬─────────────────────────┘                                │
│                  │                                                           │
│                  │ Generator pattern                                         │
│                  │ Memory-efficient                                          │
│                  │                                                           │
└──────────────────┼───────────────────────────────────────────────────────────┘
                   │
                   │ Batch uploads
                   │ pandas-gbq
                   │ google-cloud-bigquery
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GOOGLE CLOUD BIGQUERY                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  Project: inner-cinema-476211-u9                                             │
│  Dataset: uk_energy_prod                                                     │
│  Location: US                                                                │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  TABLES (65 total, 7.2M records, 925 MB)                            │   │
│  ├─────────────────────────────────────────────────────────────────────┤   │
│  │                                                                      │   │
│  │  generation_actual_per_type        14,304 records  12 MB           │   │
│  │  ├─ startTime (STRING)                                              │   │
│  │  ├─ settlementPeriod (INTEGER)                                      │   │
│  │  └─ data (RECORD - nested array)                                    │   │
│  │     ├─ psrType: "Wind Offshore", "Nuclear", etc.                    │   │
│  │     └─ quantity: generation in MW                                   │   │
│  │                                                                      │   │
│  │  fuelinst_sep_oct_2025             24,160 records  15 MB           │   │
│  │  ├─ publishTime (STRING)                                            │   │
│  │  ├─ fuelType (STRING) - "INTFR", "INTNED", etc.                    │   │
│  │  └─ generation (INTEGER) - MW (pos=import, neg=export)             │   │
│  │                                                                      │   │
│  │  pn_sep_oct_2025                 6,396,546 records  377 MB         │   │
│  │  ├─ settlementDate (STRING)                                         │   │
│  │  ├─ settlementPeriod (INTEGER) - 1 to 48                           │   │
│  │  ├─ timeFrom / timeTo (STRING)                                      │   │
│  │  ├─ levelFrom / levelTo (INTEGER) - MW                             │   │
│  │  └─ bmUnit identifiers                                              │   │
│  │                                                                      │   │
│  │  demand_outturn_summary             7,194 records   1.2 MB         │   │
│  │  balancing_physical_mils          838,000 records  28 MB           │   │
│  │  ... 60 more tables ...                                             │   │
│  │                                                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
│  Authentication: jibber_jabber_key.json (service account)                    │
└──────────────────┬───────────────────────────────────────────────────────────┘
                   │
                   │ SQL queries
                   │ google-cloud-bigquery client
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PYTHON QUERY SCRIPTS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  update_dashboard_clean.py                                                   │
│  ├─ get_latest_generation()                                                  │
│  │  └─> Returns: { 'WIND': 19.52, 'NUCLEAR': 3.68, 'GAS': 3.22, ... }      │
│  │                                                                           │
│  ├─ get_interconnector_flows()                                               │
│  │  └─> Returns: { 'France': 1.50, 'Norway': 1.05, ... }                   │
│  │                                                                           │
│  ├─ get_latest_demand()                                                      │
│  │  └─> Returns: demand in GW                                               │
│  │                                                                           │
│  └─ update_google_sheet()                                                    │
│     └─> Updates cells with latest data                                      │
│                                                                              │
└──────────────────┬───────────────────────────────────────────────────────────┘
                   │
                   │ gspread library
                   │ Google Sheets API
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         GOOGLE SHEETS DASHBOARD                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────┐              │
│  │  UK Power Market Dashboard                                │              │
│  ├──────────────────────────────────────────────────────────┤              │
│  │                                                           │              │
│  │  Grid Frequency:     50.00 Hz                             │              │
│  │                                                           │              │
│  │  Generation:                                              │              │
│  │    Wind:            19.52 GW  ████████████████           │              │
│  │    Nuclear:          3.68 GW  ████                       │              │
│  │    Gas:              3.22 GW  ███                        │              │
│  │    Biomass:          0.84 GW  █                          │              │
│  │    Solar:            0.00 GW                             │              │
│  │                                                           │              │
│  │  Interconnectors:                                         │              │
│  │    France      →  1.50 GW IMPORT                         │              │
│  │    Norway      →  1.05 GW IMPORT                         │              │
│  │    Netherlands →  1.02 GW IMPORT                         │              │
│  │    Ireland     ←  0.21 GW EXPORT                         │              │
│  │                                                           │              │
│  │  Total Demand:      28.45 GW                              │              │
│  │  Net Import:         6.76 GW                              │              │
│  │                                                           │              │
│  │  Updated: 26 Oct 2025 13:00 (SP 27)                      │              │
│  └──────────────────────────────────────────────────────────┘              │
│                                                                              │
│  Access: Shared with service account email                                   │
│  Updates: Manual or automated (Apps Script / cron)                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Timeline

```
T=0     User runs: python download_multi_year_streaming.py --year 2025
        
T+1s    Script reads insights_manifest_dynamic.json
        Identifies 44 datasets to download
        
T+2s    Connects to Elexon API
        Queries first dataset: /datasets/PN/stream
        
T+10s   Receives first page of data (5000 records)
        Converts to pandas DataFrame
        
T+15s   Accumulates to 50,000 records (batch size)
        UPLOADS TO BIGQUERY
        Clears memory buffer
        
T+20s   Next 50,000 records ready
        UPLOADS TO BIGQUERY
        
... continues until dataset complete ...

T+1hr   First dataset complete (e.g., PN with 2.6M records)
        Moves to next dataset
        
T+2hr   Multiple datasets complete
        Progress report generated
        
T+4-5hr All 44 datasets downloaded for the year
        COMPLETE
```

---

## Query Flow

```
User runs: python update_dashboard_clean.py

1. Script connects to BigQuery
   
2. Executes SQL query:
   WITH latest_data AS (
       SELECT data FROM generation_actual_per_type
       ORDER BY startTime DESC LIMIT 1
   )
   SELECT gen.psrType, gen.quantity
   FROM latest_data, UNNEST(data) as gen
   
3. BigQuery scans ~14k records
   Returns latest settlement period data
   
4. Script processes results:
   - Converts MW to GW
   - Maps fuel types to friendly names
   - Combines wind offshore + onshore
   
5. Returns dictionary:
   {
     'WIND_TOTAL': 19.52,
     'NUCLEAR': 3.68,
     'GAS': 3.22,
     ...
   }
   
6. Optionally updates Google Sheet cells
   
7. Prints summary to console

Total time: <3 seconds
```

---

## Memory Management (Critical!)

### ❌ WITHOUT Streaming (OLD - FAILED)

```
Download PN dataset (16M records)

Step 1: Fetch all data from API
├─> Load 16M records into list
├─> Memory: 10GB... 20GB... 40GB...
└─> CRASH! Out of memory

RESULT: FAILURE
```

### ✅ WITH Streaming (NEW - SUCCESS)

```
Download PN dataset (16M records)

Step 1: Create generator function
        def fetch_data():
            for page in pages:
                for record in page:
                    yield record

Step 2: Process in batches
        batch = []
        for record in fetch_data():
            batch.append(record)
            
            if len(batch) >= 50,000:
                # Upload batch
                upload_to_bigquery(batch)
                
                # Clear memory
                batch = []

Memory usage stays at ~250MB throughout!

RESULT: SUCCESS ✅
```

---

## Settlement Period Timeline

```
Day Structure: 48 settlement periods × 30 minutes = 24 hours

00:00 ──┬── SP 1  ── 00:00-00:30
        ├── SP 2  ── 00:30-01:00
        ├── SP 3  ── 01:00-01:30
        ├── SP 4  ── 01:30-02:00
        │   ...
        ├── SP 12 ── 05:30-06:00  ← Morning ramp-up
        ├── SP 13 ── 06:00-06:30
        │   ...
        ├── SP 24 ── 11:30-12:00  ← Midday peak
        ├── SP 25 ── 12:00-12:30
        │   ...
        ├── SP 36 ── 17:30-18:00  ← Evening peak starts
        ├── SP 37 ── 18:00-18:30
        ├── SP 38 ── 18:30-19:00
        │   ...
        ├── SP 47 ── 22:00-22:30  ← Current generation data
        └── SP 48 ── 23:30-00:00

Latest data in BigQuery:
  Generation:     SP 47 (25 Oct, 22:00) - Wind 19.52 GW
  Interconnector: SP 24 (26 Oct, 11:35) - Net import 6.76 GW
```

---

## Storage Hierarchy

```
Google Cloud Project: inner-cinema-476211-u9
│
└── BigQuery Dataset: uk_energy_prod
    │
    ├── generation_actual_per_type (14,304 rows, 12 MB)
    │   └── Stores: Daily generation mix by fuel type
    │
    ├── fuelinst_sep_oct_2025 (24,160 rows, 15 MB)
    │   └── Stores: Real-time fuel/interconnector data
    │
    ├── pn_sep_oct_2025 (6,396,546 rows, 377 MB)
    │   └── Stores: BM unit physical notifications
    │
    ├── demand_outturn_summary (7,194 rows, 1.2 MB)
    │   └── Stores: Actual demand data
    │
    └── ... 61 more tables ...

Total: 7,226,526 rows across 65 tables = 925 MB
```

---

## Interconnector Map

```
                    ┌──────────────┐
                    │   NORWAY     │
                    │   (INTNSL)   │
                    │   1.05 GW →  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
          DENMARK   │              │   NETHERLANDS
          (INTVKL) ─┤              ├─  (INTNED)
          0.88 GW → │              │   1.02 GW →
                    │              │
                    │   UK GRID    │
                    │              │
          FRANCE    │              │   BELGIUM
          (INTFR)  ─┤              ├─  (INTEW/INTNEM)
          1.50 GW → │              │   1.02 GW →
          (INTIFA2) │              │   0.22 GW ←
          0.99 GW → │              │
          (INTELEC) │              │
          1.00 GW → │              │   IRELAND
                    │              ├─  (INTIRL)
                    │              │   0.21 GW ←
                    └──────────────┘

Total Import:  8.46 GW
Total Export:  0.70 GW
Net Import:    6.76 GW
```

---

## Authentication Chain

```
User's Machine
│
├── jibber_jabber_key.json (Service Account Credentials)
│   ├── client_email: xxxxxxx@inner-cinema-476211-u9.iam.gserviceaccount.com
│   └── private_key: (encrypted key)
│
│   Set in environment:
│   export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"
│
├── Python Script
│   └── google.cloud.bigquery.Client(project='inner-cinema-476211-u9')
│       └── Reads credentials from environment variable
│           └── Authenticates with Google Cloud
│
└── Google Cloud
    └── Verifies service account
        └── Checks project permissions
            └── Grants access to BigQuery dataset
                └── Allows read/write operations
```

---

## Success Indicators

```
✅ API Connection
   └─> discover_all_datasets.py finds 44 working datasets

✅ Data Ingestion
   └─> download_sep_oct_2025.py: 36M records, 0 failures

✅ BigQuery Storage
   └─> 65 tables, 7.2M rows, 925 MB

✅ Data Retrieval
   └─> Queries return actual generation data:
       Wind: 19.52 GW, Nuclear: 3.68 GW, Gas: 3.22 GW

✅ Real-time Data
   └─> Latest interconnector data: 1.4 hours old
       Latest PN data: Real-time (0 hours old)

✅ Documentation
   └─> Complete technical docs with examples

STATUS: OPERATIONAL ✅
```

---

This architecture diagram shows the complete data pipeline from API to dashboard!
