#!/bin/bash
# Automated Constraint Map Deployment
# Uses clasp (Command Line Apps Script Projects) for full automation

set -e  # Exit on error

echo "================================================================================"
echo "AUTOMATED CONSTRAINT MAP DEPLOYMENT"
echo "================================================================================"

# Check if clasp is installed
if ! command -v clasp &> /dev/null; then
    echo ""
    echo "📦 Installing clasp (Google Apps Script CLI)..."
    npm install -g @google/clasp
    echo "✅ clasp installed"
fi

# Check if already logged in
if ! clasp login --status &> /dev/null; then
    echo ""
    echo "🔐 Please log in to Google Apps Script..."
    clasp login
fi

echo ""
echo "================================================================================"
echo "STEP 1: FETCH LATEST CONSTRAINT DATA"
echo "================================================================================"
echo ""
python3 generate_constraint_map_leaflet.py
echo "✅ Latest data fetched and HTML generated"

echo ""
echo "================================================================================"
echo "STEP 2: PREPARE DEPLOYMENT FILES"
echo "================================================================================"
echo ""

# Create temp directory for clasp deployment
DEPLOY_DIR="clasp_deploy_temp"
rm -rf "$DEPLOY_DIR"
mkdir -p "$DEPLOY_DIR"

# Copy files with correct extensions for clasp
cp dashboard/apps-script/constraint_map_minimal.gs "$DEPLOY_DIR/Code.gs"
cp dashboard/apps-script/ConstraintMap_Leaflet.html "$DEPLOY_DIR/ConstraintMap_Leaflet.html"

# Create .clasp.json to link to your spreadsheet
cat > "$DEPLOY_DIR/.clasp.json" << EOF
{
  "scriptId": "",
  "parentId": ["1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"],
  "rootDir": "."
}
EOF

# Create appsscript.json manifest
cat > "$DEPLOY_DIR/appsscript.json" << EOF
{
  "timeZone": "Europe/London",
  "dependencies": {},
  "exceptionLogging": "STACKDRIVER",
  "runtimeVersion": "V8",
  "oauthScopes": [
    "https://www.googleapis.com/auth/spreadsheets.currentonly",
    "https://www.googleapis.com/auth/script.container.ui"
  ]
}
EOF

echo "✅ Deployment files prepared in $DEPLOY_DIR/"

echo ""
echo "================================================================================"
echo "STEP 3: DEPLOY TO APPS SCRIPT"
echo "================================================================================"
echo ""

cd "$DEPLOY_DIR"

# Create new Apps Script project bound to spreadsheet
echo "📤 Creating Apps Script project..."
clasp create --type sheets --title "GB Constraint Map" --parentId "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA" || {
    echo "⚠️  Project may already exist, trying to use existing..."
}

# Push files
echo "📤 Pushing files to Apps Script..."
clasp push --force

echo "✅ Files uploaded to Apps Script"

# Get script ID
SCRIPT_ID=$(cat .clasp.json | grep scriptId | cut -d'"' -f4)
echo ""
echo "✅ Script ID: $SCRIPT_ID"
echo "🔗 Open in editor: https://script.google.com/d/$SCRIPT_ID/edit"

cd ..

echo ""
echo "================================================================================"
echo "DEPLOYMENT COMPLETE!"
echo "================================================================================"
echo ""
echo "✅ All files uploaded to Apps Script"
echo ""
echo "🎯 NEXT STEPS:"
echo "   1. Open your Google Sheet"
echo "   2. Close and reopen the sheet (to refresh menu)"
echo "   3. Look for '🗺️ Constraint Map' menu"
echo "   4. Click 'Show Map (Leaflet)'"
echo ""
echo "💡 If menu doesn't appear:"
echo "   1. Go to: Extensions → Apps Script"
echo "   2. Run function: onOpen"
echo "   3. Authorize when prompted"
echo ""
echo "🔗 Sheet: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
echo ""

# Clean up
rm -rf "$DEPLOY_DIR"
echo "🧹 Cleaned up temporary files"
