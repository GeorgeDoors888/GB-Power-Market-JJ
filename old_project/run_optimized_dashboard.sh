#!/bin/bash
# Optimized dashboard script that focuses on BigQuery data only
# This script avoids loading large GCS datasets directly

# Activate the virtual environment
source venv/bin/activate

# Kill any existing Streamlit processes
pkill -f streamlit || true

# Wait a moment to ensure ports are released
sleep 2

# Run the optimized Streamlit app
echo "Starting the Optimized UK Energy Dashboard..."
echo "This version only uses BigQuery tables and avoids loading large GCS datasets"
streamlit run "/Users/georgemajor/Jibber Jabber ChatGPT/8_august_jibber_jabber/optimized_dashboard_app.py"
