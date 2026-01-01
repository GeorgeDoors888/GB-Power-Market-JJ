#!/bin/bash

# Start ngrok tunnel for search API
# Run after: ngrok config add-authtoken YOUR_TOKEN

echo "🌐 Starting ngrok tunnel to port 5002..."

# Kill any existing ngrok process
pkill ngrok 2>/dev/null

# Start ngrok in background
nohup ngrok http 5002 --log=stdout > logs/ngrok.log 2>&1 &
NGROK_PID=$!

echo "✅ ngrok started (PID: $NGROK_PID)"
echo "⏳ Waiting 5 seconds for tunnel to establish..."
sleep 5

# Get public URL from ngrok API
PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('tunnels'):
        print(data['tunnels'][0]['public_url'])
    else:
        print('ERROR: No tunnels found')
        sys.exit(1)
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
")

if [[ $PUBLIC_URL == ERROR* ]]; then
    echo "❌ Failed to get public URL"
    echo "Check logs/ngrok.log for details"
    exit 1
fi

echo ""
echo "✅ ngrok tunnel active!"
echo "🌐 Public URL: $PUBLIC_URL"
echo ""
echo "📝 Next step: Update Apps Script API_ENDPOINT to:"
echo "   $PUBLIC_URL/search"
echo ""
echo "💡 To stop: pkill ngrok"
