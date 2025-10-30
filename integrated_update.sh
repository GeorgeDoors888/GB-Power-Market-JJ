#!/bin/bash
# integrated_update.sh
# This script runs both the ELEXON data ingestion and watermark management
# It can be run both on system startup and via cron scheduling

# Navigate to the project directory
cd "/Users/georgemajor/jibber-jabber 24 august 2025 big bop"

# Log file setup
LOG_DIR="logs"
mkdir -p "$LOG_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$LOG_DIR/integrated_update_$TIMESTAMP.log"

# Start logging
echo "==== Integrated ELEXON Data Update and Watermark Management ====" > "$LOG_FILE"
echo "Started: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Activate the virtual environment if needed
source .venv/bin/activate

# Set up the date range (from 1 day ago to now)
START_DATE=$(date -v-1d +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)

# 1. Run the ELEXON ingestion script (high-frequency datasets)
echo "Running ELEXON data ingestion..." >> "$LOG_FILE"
python ingest_elexon_fixed.py --start "${START_DATE}" --end "${END_DATE}" --only FREQ,FUELINST,MIP,MELS,MILS,BOD,BOALF,PN,QPN --include-offline --log-level INFO >> "$LOG_FILE" 2>&1
ELEXON_EXIT_CODE=$?

# Check if ELEXON ingestion was successful
if [ $ELEXON_EXIT_CODE -eq 0 ]; then
    echo "ELEXON data ingestion completed successfully." >> "$LOG_FILE"
else
    echo "ELEXON data ingestion failed with exit code $ELEXON_EXIT_CODE." >> "$LOG_FILE"
fi

# 2. Generate updated watermarks file for high-frequency tables
echo "Generating updated watermarks for high-frequency tables..." >> "$LOG_FILE"
python tools/bq_watermarks.py --project jibber-jabber-knowledge --dataset uk_energy_insights --tables bmrs_bod,bmrs_boalf,bmrs_mip,bmrs_mels,bmrs_mils,bmrs_freq,bmrs_fuelinst,bmrs_pn,bmrs_qpn --out "watermarks_high_freq_$TIMESTAMP.json" >> "$LOG_FILE" 2>&1
WATERMARKS_EXIT_CODE=$?

# Check if watermarks generation was successful
if [ $WATERMARKS_EXIT_CODE -eq 0 ]; then
    echo "Watermarks generation completed successfully." >> "$LOG_FILE"
else
    echo "Watermarks generation failed with exit code $WATERMARKS_EXIT_CODE." >> "$LOG_FILE"
fi

# 3. Run watermark management script to keep only the most recent files
echo "Running watermark file cleanup..." >> "$LOG_FILE"
bash manage_watermarks.sh >> "$LOG_FILE" 2>&1
CLEANUP_EXIT_CODE=$?

# Check if cleanup was successful
if [ $CLEANUP_EXIT_CODE -eq 0 ]; then
    echo "Watermark cleanup completed successfully." >> "$LOG_FILE"
else
    echo "Watermark cleanup failed with exit code $CLEANUP_EXIT_CODE." >> "$LOG_FILE"
fi

# 4. Run watermark analysis to generate a fresh report
echo "Generating watermark analysis report..." >> "$LOG_FILE"
python analyze_watermarks.py --output "watermark_analysis_$TIMESTAMP.md" >> "$LOG_FILE" 2>&1
ANALYSIS_EXIT_CODE=$?

# Check if analysis was successful
if [ $ANALYSIS_EXIT_CODE -eq 0 ]; then
    echo "Watermark analysis completed successfully." >> "$LOG_FILE"
else
    echo "Watermark analysis failed with exit code $ANALYSIS_EXIT_CODE." >> "$LOG_FILE"
fi

# Completion summary
echo "" >> "$LOG_FILE"
echo "==== Integration Summary ====" >> "$LOG_FILE"
echo "ELEXON Ingestion: $([ $ELEXON_EXIT_CODE -eq 0 ] && echo 'SUCCESS' || echo 'FAILED')" >> "$LOG_FILE"
echo "Watermarks Generation: $([ $WATERMARKS_EXIT_CODE -eq 0 ] && echo 'SUCCESS' || echo 'FAILED')" >> "$LOG_FILE"
echo "Watermarks Cleanup: $([ $CLEANUP_EXIT_CODE -eq 0 ] && echo 'SUCCESS' || echo 'FAILED')" >> "$LOG_FILE"
echo "Watermarks Analysis: $([ $ANALYSIS_EXIT_CODE -eq 0 ] && echo 'SUCCESS' || echo 'FAILED')" >> "$LOG_FILE"
echo "Completed: $(date)" >> "$LOG_FILE"

# Keep only the 5 most recent log files
find "$LOG_DIR" -name "integrated_update_*.log" -type f -print0 | xargs -0 ls -t | tail -n +6 | xargs rm -f 2>/dev/null

exit 0
