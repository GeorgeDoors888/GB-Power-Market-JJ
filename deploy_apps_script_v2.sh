#!/bin/bash
# Deploy Apps Script V2 using clasp

set -e

SPREADSHEET_ID="1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"

echo "================================================================================"
echo "📜 DEPLOYING APPS SCRIPT V2"
echo "================================================================================"
echo ""

# Check if already logged in
echo "🔐 Checking clasp authentication..."
if ! clasp login --status 2>/dev/null; then
    echo "⚠️  Not logged in. Run: clasp login"
    echo "Then come back and run this script again."
    exit 1
fi

echo "✅ Authenticated with Google"
echo ""

# Create directory structure
echo "📁 Setting up project structure..."
mkdir -p apps-script-v2
cp apps_script_v2.gs apps-script-v2/Code.gs

cat > apps-script-v2/appsscript.json << 'JSON_END'
{
  "timeZone": "Europe/London",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8"
}
JSON_END

echo "✅ Files prepared"
echo ""

echo "================================================================================"
echo "🎯 MANUAL DEPLOYMENT INSTRUCTIONS"
echo "================================================================================"
echo ""
echo "Clasp requires OAuth which can be tricky. Here's the simpler manual approach:"
echo ""
echo "1. Open your spreadsheet:"
echo "   https://docs.google.com/spreadsheets/d/$SPREADSHEET_ID/"
echo ""
echo "2. Click: Extensions → Apps Script"
echo ""
echo "3. In the Apps Script editor:"
echo "   • Delete any existing Code.gs content"
echo "   • Copy the entire contents of: apps_script_v2.gs"
echo "   • Paste into Code.gs"
echo "   • Save (Ctrl+S or Cmd+S)"
echo ""
echo "4. Close the Apps Script tab and refresh your spreadsheet"
echo ""
echo "5. You should see a new menu: 🚀 Dashboard V2"
echo ""
echo "================================================================================"
echo "📝 ALTERNATIVE: Use clasp (if OAuth works)"
echo "================================================================================"
echo ""
echo "If you want to try clasp deployment:"
echo ""
echo "1. cd apps-script-v2"
echo "2. clasp create --type standalone --title 'Dashboard V2 Scripts'"
echo "3. clasp push"
echo "4. Get script ID: clasp open"
echo "5. In spreadsheet: Extensions → Apps Script → Copy script ID"
echo "6. Update .clasp.json with script ID"
echo "7. clasp push again"
echo ""
echo "================================================================================"
echo ""

# Open the file for easy copying
echo "📋 Opening apps_script_v2.gs for you to copy..."
echo ""
open -a "TextEdit" apps_script_v2.gs 2>/dev/null || open -a "Visual Studio Code" apps_script_v2.gs 2>/dev/null || cat apps_script_v2.gs

