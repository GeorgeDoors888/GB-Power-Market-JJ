#!/bin/bash
# Execute Tasks 3 & 4: DNO Centroids + Dashboard KPI Updates
# Run: ./execute_tasks_3_and_4.sh

set -e  # Exit on error

echo "🚀 Executing Tasks 3 & 4"
echo "======================================"

# Task 3: Import DNO Centroids
echo ""
echo "📍 TASK 3: Importing DNO Centroids..."
python3 python/import_dno_centroids_to_sheets.py

echo ""
echo "✅ Task 3 complete!"
echo "   📝 Manual step: Create GeoChart in DNO_CENTROIDS tab"
echo "   See: TASK3_AND_4_EXECUTION_GUIDE.md for instructions"

# Task 4 Step 1: Import BOD Summary
echo ""
echo "📊 TASK 4 STEP 1: Importing BOD Summary data..."
python3 python/import_bod_summary_to_sheets.py

# Task 4 Step 2: Update Formulas
echo ""
echo "📝 TASK 4 STEP 2: Updating Dashboard V3 formulas..."
python3 python/task4_update_kpi_formulas.py

echo ""
echo "✅ All tasks complete!"
echo ""
echo "🔗 Open: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
echo ""
echo "📋 Verify:"
echo "   1. DNO_CENTROIDS tab created"
echo "   2. BOD_SUMMARY tab created with data"
echo "   3. Dashboard V3 row 10 formulas updated"
echo ""
echo "📝 Next: Create GeoChart in DNO_CENTROIDS tab (see guide)"
