#!/bin/bash
# Dashboard V3 Cron Installation Script
# Installs 15-minute auto-refresh for Dashboard V3

set -e

SCRIPT_DIR="$HOME/GB-Power-Market-JJ/python"
LOG_DIR="$HOME/GB-Power-Market-JJ/logs"
PYTHON_BIN=$(which python3)

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "=========================================="
echo "DASHBOARD V3 - CRON INSTALLATION"
echo "=========================================="
echo ""

# Create log directory
if [ ! -d "$LOG_DIR" ]; then
    echo -e "${YELLOW}Creating log directory: $LOG_DIR${NC}"
    mkdir -p "$LOG_DIR"
fi

# Verify script exists
REFRESH_SCRIPT="$SCRIPT_DIR/dashboard_v3_complete_refresh.py"
if [ ! -f "$REFRESH_SCRIPT" ]; then
    echo -e "${RED}❌ ERROR: Script not found: $REFRESH_SCRIPT${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Found refresh script: $REFRESH_SCRIPT${NC}"

# Test script execution
echo ""
echo "Testing script execution..."
if $PYTHON_BIN "$REFRESH_SCRIPT" 2>&1 | grep -q "SUCCESS"; then
    echo -e "${GREEN}✓ Script test passed${NC}"
else
    echo -e "${RED}❌ Script test failed - check logs${NC}"
    exit 1
fi

# Create cron entry
CRON_CMD="*/15 * * * * $PYTHON_BIN $REFRESH_SCRIPT >> $LOG_DIR/dashboard_v3_cron.log 2>&1"

# Check if cron entry already exists
if crontab -l 2>/dev/null | grep -q "dashboard_v3_complete_refresh.py"; then
    echo ""
    echo -e "${YELLOW}⚠️  Dashboard V3 cron job already exists${NC}"
    echo "Current entry:"
    crontab -l | grep "dashboard_v3_complete_refresh.py"
    echo ""
    read -p "Replace existing entry? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove old entry and add new one
        (crontab -l 2>/dev/null | grep -v "dashboard_v3_complete_refresh.py"; echo "$CRON_CMD") | crontab -
        echo -e "${GREEN}✓ Cron job updated${NC}"
    else
        echo "Skipping cron installation"
        exit 0
    fi
else
    # Add new cron entry
    (crontab -l 2>/dev/null; echo "$CRON_CMD") | crontab -
    echo -e "${GREEN}✓ Cron job installed${NC}"
fi

echo ""
echo "=========================================="
echo "INSTALLATION COMPLETE"
echo "=========================================="
echo ""
echo "Schedule: Every 15 minutes (*/15 * * * *)"
echo "Script: $REFRESH_SCRIPT"
echo "Log file: $LOG_DIR/dashboard_v3_cron.log"
echo ""
echo "Active cron jobs:"
crontab -l | grep -v "^#" | grep -v "^$"
echo ""
echo -e "${GREEN}✅ Dashboard V3 will auto-refresh every 15 minutes${NC}"
echo ""
echo "To view logs:"
echo "  tail -f $LOG_DIR/dashboard_v3_cron.log"
echo ""
echo "To remove cron job:"
echo "  crontab -e  # Then delete the dashboard_v3_auto_refresh line"
echo ""
