#!/bin/bash
# Daily update script - run this every day to get yesterday's data

PYTHON=".venv/bin/python"
SCRIPT="ingest_elexon_fixed.py"

# Get yesterday's date
YESTERDAY=$(date -v-1d +%Y-%m-%d)

echo "======================================================================"
echo "DAILY UPDATE: Loading data for $YESTERDAY"
echo "Start: $(date)"
echo "======================================================================"

# Load yesterday's data for all datasets
$PYTHON $SCRIPT --start "$YESTERDAY" --end "$YESTERDAY" > "daily_update_${YESTERDAY}.log" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Daily update completed successfully at $(date)"
    echo "Check daily_update_${YESTERDAY}.log for details"
else
    echo "❌ Daily update failed - check daily_update_${YESTERDAY}.log"
    exit 1
fi
