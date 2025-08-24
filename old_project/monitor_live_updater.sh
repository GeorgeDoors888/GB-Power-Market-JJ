#!/bin/bash
# Process monitor for live data updater
PID_FILE=".live_data_updater.pid"
LOG_DIR="logs"
MONITOR_LOG="${LOG_DIR}/updater_monitor.log"

while true; do
    if [ ! -f "$PID_FILE" ]; then
        echo "$(date): PID file not found. Creating new process..." >> "$MONITOR_LOG"
        python live_data_updater.py > "${LOG_DIR}/live_data_updater_$(date +%Y%m%d_%H%M%S).log" 2>&1 &
        NEW_PID=$!
        echo $NEW_PID > "$PID_FILE"
        echo "$(date): Started new process with PID $NEW_PID" >> "$MONITOR_LOG"
    else
        PID=$(cat "$PID_FILE")
        if ! ps -p $PID > /dev/null; then
            echo "$(date): Process with PID $PID has died. Restarting..." >> "$MONITOR_LOG"
            python live_data_updater.py > "${LOG_DIR}/live_data_updater_$(date +%Y%m%d_%H%M%S).log" 2>&1 &
            NEW_PID=$!
            echo $NEW_PID > "$PID_FILE"
            echo "$(date): Restarted process with PID $NEW_PID" >> "$MONITOR_LOG"
        fi
    fi
    sleep 60
done
