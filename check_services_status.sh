#!/bin/bash
# Complete Services Status and Startup Script
# Run this to check status and start any missing services

PROJECT_DIR="/Users/georgemajor/GB Power Market JJ"
cd "$PROJECT_DIR"

echo "================================================================================"
echo "🔍 GB POWER MARKET - SERVICES STATUS CHECK"
echo "================================================================================"
echo ""

# Function to check if service is running
check_service() {
    local name=$1
    local search_pattern=$2
    local pid=$(ps aux | grep "$search_pattern" | grep -v grep | awk '{print $2}' | head -1)
    
    if [ -n "$pid" ]; then
        echo "✅ $name: Running (PID $pid)"
        return 0
    else
        echo "❌ $name: NOT running"
        return 1
    fi
}

echo "📡 LOCAL SERVICES (MacBook)"
echo "────────────────────────────────────────────────────────────────────────────────"

# Check webhook server
check_service "DNO Webhook Server" "dno_webhook_server.py"
webhook_running=$?

# Check ngrok
check_service "Ngrok Tunnel" "ngrok http 5001"
ngrok_running=$?

# Check cron for dashboard updates
echo ""
if crontab -l 2>/dev/null | grep -q "realtime_dashboard_updater.py"; then
    echo "✅ Cron: Dashboard auto-updater configured (every 5 min)"
    echo "   Last run: $(tail -1 logs/dashboard_updater.log 2>/dev/null | awk '{print $1, $2}')"
else
    echo "❌ Cron: Dashboard auto-updater NOT configured"
fi

echo ""
echo "================================================================================"
echo "🖥️  REMOTE SERVICES (UpCloud AlmaLinux Server)"
echo "================================================================================"
echo ""
echo "⚠️  Manual check required - SSH into server:"
echo ""
echo "   ssh root@94.237.55.234"
echo ""
echo "   Then check these services:"
echo "   1. IRIS Pipeline:"
echo "      systemctl status iris-pipeline"
echo "      tail -f /opt/iris-pipeline/logs/iris_uploader.log"
echo ""
echo "   2. Dell Server Control:"
echo "      Check if automation is running for Dell power management"
echo ""

echo ""
echo "================================================================================"
echo "🔧 WHAT NEEDS TO START"
echo "================================================================================"
echo ""

# Determine what needs to start
needs_start=0

if [ $webhook_running -ne 0 ]; then
    echo "❌ DNO Webhook Server - needed for Google Sheets 'Refresh DNO' button"
    needs_start=1
fi

if [ $ngrok_running -ne 0 ]; then
    echo "❌ Ngrok Tunnel - needed to expose webhook to Google Sheets"
    needs_start=1
fi

if [ $needs_start -eq 0 ]; then
    echo "✅ All local services running!"
else
    echo ""
    echo "================================================================================"
    echo "🚀 START MISSING SERVICES"
    echo "================================================================================"
    echo ""
    
    if [ $webhook_running -ne 0 ]; then
        echo "Start webhook server:"
        echo "  python3 dno_webhook_server.py"
        echo ""
    fi
    
    if [ $ngrok_running -ne 0 ]; then
        echo "Start ngrok (in separate terminal):"
        echo "  ngrok http 5001"
        echo ""
        echo "Then update Apps Script with new URL:"
        echo "  1. Get URL: curl -s http://127.0.0.1:4040/api/tunnels | python3 -c 'import sys,json; print(json.load(sys.stdin)[\"tunnels\"][0][\"public_url\"])'"
        echo "  2. Edit bess_auto_trigger.gs line 206"
        echo "  3. Update webhookUrl to new ngrok URL"
        echo ""
    fi
fi

echo ""
echo "================================================================================"
echo "📋 GOOGLE SHEETS FUNCTIONS SUMMARY"
echo "================================================================================"
echo ""
echo "Button: 'Refresh DNO' (BESS sheet)"
echo "  Requires: ✅ Webhook Server + ✅ Ngrok"
echo "  Function: Look up DNO info, DUoS rates from postcode/MPAN"
echo ""
echo "Button: 'Generate HH Data' (BESS sheet)"  
echo "  Requires: Nothing (Apps Script calls Python directly)"
echo "  Function: Generate 365 days of half-hourly profile data"
echo ""
echo "Auto-Update: Dashboard Sheet"
echo "  Requires: ✅ Cron job (already configured)"
echo "  Frequency: Every 5 minutes"
echo "  Script: realtime_dashboard_updater.py"
echo "  Status: $(if crontab -l 2>/dev/null | grep -q "realtime_dashboard_updater"; then echo "✅ Active"; else echo "❌ Not configured"; fi)"
echo ""
echo "Auto-Update: Map Generation (Dell + UpCloud)"
echo "  Requires: ✅ Dell Server + ✅ UpCloud cron + ✅ IRIS pipeline"
echo "  Frequency: Every 30 minutes"
echo "  Status: ⚠️  Manual check required"
echo ""

echo "================================================================================"
echo "📂 USEFUL COMMANDS"
echo "================================================================================"
echo ""
echo "Check dashboard update logs:"
echo "  tail -f logs/dashboard_updater.log"
echo ""
echo "Check webhook server logs:"
echo "  tail -f dno_webhook.log  # (if logging enabled)"
echo ""
echo "Get current ngrok URL:"
echo "  curl -s http://127.0.0.1:4040/api/tunnels | python3 -c 'import sys,json; print(json.load(sys.stdin)[\"tunnels\"][0][\"public_url\"])'"
echo ""
echo "Manual dashboard update:"
echo "  python3 update_dashboard_preserve_layout.py"
echo ""
echo "Kill webhook server:"
echo "  kill $(lsof -t -i:5001)"
echo ""

echo "================================================================================"
