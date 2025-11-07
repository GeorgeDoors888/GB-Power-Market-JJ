#!/bin/bash
# AI Gateway Test Suite
# Tests all endpoints with authentication

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get API key from .env.ai-gateway
API_KEY=$(grep "^AI_GATEWAY_API_KEY=" .env.ai-gateway | cut -d'=' -f2)
BASE_URL="http://localhost:8000"

if [ -z "$API_KEY" ]; then
    echo -e "${RED}❌ Error: API_KEY not found in .env.ai-gateway${NC}"
    exit 1
fi

echo "=================================================="
echo "🧪 AI Gateway Test Suite"
echo "=================================================="
echo ""

# Function to test endpoint
test_endpoint() {
    local name="$1"
    local method="$2"
    local endpoint="$3"
    local data="$4"
    
    echo -e "${BLUE}Testing: $name${NC}"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $API_KEY" "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST -H "Authorization: Bearer $API_KEY" -H "Content-Type: application/json" -d "$data" "$BASE_URL$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n-1)
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✅ PASSED${NC} (HTTP $http_code)"
        echo "$body" | python3 -m json.tool 2>/dev/null | head -n 20 || echo "$body" | head -n 20
    else
        echo -e "${RED}❌ FAILED${NC} (HTTP $http_code)"
        echo "$body"
    fi
    echo ""
}

# Test 1: Root endpoint (no auth)
echo -e "${BLUE}Testing: Root endpoint (no auth)${NC}"
curl -s "$BASE_URL/" | python3 -m json.tool | head -15
echo ""

# Test 2: Health check
test_endpoint "Health Check" "GET" "/health" ""

# Test 3: BigQuery - Prices (read-only)
test_endpoint "BigQuery Prices (7 days)" "GET" "/bigquery/prices?days=7" ""

# Test 4: BigQuery - Generation (read-only)
test_endpoint "BigQuery Generation (Wind, 3 days)" "GET" "/bigquery/generation?days=3&fuel_type=WIND" ""

# Test 5: Google Sheets - Read
test_endpoint "Google Sheets Read" "GET" "/sheets/read?tab=Analysis%20BI%20Enhanced&range=A1:E5" ""

# Test 6: UpCloud Status
test_endpoint "UpCloud Server Status" "GET" "/upcloud/status" ""

echo "=================================================="
echo "⚠️  WRITE OPERATIONS (requires approval)"
echo "=================================================="
echo ""

# Test 7: Sheets Update (with approval requirement)
echo -e "${YELLOW}Testing: Google Sheets Update (should require approval)${NC}"
curl -s -X POST -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"tab": "Raw Data", "range": "Z1", "values": [["Test from API"]]}' \
  "$BASE_URL/sheets/update" | python3 -m json.tool
echo ""

# Test 8: Run Script (with approval)
echo -e "${YELLOW}Testing: Run Script (should show whitelist)${NC}"
curl -s -X POST -H "Authorization: Bearer $API_KEY" \
  "$BASE_URL/upcloud/run-script?script_name=battery_arbitrage.py" | python3 -m json.tool
echo ""

echo "=================================================="
echo "🚨 DANGEROUS OPERATIONS (requires approval)"
echo "=================================================="
echo ""

# Test 9: BigQuery Write (dry run)
echo -e "${YELLOW}Testing: BigQuery Write (dry run)${NC}"
curl -s -X POST -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`", "dry_run": true, "require_approval": false}' \
  "$BASE_URL/bigquery/execute" | python3 -m json.tool
echo ""

# Test 10: SSH Command (with approval)
echo -e "${YELLOW}Testing: SSH Command (should require approval)${NC}"
curl -s -X POST -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command": "uptime", "require_approval": true}' \
  "$BASE_URL/upcloud/ssh" | python3 -m json.tool
echo ""

# Test 11: Dangerous Command Detection
echo -e "${RED}Testing: Dangerous Command Detection (should block)${NC}"
curl -s -X POST -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"command": "rm -rf /tmp/test", "require_approval": false}' \
  "$BASE_URL/upcloud/ssh" | python3 -m json.tool
echo ""

echo "=================================================="
echo "✅ Test Suite Complete!"
echo "=================================================="
echo ""
echo "📝 Check audit log: tail -f /tmp/ai-gateway-audit.log"
echo "📊 View API docs: http://localhost:8000/docs"
