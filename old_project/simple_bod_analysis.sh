#!/usr/bin/env bash
# Simple script to run BOD analysis with proper authentication

# Colors for prettier output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}    BOD Analysis with Authentication     ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo

# Find Python executable
if [ -f "venv/bin/python" ]; then
    PYTHON_CMD="venv/bin/python"
elif [ -f "./venv/bin/python" ]; then
    PYTHON_CMD="./venv/bin/python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

echo -e "${YELLOW}Using Python: $PYTHON_CMD${NC}"

# Check if Google Cloud SDK is installed and refresh credentials if needed
if command -v gcloud &> /dev/null; then
    echo -e "${YELLOW}Checking Google Cloud authentication...${NC}"
    CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null)
    
    if [ -z "$CURRENT_ACCOUNT" ]; then
        echo -e "${YELLOW}No active Google Cloud account found. Running login...${NC}"
        gcloud auth login
    else
        echo -e "${YELLOW}Using Google Cloud account: $CURRENT_ACCOUNT${NC}"
    fi
    
    echo -e "${YELLOW}Refreshing application default credentials...${NC}"
    gcloud auth application-default login
else
    echo -e "${YELLOW}Google Cloud SDK not found. Will try alternate authentication methods.${NC}"
fi

# Test authentication first
echo -e "${YELLOW}Testing BigQuery authentication...${NC}"
$PYTHON_CMD simple_bq_auth.py --test

if [ $? -ne 0 ]; then
    echo -e "${RED}Authentication failed. Cannot continue with analysis.${NC}"
    exit 1
fi

# Ask for date range
echo
read -p "Enter start date (YYYY-MM-DD) or press Enter for 30 days ago: " START_DATE
read -p "Enter end date (YYYY-MM-DD) or press Enter for today: " END_DATE

# Build the command
CMD="$PYTHON_CMD simple_bod_adapter.py"

if [ ! -z "$START_DATE" ]; then
    CMD="$CMD --start-date $START_DATE"
fi

if [ ! -z "$END_DATE" ]; then
    CMD="$CMD --end-date $END_DATE"
fi

# Add debug flag
CMD="$CMD --debug"

# Run the analysis
echo -e "${YELLOW}Running BOD analysis: $CMD${NC}"
$CMD

if [ $? -eq 0 ]; then
    echo -e "${GREEN}BOD analysis completed successfully!${NC}"
    exit 0
else
    echo -e "${RED}BOD analysis failed. Please check the error messages above.${NC}"
    exit 1
fi
