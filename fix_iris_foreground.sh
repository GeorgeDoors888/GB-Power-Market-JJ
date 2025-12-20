#!/bin/bash
# Fix IRIS Client - Move to Background with Proper Logging
# Run this script to properly background the IRIS processes

echo "Stopping current foreground IRIS client..."

# Kill the foreground client on pts/18
pkill -f "python3 client.py"

# Wait for it to stop
sleep 2

echo "Restarting IRIS client in background with log file..."

# Start client in background with log redirection
cd /opt/iris-pipeline/scripts
nohup python3 client.py >> /opt/iris-pipeline/logs/iris_client.log 2>&1 &
CLIENT_PID=$!

echo "✅ IRIS client restarted in background (PID: $CLIENT_PID)"
echo "📋 Logs: /opt/iris-pipeline/logs/iris_client.log"
echo ""
echo "To monitor logs:"
echo "  tail -f /opt/iris-pipeline/logs/iris_client.log"
echo ""
echo "To check status:"
echo "  ps aux | grep client.py"
