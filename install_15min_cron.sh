#!/bin/bash
# Script to install the 15-minute update cron job

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="$SCRIPT_DIR/cron_update.log"

echo "Setting up 15-minute update cron job..."
echo "Script directory: $SCRIPT_DIR"

# Create a temporary crontab file
TEMP_CRONTAB=$(mktemp)

# Export current crontab
crontab -l > "$TEMP_CRONTAB" 2>/dev/null || echo "# New crontab" > "$TEMP_CRONTAB"

# Check if the job already exists
if grep -q "update_all_data_15min.py" "$TEMP_CRONTAB"; then
    echo "Cron job already exists. Updating..."
    # Remove the existing job
    grep -v "update_all_data_15min.py" "$TEMP_CRONTAB" > "${TEMP_CRONTAB}.new"
    mv "${TEMP_CRONTAB}.new" "$TEMP_CRONTAB"
else
    echo "Adding new cron job..."
fi

# Add the new job to run every 15 minutes
echo "# UK Energy Data 15-minute update - Added $(date)" >> "$TEMP_CRONTAB"
echo "*/15 * * * * cd $SCRIPT_DIR && python update_all_data_15min.py >> $SCRIPT_DIR/15_minute_update_cron.log 2>&1" >> "$TEMP_CRONTAB"

# Install the updated crontab
crontab "$TEMP_CRONTAB"

# Clean up
rm "$TEMP_CRONTAB"

echo "Cron job installed successfully."
echo "The script will run every 15 minutes and log to: $SCRIPT_DIR/15_minute_update_cron.log"
echo
echo "To verify, run: crontab -l"
echo "To test the script without waiting, run: python $SCRIPT_DIR/update_all_data_15min.py"
echo
echo "Done!"
