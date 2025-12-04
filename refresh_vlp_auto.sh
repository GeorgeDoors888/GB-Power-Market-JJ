#!/bin/bash
#
# VLP Dashboard Auto-Refresh Script
# Runs dashboard refresh and charts update with error handling
#

set -e  # Exit on error

# Configuration
PROJECT_DIR="$HOME/GB-Power-Market-JJ"
LOG_DIR="$PROJECT_DIR/logs"
PYTHON_CMD="python3"  # Use system python3 with user packages
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Ensure log directory exists
mkdir -p "$LOG_DIR"

echo "================================================================================"
echo "VLP DASHBOARD AUTO-REFRESH"
echo "Started: $TIMESTAMP"
echo "================================================================================"
echo

# Check if credentials file exists
if [ ! -f "$PROJECT_DIR/inner-cinema-credentials.json" ]; then
    echo -e "${RED}❌ ERROR: Credentials file not found${NC}"
    echo "Expected: $PROJECT_DIR/inner-cinema-credentials.json"
    exit 1
fi

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Step 1: Refresh dashboard data
echo -e "${YELLOW}📊 Step 1: Refreshing dashboard data...${NC}"
if $PYTHON_CMD vlp_dashboard_python.py >> "$LOG_DIR/vlp_refresh_$(date +%Y%m%d).log" 2>&1; then
    echo -e "${GREEN}✅ Dashboard data refreshed${NC}"
else
    echo -e "${RED}❌ Dashboard refresh failed (see logs)${NC}"
    echo "Log: $LOG_DIR/vlp_refresh_$(date +%Y%m%d).log"
    exit 1
fi

echo

# Step 2: Update charts (optional, less frequent)
# Uncomment if you want charts updated every time
# if [ "$1" == "--with-charts" ]; then
#     echo -e "${YELLOW}📈 Step 2: Updating charts...${NC}"
#     if $PYTHON_CMD vlp_charts_python.py >> "$LOG_DIR/vlp_charts_$(date +%Y%m%d).log" 2>&1; then
#         echo -e "${GREEN}✅ Charts updated${NC}"
#     else
#         echo -e "${RED}⚠️  Charts update failed (non-critical)${NC}"
#     fi
#     echo
# fi

# Get latest metrics from BigQuery
echo -e "${YELLOW}📈 Current Metrics:${NC}"
METRICS=$($PYTHON_CMD -c "
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

creds = Credentials.from_service_account_file(
    'inner-cinema-credentials.json',
    scopes=['https://www.googleapis.com/auth/bigquery']
)
client = bigquery.Client(project='inner-cinema-476211-u9', location='US', credentials=creds)

query = '''
SELECT 
    settlementDate,
    settlementPeriod,
    ROUND(net_margin_per_mwh, 2) as profit,
    ROUND(total_stacked_revenue_per_mwh, 2) as revenue,
    trading_signal,
    duos_band
FROM \`inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs\`
ORDER BY settlementDate DESC, settlementPeriod DESC
LIMIT 1
'''

result = client.query(query).result()
for row in result:
    print(f'Date: {row.settlementDate} P{row.settlementPeriod}')
    print(f'Profit: £{row.profit:.2f}/MWh')
    print(f'Revenue: £{row.revenue:.2f}/MWh')
    print(f'Signal: {row.trading_signal}')
    print(f'Band: {row.duos_band}')
" 2>/dev/null)

if [ -n "$METRICS" ]; then
    echo "$METRICS" | sed 's/^/   /'
else
    echo -e "${RED}   ⚠️  Could not fetch metrics${NC}"
fi

echo
echo "================================================================================"
echo -e "${GREEN}✅ AUTO-REFRESH COMPLETE${NC}"
echo "Finished: $(date '+%Y-%m-%d %H:%M:%S')"
echo "================================================================================"
echo
echo "📊 View dashboard:"
echo "   https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit"
echo

# Log completion
echo "[$TIMESTAMP] Refresh completed successfully" >> "$LOG_DIR/vlp_refresh_history.log"
