# Elexon Insights Data Ingestion

## 📂 Copied Files (26 October 2025)

### Main Ingestion Scripts
- **`bulk_downloader.py`** (12KB) - Main async downloader for 278 Elexon datasets
- **`elexon_neso_downloader.py`** (11KB) - Unified Elexon/NESO API downloader
- **`historic_downloader.py`** (2.4KB) - Historical data ingestion
- **`unified_downloader.py`** (17KB) - Unified data downloader with error handling

### Configuration Files
- **`insights_endpoints.generated.yml`** (107KB) - 278 dataset definitions (3,638 lines)
- **`insights_endpoints.with_units.yml`** (43KB) - Extended metadata with units (2,409 lines)

### Analysis & Support
- **`analyze_complete_datasets.py`** (17KB) - Dataset completeness analysis
- **`requirements.txt`** (299B) - Python dependencies

## 🎯 What This Does

Downloads **278 Elexon API datasets** directly into BigQuery:
- **BMRS (Balancing Mechanism)**: ~49 datasets
- **Insights API**: ~229 datasets

### Key Features
- ✅ Async parallel downloads (configurable concurrency)
- ✅ Automatic BigQuery table creation
- ✅ Schema evolution (adds new fields automatically)
- ✅ Date windowing for large queries
- ✅ Direct upload (no local CSV storage)
- ✅ Error handling and retry logic

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure GCP authentication
gcloud auth login
gcloud auth application-default login
gcloud config set project jibber-jabber-knowledge
gcloud config set compute/region europe-west2
```

### 2. Environment Variables
```bash
export GOOGLE_CLOUD_PROJECT="jibber-jabber-knowledge"
export GOOGLE_CLOUD_REGION="europe-west2"
export BIGQUERY_DATASET="uk_energy_insights"
export TZ="Europe/London"
export INSIGHTS_CONCURRENCY=10  # Parallel downloads
```

### 3. Run Data Ingestion

#### Full Historical Download
```bash
# Download all datasets (2022-present)
python bulk_downloader.py --start-date 2022-01-01 --end-date 2025-10-25

# Recent data only
python bulk_downloader.py --start-date 2024-01-01 --end-date 2025-10-25
```

#### Specific Datasets
```bash
# Key datasets only
python bulk_downloader.py \
    --datasets NDF DEMAND_OUTTURN FUELINST FREQ BOD BOALF \
    --start-date 2024-01-01 \
    --end-date 2025-10-25
```

#### Incremental Updates (Daily Cron)
```bash
# Update yesterday's data
python bulk_downloader.py \
    --start-date $(date -v-1d +%Y-%m-%d) \
    --end-date $(date +%Y-%m-%d)
```

## 📦 BigQuery Structure

**Project**: `jibber-jabber-knowledge`  
**Dataset**: `uk_energy_insights`  
**Location**: `europe-west2` (London, UK)

**Tables** (278 total):
- `bmrs_dynamic_data_per_bmu_*`
- `bmrs_market_wide_*`
- `bmrs_physical_data_*`
- `insights_demand_outturn`
- `insights_generation_mix`
- `insights_system_frequency`
- ... and 270+ more

## 🔧 Advanced Configuration

### Custom Date Windowing
Some datasets require smaller date ranges:
```yaml
dataset:
  window_days: 7  # Query in 7-day chunks
```

### High Concurrency
```bash
# Fast downloads with 20 parallel requests
export INSIGHTS_CONCURRENCY=20
python bulk_downloader.py
```

### Schema Evolution
Tables automatically update when new fields appear:
```python
def ensure_bq_table(client, table_id, sample_row, default_project):
    """
    Creates table if missing
    Adds new columns if schema evolved
    Preserves existing data
    """
```

## 📖 Key Datasets

### Critical Datasets
- **BOD**: Balancing Mechanism Bid-Offer Data
- **BOALF**: Balancing Mechanism Bid-Offer Acceptance Levels
- **FUELINST**: Instantaneous generation by fuel type
- **DEMAND_OUTTURN**: Actual demand
- **NDF**: National Demand Forecast
- **FREQ**: System frequency
- **IMBALANCE_PRICE**: Energy imbalance prices

### Full List
See `insights_endpoints.generated.yml` for all 278 datasets.

## 🛡️ Safe Execution

For heavy downloads, use the safe runner to prevent terminal crashes:
```bash
# In parent repo directory
python ~/repo/safe_runner.py 'python bulk_downloader.py --start-date 2024-01-01 --end-date 2025-10-25'

# Or with enhanced monitoring
python ~/repo/enhanced_safe_runner.py bulk_downloader.py --start-date 2024-01-01 --end-date 2025-10-25
```

## 🔗 Source Repository

**Original**: `~/jibber-jabber 24 august 2025 big bop`  
**GitHub**: `git@github.com:GeorgeDoors888/jibber-jabber-24-august-2025-big-bop.git`

## 📝 Dependencies

```
google-cloud-bigquery>=3.0.0
httpx>=0.24.0
pandas>=2.0.0
pyarrow>=12.0.0
python-dotenv>=1.0.0
tqdm>=4.65.0
google-auth
google-auth-oauthlib
google-auth-httplib2
```

## 🎛️ Monitoring

Check dataset completeness:
```bash
python analyze_complete_datasets.py
```

## 📅 Last Updated
26 October 2025

## 🤝 Maintainer
GeorgeDoors888
