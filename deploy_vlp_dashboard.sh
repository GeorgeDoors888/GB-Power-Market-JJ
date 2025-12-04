#!/bin/bash
# VLP Revenue Dashboard - Complete Deployment Script

set -e

echo "================================================================================"
echo "VLP REVENUE DASHBOARD - AUTOMATED DEPLOYMENT"
echo "================================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
SPREADSHEET_ID="1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
CLASP_DIR="energy_dashboard_clasp"

# Step 1: Check prerequisites
echo "🔍 Step 1: Checking prerequisites..."
echo ""

if ! command -v clasp &> /dev/null; then
    echo -e "${RED}❌ CLASP not found${NC}"
    echo "Install with: npm install -g @google/clasp"
    exit 1
fi
echo -e "${GREEN}✅ CLASP found: $(clasp --version)${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Python 3 found: $(python3 --version)${NC}"

if [ ! -f "inner-cinema-credentials.json" ]; then
    echo -e "${RED}❌ Credentials file not found: inner-cinema-credentials.json${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Credentials file found${NC}"

echo ""

# Step 2: Install Python dependencies
echo "📦 Step 2: Installing Python dependencies..."
echo ""

pip3 install --user google-cloud-bigquery gspread google-auth pandas db-dtypes pyarrow 2>&1 | grep -v "externally-managed-environment" || true

echo -e "${GREEN}✅ Python dependencies ready${NC}"
echo ""

# Step 3: Check CLASP login status
echo "🔐 Step 3: Checking CLASP authentication..."
echo ""

if clasp login --status | grep -q "not logged in"; then
    echo -e "${YELLOW}⚠️ Not logged in to CLASP${NC}"
    echo "Running: clasp login"
    clasp login
fi

echo -e "${GREEN}✅ CLASP authenticated${NC}"
echo ""

# Step 4: Link CLASP to spreadsheet
echo "🔗 Step 4: Linking CLASP to Google Sheet..."
echo ""

cd "$CLASP_DIR"

# Check if already linked to a script
if grep -q "YOUR_SCRIPT_ID_HERE" .clasp.json; then
    echo -e "${YELLOW}⚠️ Script not yet linked. Creating new Apps Script project...${NC}"
    
    # Create new Apps Script project bound to spreadsheet
    clasp create --type sheets --title "VLP Revenue Dashboard" --parentId "$SPREADSHEET_ID"
    
    echo -e "${GREEN}✅ Apps Script project created${NC}"
else
    echo -e "${GREEN}✅ Already linked to Apps Script project${NC}"
fi

echo ""

# Step 5: Deploy Apps Script
echo "☁️ Step 5: Deploying Apps Script to Google Sheets..."
echo ""

echo "Files to deploy:"
ls -1 *.gs *.json

clasp push

echo -e "${GREEN}✅ Apps Script deployed${NC}"
echo ""

# Step 6: Enable BigQuery Advanced Service
echo "🔧 Step 6: Configuring Advanced Services..."
echo ""

echo -e "${YELLOW}⚠️ MANUAL STEP REQUIRED:${NC}"
echo "1. Open Apps Script editor: https://script.google.com"
echo "2. Select your 'VLP Revenue Dashboard' project"
echo "3. Go to: Resources → Advanced Google Services"
echo "4. Enable 'BigQuery API'"
echo "5. Also enable in Google Cloud Console"
echo ""
read -p "Press Enter when completed..."

cd ..

echo ""

# Step 7: Test BigQuery view access
echo "🧪 Step 7: Testing BigQuery view access..."
echo ""

bq query --project_id=inner-cinema-476211-u9 --use_legacy_sql=false --max_rows=1 \
"SELECT settlementDate, settlementPeriod, net_margin_per_mwh 
FROM \`inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs\` 
ORDER BY settlementDate DESC, settlementPeriod DESC LIMIT 1"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ BigQuery view accessible${NC}"
else
    echo -e "${RED}❌ BigQuery view access failed${NC}"
    exit 1
fi

echo ""

# Step 8: Run Python refresh script
echo "🐍 Step 8: Running initial dashboard refresh..."
echo ""

python3 refresh_vlp_dashboard.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dashboard refreshed successfully${NC}"
else
    echo -e "${RED}❌ Dashboard refresh failed${NC}"
    exit 1
fi

echo ""

# Step 9: Set up Apps Script triggers
echo "⏰ Step 9: Setting up automatic triggers..."
echo ""

echo -e "${YELLOW}⚠️ MANUAL STEP REQUIRED:${NC}"
echo "1. Open Google Sheet: https://docs.google.com/spreadsheets/d/$SPREADSHEET_ID"
echo "2. Click: ⚡ Energy Tools → Enable Auto-Refresh"
echo "3. Authorize the script when prompted"
echo "4. Triggers will be set for:"
echo "   • Live Ticker: every 5 minutes"
echo "   • Full Dashboard: every 30 minutes"
echo ""
read -p "Press Enter when completed..."

echo ""

# Step 10: Create cron job for Python refresh
echo "🕐 Step 10: Setting up cron job (optional)..."
echo ""

read -p "Do you want to set up automatic Python refresh via cron? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    SCRIPT_PATH="$(pwd)/refresh_vlp_dashboard.py"
    CRON_CMD="*/30 * * * * cd $(pwd) && /usr/bin/python3 $SCRIPT_PATH >> logs/vlp_refresh.log 2>&1"
    
    echo "Adding cron job:"
    echo "$CRON_CMD"
    echo ""
    
    # Add to crontab (commented by default)
    (crontab -l 2>/dev/null; echo "# VLP Dashboard Refresh (every 30 minutes)") | crontab -
    (crontab -l 2>/dev/null; echo "# $CRON_CMD") | crontab -
    
    echo -e "${GREEN}✅ Cron job template added (commented out)${NC}"
    echo "Edit with: crontab -e"
    echo "Uncomment the line to activate"
else
    echo "Skipping cron setup"
fi

echo ""

# Summary
echo "================================================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "================================================================================"
echo ""
echo "📊 Dashboard URL:"
echo "https://docs.google.com/spreadsheets/d/$SPREADSHEET_ID"
echo ""
echo "🎯 What's deployed:"
echo "  • VLP Revenue Dashboard sheet"
echo "  • Live ticker (updates every 5 min)"
echo "  • Service breakdown with 8 revenue streams"
echo "  • Stacking scenarios comparison"
echo "  • Profit analysis by DUoS band"
echo "  • Service compatibility matrix"
echo "  • 48-period forecast"
echo ""
echo "🔄 Refresh options:"
echo "  • Automatic: Apps Script triggers (5-30 min)"
echo "  • Manual: ⚡ Energy Tools → VLP Revenue → Refresh VLP Data"
echo "  • Python: python3 refresh_vlp_dashboard.py"
echo ""
echo "📖 Documentation:"
echo "  • PRICING_DATA_ARCHITECTURE.md - Explains data sources"
echo "  • VLP_REVENUE_OUTPUT_SUMMARY.md - Latest analysis"
echo "  • energy_dashboard_clasp/README.md - Apps Script guide"
echo ""
echo "================================================================================"
echo ""
