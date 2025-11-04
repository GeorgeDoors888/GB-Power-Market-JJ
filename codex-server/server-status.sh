#!/bin/bash
# Check Codex server status and resource usage
cd "$(dirname "$0")"

echo "🔍 Codex Server Status"
echo "======================="
echo ""

if [ -f server.pid ] && kill -0 $(cat server.pid) 2>/dev/null; then
    PID=$(cat server.pid)
    echo "✅ Status: Running"
    echo "   PID: $PID"
    echo ""
    
    # Get detailed process info
    echo "📊 Resources:"
    ps aux | grep $PID | grep -v grep | awk '{
        printf "   CPU: %s%%\n", $3
        printf "   Memory: %.1f MB\n", $6/1024
        printf "   Uptime: %s\n", $10
    }'
    echo ""
    
    # Check port
    echo "🌐 Network:"
    if lsof -i :8000 | grep -q LISTEN; then
        echo "   ✅ Port 8000: Listening"
        echo "   URL: http://localhost:8000"
    else
        echo "   ❌ Port 8000: Not listening"
    fi
    echo ""
    
    # Test health endpoint
    echo "🏥 Health Check:"
    if command -v curl &> /dev/null; then
        HEALTH=$(curl -s http://localhost:8000/health 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo "   ✅ Server responding"
            echo "   Response: $HEALTH"
        else
            echo "   ⚠️  Server not responding"
        fi
    else
        echo "   (curl not available)"
    fi
    echo ""
    
    # Cost info
    echo "💰 Cost: $0/hour (local server)"
    
else
    echo "❌ Status: Not running"
    echo ""
    if [ -f server.pid ]; then
        echo "   (Stale PID file found: $(cat server.pid))"
        echo "   Clean up with: rm server.pid"
    fi
    echo ""
    echo "Start with: ./server-start.sh"
fi

echo ""
echo "======================="
echo "Commands:"
echo "  ./server-start.sh  - Start server"
echo "  ./server-stop.sh   - Stop server"
echo "  ./server-status.sh - Show this status"
