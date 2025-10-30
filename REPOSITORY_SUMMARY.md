# Jibber Jabber - Elexon 278 Dataset Downloader

## Overview
Comprehensive UK energy data collection system with **278 Elexon Insights API datasets** + DNO (Distribution Network Operator) data.

## Repository Details
- **Location**: `~/jibber-jabber 24 august 2025 big bop`
- **GitHub**: `git@github.com:GeorgeDoors888/jibber-jabber-24-august-2025-big-bop.git`
- **Python Files**: 304 scripts
- **BigQuery Project**: `jibber-jabber-knowledge`
- **Dataset**: `uk_energy_prod`, `uk_energy_insights`

## Core Components

### 1. Elexon Insights API (278 Datasets)
**Configuration**: `insights_endpoints.generated.yml` (3,638 lines)

**Main Downloader**: `bulk_downloader.py`
- Async parallel downloading with configurable concurrency
- Automatic BigQuery table creation with schema inference
- Handles nested/complex JSON structures
- Direct upload to BigQuery (no local storage)
- Schema evolution support

**Dataset Categories**:
- Balancing mechanism data (BOD, BOALF)
- Generation data (fuel mix, outturn)
- Demand forecasts and actuals
- System frequency and warnings
- Market prices and imbalances
- Interconnector flows
- Settlement data
- And 270+ more...

### 2. Usage

```bash
# Download all 278 datasets
python bulk_downloader.py --start-date 2022-01-01 --end-date 2025-10-25

# Download specific datasets
python bulk_downloader.py --datasets NDF DEMAND_OUTTURN FUELINST FREQ --start-date 2024-01-01

# Configure concurrency (default: 6)
export INSIGHTS_CONCURRENCY=10
python bulk_downloader.py
```

### 3. BigQuery Integration
- **Auto-table creation** with inferred schemas
- **Schema merging** for new fields
- **Batch inserts** for performance
- **Error handling** and retry logic

### 4. DNO Data Collection
Additional scripts for Distribution Network Operator data:
- `collect_all_dno_data.py`
- `comprehensive_dno_collector.py`
- `download_all_dno_duos_files.py`

## Key Features

✅ **278 Elexon Insights API datasets**  
✅ **Async parallel downloads**  
✅ **Automatic BigQuery schema management**  
✅ **Date range windowing** for large queries  
✅ **DNO data collection**  
✅ **304 Python analysis/processing scripts**  
✅ **GitHub tracked**  

## Dependencies
- google-cloud-bigquery
- httpx (async HTTP)
- pandas, pyarrow
- python-dotenv
- tqdm (progress bars)

## Related Repositories
- `Jibber_jabber_deploy_30august2025` - Dashboard using Google Sheets
- `jibber-jabber-energy-analytics` - Energy analysis with BigQuery
