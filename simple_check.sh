#!/bin/bash
# Simple extraction monitor
echo ""
echo "🔍 Checking extraction status..."
echo ""

# Check if process is running
ssh root@94.237.55.15 'docker exec driveindexer cat /tmp/extraction_parallel.log | tail -1'

echo ""
echo "📊 Log file size:"
ssh root@94.237.55.15 'docker exec driveindexer ls -lh /tmp/extraction_parallel.log'

echo ""
echo "💡 To watch live: ssh root@94.237.55.15 'docker exec driveindexer tail -f /tmp/extraction_parallel.log'"
echo ""
