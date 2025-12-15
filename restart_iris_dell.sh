#!/bin/bash
# Restart IRIS Pipeline on Dell Server (192.168.1.50)
# Run this script ON the Dell server to restart IRIS client and uploader

echo "=========================================="
echo "IRIS Pipeline Restart Script"
echo "Server: $(hostname)"
echo "Date: $(date)"
echo "=========================================="
echo ""

# Check if we're on the right machine
if [ "$(hostname)" != "localhost.localdomain" ] && [ "$(hostname)" != "dell" ]; then
    echo "⚠️  WARNING: This script should run on the Dell server (192.168.1.50)"
    echo "Current hostname: $(hostname)"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Find IRIS installation directory
if [ -d "/home/george/GB-Power-Data/iris_windows_deployment" ]; then
    IRIS_DIR="/home/george/GB-Power-Data/iris_windows_deployment"
elif [ -d "/opt/iris-pipeline" ]; then
    IRIS_DIR="/opt/iris-pipeline"
else
    echo "❌ ERROR: Cannot find IRIS installation directory"
    echo "Checked:"
    echo "  - /home/george/GB-Power-Data/iris_windows_deployment"
    echo "  - /opt/iris-pipeline"
    exit 1
fi

echo "📁 IRIS Directory: $IRIS_DIR"
echo ""

# Check current processes
echo "🔍 Checking current IRIS processes..."
CLIENT_PID=$(ps aux | grep "client.py" | grep -v grep | awk '{print $2}')
UPLOADER_PID=$(ps aux | grep "iris_to_bigquery" | grep -v grep | awk '{print $2}')

if [ -n "$CLIENT_PID" ]; then
    echo "  ✅ IRIS Client running (PID: $CLIENT_PID)"
else
    echo "  ❌ IRIS Client NOT running"
fi

if [ -n "$UPLOADER_PID" ]; then
    echo "  ✅ IRIS Uploader running (PID: $UPLOADER_PID)"
else
    echo "  ❌ IRIS Uploader NOT running"
fi
echo ""

# Kill existing processes
if [ -n "$CLIENT_PID" ] || [ -n "$UPLOADER_PID" ]; then
    echo "🛑 Stopping existing processes..."
    [ -n "$CLIENT_PID" ] && kill $CLIENT_PID && echo "  Killed client PID $CLIENT_PID"
    [ -n "$UPLOADER_PID" ] && kill $UPLOADER_PID && echo "  Killed uploader PID $UPLOADER_PID"
    sleep 2
fi

# Check for data directory
if [ -d "$IRIS_DIR/data" ]; then
    DATA_DIR="$IRIS_DIR/data"
elif [ -d "$IRIS_DIR/iris_data" ]; then
    DATA_DIR="$IRIS_DIR/iris_data"
else
    echo "⚠️  Warning: Cannot find data directory, creating it..."
    DATA_DIR="$IRIS_DIR/data"
    mkdir -p "$DATA_DIR"
fi

echo "📊 Data Directory: $DATA_DIR"
echo ""

# Check Python
PYTHON=$(which python3)
if [ -z "$PYTHON" ]; then
    echo "❌ ERROR: python3 not found"
    exit 1
fi
echo "🐍 Python: $PYTHON"
echo ""

# Start IRIS Client
echo "🚀 Starting IRIS Client..."
cd "$IRIS_DIR/scripts" || cd "$IRIS_DIR"

if [ -f "client.py" ]; then
    nohup $PYTHON client.py > /dev/null 2>&1 &
    CLIENT_NEW_PID=$!
    sleep 2
    if ps -p $CLIENT_NEW_PID > /dev/null; then
        echo "  ✅ IRIS Client started (PID: $CLIENT_NEW_PID)"
    else
        echo "  ❌ IRIS Client failed to start"
        echo "  Check logs at: $IRIS_DIR/logs/client.log"
    fi
else
    echo "  ❌ client.py not found in $IRIS_DIR/scripts or $IRIS_DIR"
fi

# Start IRIS Uploader
echo "🚀 Starting IRIS Uploader..."

if [ -f "iris_to_bigquery_unified.py" ]; then
    export IRIS_DATA_DIR="$DATA_DIR"
    nohup $PYTHON iris_to_bigquery_unified.py > ../logs/uploader.log 2>&1 &
    UPLOADER_NEW_PID=$!
    sleep 2
    if ps -p $UPLOADER_NEW_PID > /dev/null; then
        echo "  ✅ IRIS Uploader started (PID: $UPLOADER_NEW_PID)"
    else
        echo "  ❌ IRIS Uploader failed to start"
        echo "  Check logs at: $IRIS_DIR/logs/uploader.log"
    fi
else
    echo "  ❌ iris_to_bigquery_unified.py not found"
fi

echo ""
echo "=========================================="
echo "✅ IRIS Pipeline Restart Complete"
echo "=========================================="
echo ""
echo "Monitor logs:"
echo "  Client:   tail -f $IRIS_DIR/logs/client.log"
echo "  Uploader: tail -f $IRIS_DIR/logs/uploader.log"
echo ""
echo "Check processes:"
echo "  ps aux | grep -E '(client.py|iris_to_bigquery)' | grep -v grep"
echo ""
