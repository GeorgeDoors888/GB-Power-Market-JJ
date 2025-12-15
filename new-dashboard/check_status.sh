#!/bin/bash
# Check Dashboard V2 deployment status

echo "=============================================================================="
echo "DASHBOARD V2 STATUS CHECK"
echo "=============================================================================="
echo ""

# Check webhook server
echo "📡 Webhook Server:"
if ps aux | grep -v grep | grep "webhook_server.py" > /dev/null; then
    PID=$(cat webhook.pid 2>/dev/null || echo "unknown")
    echo "   ✅ Running (PID: $PID)"
    echo "   📍 Local: http://localhost:5001"
else
    echo "   ❌ NOT RUNNING"
    echo "   💡 Start with: python3 webhook_server.py &"
fi
echo ""

# Check ngrok tunnel
echo "🌐 ngrok Tunnel:"
if ps aux | grep -v grep | grep "ngrok http" > /dev/null; then
    PID=$(cat ngrok.pid 2>/dev/null || echo "unknown")
    PUBLIC_URL=$(curl -s http://localhost:4040/api/tunnels 2>/dev/null | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['tunnels'][0]['public_url'])" 2>/dev/null)
    if [ -n "$PUBLIC_URL" ]; then
        echo "   ✅ Running (PID: $PID)"
        echo "   🌍 Public: $PUBLIC_URL"
    else
        echo "   ⚠️  Running but URL not ready"
    fi
else
    echo "   ❌ NOT RUNNING"
    echo "   💡 Start with: ngrok http 5001 &"
fi
echo ""

# Test webhook health
echo "🏥 Health Check:"
HEALTH=$(curl -s http://localhost:5001/health 2>/dev/null | python3 -c "import sys, json; print(json.load(sys.stdin)['status'])" 2>/dev/null)
if [ "$HEALTH" = "ok" ]; then
    echo "   ✅ Webhook responding"
else
    echo "   ❌ Webhook not responding"
fi
echo ""

# Check Google Sheets
echo "📊 Google Sheets:"
echo "   New Dashboard: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
echo "   Old Dashboard: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
echo ""

# Apps Script status
echo "📝 Apps Script:"
SCRIPT_ID=$(cat .clasp.json | python3 -c "import sys, json; print(json.load(sys.stdin)['scriptId'])" 2>/dev/null)
if [ -n "$SCRIPT_ID" ]; then
    echo "   ✅ Script ID: $SCRIPT_ID"
    echo "   🔗 Edit: https://script.google.com/d/$SCRIPT_ID/edit"
else
    echo "   ❌ No script ID found"
fi
echo ""

# Service account check
echo "🔑 Service Account:"
echo "   📧 all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com"
echo "   ⚠️  MUST have Editor access to new spreadsheet"
echo "   💡 Share manually if webhooks fail with permission errors"
echo ""

echo "=============================================================================="
echo "NEXT STEPS:"
echo "=============================================================================="
echo ""
echo "1. Share spreadsheet with service account:"
echo "   - Open: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
echo "   - Click Share → Add: all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com"
echo "   - Give Editor access"
echo ""
echo "2. Test in Google Sheets:"
echo "   - Refresh the spreadsheet"
echo "   - Menu: Data → Copy from Old Dashboard"
echo "   - Menu: Maps → Constraint Map"
echo ""
echo "3. Monitor logs:"
echo "   tail -f webhook.log"
echo ""
