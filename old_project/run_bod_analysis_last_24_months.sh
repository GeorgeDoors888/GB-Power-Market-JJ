#!/bin/bash

# Run the BOD analysis for the last 24 months with real data
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

# Use the proper service account key file
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/service_account_key.json"
echo "Set GOOGLE_APPLICATION_CREDENTIALS to service_account_key.json"

# Check if the key file exists
if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  echo "Error: service_account_key.json not found!"
  exit 1
fi

# Create output directories
mkdir -p ./out/charts
mkdir -p ./out/tables

# Print what we're doing
echo "Starting BOD analysis for last 24 months: $START_DATE to $END_DATE"
echo "Using real data from BigQuery"

# Run the original BOD analysis script
echo "Running analysis with real data..."
python bod_analysis.py --no-gdoc --start-date "$START_DATE" --end-date "$END_DATE"

# Check if the analysis was successful
if [ $? -eq 0 ]; then
  echo "BOD analysis completed successfully!"
  echo "Results are available in ./out/charts/ and ./out/tables/"
else
  echo "BOD analysis failed. Falling back to enhanced script with synthetic data..."
  python bod_analysis_enhanced.py --use-synthetic --no-gdoc --start-date "$START_DATE" --end-date "$END_DATE"
fi
