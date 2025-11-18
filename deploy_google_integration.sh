#!/bin/bash
#
# Google Integration Deployment Script
# =====================================
# Sets up BigQuery datasets, Google Sheets connections, and service account permissions
#
# Usage: ./deploy_google_integration.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="inner-cinema-476211-u9"
LOCATION="US"
CREDENTIALS_FILE="inner-cinema-credentials.json"
DATASET_SOURCE="uk_energy_prod"
DATASET_ANALYTICS="uk_energy_analysis"
DASHBOARD_SHEET_ID="12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Google Integration Deployment${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Step 1: Verify credentials
echo -e "${YELLOW}Step 1: Verifying Google credentials...${NC}"
if [ ! -f "$CREDENTIALS_FILE" ]; then
    echo -e "${RED}❌ Error: Credentials file not found: $CREDENTIALS_FILE${NC}"
    echo -e "${YELLOW}Please ensure your service account credentials are in: $CREDENTIALS_FILE${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Credentials file found${NC}"
export GOOGLE_APPLICATION_CREDENTIALS="$CREDENTIALS_FILE"

# Step 2: Test BigQuery connection
echo -e "\n${YELLOW}Step 2: Testing BigQuery connection...${NC}"
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='$PROJECT_ID', location='$LOCATION')
print('✅ BigQuery connection successful')
" || {
    echo -e "${RED}❌ BigQuery connection failed${NC}"
    exit 1
}

# Step 3: Create analytics dataset
echo -e "\n${YELLOW}Step 3: Creating analytics dataset...${NC}"
python3 << 'EOF'
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

dataset_id = 'inner-cinema-476211-u9.uk_energy_analysis'
try:
    dataset = bigquery.Dataset(dataset_id)
    dataset.location = 'US'
    dataset = client.create_dataset(dataset, exists_ok=True)
    print(f'✅ Created dataset: {dataset_id}')
except Exception as e:
    print(f'⚠️  Dataset may already exist: {e}')
EOF

# Step 4: Test Google Sheets connection
echo -e "\n${YELLOW}Step 4: Testing Google Sheets connection...${NC}"
python3 -c "
import gspread
from google.oauth2.service_account import Credentials

scopes = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

creds = Credentials.from_service_account_file('$CREDENTIALS_FILE', scopes=scopes)
gc = gspread.authorize(creds)

try:
    sheet = gc.open_by_key('$DASHBOARD_SHEET_ID')
    print(f'✅ Google Sheets connection successful')
    print(f'   Sheet title: {sheet.title}')
except Exception as e:
    print(f'❌ Google Sheets connection failed: {e}')
    exit(1)
" || {
    echo -e "${RED}❌ Google Sheets connection failed${NC}"
    echo -e "${YELLOW}Make sure the service account has access to the sheet:${NC}"
    echo -e "${YELLOW}  https://docs.google.com/spreadsheets/d/$DASHBOARD_SHEET_ID${NC}"
    exit 1
}

# Step 5: Verify required Python packages
echo -e "\n${YELLOW}Step 5: Verifying Python packages...${NC}"
REQUIRED_PACKAGES="google-cloud-bigquery gspread google-auth pandas numpy scipy statsmodels matplotlib seaborn"
MISSING_PACKAGES=""

for pkg in $REQUIRED_PACKAGES; do
    python3 -c "import $(echo $pkg | tr '-' '_' | cut -d'_' -f1)" 2>/dev/null || {
        MISSING_PACKAGES="$MISSING_PACKAGES $pkg"
    }
done

if [ -n "$MISSING_PACKAGES" ]; then
    echo -e "${YELLOW}⚠️  Missing packages:$MISSING_PACKAGES${NC}"
    echo -e "${YELLOW}Installing missing packages...${NC}"
    .venv/bin/pip install $MISSING_PACKAGES
    echo -e "${GREEN}✅ Packages installed${NC}"
else
    echo -e "${GREEN}✅ All required packages installed${NC}"
fi

# Step 6: Check data availability
echo -e "\n${YELLOW}Step 6: Checking data availability...${NC}"
python3 << EOF
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '$CREDENTIALS_FILE'
client = bigquery.Client(project='$PROJECT_ID', location='$LOCATION')

tables_to_check = [
    'bmrs_mid',
    'bmrs_boalf',
    'bmrs_fuelinst_iris',
    'bmrs_inddem_iris',
    'bmrs_freq'
]

print('Checking tables in $DATASET_SOURCE:')
for table_name in tables_to_check:
    query = f"""
    SELECT COUNT(*) as cnt
    FROM \`$PROJECT_ID.$DATASET_SOURCE.{table_name}\`
    LIMIT 1
    """
    try:
        result = client.query(query).result()
        row_count = list(result)[0].cnt
        print(f'  ✅ {table_name}: {row_count:,} rows')
    except Exception as e:
        print(f'  ❌ {table_name}: Not accessible - {e}')

EOF

# Step 7: Create output directories
echo -e "\n${YELLOW}Step 7: Creating output directories...${NC}"
mkdir -p output
mkdir -p logs
mkdir -p tests
echo -e "${GREEN}✅ Directories created${NC}"

# Step 8: Run a test query
echo -e "\n${YELLOW}Step 8: Running test query...${NC}"
python3 << 'EOF'
from google.cloud import bigquery
import os
import pandas as pd

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

query = """
SELECT 
    settlementDate,
    COUNT(*) as records,
    AVG(CASE WHEN price > 0 THEN price END) as avg_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY settlementDate
ORDER BY settlementDate DESC
LIMIT 7
"""

try:
    df = client.query(query).to_dataframe()
    print('✅ Test query successful')
    print('\nLast 7 days of price data:')
    print(df.to_string(index=False))
except Exception as e:
    print(f'❌ Test query failed: {e}')
    exit(1)
EOF

# Summary
echo -e "\n${BLUE}============================================${NC}"
echo -e "${GREEN}✅ Google Integration Deployment Complete${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "${GREEN}Configuration Summary:${NC}"
echo -e "  Project ID:     $PROJECT_ID"
echo -e "  Location:       $LOCATION"
echo -e "  Source Dataset: $DATASET_SOURCE"
echo -e "  Analytics Dataset: $DATASET_ANALYTICS"
echo -e "  Dashboard Sheet: https://docs.google.com/spreadsheets/d/$DASHBOARD_SHEET_ID"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo -e "  1. Run advanced statistics: .venv/bin/python advanced_statistical_analysis.py"
echo -e "  2. Run battery analysis: .venv/bin/python battery_profit_analysis.py"
echo -e "  3. Update GSP dashboard: .venv/bin/python gsp_wind_analysis.py"
echo ""
echo -e "${GREEN}Monitoring:${NC}"
echo -e "  Check BigQuery: https://console.cloud.google.com/bigquery?project=$PROJECT_ID"
echo -e "  Check Dashboard: https://docs.google.com/spreadsheets/d/$DASHBOARD_SHEET_ID"
echo ""
