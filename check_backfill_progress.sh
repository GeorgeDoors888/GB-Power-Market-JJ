#!/bin/bash
# Monitor backfill progress

echo "🔍 BACKFILL PROGRESS MONITOR"
echo "================================"
echo ""

# Check if process is running
if ps aux | grep -q "[b]ackfill_gust_pressure_21_farms.py"; then
    echo "✅ Process is RUNNING"
    echo ""
else
    echo "❌ Process is NOT running"
    echo ""
fi

# Show last 30 lines of log
echo "📋 Recent log output:"
echo "================================"
tail -30 /tmp/backfill_final.log 2>/dev/null || echo "Log file not found"
echo ""

# Count farms downloaded
if [ -f /tmp/backfill_final.log ]; then
    FARMS=$(grep -c "Retrieved.*hours of data" /tmp/backfill_final.log)
    echo "📊 Farms completed: $FARMS / 21"
    echo "⏱️  Estimated time remaining: $((21 - FARMS)) minutes"
fi
