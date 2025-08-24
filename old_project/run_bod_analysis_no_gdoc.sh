#!/bin/bash

# Auto-run BOD analysis with proper error handling (skips Google Doc report)
cd "$(dirname "$0")"

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

# Run the BOD analysis with the --no-gdoc flag
echo "Starting BOD analysis (skipping Google Doc report)..."
python bod_analysis.py --no-gdoc "$@"

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
