#!/bin/bash
# Script to launch the comprehensive test dashboard for graph verification

echo "🚀 Launching UK Energy Comprehensive Test Dashboard"
echo "---------------------------------------------------"
echo "This script will launch a Streamlit dashboard with 15+ visualization types to verify all graphs work with test data."
echo

# Ensure we're in the correct directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
fi

# Install required packages
echo "📦 Installing required packages..."
pip install streamlit plotly pandas google-cloud-bigquery 
echo "📦 Installing optional packages (for enhanced visualizations)..."
pip install statsmodels matplotlib seaborn

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

# Run the comprehensive test dashboard
echo "📊 Starting comprehensive test dashboard with 15+ visualization types..."
streamlit run comprehensive_test_dashboard.py

# Note: Streamlit runs in the foreground, so code below this line won't execute
# until Streamlit is closed
echo "✅ Test dashboard closed."
