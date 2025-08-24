#!/bin/bash
# auto_generate_data.sh
#
# Wrapper script to automate data generation without prompts or approvals
# Usage: ./auto_generate_data.sh [--force] [--tables TABLE1 TABLE2...]

# Set up Python environment
source venv/bin/activate 2>/dev/null || echo "No virtualenv found, using system Python"

# Set the default arguments
ARGS="--no-prompt"

# Process script arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --force)
      ARGS="$ARGS --force"
      shift
      ;;
    --tables)
      shift
      TABLES=""
      # Collect all tables until the next flag
      while [[ $# -gt 0 && ! $1 == --* ]]; do
        TABLES="$TABLES $1"
        shift
      done
      if [[ ! -z "$TABLES" ]]; then
        ARGS="$ARGS --tables $TABLES"
      fi
      ;;
    --days)
      shift
      if [[ $# -gt 0 ]]; then
        ARGS="$ARGS --days $1"
        shift
      fi
      ;;
    --start-date)
      shift
      if [[ $# -gt 0 ]]; then
        ARGS="$ARGS --start-date $1"
        shift
      fi
      ;;
    --end-date)
      shift
      if [[ $# -gt 0 ]]; then
        ARGS="$ARGS --end-date $1"
        shift
      fi
      ;;
    *)
      echo "Unknown option: $1"
      shift
      ;;
  esac
done

# Set status file to include timestamp for tracking
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
STATUS_FILE="data_generation_status_$TIMESTAMP.json"
ARGS="$ARGS --status-file $STATUS_FILE"

echo "=== Automated Data Generation ==="
echo "Running with arguments: $ARGS"
echo ""

# Run the Python script with all arguments
python generate_test_data_automated.py $ARGS

# Check if generation was successful
if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Data generation completed successfully!"
  echo "Status file: $STATUS_FILE"
  
  # Optionally run statistics/analysis afterwards
  if [ -f "simplified_stats_bigquery.py" ]; then
    echo ""
    echo "Would you like to run data analysis on the newly generated data? (y/n)"
    read -r RUN_ANALYSIS
    if [[ $RUN_ANALYSIS == "y" || $RUN_ANALYSIS == "Y" ]]; then
      echo "Running analysis..."
      python simplified_stats_bigquery.py
    fi
  fi
else
  echo ""
  echo "❌ Data generation failed. Check the output above for errors."
fi
