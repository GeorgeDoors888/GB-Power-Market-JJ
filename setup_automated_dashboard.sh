#!/bin/bash
# Setup script for automated GB Power Market Dashboard updates on macOS
# This uses launchd (macOS's native scheduler) instead of cron

set -e  # Exit on error

echo "=========================================="
echo "GB Power Market Dashboard - Setup Automation"
echo "=========================================="
echo ""

# Configuration
PROJECT_DIR="/Users/georgemajor/GB Power Market JJ"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"
SCRIPT_NAME="automated_dashboard_system.py"
LOG_DIR="$PROJECT_DIR/logs"
PLIST_NAME="com.gbpower.dashboard.automation"
PLIST_FILE="$HOME/Library/LaunchAgents/${PLIST_NAME}.plist"

# Validate project directory
if [ ! -d "$PROJECT_DIR" ]; then
    echo "❌ Error: Project directory not found: $PROJECT_DIR"
    exit 1
fi

# Validate virtual environment
if [ ! -f "$VENV_PYTHON" ]; then
    echo "❌ Error: Virtual environment not found: $VENV_PYTHON"
    exit 1
fi

# Validate script
if [ ! -f "$PROJECT_DIR/$SCRIPT_NAME" ]; then
    echo "❌ Error: Script not found: $PROJECT_DIR/$SCRIPT_NAME"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"
echo "✅ Log directory ready: $LOG_DIR"

# Create launchd plist file
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- Job Identification -->
    <key>Label</key>
    <string>${PLIST_NAME}</string>
    
    <!-- Program to Run -->
    <key>ProgramArguments</key>
    <array>
        <string>${VENV_PYTHON}</string>
        <string>${PROJECT_DIR}/${SCRIPT_NAME}</string>
    </array>
    
    <!-- Working Directory -->
    <key>WorkingDirectory</key>
    <string>${PROJECT_DIR}</string>
    
    <!-- Schedule: Run every 15 minutes -->
    <key>StartInterval</key>
    <integer>900</integer>
    
    <!-- Run on Load (immediately when loaded) -->
    <key>RunAtLoad</key>
    <true/>
    
    <!-- Output Logging -->
    <key>StandardOutPath</key>
    <string>${LOG_DIR}/dashboard_automation.log</string>
    
    <key>StandardErrorPath</key>
    <string>${LOG_DIR}/dashboard_automation_error.log</string>
    
    <!-- Keep job alive if it exits -->
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    
    <!-- Environment Variables -->
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:${PROJECT_DIR}/.venv/bin</string>
        <key>GOOGLE_APPLICATION_CREDENTIALS</key>
        <string>${PROJECT_DIR}/token.pickle</string>
    </dict>
    
    <!-- Resource Limits -->
    <key>SoftResourceLimits</key>
    <dict>
        <key>NumberOfFiles</key>
        <integer>1024</integer>
    </dict>
    
    <!-- Process Priority (Nice value: 0 = normal) -->
    <key>Nice</key>
    <integer>0</integer>
</dict>
</plist>
EOF

echo "✅ Created launchd configuration: $PLIST_FILE"

# Unload existing job if running
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "⚠️  Unloading existing automation job..."
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
fi

# Load the new job
echo "🚀 Loading automation job..."
launchctl load "$PLIST_FILE"

# Verify it's running
sleep 2
if launchctl list | grep -q "$PLIST_NAME"; then
    echo "✅ Automation job loaded successfully!"
    echo ""
    echo "=========================================="
    echo "Setup Complete!"
    echo "=========================================="
    echo ""
    echo "📊 Dashboard will update automatically every 15 minutes"
    echo ""
    echo "Useful Commands:"
    echo "  View status:    launchctl list | grep $PLIST_NAME"
    echo "  View logs:      tail -f $LOG_DIR/dashboard_automation.log"
    echo "  View errors:    tail -f $LOG_DIR/dashboard_automation_error.log"
    echo "  Stop service:   launchctl unload $PLIST_FILE"
    echo "  Start service:  launchctl load $PLIST_FILE"
    echo "  Test manually:  $VENV_PYTHON $PROJECT_DIR/$SCRIPT_NAME --dry-run"
    echo ""
    echo "🔍 First run will start within 15 minutes"
    echo "📝 Check logs at: $LOG_DIR/dashboard_automation.log"
else
    echo "❌ Failed to load automation job"
    echo "Check for errors with: launchctl error"
    exit 1
fi
