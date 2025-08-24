#!/bin/bash
# Enhanced UK Energy Live Data System Runner
# Manages live data updater, backfilling of missing data, and dashboard display
# This script uses actual data from Elexon/BMRS API, not test data

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

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   UK Energy Live Data System Manager   ${NC}"
echo -e "${BLUE}=========================================${NC}"

# Load environment and API keys
echo -e "\n${BLUE}Loading environment and API keys...${NC}"
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
    echo -e "${RED}Error: api.env file not found${NC}"
    exit 1
fi

# Make sure the BMRS API key is set
if [ -z "$BMRS_API_KEY" ] && [ -n "$BMRS_API_KEY_1" ]; then
    export BMRS_API_KEY="$BMRS_API_KEY_1"
    echo -e "${GREEN}Using BMRS_API_KEY_1 as primary API key${NC}"
fi

# Activate virtual environment
echo -e "\n${BLUE}Activating Python virtual environment...${NC}"
source venv/bin/activate

# Function to run backfill
run_backfill() {
    echo -e "\n${YELLOW}Running data backfill for the last 30 days...${NC}"
    
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
        echo -e "${GREEN}Successfully backfilled missing data${NC}"
    else
        echo -e "${RED}Error during backfill process${NC}"
        tail -n 20 $LOGS_DIR/backfill_${TIMESTAMP}.log
    fi
}

# Function to manage the live data updater
manage_live_updater() {
    # Check if the live data updater is already running
    if ps aux | grep -v grep | grep -q "live_data_updater.py"; then
        echo -e "${YELLOW}Live data updater is already running${NC}"
        PID=$(ps aux | grep -v grep | grep "live_data_updater.py" | awk '{print $2}')
        echo -e "PID: ${PID}"
    else
        echo -e "${YELLOW}Starting live data updater in background...${NC}"
        
    # Start the live data updater in the background
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    nohup python live_data_updater.py update > $LOGS_DIR/live_data_updater_${TIMESTAMP}.log 2>&1 &
    UPDATER_PID=$!
    echo -e "${GREEN}Started live data updater with PID: ${UPDATER_PID}${NC}"        # Give it a moment to initialize
        sleep 3
        
        # Check if it's still running
        if ps -p $UPDATER_PID > /dev/null; then
            echo -e "${GREEN}Live data updater is running successfully${NC}"
        else
            echo -e "${RED}Error: Live data updater failed to start${NC}"
            tail -n 20 $LOGS_DIR/live_data_updater_${TIMESTAMP}.log
        fi
    fi
}

# Function to manage the dashboard
manage_dashboard() {
    # Check if there are any existing Streamlit processes running
    if ps aux | grep -v grep | grep -q "streamlit run"; then
        echo -e "${YELLOW}Stopping existing Streamlit dashboard...${NC}"
        pkill -f "streamlit run"
        sleep 2
    fi

    # Create .streamlit directory if it doesn't exist
    mkdir -p ~/.streamlit

    # Create a Streamlit config file with improved theme
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

    # Start the dashboard
    echo -e "${YELLOW}Starting UK Energy Live Dashboard...${NC}"
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    
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
    else
        echo -e "${RED}Error: Dashboard failed to start${NC}"
        tail -n 20 $LOGS_DIR/dashboard_${TIMESTAMP}.log
    fi
}

# Function to check data in BigQuery
check_data() {
    echo -e "\n${BLUE}Checking data availability in BigQuery...${NC}"
    
    python -c "
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta

client = bigquery.Client(project='jibber-jabber-knowledge')

tables = [
    'neso_demand_forecasts',
    'neso_wind_forecasts', 
    'neso_carbon_intensity', 
    'neso_interconnector_flows',
    'elexon_demand_outturn',
    'elexon_generation_outturn',
    'elexon_system_warnings'
]

print('Data availability report:')
print('========================')

for table in tables:
    try:
        # Check record count
        count_query = f\"\"\"
        SELECT COUNT(*) as count 
        FROM \`jibber-jabber-knowledge.uk_energy_prod.{table}\`
        \"\"\"
        count_df = client.query(count_query).result().to_dataframe()
        count = count_df['count'].values[0]
        
        # Check date range
        range_query = f\"\"\"
        SELECT 
            MIN(settlement_date) as min_date, 
            MAX(settlement_date) as max_date,
            COUNT(DISTINCT settlement_date) as unique_dates
        FROM \`jibber-jabber-knowledge.uk_energy_prod.{table}\`
        \"\"\"
        range_df = client.query(range_query).result().to_dataframe()
        
        print(f'{table}:')
        print(f'  Total records: {count}')
        if not range_df.empty and range_df['min_date'].values[0] is not None:
            print(f'  Date range: {range_df[\"min_date\"].values[0]} to {range_df[\"max_date\"].values[0]}')
            print(f'  Unique dates: {range_df[\"unique_dates\"].values[0]}')
            
            # Check for data from last 7 days
            today = datetime.now().date()
            week_ago = today - timedelta(days=7)
            recent_query = f\"\"\"
            SELECT COUNT(DISTINCT settlement_date) as recent_dates
            FROM \`jibber-jabber-knowledge.uk_energy_prod.{table}\`
            WHERE settlement_date >= '{week_ago}'
            \"\"\"
            recent_df = client.query(recent_query).result().to_dataframe()
            print(f'  Last 7 days coverage: {recent_df[\"recent_dates\"].values[0]}/7 days')
        else:
            print('  No date information available')
        print('')
    except Exception as e:
        print(f'{table}: Error - {str(e)}')
        print('')
"
}

# Main menu
show_menu() {
    echo -e "\n${BLUE}UK Energy Live Data System Manager${NC}"
    echo -e "${YELLOW}--------------------------------${NC}"
    echo -e "1. Start/Check Live Data Updater"
    echo -e "2. Run Data Backfill (Last 30 Days)"
    echo -e "3. Start Dashboard"
    echo -e "4. Check Data in BigQuery"
    echo -e "5. Run Complete System (Updater + Backfill + Dashboard)"
    echo -e "6. Stop All Components"
    echo -e "7. Exit"
    echo -e "${YELLOW}--------------------------------${NC}"
    echo -n "Enter your choice [1-7]: "
    read choice

    case $choice in
        1)
            manage_live_updater
            show_menu
            ;;
        2)
            run_backfill
            show_menu
            ;;
        3)
            manage_dashboard
            show_menu
            ;;
        4)
            check_data
            show_menu
            ;;
        5)
            echo -e "\n${GREEN}Running complete system...${NC}"
            manage_live_updater
            run_backfill
            manage_dashboard
            echo -e "\n${GREEN}UK Energy Live Data System is now running!${NC}"
            echo -e "${BLUE}Dashboard URL: http://localhost:8501${NC}"
            show_menu
            ;;
        6)
            echo -e "\n${YELLOW}Stopping all components...${NC}"
            pkill -f "streamlit run" || true
            pkill -f "live_data_updater.py" || true
            echo -e "${GREEN}All components stopped${NC}"
            show_menu
            ;;
        7)
            echo -e "\n${GREEN}Exiting...${NC}"
            exit 0
            ;;
        *)
            echo -e "\n${RED}Invalid choice${NC}"
            show_menu
            ;;
    esac
}

# If no arguments provided, show the menu
if [ $# -eq 0 ]; then
    show_menu
else
    # Process command line arguments
    case "$1" in
        start-updater)
            manage_live_updater
            ;;
        run-backfill)
            run_backfill
            ;;
        start-dashboard)
            manage_dashboard
            ;;
        check-data)
            check_data
            ;;
        run-all)
            manage_live_updater
            run_backfill
            manage_dashboard
            echo -e "\n${GREEN}UK Energy Live Data System is now running!${NC}"
            echo -e "${BLUE}Dashboard URL: http://localhost:8501${NC}"
            ;;
        stop-all)
            pkill -f "streamlit run" || true
            pkill -f "live_data_updater.py" || true
            echo -e "${GREEN}All components stopped${NC}"
            ;;
        *)
            echo -e "${RED}Unknown command: $1${NC}"
            echo -e "Available commands: start-updater, run-backfill, start-dashboard, check-data, run-all, stop-all"
            exit 1
            ;;
    esac
fi
