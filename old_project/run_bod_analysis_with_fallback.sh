#!/bin/bash

# Run BOD analysis with local auth setup - suitable for development use
cd "$(dirname "$0")"

# Calculate date range (last 24 months)
START_DATE=$(date -v-24m +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)

# Check if venv exists and activate it
if [ -d "venv" ]; then
  source venv/bin/activate
  echo "Activated Python virtual environment"
else
  echo "No venv found - using system Python"
fi

# Create output directories
mkdir -p ./out/charts
mkdir -p ./out/tables

# Set up authentication for local development
echo "Setting up local authentication"
echo "1. First, try to authenticate using default credentials..."

# Run with application default credentials
python -c "
from google.cloud import bigquery
import sys

try:
    client = bigquery.Client()
    query_job = client.query('SELECT 1')
    result = query_job.result()
    print('Default authentication successful!')
    sys.exit(0)
except Exception as e:
    print(f'Default authentication failed: {e}')
    sys.exit(1)
"

# If default auth fails, run with synthetic data
if [ $? -ne 0 ]; then
    echo "2. Default authentication failed, using synthetic data instead."
    echo "Starting BOD analysis for last 24 months: $START_DATE to $END_DATE"
    echo "Using synthetic data"
    
    # Run the enhanced BOD analysis script with synthetic data
    python bod_analysis_enhanced.py --use-synthetic --start-date "$START_DATE" --end-date "$END_DATE"
    
    if [ $? -eq 0 ]; then
        echo "BOD analysis with synthetic data completed successfully!"
        echo "Results are available in ./out/charts/ and ./out/tables/"
    else
        echo "BOD analysis failed. Please check the logs for errors."
    fi
else
    echo "Starting BOD analysis for last 24 months: $START_DATE to $END_DATE"
    echo "Using real data from BigQuery"
    
    # Run the original BOD analysis script
    python bod_analysis.py --no-gdoc --start-date "$START_DATE" --end-date "$END_DATE"
    
    if [ $? -eq 0 ]; then
        echo "BOD analysis completed successfully!"
        echo "Results are available in ./out/charts/ and ./out/tables/"
    else
        echo "BOD analysis failed. Falling back to synthetic data..."
        python bod_analysis_enhanced.py --use-synthetic --no-gdoc --start-date "$START_DATE" --end-date "$END_DATE"
    fi
fi
