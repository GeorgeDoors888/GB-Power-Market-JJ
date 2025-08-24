#!/bin/bash
# Run both the live data updater and the dashboard
# The live data updater runs in the background and the dashboard in the foreground

# Define colors for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== UK Energy Live Data System ===${NC}"

# Directory for logs
LOGS_DIR="logs"
mkdir -p $LOGS_DIR

# Timestamp for log files
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Check if the live data updater is already running
if ps aux | grep -v grep | grep -q "live_data_updater.py"; then
    echo -e "${CYAN}Live data updater is already running${NC}"
    PID=$(ps aux | grep -v grep | grep "live_data_updater.py" | awk '{print $2}')
    echo -e "PID: ${PID}"
else
    echo -e "${CYAN}Starting live data updater in background...${NC}"
    source venv/bin/activate
    
    # Start the live data updater in the background
    python live_data_updater.py run > $LOGS_DIR/live_data_updater_${TIMESTAMP}.log 2>&1 &
    
    # Save the PID to a file
    echo $! > live_data_updater.pid
    echo -e "${GREEN}Live data updater started with PID: $!${NC}"
    echo -e "Log file: $LOGS_DIR/live_data_updater_${TIMESTAMP}.log"
fi

# Backfill missing data if requested
if [ "$1" == "--backfill" ]; then
    echo -e "${CYAN}Backfilling missing data...${NC}"
    source venv/bin/activate
    python backfill_missing_data.py --start-date $(date -v-30d +"%Y-%m-%d") --end-date $(date +"%Y-%m-%d")
    echo -e "${GREEN}Backfill complete${NC}"
fi

# Start the dashboard
echo -e "${CYAN}Starting live energy dashboard...${NC}"
source venv/bin/activate
streamlit run live_energy_dashboard.py

# Note: The script will continue running the dashboard in the foreground
# The live data updater will keep running in the background
