#!/bin/bash

# Check extraction progress on UpCloud server (16 Workers)
echo "=== Extraction Progress Monitor (16 Workers) ==="
echo ""

# SSH into server and check the log
ssh root@94.237.55.15 << 'EOF'

echo "🚀 Server Configuration:"
echo "------------------------"
echo "CPUs: $(nproc)"
echo "RAM: $(free -h | grep Mem | awk '{print $2}')"
echo "Workers: 16"
echo ""

echo "📊 Current Progress:"
echo "-------------------"

# Get the last few lines showing progress
tail -100 /tmp/extraction_16workers.log 2>/dev/null | grep -E "it/s|%\|" | tail -5 || echo "Log file not accessible yet"

echo ""
echo "⚡ Current Rate:"
echo "----------------"
# Extract the latest rate
LATEST_RATE=$(tail -100 /tmp/extraction_16workers.log 2>/dev/null | grep -E "it/s|%\|" | tail -1 | grep -oE '[0-9]+\.[0-9]+it/s' | head -1)
if [ ! -z "$LATEST_RATE" ]; then
    RATE=$(echo $LATEST_RATE | grep -oE '[0-9]+\.[0-9]+')
    DOCS_PER_HOUR=$(echo "scale=0; $RATE * 3600" | bc)
    DOCS_PER_DAY=$(echo "scale=0; $RATE * 86400" | bc)
    echo "Current: $RATE docs/second"
    echo "Hourly: ~$DOCS_PER_HOUR docs/hour"
    echo "Daily: ~$DOCS_PER_DAY docs/day"
else
    echo "Rate data not yet available (still initializing)"
fi

echo ""
echo "💾 Memory & CPU Usage:"
echo "----------------------"
docker stats --no-stream driveindexer

echo ""
echo "⚠️  Recent Errors (last 5):"
echo "---------------------------"
tail -100 /tmp/extraction_16workers.log 2>/dev/null | grep "WARNING\|ERROR" | tail -5

echo ""
echo "📝 Latest Activity:"
echo "-------------------"
tail -3 /tmp/extraction_16workers.log 2>/dev/null

EOF

echo ""
echo "=== End of Report ==="
echo ""
echo "💡 Tip: Run this script periodically to monitor progress"
echo "   Expected completion: ~8-12 hours at 4-6 docs/sec"
