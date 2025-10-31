#!/bin/bash

# IRIS JSON Files Cleanup Script
# Deletes large unwanted datasets and optionally all processed files
# Usage: ./iris_cleanup_files.sh [--all|--unwanted|--dry-run]

set -e

IRIS_DATA_DIR="iris-clients/python/iris_data"
LOG_FILE="iris_cleanup.log"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🗑️  IRIS JSON Files Cleanup Script" | tee -a "$LOG_FILE"
echo "===================================" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Check if IRIS data directory exists
if [ ! -d "$IRIS_DATA_DIR" ]; then
    echo "❌ Error: IRIS data directory not found: $IRIS_DATA_DIR" | tee -a "$LOG_FILE"
    exit 1
fi

# Parse command line arguments
MODE="${1:---unwanted}"
DRY_RUN=false

if [ "$MODE" = "--dry-run" ] || [ "$2" = "--dry-run" ]; then
    DRY_RUN=true
    echo "🔍 DRY RUN MODE - No files will be deleted" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
fi

# Unwanted datasets (large datasets we don't have tables for)
# These are forecasts and minor datasets we're not currently tracking
UNWANTED_DATASETS=(
    "UOU2T3YW"      # Output Usable 3-year weekly (433 MB!)
    "UOU2T14D"      # Output Usable 14-day daily (36 MB)
    "DISPTAV"       # Disputed Availability (78 MB)
    "BOAV"          # Bid-Offer Availability (61 MB)
    "ISPSTACK"      # ISEM Stack (24 MB)
    "PN"            # Physical Notifications (36 MB)
    "QPN"           # Quiescent Physical Notifications (33 MB)
    "NETBSAD"       # Net Balancing Services Adjustment Data
    "INDGEN"        # Indicated Generation
    "INDDEM"        # Indicated Demand
    "LOLPDRM"       # Loss of Load Probability and De-rated Margin
    "TSDF"          # Transmission System Demand Forecast
    "ITSDO"         # Initial Transmission System Demand Outturn
    "MELNGC"        # MEL for NGC
    "MILNGC"        # MIL for NGC
    "SEL"           # Stable Export Limit
    "SIL"           # Stable Import Limit
    "NONBM"         # Non-BM STOR
    "DISBSAD"       # Disaggregated Balancing Services Adjustment Data
    "DETSYSPRICES"  # Detailed System Prices
    "CDN"           # Credit Default Notice
    "SYSWARN"       # System Warnings
)

# Datasets we KEEP (have tables for these)
KEEP_DATASETS=(
    "BOALF"
    "BOD"
    "MILS"
    "MELS"
    "FREQ"
    "FUELINST"
    "REMIT"
    "MID"
    "BEB"
)

function delete_dataset() {
    local dataset=$1
    local dataset_path="$IRIS_DATA_DIR/$dataset"
    
    if [ ! -d "$dataset_path" ]; then
        echo "  ⏭️  $dataset - Not found, skipping" | tee -a "$LOG_FILE"
        return
    fi
    
    local file_count=$(find "$dataset_path" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    local size=$(du -sh "$dataset_path" 2>/dev/null | awk '{print $1}')
    
    if [ "$DRY_RUN" = true ]; then
        echo "  🔍 Would delete: $dataset ($file_count files, $size)" | tee -a "$LOG_FILE"
    else
        echo "  🗑️  Deleting: $dataset ($file_count files, $size)" | tee -a "$LOG_FILE"
        rm -rf "$dataset_path"
        echo "    ✅ Deleted" | tee -a "$LOG_FILE"
    fi
}

function show_current_status() {
    echo "📊 Current Status:" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    local total_files=$(find "$IRIS_DATA_DIR" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    local total_size=$(du -sh "$IRIS_DATA_DIR" 2>/dev/null | awk '{print $1}')
    
    echo "Total: $total_files files, $total_size" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "Top 15 datasets by size:" | tee -a "$LOG_FILE"
    
    for dir in "$IRIS_DATA_DIR"/*; do
        if [ -d "$dir" ]; then
            local dataset=$(basename "$dir")
            local size=$(du -sh "$dir" 2>/dev/null | awk '{print $1}')
            local count=$(find "$dir" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
            
            # Check if it's a kept dataset
            local status="❌"
            for keep in "${KEEP_DATASETS[@]}"; do
                if [ "$dataset" = "$keep" ]; then
                    status="✅"
                    break
                fi
            done
            
            echo "$status $size - $dataset ($count files)"
        fi
    done | sort -k2 -hr | head -15 | tee -a "$LOG_FILE"
    
    echo "" | tee -a "$LOG_FILE"
}

# Show current status
show_current_status

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

if [ "$MODE" = "--unwanted" ]; then
    echo "🎯 Mode: Delete unwanted datasets only" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "Deleting large datasets we don't have BigQuery tables for:" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    for dataset in "${UNWANTED_DATASETS[@]}"; do
        delete_dataset "$dataset"
    done
    
elif [ "$MODE" = "--all" ]; then
    echo "🎯 Mode: Delete ALL datasets (except current processing)" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "⚠️  WARNING: This will delete files for datasets WITH tables!" | tee -a "$LOG_FILE"
    echo "   Files will be re-downloaded from IRIS if needed." | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    if [ "$DRY_RUN" = false ]; then
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo "❌ Cancelled" | tee -a "$LOG_FILE"
            exit 0
        fi
    fi
    
    echo "Deleting all dataset directories:" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    for dir in "$IRIS_DATA_DIR"/*; do
        if [ -d "$dir" ]; then
            dataset=$(basename "$dir")
            delete_dataset "$dataset"
        fi
    done
    
else
    echo "❌ Invalid mode: $MODE" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "Usage: $0 [--all|--unwanted|--dry-run]" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "Modes:" | tee -a "$LOG_FILE"
    echo "  --unwanted  : Delete only large unwanted datasets (default)" | tee -a "$LOG_FILE"
    echo "  --all       : Delete ALL datasets (requires confirmation)" | tee -a "$LOG_FILE"
    echo "  --dry-run   : Show what would be deleted without deleting" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    echo "Examples:" | tee -a "$LOG_FILE"
    echo "  $0                    # Delete unwanted datasets" | tee -a "$LOG_FILE"
    echo "  $0 --dry-run          # Preview what would be deleted" | tee -a "$LOG_FILE"
    echo "  $0 --unwanted         # Delete unwanted datasets" | tee -a "$LOG_FILE"
    echo "  $0 --all              # Delete ALL datasets (with confirmation)" | tee -a "$LOG_FILE"
    exit 1
fi

echo "" | tee -a "$LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Show final status
if [ "$DRY_RUN" = false ]; then
    echo "📊 After Cleanup:" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    show_current_status
fi

echo "✅ Cleanup complete!" | tee -a "$LOG_FILE"
echo "Finished: $(date)" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
echo "Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"
