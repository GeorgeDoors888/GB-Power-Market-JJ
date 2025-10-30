#!/bin/bash

# Auto-start 2023 ingestion after 2024 completes
# This script monitors the 2024 process and starts 2023 when done

PID=5637  # Current 2024 ingestion process

echo "🔍 Monitoring 2024 ingestion (PID: $PID)"
echo "⏳ Will auto-start 2023 when 2024 completes..."
echo "📅 Started monitoring at $(date '+%I:%M %p')"
echo ""

# Wait for 2024 process to complete
while kill -0 $PID 2>/dev/null; do
    sleep 300  # Check every 5 minutes
done

echo ""
echo "✅ 2024 ingestion completed at $(date '+%I:%M %p')"
echo "🚀 Starting 2023 ingestion..."
echo ""

# Start 2023 ingestion
nohup /Users/georgemajor/GB\ Power\ Market\ JJ/.venv/bin/python \
    ingest_elexon_fixed.py \
    --start 2023-01-01 \
    --end 2023-12-31 \
    > year_2023_ingest.log 2>&1 &

NEW_PID=$!

echo "✅ 2023 ingestion started at $(date '+%I:%M %p')"
echo "📝 Process ID: $NEW_PID"
echo "📄 Log file: year_2023_ingest.log"
echo ""
echo "Monitor with: tail -f year_2023_ingest.log"
echo "Check status: ps aux | grep $NEW_PID"
