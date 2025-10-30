#!/bin/bash
# Setup 15-Minute Energy Data Automation
# This script sets up the cron job for automated 15-minute updates

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UPDATER_SCRIPT="${SCRIPT_DIR}/energy_15min_updater.sh"

echo "🔧 Setting up 15-minute energy data automation..."

# Check if updater script exists and is executable
if [[ ! -f "${UPDATER_SCRIPT}" ]]; then
    echo "❌ Updater script not found: ${UPDATER_SCRIPT}"
    exit 1
fi

if [[ ! -x "${UPDATER_SCRIPT}" ]]; then
    echo "Making updater script executable..."
    chmod +x "${UPDATER_SCRIPT}"
fi

# Create logs directory
mkdir -p "${SCRIPT_DIR}/logs/automation"

echo "📋 Current cron jobs:"
crontab -l 2>/dev/null || echo "No existing cron jobs found"

echo ""
echo "🕐 Adding 15-minute energy data update cron job..."

# Create new cron entry
CRON_ENTRY="*/15 * * * * ${UPDATER_SCRIPT} >> ${SCRIPT_DIR}/logs/automation/cron_output.log 2>&1"

# Get existing crontab
EXISTING_CRON=$(crontab -l 2>/dev/null || echo "")

# Check if our cron job already exists
if echo "${EXISTING_CRON}" | grep -q "${UPDATER_SCRIPT}"; then
    echo "⚠️  Cron job already exists for ${UPDATER_SCRIPT}"
    echo "Current entry:"
    echo "${EXISTING_CRON}" | grep "${UPDATER_SCRIPT}"
    echo ""
    echo "Do you want to replace it? (y/N)"
    read -r REPLACE

    if [[ "${REPLACE}" =~ ^[Yy]$ ]]; then
        # Remove existing entry and add new one
        NEW_CRON=$(echo "${EXISTING_CRON}" | grep -v "${UPDATER_SCRIPT}")
        echo "${NEW_CRON}" | echo "${CRON_ENTRY}" | crontab -
        echo "✅ Cron job updated successfully"
    else
        echo "⏭️  Keeping existing cron job"
    fi
else
    # Add new entry to existing cron
    (echo "${EXISTING_CRON}"; echo "${CRON_ENTRY}") | crontab -
    echo "✅ Cron job added successfully"
fi

echo ""
echo "📋 Updated cron jobs:"
crontab -l

echo ""
echo "🎉 Setup completed!"
echo ""
echo "The system will now:"
echo "  • Check for updates every 15 minutes"
echo "  • Only ingest missing data since last update"
echo "  • Track progress in Google Sheets"
echo "  • Log all activities to ${SCRIPT_DIR}/logs/automation/"
echo ""
echo "To manually test the system:"
echo "  ${UPDATER_SCRIPT}"
echo ""
echo "To view logs:"
echo "  tail -f ${SCRIPT_DIR}/logs/automation/15min_updates_$(date +%Y%m%d).log"
echo ""
echo "To disable automation:"
echo "  crontab -e  # then comment out or delete the line with ${UPDATER_SCRIPT}"
