#!/bin/bash
# Re-run FUELINST repairs for 2023, 2024, and 2025 after table clearing

PYTHON=".venv/bin/python"
SCRIPT="ingest_elexon_fixed.py"
LOG_DIR="logs_20251028_123449"

echo "======================================================================"
echo "FUELINST REPAIR - RERUN AFTER TABLE CLEARING"
echo "======================================================================"
echo "Started: $(date)"
echo ""

# Wait for current 2023 job to finish
echo "[1/3] Waiting for 2023 FUELINST to complete (PID 99294)..."
while ps -p 99294 > /dev/null 2>&1; do
    # Show progress every minute
    if [ $((SECONDS % 60)) -eq 0 ]; then
        completed=$(grep -c "Successfully loaded" ${LOG_DIR}/2023_fuelinst_rerun.log 2>/dev/null || echo 0)
        echo "  Progress: $completed successful loads so far..."
    fi
    sleep 5
done

echo "✅ 2023 FUELINST completed at $(date)"
echo ""

# Run 2024 FUELINST
echo "[2/3] Starting 2024 FUELINST repair..."
$PYTHON $SCRIPT --start 2024-01-01 --end 2024-12-31 --only FUELINST,FREQ,FUELHH \
    > ${LOG_DIR}/2024_fuelinst_rerun.log 2>&1

echo "✅ 2024 FUELINST completed at $(date)"
echo ""

# Run 2025 FUELINST
echo "[3/3] Starting 2025 FUELINST repair..."
$PYTHON $SCRIPT --start 2025-01-01 --end 2025-10-28 --only FUELINST,FREQ,FUELHH \
    > ${LOG_DIR}/2025_fuelinst_rerun.log 2>&1

echo "✅ 2025 FUELINST completed at $(date)"
echo ""

echo "======================================================================"
echo "ALL FUELINST REPAIRS COMPLETE!"
echo "======================================================================"

# Show summary
echo ""
echo "Summary:"
grep "Successfully loaded.*fuelinst" ${LOG_DIR}/2023_fuelinst_rerun.log | wc -l | xargs echo "  2023 FUELINST loads:"
grep "Successfully loaded.*fuelinst" ${LOG_DIR}/2024_fuelinst_rerun.log | wc -l | xargs echo "  2024 FUELINST loads:"
grep "Successfully loaded.*fuelinst" ${LOG_DIR}/2025_fuelinst_rerun.log | wc -l | xargs echo "  2025 FUELINST loads:"
