#!/bin/bash
# GSP Auto-Update Scheduler
# Adds cron job to refresh GSP data every 10 minutes

echo "========================================"
echo "🔄 GSP AUTO-UPDATE SCHEDULER"
echo "========================================"
echo ""

# Get the current directory
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "📁 Working directory: $DIR"
echo ""

# Check if Python virtual environment exists
if [ ! -f "$DIR/.venv/bin/python" ]; then
    echo "❌ ERROR: Virtual environment not found at $DIR/.venv"
    echo "   Please create it first: python3 -m venv .venv"
    exit 1
fi

# Check if script exists
if [ ! -f "$DIR/gsp_auto_updater.py" ]; then
    echo "❌ ERROR: gsp_auto_updater.py not found"
    exit 1
fi

# Create logs directory
mkdir -p "$DIR/logs"
echo "✅ Created logs directory"

# Test the script first
echo ""
echo "🧪 Testing GSP updater script..."
cd "$DIR"
.venv/bin/python gsp_auto_updater.py
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "❌ ERROR: Script test failed (exit code: $EXIT_CODE)"
    echo "   Please fix errors before scheduling"
    exit 1
fi

echo ""
echo "✅ Script test successful!"
echo ""

# Check if cron job already exists
CRON_CMD="*/10 * * * * cd $DIR && .venv/bin/python gsp_auto_updater.py >> logs/gsp_auto_updater.log 2>&1"
EXISTING=$(crontab -l 2>/dev/null | grep "gsp_auto_updater.py" || true)

if [ -n "$EXISTING" ]; then
    echo "⚠️  Cron job already exists:"
    echo "   $EXISTING"
    echo ""
    read -p "Remove existing and add new? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove existing cron job
        crontab -l 2>/dev/null | grep -v "gsp_auto_updater.py" | crontab -
        echo "✅ Removed old cron job"
    else
        echo "ℹ️  Keeping existing cron job"
        exit 0
    fi
fi

# Add new cron job
echo ""
echo "📝 Adding cron job..."
(crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -

if [ $? -eq 0 ]; then
    echo "✅ Cron job added successfully!"
    echo ""
    echo "📋 Current cron jobs:"
    crontab -l | grep "gsp_auto_updater.py"
    echo ""
    echo "⏰ Schedule: Every 10 minutes"
    echo "📊 Dashboard: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
    echo ""
    echo "💡 View logs:"
    echo "   tail -f $DIR/logs/gsp_auto_updater.log"
    echo ""
    echo "🎉 Setup complete! GSP data will refresh every 10 minutes."
else
    echo "❌ ERROR: Failed to add cron job"
    exit 1
fi
