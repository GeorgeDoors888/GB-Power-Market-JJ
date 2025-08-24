#!/bin/bash
# Run the GB Energy Dashboard with original structure and improved visualizations
# Version 2.0.0 - With proper date range display and original color scheme

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

# Run the streamlit app with the original dashboard aesthetics
echo "Starting the improved GB Energy Dashboard..."
echo "This version has the complete dark theme, 9-year date range, and advanced statistics tab"
echo "Logs will be saved to ${LOG_FILE}"

# Run the dashboard with dark styling
streamlit run "/Users/georgemajor/Jibber Jabber ChatGPT/8_august_jibber_jabber/gb_energy_dashboard_improved.py" \
  --server.port=8505 \
  --server.headless=true \
  --browser.gatherUsageStats=false \
  --theme.base="dark" \
  --theme.primaryColor="#3366CC" \
  --theme.backgroundColor="#0E1117" \
  --theme.secondaryBackgroundColor="#262730" \
  --theme.textColor="#FAFAFA" \
  --logger.level="info" \
  2>&1 | tee "${LOG_FILE}" &

# Wait a moment for the server to start
sleep 3

# Open the browser
echo "Opening dashboard in browser..."
open http://localhost:8505/

echo "Dashboard is running on http://localhost:8505/"
echo "Press Ctrl+C to stop the dashboard"
