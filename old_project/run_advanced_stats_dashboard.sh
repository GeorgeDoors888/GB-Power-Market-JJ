#!/bin/bash
# Run script for Advanced Statistical Analysis Dashboard

# Set up environment
echo "Setting up environment..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Make sure virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install required packages
echo "Installing required packages..."
pip install google-cloud-bigquery pandas numpy scipy statsmodels matplotlib pandas-gbq pyarrow streamlit plotly google-cloud-storage

# Make sure Google credentials are set
if [ -f "client_secret.json" ]; then
    echo "Setting Google credentials..."
    export GOOGLE_APPLICATION_CREDENTIALS="$SCRIPT_DIR/client_secret.json"
else
    echo "Warning: client_secret.json not found. Make sure Google credentials are set."
fi

# Create output directory if it doesn't exist
mkdir -p ./output

# Run the Streamlit app
echo "Starting Advanced Statistical Analysis Dashboard..."
streamlit run advanced_stats_bigquery_app.py
