#!/bin/bash
# run_automated_pipeline.sh
#
# Script to run the entire pipeline (data generation, analysis, dashboard) without prompts
# Usage: ./run_automated_pipeline.sh [--regenerate-data] [--skip-analysis] [--skip-dashboard]

# Default settings
REGENERATE_DATA=false
RUN_ANALYSIS=true
RUN_DASHBOARD=true

# Process arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --regenerate-data)
      REGENERATE_DATA=true
      shift
      ;;
    --skip-analysis)
      RUN_ANALYSIS=false
      shift
      ;;
    --skip-dashboard)
      RUN_DASHBOARD=false
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: ./run_automated_pipeline.sh [--regenerate-data] [--skip-analysis] [--skip-dashboard]"
      exit 1
      ;;
  esac
done

# Activate virtual environment if it exists
source venv/bin/activate 2>/dev/null || echo "No virtualenv found, using system Python"

# Record start time
START_TIME=$(date +%s)
echo "=== Automated Pipeline Started at $(date) ==="

# 1. Data Generation
if [ "$REGENERATE_DATA" = true ]; then
  echo -e "\n=== Regenerating All Test Data ==="
  ./auto_generate_data.sh --force
else
  echo -e "\n=== Checking for Missing Data ==="
  # Only generate data that doesn't exist yet
  ./auto_generate_data.sh
fi

# Check if data generation was successful
if [ $? -ne 0 ]; then
  echo "❌ Data generation failed. Stopping pipeline."
  exit 1
fi

# 2. Run Analysis
if [ "$RUN_ANALYSIS" = true ]; then
  echo -e "\n=== Running Data Analysis ==="
  if [ -f "simplified_stats_bigquery.py" ]; then
    python simplified_stats_bigquery.py
    
    if [ $? -ne 0 ]; then
      echo "⚠️ Analysis completed with errors."
    else
      echo "✅ Analysis completed successfully."
    fi
  else
    echo "⚠️ Analysis script (simplified_stats_bigquery.py) not found. Skipping."
  fi
fi

# 3. Run Dashboard
if [ "$RUN_DASHBOARD" = true ]; then
  echo -e "\n=== Starting Dashboard ==="
  
  # Kill any running Streamlit instances
  pkill -f streamlit 2>/dev/null
  sleep 2
  
  # Check which dashboard script to use
  if [ -f "interactive_dashboard_app.py" ]; then
    echo "Starting interactive dashboard..."
    streamlit run interactive_dashboard_app.py &
    DASHBOARD_PID=$!
    echo "Dashboard started with PID: $DASHBOARD_PID"
  elif [ -f "energy_dashboard.py" ]; then
    echo "Starting energy dashboard..."
    streamlit run energy_dashboard.py &
    DASHBOARD_PID=$!
    echo "Dashboard started with PID: $DASHBOARD_PID"
  else
    echo "⚠️ No dashboard script found. Skipping."
  fi
fi

# Calculate and display total runtime
END_TIME=$(date +%s)
RUNTIME=$((END_TIME - START_TIME))
MINS=$((RUNTIME / 60))
SECS=$((RUNTIME % 60))

echo -e "\n=== Pipeline Completed in ${MINS}m ${SECS}s ==="
echo "Finished at $(date)"

# If dashboard is running, provide instructions
if [ "$RUN_DASHBOARD" = true ] && [ ! -z "$DASHBOARD_PID" ]; then
  echo -e "\nDashboard is running in the background."
  echo "Access it at: http://localhost:8501"
  echo "To stop the dashboard, run: kill $DASHBOARD_PID"
fi
