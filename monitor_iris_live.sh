#!/bin/bash

echo "🔴 LIVE: IRIS Upload Monitor - Started at $(date)"
echo "=================================================="
echo ""

while true; do
    clear
    echo "🔴 LIVE: IRIS to BigQuery Upload Status"
    echo "Updated: $(date '+%H:%M:%S')"
    echo "=================================================="
    echo ""
    
    # Get BigQuery counts
    echo "📊 BIGQUERY ROW COUNTS:"
    bq query --use_legacy_sql=false --format=csv "
    SELECT 
      'INDO' as dataset,
      COUNT(*) as rows,
      MAX(ingested_utc) as last_update
    FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_indo_iris\`
    UNION ALL
    SELECT 
      'INDGEN' as dataset,
      COUNT(*) as rows,
      MAX(ingested_utc) as last_update
    FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen_iris\`
    UNION ALL
    SELECT 
      'INDDEM' as dataset,
      COUNT(*) as rows,
      MAX(ingested_utc) as last_update
    FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_inddem_iris\`
    ORDER BY dataset
    " 2>/dev/null | column -t -s,
    
    echo ""
    echo "📁 FILES REMAINING ON SERVER:"
    ssh root@94.237.55.234 'for dir in INDO INDGEN INDDEM; do echo -n "$dir: "; find /opt/iris-pipeline/iris-clients/python/iris_data/$dir -name "*.json" 2>/dev/null | wc -l; done' 2>/dev/null
    
    echo ""
    echo "⚙️  PROCESS STATUS:"
    ssh root@94.237.55.234 'ps aux | grep "[p]ython3 iris_to_bigquery" | head -1 | awk "{print \"PID: \"\$2\" | CPU: \"\$3\"% | MEM: \"\$4\"% | RSS: \"\$6\"KB\"}"' 2>/dev/null || echo "❌ Process not running"
    
    echo ""
    echo "📝 RECENT ACTIVITY (Last 3 operations):"
    ssh root@94.237.55.234 'tail -100 /opt/iris-pipeline/logs/iris_uploader.log | grep "✅ Inserted" | tail -3' 2>/dev/null
    
    echo ""
    echo "⏱️  Next update in 30 seconds... (Ctrl+C to stop)"
    sleep 30
done
