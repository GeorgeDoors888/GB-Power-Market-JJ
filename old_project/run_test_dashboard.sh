#!/bin/bash
# Script to launch the test dashboard for graph verification

echo "🚀 Launching UK Energy Test Dashboard"
echo "-----------------------------------"
echo "This script will launch a Streamlit dashboard to verify all graphs work with test data."
echo

# Ensure we're in the correct directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing..."
    pip install streamlit plotly pandas google-cloud-bigquery
fi

# Check BigQuery credentials
echo "🔑 Checking BigQuery credentials..."
python -c "from google.cloud import bigquery; client = bigquery.Client(project='jibber-jabber-knowledge')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ BigQuery credentials not found or invalid."
    echo "Please set up your credentials with:"
    echo "export GOOGLE_APPLICATION_CREDENTIALS=path/to/your/client_secret.json"
    exit 1
else
    echo "✅ BigQuery credentials verified."
fi

# Run the test dashboard
echo "📊 Starting test dashboard..."
streamlit run test_dashboard_graphs.py

# Note: Streamlit runs in the foreground, so code below this line won't execute
# until Streamlit is closed
echo "✅ Test dashboard closed."
