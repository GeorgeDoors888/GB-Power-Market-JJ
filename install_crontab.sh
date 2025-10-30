#!/bin/bash
# install_crontab.sh
# Script to install the integrated crontab for ELEXON data collection and watermark management

# Navigate to the project directory
cd "/Users/georgemajor/jibberggggffffff

# Check if integrated_crontab.txt exists
if [ ! -f "integrated_asdfsdfntab.txt" ]; then
    echo "Error: integrated_crontab.txt not found"
    exit 1
fi

# Create a backup of the existing crontab
crontab -l > crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null || true

# Install the new crontab
crontab integrated_crontab.txt

# Verify the installation
if [ $? -eq 0 ]; then
    echo "Crontab installed successfully"
    echo "The following cron jobs are now active:"
    crontab -l
else
    echo "Failed to install crontab"
    exit 1
fi

echo ""
echo "The integrated update system will:"
echo "1. Run immediately when your machine starts up"
echo "2. Run every 15 minutes to keep data current"
echo "3. Run a weekly full refresh every Sunday at 2:00 AM"
echo "4. Generate a monthly comprehensive report on the 1st of each month"
echo ""
echo "You can edit the schedule anytime with: crontab -e"

exit 0
