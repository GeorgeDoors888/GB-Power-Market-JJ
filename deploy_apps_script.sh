#!/bin/bash
# Deploy BESS Apps Script to Google Sheets using clasp

set -e

echo "=========================================="
echo "BESS Apps Script Deployment"
echo "=========================================="

# Check if clasp is installed
if ! command -v clasp &> /dev/null; then
    echo "❌ clasp not found. Install with: npm install -g @google/clasp"
    exit 1
fi

echo "✅ clasp found: $(clasp --version)"

# Check if authenticated
echo ""
echo "🔐 Checking authentication..."
if ! clasp list &> /dev/null; then
    echo "❌ Not authenticated. Running 'clasp login'..."
    echo ""
    echo "A browser window will open. Please:"
    echo "1. Sign in with your Google account"
    echo "2. Allow clasp to access Google Apps Script"
    echo "3. Return here when done"
    echo ""
    read -p "Press Enter to continue..."
    clasp login
fi

echo "✅ Authenticated"

# Verify apps-script folder
if [ ! -d "apps-script" ]; then
    echo "❌ apps-script folder not found"
    exit 1
fi

echo ""
echo "📂 Apps Script files:"
ls -la apps-script/

# Push to Google Apps Script
echo ""
echo "📤 Deploying to Google Apps Script..."
cd apps-script
clasp push --force

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ DEPLOYMENT SUCCESSFUL!"
    echo "=========================================="
    echo ""
    echo "The Apps Script has been deployed to your Google Sheets."
    echo ""
    echo "To use it:"
    echo "1. Open your spreadsheet"
    echo "2. Refresh the page"
    echo "3. Look for the '🔋 BESS Tools' menu"
    echo "4. Click: 🔋 BESS Tools → 📊 Generate HH Data"
    echo ""
    echo "Script ID: $(cat ../.clasp.json | grep scriptId | cut -d'"' -f4)"
    echo ""
else
    echo ""
    echo "=========================================="
    echo "❌ DEPLOYMENT FAILED"
    echo "=========================================="
    echo ""
    echo "Try running manually:"
    echo "  clasp login"
    echo "  cd apps-script"
    echo "  clasp push --force"
    echo ""
    exit 1
fi
