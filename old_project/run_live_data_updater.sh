#!/bin/bash
# Live Data Updater Service for UK Energy Data
# Monitors and updates data from Elexon BMRS within the last 25 hours
# Runs continuously to capture new data as soon as it's published

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Directory where logs will be stored
LOG_DIR="logs"
PID_FILE=".live_data_updater.pid"
MONITOR_PID_FILE=".live_data_updater_monitor.pid"

# Kill any existing live data updater processes
echo -e "${YELLOW}Stopping any existing live data updater processes...${NC}"
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat $PID_FILE)
    if ps -p $OLD_PID > /dev/null; then
        echo -e "${YELLOW}Killing existing process with PID $OLD_PID${NC}"
        kill $OLD_PID
    fi
    rm $PID_FILE
fi

if [ -f "$MONITOR_PID_FILE" ]; then
    OLD_MONITOR_PID=$(cat $MONITOR_PID_FILE)
    if ps -p $OLD_MONITOR_PID > /dev/null; then
        echo -e "${YELLOW}Killing existing monitor process with PID $OLD_MONITOR_PID${NC}"
        kill $OLD_MONITOR_PID
    fi
    rm $MONITOR_PID_FILE
fi

pkill -f live_data_updater.py || true
sleep 2

# Set up environment
echo -e "${BLUE}Setting up environment...${NC}"
mkdir -p $LOG_DIR
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/live_data_updater_${TIMESTAMP}.log"

# Check if Python and required packages are available
echo -e "${BLUE}Checking Python environment...${NC}"
python -c "import sys; print(f'Python {sys.version}')"
if [ $? -ne 0 ]; then
    echo -e "${RED}Python not found. Please install Python 3.6 or higher.${NC}"
    exit 1
fi

# Check for required packages
echo -e "${BLUE}Checking dependencies...${NC}"
python -c "import pandas, requests, schedule" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${RED}Missing required Python packages. Installing...${NC}"
    pip install pandas requests schedule
fi

# Optional: check for Google Cloud packages
python -c "import google.cloud.storage, google.cloud.bigquery" 2>/dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Google Cloud packages not found. Cloud features will be disabled.${NC}"
    echo -e "${YELLOW}To enable cloud features, install: pip install google-cloud-storage google-cloud-bigquery${NC}"
else
    echo -e "${GREEN}Google Cloud packages found.${NC}"
fi

# Set environment variables if needed
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    if [ -f "client_secret.json" ]; then
        echo -e "${YELLOW}Setting Google Cloud credentials...${NC}"
        export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/client_secret.json"
    else
        echo -e "${RED}Warning: GOOGLE_APPLICATION_CREDENTIALS not set and client_secret.json not found${NC}"
        echo -e "${RED}Cloud storage and BigQuery operations will be disabled${NC}"
    fi
fi

# Choose the operation mode
if [ "$1" = "test" ]; then
    # Run in test mode first to check if everything is working
    echo -e "${GREEN}Running in test mode to verify connectivity...${NC}"
    python live_data_updater.py test
    
    # Check if test was successful
    if [ $? -ne 0 ]; then
        echo -e "${RED}Test failed. Please check the logs for details.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Test successful! Proceeding with service startup.${NC}"
fi

# Start the live data updater
echo -e "${GREEN}Starting live data updater service...${NC}"
echo -e "${BLUE}This service will continuously monitor and update data from Elexon BMRS${NC}"
echo -e "${BLUE}Data published within the last 25 hours will be captured as soon as it's available${NC}"
echo -e "${BLUE}Logs will be saved to ${LOG_FILE}${NC}"
echo ""

# Start the live data updater in the background
python live_data_updater.py > "${LOG_FILE}" 2>&1 &
UPDATER_PID=$!

# Store the PID for future reference
echo $UPDATER_PID > $PID_FILE
echo -e "${GREEN}Live data updater service is running with PID ${UPDATER_PID}${NC}"

# Create a robust process monitor
echo -e "${GREEN}Setting up process monitoring...${NC}"
cat > monitor_live_updater.sh << 'EOL'
#!/bin/bash
# Process monitor for live data updater
PID_FILE=".live_data_updater.pid"
LOG_DIR="logs"
MONITOR_LOG="${LOG_DIR}/updater_monitor.log"

while true; do
    if [ ! -f "$PID_FILE" ]; then
        echo "$(date): PID file not found. Creating new process..." >> "$MONITOR_LOG"
        python live_data_updater.py > "${LOG_DIR}/live_data_updater_$(date +%Y%m%d_%H%M%S).log" 2>&1 &
        NEW_PID=$!
        echo $NEW_PID > "$PID_FILE"
        echo "$(date): Started new process with PID $NEW_PID" >> "$MONITOR_LOG"
    else
        PID=$(cat "$PID_FILE")
        if ! ps -p $PID > /dev/null; then
            echo "$(date): Process with PID $PID has died. Restarting..." >> "$MONITOR_LOG"
            python live_data_updater.py > "${LOG_DIR}/live_data_updater_$(date +%Y%m%d_%H%M%S).log" 2>&1 &
            NEW_PID=$!
            echo $NEW_PID > "$PID_FILE"
            echo "$(date): Restarted process with PID $NEW_PID" >> "$MONITOR_LOG"
        fi
    fi
    sleep 60
done
EOL

# Make the monitor script executable
chmod +x monitor_live_updater.sh

# Start the monitor in the background
./monitor_live_updater.sh &
MONITOR_PID=$!
echo $MONITOR_PID > $MONITOR_PID_FILE

echo -e "${GREEN}Process monitor is running with PID ${MONITOR_PID}${NC}"
echo -e "${BLUE}The service is now running in the background${NC}"
echo -e "${BLUE}To view logs, run: ${YELLOW}tail -f ${LOG_FILE}${NC}"
echo -e "${BLUE}To stop the service, run: ${YELLOW}pkill -f live_data_updater.py${NC}"
echo ""
echo -e "${BLUE}Available commands:${NC}"
echo -e "${YELLOW}python live_data_updater.py list${NC} - List available data sources"
echo -e "${YELLOW}python live_data_updater.py update${NC} - Manually trigger a full update"
echo -e "${YELLOW}python live_data_updater.py elexon${NC} - Update only Elexon datasets"
echo -e "${YELLOW}python live_data_updater.py neso${NC} - Update only NESO datasets"
echo ""
echo -e "${GREEN}Service is fully operational!${NC}"
