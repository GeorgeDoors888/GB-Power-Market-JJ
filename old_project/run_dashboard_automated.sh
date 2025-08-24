#!/bin/bash

# Auto-run dashboard with proper error handling
cd "$(dirname "$0")"
source venv/bin/activate

# Kill any existing Streamlit processes
pkill -f streamlit || true
sleep 2

# Make sure BigQuery credentials are available
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  if [ -f "client_secret.json" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/client_secret.json"
    echo "Set GOOGLE_APPLICATION_CREDENTIALS to client_secret.json"
  else
    echo "Warning: GOOGLE_APPLICATION_CREDENTIALS not set and client_secret.json not found"
  fi
fi

# Run the dashboard
echo "Starting dashboard with automatic column name handling..."
streamlit run live_energy_dashboard.py
