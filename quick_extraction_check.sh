#!/bin/bash
# Quick progress check

echo "⚡ EXTRACTION PROGRESS"
echo "======================================================================"

# Check if running
if ssh root@94.237.55.15 'docker exec driveindexer test -f /tmp/optimized_extract.pid' 2>/dev/null; then
    PID=$(ssh root@94.237.55.15 'docker exec driveindexer cat /tmp/optimized_extract.pid')
    echo "✅ Process running (PID: $PID)"
else
    echo "❌ Process not running"
fi

# Show last few lines
echo ""
echo "📋 Recent activity:"
ssh root@94.237.55.15 'docker exec driveindexer tail -20 /tmp/optimized_extraction.log' 2>/dev/null | tail -10

# Check database
echo ""
echo "📊 Database status:"
ssh root@94.237.55.15 'docker exec driveindexer python /tmp/check_extraction_status.py' 2>/dev/null | grep -E "Processed|Remaining|Progress|chunks"

echo ""
echo "======================================================================"
