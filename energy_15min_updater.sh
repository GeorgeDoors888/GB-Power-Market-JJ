#!/bin/bash
# 15-Minute Energy Data Automation Script
# This script runs every 15 minutes to update Elexon and NESO data incrementally

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs/automation"
VENV_PATH="${SCRIPT_DIR}/.venv_ingestion"
PYTHON_ENV="${VENV_PATH}/bin"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Log file with timestamp
LOG_FILE="${LOG_DIR}/15min_updates_$(date +%Y%m%d).log"

# Function for logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

log "🚀 Starting 15-minute energy data update cycle"

# Check if virtual environment exists
if [[ ! -d "${VENV_PATH}" ]]; then
    log "❌ Virtual environment not found at ${VENV_PATH}"
    log "Please run setup_environment.sh first"
    exit 1
fi

# Activate virtual environment
source "${PYTHON_ENV}/activate"

# Check if tracker script exists
TRACKER_SCRIPT="${SCRIPT_DIR}/automated_data_tracker.py"
if [[ ! -f "${TRACKER_SCRIPT}" ]]; then
    log "❌ Tracker script not found: ${TRACKER_SCRIPT}"
    exit 1
fi

# Check if ingestion script exists
INGEST_SCRIPT="${SCRIPT_DIR}/ingest_elexon_fixed.py"
if [[ ! -f "${INGEST_SCRIPT}" ]]; then
    log "❌ Ingestion script not found: ${INGEST_SCRIPT}"
    exit 1
fi

# Run the tracker to determine what needs updating
log "📊 Checking what data needs updating (safe mode)..."
TRACKER_SCRIPT="${SCRIPT_DIR}/safe_data_tracker.py"
if [[ ! -f "${TRACKER_SCRIPT}" ]]; then
    log "⚠️  Safe tracker not found, falling back to automated_data_tracker.py"
    TRACKER_SCRIPT="${SCRIPT_DIR}/automated_data_tracker.py"
fi

TRACKER_OUTPUT=$(python "${TRACKER_SCRIPT}" 2>&1)
TRACKER_EXIT_CODE=$?

if [[ ${TRACKER_EXIT_CODE} -ne 0 ]]; then
    log "❌ Tracker script failed:"
    log "${TRACKER_OUTPUT}"
    exit 1
fi

log "Tracker output: ${TRACKER_OUTPUT}"

# Parse tracker output to determine action
ACTION=$(echo "${TRACKER_OUTPUT}" | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('action', 'unknown'))
except:
    print('unknown')
")

log "📋 Action determined: ${ACTION}"

case "${ACTION}" in
    "elexon_update")
        log "🔄 Starting incremental Elexon data update..."

        # Extract date range from tracker output
        START_DATE=$(echo "${TRACKER_OUTPUT}" | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('start_date', ''))
except:
    print('')
")

        END_DATE=$(echo "${TRACKER_OUTPUT}" | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('end_date', ''))
except:
    print('')
")

        if [[ -z "${START_DATE}" || -z "${END_DATE}" ]]; then
            log "❌ Could not determine date range for update"
            exit 1
        fi

        log "📅 Date range: ${START_DATE} to ${END_DATE}"

        # Run incremental Elexon ingestion
        log "🚀 Running Elexon ingestion..."
        INGEST_OUTPUT=$(python "${INGEST_SCRIPT}" \
            --start "${START_DATE}" \
            --end "${END_DATE}" \
            --log-level INFO \
            --skip-existing \
            2>&1)
        INGEST_EXIT_CODE=$?

        if [[ ${INGEST_EXIT_CODE} -eq 0 ]]; then
            log "✅ Elexon ingestion completed successfully"
            log "Updating tracker with success status..."

            # Update tracker with success
            python -c "
from automated_data_tracker import DataTracker
from datetime import datetime, timezone
tracker = DataTracker()
tracker.update_ingestion_time('ELEXON', 'ALL', datetime.now(timezone.utc), 'SUCCESS')
" 2>&1 | tee -a "${LOG_FILE}"

        else
            log "❌ Elexon ingestion failed with exit code ${INGEST_EXIT_CODE}"
            log "Error output:"
            log "${INGEST_OUTPUT}"

            # Update tracker with failure
            python -c "
from automated_data_tracker import DataTracker
from datetime import datetime, timezone
tracker = DataTracker()
tracker.update_ingestion_time('ELEXON', 'ALL', datetime.now(timezone.utc), 'FAILED')
" 2>&1 | tee -a "${LOG_FILE}"

            exit 1
        fi
        ;;

    "skip")
        REASON=$(echo "${TRACKER_OUTPUT}" | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('reason', 'unknown'))
except:
    print('unknown')
")
        log "⏭️  Skipping update: ${REASON}"
        ;;

    "error")
        ERROR_MSG=$(echo "${TRACKER_OUTPUT}" | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('error', 'unknown error'))
except:
    print('unknown error')
")
        log "❌ Tracker reported error: ${ERROR_MSG}"
        exit 1
        ;;

    *)
        log "❓ Unknown action: ${ACTION}"
        log "Full tracker output: ${TRACKER_OUTPUT}"
        exit 1
        ;;
esac

# NESO data update logic
log "🔄 Checking NESO data updates..."
NESO_SCRIPT="${SCRIPT_DIR}/neso_data_updater.py"
if [[ -f "${NESO_SCRIPT}" ]]; then
    log "🚀 Running NESO data update..."
    NESO_OUTPUT=$(python "${NESO_SCRIPT}" 2>&1)
    NESO_EXIT_CODE=$?

    if [[ ${NESO_EXIT_CODE} -eq 0 ]]; then
        log "✅ NESO data update completed successfully"
        log "NESO output: ${NESO_OUTPUT}"
    else
        log "⚠️  NESO data update had issues (exit code ${NESO_EXIT_CODE})"
        log "NESO output: ${NESO_OUTPUT}"
    fi
else
    log "⏭️  NESO updater script not found, skipping NESO updates"
fi

# Cleanup old logs (keep last 7 days)
find "${LOG_DIR}" -name "*.log" -mtime +7 -delete 2>/dev/null || true

log "✅ 15-minute update cycle completed successfully"
