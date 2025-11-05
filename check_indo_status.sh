#!/bin/bash
# CHECK INDO DATA STATUS - Run at 9 AM GMT on 5 November 2025
# This script checks if INDO files have been processed into BigQuery

echo "=========================================="
echo "INDO DATA STATUS CHECK"
echo "$(date)"
echo "=========================================="
echo ""

echo "1️⃣ Checking INDO files remaining on server..."
INDO_FILES=$(ssh root@94.237.55.234 'find /opt/iris-pipeline/iris-clients/python/iris_data/INDO -name "*.json" 2>/dev/null | wc -l')
echo "   INDO files remaining: $INDO_FILES"
echo ""

echo "2️⃣ Checking if bmrs_indo_iris table exists in BigQuery..."
if bq ls inner-cinema-476211-u9:uk_energy_prod | grep -q "bmrs_indo_iris"; then
    echo "   ✅ Table exists!"
    echo ""
    
    echo "3️⃣ Checking INDO data freshness..."
    bq query --use_legacy_sql=false "
    SELECT 
        MAX(DATE(settlementDate)) as latest_date, 
        MIN(DATE(settlementDate)) as earliest_date,
        COUNT(*) as total_records,
        COUNT(DISTINCT DATE(settlementDate)) as days_covered
    FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_indo_iris\`
    "
    echo ""
    
    echo "4️⃣ Expected: latest_date = 2025-11-04 or 2025-11-05"
    echo ""
    
    echo "5️⃣ Checking all new _iris tables created..."
    echo "Tables created:"
    bq ls inner-cinema-476211-u9:uk_energy_prod | grep "_iris"
    echo ""
    
    echo "6️⃣ Checking uploader status..."
    ssh root@94.237.55.234 'ps aux | grep iris_to_bigquery | grep -v grep' > /dev/null
    if [ $? -eq 0 ]; then
        echo "   ✅ Uploader still running"
    else
        echo "   ❌ Uploader NOT running!"
    fi
    echo ""
    
    echo "7️⃣ Last 20 lines of uploader log..."
    ssh root@94.237.55.234 'tail -20 /opt/iris-pipeline/logs/iris_uploader.log'
    echo ""
    
    echo "=========================================="
    echo "✅ CHECK COMPLETE"
    echo "=========================================="
    echo ""
    echo "If latest_date is 2025-11-04 or newer, you can:"
    echo "1. Run the dashboard script: python3 create_live_dashboard.py"
    echo "2. Check the results in Google Sheets"
    
else
    echo "   ❌ Table does NOT exist yet!"
    echo ""
    echo "   The uploader is still processing earlier datasets."
    echo "   Current progress:"
    ssh root@94.237.55.234 'tail -30 /opt/iris-pipeline/logs/iris_uploader.log | grep -E "📦 Found|📊 Processing|Cycle"'
    echo ""
    echo "   Check again in 2-3 hours."
fi
