#!/bin/bash
# Multi-Process Management Setup for 128GB Machine
# Prevents process interruption and enables parallel execution

set -e

echo "=========================================="
echo "Setting Up Multi-Process Infrastructure"
echo "=========================================="
echo "Machine: 128GB RAM"
echo "Date: $(date)"
echo ""

# 1. Create dedicated log directory structure
echo "1. Creating log directory structure..."
mkdir -p /opt/iris-pipeline/logs/{client,uploader,dashboard,backfill}
mkdir -p /home/george/GB-Power-Market-JJ/logs/{queries,scripts,monitoring}

# 2. Create systemd service for IRIS client
echo "2. Creating systemd service for IRIS client..."
sudo tee /etc/systemd/system/iris-client.service > /dev/null << 'EOF'
[Unit]
Description=IRIS Client - Azure Service Bus Data Downloader
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/iris-pipeline/scripts
Environment="GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json"
ExecStart=/usr/bin/python3 /opt/iris-pipeline/scripts/client.py
StandardOutput=append:/opt/iris-pipeline/logs/client/iris_client.log
StandardError=append:/opt/iris-pipeline/logs/client/iris_client_error.log
Restart=always
RestartSec=30
KillMode=mixed
TimeoutStopSec=30

# Resource limits (128GB machine)
MemoryMax=4G
CPUQuota=50%

[Install]
WantedBy=multi-user.target
EOF

# 3. Create systemd service for IRIS uploader
echo "3. Creating systemd service for IRIS uploader..."
sudo tee /etc/systemd/system/iris-uploader.service > /dev/null << 'EOF'
[Unit]
Description=IRIS Uploader - BigQuery Data Upload (Continuous Mode)
After=network-online.target iris-client.service
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/iris-pipeline/scripts
Environment="GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json"
ExecStart=/usr/bin/python3 /opt/iris-pipeline/scripts/iris_to_bigquery_unified.py --continuous
StandardOutput=append:/opt/iris-pipeline/logs/uploader/iris_uploader.log
StandardError=append:/opt/iris-pipeline/logs/uploader/iris_uploader_error.log
Restart=always
RestartSec=30
KillMode=mixed
TimeoutStopSec=60

# Resource limits
MemoryMax=8G
CPUQuota=100%

[Install]
WantedBy=multi-user.target
EOF

# 4. Create systemd service for dashboard updates
echo "4. Creating systemd service for dashboard updates..."
sudo tee /etc/systemd/system/dashboard-updater.service > /dev/null << 'EOF'
[Unit]
Description=GB Power Dashboard Auto-Updater (Every 5 minutes)
After=network-online.target

[Service]
Type=simple
User=george
WorkingDirectory=/home/george/GB-Power-Market-JJ
Environment="GOOGLE_APPLICATION_CREDENTIALS=/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json"
ExecStart=/usr/bin/python3 /home/george/GB-Power-Market-JJ/realtime_dashboard_updater.py
StandardOutput=append:/home/george/GB-Power-Market-JJ/logs/dashboard/dashboard_updater.log
StandardError=append:/home/george/GB-Power-Market-JJ/logs/dashboard/dashboard_updater_error.log
Restart=always
RestartSec=10

# Resource limits
MemoryMax=2G
CPUQuota=25%

[Install]
WantedBy=multi-user.target
EOF

# 5. Create systemd timer for daily backfill (historical data)
echo "5. Creating systemd timer for daily backfill..."
sudo tee /etc/systemd/system/historical-backfill.service > /dev/null << 'EOF'
[Unit]
Description=Historical Data Backfill (Daily Gap Check)
After=network-online.target

[Service]
Type=oneshot
User=george
WorkingDirectory=/home/george/GB-Power-Market-JJ
Environment="GOOGLE_APPLICATION_CREDENTIALS=/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json"
ExecStart=/usr/bin/python3 /home/george/GB-Power-Market-JJ/backfill_gaps_only.py
StandardOutput=append:/home/george/GB-Power-Market-JJ/logs/backfill/backfill.log
StandardError=append:/home/george/GB-Power-Market-JJ/logs/backfill/backfill_error.log

# Resource limits
MemoryMax=4G
CPUQuota=50%
EOF

sudo tee /etc/systemd/system/historical-backfill.timer > /dev/null << 'EOF'
[Unit]
Description=Run Historical Backfill Daily at 02:00 AM

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# 6. Create screen session manager script
echo "6. Creating screen session manager..."
cat > /home/george/GB-Power-Market-JJ/manage_sessions.sh << 'EOF'
#!/bin/bash
# Screen Session Manager - Manage long-running processes

ACTION=$1
SESSION=$2

case "$ACTION" in
    start)
        case "$SESSION" in
            iris-client)
                screen -dmS iris-client bash -c "cd /opt/iris-pipeline/scripts && export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json && python3 client.py 2>&1 | tee -a /opt/iris-pipeline/logs/client/screen.log"
                echo "✅ Started iris-client in screen"
                ;;
            iris-uploader)
                screen -dmS iris-uploader bash -c "cd /opt/iris-pipeline/scripts && export GOOGLE_APPLICATION_CREDENTIALS=/opt/iris-pipeline/secrets/sa.json && python3 iris_to_bigquery_unified.py --continuous 2>&1 | tee -a /opt/iris-pipeline/logs/uploader/screen.log"
                echo "✅ Started iris-uploader in screen"
                ;;
            dashboard)
                screen -dmS dashboard bash -c "cd /home/george/GB-Power-Market-JJ && export GOOGLE_APPLICATION_CREDENTIALS=/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json && python3 realtime_dashboard_updater.py 2>&1 | tee -a logs/dashboard/screen.log"
                echo "✅ Started dashboard in screen"
                ;;
            bigquery-audit)
                screen -dmS bigquery-audit bash -c "cd /home/george/GB-Power-Market-JJ && export GOOGLE_APPLICATION_CREDENTIALS=/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json && python3 DATA_COMPREHENSIVE_AUDIT_DEC20_2025.py 2>&1 | tee logs/queries/audit_$(date +%Y%m%d_%H%M%S).log"
                echo "✅ Started bigquery-audit in screen"
                ;;
            *)
                echo "Unknown session: $SESSION"
                echo "Available: iris-client, iris-uploader, dashboard, bigquery-audit"
                exit 1
                ;;
        esac
        ;;

    list)
        echo "Active screen sessions:"
        screen -ls
        ;;

    attach)
        if [ -z "$SESSION" ]; then
            echo "Usage: $0 attach <session-name>"
            exit 1
        fi
        screen -r "$SESSION"
        ;;

    stop)
        if [ -z "$SESSION" ]; then
            echo "Usage: $0 stop <session-name>"
            exit 1
        fi
        screen -S "$SESSION" -X quit
        echo "✅ Stopped $SESSION"
        ;;

    stopall)
        for sess in iris-client iris-uploader dashboard bigquery-audit; do
            screen -S "$sess" -X quit 2>/dev/null && echo "Stopped $sess" || true
        done
        echo "✅ All sessions stopped"
        ;;

    restart)
        if [ -z "$SESSION" ]; then
            echo "Usage: $0 restart <session-name>"
            exit 1
        fi
        $0 stop "$SESSION"
        sleep 2
        $0 start "$SESSION"
        ;;

    *)
        echo "GB Power Market - Screen Session Manager"
        echo "========================================"
        echo "Usage: $0 <action> [session-name]"
        echo ""
        echo "Actions:"
        echo "  start <session>   - Start a screen session"
        echo "  stop <session>    - Stop a screen session"
        echo "  stopall           - Stop all sessions"
        echo "  restart <session> - Restart a session"
        echo "  list              - List active sessions"
        echo "  attach <session>  - Attach to session (Ctrl-A D to detach)"
        echo ""
        echo "Sessions:"
        echo "  iris-client       - IRIS Azure downloader"
        echo "  iris-uploader     - BigQuery uploader"
        echo "  dashboard         - Dashboard auto-updater"
        echo "  bigquery-audit    - Run data audit"
        echo ""
        echo "Examples:"
        echo "  $0 start iris-client"
        echo "  $0 list"
        echo "  $0 attach iris-client"
        echo "  $0 stop dashboard"
        exit 1
        ;;
esac
EOF

chmod +x /home/george/GB-Power-Market-JJ/manage_sessions.sh

# 7. Create process status checker
echo "7. Creating process status checker..."
cat > /home/george/GB-Power-Market-JJ/check_all_processes.sh << 'EOF'
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
EOF

chmod +x /home/george/GB-Power-Market-JJ/check_all_processes.sh

# 8. Stop current foreground processes
echo "8. Stopping current foreground processes..."
pkill -f "python3 client.py" 2>/dev/null || true
sleep 2

# 9. Reload systemd and enable services
echo "9. Configuring systemd services..."
sudo systemctl daemon-reload
sudo systemctl enable iris-client.service
sudo systemctl enable iris-uploader.service
sudo systemctl enable dashboard-updater.service
sudo systemctl enable historical-backfill.timer

# 10. Start services
echo "10. Starting services..."
sudo systemctl start iris-client
sleep 3
sudo systemctl start iris-uploader
sleep 2
sudo systemctl start dashboard-updater

echo ""
echo "=========================================="
echo "✅ SETUP COMPLETE"
echo "=========================================="
echo ""
echo "Services Started:"
echo "  ✅ iris-client (systemd)"
echo "  ✅ iris-uploader (systemd)"
echo "  ✅ dashboard-updater (systemd)"
echo ""
echo "Check Status:"
echo "  ./check_all_processes.sh"
echo ""
echo "View Logs:"
echo "  tail -f /opt/iris-pipeline/logs/client/iris_client.log"
echo "  tail -f /opt/iris-pipeline/logs/uploader/iris_uploader.log"
echo ""
echo "Manage Screen Sessions (alternative to systemd):"
echo "  ./manage_sessions.sh list"
echo "  ./manage_sessions.sh start iris-client"
echo "  ./manage_sessions.sh attach iris-client"
echo ""
echo "All processes now run independently without interrupting terminal!"
echo "=========================================="
