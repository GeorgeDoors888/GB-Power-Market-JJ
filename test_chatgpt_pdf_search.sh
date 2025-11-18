#!/bin/bash

# Test ChatGPT can find PDFs via Railway endpoint
echo "🧪 Testing PDF Discovery for ChatGPT..."
echo ""

RAILWAY_URL="https://jibber-jabber-production.up.railway.app"
AUTH_TOKEN="Bearer codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA"

# Test 1: List all PDFs
echo "📋 Test 1: List all available PDFs"
curl -s -X POST "$RAILWAY_URL/query_bigquery" \
  -H "Authorization: $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT JSON_VALUE(metadata, '\''$.filename'\'') as filename, COUNT(*) as chunks FROM `inner-cinema-476211-u9.uk_energy_prod.document_chunks` WHERE JSON_VALUE(metadata, '\''$.mime_type'\'') = '\''application/pdf'\'' GROUP BY filename ORDER BY chunks DESC LIMIT 5"
  }' | jq -r '.results[] | "\(.filename): \(.chunks) chunks"'

echo ""
echo "🔍 Test 2: Search for 'grid code' in PDFs"
curl -s -X POST "$RAILWAY_URL/query_bigquery" \
  -H "Authorization: $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sql": "SELECT JSON_VALUE(metadata, '\''$.filename'\'') as filename, chunk_index, LEFT(content, 150) as preview FROM `inner-cinema-476211-u9.uk_energy_prod.document_chunks` WHERE JSON_VALUE(metadata, '\''$.mime_type'\'') = '\''application/pdf'\'' AND LOWER(content) LIKE '\''%grid code%'\'' LIMIT 3"
  }' | jq -r '.results[] | "\n�� \(.filename) (chunk \(.chunk_index))\n   \(.preview)..."'

echo ""
echo "✅ Tests complete!"
