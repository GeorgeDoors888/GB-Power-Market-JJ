#!/bin/bash
# IMMEDIATE FIX - Stop Foreground IRIS Processes NOW

echo "Stopping foreground IRIS processes..."

# Kill the foreground client
pkill -9 -f "python3 client.py"
sleep 2

# Kill any uploader not properly backgrounded
pkill -9 -f "python3 iris_to_bigquery" || true

echo "✅ Foreground processes killed"
echo ""
echo "Starting in background with proper logging..."

# Start client in background
cd /opt/iris-pipeline/scripts
export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json
nohup python3 client.py >> /opt/iris-pipeline/logs/iris_client_$(date +%Y%m%d).log 2>&1 &
echo "✅ IRIS client started (PID: $!)"

sleep 3

# Start uploader in background
nohup python3 iris_to_bigquery_unified.py --continuous >> /opt/iris-pipeline/logs/iris_uploader_$(date +%Y%m%d).log 2>&1 &
echo "✅ IRIS uploader started (PID: $!)"

echo ""
echo "=========================================="
echo "✅ DONE - Your terminal is now clean!"
echo "=========================================="
echo ""
echo "View logs:"
echo "  tail -f /opt/iris-pipeline/logs/iris_client_$(date +%Y%m%d).log"
echo "  tail -f /opt/iris-pipeline/logs/iris_uploader_$(date +%Y%m%d).log"
echo ""
echo "Check processes:"
echo "  ps aux | grep python3"
echo ""
