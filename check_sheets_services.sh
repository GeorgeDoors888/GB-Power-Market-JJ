#!/bin/bash
# GOOGLE SHEETS FUNCTIONS - REQUIRED SERVICES CHECK & START
# Run this script to ensure all services are running for Google Sheets buttons

echo "=================================================================="
echo "CHECKING GOOGLE SHEETS INTEGRATION SERVICES"
echo "=================================================================="
echo ""

# Change to project directory
cd "/Users/georgemajor/GB Power Market JJ" || exit 1

# 1. Check webhook server status
echo "1️⃣  WEBHOOK SERVER (dno_webhook_server.py)"
echo "   Port: 5001"
echo "   Required for: DNO Refresh button, Generate HH Data button"
echo ""

WEBHOOK_PID=$(ps aux | grep "[p]ython3 dno_webhook_server.py" | awk '{print $2}')

if [ -n "$WEBHOOK_PID" ]; then
    echo "   ✅ RUNNING (PID: $WEBHOOK_PID)"
else
    echo "   ❌ NOT RUNNING"
    echo ""
    echo "   To start:"
    echo "   export GOOGLE_APPLICATION_CREDENTIALS=\"$PWD/inner-cinema-credentials.json\""
    echo "   nohup python3 dno_webhook_server.py > webhook.log 2>&1 &"
    echo ""
    
    read -p "   Start webhook server now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        export GOOGLE_APPLICATION_CREDENTIALS="$PWD/inner-cinema-credentials.json"
        nohup python3 dno_webhook_server.py > webhook.log 2>&1 &
        sleep 2
        WEBHOOK_PID=$(ps aux | grep "[p]ython3 dno_webhook_server.py" | awk '{print $2}')
        if [ -n "$WEBHOOK_PID" ]; then
            echo "   ✅ Started (PID: $WEBHOOK_PID)"
        else
            echo "   ❌ Failed to start - check webhook.log"
        fi
    fi
fi

echo ""
echo "=================================================================="

# 2. Check ngrok tunnel status
echo "2️⃣  NGROK TUNNEL"
echo "   Required for: Connecting Apps Script to local webhook"
echo ""

NGROK_PID=$(ps aux | grep "[n]grok http 5001" | awk '{print $2}')

if [ -n "$NGROK_PID" ]; then
    echo "   ✅ RUNNING (PID: $NGROK_PID)"
    
    # Try to get ngrok URL
    sleep 1
    NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o 'https://[a-z0-9]*\.ngrok-free\.app' | head -1)
    
    if [ -n "$NGROK_URL" ]; then
        echo "   🔗 URL: $NGROK_URL"
        echo ""
        echo "   ⚠️  UPDATE THIS URL IN APPS SCRIPT:"
        echo "   File: bess_auto_trigger.gs"
        echo "   Line 206: const webhookUrl = '$NGROK_URL/trigger-dno-lookup';"
    else
        echo "   ⚠️  Could not retrieve URL (check http://localhost:4040)"
    fi
else
    echo "   ❌ NOT RUNNING"
    echo ""
    echo "   To start:"
    echo "   ngrok http 5001"
    echo ""
    
    read -p "   Start ngrok tunnel now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   Starting ngrok in background..."
        nohup ngrok http 5001 > /dev/null 2>&1 &
        sleep 3
        
        NGROK_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | grep -o 'https://[a-z0-9]*\.ngrok-free\.app' | head -1)
        
        if [ -n "$NGROK_URL" ]; then
            echo "   ✅ Started"
            echo "   🔗 URL: $NGROK_URL"
            echo ""
            echo "   ⚠️  UPDATE THIS URL IN APPS SCRIPT:"
            echo "   File: bess_auto_trigger.gs"
            echo "   Line 206: const webhookUrl = '$NGROK_URL/trigger-dno-lookup';"
        else
            echo "   ❌ Failed to start - run manually: ngrok http 5001"
        fi
    fi
fi

echo ""
echo "=================================================================="

# 3. Check credentials
echo "3️⃣  GOOGLE CREDENTIALS"
echo ""

if [ -f "inner-cinema-credentials.json" ]; then
    echo "   ✅ inner-cinema-credentials.json exists"
else
    echo "   ❌ inner-cinema-credentials.json NOT FOUND"
    echo "   This file is required for BigQuery and Sheets access"
fi

echo ""
echo "=================================================================="

# 4. Summary of what each button does
echo ""
echo "📋 GOOGLE SHEETS BUTTONS & DEPENDENCIES:"
echo ""
echo "┌────────────────────────────────────────────────────────────────┐"
echo "│ BUTTON: Refresh DNO                                            │"
echo "├────────────────────────────────────────────────────────────────┤"
echo "│ Function: Updates DNO info, DUoS rates, time bands             │"
echo "│ Reads: A6 (postcode), I6 (supplement), J6 (LLFC), A10 (voltage)│"
echo "│ Writes: C6-H6 (DNO), B10-D10 (rates), E10-J10 (MPAN details)  │"
echo "│ Requires:                                                       │"
echo "│   ✓ Webhook server (dno_webhook_server.py on port 5001)       │"
echo "│   ✓ ngrok tunnel (exposes webhook to Apps Script)             │"
echo "│   ✓ Apps Script webhook URL updated                           │"
echo "└────────────────────────────────────────────────────────────────┘"
echo ""
echo "┌────────────────────────────────────────────────────────────────┐"
echo "│ BUTTON: Generate HH Data (if implemented)                      │"
echo "├────────────────────────────────────────────────────────────────┤"
echo "│ Function: Generates half-hourly load profiles                  │"
echo "│ Reads: G17-G19 (min/avg/max kW)                               │"
echo "│ Writes: BESS sheet rows 20+ (timestamp, demand)               │"
echo "│ Requires:                                                       │"
echo "│   ✓ Webhook server (same as above)                            │"
echo "│   ✓ ngrok tunnel (same as above)                              │"
echo "│   OR: Direct Apps Script mode (no webhook needed, limited)    │"
echo "└────────────────────────────────────────────────────────────────┘"
echo ""
echo "=================================================================="

# 5. Quick start commands
echo ""
echo "🚀 QUICK START COMMANDS:"
echo ""
echo "# Start webhook server:"
echo "export GOOGLE_APPLICATION_CREDENTIALS=\"$PWD/inner-cinema-credentials.json\""
echo "python3 dno_webhook_server.py &"
echo ""
echo "# Start ngrok tunnel:"
echo "ngrok http 5001"
echo ""
echo "# Check status:"
echo "./check_sheets_services.sh"
echo ""
echo "# Stop webhook:"
echo "pkill -f dno_webhook_server"
echo ""
echo "# Stop ngrok:"
echo "pkill ngrok"
echo ""
echo "=================================================================="

# 6. Test connectivity
echo ""
echo "🧪 TESTING CONNECTIVITY:"
echo ""

if [ -n "$WEBHOOK_PID" ]; then
    echo "Testing webhook server (localhost:5001)..."
    curl -s http://localhost:5001/health > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "   ✅ Webhook responding"
    else
        echo "   ⚠️  Webhook not responding (might not have /health endpoint)"
    fi
fi

if [ -n "$NGROK_URL" ]; then
    echo "Testing ngrok tunnel..."
    curl -s -o /dev/null -w "%{http_code}" "$NGROK_URL" 2>/dev/null | grep -q "200\|404"
    if [ $? -eq 0 ]; then
        echo "   ✅ Ngrok tunnel accessible"
    else
        echo "   ⚠️  Ngrok tunnel not responding"
    fi
fi

echo ""
echo "=================================================================="
echo "✅ SERVICE CHECK COMPLETE"
echo "=================================================================="
