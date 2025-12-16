#!/bin/bash
# Monitor BOALF Historical Backfill Progress

LOG_FILE="/home/george/GB-Power-Market-JJ/logs/backfill_live.log"

if [[ ! -f "$LOG_FILE" ]]; then
  echo "❌ Backfill log not found: $LOG_FILE"
  exit 1
fi

echo "=================================================="
echo "BOALF Historical Backfill Monitor"
echo "=================================================="
echo ""

# Check if process is running
if ps aux | grep -q "[b]ackfill_boalf_historical.sh"; then
  echo "✅ Backfill process is RUNNING"
else
  echo "⚠️  Backfill process is NOT running"
fi

echo ""
echo "Latest Progress:"
echo "--------------------------------------------------"
tail -20 "$LOG_FILE" | grep -E "Processing:|SUCCESS|FAILED|%]" | tail -5

echo ""
echo "Statistics:"
echo "--------------------------------------------------"

# Count completed months
completed=$(grep -c "✅ SUCCESS" "$LOG_FILE" 2>/dev/null || echo "0")
failed=$(grep -c "❌ FAILED" "$LOG_FILE" 2>/dev/null || echo "0")
total=48

echo "Completed: $completed/$total"
echo "Failed: $failed"

if [[ $completed -gt 0 ]]; then
  pct=$((100 * completed / total))
  echo "Progress: ${pct}%"
fi

echo ""
echo "To follow live: tail -f $LOG_FILE"
echo "=================================================="
