#!/bin/bash
# Live progress monitor - checks BigQuery every 30 seconds
# Press Ctrl+C to stop

echo ""
echo "================================================================================"
echo "📊 LIVE EXTRACTION MONITOR"
echo "================================================================================"
echo ""
echo "Checking BigQuery chunks table every 30 seconds..."
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
    # Get current timestamp
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Query BigQuery for progress (using local credentials)
    RESULT=$(python3 << 'EOF'
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'gridsmart_service_account.json'
try:
    from google.cloud import bigquery
    c = bigquery.Client(project='inner-cinema-476211-u9')
    r = list(c.query('SELECT COUNT(*) cnt, COUNT(DISTINCT doc_id) docs FROM `inner-cinema-476211-u9.uk_energy_insights.chunks`').result())[0]
    print(f"{r.docs:,}|{r.cnt:,}")
except Exception as e:
    print(f"ERROR|{e}")
EOF
)
    
    # Parse result
    DOCS=$(echo $RESULT | cut -d'|' -f1)
    CHUNKS=$(echo $RESULT | cut -d'|' -f2)
    
    if [ "$DOCS" = "ERROR" ]; then
        echo "[$TIMESTAMP] ❌ Error querying BigQuery: $CHUNKS"
    else
        # Calculate progress
        REMAINING=$((140434 - DOCS))
        PROGRESS=$(python3 -c "print(f'{($DOCS/140434*100):.2f}')" 2>/dev/null || echo "0")
        
        echo "[$TIMESTAMP] 📄 Docs: $DOCS / 140,434 | 📊 Progress: ${PROGRESS}% | 📦 Chunks: $CHUNKS | ⏳ Remaining: $REMAINING"
    fi
    
    # Wait 30 seconds
    sleep 30
done
