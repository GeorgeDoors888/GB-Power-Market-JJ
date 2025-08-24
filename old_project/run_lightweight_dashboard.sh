#!/bin/bash
# Lightweight dashboard script that avoids any heavy data processing
# Will only show table info and simple summaries

# Activate the virtual environment
source venv/bin/activate

# Kill any existing Streamlit processes
pkill -f streamlit || true

# Wait a moment to ensure ports are released
sleep 2

# Run the lightweight Streamlit app
echo "Starting the Lightweight UK Energy Dashboard..."
echo "This version only shows basic table info and avoids heavy data processing"
streamlit run "/Users/georgemajor/Jibber Jabber ChatGPT/8_august_jibber_jabber/lightweight_dashboard.py"
