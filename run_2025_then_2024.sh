#!/bin/bash
#
# Wait for the current 2025 ingestion to complete, then automatically start 2024
#

CURRENT_PID=40652
LOG_2025="jan_aug_ingest_clean.log"
LOG_2024="year_2024_ingest.log"

echo "=================================================="
echo "Automatic 2024 Ingestion Starter"
echo "=================================================="
echo "Waiting for 2025 ingestion (PID: $CURRENT_PID) to complete..."
echo ""

# Wait for the 2025 process to finish
while kill -0 $CURRENT_PID 2>/dev/null; do
    sleep 60  # Check every minute
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Still waiting for 2025 to finish..."
done

echo ""
echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ 2025 ingestion completed!"
echo "=================================================="
echo "Starting 2024 ingestion..."
echo "=================================================="
echo ""

# Start 2024 ingestion
cd "/Users/georgemajor/GB Power Market JJ"
nohup .venv/bin/python ingest_elexon_fixed.py --start 2024-01-01 --end 2024-12-31 > "$LOG_2024" 2>&1 &

NEW_PID=$!
echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ 2024 ingestion started!"
echo "Process ID: $NEW_PID"
echo "Log file: $LOG_2024"
echo ""
echo "To monitor: tail -f $LOG_2024"
echo "=================================================="
