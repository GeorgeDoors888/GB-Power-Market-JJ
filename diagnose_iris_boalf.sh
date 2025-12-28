#!/bin/bash
# Diagnose IRIS BOALF Collection Issue
# This script helps identify why BOALF data stopped on Dec 18

echo "════════════════════════════════════════════════════════════════════════════"
echo "🔍 IRIS BOALF DIAGNOSTIC SCRIPT"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""

echo "Step 1: Check local IRIS configuration"
echo "────────────────────────────────────────────────────────────────────────────"

if [ -d "iris-clients" ]; then
    echo "✅ Found iris-clients directory"

    # Check for BOALF configuration
    echo ""
    echo "Checking for BOALF in configuration files..."
    grep -r "BOALF\|boalf" iris-clients/ 2>/dev/null || echo "⚠️  No BOALF references found"

    echo ""
    echo "Python IRIS client scripts:"
    find iris-clients/ -name "*.py" -type f 2>/dev/null
else
    echo "❌ iris-clients directory not found"
fi

echo ""
echo "Step 2: Check if IRIS uploader is configured for BOALF"
echo "────────────────────────────────────────────────────────────────────────────"

if [ -f "iris_to_bigquery_unified.py" ]; then
    echo "✅ Found iris_to_bigquery_unified.py"
    echo ""
    echo "Checking for BOALF table mapping..."
    grep -i "boalf" iris_to_bigquery_unified.py || echo "⚠️  No BOALF mapping found"
else
    echo "❌ iris_to_bigquery_unified.py not found"
fi

echo ""
echo "Step 3: Check AlmaLinux server (requires SSH access)"
echo "────────────────────────────────────────────────────────────────────────────"
echo ""
echo "Run these commands on 94.237.55.234:"
echo ""
echo "  ssh root@94.237.55.234"
echo "  cd /opt/iris-pipeline"
echo "  cat config.yml | grep -i boalf"
echo "  ps aux | grep iris"
echo "  tail -50 logs/iris_client.log | grep -i boalf"
echo ""

echo "Step 4: BigQuery table status"
echo "────────────────────────────────────────────────────────────────────────────"

python3 << 'PYEOF'
from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

query = """
SELECT
    DATE(settlementDate) as date,
    COUNT(*) as records
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
WHERE DATE(settlementDate) >= '2025-12-15'
GROUP BY date
ORDER BY date DESC
LIMIT 10
"""

print("\nbmrs_boalf_iris recent data:")
result = client.query(query).to_dataframe()
if result.empty:
    print("❌ NO DATA since Dec 15")
else:
    print(result.to_string(index=False))
    latest = str(result['date'].max())
    if latest < '2025-12-19':
        print(f"\n⚠️  Data stopped on {latest}")
PYEOF

echo ""
echo "════════════════════════════════════════════════════════════════════════════"
echo "📋 RECOMMENDED ACTIONS"
echo "════════════════════════════════════════════════════════════════════════════"
echo ""
echo "1. Check AlmaLinux IRIS server configuration"
echo "   → Verify BOALF endpoint is in config.yml"
echo ""
echo "2. Check IRIS client logs for errors"
echo "   → Look for connection issues or API errors"
echo ""
echo "3. Restart IRIS service if configuration is correct"
echo "   → systemctl restart iris-client (or equivalent)"
echo ""
echo "4. Once fixed, backfill missing data:"
echo "   → cd /home/george/GB-Power-Market-JJ"
echo "   → python3 daily_data_pipeline.py"
echo ""
echo "════════════════════════════════════════════════════════════════════════════"
