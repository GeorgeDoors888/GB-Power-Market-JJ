#!/bin/bash
# Download remaining ERA5 farms (runs daily via cron)
# Schedule: 0 3 * * * (3 AM UTC daily)

cd /home/george/GB-Power-Market-JJ
LOG_FILE="logs/era5_download_with_gusts_$(date +\%Y\%m\%d).log"

echo "========================================" | tee -a "$LOG_FILE"
echo "ERA5 Download (with gusts) - $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Set environment
export GOOGLE_APPLICATION_CREDENTIALS="/home/george/GB-Power-Market-JJ/inner-cinema-credentials.json"

# Run download script
python3 download_era5_with_gusts.py 2>&1 | tee -a "$LOG_FILE"

echo "" | tee -a "$LOG_FILE"
echo "Download complete - $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
