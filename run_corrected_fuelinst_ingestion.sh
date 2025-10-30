#!/bin/bash
# CORRECTED FUELINST Ingestion - Using Insights API
# This script runs the repairs with the FIXED code that uses the correct API endpoint

set -e

PYTHON=".venv/bin/python"
SCRIPT="ingest_elexon_fixed.py"
LOG_DIR="logs_20251028_123449"

echo "======================================================================"
echo "CORRECTED FUELINST INGESTION - Using Insights API"
echo "======================================================================"
echo "Started: $(date)"
echo ""
echo "Code fix: FUELINST now uses /generation/actual/per-type (Insights API)"
echo "Previous issue: Was using /datasets/FUELINST (live data only)"
echo ""
echo "Timeline:"
echo "  [1/3] 2023 FUELINST/FUELHH: ~30 minutes"
echo "  [2/3] 2024 FUELINST/FUELHH: ~30 minutes"
echo "  [3/3] 2025 FUELINST/FUELHH: ~25 minutes"
echo "  Total: ~85 minutes"
echo "======================================================================"
echo ""

# Run 2023 FUELINST (CORRECTED - using Insights API now)
echo "[1/3] Starting 2023 FUELINST repair (CORRECTED)..."
echo "Start: $(date)"
$PYTHON $SCRIPT --start 2023-01-01 --end 2023-12-31 --only FUELINST,FUELHH \
    > ${LOG_DIR}/2023_fuelinst_corrected.log 2>&1

echo "✅ 2023 FUELINST completed at $(date)"
echo ""

# Run 2024 FUELINST (CORRECTED - using Insights API now)
echo "[2/3] Starting 2024 FUELINST repair (CORRECTED)..."
echo "Start: $(date)"
$PYTHON $SCRIPT --start 2024-01-01 --end 2024-12-31 --only FUELINST,FUELHH \
    > ${LOG_DIR}/2024_fuelinst_corrected.log 2>&1

echo "✅ 2024 FUELINST completed at $(date)"
echo ""

# Run 2025 FUELINST (CORRECTED - using Insights API now)
echo "[3/3] Starting 2025 FUELINST repair (CORRECTED)..."
echo "Start: $(date)"
$PYTHON $SCRIPT --start 2025-01-01 --end 2025-10-28 --only FUELINST,FUELHH \
    > ${LOG_DIR}/2025_fuelinst_corrected.log 2>&1

echo "✅ 2025 FUELINST completed at $(date)"
echo ""

echo "======================================================================"
echo "ALL CORRECTED FUELINST INGESTION COMPLETE!"
echo "======================================================================"

# Show summary
echo ""
echo "Summary:"
grep -c "Successfully loaded.*fuelinst" ${LOG_DIR}/2023_fuelinst_corrected.log 2>/dev/null | xargs echo "  2023 FUELINST loads:" || echo "  2023: Check log"
grep -c "Successfully loaded.*fuelinst" ${LOG_DIR}/2024_fuelinst_corrected.log 2>/dev/null | xargs echo "  2024 FUELINST loads:" || echo "  2024: Check log"
grep -c "Successfully loaded.*fuelinst" ${LOG_DIR}/2025_fuelinst_corrected.log 2>/dev/null | xargs echo "  2025 FUELINST loads:" || echo "  2025: Check log"
echo ""

echo "Verification:"
echo "  Run: .venv/bin/python test_user_query.py"
echo "  Run: .venv/bin/python verify_data_complete.py"
echo ""
echo "Expected completion: $(date -v+90M 2>/dev/null || date -d '+90 minutes' 2>/dev/null || echo 'in ~90 minutes')"
