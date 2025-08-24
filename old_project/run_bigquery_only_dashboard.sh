#!/bin/bash
# Run a dashboard that ONLY uses BigQuery and does not attempt to access GCS data
# This should run quickly since it only accesses the smaller BigQuery tables

# Activate the virtual environment
source venv/bin/activate

# Kill any existing Streamlit processes
pkill -f streamlit || true

# Wait a moment to ensure ports are released
sleep 2

# Run the streamlit app
echo "Starting the BigQuery-Only UK Energy Dashboard..."
echo "This version will NOT attempt to access the 1TB+ GCS dataset"
streamlit run "/Users/georgemajor/Jibber Jabber ChatGPT/8_august_jibber_jabber/bigquery_only_dashboard.py"
