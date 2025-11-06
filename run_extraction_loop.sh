#!/bin/bash
# Continuous extraction loop - restarts script if it stops
# This handles the memory leak by automatically restarting

LOG_FILE="/tmp/extraction_loop.log"
EXTRACTION_SCRIPT="/tmp/run_ce.py"
MAX_RESTARTS=1000  # Stop after 1000 restarts (safety limit)

echo "$(date): 🚀 Starting extraction loop" | tee -a "$LOG_FILE"
echo "$(date):    Will restart script automatically if it stops" | tee -a "$LOG_FILE"
echo "$(date):    Max restarts: $MAX_RESTARTS" | tee -a "$LOG_FILE"

restart_count=0

while [ $restart_count -lt $MAX_RESTARTS ]; do
    restart_count=$((restart_count + 1))
    echo "$(date): 📦 Starting extraction (restart #$restart_count)" | tee -a "$LOG_FILE"
    
    # Run the extraction script
    cd /app
    python3 "$EXTRACTION_SCRIPT" 2>&1 | tee -a /tmp/extraction.out
    
    exit_code=$?
    echo "$(date): ⚠️  Extraction stopped with exit code $exit_code" | tee -a "$LOG_FILE"
    
    # If exit code is 0, it completed successfully
    if [ $exit_code -eq 0 ]; then
        echo "$(date): ✅ Extraction completed successfully!" | tee -a "$LOG_FILE"
        break
    fi
    
    # Wait 5 seconds before restarting
    echo "$(date): ⏳ Waiting 5 seconds before restart..." | tee -a "$LOG_FILE"
    sleep 5
done

echo "$(date): 🏁 Extraction loop finished after $restart_count restarts" | tee -a "$LOG_FILE"
