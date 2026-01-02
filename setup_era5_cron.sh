#!/bin/bash
# Setup daily cron job to download remaining ERA5 weather data

SCRIPT_PATH="/home/george/GB-Power-Market-JJ/download_era5_remaining_farms.py"
LOG_PATH="/home/george/GB-Power-Market-JJ/logs/era5_incremental.log"

# Create logs directory
mkdir -p /home/george/GB-Power-Market-JJ/logs

# Create cron job (runs at 3 AM daily)
CRON_CMD="0 3 * * * cd /home/george/GB-Power-Market-JJ && /usr/bin/python3 $SCRIPT_PATH >> $LOG_PATH 2>&1"

# Check if cron job already exists
if crontab -l 2>/dev/null | grep -q "download_era5_remaining_farms.py"; then
    echo "⚠️  Cron job already exists"
    echo "Current crontab:"
    crontab -l | grep "download_era5_remaining_farms.py"
else
    # Add to crontab
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo "✅ Cron job added successfully"
    echo "   Schedule: Daily at 3:00 AM"
    echo "   Script: $SCRIPT_PATH"
    echo "   Log: $LOG_PATH"
fi

echo ""
echo "📋 Current crontab:"
crontab -l | grep -E "(download_era5|#)"

echo ""
echo "🧪 Test run (manual):"
echo "   python3 $SCRIPT_PATH"
