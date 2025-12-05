#!/bin/bash
# Setup script for automated daily COSTS backfill cron job
# This script installs a cron job that runs daily at 6:00 AM UTC

set -e

SCRIPT_DIR="/home/george/GB-Power-Market-JJ"
SCRIPT_NAME="auto_backfill_costs_daily.py"
SCRIPT_PATH="$SCRIPT_DIR/$SCRIPT_NAME"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/auto_backfill_costs.log"
CRON_SCHEDULE="0 6 * * *"  # Daily at 6:00 AM UTC

echo "=================================================================="
echo "SETUP AUTOMATED DAILY COSTS BACKFILL CRON JOB"
echo "=================================================================="
echo ""

# Create logs directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
    echo "📁 Creating logs directory: $LOG_DIR"
    mkdir -p "$LOG_DIR"
else
    echo "✅ Logs directory exists: $LOG_DIR"
fi

# Check if script exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Script not found: $SCRIPT_PATH"
    exit 1
fi
echo "✅ Script found: $SCRIPT_PATH"

# Make script executable
chmod +x "$SCRIPT_PATH"
echo "✅ Script is executable"

# Create cron job entry
CRON_COMMAND="/usr/bin/python3 $SCRIPT_PATH >> $LOG_FILE 2>&1"
CRON_ENTRY="$CRON_SCHEDULE $CRON_COMMAND"

echo ""
echo "📋 Cron job configuration:"
echo "   Schedule: $CRON_SCHEDULE (Daily at 6:00 AM UTC)"
echo "   Script: $SCRIPT_PATH"
echo "   Log file: $LOG_FILE"
echo ""

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "$SCRIPT_NAME"; then
    echo "⚠️  Cron job already exists for $SCRIPT_NAME"
    echo ""
    read -p "Remove existing and reinstall? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove existing cron job
        crontab -l 2>/dev/null | grep -v "$SCRIPT_NAME" | crontab -
        echo "✅ Removed existing cron job"
    else
        echo "ℹ️  Keeping existing cron job"
        exit 0
    fi
fi

# Add new cron job
(crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
echo "✅ Cron job installed!"

echo ""
echo "=================================================================="
echo "SETUP COMPLETE!"
echo "=================================================================="
echo ""
echo "The daily backfill will run automatically at 6:00 AM UTC."
echo ""
echo "Useful commands:"
echo "  View cron jobs:     crontab -l"
echo "  Edit cron jobs:     crontab -e"
echo "  Remove cron job:    crontab -l | grep -v '$SCRIPT_NAME' | crontab -"
echo "  View logs:          tail -f $LOG_FILE"
echo "  Test manually:      python3 $SCRIPT_PATH"
echo ""
echo "Log rotation (optional):"
echo "  Create logrotate config: sudo nano /etc/logrotate.d/costs-backfill"
echo "  Add this content:"
echo "    $LOG_FILE {"
echo "      weekly"
echo "      rotate 8"
echo "      compress"
echo "      missingok"
echo "      notifempty"
echo "    }"
echo ""
