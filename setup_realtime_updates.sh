#!/bin/bash
# Setup script for real-time FUELINST data updates
# This configures cron to run updates every 5 minutes

PROJECT_DIR="/Users/georgemajor/GB Power Market JJ"
PYTHON_BIN="$PROJECT_DIR/.venv/bin/python"
UPDATER_SCRIPT="$PROJECT_DIR/realtime_updater.py"
LOG_DIR="$PROJECT_DIR/logs"

echo "=============================================================================="
echo "🚀 REAL-TIME DATA UPDATE SETUP"
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
echo "🧪 Testing updater script..."
cd "$PROJECT_DIR"
"$PYTHON_BIN" "$UPDATER_SCRIPT" --check-only

if [ $? -eq 0 ]; then
    echo "   ✅ Updater script works!"
else
    echo "   ❌ Updater script failed. Please check the logs."
    exit 1
fi

# Generate crontab entry
CRON_ENTRY="*/5 * * * * cd '$PROJECT_DIR' && '$PYTHON_BIN' '$UPDATER_SCRIPT' >> '$LOG_DIR/realtime_cron.log' 2>&1"

echo ""
echo "=============================================================================="
echo "📋 CRON JOB CONFIGURATION"
echo "=============================================================================="
echo ""
echo "The following cron job will run every 5 minutes:"
echo ""
echo "$CRON_ENTRY"
echo ""
echo "This will:"
echo "  • Run every 5 minutes (*/5 * * * *)"
echo "  • Fetch data from the last 15 minutes"
echo "  • Log to: $LOG_DIR/realtime_cron.log"
echo "  • Also logs to: $LOG_DIR/realtime_updates.log"
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
echo "📊 Monitoring:"
echo "   • Real-time logs: tail -f $LOG_DIR/realtime_updates.log"
echo "   • Cron logs: tail -f $LOG_DIR/realtime_cron.log"
echo ""
echo "🛠️  Management commands:"
echo "   • Check status: $PYTHON_BIN $UPDATER_SCRIPT --check-only"
echo "   • Manual run: $PYTHON_BIN $UPDATER_SCRIPT"
echo "   • View cron jobs: crontab -l"
echo "   • Edit cron jobs: crontab -e"
echo "   • Remove cron job: crontab -e (then delete the line)"
echo ""
echo "⏰ Next update: Within 5 minutes"
echo "=============================================================================="
