#!/bin/bash
# Run this script ON YOUR iMAC (not Dell server)

set -e

echo "📋 Deploying Diagnostic Test"
echo "=============================="
echo ""

cd ~/temp/appsscript_v3 || cd /Users/george/temp/appsscript_v3 || {
    echo "❌ Directory not found: ~/temp/appsscript_v3"
    echo "Please create it first or cd to your clasp directory"
    exit 1
}

echo "Current directory: $(pwd)"
echo ""

# Show what we're deploying
echo "Files to deploy:"
ls -lh *.gs *.html *.json 2>/dev/null | head -10

echo ""
echo "Pushing to Apps Script..."
clasp push --force

echo ""
echo "✅ DEPLOYMENT COMPLETE!"
echo ""
echo "================================================"
echo "📝 NOW TEST IN GOOGLE SHEETS:"
echo "================================================"
echo ""
echo "1. Open Google Sheets"
echo ""
echo "2. Extensions → Apps Script"
echo ""
echo "3. Find 'DiagnosticMapTest.gs' in left sidebar"
echo ""
echo "4. Select function: testMapSidebarDeployment"
echo ""
echo "5. Click ▶️ Run"
echo ""
echo "6. Check Execution log for detailed output"
echo ""
echo "================================================"
