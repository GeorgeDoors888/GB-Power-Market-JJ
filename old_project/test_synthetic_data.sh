#!/bin/bash

# Test the enhanced BOD analysis with synthetic data
cd "$(dirname "$0")"

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

# Run the enhanced BOD analysis with synthetic data
echo "Starting synthetic data test for BOD analysis..."
python bod_analysis_enhanced.py --use-synthetic --debug --no-gdoc --start-date "2023-01-01" --end-date "2023-01-31"

# Check if the analysis was successful
if [ $? -eq 0 ]; then
  echo "Synthetic data test completed successfully!"
else
  echo "Synthetic data test failed. Please check the logs for errors."
fi
