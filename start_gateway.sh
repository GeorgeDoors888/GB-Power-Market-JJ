#!/bin/bash
# AI Gateway Startup Script
# Usage: ./start_gateway.sh

echo "🚀 Starting AI Gateway Server..."

# Navigate to project directory
cd "$(dirname "$0")"

# Set environment variables directly
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/inner-cinema-credentials.json"
export AI_GATEWAY_API_KEY="33d5da24be2b33910b7b8a57e11f99b3b6631c46266bc1603626dcac3cece3af"

# Check credentials exist
if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "❌ Error: Credentials file not found at $GOOGLE_APPLICATION_CREDENTIALS"
    exit 1
fi

# Kill any existing instances
pkill -f "python.*api_gateway.py" 2>/dev/null || true
sleep 1

# Start server in background
echo "📝 Starting server (logs: /tmp/ai-gateway.log)..."
.venv/bin/python api_gateway.py > /tmp/ai-gateway.log 2>&1 &
SERVER_PID=$!

echo "⏳ Waiting for server to start..."
sleep 4

# Check if server is running
if ps -p $SERVER_PID > /dev/null 2>&1; then
    echo "✅ Server started successfully (PID: $SERVER_PID)"
    echo "🌐 API available at: http://localhost:8000"
    echo "📖 API docs: http://localhost:8000/docs"
    echo "🔍 Health check: http://localhost:8000/health"
    echo ""
    echo "📋 Quick test:"
    echo "  curl http://localhost:8000/"
    echo ""
    echo "To stop server: pkill -f 'python.*api_gateway.py'"
    echo "To view logs: tail -f /tmp/ai-gateway.log"
    echo "To run tests: ./test_gateway.sh"
else
    echo "❌ Server failed to start. Check logs:"
    tail -30 /tmp/ai-gateway.log
    exit 1
fi
