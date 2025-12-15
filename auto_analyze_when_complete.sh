#!/bin/bash
# Auto-analyze ALL BMUs when 3-year ingestion completes
# Monitors ingestion progress and triggers comprehensive analysis at completion

TARGET_DAYS=1443
CHECK_INTERVAL=300  # 5 minutes

echo "════════════════════════════════════════════════════════════════"
echo "  AUTO-ANALYSIS: Waiting for 3-year ingestion to complete"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "📊 Target: $TARGET_DAYS days (2022-01-01 to 2025-12-13)"
echo "⏱️  Checking every $CHECK_INTERVAL seconds"
echo ""

while true; do
    # Get current progress
    CURRENT_DAYS=$(python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); query = 'SELECT COUNT(DISTINCT DATE(CAST(settlementDate AS STRING))) as days FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_boav\`'; row = list(client.query(query).result())[0]; print(row.days)" 2>/dev/null)
    
    if [ -z "$CURRENT_DAYS" ]; then
        echo "⚠️  Could not query BigQuery, retrying..."
        sleep 60
        continue
    fi
    
    PERCENTAGE=$(echo "scale=1; $CURRENT_DAYS * 100 / $TARGET_DAYS" | bc)
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "[$TIMESTAMP] Progress: $CURRENT_DAYS / $TARGET_DAYS days ($PERCENTAGE%)"
    
    # Check if complete (allowing for small variance)
    if [ "$CURRENT_DAYS" -ge 1400 ]; then
        echo ""
        echo "════════════════════════════════════════════════════════════════"
        echo "  ✅ INGESTION COMPLETE! ($CURRENT_DAYS days)"
        echo "════════════════════════════════════════════════════════════════"
        echo ""
        echo "🚀 Starting comprehensive analysis of ALL BMUs..."
        echo ""
        
        # Run comprehensive analysis
        python3 /home/george/GB-Power-Market-JJ/analyze_all_bm_comprehensive.py
        
        if [ $? -eq 0 ]; then
            echo ""
            echo "════════════════════════════════════════════════════════════════"
            echo "  ✅ ALL ANALYSIS COMPLETE!"
            echo "════════════════════════════════════════════════════════════════"
            echo ""
            echo "📊 Check Google Sheets: BM Revenue Analysis - Full History"
            echo "🔗 https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
            echo ""
        else
            echo "⚠️  Analysis failed, check logs"
        fi
        
        break
    fi
    
    sleep $CHECK_INTERVAL
done
