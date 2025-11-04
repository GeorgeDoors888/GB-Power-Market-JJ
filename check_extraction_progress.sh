#!/bin/bash
# Extraction Progress Monitor
# Run this anytime to see current progress

echo ""
echo "================================================================================"
echo "📊 EXTRACTION PROGRESS MONITOR"
echo "================================================================================"
echo ""

# Get last line of log (shows current progress)
echo "🔍 Fetching current status..."
LAST_LINE=$(ssh root@94.237.55.15 'docker exec driveindexer tail -1 /tmp/extraction_8workers.log 2>/dev/null')

if [ -z "$LAST_LINE" ]; then
    echo "❌ Could not fetch log. Extraction might not be running."
    exit 1
fi

echo "📄 Latest log entry:"
echo "$LAST_LINE"
echo ""

# Try to extract progress numbers
if echo "$LAST_LINE" | grep -q "%"; then
    PROGRESS=$(echo "$LAST_LINE" | grep -oE '[0-9]+%' | head -1)
    DOCS_DONE=$(echo "$LAST_LINE" | grep -oE '[0-9]+/[0-9]+' | cut -d'/' -f1)
    DOCS_TOTAL=$(echo "$LAST_LINE" | grep -oE '[0-9]+/[0-9]+' | cut -d'/' -f2)
    RATE=$(echo "$LAST_LINE" | grep -oE '[0-9]+\.[0-9]+it/s' | sed 's/it\/s//')
    
    if [ ! -z "$PROGRESS" ]; then
        echo "✅ Progress: $PROGRESS"
    fi
    
    if [ ! -z "$DOCS_DONE" ] && [ ! -z "$DOCS_TOTAL" ]; then
        REMAINING=$((DOCS_TOTAL - DOCS_DONE))
        echo "📄 Documents: $DOCS_DONE / $DOCS_TOTAL (Remaining: $REMAINING)"
    fi
    
    if [ ! -z "$RATE" ]; then
        RATE_PER_HOUR=$(python3 -c "print(f'{float('$RATE') * 3600:.0f}')" 2>/dev/null || echo "N/A")
        echo "⚡ Current rate: $RATE docs/sec ($RATE_PER_HOUR per hour)"
        
        if [ ! -z "$REMAINING" ] && [ "$RATE" != "0" ]; then
            HOURS_LEFT=$(python3 -c "print(f'{$REMAINING / (float('$RATE') * 3600):.1f}')" 2>/dev/null || echo "N/A")
            echo "⏳ Estimated time remaining: $HOURS_LEFT hours"
        fi
    fi
fi

echo ""
echo "💾 Memory usage:"
ssh root@94.237.55.15 'docker stats driveindexer --no-stream --format "   CPU: {{.CPUPerc}}  |  Memory: {{.MemUsage}} ({{.MemPerc}})"'

echo ""
echo "================================================================================"
echo "💡 To watch live: ssh root@94.237.55.15 'docker exec driveindexer tail -f /tmp/extraction_8workers.log'"
echo "================================================================================"
echo ""
