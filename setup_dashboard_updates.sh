#!/bin/bash
# Setup script for automated Google Sheet dashboard updates
# This configures cron to run dashboard updates every 10 minutes

PROJECT_DIR="/Users/georgemajor/GB Power Market JJ"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
UPDATER_SCRIPT="$PROJECT_DIR/dashboard_auto_updater.py"
LOG_DIR="$PROJECT_DIR/logs"

echo "=============================================================================="
echo "📊 DASHBOARD AUTO-UPDATE SETUP"
echo "=============================================================================="
echo ""

# Create logs directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
    echo "📁 Creating logs directory..."
    mkdir -p "$LOG_DIR"
    echo "   ✅ Created: $LOG_DIR"
fi

# Test the updater script first
echo ""
echo "🧪 Testing dashboard updater script..."
cd "$PROJECT_DIR"
"$PYTHON_BIN" "$UPDATER_SCRIPT"

if [ $? -eq 0 ]; then
    echo "   ✅ Dashboard updater works!"
else
    echo "   ❌ Dashboard updater failed. Please check the logs."
    exit 1
fi

# Generate crontab entry
CRON_ENTRY="*/10 * * * * cd '$PROJECT_DIR' && '$PYTHON_BIN' '$UPDATER_SCRIPT' >> '$LOG_DIR/dashboard_updates.log' 2>&1"

echo ""
echo "=============================================================================="
echo "📋 CRON JOB CONFIGURATION"
echo "=============================================================================="
echo ""
echo "The following cron job will run every 10 minutes:"
echo ""
echo "$CRON_ENTRY"
echo ""
echo "This will:"
echo "  • Run every 10 minutes (*/10 * * * *)"
echo "  • Fetch latest data from BigQuery"
echo "  • Calculate metrics and summaries"
echo "  • Update Google Sheet dashboard"
echo "  • Log to: $LOG_DIR/dashboard_updates.log"
echo ""
echo "=============================================================================="
echo "⚙️  INSTALLATION OPTIONS"
echo "=============================================================================="
echo ""
echo "Option 1: Automatic Installation (Recommended)"
echo "   This will add the cron job to your crontab automatically."
echo ""
echo "Option 2: Manual Installation"
echo "   You can copy the cron entry above and add it manually using:"
echo "   $ crontab -e"
echo ""
read -p "Would you like to install automatically? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "📝 Installing cron job..."
    
    # Check if cron job already exists
    if crontab -l 2>/dev/null | grep -q "$UPDATER_SCRIPT"; then
        echo "   ⚠️  Cron job already exists. Skipping installation."
        echo "   To update, first remove the old job with: crontab -e"
    else
        # Add to crontab
        (crontab -l 2>/dev/null; echo "$CRON_ENTRY") | crontab -
        
        if [ $? -eq 0 ]; then
            echo "   ✅ Cron job installed successfully!"
            echo ""
            echo "   To verify, run: crontab -l"
        else
            echo "   ❌ Failed to install cron job."
            exit 1
        fi
    fi
else
    echo ""
    echo "📋 Manual installation instructions:"
    echo "   1. Run: crontab -e"
    echo "   2. Add this line:"
    echo "      $CRON_ENTRY"
    echo "   3. Save and exit"
fi

echo ""
echo "=============================================================================="
echo "✅ SETUP COMPLETE"
echo "=============================================================================="
echo ""
echo "📊 Your dashboard will now update automatically every 10 minutes!"
echo "   🔗 View: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
echo ""
echo "📊 Monitoring:"
echo "   • Dashboard logs: tail -f $LOG_DIR/dashboard_updates.log"
echo "   • Manual update: $PYTHON_BIN $UPDATER_SCRIPT"
echo ""
echo "🛠️  Management commands:"
echo "   • View cron jobs: crontab -l"
echo "   • Edit cron jobs: crontab -e"
echo "   • Remove cron job: crontab -e (then delete the line)"
echo ""
echo "⏰ Next update: Within 10 minutes"
echo "=============================================================================="
