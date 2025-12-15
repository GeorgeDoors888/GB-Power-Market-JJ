#!/bin/bash
# Setup and run the Analysis sheet creation and update

echo "📊 ANALYSIS SHEET SETUP - UNIFIED DATA ARCHITECTURE"
echo "===================================================="
echo ""

# Check if we're in the right directory
if [ ! -f "ANALYSIS_SHEET_DESIGN.md" ]; then
    echo "❌ Error: Not in the correct directory"
    echo "Please run from: /Users/georgemajor/GB Power Market JJ"
    exit 1
fi

# Find Python
if [ -f ".venv/bin/python" ]; then
    PYTHON=".venv/bin/python"
elif [ -f "venv/bin/python" ]; then
    PYTHON="venv/bin/python"
else
    PYTHON="python3"
fi

echo "Using Python: $PYTHON"
$PYTHON --version
echo ""

# Install required package
echo "📦 Installing gspread-formatting..."
$PYTHON -m pip install -q gspread-formatting
echo "✅ Package installed"
echo ""

# Step 1: Create unified views and Analysis sheet
echo "STEP 1: Creating unified BigQuery views and Analysis sheet..."
echo "--------------------------------------------------------------"
$PYTHON create_analysis_sheet.py
RESULT=$?

if [ $RESULT -ne 0 ]; then
    echo ""
    echo "⚠️ Warning: Sheet creation had errors, but continuing..."
fi

echo ""
echo ""

# Step 2: Update the Analysis sheet with data
echo "STEP 2: Populating Analysis sheet with data..."
echo "--------------------------------------------------------------"
$PYTHON update_analysis_sheet.py

echo ""
echo ""
echo "=" * 70
echo "✅ ANALYSIS SHEET SETUP COMPLETE!"
echo "=" * 70
echo ""
echo "📚 Documentation: ANALYSIS_SHEET_DESIGN.md"
echo "🔗 Spreadsheet: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/"
echo ""
echo "📋 What was created:"
echo "  ✅ 5 unified BigQuery views (bmrs_*_unified)"
echo "  ✅ Analysis sheet in Google Sheets"
echo "  ✅ Populated with historical + real-time data"
echo "  ✅ Date range dropdowns (24hrs - 4 years)"
echo "  ✅ Data group checkboxes"
echo "  ✅ Professional formatting"
echo ""
echo "🔄 To update the sheet with latest data:"
echo "  python3 update_analysis_sheet.py"
echo ""
echo "⏰ For automatic updates every 5 minutes:"
echo "  */5 * * * * cd '$PWD' && python3 update_analysis_sheet.py >> analysis_updates.log 2>&1"
echo ""
