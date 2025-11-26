#!/bin/bash
# Start Battery Revenue Webhook Server with ngrok tunnel

echo "🔋 Battery Revenue Analysis - Webhook Server Launcher"
echo "=" 
echo ""

# Change to script directory
cd "$(dirname "$0")"

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "⚠️  Flask not installed. Installing..."
    pip3 install --user flask flask-cors
fi

# Check if ngrok is installed
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok not found!"
    echo "Install with: brew install ngrok"
    echo "Then run: ngrok config add-authtoken YOUR_TOKEN"
    exit 1
fi

echo "✅ Prerequisites satisfied"
echo ""

# Start webhook server in background
echo "🚀 Starting webhook server on port 5002..."
python3 battery_revenue_webhook.py > webhook.log 2>&1 &
WEBHOOK_PID=$!
echo "   PID: $WEBHOOK_PID"

# Wait for server to start
sleep 2

# Start ngrok tunnel
echo "🌐 Starting ngrok tunnel..."
ngrok http 5002 > /dev/null &
NGROK_PID=$!
echo "   PID: $NGROK_PID"

# Wait for ngrok to start
sleep 3

# Get ngrok URL
NGROK_URL=$(curl -s http://localhost:4040/api/tunnels | grep -o '"public_url":"https://[^"]*' | grep -o 'https://[^"]*' | head -1)

if [ -z "$NGROK_URL" ]; then
    echo "❌ Failed to get ngrok URL"
    kill $WEBHOOK_PID $NGROK_PID 2>/dev/null
    exit 1
fi

echo ""
echo "=" 
echo "✅ WEBHOOK SERVER READY!"
echo "=" 
echo ""
echo "📍 Webhook URL: $NGROK_URL"
echo ""
echo "🔧 Update Apps Script CONFIG.WEBHOOK_URL to:"
echo "   '$NGROK_URL'"
echo ""
echo "🧪 Test endpoints:"
echo "   curl $NGROK_URL/health"
echo "   curl -X POST $NGROK_URL/refresh-battery-revenue"
echo ""
echo "📊 Ngrok dashboard: http://localhost:4040"
echo "📝 Webhook logs: tail -f webhook.log"
echo ""
echo "🛑 To stop:"
echo "   kill $WEBHOOK_PID $NGROK_PID"
echo ""
echo "=" 

# Save PIDs to file for easy cleanup
echo "$WEBHOOK_PID $NGROK_PID" > .webhook_pids

# Keep script running
echo "Press Ctrl+C to stop all services..."
trap "kill $WEBHOOK_PID $NGROK_PID 2>/dev/null; rm -f .webhook_pids; echo ''; echo '🛑 Services stopped'; exit" INT TERM

# Wait for either process to exit
wait
