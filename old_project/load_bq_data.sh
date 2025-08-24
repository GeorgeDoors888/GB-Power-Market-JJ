#!/bin/bash
# Script to set up authentication and load data into BigQuery

# Set some colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}===== UK Energy Data Loading Script =====${NC}"
echo "This script will help you load historical data into BigQuery."
echo

# Step 1: Check if the virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}Failed to activate virtual environment.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Virtual environment activated.${NC}"
else
    echo -e "${GREEN}Virtual environment already activated: $VIRTUAL_ENV${NC}"
fi

# Step 2: Check for required Python packages
echo -e "\n${YELLOW}Checking required Python packages...${NC}"
python -c "import google.cloud.storage, google.cloud.bigquery" 2>/dev/null
if [[ $? -ne 0 ]]; then
    echo -e "${YELLOW}Installing required packages...${NC}"
    pip install google-cloud-storage google-cloud-bigquery
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}Failed to install required packages.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Required packages installed.${NC}"
else
    echo -e "${GREEN}Required packages already installed.${NC}"
fi

# Step 3: Check authentication
echo -e "\n${YELLOW}Checking authentication status...${NC}"
python bq_data_loader.py --check-auth
if [[ $? -ne 0 ]]; then
    echo -e "${YELLOW}Running authentication command...${NC}"
    gcloud auth application-default login
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}Authentication failed. Please make sure gcloud CLI is installed and try again.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Authentication completed.${NC}"
else
    echo -e "${GREEN}Authentication already set up.${NC}"
fi

# Step 4: Make data loader script executable
chmod +x bq_data_loader.py

# Step 5: Ask user what data they want to load
echo -e "\n${YELLOW}What data would you like to load?${NC}"
echo "1) All data types"
echo "2) Demand data"
echo "3) Frequency data"
echo "4) Generation data"
echo "5) Balancing services data"
echo "6) System warnings data"
echo "7) Interconnector flows data"
echo "8) Carbon intensity data"
echo "9) Exit"
read -p "Enter your choice [1-9]: " data_choice

DATA_TYPE=""
case $data_choice in
    1) DATA_TYPE="all" ;;
    2) DATA_TYPE="demand" ;;
    3) DATA_TYPE="frequency" ;;
    4) DATA_TYPE="generation" ;;
    5) DATA_TYPE="balancing" ;;
    6) DATA_TYPE="warnings" ;;
    7) DATA_TYPE="interconnector" ;;
    8) DATA_TYPE="carbon" ;;
    9) echo "Exiting."; exit 0 ;;
    *) echo -e "${RED}Invalid choice.${NC}"; exit 1 ;;
esac

# Step 6: Ask about date filtering
echo -e "\n${YELLOW}Would you like to filter by date?${NC}"
echo "1) Load all available data"
echo "2) Load data from a specific start date"
echo "3) Load data for a date range"
read -p "Enter your choice [1-3]: " date_choice

DATE_PARAMS=""
if [[ $date_choice -eq 2 ]]; then
    read -p "Enter the start date (YYYY-MM-DD): " date_input
    # Validate date format
    if [[ $date_input =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        DATE_PARAMS="--start-date $date_input"
    else
        echo -e "${RED}Invalid date format. Using no date filter.${NC}"
    fi
elif [[ $date_choice -eq 3 ]]; then
    read -p "Enter the start date (YYYY-MM-DD): " start_date
    read -p "Enter the end date (YYYY-MM-DD): " end_date
    
    # Validate date formats
    if [[ $start_date =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] && [[ $end_date =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        DATE_PARAMS="--start-date $start_date --end-date $end_date"
    else
        echo -e "${RED}Invalid date format. Using no date filter.${NC}"
    fi
fi

# Step 7: Ask about limiting the number of files
echo -e "\n${YELLOW}Would you like to limit the number of files processed per data type?${NC}"
echo "1) Process all files"
echo "2) Set a limit"
read -p "Enter your choice [1-2]: " limit_choice

MAX_FILES=""
if [[ $limit_choice -eq 2 ]]; then
    read -p "Enter maximum number of files to process: " files_input
    # Validate number
    if [[ $files_input =~ ^[0-9]+$ ]]; then
        MAX_FILES="--max-files $files_input"
    else
        echo -e "${RED}Invalid number. Processing all files.${NC}"
    fi
fi

# Step 8: Run the data loader
echo -e "\n${YELLOW}Starting data loading process...${NC}"
echo -e "Running: ./bq_data_loader.py --data-type $DATA_TYPE $DATE_PARAMS $MAX_FILES"
./bq_data_loader.py --data-type $DATA_TYPE $DATE_PARAMS $MAX_FILES

if [[ $? -eq 0 ]]; then
    echo -e "\n${GREEN}Data loading completed successfully!${NC}"
    echo "You can now validate the data using the following commands:"
    echo "  ./bq_data_loader.py --data-type $DATA_TYPE --validate-only"
    echo "Or check the data in BigQuery directly."
else
    echo -e "\n${RED}Data loading completed with errors.${NC}"
    echo "Please check the log file for details: bq_data_loading.log"
fi

echo -e "\n${YELLOW}===== Data Loading Script Complete =====${NC}"
