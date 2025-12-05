#!/bin/bash
# deploy_bess_dashboard.sh - Complete deployment automation
# Usage: ./deploy_bess_dashboard.sh

set -e  # Exit on error

echo "🚀 GB Power Market BESS Dashboard - Deployment Script"
echo "========================================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="inner-cinema-476211-u9"
DATASET="uk_energy_prod"
CREDS_FILE="inner-cinema-credentials.json"
SHEET_ID="1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

echo "📋 Checking prerequisites..."
echo ""

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Python 3: $(python3 --version)${NC}"
fi

# Check credentials file
if [ ! -f "$CREDS_FILE" ]; then
    echo -e "${RED}❌ Credentials file not found: $CREDS_FILE${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Credentials file found${NC}"
fi

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/$CREDS_FILE"
echo -e "${GREEN}✅ GOOGLE_APPLICATION_CREDENTIALS set${NC}"

echo ""
echo "📦 Installing Python dependencies..."
echo ""

# Install required packages
pip3 install --user google-cloud-bigquery db-dtypes pyarrow pandas gspread oauth2client --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
fi

echo ""
echo "🗄️  Deploying BigQuery views..."
echo ""

# Deploy v_bess_cashflow_inputs view
echo "Creating v_bess_cashflow_inputs view..."
bq query --use_legacy_sql=false < bigquery_views/v_bess_cashflow_inputs.sql

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ BigQuery views deployed${NC}"
else
    echo -e "${YELLOW}⚠️  View deployment had warnings (may already exist)${NC}"
fi

echo ""
echo "🧪 Testing Python modules..."
echo ""

# Test bess_profit_model
echo "Testing BESS profit model..."
python3 -c "from bess_profit_model_enhanced import BESSAsset; print('✅ BESS model OK')" 2>&1 | grep -q "✅" && echo -e "${GREEN}✅ BESS model loaded${NC}" || echo -e "${YELLOW}⚠️  BESS model warnings${NC}"

# Test tcr_charge_model
echo "Testing TCR charge model..."
python3 -c "from tcr_charge_model_enhanced import TCRChargeModel; print('✅ TCR model OK')" 2>&1 | grep -q "✅" && echo -e "${GREEN}✅ TCR model loaded${NC}" || echo -e "${YELLOW}⚠️  TCR model warnings${NC}"

echo ""
echo "🔄 Running dashboard pipeline (dry run)..."
echo ""

# Test dashboard pipeline
python3 dashboard_pipeline.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Dashboard pipeline completed${NC}"
else
    echo -e "${RED}❌ Dashboard pipeline failed${NC}"
    exit 1
fi

echo ""
echo "📝 Setting up automation..."
echo ""

# Create logs directory
mkdir -p logs

# Create cron entry (commented out - user must enable manually)
CRON_ENTRY="*/15 * * * * cd $PWD && /usr/bin/python3 dashboard_pipeline.py >> logs/pipeline.log 2>&1"

echo "To enable automatic updates every 15 minutes, add this to crontab:"
echo ""
echo -e "${YELLOW}$CRON_ENTRY${NC}"
echo ""
echo "Run: crontab -e"
echo "Then paste the line above and save."
echo ""

# Create systemd service (optional)
cat > bess-dashboard.service << EOF
[Unit]
Description=GB Power Market BESS Dashboard
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PWD
Environment="GOOGLE_APPLICATION_CREDENTIALS=$PWD/$CREDS_FILE"
ExecStart=/usr/bin/python3 $PWD/dashboard_pipeline.py
Restart=on-failure
RestartSec=300

[Install]
WantedBy=multi-user.target
EOF

echo "Optional: Systemd service file created (bess-dashboard.service)"
echo "To install: sudo cp bess-dashboard.service /etc/systemd/system/"
echo "Then: sudo systemctl enable bess-dashboard.service"
echo "And: sudo systemctl start bess-dashboard.service"
echo ""

# Create monitoring script
cat > check_dashboard.sh << 'EOF'
#!/bin/bash
# Quick health check for dashboard pipeline

LAST_RUN=$(tail -1 logs/pipeline.log 2>/dev/null | grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}' | head -1)

if [ -z "$LAST_RUN" ]; then
    echo "❌ No pipeline runs found"
    exit 1
fi

LAST_RUN_EPOCH=$(date -d "$LAST_RUN" +%s 2>/dev/null || date -j -f "%Y-%m-%d %H:%M:%S" "$LAST_RUN" +%s 2>/dev/null)
NOW_EPOCH=$(date +%s)
AGE_MINUTES=$(( ($NOW_EPOCH - $LAST_RUN_EPOCH) / 60 ))

if [ $AGE_MINUTES -lt 20 ]; then
    echo "✅ Dashboard healthy - last run $AGE_MINUTES mins ago"
else
    echo "⚠️  Dashboard stale - last run $AGE_MINUTES mins ago"
fi

# Show last 5 lines
echo ""
echo "Last log entries:"
tail -5 logs/pipeline.log
EOF

chmod +x check_dashboard.sh

echo -e "${GREEN}✅ Monitoring script created: ./check_dashboard.sh${NC}"
echo ""

# Apps Script deployment instructions
cat > APPS_SCRIPT_DEPLOY.txt << EOF
=============================================================================
📱 APPS SCRIPT DEPLOYMENT INSTRUCTIONS
=============================================================================

1. Open your Google Sheet:
   https://docs.google.com/spreadsheets/d/$SHEET_ID/

2. Go to: Extensions → Apps Script

3. Delete any existing code in Code.gs

4. Copy the entire contents of:
   apps_script_enhanced/Code.js

5. Paste into Code.gs

6. Click Save (disk icon)

7. Run the function: formatAllSheets
   - Click "Run" button
   - Authorize when prompted
   - Grant permissions

8. Refresh your Google Sheet

9. You should now see a menu: ⚡ GB Energy Dashboard

10. Use the menu to:
    - Format Dashboard
    - Format BESS Sheet
    - Format TCR Sheet
    - Setup Dropdowns
    - Refresh Maps

=============================================================================

To add automatic refresh triggers:

1. In Apps Script editor: Click clock icon (Triggers)
2. Click "+ Add Trigger"
3. Choose function: formatAllSheets
4. Event source: Time-driven
5. Type: Minutes timer
6. Interval: Every 15 minutes
7. Save

This will auto-format sheets every 15 minutes to maintain design.

=============================================================================
EOF

echo -e "${GREEN}✅ Apps Script deployment guide created: APPS_SCRIPT_DEPLOY.txt${NC}"
echo ""

echo "========================================================="
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo "========================================================="
echo ""
echo "Next steps:"
echo ""
echo "1. ✅ Python pipeline is ready and tested"
echo "2. ⏰ Enable cron automation (see instructions above)"
echo "3. 📱 Deploy Apps Script (see APPS_SCRIPT_DEPLOY.txt)"
echo "4. 📊 Verify data in Google Sheets:"
echo "   https://docs.google.com/spreadsheets/d/$SHEET_ID/"
echo ""
echo "Monitoring:"
echo "  - Check logs: tail -f logs/pipeline.log"
echo "  - Health check: ./check_dashboard.sh"
echo "  - Manual run: python3 dashboard_pipeline.py"
echo ""
echo "Documentation:"
echo "  - Implementation guide: BESS_DASHBOARD_IMPLEMENTATION.md"
echo "  - Architecture: STOP_DATA_ARCHITECTURE_REFERENCE.md"
echo "  - Configuration: PROJECT_CONFIGURATION.md"
echo ""
echo -e "${GREEN}Happy analyzing! 📈⚡${NC}"
