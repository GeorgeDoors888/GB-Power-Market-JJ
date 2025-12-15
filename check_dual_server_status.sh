#!/bin/bash
# Quick status check for dual-server architecture

echo "================================================================"
echo "  GB POWER MARKET - DUAL SERVER STATUS CHECK"
echo "================================================================"
echo ""

# Check UpCloud health
echo "🌐 UpCloud Server (94.237.55.234)"
echo "----------------------------------------------------------------"
HEALTH_CHECK=$(curl -s --max-time 5 http://94.237.55.234:8080/health)
if [ $? -eq 0 ]; then
    echo "✅ Health endpoint responding"
    echo "$HEALTH_CHECK" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_CHECK"
else
    echo "❌ Health endpoint not responding"
fi
echo ""

# Check Dell failover monitor
echo "💻 Dell Failover Monitor"
echo "----------------------------------------------------------------"
MONITOR_PID=$(ps aux | grep monitor_and_failover.py | grep -v grep | awk '{print $2}')
if [ -n "$MONITOR_PID" ]; then
    echo "✅ Monitor running (PID: $MONITOR_PID)"
    
    # Check if failover is active
    FAILOVER_ACTIVE=$(ps aux | grep "realtime_dashboard_updater.py\|update_outages_enhanced.py" | grep -v grep | wc -l)
    if [ "$FAILOVER_ACTIVE" -gt 0 ]; then
        echo "🚨 FAILOVER ACTIVE - Dell backup services running"
    else
        echo "✅ Normal mode - UpCloud handling all services"
    fi
    
    # Show last log entry
    if [ -f "failover_monitor.log" ]; then
        echo ""
        echo "Last log entry:"
        tail -1 failover_monitor.log
    fi
else
    echo "⚠️  Monitor not running"
    echo "Start with: nohup python3 monitor_and_failover.py &"
fi
echo ""

# Check Dashboard status
echo "📊 Google Sheets Dashboard"
echo "----------------------------------------------------------------"
DASHBOARD_STATUS=$(python3 -c "
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

try:
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key('1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA')
    dashboard = sh.worksheet('Dashboard')
    
    row2 = dashboard.get('A2')
    if row2 and len(row2) > 0 and len(row2[0]) > 0:
        print('✅', row2[0][0])
    else:
        print('⚠️  No timestamp found')
except Exception as e:
    print(f'❌ Error: {e}')
" 2>&1)

echo "$DASHBOARD_STATUS"
echo ""

# Summary
echo "================================================================"
echo "  SUMMARY"
echo "================================================================"

if echo "$HEALTH_CHECK" | grep -q "healthy"; then
    echo "✅ UpCloud: Online and healthy"
else
    echo "⚠️  UpCloud: Issues detected"
fi

if [ -n "$MONITOR_PID" ]; then
    echo "✅ Dell Monitor: Active"
else
    echo "⚠️  Dell Monitor: Not running"
fi

if echo "$DASHBOARD_STATUS" | grep -q "✅"; then
    echo "✅ Dashboard: Updating"
else
    echo "⚠️  Dashboard: Check required"
fi

echo ""
echo "================================================================"
echo "For detailed logs:"
echo "  UpCloud: ssh root@94.237.55.234 'tail -f /root/GB-Power-Market-JJ/logs/*.log'"
echo "  Dell: tail -f failover_monitor.log"
echo "================================================================"
