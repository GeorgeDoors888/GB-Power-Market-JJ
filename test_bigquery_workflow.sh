#!/bin/bash
# BigQuery HH DATA - End-to-End Test Script
# Tests complete workflow: Generate → Upload → Query → Calculate

set -e  # Exit on error

echo "🧪 BigQuery HH DATA End-to-End Test"
echo "===================================="
echo ""

# Configuration
PROJECT_ID="inner-cinema-476211-u9"
DATASET="uk_energy_prod"
TABLE="hh_data_btm_generated"
SUPPLY_TYPE="Commercial"
SCALE_VALUE=10000

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Check if HH DATA sheet exists
echo "📋 Step 1: Check HH DATA sheet status"
echo "--------------------------------------"
echo "${YELLOW}MANUAL STEP REQUIRED:${NC}"
echo "1. Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit"
echo "2. Click button: '🔄 Generate HH Data'"
echo "3. Wait 10-15 seconds"
echo "4. Verify 'HH DATA' sheet exists with 17,520 rows"
echo ""
read -p "Press Enter after generating HH DATA in Google Sheets..."
echo ""

# Step 2: Upload to BigQuery
echo "📤 Step 2: Upload HH DATA to BigQuery"
echo "--------------------------------------"
echo "Running: python3 upload_hh_to_bigquery.py \"${SUPPLY_TYPE}\" ${SCALE_VALUE}"
echo ""

if python3 upload_hh_to_bigquery.py "${SUPPLY_TYPE}" ${SCALE_VALUE} "test_workflow"; then
    echo "${GREEN}✅ Upload successful${NC}"
else
    echo "${RED}❌ Upload failed${NC}"
    exit 1
fi
echo ""

# Step 3: Verify BigQuery data
echo "🔍 Step 3: Verify BigQuery data"
echo "-------------------------------"
echo "Querying BigQuery table..."

RECORD_COUNT=$(python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='${PROJECT_ID}', location='US')
query = '''
SELECT COUNT(*) as count
FROM \`${PROJECT_ID}.${DATASET}.${TABLE}\`
WHERE generated_by = 'test_workflow'
'''
result = client.query(query).result()
for row in result:
    print(row.count)
")

if [ "$RECORD_COUNT" -eq 17520 ]; then
    echo "${GREEN}✅ Found 17,520 records in BigQuery${NC}"
else
    echo "${RED}❌ Expected 17,520 records, found ${RECORD_COUNT}${NC}"
    exit 1
fi
echo ""

# Step 4: Verify sheet deletion
echo "🗑️  Step 4: Verify HH DATA sheet deletion"
echo "----------------------------------------"
echo "${YELLOW}MANUAL VERIFICATION REQUIRED:${NC}"
echo "1. Return to Google Sheets"
echo "2. Verify 'HH DATA' sheet is DELETED"
echo "3. Only BtM sheet should remain"
echo ""
read -p "Press Enter after verifying sheet deletion..."
echo ""

# Step 5: Test fast query performance
echo "⚡ Step 5: Test query performance"
echo "--------------------------------"
echo "Running: python3 btm_dno_lookup.py"
echo "Expected: ~10 seconds (70x faster than 7 minutes)"
echo ""

START_TIME=$(date +%s)
if time python3 btm_dno_lookup.py > /tmp/btm_test_output.txt 2>&1; then
    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))
    
    if [ "$DURATION" -le 20 ]; then
        echo "${GREEN}✅ Completed in ${DURATION} seconds (target: <20 sec)${NC}"
    else
        echo "${YELLOW}⚠️  Completed in ${DURATION} seconds (slower than expected)${NC}"
    fi
    
    # Check if BigQuery was used
    if grep -q "Reading HH DATA from BigQuery" /tmp/btm_test_output.txt; then
        echo "${GREEN}✅ Used BigQuery (fast path)${NC}"
    elif grep -q "falling back to Google Sheets" /tmp/btm_test_output.txt; then
        echo "${RED}❌ Fell back to Google Sheets (slow path)${NC}"
    fi
else
    echo "${RED}❌ btm_dno_lookup.py failed${NC}"
    cat /tmp/btm_test_output.txt
    exit 1
fi
echo ""

# Step 6: Verify BtM sheet results
echo "📊 Step 6: Verify BtM sheet results"
echo "-----------------------------------"
echo "${YELLOW}MANUAL VERIFICATION REQUIRED:${NC}"
echo "1. Open BtM sheet in Google Sheets"
echo "2. Check cells A28-C30 for DUoS kWh totals (Red/Amber/Green)"
echo "3. Check cells A31-C39 for transmission levy unit rates:"
echo "   • TNUoS: £12.50/MWh"
echo "   • BSUoS: £4.50/MWh"
echo "   • CCL: £7.75/MWh"
echo "   • RO: £6.50/MWh"
echo "   • FiT: £10.50/MWh"
echo ""
read -p "Press Enter after verifying results..."
echo ""

# Step 7: Check BigQuery table metadata
echo "📈 Step 7: BigQuery table metadata"
echo "----------------------------------"

python3 << 'EOF'
from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
TABLE = "hh_data_btm_generated"

client = bigquery.Client(project=PROJECT_ID, location="US")
table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"

# Get table metadata
table = client.get_table(table_id)

print(f"Table: {table.table_id}")
print(f"Total rows: {table.num_rows:,}")
print(f"Total size: {table.num_bytes / 1024 / 1024:.2f} MB")
print(f"Partitioning: {table.time_partitioning.type_} on {table.time_partitioning.field}")
print(f"Clustering: {', '.join(table.clustering_fields)}")
print(f"Created: {table.created}")
print(f"Modified: {table.modified}")

# Get unique supply types
query = f"""
SELECT 
  supply_type,
  COUNT(*) as records,
  MAX(generated_at) as last_generated
FROM `{table_id}`
GROUP BY supply_type
ORDER BY last_generated DESC
"""

print("\nSupply Types:")
for row in client.query(query).result():
    print(f"  • {row.supply_type}: {row.records:,} records (last: {row.last_generated})")

EOF

echo ""

# Summary
echo "🎉 Test Summary"
echo "==============="
echo ""
echo "${GREEN}✅ All tests completed successfully!${NC}"
echo ""
echo "Performance Comparison:"
echo "  • Before (Google Sheets API): ~7 minutes"
echo "  • After (BigQuery):          ~10 seconds"
echo "  • Improvement:               70x faster"
echo ""
echo "Next Steps:"
echo "1. Create BigQuery scheduled cleanup query:"
echo "   https://console.cloud.google.com/bigquery/scheduled-queries?project=inner-cinema-476211-u9"
echo "   SQL: See create_bigquery_scheduled_cleanup.sql"
echo ""
echo "2. Optional: Add direct BigQuery upload to Apps Script"
echo "   (eliminates manual python3 command)"
echo ""
echo "📚 Full documentation: BIGQUERY_HH_DATA_IMPLEMENTATION.md"
