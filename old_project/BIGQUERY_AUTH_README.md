# BigQuery Authentication Solutions

This directory contains several solutions for authenticating with Google BigQuery for BOD (Bid-Offer Data) analysis.

## Solution 1: Simple Standalone Approach (Recommended)

The simplest approach uses these scripts:

1. `simple_bq_auth.py` - A standalone authentication helper that doesn't depend on other modules
2. `simple_bod_adapter.py` - A simplified adapter that performs BOD analysis without complex dependencies
3. `simple_bod_analysis.sh` - A shell script to run the BOD analysis with proper authentication

### How to Run

```bash
# Run the simple analysis script
./simple_bod_analysis.sh
```

This will:

1. Check and refresh Google Cloud authentication if needed
2. Test BigQuery connection
3. Ask for date range for analysis
4. Run the BOD analysis with proper error handling

You can also run the adapter directly:

```bash
# Activate virtual environment if needed
source venv/bin/activate

# Run with default settings (last 30 days)
./simple_bod_adapter.py

# Run with specific date range
./simple_bod_adapter.py --start-date 2025-01-01 --end-date 2025-08-23

# Run with synthetic data (no BigQuery connection needed)
./simple_bod_adapter.py --use-synthetic
```

## Solution 2: Comprehensive Approach

The more comprehensive approach uses:

1. `bq_auth.py` - A full-featured authentication module with caching and multiple methods
2. `run_bod_with_auth.py` - A Python script to authenticate and run analysis
3. `reset_credentials.sh` - A script to reset authentication and guide through setup

### Usage Instructions

```bash
# Reset credentials and run analysis
./reset_credentials.sh

# Or run the Python script directly
python run_bod_with_auth.py --start-date 2023-08-01 --end-date 2023-08-31
```

## Troubleshooting

If you encounter authentication issues:

1. Ensure Google Cloud SDK is installed:

   ```bash
   # Install gcloud CLI
   # For macOS:
   brew install --cask google-cloud-sdk
   
   # For other platforms, see:
   # https://cloud.google.com/sdk/docs/install
   ```

2. Login to Google Cloud:

   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```

3. Check your permissions:

   ```bash
   # List projects you have access to
   gcloud projects list
   
   # Set your project
   gcloud config set project YOUR_PROJECT_ID
   ```

4. Check service account key files:
   - Ensure `client_secret.json` or `service_account.json` exists in the project directory
   - Ensure the service account has BigQuery permissions

5. Test connection directly:

   ```bash
   python simple_bq_auth.py --test
   ```

## Directory Organization

- **direct_bod_analysis.py** - Main script for analyzing BOD data
- **simple_bq_auth.py** - Simple standalone authentication helper
- **bq_auth.py** - Comprehensive authentication module
- **simple_bod_analysis.sh** - Simple shell script for running analysis
- **reset_credentials.sh** - Script to reset and refresh credentials
- **run_bod_with_auth.py** - Python script to run analysis with authentication

## Requirements

- Python 3.6+
- Google Cloud SDK (recommended)
- Python packages:
  - google-cloud-bigquery
  - pandas
  - matplotlib (for visualization)
  - seaborn (optional, for enhanced visualization)
