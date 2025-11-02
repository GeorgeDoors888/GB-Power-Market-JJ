#!/bin/bash
# Start Codex server with cost control
cd "$(dirname "$0")"
source .venv/bin/activate

# Check if already running
if [ -f server.pid ] && kill -0 $(cat server.pid) 2>/dev/null; then
    echo "❌ Server already running (PID: $(cat server.pid))"
    echo "   Use ./server-stop.sh first"
    exit 1
fi

# Start server in background
python codex_server.py > server.log 2>&1 &
echo $! > server.pid

echo "✅ Codex server started"
echo "   PID: $(cat server.pid)"
echo "   URL: http://localhost:8000"
echo "   Docs: http://localhost:8000/docs"
echo "   Logs: tail -f server.log"
echo ""
echo "💰 Cost: $0 (running locally)"
echo "📊 Resources: ~16MB RAM, minimal CPU"
echo ""
echo "Stop with: ./server-stop.sh"
