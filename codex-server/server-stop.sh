#!/bin/bash
# Stop Codex server
cd "$(dirname "$0")"

if [ -f server.pid ]; then
    PID=$(cat server.pid)
    if kill -0 $PID 2>/dev/null; then
        # Get uptime before killing
        UPTIME=$(ps -p $PID -o etime= | tr -d ' ')
        kill $PID
        rm server.pid
        echo "✅ Codex server stopped"
        echo "   Uptime: $UPTIME"
        echo "   💰 Cost: $0 (local server)"
    else
        echo "❌ Server not running (stale PID)"
        rm server.pid
    fi
else
    echo "❌ No server.pid found"
    echo "   Checking for running processes..."
    if pgrep -f codex_server.py > /dev/null; then
        echo "   Found running server, stopping all..."
        pkill -f codex_server.py
        echo "✅ Stopped"
    else
        echo "   No server running"
    fi
fi
