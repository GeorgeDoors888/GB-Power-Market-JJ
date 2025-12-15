#!/bin/bash
# Quick deploy script for BESS Apps Script

set -e

echo "📋 BESS Apps Script Deployment"
echo "================================"
echo ""

# Check if Code.gs exists
if [ ! -f "/home/george/GB-Power-Market-JJ/apps_script_deploy/Code.gs" ]; then
    echo "❌ Code.gs not found. Copying from source..."
    cp /home/george/GB-Power-Market-JJ/apps_script_enhanced/bess_integration.gs \
       /home/george/GB-Power-Market-JJ/apps_script_deploy/Code.gs
    echo "✅ Code.gs copied"
fi

# Check if .clasp.json exists
if [ ! -f "/home/george/GB-Power-Market-JJ/apps_script_deploy/.clasp.json" ]; then
    echo ""
    echo "⚠️  .clasp.json not found"
    echo ""
    echo "You need to complete authentication first:"
    echo ""
    echo "1. Run: cd /home/george/GB-Power-Market-JJ/apps_script_deploy && clasp login --no-localhost"
    echo "2. Follow browser prompt and authorize"
    echo "3. Create .clasp.json with your script ID"
    echo ""
    echo "See CLASP_SETUP.md for detailed instructions"
    exit 1
fi

# Check if authenticated
if [ ! -f "$HOME/.clasprc.json" ]; then
    echo ""
    echo "⚠️  Not authenticated with clasp"
    echo ""
    echo "Run: cd /home/george/GB-Power-Market-JJ/apps_script_deploy && clasp login --no-localhost"
    echo ""
    exit 1
fi

echo "✅ Code.gs ready"
echo "✅ .clasp.json found"
echo "✅ Authenticated"
echo ""

# Deploy
cd /home/george/GB-Power-Market-JJ/apps_script_deploy
echo "🚀 Deploying to Google Sheets..."
clasp push

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Open https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/"
echo "2. Refresh page (Ctrl+R)"
echo "3. Look for '⚡ GB Energy Dashboard' menu"
echo "4. Go to BESS sheet → Menu → Format Enhanced Section"
