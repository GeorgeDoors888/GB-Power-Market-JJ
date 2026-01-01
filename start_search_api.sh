#!/bin/bash
# Start Search API Server for automatic Apps Script execution

echo "🚀 Starting Search API Server..."
echo ""
echo "📍 This enables automatic search execution from Google Sheets"
echo "⚙️  Apps Script will call: http://localhost:5002/search"
echo ""

# Check if Flask is installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📦 Installing Flask..."
    pip3 install --user flask flask-cors
fi

# Check if search script exists
if [ ! -f "advanced_search_tool_enhanced.py" ]; then
    echo "❌ ERROR: advanced_search_tool_enhanced.py not found"
    exit 1
fi

echo "✅ Starting server on port 5002..."
echo ""

# Run in background
nohup python3 search_api_server.py > logs/search_api.log 2>&1 &
PID=$!

echo "✅ Server started! PID: $PID"
echo ""
echo "📋 Next Steps:"
echo "   1. Open Google Sheets Apps Script"
echo "   2. Update API_ENDPOINT variable (currently localhost:5002)"
echo "   3. For remote access, run: ngrok http 5002"
echo "   4. Test search from Google Sheets"
echo ""
echo "📊 Monitor logs: tail -f logs/search_api.log"
echo "🛑 Stop server: kill $PID"
echo ""
echo "💡 For production deployment, see: SEARCH_API_DEPLOYMENT_GUIDE.md"
