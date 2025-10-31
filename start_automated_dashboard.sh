#!/bin/bash

# Start Automated IRIS Dashboard
# This script starts the dashboard updater in the background

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

PID_FILE="automated_dashboard.pid"
LOG_FILE="automated_dashboard.log"

echo "🚀 Starting Automated IRIS Dashboard"
echo "====================================="
echo ""

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  Dashboard already running with PID: $OLD_PID"
        echo ""
        echo "To stop it, run:"
        echo "  kill $OLD_PID"
        exit 1
    else
        echo "🧹 Cleaning up stale PID file"
        rm "$PID_FILE"
    fi
fi

# Check service account file
if [ ! -f "jibber_jabber_key.json" ]; then
    echo "❌ Error: jibber_jabber_key.json not found"
    echo "   Please ensure your Google service account key is present"
    exit 1
fi

# Start dashboard in background
echo "📊 Starting dashboard updater (updates every 5 minutes)..."
nohup ./.venv/bin/python automated_iris_dashboard.py --loop > "$LOG_FILE" 2>&1 &
NEW_PID=$!

# Save PID
echo "$NEW_PID" > "$PID_FILE"

echo "✅ Dashboard started with PID: $NEW_PID"
echo ""
echo "📋 Commands:"
echo "  View logs:      tail -f $LOG_FILE"
echo "  Check status:   ps aux | grep $NEW_PID"
echo "  Stop dashboard: kill $NEW_PID"
echo ""
echo "🌐 Your Google Sheet will be created/updated automatically"
echo "   Check the log for the spreadsheet URL"
echo ""
echo "Sleeping 3 seconds then showing initial log..."
sleep 3
echo ""
echo "📊 Initial Log Output:"
echo "====================="
tail -20 "$LOG_FILE"
