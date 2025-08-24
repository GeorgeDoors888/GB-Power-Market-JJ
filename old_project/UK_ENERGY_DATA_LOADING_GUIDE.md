# UK Energy Data Loading Guide

This guide will help you load real energy data into BigQuery for your energy dashboard and analysis system.

## 1. Prerequisites

Before loading data, ensure you have:

- Google Cloud SDK installed
- Python 3.6+ with virtual environment
- BigQuery and GCS permissions
- Authentication configured properly

## 2. Authentication Setup

To properly authenticate with Google Cloud:

```bash
# Login with your Google account
gcloud auth login

# Set up application default credentials
gcloud auth application-default login
```

This will create credentials at `~/.config/gcloud/application_default_credentials.json` that the scripts will use.

## 3. Loading Data

We've created two tools to simplify the data loading process:

### Option 1: Interactive Script (Recommended)

Run the interactive script which will guide you through the process:

```bash
chmod +x load_bq_data.sh
./load_bq_data.sh
```

This script will:
1. Check for required Python packages
2. Verify authentication is set up
3. Allow you to choose which data types to load
4. Let you filter by date
5. Handle the data loading process

### Option 2: Manual Loading

If you prefer more control, you can use the data loader script directly:

```bash
chmod +x bq_data_loader.py

# Load all data types
./bq_data_loader.py --data-type all

# Load specific data type
./bq_data_loader.py --data-type demand

# Load data from a specific date
./bq_data_loader.py --data-type demand --date-filter 2023-01-01

# Limit number of files processed
./bq_data_loader.py --data-type demand --max-files 10

# Just validate existing data without loading
./bq_data_loader.py --data-type all --validate-only

# Check authentication status
./bq_data_loader.py --check-auth
```

## 4. Data Types

The system supports loading these data types:

- `demand` - Electricity demand data
- `frequency` - Grid frequency data
- `generation` - Electricity generation data
- `balancing` - Balancing services data
- `warnings` - System warnings data
- `interconnector` - Interconnector flows data
- `carbon` - Carbon intensity data

## 5. Validation

After loading data, you should validate it with:

```bash
# Validate all data types
./bq_data_loader.py --validate-only --data-type all

# Validate specific data from a date
./bq_data_loader.py --validate-only --data-type demand --date-filter 2023-01-01
```

You can also check directly in BigQuery:

```bash
# Activate the virtual environment if not already activated
source venv/bin/activate

# Check row count for a specific table
python -c "from google.cloud import bigquery; client = bigquery.Client(); query = 'SELECT COUNT(*) as count FROM \`jibber-jabber-knowledge.uk_energy_prod.elexon_demand_outturn\`'; print(client.query(query).result().to_dataframe())"

# Check date range for a specific table
python -c "from google.cloud import bigquery; client = bigquery.Client(); query = 'SELECT MIN(settlement_date) as min_date, MAX(settlement_date) as max_date FROM \`jibber-jabber-knowledge.uk_energy_prod.elexon_demand_outturn\`'; print(client.query(query).result().to_dataframe())"
```

## 6. Troubleshooting

If you encounter issues:

1. **Authentication errors**: Run `gcloud auth application-default login` again
2. **Missing packages**: Run `pip install google-cloud-storage google-cloud-bigquery`
3. **Schema issues**: Check the logs in `bq_data_loading.log` for details
4. **Timeout errors**: Try loading smaller date ranges or fewer files
5. **Empty tables**: Make sure the GCS bucket has data in the expected locations

## 7. Next Steps

After loading data, you can:

1. Run the energy dashboard with real data
2. Perform analytics on the loaded data
3. Set up automated data loading schedules
4. Create BigQuery views for common queries

## 8. Additional Resources

- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [Google Cloud Storage Documentation](https://cloud.google.com/storage/docs)
- [Google Cloud Authentication Guide](https://cloud.google.com/docs/authentication/getting-started)
