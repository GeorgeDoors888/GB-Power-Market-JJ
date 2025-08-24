# Elexon & NESO Data Collection System

This system provides a comprehensive solution for collecting, storing, and analyzing UK energy data from Elexon BMRS (Balancing Mechanism Reporting Service) and National Energy System Operator (NESO) data sources. The system is designed to handle historical data backfilling (from 2016 to present) as well as ongoing data collection.

## System Components

1. **Enhanced Elexon & NESO Downloader** (`enhanced_elexon_neso_downloader.py`)
   - Downloads data from Elexon BMRS API
   - Stores raw data in Google Cloud Storage (GCS)
   - Handles rate limiting, retries, and error recovery
   - Supports configurable date ranges for backfilling

2. **Enhanced BigQuery Loader** (`enhanced_bigquery_loader.py`)
   - Loads data from GCS to BigQuery tables
   - Handles schema mapping and data transformation
   - Supports incremental loading and validation
   - Parallel processing for efficient loading

3. **Deployment Script** (`deploy_data_collectors.sh`)
   - Orchestrates the download and load process
   - Verifies data completeness and quality
   - Handles error recovery and reporting
   - Provides detailed logging

## Setup Requirements

- Python 3.7+ with the following packages:
  - google-cloud-storage
  - google-cloud-bigquery
  - requests
- Google Cloud SDK (gcloud)
- Valid Elexon BMRS API key (stored in `api.env` or as environment variable)
- Google Cloud project with:
  - BigQuery dataset created
  - GCS bucket created
  - Proper IAM permissions

## Configuration

### API Key Setup

Create an `api.env` file with your Elexon BMRS API key:

```
BMRS_API_KEY="your-api-key-here"
```

### Google Cloud Setup

Authenticate with Google Cloud:

```bash
gcloud auth login
gcloud config set project jibber-jabber-knowledge
```

## Usage

### Deploying the Complete System

To download and load all datasets from 2016 to present:

```bash
./deploy_data_collectors.sh
```

This script will:
1. Check prerequisites (auth, API keys, etc.)
2. Process each dataset in sequence
3. Verify data completeness in BigQuery
4. Generate detailed logs in the `logs` directory

### Running Individual Components

#### Data Downloader

```bash
python3 enhanced_elexon_neso_downloader.py \
  --start-date 2016-01-01 \
  --end-date 2025-08-25 \
  --datasets bid_offer_acceptances \
  --bucket jibber-jabber-knowledge-bmrs-data \
  --project jibber-jabber-knowledge \
  --dataset-id uk_energy_prod
```

Available options:
- `--start-date`: Start date in YYYY-MM-DD format
- `--end-date`: End date in YYYY-MM-DD format
- `--datasets`: Specific datasets to download (space-separated)
- `--bucket`: GCS bucket name
- `--project`: GCP project ID
- `--dataset-id`: BigQuery dataset ID
- `--max-days`: Maximum days per API request (default: 7)
- `--list-datasets`: List available datasets and exit

#### BigQuery Loader

```bash
python3 enhanced_bigquery_loader.py \
  --start-date 2016-01-01 \
  --end-date 2025-08-25 \
  --datasets bid_offer_acceptances \
  --bucket jibber-jabber-knowledge-bmrs-data \
  --project jibber-jabber-knowledge \
  --dataset-id uk_energy_prod
```

Available options:
- `--start-date`: Start date in YYYY-MM-DD format
- `--end-date`: End date in YYYY-MM-DD format
- `--datasets`: Specific datasets to load (space-separated)
- `--bucket`: GCS bucket name
- `--project`: GCP project ID
- `--dataset-id`: BigQuery dataset ID
- `--max-workers`: Maximum number of parallel workers per dataset (default: 4)
- `--list-datasets`: List available datasets and exit
- `--validate-schema`: Validate dataset schemas and exit

## Available Datasets

The system supports the following datasets:

| Dataset Key | Description | Available From | Priority |
|-------------|-------------|----------------|----------|
| bid_offer_acceptances | Balancing Mechanism bid and offer acceptances | 2016 | Very High |
| generation_outturn | Actual electricity generation by fuel type | 2016 | Very High |
| demand_outturn | Actual electricity demand measurements | 2016 | Very High |
| system_warnings | Grid warnings and notices | 2016 | High |
| frequency | Grid frequency measurements | 2016 | High |
| fuel_instructions | Real-time monitoring of fuel types and output levels | 2016 | Very High |
| individual_generation | Performance metrics for each power station | 2016 | Very High |
| market_index | Electricity market pricing indices | 2018 | Medium |
| wind_forecasts | Wind generation forecasts | 2017 | High |
| balancing_services | Balancing services adjustment data | 2018 | High |
| carbon_intensity | Grid carbon intensity measurements | 2018 | Medium |

## Troubleshooting

### Common Issues

1. **API Rate Limiting**
   - The downloaders include backoff logic, but you may still hit rate limits
   - Solution: Adjust the delay between requests or split into smaller date ranges

2. **BigQuery Schema Mismatches**
   - If API response formats change, schema validation may fail
   - Solution: Run with `--validate-schema` to check and update schemas as needed

3. **Missing Data for Specific Date Ranges**
   - Some endpoints have gaps or only go back to certain dates
   - Solution: Check the dataset configuration for start_year values

### Logs

Detailed logs are stored in the `logs` directory:
- `deployment_YYYYMMDD_HHMMSS.log`: Main deployment log
- `download_dataset_YYYYMMDD_HHMMSS.log`: Downloader logs for specific datasets
- `load_dataset_YYYYMMDD_HHMMSS.log`: Loader logs for specific datasets

## Maintenance and Updates

### Updating API Endpoints

If the Elexon BMRS API changes, update the `ELEXON_BASE_URL` in `enhanced_elexon_neso_downloader.py` and adjust the dataset endpoint configurations as needed.

### Adding New Datasets

To add a new dataset:
1. Add its configuration to the `_configure_datasets` method in `enhanced_elexon_neso_downloader.py`
2. Add its mapping to the `_configure_dataset_mappings` method in `enhanced_bigquery_loader.py`
3. Ensure a corresponding BigQuery table exists with the appropriate schema

## Contributing

When contributing to this project:
1. Follow the existing code style and patterns
2. Add appropriate error handling and logging
3. Update documentation when adding new features
4. Test thoroughly with sample data before deploying

## License

This project is proprietary and confidential. Unauthorized copying, transfer, or use is strictly prohibited.
