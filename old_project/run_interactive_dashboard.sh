#!/bin/bash
# Script to run the interactive dashboard with the new advanced statistics tab

# Activate the virtual environment
source venv/bin/activate

# Run the Streamlit app
echo "Starting the UK Energy Dashboard with Advanced Statistics..."
streamlit run interactive_dashboard_app.py
