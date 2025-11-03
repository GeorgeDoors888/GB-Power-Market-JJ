#!/bin/bash
# Setup Cron Job for Automated Map Generation on AlmaLinux
# Runs every 30 minutes to regenerate the GB Power Map

set -e

echo "=== Setting Up Cron Job for GB Power Map ==="

# Configuration
SCRIPT_PATH="/var/www/maps/scripts/auto_generate_map_linux.py"
PYTHON_BIN="/usr/bin/python3"
LOG_DIR="/var/www/maps/logs"

# Check if Python exists
echo ""
echo "Step 1: Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✓ Found: $PYTHON_VERSION"
    PYTHON_BIN=$(which python3)
else
    echo "✗ ERROR: Python3 not found"
    exit 1
fi

# Check if script exists
echo ""
echo "Step 2: Checking script file..."
if [ -f "$SCRIPT_PATH" ]; then
    echo "✓ Found: $SCRIPT_PATH"
else
    echo "⚠ WARNING: Script not found at $SCRIPT_PATH"
    echo "  Please copy auto_generate_map_linux.py to /var/www/maps/scripts/"
    exit 1
fi

# Create cron job
echo ""
echo "Step 3: Creating cron job..."

# Backup existing crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true

# Remove any existing map generation cron jobs
crontab -l 2>/dev/null | grep -v "auto_generate_map" > /tmp/new_crontab || true

# Add new cron job - every 30 minutes
echo "" >> /tmp/new_crontab
echo "# GB Power Map Auto-Generation (every 30 minutes)" >> /tmp/new_crontab
echo "*/30 * * * * $PYTHON_BIN $SCRIPT_PATH >> $LOG_DIR/cron.log 2>&1" >> /tmp/new_crontab

# Install new crontab
crontab /tmp/new_crontab
rm /tmp/new_crontab

echo "✓ Cron job installed"

# Display current crontab
echo ""
echo "=== Current Crontab ==="
crontab -l | grep -A 1 "GB Power Map" || echo "No map cron jobs found"

# Test script manually
echo ""
echo "Step 4: Testing script manually..."
echo "Running: $PYTHON_BIN $SCRIPT_PATH"
if $PYTHON_BIN $SCRIPT_PATH; then
    echo "✓ Script executed successfully"
else
    echo "⚠ Script execution failed - check logs"
fi

# Check output
echo ""
echo "Step 5: Checking output..."
MAP_FILE="/var/www/maps/gb_power_complete_map.html"
if [ -f "$MAP_FILE" ]; then
    FILE_SIZE=$(stat -f%z "$MAP_FILE" 2>/dev/null || stat -c%s "$MAP_FILE" 2>/dev/null)
    FILE_SIZE_MB=$(echo "scale=2; $FILE_SIZE / 1048576" | bc)
    MODIFIED=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$MAP_FILE" 2>/dev/null || stat -c "%y" "$MAP_FILE" 2>/dev/null)
    echo "✓ Map file created:"
    echo "  Path: $MAP_FILE"
    echo "  Size: $FILE_SIZE_MB MB"
    echo "  Modified: $MODIFIED"
else
    echo "⚠ WARNING: Map file not found at $MAP_FILE"
    echo "  Check logs at $LOG_DIR/"
fi

# Display recent log entries
echo ""
echo "=== Recent Log Entries ==="
LOG_FILE="$LOG_DIR/map_generation_$(date +%Y%m%d).log"
if [ -f "$LOG_FILE" ]; then
    tail -n 10 "$LOG_FILE"
else
    echo "No log file found yet"
fi

# Server information
echo ""
echo "=== Server Information ==="
echo "Server: almalinux-1cpu-2gb-uk-lon1"
echo "IP: 94.237.55.234"
echo "Local URL: http://localhost/gb_power_complete_map.html"
echo "Public URL: http://94.237.55.234/gb_power_complete_map.html"

# Test web access
echo ""
echo "Step 6: Testing web access..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost/gb_power_complete_map.html | grep -q "200"; then
    echo "✓ Map is accessible via HTTP"
else
    echo "⚠ Map not yet accessible (may need to wait for next cron run)"
fi

echo ""
echo "=== Setup Complete ==="
echo ""
echo "The map will now be automatically generated every 30 minutes."
echo ""
echo "Useful commands:"
echo "  View crontab: crontab -l"
echo "  Edit crontab: crontab -e"
echo "  View logs: tail -f $LOG_DIR/map_generation_*.log"
echo "  View cron log: tail -f $LOG_DIR/cron.log"
echo "  Manual run: $PYTHON_BIN $SCRIPT_PATH"
echo "  Check status: systemctl status crond"
echo ""
echo "Next scheduled runs:"
# Show next 5 cron execution times
echo "Current time: $(date)"
echo "Cron runs at: 00, 30 minutes past each hour"
