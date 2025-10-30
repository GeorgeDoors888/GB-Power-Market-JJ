#!/bin/bash
# Quick progress check
echo "🔍 BMRS Fix Progress Check"
echo "========================="
echo ""

# Check if processes are running
if ps aux | grep -q "fix_failed_datasets.py" | grep -v grep; then
    echo "✅ Fix script: RUNNING"
else
    echo "❌ Fix script: STOPPED"
fi

if ps aux | grep -q "ingest_elexon_fixed.py" | grep -v grep; then
    echo "✅ Ingestion: RUNNING"
else
    echo "❌ Ingestion: STOPPED"
fi

echo ""

# Show latest progress from log
LOG_FILE=$(ls -t fix_failed_datasets_*.log 2>/dev/null | head -1)
if [ -n "$LOG_FILE" ]; then
    echo "📊 Latest Progress:"
    echo "=================="

    # Count successes
    SUCCESS_COUNT=$(grep -c "✅.*SUCCESS" "$LOG_FILE" 2>/dev/null || echo "0")
    echo "✅ Completed: $SUCCESS_COUNT/30"

    # Show current dataset
    CURRENT=$(grep "📊 Progress:" "$LOG_FILE" | tail -1 | cut -d'-' -f2 | xargs)
    if [ -n "$CURRENT" ]; then
        echo "🔄 Current: $CURRENT"
    fi

    # Show last few log entries
    echo ""
    echo "📝 Recent Activity:"
    tail -5 "$LOG_FILE" | grep -E "(✅|🔄|📊)" | tail -3
else
    echo "❌ No log file found"
fi

echo ""
echo "⏰ $(date)"
