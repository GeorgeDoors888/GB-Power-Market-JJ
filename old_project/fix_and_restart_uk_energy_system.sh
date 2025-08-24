#!/bin/bash
# Master script to fix the UK Energy Data System and ensure everything is working properly
# This script will:
# 1. Stop any existing Streamlit dashboards and live data updaters
# 2. Fix the BigQuery schemas to ensure data can be loaded properly
# 3. Start the live data updater with the correct API keys
# 4. Backfill any missing data from the past 30 days
# 5. Start the dashboard with the latest data

# Define colors for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directory for this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Create logs directory
LOGS_DIR="logs"
mkdir -p $LOGS_DIR

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   UK Energy Data System Fix & Restart   ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Step 1: Stop any existing processes
echo -e "\n${YELLOW}Step 1: Stopping existing processes...${NC}"
pkill -f "streamlit run" || true
pkill -f "live_data_updater.py" || true

echo -e "${GREEN}✓ Stopped any existing dashboard and data updater processes${NC}"
sleep 2

# Step 2: Load environment and API keys
echo -e "\n${YELLOW}Step 2: Loading environment and API keys...${NC}"
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
    echo -e "${GREEN}✓ Loaded API keys from api.env${NC}"
else
    echo -e "${RED}Error: api.env file not found${NC}"
    exit 1
fi

# Make sure the BMRS API key is set
if [ -z "$BMRS_API_KEY" ] && [ -n "$BMRS_API_KEY_1" ]; then
    export BMRS_API_KEY="$BMRS_API_KEY_1"
    echo -e "${GREEN}✓ Using BMRS_API_KEY_1 as primary API key${NC}"
fi

# Activate virtual environment
echo -e "\n${YELLOW}Step 3: Activating Python environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Activated Python virtual environment${NC}"

# Step 4: Fix BigQuery schemas
echo -e "\n${YELLOW}Step 4: Fixing BigQuery schemas...${NC}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
python fix_bigquery_schemas.py > $LOGS_DIR/schema_fix_${TIMESTAMP}.log 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Successfully fixed BigQuery schemas${NC}"
else
    echo -e "${RED}× Error fixing BigQuery schemas. Check logs for details.${NC}"
    tail -n 20 $LOGS_DIR/schema_fix_${TIMESTAMP}.log
    echo -e "${YELLOW}Continuing anyway...${NC}"
fi

# Step 5: Start live data updater
echo -e "\n${YELLOW}Step 5: Starting live data updater...${NC}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
nohup python live_data_updater.py update > $LOGS_DIR/live_data_updater_${TIMESTAMP}.log 2>&1 &
UPDATER_PID=$!
echo -e "${GREEN}✓ Started live data updater with PID: ${UPDATER_PID}${NC}"

# Give it a moment to initialize
sleep 5

# Check if it's still running
if ps -p $UPDATER_PID > /dev/null; then
    echo -e "${GREEN}✓ Live data updater is running successfully${NC}"
else
    echo -e "${RED}× Error: Live data updater failed to start${NC}"
    tail -n 20 $LOGS_DIR/live_data_updater_${TIMESTAMP}.log
    echo -e "${YELLOW}Will try to continue...${NC}"
fi

# Step 6: Run backfill for missing data
echo -e "\n${YELLOW}Step 6: Running data backfill for the last 30 days...${NC}"

# Calculate date 30 days ago
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    START_DATE=$(date -v-30d +"%Y-%m-%d")
else
    # Linux
    START_DATE=$(date -d "30 days ago" +"%Y-%m-%d")
fi

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
echo -e "${BLUE}Backfilling data from ${START_DATE} to today${NC}"

python backfill_missing_data.py --start-date $START_DATE > $LOGS_DIR/backfill_${TIMESTAMP}.log 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Successfully backfilled missing data${NC}"
else
    echo -e "${RED}× Error during backfill process${NC}"
    tail -n 20 $LOGS_DIR/backfill_${TIMESTAMP}.log
    echo -e "${YELLOW}Continuing to dashboard...${NC}"
fi

# Step 7: Start the dashboard
echo -e "\n${YELLOW}Step 7: Starting UK Energy Live Dashboard...${NC}"

# Create .streamlit directory if it doesn't exist
mkdir -p ~/.streamlit

# Create a Streamlit config file with improved theme (no clour change)
cat > ~/.streamlit/config.toml << EOF
[theme]
primaryColor="#0068c9"
backgroundColor="#ffffff"
secondaryBackgroundColor="#f0f2f6"
textColor="#262730"
font="sans serif"

[server]
enableCORS = false
enableXsrfProtection = false
headless = true
EOF

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
nohup streamlit run live_energy_dashboard.py > $LOGS_DIR/dashboard_${TIMESTAMP}.log 2>&1 &
DASHBOARD_PID=$!
echo -e "${GREEN}✓ Started dashboard with PID: ${DASHBOARD_PID}${NC}"

# Wait a moment for Streamlit to initialize
sleep 5

# Check if dashboard is running
if ps -p $DASHBOARD_PID > /dev/null; then
    echo -e "${GREEN}✓ Dashboard is running successfully${NC}"
    echo -e "${BLUE}Opening dashboard in browser...${NC}"
    
    # Try to open the dashboard in a browser
    open http://localhost:8501 || xdg-open http://localhost:8501 || echo -e "${YELLOW}Please open http://localhost:8501 in your browser${NC}"
else
    echo -e "${RED}× Error: Dashboard failed to start${NC}"
    tail -n 20 $LOGS_DIR/dashboard_${TIMESTAMP}.log
fi

# Summary
echo -e "\n${GREEN}=========================================${NC}"
echo -e "${GREEN}   UK Energy System Fix Complete!   ${NC}"
echo -e "${GREEN}=========================================${NC}"
echo -e "${YELLOW}System status:${NC}"
echo -e "Live Data Updater PID: ${UPDATER_PID}"
echo -e "Dashboard PID: ${DASHBOARD_PID}"
echo -e "Dashboard URL: http://localhost:8501"
echo -e "\n${BLUE}To stop the system:${NC}"
echo -e "  pkill -f 'streamlit run'"
echo -e "  pkill -f 'live_data_updater.py'"
echo -e "\n${BLUE}For system management:${NC}"
echo -e "  ./run_uk_energy_system.sh"
echo -e "${GREEN}=========================================${NC}"
