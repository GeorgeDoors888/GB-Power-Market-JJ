#!/bin/bash
# Setup script to schedule local extraction for midnight-8am

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PLIST_FILE="$HOME/Library/LaunchAgents/com.overarch.local-extraction.plist"

echo "🛠️  Setting up local extraction scheduler"
echo "=========================================="
echo ""
echo "This will run extraction on your Mac from midnight to 8am daily"
echo ""

# Create the launchd plist file
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.overarch.local-extraction</string>
    
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>$SCRIPT_DIR/local_extraction.py</string>
    </array>
    
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>0</integer>
        <key>Minute</key>
        <integer>5</integer>
    </dict>
    
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/local_extraction_scheduler.log</string>
    
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/local_extraction_scheduler.error.log</string>
    
    <key>RunAtLoad</key>
    <false/>
</dict>
</plist>
EOF

echo "✅ Created launch agent: $PLIST_FILE"
echo ""
echo "📋 To activate the scheduler:"
echo "   launchctl load $PLIST_FILE"
echo ""
echo "📋 To deactivate the scheduler:"
echo "   launchctl unload $PLIST_FILE"
echo ""
echo "📋 To run manually right now (for testing):"
echo "   python3 $SCRIPT_DIR/local_extraction.py"
echo ""
echo "⚠️  NOTE: Your Mac must be running and not sleeping at midnight"
echo "   Go to System Settings > Energy Saver and disable sleep"
echo "   Or use 'caffeinate' to keep it awake"
echo ""
echo "=========================================="
echo ""
read -p "Do you want to activate the scheduler now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    launchctl load "$PLIST_FILE"
    echo "✅ Scheduler activated! Will run at midnight every day."
else
    echo "⏸️  Scheduler created but not activated."
    echo "   Run: launchctl load $PLIST_FILE"
fi
