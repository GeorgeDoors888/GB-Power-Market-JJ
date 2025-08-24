# BOD Analysis with Alternative Authentication

This package provides tools for analyzing BOD (Bid-Offer Data) from BigQuery with robust authentication handling.

## Key Files

1. `direct_bod_analysis.py` - The main analysis script with multiple authentication fallbacks
2. `bod_auth.py` - A standalone authentication module that can be imported into other scripts

## Features

- **Multiple Authentication Methods**: Tries various authentication methods in order:
  1. Service account JSON key file (explicit path)
  2. GOOGLE_APPLICATION_CREDENTIALS environment variable
  3. Common credential file locations
  4. Application Default Credentials (ADC)
  5. OAuth browser flow (if dependencies are available)
  6. Default authentication (works on GCP or with ADC)

- **Data Analysis**:
  - Load BOD, imbalance price, demand, and generation mix data
  - Generate visualizations and reports
  - Export to CSV and other formats

- **Synthetic Data**: Can generate synthetic data for testing or when real data is unavailable

## Requirements

```
pip install google-cloud-bigquery pandas matplotlib google-auth google-auth-oauthlib
            numpy seaborn pyarrow tabulate
```

For OAuth authentication (optional):
```
pip install google-auth-oauthlib
```

## Usage

### Direct BOD Analysis Script

```bash
# Basic usage
python direct_bod_analysis.py

# With date range
python direct_bod_analysis.py --start-date 2024-07-01 --end-date 2024-07-31

# With explicit service account key
python direct_bod_analysis.py --service-account /path/to/key.json

# With custom project/dataset/table
python direct_bod_analysis.py --project my-project --dataset energy_data --bod-table bid_offer_data

# Use synthetic data (no BigQuery access required)
python direct_bod_analysis.py --use-synthetic

# Debug mode
python direct_bod_analysis.py --debug
```

### Authentication Module

You can import the authentication module into your own scripts:

```python
from bod_auth import get_bigquery_client

# Get client with automatic authentication fallback
client = get_bigquery_client(
    project_id="your-project-id",
    service_account_path="/path/to/key.json",  # optional
    verbose=True  # optional
)

# Now use the client
if client:
    results = client.query("SELECT * FROM `project.dataset.table` LIMIT 10").to_dataframe()
    print(results)
else:
    print("Authentication failed")
```

## Authentication Troubleshooting

If you're having trouble authenticating:

1. Check if your service account has the necessary BigQuery permissions
2. Verify that GOOGLE_APPLICATION_CREDENTIALS environment variable is set correctly
3. Try running `gcloud auth application-default login` to set up ADC
4. For OAuth, ensure you have a valid `client_secret.json` file
5. When running on GCP, ensure the VM has the BigQuery permissions

## License

This software is provided for educational purposes only. Use at your own risk.
