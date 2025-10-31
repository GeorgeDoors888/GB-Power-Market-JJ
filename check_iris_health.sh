#!/bin/bash
# IRIS Integration Health Check
# Run: ./check_iris_health.sh

echo "═══════════════════════════════════════════════════════"
echo "🔍 IRIS Integration Health Check"
echo "Time: $(date)"
echo "═══════════════════════════════════════════════════════"
echo ""

# Check processes
echo "📊 Services Status:"
CLIENT_PID=$(cat iris-clients/python/iris_client.pid 2>/dev/null || echo "unknown")
PROC_PID=$(cat iris_processor.pid 2>/dev/null || echo "unknown")

if ps -p $CLIENT_PID > /dev/null 2>&1; then
    echo "  ✅ IRIS Client: Running (PID: $CLIENT_PID)"
else
    echo "  ❌ IRIS Client: NOT RUNNING"
fi

if ps -p $PROC_PID > /dev/null 2>&1; then
    echo "  ✅ IRIS Processor: Running (PID: $PROC_PID)"
else
    echo "  ❌ IRIS Processor: NOT RUNNING"
fi

echo ""

# Check file backlog
echo "📁 File Backlog:"
JSON_COUNT=$(find iris-clients/python/iris_data -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
echo "  Pending JSON files: $JSON_COUNT"

if [ "$JSON_COUNT" -gt 1000 ]; then
    echo "  ⚠️  WARNING: High backlog (>1000 files)"
elif [ "$JSON_COUNT" -gt 100 ]; then
    echo "  ⚠️  CAUTION: Growing backlog (>100 files)"
else
    echo "  ✅ Backlog normal"
fi

echo ""

# Check BigQuery data
echo "📊 BigQuery Data (BOALF):"
bq query --project_id=inner-cinema-476211-u9 --use_legacy_sql=false --format=csv \
  "SELECT 
     COUNT(*) as records,
     TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), MAX(ingested_utc), MINUTE) as lag_minutes
   FROM uk_energy_prod.bmrs_boalf_iris" 2>/dev/null | tail -1 | \
   awk -F',' '{printf "  Records: %s\n  Data lag: %s minutes\n", $1, $2}'

echo ""

# Recent processor activity
echo "📝 Recent Processor Activity (last 5 lines):"
tail -5 iris_processor.log 2>/dev/null | sed 's/^/  /'

echo ""
echo "═══════════════════════════════════════════════════════"
