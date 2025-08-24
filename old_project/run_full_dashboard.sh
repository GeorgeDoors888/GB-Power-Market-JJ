#!/bin/bash
# Script to run the interactive dashboard with the new advanced statistics tab

# Activate the virtual environment
source venv/bin/activate

# Kill any existing Streamlit processes
pkill -f streamlit || true

# Wait a moment to ensure ports are released
sleep 2

# Run the Streamlit app with the full path
echo "Starting the UK Energy Dashboard with Advanced Statistics..."
streamlit run "/Users/georgemajor/Jibber Jabber ChatGPT/8_august_jibber_jabber/interactive_dashboard_app.py"
