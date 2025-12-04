#!/bin/bash
# VLP Dashboard Cron Setup Script
# Sets up automated refresh every 30 minutes

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_EXEC=$(which python3)
AUTO_REFRESH_SCRIPT="$SCRIPT_DIR/vlp_auto_refresh.py"

echo "=================================="
echo "VLP Dashboard Cron Setup"
echo "=================================="
echo ""
echo "This will add a cron job to refresh the VLP dashboard every 30 minutes"
echo ""
echo "Script: $AUTO_REFRESH_SCRIPT"
echo "Python: $PYTHON_EXEC"
echo ""

# Check if script exists
if [ ! -f "$AUTO_REFRESH_SCRIPT" ]; then
    echo "❌ Error: Auto-refresh script not found"
    exit 1
fi

# Create cron job entry
CRON_ENTRY="*/30 * * * * cd $SCRIPT_DIR && $PYTHON_EXEC $AUTO_REFRESH_SCRIPT >> $SCRIPT_DIR/logs/cron.log 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "vlp_auto_refresh.py"; then
    echo "⚠️  Cron job already exists. Updating..."
    # Remove old entry
    crontab -l 2>/dev/null | grep -v "vlp_auto_refresh.py" | crontab -
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -

echo "✅ Cron job added successfully!"
echo ""
echo "Schedule: Every 30 minutes"
echo "Log file: $SCRIPT_DIR/logs/cron.log"
echo ""
echo "To view cron jobs:"
echo "  crontab -l"
echo ""
echo "To remove this cron job:"
echo "  crontab -l | grep -v 'vlp_auto_refresh.py' | crontab -"
echo ""
echo "To monitor logs:"
echo "  tail -f $SCRIPT_DIR/logs/vlp_auto_refresh.log"
echo "  tail -f $SCRIPT_DIR/logs/cron.log"
echo ""
