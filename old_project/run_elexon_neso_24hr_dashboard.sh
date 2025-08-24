#!/bin/bash
# Run both the live data updater and the dashboard with proper configuration
# for ELEXON and NESO data with 24-hour lookback and backfill
# 
# This script ensures only ELEXON and NESO data is fetched and displayed

# Define colors for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== UK Energy Live Data System (ELEXON & NESO ONLY) ===${NC}"
echo -e "${YELLOW}=== 24-hour Data Collection with Backfill ===${NC}"

# Directory for logs
LOGS_DIR="logs"
mkdir -p $LOGS_DIR

# Timestamp for log files
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Ensure we're using the correct Python environment
source venv/bin/activate

# Kill any existing streamlit processes
pkill -f streamlit || true
echo -e "${CYAN}Cleared any existing dashboard processes${NC}"

# Kill any existing updater processes
if ps aux | grep -v grep | grep -q "live_data_updater.py"; then
    PID=$(ps aux | grep -v grep | grep "live_data_updater.py" | awk '{print $2}')
    echo -e "${CYAN}Stopping existing live data updater (PID: ${PID})${NC}"
    kill $PID
    sleep 2
fi

# Modify the live_data_updater to ensure it only collects 24 hours of data
sed -i.bak 's/timedelta(hours=25)/timedelta(hours=24)/g' live_data_updater.py
echo -e "${CYAN}Updated live data updater to collect exactly 24 hours of data${NC}"

# Start the live data updater in the background
echo -e "${CYAN}Starting live data updater in background...${NC}"
python live_data_updater.py run > $LOGS_DIR/live_data_updater_${TIMESTAMP}.log 2>&1 &

# Save the PID to a file
echo $! > live_data_updater.pid
echo -e "${GREEN}Live data updater started with PID: $!${NC}"
echo -e "Log file: $LOGS_DIR/live_data_updater_${TIMESTAMP}.log"

# Perform backfill for any missing data
echo -e "${CYAN}Backfilling missing data from the past week...${NC}"
python backfill_missing_data.py --start-date $(date -v-7d +"%Y-%m-%d") --end-date $(date +"%Y-%m-%d") > $LOGS_DIR/backfill_${TIMESTAMP}.log 2>&1
echo -e "${GREEN}Backfill complete${NC}"
echo -e "Log file: $LOGS_DIR/backfill_${TIMESTAMP}.log"

# Start the dashboard
echo -e "${CYAN}Starting live energy dashboard...${NC}"
streamlit run live_energy_dashboard.py

# Note: The script will continue running the dashboard in the foreground
# The live data updater will keep running in the background
