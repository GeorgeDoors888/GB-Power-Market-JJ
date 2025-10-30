#!/bin/bash
# Energy Data 15-Minute Update Orchestrator
# This script coordinates BMRS and NESO data updates every 15 minutes
# Usage: Add to crontab: */15 * * * * /path/to/energy_data_updater.sh

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
ENV_DIR="${SCRIPT_DIR}/.venv_ingestion"
GSHEETS_ENV_DIR="${SCRIPT_DIR}/gsheets_env"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
LOG_FILE="${LOG_DIR}/energy_update_${TIMESTAMP}.log"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "${LOG_FILE}"
}

# Error handling
handle_error() {
    local exit_code=$1
    local line_number=$2
    log "ERROR: Command failed with exit code ${exit_code} on line ${line_number}"
    send_alert "Energy Data Update Failed" "Update failed at line ${line_number} with exit code ${exit_code}. Check log: ${LOG_FILE}"
    exit ${exit_code}
}

trap 'handle_error $? $LINENO' ERR

# Alert function (extend with Slack/email as needed)
send_alert() {
    local subject="$1"
    local message="$2"
    log "ALERT: ${subject} - ${message}"
    # TODO: Add email/Slack notification here
    # echo "${message}" | mail -s "${subject}" admin@example.com
}

# Main update function
main() {
    log "Starting 15-minute energy data update cycle"

    local start_time=$(date +%s)
    local current_hour=$(date '+%H')
    local current_minute=$(date '+%M')

    # Determine update schedule based on time
    local run_high_priority=true
    local run_standard_priority=false
    local run_daily_priority=false

    # Standard priority: Every 30 minutes (offset by 15)
    if [[ $((10#${current_minute} % 30)) -eq 15 ]]; then
        run_standard_priority=true
        log "Standard priority update scheduled (30-min cycle, offset)"
    fi

    # Daily priority: Once per day at 06:00
    if [[ "${current_hour}" == "06" && "${current_minute}" == "00" ]]; then
        run_daily_priority=true
        log "Daily priority update scheduled (06:00)"
    fi

    # Always run high priority
    log "High priority update scheduled (every 15 min)"

    # Execute updates in parallel where possible
    local pids=()

    # High Priority Updates (every 15 minutes)
    if [[ "${run_high_priority}" == "true" ]]; then
        log "Starting high priority BMRS updates..."
        python "${SCRIPT_DIR}/update_bmrs_priority.py" --log-file "${LOG_FILE}" &
        pids+=($!)
    fi

    # Standard Priority Updates (every 30 minutes, offset)
    if [[ "${run_standard_priority}" == "true" ]]; then
        log "Starting standard priority BMRS updates..."
        python "${SCRIPT_DIR}/update_bmrs_standard.py" --log-file "${LOG_FILE}" &
        pids+=($!)
    fi

    # Daily Priority Updates (once per day)
    if [[ "${run_daily_priority}" == "true" ]]; then
        log "Starting daily BMRS and NESO updates..."
        python "${SCRIPT_DIR}/update_bmrs_daily.py" --log-file "${LOG_FILE}" &
        pids+=($!)

        python "${SCRIPT_DIR}/update_neso_stor.py" --log-file "${LOG_FILE}" &
        pids+=($!)
    fi

    # Wait for all background processes
    local failed_jobs=0
    for pid in "${pids[@]}"; do
        if ! wait "${pid}"; then
            log "WARNING: Background job with PID ${pid} failed"
            failed_jobs=$((failed_jobs + 1))
        fi
    done

    # Post-update validation
    log "Running post-update data validation..."
    python "${SCRIPT_DIR}/validate_data_quality.py" --log-file "${LOG_FILE}"

    # Calculate duration and send status
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    if [[ ${failed_jobs} -eq 0 ]]; then
        log "✅ Update cycle completed successfully in ${duration}s"
        send_status_report "success" "${duration}" "${failed_jobs}"
    else
        log "⚠️  Update cycle completed with ${failed_jobs} failed jobs in ${duration}s"
        send_status_report "partial" "${duration}" "${failed_jobs}"
    fi

    # Cleanup old logs (keep last 48 hours)
    find "${LOG_DIR}" -name "energy_update_*.log" -mtime +2 -delete 2>/dev/null || true

    log "15-minute update cycle finished"
}

# Status reporting function
send_status_report() {
    local status="$1"
    local duration="$2"
    local failed_jobs="$3"

    python "${SCRIPT_DIR}/send_status_report.py" \
        --status "${status}" \
        --duration "${duration}" \
        --failed-jobs "${failed_jobs}" \
        --log-file "${LOG_FILE}" || true
}

# Pre-flight checks
preflight_checks() {
    log "Running pre-flight checks..."

    # Check virtual environments
    if [[ ! -d "${ENV_DIR}" ]]; then
        log "ERROR: BMRS virtual environment not found at ${ENV_DIR}"
        exit 1
    fi

    if [[ ! -d "${GSHEETS_ENV_DIR}" ]]; then
        log "ERROR: NESO virtual environment not found at ${GSHEETS_ENV_DIR}"
        exit 1
    fi

    # Check required scripts exist
    local required_scripts=(
        "update_bmrs_priority.py"
        "update_bmrs_standard.py"
        "update_bmrs_daily.py"
        "update_neso_stor.py"
        "validate_data_quality.py"
        "send_status_report.py"
    )

    for script in "${required_scripts[@]}"; do
        if [[ ! -f "${SCRIPT_DIR}/${script}" ]]; then
            log "ERROR: Required script not found: ${script}"
            exit 1
        fi
    done

    # Check BigQuery connectivity
    if ! command -v bq &> /dev/null; then
        log "ERROR: BigQuery CLI tool 'bq' not found"
        exit 1
    fi

    # Test BigQuery access
    if ! bq ls --project_id=jibber-jabber-knowledge &>/dev/null; then
        log "ERROR: Cannot access BigQuery project jibber-jabber-knowledge"
        exit 1
    fi

    log "✅ Pre-flight checks passed"
}

# Lock file management to prevent overlapping runs
LOCK_FILE="${SCRIPT_DIR}/.energy_update.lock"

acquire_lock() {
    if [[ -f "${LOCK_FILE}" ]]; then
        local lock_pid=$(cat "${LOCK_FILE}")
        if kill -0 "${lock_pid}" 2>/dev/null; then
            log "ERROR: Another update process is running (PID: ${lock_pid})"
            exit 1
        else
            log "WARNING: Stale lock file found, removing..."
            rm -f "${LOCK_FILE}"
        fi
    fi

    echo $$ > "${LOCK_FILE}"
    log "Acquired update lock (PID: $$)"
}

release_lock() {
    rm -f "${LOCK_FILE}"
    log "Released update lock"
}

# Cleanup on exit
cleanup() {
    release_lock
}

trap cleanup EXIT

# Main execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    acquire_lock
    preflight_checks
    main "$@"
fi
