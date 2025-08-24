#!/bin/bash
# Run the GB Energy Dashboard with enhanced visualizations
# Version 1.2.0 - Fixed version with improved UI and stable visualizations

# Activate the virtual environment
source venv/bin/activate

# Kill any existing Streamlit processes
echo "Stopping any existing Streamlit processes..."
pkill -f streamlit || true

# Wait a moment to ensure ports are released
sleep 2

# Create a log directory if it doesn't exist
mkdir -p logs

# Timestamp for the log file
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="logs/dashboard_${TIMESTAMP}.log"

# Run the streamlit app with more verbose error reporting
echo "Starting the GB Energy Dashboard with enhanced visualizations..."
echo "Logs will be saved to ${LOG_FILE}"

# Run the dashboard with improved visualization settings
streamlit run "/Users/georgemajor/Jibber Jabber ChatGPT/8_august_jibber_jabber/gb_energy_dashboard_fixed.py" \
  --server.port=8505 \
  --server.headless=true \
  --browser.gatherUsageStats=false \
  --theme.base="light" \
  --theme.primaryColor="#1E3A8A" \
  --theme.backgroundColor="#FFFFFF" \
  --theme.secondaryBackgroundColor="#F0F2F6" \
  --theme.textColor="#262730" \
  --logger.level="info" \
  2>&1 | tee "${LOG_FILE}" &

# Wait a moment for the server to start
sleep 3

# Open the browser
echo "Opening dashboard in browser..."
open http://localhost:8505/

echo "Dashboard is running on http://localhost:8505/"
echo "Press Ctrl+C to stop the dashboard"
