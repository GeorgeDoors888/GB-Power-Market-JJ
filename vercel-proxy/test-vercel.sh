#!/bin/bash

# Test Vercel Proxy Deployment
# Replace YOUR_VERCEL_URL with the actual URL from Vercel

echo "🧪 Testing Vercel Proxy Deployment"
echo "=================================="
echo ""

# Check if URL is provided
if [ -z "$1" ]; then
    echo "❌ Please provide your Vercel URL"
    echo ""
    echo "Usage: ./test-vercel.sh https://your-vercel-url.vercel.app"
    echo ""
    echo "Example: ./test-vercel.sh https://overarch-jibber-jabber-vercel-proxy.vercel.app"
    exit 1
fi

VERCEL_URL="$1"

echo "Testing URL: $VERCEL_URL"
echo ""

# Test 1: Health Check
echo "📊 Test 1: Health Check"
echo "----------------------"
curl -sS "${VERCEL_URL}/api/proxy?path=/health" | python3 -m json.tool
echo ""
echo ""

# Test 2: BigQuery Datasets
echo "📊 Test 2: List BigQuery Datasets"
echo "----------------------------------"
curl -sS "${VERCEL_URL}/api/proxy?path=/query_bigquery_get&sql=SELECT%20schema_name%20FROM%20%60jibber-jabber-knowledge.INFORMATION_SCHEMA.SCHEMATA%60" | python3 -m json.tool
echo ""
echo ""

# Test 3: List UK Energy Tables (first 5)
echo "📊 Test 3: List UK Energy Tables"
echo "---------------------------------"
curl -sS "${VERCEL_URL}/api/proxy?path=/query_bigquery_get&sql=SELECT%20table_name%20FROM%20%60jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES%60%20LIMIT%205" | python3 -m json.tool
echo ""
echo ""

echo "✅ Tests Complete!"
echo ""
echo "If all tests passed, your Vercel proxy is working!"
echo "Copy this URL to give to ChatGPT:"
echo ""
echo "    ${VERCEL_URL}/api/proxy"
echo ""
