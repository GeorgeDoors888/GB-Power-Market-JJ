#!/bin/bash
# Setup script for Elexon & NESO data collection system
# This script creates a Python virtual environment and installs required packages

set -e  # Exit on error

# Color codes for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "=================================================="
echo "  Setting up Elexon & NESO Data Collection System "
echo "  $(date)"
echo "=================================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1)
if [[ $? -ne 0 ]]; then
    echo -e "${RED}Python 3 not found. Please install Python 3.7 or later.${NC}"
    exit 1
fi

echo -e "${BLUE}Using ${PYTHON_VERSION}${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv venv
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}Failed to create virtual environment. Please install venv package.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Virtual environment created successfully.${NC}"
else
    echo -e "${YELLOW}Virtual environment already exists.${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate

# Install required packages
echo -e "${BLUE}Installing required packages...${NC}"
pip install --upgrade pip
pip install google-cloud-storage google-cloud-bigquery requests

# Verify installations
echo -e "${BLUE}Verifying installations...${NC}"
python3 -c "import google.cloud.storage; import google.cloud.bigquery; import requests; print('All packages installed successfully.')"

if [[ $? -ne 0 ]]; then
    echo -e "${RED}Failed to install required packages.${NC}"
    exit 1
fi

echo -e "${GREEN}Environment setup completed successfully.${NC}"
echo -e "${YELLOW}To activate the environment, run: source venv/bin/activate${NC}"
echo -e "${YELLOW}To run the table creation script: ./create_bigquery_tables.py${NC}"
echo -e "${YELLOW}To deploy the data collection system: ./deploy_data_collectors.sh${NC}"
echo "=================================================="
