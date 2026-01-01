#!/bin/bash

# Complete Startup Script for Search Interface
# Starts API server + ngrok tunnel, updates Apps Script

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting Search Interface Services"
echo "======================================"

# Step 1: Check API server
echo ""
echo "📡 Step 1: Checking API Server..."
if ps aux | grep -v grep | grep -q search_api_server; then
    echo "✅ API server already running"
    API_PID=$(ps aux | grep -v grep | grep search_api_server | head -1 | awk '{print $2}')
    echo "   PID: $API_PID"
else
    echo "⚠️  API server not running, starting..."
    ./start_search_api.sh
    sleep 3
fi

# Verify API health
if curl -s http://localhost:5002/health > /dev/null; then
    echo "✅ API server healthy"
else
    echo "❌ API server not responding on port 5002"
    exit 1
fi

# Step 2: Check ngrok authentication
echo ""
echo "🔐 Step 2: Checking ngrok Authentication..."
if [ ! -f ~/.config/ngrok/ngrok.yml ]; then
    echo "❌ ngrok not authenticated!"
    echo ""
    echo "Please run:"
    echo "  ngrok config add-authtoken YOUR_TOKEN"
    echo ""
    echo "Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken"
    exit 1
fi

echo "✅ ngrok authenticated"

# Step 3: Start ngrok tunnel
echo ""
echo "🌐 Step 3: Starting ngrok Tunnel..."

# Kill any existing ngrok
pkill ngrok 2>/dev/null || true
sleep 2

# Start ngrok
nohup ngrok http 5002 --log=stdout > logs/ngrok.log 2>&1 &
NGROK_PID=$!
echo "✅ ngrok started (PID: $NGROK_PID)"

# Wait for tunnel
echo "⏳ Waiting for tunnel to establish..."
sleep 5

# Get public URL
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('tunnels'):
        print(data['tunnels'][0]['public_url'])
    else:
        print('ERROR')
except:
    print('ERROR')
" 2>/dev/null)

if [[ "$PUBLIC_URL" == "ERROR" ]] || [[ -z "$PUBLIC_URL" ]]; then
    echo "❌ Failed to get ngrok public URL"
    echo "Check logs/ngrok.log for details:"
    echo ""
    tail -20 logs/ngrok.log
    exit 1
fi

echo "✅ ngrok tunnel active"
echo "🌐 Public URL: $PUBLIC_URL"

# Step 4: Update Apps Script
echo ""
echo "📝 Step 4: Updating Apps Script endpoint..."
python3 update_apps_script_endpoint.py "$PUBLIC_URL"

# Step 5: Summary
echo ""
echo "======================================"
echo "✅ All Services Started Successfully!"
echo "======================================"
echo ""
echo "📊 Service Status:"
echo "  - API Server: ✅ Running on http://localhost:5002"
echo "  - ngrok Tunnel: ✅ Active at $PUBLIC_URL"
echo "  - Apps Script: ✅ Updated (needs installation)"
echo ""
echo "📋 Next Steps:"
echo "  1. Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
echo "  2. Go to: Extensions > Apps Script"
echo "  3. Replace Code.gs with: search_interface.gs"
echo "  4. Save and refresh spreadsheet"
echo "  5. Click Search button → Should auto-execute! ✨"
echo ""
echo "🔍 Monitor Services:"
echo "  - API logs: tail -f logs/search_api.log"
echo "  - ngrok logs: tail -f logs/ngrok.log"
echo "  - ngrok web UI: http://localhost:4040"
echo ""
echo "🛑 Stop Services:"
echo "  pkill ngrok && pkill -f search_api_server"
echo ""
