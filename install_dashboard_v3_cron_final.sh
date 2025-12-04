#!/bin/bash

# Dashboard V3 - Install Cron Job (Final Version)
# Runs dashboard_v3_auto_refresh_with_data.py every 15 minutes

set -e

SCRIPT_DIR="$HOME/GB-Power-Market-JJ"
PYTHON_SCRIPT="$SCRIPT_DIR/python/dashboard_v3_auto_refresh_with_data.py"
LOG_DIR="$SCRIPT_DIR/logs"
LOG_FILE="$LOG_DIR/dashboard_v3_auto_refresh.log"

echo "======================================================================"
echo "🔧 Dashboard V3 - Cron Job Installer (Final)"
echo "======================================================================"
echo ""

# Check script exists
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Error: $PYTHON_SCRIPT not found"
    exit 1
fi

# Create logs directory
mkdir -p "$LOG_DIR"

# Test script execution
echo "1️⃣  Testing script execution..."
if python3 "$PYTHON_SCRIPT" > /dev/null 2>&1; then
    echo "   ✅ Script runs successfully"
else
    echo "   ⚠️  Script test failed, but continuing (might be first run)"
fi

# Check for existing cron job
CRON_PATTERN="dashboard_v3_auto_refresh"
EXISTING_CRON=$(crontab -l 2>/dev/null | grep "$CRON_PATTERN" || true)

if [ ! -z "$EXISTING_CRON" ]; then
    echo ""
    echo "2️⃣  Existing cron job found:"
    echo "   $EXISTING_CRON"
    echo ""
    read -p "   Replace it? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        crontab -l 2>/dev/null | grep -v "$CRON_PATTERN" | crontab -
        echo "   ✅ Removed old cron job"
    else
        echo "   ⏭️  Keeping existing cron job"
        exit 0
    fi
else
    echo ""
    echo "2️⃣  No existing cron job found"
fi

# Install new cron job
echo ""
echo "3️⃣  Installing new cron job..."

CRON_CMD="*/15 * * * * /usr/bin/python3 $PYTHON_SCRIPT >> $LOG_FILE 2>&1"

(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

echo "   ✅ Cron job installed"

# Verify
echo ""
echo "4️⃣  Verification:"
echo ""
crontab -l | grep "$CRON_PATTERN"

echo ""
echo "======================================================================"
echo "✅ SUCCESS: Dashboard V3 will auto-refresh every 15 minutes"
echo "======================================================================"
echo ""
echo "📊 What gets refreshed:"
echo "  • VLP_Data sheet (balancing actions)"
echo "  • Market_Prices sheet (IRIS wholesale prices)"
echo "  • Fuel Mix & Interconnectors"
echo "  • Active Outages"
echo ""
echo "📝 Monitor logs:"
echo "   tail -f $LOG_FILE"
echo ""
echo "🛑 To remove cron job:"
echo "   crontab -e"
echo "   (delete the line containing 'dashboard_v3_auto_refresh_with_data')"
echo ""
echo "======================================================================"
