#!/bin/bash
# Monitor the continuous extraction progress

echo "🔄 CONTINUOUS EXTRACTION MONITOR"
echo "======================================================================"

# Check if process is running
PID_FILE="/tmp/continuous_extract.pid"
if ssh root@94.237.55.15 "docker exec driveindexer test -f $PID_FILE" 2>/dev/null; then
    PID=$(ssh root@94.237.55.15 "docker exec driveindexer cat $PID_FILE")
    echo "✅ Process running (PID: $PID)"
else
    echo "❌ Process not running"
fi

echo ""
echo "======================================================================"
echo "📊 CURRENT DATABASE STATUS"
echo "======================================================================"
ssh root@94.237.55.15 'docker exec driveindexer python /tmp/check_extraction_status.py'

echo ""
echo "======================================================================"
echo "📋 RECENT PROGRESS LOG"
echo "======================================================================"
ssh root@94.237.55.15 'docker exec driveindexer tail -30 /tmp/extraction_progress.log 2>/dev/null || echo "No progress log yet"'

echo ""
echo "======================================================================"
echo "📈 SESSION STATS"
echo "======================================================================"
SUCCESSES=$(ssh root@94.237.55.15 'docker exec driveindexer bash -c "tail -n +2 /tmp/extraction_success_continuous.log 2>/dev/null | wc -l"' 2>/dev/null || echo "0")
ERRORS=$(ssh root@94.237.55.15 'docker exec driveindexer bash -c "tail -n +2 /tmp/extraction_errors_continuous.log 2>/dev/null | wc -l"' 2>/dev/null || echo "0")
echo "✅ This session - Successful: $SUCCESSES"
echo "❌ This session - Errors: $ERRORS"

echo ""
echo "======================================================================"
echo "💡 This extraction will run continuously until all documents are done"
echo "   Monitor: ./monitor_continuous.sh"
echo "   Stop: ssh root@94.237.55.15 'docker exec driveindexer python -c \"import os; os.kill(\$(cat /tmp/continuous_extract.pid), 15)\"'"
echo "======================================================================"
