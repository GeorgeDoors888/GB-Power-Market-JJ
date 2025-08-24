#!/bin/bash

# Run BOD analysis with the correct service account key
cd "$(dirname "$0")"

# Default dates (can be overridden with command line args)
START_DATE="2016-01-01"
END_DATE="$(date +%Y-%m-%d)"
GDOC_FLAG=""

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --start-date) START_DATE="$2"; shift ;;
        --end-date) END_DATE="$2"; shift ;;
        --no-gdoc) GDOC_FLAG="--no-gdoc" ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Check if venv exists and activate it
if [ -d "venv" ]; then
  source venv/bin/activate
  echo "Activated Python virtual environment"
else
  echo "No venv found - using system Python"
fi

# Use the new service account key file
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/service_account_key.json"
echo "Set GOOGLE_APPLICATION_CREDENTIALS to service_account_key.json"

# Check if the key file exists
if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  echo "Error: service_account_key.json not found!"
  echo "The analysis will run with limited functionality (no data from BigQuery)"
fi

# Create output directories
mkdir -p ./out/charts
mkdir -p ./out/tables

# Run the BOD analysis with date range
echo "Starting BOD analysis for period: $START_DATE to $END_DATE..."
python bod_analysis.py $GDOC_FLAG --start-date "$START_DATE" --end-date "$END_DATE"

# Check if the analysis was successful
if [ $? -eq 0 ]; then
  echo "BOD analysis completed successfully!"
  echo "Results are available in ./out/charts/ and ./out/tables/"
  
  # If Google Doc was generated, show the link
  if [ -z "$GDOC_FLAG" ]; then
    if [ -f "./out/latest_report_url.txt" ]; then
      echo "Google Doc report available at: $(cat ./out/latest_report_url.txt)"
    fi
  fi
else
  echo "BOD analysis failed. Please check the logs for errors."
fi
