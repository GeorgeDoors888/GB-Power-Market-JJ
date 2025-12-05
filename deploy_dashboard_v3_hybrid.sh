#!/bin/bash

###############################################################################
# Dashboard V3 Hybrid - Quick Deploy Script
# 
# This script deploys Option C (Hybrid) implementation:
# - Python loads data from BigQuery
# - Apps Script formats Dashboard V3
# 
# Usage: ./deploy_dashboard_v3_hybrid.sh
###############################################################################

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}   📊 DASHBOARD V3 - HYBRID DEPLOYMENT (OPTION C)${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

# Check we're in the right directory
if [ ! -f "README.md" ] || [ ! -d "python" ]; then
    echo -e "${RED}❌ Error: Must run from GB-Power-Market-JJ directory${NC}"
    echo "   Current directory: $(pwd)"
    exit 1
fi

echo -e "${GREEN}✅ Working directory verified${NC}"
echo ""

# Check credentials file exists
if [ ! -f "inner-cinema-credentials.json" ]; then
    echo -e "${RED}❌ Error: inner-cinema-credentials.json not found${NC}"
    echo "   Please ensure service account credentials are in root directory"
    exit 1
fi

echo -e "${GREEN}✅ Credentials file found${NC}"
echo ""

# Check Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: python3 not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python3 available: $(python3 --version)${NC}"
echo ""

# Check required Python packages
echo -e "${YELLOW}📦 Checking Python dependencies...${NC}"
python3 -c "import google.cloud.bigquery" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Installing google-cloud-bigquery...${NC}"
    pip3 install --user google-cloud-bigquery
}
python3 -c "import googleapiclient" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Installing google-api-python-client...${NC}"
    pip3 install --user google-api-python-client
}
python3 -c "import pandas" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Installing pandas...${NC}"
    pip3 install --user pandas
}

echo -e "${GREEN}✅ All Python dependencies installed${NC}"
echo ""

# Test BigQuery connection
echo -e "${YELLOW}🔧 Testing BigQuery connection...${NC}"
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); print('✅ Connected to BigQuery')" || {
    echo -e "${RED}❌ Error: Cannot connect to BigQuery${NC}"
    echo "   Check GOOGLE_APPLICATION_CREDENTIALS or inner-cinema-credentials.json"
    exit 1
}
echo ""

# Run Python data loader
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}   STEP 1: Loading data from BigQuery${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""

python3 python/populate_dashboard_tables_hybrid.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Data load complete!${NC}"
else
    echo ""
    echo -e "${RED}❌ Data load failed!${NC}"
    exit 1
fi

# Instructions for Apps Script deployment
echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}   STEP 2: Deploy Apps Script (Manual)${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""
echo -e "${YELLOW}📋 Manual steps required:${NC}"
echo ""
echo "   1. Open spreadsheet:"
echo "      https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/"
echo ""
echo "   2. Go to: Extensions → Apps Script"
echo ""
echo "   3. Delete existing code in Code.gs"
echo ""
echo "   4. Copy contents of:"
echo "      ~/GB-Power-Market-JJ/Code_V3_Hybrid.gs"
echo ""
echo "   5. Paste into Code.gs and Save (Cmd+S / Ctrl+S)"
echo ""
echo "   6. Authorize script (Run any function → Review Permissions)"
echo ""
echo "   7. Refresh spreadsheet (close and reopen)"
echo ""
echo "   8. Click: ⚡ GB Energy V3 → Rebuild Dashboard Design"
echo ""

# Offer to open files
echo -e "${YELLOW}📂 Open files now?${NC}"
read -p "   Open Code_V3_Hybrid.gs in editor? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v code &> /dev/null; then
        code Code_V3_Hybrid.gs
        echo -e "${GREEN}   ✅ Opened in VS Code${NC}"
    elif command -v nano &> /dev/null; then
        nano Code_V3_Hybrid.gs
    else
        echo -e "${YELLOW}   ⚠️  No editor found, please open manually${NC}"
    fi
fi

echo ""
read -p "   Open spreadsheet in browser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    open "https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/" 2>/dev/null || \
    xdg-open "https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/" 2>/dev/null || \
    echo -e "${YELLOW}   ⚠️  Please open manually${NC}"
fi

echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}   DEPLOYMENT STATUS${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""
echo -e "${GREEN}✅ Python data loader:${NC} Complete"
echo -e "${YELLOW}⏳ Apps Script deploy:${NC} Awaiting manual steps"
echo -e "${YELLOW}⏳ Dashboard build:${NC} Run after Apps Script deployed"
echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${BLUE}   📚 Documentation${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""
echo "   📖 Full guide:"
echo "      ~/GB-Power-Market-JJ/DASHBOARD_V3_HYBRID_DEPLOYMENT_GUIDE.md"
echo ""
echo "   📋 Comparison analysis:"
echo "      ~/GB-Power-Market-JJ/DASHBOARD_V3_DESIGN_DIFFERENCES_TODO.md"
echo ""
echo -e "${GREEN}🎉 Hybrid deployment initiated successfully!${NC}"
echo ""
