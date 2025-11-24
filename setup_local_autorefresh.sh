#!/bin/bash
# Local Auto-Refresh Setup (Alternative to UpCloud deployment)
# Runs dashboard refresh every 5 minutes from your Mac

SCRIPT_DIR="/Users/georgemajor/GB Power Market JJ"
LOG_FILE="$SCRIPT_DIR/logs/dashboard-refresh.log"

echo "======================================"
echo "🔄 SETTING UP LOCAL AUTO-REFRESH"
echo "======================================"

# Create logs directory
mkdir -p "$SCRIPT_DIR/logs"

# Create cron job script
cat > "$SCRIPT_DIR/run_dashboard_refresh.sh" << 'EOF'
#!/bin/bash
cd "/Users/georgemajor/GB Power Market JJ"
echo "$(date): Starting dashboard refresh..." >> logs/dashboard-refresh.log
/usr/local/bin/python3 fix_dashboard_complete.py >> logs/dashboard-refresh.log 2>&1
echo "$(date): Refresh complete (exit code: $?)" >> logs/dashboard-refresh.log
echo "---" >> logs/dashboard-refresh.log
EOF

chmod +x "$SCRIPT_DIR/run_dashboard_refresh.sh"

# Add to crontab (every 5 minutes)
CRON_LINE="*/5 * * * * /Users/georgemajor/GB\ Power\ Market\ JJ/run_dashboard_refresh.sh"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "run_dashboard_refresh.sh"; then
    echo "⚠️  Cron job already exists"
else
    # Add new cron job
    (crontab -l 2>/dev/null; echo "$CRON_LINE") | crontab -
    echo "✅ Added cron job: Dashboard refreshes every 5 minutes"
fi

echo ""
echo "======================================"
echo "✅ LOCAL AUTO-REFRESH CONFIGURED!"
echo "======================================"
echo "📊 Script: run_dashboard_refresh.sh"
echo "📝 Logs: logs/dashboard-refresh.log"
echo "⏰ Schedule: Every 5 minutes"
echo ""
echo "Useful commands:"
echo "  tail -f logs/dashboard-refresh.log   # Watch live updates"
echo "  crontab -l                            # View cron jobs"
echo "  ./run_dashboard_refresh.sh            # Manual test"
echo ""
echo "To disable:"
echo "  crontab -l | grep -v 'run_dashboard_refresh.sh' | crontab -"
echo "======================================"
