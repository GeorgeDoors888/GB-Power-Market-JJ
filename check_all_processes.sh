#!/bin/bash
# Check status of all GB Power Market processes

echo "=========================================="
echo "GB Power Market - Process Status"
echo "=========================================="
echo "Date: $(date)"
echo "Hostname: $(hostname)"
echo "Uptime: $(uptime -p)"
echo ""

echo "=========================================="
echo "1. SYSTEMD SERVICES"
echo "=========================================="
for service in iris-client iris-uploader dashboard-updater historical-backfill; do
    if systemctl is-active --quiet $service 2>/dev/null; then
        echo "✅ $service: ACTIVE"
        systemctl status $service --no-pager -l | grep -E "(Active|Main PID|Memory|CPU)" | head -4
    else
        echo "❌ $service: INACTIVE"
    fi
    echo ""
done

echo "=========================================="
echo "2. SCREEN SESSIONS"
echo "=========================================="
screen -ls 2>/dev/null || echo "No screen sessions active"
echo ""

echo "=========================================="
echo "3. PYTHON PROCESSES"
echo "=========================================="
ps aux | grep -E "python3.*(client|iris_to_bigquery|dashboard|backfill)" | grep -v grep | awk '{printf "PID %-7s CPU %-5s MEM %-5s CMD %s\n", $2, $3"%", $4"%", $11" "$12" "$13}'
echo ""

echo "=========================================="
echo "4. RESOURCE USAGE (128GB Machine)"
echo "=========================================="
echo "Memory:"
free -h | grep -E "Mem|Swap"
echo ""
echo "CPU Load:"
uptime | awk -F'load average:' '{print "  "$2}'
echo ""
echo "Disk Usage:"
df -h /opt/iris-pipeline /home/george | grep -v "tmpfs"
echo ""

echo "=========================================="
echo "5. RECENT LOG ACTIVITY"
echo "=========================================="
echo "IRIS Client (last 5 lines):"
tail -5 /opt/iris-pipeline/logs/client/iris_client.log 2>/dev/null || echo "  No logs found"
echo ""
echo "IRIS Uploader (last 5 lines):"
tail -5 /opt/iris-pipeline/logs/uploader/iris_uploader.log 2>/dev/null || echo "  No logs found"
echo ""

echo "=========================================="
echo "6. QUICK HEALTH CHECK"
echo "=========================================="
ISSUES=0

# Check if IRIS client is running
if ! pgrep -f "python3.*client.py" > /dev/null; then
    echo "⚠️  WARNING: IRIS client not running"
    ISSUES=$((ISSUES + 1))
fi

# Check if uploader is running
if ! pgrep -f "python3.*iris_to_bigquery" > /dev/null; then
    echo "⚠️  WARNING: IRIS uploader not running"
    ISSUES=$((ISSUES + 1))
fi

# Check disk space
DISK_USAGE=$(df /opt/iris-pipeline | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "⚠️  WARNING: Disk usage >90% on /opt/iris-pipeline"
    ISSUES=$((ISSUES + 1))
fi

# Check memory
MEM_USAGE=$(free | grep Mem | awk '{print ($3/$2) * 100.0}' | cut -d. -f1)
if [ "$MEM_USAGE" -gt 90 ]; then
    echo "⚠️  WARNING: Memory usage >90%"
    ISSUES=$((ISSUES + 1))
fi

if [ "$ISSUES" -eq 0 ]; then
    echo "✅ All systems operational"
else
    echo "⚠️  Found $ISSUES issue(s)"
fi

echo ""
echo "=========================================="
echo "MANAGEMENT COMMANDS"
echo "=========================================="
echo "Systemd:"
echo "  sudo systemctl start iris-client"
echo "  sudo systemctl status iris-client"
echo "  sudo systemctl restart iris-uploader"
echo ""
echo "Screen:"
echo "  ./manage_sessions.sh list"
echo "  ./manage_sessions.sh start iris-client"
echo "  ./manage_sessions.sh attach iris-client  # Ctrl-A D to detach"
echo ""
echo "Logs:"
echo "  tail -f /opt/iris-pipeline/logs/client/iris_client.log"
echo "  tail -f /opt/iris-pipeline/logs/uploader/iris_uploader.log"
echo "=========================================="
