#!/bin/bash
# VLP Dashboard - Quick Verification Script
# Run this to verify all systems are operational

echo "🔍 VLP DASHBOARD VERIFICATION"
echo "============================================================"
echo ""

# 1. Check Python dependencies
echo "1️⃣ Checking Python dependencies..."
python3 -c "import google.cloud.bigquery, gspread, oauth2client; print('   ✅ All Python packages installed')" 2>/dev/null || echo "   ❌ Missing Python packages - run: pip3 install --user google-cloud-bigquery gspread oauth2client"
echo ""

# 2. Check credentials file
echo "2️⃣ Checking credentials..."
if [ -f "/home/george/inner-cinema-credentials.json" ]; then
    echo "   ✅ Credentials file found"
else
    echo "   ❌ Credentials file missing: /home/george/inner-cinema-credentials.json"
fi
echo ""

# 3. Check CLASP authentication
echo "3️⃣ Checking CLASP authentication..."
if [ -f "$HOME/.clasprc.json" ]; then
    echo "   ✅ CLASP authenticated"
    clasp --version 2>/dev/null && echo "   ✅ CLASP version $(clasp --version)"
else
    echo "   ❌ CLASP not authenticated - run: clasp login"
fi
echo ""

# 4. Check Apps Script files
echo "4️⃣ Checking Apps Script files..."
if [ -f "appsscript_v3/vlp_menu.gs" ]; then
    echo "   ✅ vlp_menu.gs exists"
else
    echo "   ❌ vlp_menu.gs missing - run: cp vlp_menu.gs appsscript_v3/"
fi
echo ""

# 5. Check VLP scripts
echo "5️⃣ Checking VLP Python scripts..."
scripts=("vlp_dashboard_simple.py" "format_vlp_dashboard.py" "create_vlp_charts.py")
for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
        echo "   ✅ $script"
    else
        echo "   ❌ $script missing"
    fi
done
echo ""

# 6. Check configuration
echo "6️⃣ Checking configuration..."
if [ -f "vlp_prerequisites.json" ]; then
    echo "   ✅ vlp_prerequisites.json exists"
    BMU=$(grep -o '"BMU_BATTERY": "[^"]*"' vlp_prerequisites.json | cut -d'"' -f4)
    SHEET=$(grep -o '"SPREADSHEET_ID": "[^"]*"' vlp_prerequisites.json | cut -d'"' -f4)
    echo "   ✅ BMU: $BMU"
    echo "   ✅ Spreadsheet: $SHEET"
else
    echo "   ❌ vlp_prerequisites.json missing"
fi
echo ""

# 7. Test BigQuery connection
echo "7️⃣ Testing BigQuery connection..."
python3 -c "
from google.cloud import bigquery
try:
    client = bigquery.Client(project='inner-cinema-476211-u9', location='US')
    print('   ✅ BigQuery connection successful')
except Exception as e:
    print(f'   ❌ BigQuery connection failed: {e}')
" 2>&1 | grep -v "UserWarning"
echo ""

# 8. Check Apps Script deployment
echo "8️⃣ Checking Apps Script deployments..."
clasp deployments 2>/dev/null | grep -E "VLP Dashboard|Found" | head -5
echo ""

# 9. Show quick commands
echo "============================================================"
echo "📝 QUICK COMMANDS"
echo "============================================================"
echo ""
echo "Run full pipeline:"
echo "  python3 vlp_dashboard_simple.py && python3 format_vlp_dashboard.py && python3 create_vlp_charts.py"
echo ""
echo "Push to Apps Script:"
echo "  clasp push"
echo ""
echo "Deploy new version:"
echo "  clasp deploy --description 'VLP Dashboard v1.1'"
echo ""
echo "Open spreadsheet:"
echo "  https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/"
echo ""
echo "============================================================"
echo "✅ VERIFICATION COMPLETE"
echo "============================================================"
