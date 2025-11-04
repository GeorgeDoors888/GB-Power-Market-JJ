#!/bin/bash
# Monitor the working extraction progress

echo "📊 EXTRACTION PROGRESS"
echo "======================================================================"

# Check if process is running
if ssh root@94.237.55.15 'docker exec driveindexer test -f /tmp/working_extract.pid && cat /tmp/working_extract.pid' 2>/dev/null; then
    PID=$(ssh root@94.237.55.15 'docker exec driveindexer cat /tmp/working_extract.pid')
    echo "✅ Process running (PID: $PID)"
else
    echo "❌ Process not running"
fi

echo ""
echo "📋 Recent log output:"
echo "----------------------------------------------------------------------"
ssh root@94.237.55.15 'docker exec driveindexer tail -20 /tmp/working_extraction.log'

echo ""
echo "----------------------------------------------------------------------"
echo "📊 Stats:"
echo "----------------------------------------------------------------------"
SUCCESSES=$(ssh root@94.237.55.15 'docker exec driveindexer bash -c "wc -l < /tmp/extraction_success_working.log"')
ERRORS=$(ssh root@94.237.55.15 'docker exec driveindexer bash -c "wc -l < /tmp/extraction_errors_working.log"')
echo "✅ Successful: $((SUCCESSES - 1))"  # Subtract header
echo "❌ Errors: $((ERRORS - 1))"  # Subtract header

echo ""
echo "----------------------------------------------------------------------"
echo "📊 Database status:"
echo "----------------------------------------------------------------------"
ssh root@94.237.55.15 'docker exec driveindexer python /tmp/check_extraction_status.py' | grep -E "Documents|chunks|Progress"

echo ""
echo "======================================================================"
echo "💡 Run this script again to check progress"
echo "   Command: ./monitor_working.sh"
