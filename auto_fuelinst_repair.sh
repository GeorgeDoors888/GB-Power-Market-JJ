#!/bin/bash
# Auto FUELINST Repair Script
# Waits for 2023 ingestion to complete, then repairs FUELINST for all years

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="fuelinst_repair_$(date +%Y%m%d_%H%M%S).log"
VENV_PYTHON=".venv/bin/python"

echo "======================================================================"
echo "🔧 FUELINST Repair Script Started: $(date)"
echo "======================================================================"
echo ""
echo "This script will:"
echo "  1. Monitor PID 16445 (2023 auto-starter)"
echo "  2. Wait for 2023 ingestion to complete (~7:14 PM)"
echo "  3. Repair FUELINST for 2023, 2024, and 2025"
echo "  4. Use new config: 7d chunks, 30-frame batching, 5s delays"
echo ""
echo "Log file: $LOG_FILE"
echo "======================================================================"
echo ""

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Monitor the 2023 auto-starter
log "⏳ Waiting for 2023 ingestion to complete (monitoring PID 16445)..."

while kill -0 16445 2>/dev/null; do
    sleep 300  # Check every 5 minutes
    log "   Still running... checking again in 5 minutes"
done

log "✅ 2023 auto-starter (PID 16445) has completed!"
log ""

# Wait an additional 5 minutes to ensure 2023 ingestion itself has finished
log "⏳ Waiting 5 minutes to ensure 2023 ingestion has fully completed..."
sleep 300

log "======================================================================"
log "🔧 Starting FUELINST Repair for All Years"
log "======================================================================"
log ""

# Function to run FUELINST ingestion for a specific year
run_fuelinst_year() {
    local YEAR=$1
    local START_DATE="${YEAR}-01-01"
    local END_DATE="${YEAR}-12-31"
    
    log "📅 Repairing FUELINST, FREQ, FUELHH for $YEAR ($START_DATE to $END_DATE)..."
    log "   Note: These datasets failed due to rate limits in main run"
    log "   Using NEW config: 7d chunks, 30-frame batch, 5s delays"
    
    $VENV_PYTHON ingest_elexon_fixed.py \
        --start "$START_DATE" \
        --end "$END_DATE" \
        --only FUELINST,FREQ,FUELHH \
        2>&1 | tee -a "$LOG_FILE"
    
    local EXIT_CODE=${PIPESTATUS[0]}
    
    if [ $EXIT_CODE -eq 0 ]; then
        log "✅ Successfully completed FUELINST/FREQ/FUELHH repair for $YEAR"
    else
        log "❌ FUELINST/FREQ/FUELHH repair for $YEAR failed with exit code $EXIT_CODE"
    fi
    
    log ""
    return $EXIT_CODE
}

# Repair each year in sequence
log "=" * 70
log "REPAIR STRATEGY:"
log "=" * 70
log "2023: Load ONLY FUELINST, FREQ, FUELHH (other 50 loaded by main run)"
log "2024: Load ONLY FUELINST, FREQ, FUELHH (other 50 loaded by main run)"
log "2025: Load ALL datasets EXCEPT BOD (only BOD exists from original run)"
log "=" * 70
log ""

# Start with 2023 (just completed, might have rate limit issues on 3 datasets)
run_fuelinst_year 2023

# Then 2024 (definitely had rate limit issues on 3 datasets)
run_fuelinst_year 2024

# Then 2025 Jan-Aug (catastrophic failure - only BOD exists, need to load 52 others)
log "📅 Repairing ALL DATASETS for 2025 (Jan-Aug) EXCEPT BOD..."
log "   Original 2025 run only loaded BOD (1/53 datasets)"
log "   BOD has 73.2M rows - excluding to prevent duplicates"
log "   Will load 52 missing datasets with NEW config"
$VENV_PYTHON ingest_elexon_fixed.py \
    --start "2025-01-01" \
    --end "2025-08-31" \
    --exclude BOD \
    2>&1 | tee -a "$LOG_FILE"

FINAL_EXIT_CODE=${PIPESTATUS[0]}

if [ $FINAL_EXIT_CODE -eq 0 ]; then
    log "✅ Successfully completed FUELINST repair for 2025 (Jan-Aug)"
else
    log "❌ FUELINST repair for 2025 failed with exit code $FINAL_EXIT_CODE"
fi

log ""
log "======================================================================"
log "🎉 FUELINST Repair Script Completed: $(date)"
log "======================================================================"
log ""
log "📊 Verification queries to run in BigQuery:"
log ""
log "-- Check 2023 FUELINST data:"
log "SELECT EXTRACT(MONTH FROM startTime) as month, COUNT(*) as rows"
log "FROM \`uk_energy_prod.bmrs_fuelinst\`"
log "WHERE EXTRACT(YEAR FROM startTime) = 2023"
log "GROUP BY month ORDER BY month;"
log ""
log "-- Check 2024 FUELINST data:"
log "SELECT EXTRACT(MONTH FROM startTime) as month, COUNT(*) as rows"
log "FROM \`uk_energy_prod.bmrs_fuelinst\`"
log "WHERE EXTRACT(YEAR FROM startTime) = 2024"
log "GROUP BY month ORDER BY month;"
log ""
log "-- Check 2025 FUELINST data:"
log "SELECT EXTRACT(MONTH FROM startTime) as month, COUNT(*) as rows"
log "FROM \`uk_energy_prod.bmrs_fuelinst\`"
log "WHERE EXTRACT(YEAR FROM startTime) = 2025"
log "GROUP BY month ORDER BY month;"
log ""
log "Log saved to: $LOG_FILE"

# Exit with the status of the last operation
exit $FINAL_EXIT_CODE
