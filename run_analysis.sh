#!/bin/bash

# Complete BigQuery + Python Analysis Pipeline
# Fetches 50 recent prices and calculates statistics on Railway

echo "🔍 Step 1: Querying BigQuery for 50 recent prices..."

SQL='SELECT price FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid` ORDER BY settlementDate DESC LIMIT 50'
TOKEN='codex_fQI8xJXNPnhasYBOjd6h7mPHoF7HNI0Dh8rlgoJ2skA'

# Query BigQuery
QRESP=$(curl -s -X POST https://jibber-jabber-production.up.railway.app/query_bigquery \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"sql\": \"$SQL\"}")

echo "✅ Query complete!"

# Extract prices into JSON array
PRICES=$(echo "$QRESP" | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps([row['price'] for row in data.get('data', [])]))")

echo "📊 Step 2: Executing Python analysis on Railway..."
echo ""

# Execute Python analysis
curl -s -X POST https://jibber-jabber-production.up.railway.app/execute \
  -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"language\": \"python\",
    \"timeout\": 30,
    \"code\": \"import statistics\\nprices = $PRICES\\nif prices:\\n    mean = statistics.mean(prices)\\n    median = statistics.median(prices)\\n    stdev = statistics.stdev(prices) if len(prices) > 1 else 0.0\\n    volatility = (stdev / mean * 100) if mean else 0.0\\n    print('📊 UK Electricity Market Analysis (Last 50 Prices)')\\n    print('=' * 55)\\n    print(f'Count: {len(prices)} prices')\\n    print(f'Mean: £{mean:.2f}/MWh')\\n    print(f'Median: £{median:.2f}/MWh')\\n    print(f'Standard Deviation: £{stdev:.2f}')\\n    print(f'Volatility: {volatility:.2f}%')\\n    print(f'Min: £{min(prices):.2f}/MWh')\\n    print(f'Max: £{max(prices):.2f}/MWh')\\n    print(f'Range: £{max(prices) - min(prices):.2f}')\\nelse:\\n    print('❌ No prices returned')\"
  }" | python3 -c "import sys, json; result=json.load(sys.stdin); print(result.get('output', result.get('error', 'Unknown')))"

echo ""
echo "✅ Analysis complete!"
