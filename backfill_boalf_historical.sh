#!/bin/bash

################################################################################
# Historical BOALF Price Backfill Script
# 
# Purpose: Automate derivation of acceptance prices for 2022-2025 period
#          by joining bmrs_boalf + bmrs_bod tables using derive_boalf_prices.py
#
# Coverage: ~46 months (Jan 2022 - Oct 2025)
# Estimate: ~11 million acceptances total
# Runtime: 5-8 minutes/month = 4-6 hours total
#
# Features:
# - Checkpointing: Skips already-processed months
# - Logging: Detailed progress tracking
# - Error handling: Continues on failure with summary
# - Monthly batching: Processes one month at a time
#
# Usage:
#   ./backfill_boalf_historical.sh                    # Process all missing months
#   ./backfill_boalf_historical.sh 2024 2025          # Only 2024-2025
#   ./backfill_boalf_historical.sh --force 2024 01    # Reprocess specific month
#
# Output:
#   logs/boalf_backfill_YYYYMMDD_HHMMSS.log
#   logs/boalf_backfill_summary.txt
################################################################################

set -euo pipefail

# Configuration
PROJECT_ID="inner-cinema-476211-u9"
DATASET="uk_energy_prod"
TABLE="bmrs_boalf_complete"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="${SCRIPT_DIR}/logs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/boalf_backfill_${TIMESTAMP}.log"
SUMMARY_FILE="${LOG_DIR}/boalf_backfill_summary.txt"
CHECKPOINT_FILE="${LOG_DIR}/boalf_backfill_checkpoint.txt"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Parse arguments
FORCE_MODE=0
START_YEAR=2022
END_YEAR=2025
SPECIFIC_YEAR=""
SPECIFIC_MONTH=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --force)
      FORCE_MODE=1
      shift
      ;;
    [0-9][0-9][0-9][0-9])
      if [[ -z "$SPECIFIC_YEAR" ]]; then
        SPECIFIC_YEAR=$1
      else
        SPECIFIC_MONTH=$1
      fi
      shift
      ;;
    *)
      echo "Unknown parameter: $1"
      exit 1
      ;;
  esac
done

# Override years if specific year provided
if [[ -n "$SPECIFIC_YEAR" ]]; then
  START_YEAR=$SPECIFIC_YEAR
  END_YEAR=$SPECIFIC_YEAR
fi

# Logging functions
log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log_error() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $*" | tee -a "$LOG_FILE" >&2
}

# Check if month already processed
is_month_processed() {
  local year=$1
  local month=$2
  
  if [[ $FORCE_MODE -eq 1 ]]; then
    return 1  # Not processed (force rerun)
  fi
  
  if [[ ! -f "$CHECKPOINT_FILE" ]]; then
    return 1  # Not processed
  fi
  
  grep -q "^${year}-${month}$" "$CHECKPOINT_FILE" && return 0 || return 1
}

# Mark month as processed
mark_month_processed() {
  local year=$1
  local month=$2
  echo "${year}-${month}" >> "$CHECKPOINT_FILE"
}

# Get last day of month
get_last_day() {
  local year=$1
  local month=$2
  
  # Use date command to calculate last day
  if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    date -j -v1d -v+1m -v-1d -f "%Y-%m-%d" "${year}-${month}-01" "+%d"
  else
    # Linux
    date -d "${year}-${month}-01 +1 month -1 day" "+%d"
  fi
}

# Process single month
process_month() {
  local year=$1
  local month=$2
  local current_num=$3
  local total_num=$4
  
  local pct=$((100 * current_num / total_num))
  
  log "========================================="
  log "Processing: ${year}-${month} [${current_num}/${total_num} = ${pct}%]"
  log "========================================="
  
  # Calculate date range
  local start_date="${year}-${month}-01"
  local last_day
  last_day=$(get_last_day "$year" "$month")
  local end_date="${year}-${month}-${last_day}"
  
  log "Date range: ${start_date} to ${end_date}"
  
  # Check if already processed
  if is_month_processed "$year" "$month"; then
    log "SKIP: Already processed (use --force to rerun)"
    return 0
  fi
  
  # Run derivation script
  local month_start=$(date +%s)
  
  if python3 "${SCRIPT_DIR}/derive_boalf_prices.py" \
      --start "$start_date" \
      --end "$end_date" \
      2>&1 | tee -a "$LOG_FILE"; then
    
    local month_end=$(date +%s)
    local duration=$((month_end - month_start))
    
    log "✅ SUCCESS: ${year}-${month} completed in ${duration}s"
    mark_month_processed "$year" "$month"
    
    return 0
  else
    local month_end=$(date +%s)
    local duration=$((month_end - month_start))
    
    log_error "❌ FAILED: ${year}-${month} after ${duration}s"
    return 1
  fi
}

# Main execution
main() {
  log "========================================="
  log "BOALF Historical Backfill Starting"
  log "========================================="
  log "Period: ${START_YEAR}-${END_YEAR}"
  log "Force mode: ${FORCE_MODE}"
  log "Target table: ${PROJECT_ID}.${DATASET}.${TABLE}"
  log "Log file: ${LOG_FILE}"
  log ""
  
  # Initialize counters
  local total_months=0
  local processed_months=0
  local skipped_months=0
  local failed_months=0
  local failed_list=()
  
  local script_start=$(date +%s)
  
  # First pass: count total months
  local month_count=0
  for year in $(seq "$START_YEAR" "$END_YEAR"); do
    local start_month=1
    local end_month=12
    
    if [[ -n "$SPECIFIC_MONTH" ]] && [[ "$year" == "$SPECIFIC_YEAR" ]]; then
      start_month=$((10#$SPECIFIC_MONTH))
      end_month=$start_month
    fi
    
    if [[ $year -eq 2025 ]]; then
      local current_month=$(date +%m)
      if [[ $end_month -gt $((10#$current_month)) ]]; then
        end_month=$((10#$current_month))
      fi
    fi
    
    for month in $(seq -f "%02g" "$start_month" "$end_month"); do
      month_count=$((month_count + 1))
    done
  done
  
  log "Total months to process: ${month_count}"
  log ""
  
  # Second pass: process each year and month
  local current_month_num=0
  for year in $(seq "$START_YEAR" "$END_YEAR"); do
    # Determine month range
    local start_month=1
    local end_month=12
    
    # Limit to specific month if provided
    if [[ -n "$SPECIFIC_MONTH" ]] && [[ "$year" == "$SPECIFIC_YEAR" ]]; then
      start_month=$((10#$SPECIFIC_MONTH))
      end_month=$start_month
    fi
    
    # Don't process future months in 2025
    if [[ $year -eq 2025 ]]; then
      local current_month=$(date +%m)
      if [[ $end_month -gt $((10#$current_month)) ]]; then
        end_month=$((10#$current_month))
      fi
    fi
    
    for month in $(seq -f "%02g" "$start_month" "$end_month"); do
      total_months=$((total_months + 1))
      current_month_num=$((current_month_num + 1))
      
      if is_month_processed "$year" "$month" && [[ $FORCE_MODE -eq 0 ]]; then
        local pct=$((100 * current_month_num / month_count))
        log "SKIP: ${year}-${month} [${current_month_num}/${month_count} = ${pct}%] (already processed)"
        skipped_months=$((skipped_months + 1))
        continue
      fi
      
      if process_month "$year" "$month" "$current_month_num" "$month_count"; then
        processed_months=$((processed_months + 1))
      else
        failed_months=$((failed_months + 1))
        failed_list+=("${year}-${month}")
      fi
      
      # Brief pause between months to avoid API throttling
      sleep 2
    done
  done
  
  local script_end=$(date +%s)
  local total_duration=$((script_end - script_start))
  local hours=$((total_duration / 3600))
  local minutes=$(( (total_duration % 3600) / 60 ))
  local seconds=$((total_duration % 60))
  
  # Generate summary
  log ""
  log "========================================="
  log "BACKFILL SUMMARY"
  log "========================================="
  log "Total months in range: ${total_months}"
  log "Processed: ${processed_months}"
  log "Skipped (already done): ${skipped_months}"
  log "Failed: ${failed_months}"
  log "Total runtime: ${hours}h ${minutes}m ${seconds}s"
  
  if [[ $failed_months -gt 0 ]]; then
    log ""
    log "Failed months:"
    for failed in "${failed_list[@]}"; do
      log "  - ${failed}"
    done
  fi
  
  # Write summary to file
  {
    echo "BOALF Historical Backfill Summary"
    echo "Generated: $(date)"
    echo ""
    echo "Period: ${START_YEAR}-${END_YEAR}"
    echo "Total months: ${total_months}"
    echo "Processed: ${processed_months}"
    echo "Skipped: ${skipped_months}"
    echo "Failed: ${failed_months}"
    echo "Runtime: ${hours}h ${minutes}m ${seconds}s"
    echo ""
    if [[ $failed_months -gt 0 ]]; then
      echo "Failed months:"
      for failed in "${failed_list[@]}"; do
        echo "  - ${failed}"
      done
    fi
  } > "$SUMMARY_FILE"
  
  log "Summary written to: ${SUMMARY_FILE}"
  log "========================================="
  
  # Exit with error if any months failed
  if [[ $failed_months -gt 0 ]]; then
    exit 1
  fi
}

# Run main function
main "$@"
