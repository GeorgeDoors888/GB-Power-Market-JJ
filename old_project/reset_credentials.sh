#!/usr/bin/env bash
# Script to reset BigQuery authentication and request credentials again

# Colors for prettier output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}    BigQuery Authentication Reset Tool   ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo

# Check if Python virtual environment exists, activate if it does
if [ -d "venv" ]; then
    echo -e "${YELLOW}Activating Python virtual environment...${NC}"
    source venv/bin/activate
fi

# Check if gcloud is installed
if command -v gcloud &> /dev/null; then
    echo -e "${YELLOW}Refreshing application default credentials...${NC}"
    gcloud auth application-default login
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to refresh application default credentials.${NC}"
        echo -e "${YELLOW}You may need to install the Google Cloud SDK.${NC}"
        echo -e "${YELLOW}Visit: https://cloud.google.com/sdk/docs/install${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}Google Cloud SDK (gcloud) not found. Attempting to continue with existing credentials.${NC}"
fi

# Check if the auth script exists
if [ ! -f "./bq_auth.py" ]; then
    echo -e "${RED}Error: bq_auth.py not found in the current directory${NC}"
    echo -e "${YELLOW}Make sure you're running this script from the project root directory${NC}"
    
    # Try to locate the file in case it's in a subdirectory
    FOUND_PATH=$(find . -name "bq_auth.py" -type f | head -n 1)
    if [ ! -z "$FOUND_PATH" ]; then
        echo -e "${YELLOW}Found bq_auth.py at: $FOUND_PATH${NC}"
        echo -e "${YELLOW}Please copy it to the current directory or run from that location${NC}"
    fi
    
    exit 1
fi

echo -e "${YELLOW}Clearing existing credentials and requesting new ones...${NC}"

# Use the correct Python executable
if [ -f "venv/bin/python" ]; then
    PYTHON_CMD="venv/bin/python"
elif [ -f "./venv/bin/python" ]; then
    PYTHON_CMD="./venv/bin/python"
else
    PYTHON_CMD="python3"
fi

$PYTHON_CMD ./bq_auth.py --reset

# Check if the reset was successful
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}Credentials reset successfully!${NC}"
    
    # Ask if user wants to test authentication
    echo
    read -p "Do you want to test authentication and list available datasets? (y/n): " TEST_AUTH
    
    if [[ $TEST_AUTH == "y" || $TEST_AUTH == "Y" ]]; then
        echo
        $PYTHON_CMD ./bq_auth.py --test
    fi
    
    # Ask if user wants to run the BOD analysis
    echo
    read -p "Do you want to run the BOD analysis with new credentials? (y/n): " RUN_BOD
    
    if [[ $RUN_BOD == "y" || $RUN_BOD == "Y" ]]; then
        echo
        echo -e "${YELLOW}Running BOD analysis with new credentials...${NC}"
        
        # Offer date range selection
        echo
        read -p "Enter start date (YYYY-MM-DD) or press Enter for 30 days ago: " START_DATE
        read -p "Enter end date (YYYY-MM-DD) or press Enter for today: " END_DATE
        
        COMMAND="$PYTHON_CMD direct_bod_analysis.py"
        
        if [ ! -z "$START_DATE" ]; then
            COMMAND="$COMMAND --start-date $START_DATE"
        fi
        
        if [ ! -z "$END_DATE" ]; then
            COMMAND="$COMMAND --end-date $END_DATE"
        fi
        
        echo -e "${YELLOW}Running: $COMMAND${NC}"
        $COMMAND
    fi
    
    echo -e "\n${GREEN}Done!${NC}"
else
    echo -e "\n${RED}Failed to reset credentials. Please check the error messages above.${NC}"
    exit 1
fi
