#!/bin/bash
# Complete data loading and setup script
# This will:
# 1. Load 2022 data
# 2. Fix FUELINST for 2023, 2024, 2025
# 3. Load Sep-Oct 2025 data
# 4. Set up daily update script

set -e  # Exit on error

PYTHON=".venv/bin/python"
SCRIPT="ingest_elexon_fixed.py"
LOG_DIR="logs_$(date +%Y%m%d_%H%M%S)"

mkdir -p "$LOG_DIR"

echo "======================================================================"
echo "COMPLETE DATA LOADING PLAN"
echo "======================================================================"
echo "Start time: $(date)"
echo ""
echo "Steps:"
echo "  1. Load 2022 full year (~8 hours)"
echo "  2. Fix FUELINST 2023 (~30 min)"
echo "  3. Fix FUELINST 2024 (~30 min)"
echo "  4. Fix FUELINST 2025 Jan-Oct (~2 hours)"
echo "  5. Load 2025 Sep-Oct all datasets (~1 hour)"
echo "  6. Create daily update script"
echo ""
echo "Total estimated time: ~12 hours"
echo "Expected completion: ~12:30 AM tomorrow"
echo "======================================================================"
echo ""

# Step 1: Load 2022 data
echo "[STEP 1/6] Loading 2022 full year..."
echo "Start: $(date)"
$PYTHON $SCRIPT --start 2022-01-01 --end 2022-12-31 > "$LOG_DIR/2022_full_year.log" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 2022 completed at $(date)"
else
    echo "❌ 2022 failed - check logs"
    exit 1
fi
echo ""

# Step 2: Fix FUELINST 2023
echo "[STEP 2/6] Fixing FUELINST/FREQ/FUELHH for 2023..."
echo "Start: $(date)"
$PYTHON $SCRIPT --start 2023-01-01 --end 2023-12-31 --only FUELINST,FREQ,FUELHH > "$LOG_DIR/2023_fuelinst_fix.log" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 2023 FUELINST fix completed at $(date)"
else
    echo "❌ 2023 FUELINST fix failed - check logs"
    exit 1
fi
echo ""

# Step 3: Fix FUELINST 2024
echo "[STEP 3/6] Fixing FUELINST/FREQ/FUELHH for 2024..."
echo "Start: $(date)"
$PYTHON $SCRIPT --start 2024-01-01 --end 2024-12-31 --only FUELINST,FREQ,FUELHH > "$LOG_DIR/2024_fuelinst_fix.log" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 2024 FUELINST fix completed at $(date)"
else
    echo "❌ 2024 FUELINST fix failed - check logs"
    exit 1
fi
echo ""

# Step 4: Fix FUELINST 2025 (Jan-Oct, excluding Oct 27 which exists)
echo "[STEP 4/6] Fixing FUELINST/FREQ/FUELHH for 2025 Jan-Oct..."
echo "Start: $(date)"
$PYTHON $SCRIPT --start 2025-01-01 --end 2025-10-28 --only FUELINST,FREQ,FUELHH > "$LOG_DIR/2025_fuelinst_fix.log" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 2025 FUELINST fix completed at $(date)"
else
    echo "❌ 2025 FUELINST fix failed - check logs"
    exit 1
fi
echo ""

# Step 5: Load 2025 Sep-Oct all datasets (excluding datasets already loaded)
echo "[STEP 5/6] Loading 2025 Sep-Oct all datasets..."
echo "Start: $(date)"
$PYTHON $SCRIPT --start 2025-09-01 --end 2025-10-28 > "$LOG_DIR/2025_sep_oct_all.log" 2>&1
if [ $? -eq 0 ]; then
    echo "✅ 2025 Sep-Oct completed at $(date)"
else
    echo "❌ 2025 Sep-Oct failed - check logs"
    exit 1
fi
echo ""

# Step 6: Create daily update script
echo "[STEP 6/6] Creating daily update script..."
cat > daily_update.sh << 'EOF'
#!/bin/bash
# Daily update script - run this every day to get yesterday's data

PYTHON=".venv/bin/python"
SCRIPT="ingest_elexon_fixed.py"

# Get yesterday's date
YESTERDAY=$(date -v-1d +%Y-%m-%d)

echo "======================================================================"
echo "DAILY UPDATE: Loading data for $YESTERDAY"
echo "Start: $(date)"
echo "======================================================================"

# Load yesterday's data for all datasets
$PYTHON $SCRIPT --start "$YESTERDAY" --end "$YESTERDAY" > "daily_update_${YESTERDAY}.log" 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Daily update completed successfully at $(date)"
    echo "Check daily_update_${YESTERDAY}.log for details"
else
    echo "❌ Daily update failed - check daily_update_${YESTERDAY}.log"
    exit 1
fi
EOF

chmod +x daily_update.sh
echo "✅ Created daily_update.sh"
echo ""

echo "======================================================================"
echo "ALL STEPS COMPLETED!"
echo "======================================================================"
echo "End time: $(date)"
echo ""
echo "Summary:"
echo "  ✅ 2022 data loaded"
echo "  ✅ 2023 FUELINST fixed"
echo "  ✅ 2024 FUELINST fixed"
echo "  ✅ 2025 FUELINST fixed"
echo "  ✅ 2025 Sep-Oct loaded"
echo "  ✅ Daily update script created"
echo ""
echo "Logs saved in: $LOG_DIR"
echo ""
echo "To run daily updates:"
echo "  ./daily_update.sh"
echo ""
echo "Or set up a cron job:"
echo "  0 6 * * * cd $(pwd) && ./daily_update.sh"
echo "  (Runs every day at 6 AM)"
echo "======================================================================"
