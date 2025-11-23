#!/bin/bash
# 
# Automatic Map Update Cron Job
# ==============================
# This script runs the map updater and logs output
#

# Change to script directory
cd "/Users/georgemajor/GB Power Market JJ" || exit 1

# Create logs directory if it doesn't exist
mkdir -p logs

# Log file with date
LOG_FILE="logs/map_updates_$(date +%Y%m%d).log"

# Run updater
echo "=================================================" >> "$LOG_FILE"
echo "Map update started: $(date)" >> "$LOG_FILE"
echo "=================================================" >> "$LOG_FILE"

/usr/local/bin/python3 auto_update_maps.py >> "$LOG_FILE" 2>&1

EXIT_CODE=$?

echo "Exit code: $EXIT_CODE" >> "$LOG_FILE"
echo "Completed: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Keep only last 7 days of logs
find logs/ -name "map_updates_*.log" -mtime +7 -delete

exit $EXIT_CODE
