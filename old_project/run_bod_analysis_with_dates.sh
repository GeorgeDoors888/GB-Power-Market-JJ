#!/bin/bash

# Run BOD analysis for a specific date range
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

# Make sure BigQuery credentials are available
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  if [ -f "client_secret.json" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/client_secret.json"
    echo "Set GOOGLE_APPLICATION_CREDENTIALS to client_secret.json"
  else
    echo "Warning: GOOGLE_APPLICATION_CREDENTIALS not set and client_secret.json not found"
    echo "The analysis will run with limited functionality (no data from BigQuery)"
  fi
fi

# Create output directories
mkdir -p ./out/charts
mkdir -p ./out/tables

# Run the BOD analysis with date range
echo "Starting BOD analysis for period: $START_DATE to $END_DATE..."
python bod_analysis.py $GDOC_FLAG --start-date "$START_DATE" --end-date "$END_DATE"

# Check if the analysis was successful
if [ $? -eq 0 ]; then
  echo "Analysis completed successfully!"
  echo "Results available in:"
  echo "  - KPI Summary: ./out/kpi_summary.txt"
  echo "  - Charts: ./out/charts/"
  echo "  - Data tables: ./out/tables/"
else
  echo "Analysis failed. Please check the error messages above."
fi
