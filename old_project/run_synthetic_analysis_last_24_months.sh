#!/bin/bash

# Run BOD analysis with high-quality synthetic data for the last 24 months
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

# Print what we're doing
echo "Starting BOD analysis for last 24 months: $START_DATE to $END_DATE"
echo "Using high-quality synthetic data"

# Run the enhanced BOD analysis script with synthetic data
echo "Running analysis with synthetic data..."
python bod_analysis_enhanced.py --use-synthetic --debug --start-date "$START_DATE" --end-date "$END_DATE"

# Check if the analysis was successful
if [ $? -eq 0 ]; then
  echo "BOD analysis with synthetic data completed successfully!"
  echo "Results are available in ./out/charts/ and ./out/tables/"
else
  echo "BOD analysis failed. Please check the logs for errors."
fi
