#!/bin/bash
# Live Backfill Monitor - Updates every 10 seconds

while true; do
  clear
  date
  echo ""
  ./monitor_backfill.sh
  
  # Check if process still running
  if ! ps aux | grep -q "[b]ackfill_boalf_historical.sh"; then
    echo ""
    echo "🏁 Backfill process has COMPLETED!"
    echo ""
    echo "Final summary:"
    tail -20 /home/george/GB-Power-Market-JJ/logs/backfill_live.log | grep -E "Total months|Processed|Failed|Runtime"
    break
  fi
  
  echo ""
  echo "Press Ctrl+C to stop monitoring"
  sleep 10
done
