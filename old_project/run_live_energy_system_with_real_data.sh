#!/bin/bash
# Run UK Energy Live Data System with real-time data from Elexon BMRS API
# This script loads API keys, runs the live data updater to fetch real-time data,
# and launches the dashboard to display the data.

# Define colors for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directory for this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Directory for logs
LOGS_DIR="logs"
mkdir -p $LOGS_DIR

# Load environment and API keys
echo -e "${BLUE}Loading environment and API keys...${NC}"
if [ -f "api.env" ]; then
    # Export all keys from api.env
    while IFS='=' read -r key value || [[ -n "$key" ]]; do
        if [[ ! $key =~ ^# && -n $key ]]; then
            # Remove quotes if present
            value=$(echo $value | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//")
            export "$key=$value"
            echo -e "  Loaded $key ✅"
        fi
    done < "api.env"
    echo -e "${GREEN}Loaded API keys from api.env${NC}"
else
    echo -e "${RED}Warning: api.env file not found${NC}"
fi

# Make sure the BMRS API key is set
if [ -z "$BMRS_API_KEY" ] && [ -n "$BMRS_API_KEY_1" ]; then
    export BMRS_API_KEY="$BMRS_API_KEY_1"
    echo -e "${GREEN}Using BMRS_API_KEY_1 as primary API key${NC}"
fi

# Check if the live data updater is already running
if ps aux | grep -v grep | grep -q "live_data_updater.py"; then
    echo -e "${YELLOW}Live data updater is already running${NC}"
    PID=$(ps aux | grep -v grep | grep "live_data_updater.py" | awk '{print $2}')
    echo -e "PID: ${PID}"
else
    echo -e "${YELLOW}Starting live data updater in background...${NC}"
    source venv/bin/activate
    
    # Start the live data updater in the background
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    nohup python live_data_updater.py run > $LOGS_DIR/live_data_updater_${TIMESTAMP}.log 2>&1 &
    UPDATER_PID=$!
    echo -e "${GREEN}Started live data updater with PID: ${UPDATER_PID}${NC}"
    
    # Give it a moment to initialize
    sleep 3
    
    # Check if it's still running
    if ps -p $UPDATER_PID > /dev/null; then
        echo -e "${GREEN}Live data updater is running successfully${NC}"
    else
        echo -e "${RED}Error: Live data updater failed to start${NC}"
        # Try to get error output
        tail -n 20 $LOGS_DIR/live_data_updater_${TIMESTAMP}.log
        exit 1
    fi
fi

# Check if there are any existing Streamlit processes running
if ps aux | grep -v grep | grep -q "streamlit run"; then
    echo -e "${YELLOW}Stopping existing Streamlit dashboard...${NC}"
    pkill -f "streamlit run"
    sleep 2
fi

# Start the dashboard
echo -e "${YELLOW}Starting UK Energy Live Dashboard...${NC}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create .streamlit directory if it doesn't exist
mkdir -p ~/.streamlit

# Create a Streamlit config file to enable server-side theme
cat > ~/.streamlit/config.toml << EOF
[theme]
primaryColor="#1E88E5"
backgroundColor="#FFFFFF"
secondaryBackgroundColor="#F0F2F6"
textColor="#333333"
font="sans serif"

[server]
enableCORS = false
enableXsrfProtection = false
headless = true
EOF

# Launch the dashboard with real-time data
nohup streamlit run live_energy_dashboard.py > $LOGS_DIR/dashboard_${TIMESTAMP}.log 2>&1 &
DASHBOARD_PID=$!
echo -e "${GREEN}Started dashboard with PID: ${DASHBOARD_PID}${NC}"

# Wait a moment for Streamlit to initialize
sleep 5

# Check if dashboard is running
if ps -p $DASHBOARD_PID > /dev/null; then
    echo -e "${GREEN}Dashboard is running successfully${NC}"
    echo -e "${BLUE}Opening dashboard in browser...${NC}"
    
    # Try to open the dashboard in a browser
    open http://localhost:8501 || xdg-open http://localhost:8501 || echo -e "${YELLOW}Please open http://localhost:8501 in your browser${NC}"
    
    echo -e "\n${GREEN}UK Energy Live Data System is now running!${NC}"
    echo -e "${BLUE}Live Data Updater PID: ${UPDATER_PID}${NC}"
    echo -e "${BLUE}Dashboard PID: ${DASHBOARD_PID}${NC}"
    echo -e "${YELLOW}Dashboard URL: http://localhost:8501${NC}"
    echo -e "\n${YELLOW}To stop the system:${NC}"
    echo -e "  pkill -f 'streamlit run'"
    echo -e "  pkill -f 'live_data_updater.py'"
else
    echo -e "${RED}Error: Dashboard failed to start${NC}"
    # Try to get error output
    tail -n 20 $LOGS_DIR/dashboard_${TIMESTAMP}.log
    exit 1
fi
