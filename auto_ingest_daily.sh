#!/bin/bash
#
# Automated Daily Ingestion Script for GB Power Market Data
# Runs every 15 minutes to fetch latest data from Elexon BMRS API
#
# Setup:
#   chmod +x auto_ingest_daily.sh
#   crontab -e
#   Add: */15 * * * * /home/george/GB-Power-Market-JJ/auto_ingest_daily.sh >> /home/george/GB-Power-Market-JJ/logs/auto_ingest.log 2>&1
#

set -e  # Exit on error

# Configuration
PROJECT_DIR="/home/george/GB-Power-Market-JJ"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/auto_ingest_$(date +%Y%m%d).log"
PYTHON_BIN="python3"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Log function
log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "🚀 Starting Auto Ingestion"
log "=========================================="

# Change to project directory
cd "$PROJECT_DIR" || exit 1

# Set up Google Cloud credentials
export GOOGLE_APPLICATION_CREDENTIALS="$PROJECT_DIR/inner-cinema-credentials.json"

# Calculate date range (yesterday to today to catch any lag)
YESTERDAY=$(date -d "yesterday" +%Y-%m-%d)
TODAY=$(date +%Y-%m-%d)

log "📅 Date range: $YESTERDAY to $TODAY"

# Priority datasets for real-time updates
PRIORITY_DATASETS="BOALF,BOD,COSTS,FUELINST,FREQ,MID,REMIT"

log "📊 Datasets: $PRIORITY_DATASETS"

# Run ingestion for each priority dataset
IFS=',' read -ra DATASETS <<< "$PRIORITY_DATASETS"
for DATASET in "${DATASETS[@]}"; do
    log "🔄 Processing $DATASET..."

    # Use the custom backfill script for BOALF (proven working)
    if [ "$DATASET" == "BOALF" ]; then
        # Modify GAP_START and GAP_END in backfill script for daily run
        # For now, skip BOALF in auto mode (use backfill manually)
        log "⏭️  Skipping BOALF (use backfill_boalf_gap.py manually)"
        continue
    fi

    # For other datasets, use curl + BigQuery direct insert
    # This requires creating dataset-specific ingestion scripts
    log "⚠️  $DATASET ingestion not yet implemented"
done

# Special handling for REMIT (already has dedicated script)
log "🔄 Processing REMIT via dedicated script..."
if [ -f "$PROJECT_DIR/ingest_remit_realtime.py" ]; then
    $PYTHON_BIN "$PROJECT_DIR/ingest_remit_realtime.py" --start "$YESTERDAY" --end "$TODAY" || \
        log "❌ REMIT ingestion failed"
else
    log "⚠️  ingest_remit_realtime.py not found, skipping REMIT"
fi

log "✅ Auto ingestion complete"
log "==========================================\n"
