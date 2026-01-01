#!/bin/bash
# Deploy Apps Script from iMac (with working network)
# Copy files from Dell to iMac, then push via clasp

echo "========================================================================"
echo "  DEPLOY FROM IMAC (Dell → iMac → Apps Script)"
echo "========================================================================"
echo ""
echo "This script assumes you're running it ON YOUR IMAC, not the Dell server"
echo ""

# Configuration
DELL_HOST="dell"  # Your SSH config alias or use: george@94.237.55.234
DELL_DIR="/home/george/GB-Power-Market-JJ/appsscript_v3"
LOCAL_TEMP="$HOME/temp_apps_script_deploy"

# Step 1: Create temp directory on iMac
echo "1️⃣ Creating temp directory on iMac..."
mkdir -p "$LOCAL_TEMP"
cd "$LOCAL_TEMP"

# Step 2: Copy files from Dell to iMac
echo ""
echo "2️⃣ Copying files from Dell server..."
echo "   From: $DELL_HOST:$DELL_DIR"
echo "   To: $LOCAL_TEMP"
echo ""

scp "$DELL_HOST:$DELL_DIR/appsscript.json" . || { echo "❌ Failed to copy appsscript.json"; exit 1; }
scp "$DELL_HOST:$DELL_DIR/map_sidebarh.html" . || { echo "❌ Failed to copy map_sidebarh.html"; exit 1; }
scp "$DELL_HOST:$DELL_DIR/map_sidebar.gs" . || { echo "❌ Failed to copy map_sidebar.gs"; exit 1; }
scp "$DELL_HOST:$DELL_DIR/MASTER_onOpen.gs" . || { echo "❌ Failed to copy MASTER_onOpen.gs"; exit 1; }
scp "$DELL_HOST:$DELL_DIR/Code.gs" . 2>/dev/null  # Optional existing files
scp "$DELL_HOST:$DELL_DIR/AutoOptimize.gs" . 2>/dev/null
scp "$DELL_HOST:$DELL_DIR/SheetsOptimization.gs" . 2>/dev/null
scp "$DELL_HOST:$DELL_DIR/vlp_menu.gs" . 2>/dev/null
scp "$DELL_HOST:$DELL_DIR/DnoMap.html" . 2>/dev/null
scp "$DELL_HOST:$DELL_DIR/DnoMapSimple.html" . 2>/dev/null

# Copy .clasp.json
scp "$DELL_HOST:/home/george/GB-Power-Market-JJ/.clasp.json" . || { echo "❌ Failed to copy .clasp.json"; exit 1; }

echo "✅ Files copied"

# Step 3: Show what will be pushed
echo ""
echo "3️⃣ Files ready to push:"
ls -lh *.{json,html,gs} 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'

# Step 4: Check clasp authentication on iMac
echo ""
echo "4️⃣ Checking clasp authentication..."
if clasp login --status 2>&1 | grep -q "Logged in"; then
    echo "   ✅ Clasp authenticated"
elif [ -f ~/.clasprc.json ]; then
    echo "   ✅ Clasp credentials found"
else
    echo "   ⚠️  Not authenticated - run: clasp login"
    echo "   Opening browser for authentication..."
    clasp login
fi

# Step 5: Push to Apps Script
echo ""
echo "5️⃣ Pushing to Apps Script from iMac..."
echo "   Script ID: $(jq -r .scriptId .clasp.json)"
echo ""

clasp push --force

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ =================================="
    echo "✅  DEPLOYMENT SUCCESSFUL!"
    echo "✅ =================================="
    echo ""
    echo "📋 Files deployed:"
    echo "   ✅ appsscript.json (OAuth scopes fixed)"
    echo "   ✅ map_sidebarh.html (Map UI)"
    echo "   ✅ map_sidebar.gs (Map backend)"
    echo "   ✅ MASTER_onOpen.gs (Menu integration)"
    echo ""
    echo "📋 Next steps (In Google Sheets):"
    echo ""
    echo "   1. Open your Google Sheet"
    echo "   2. Extensions → Apps Script"
    echo "   3. Run function: showMapSidebar"
    echo "   4. Click 'Review Permissions' → Allow (authorizes new OAuth scopes)"
    echo "   5. Add Script Property:"
    echo "      • File → Project Settings → Script Properties"
    echo "      • Name: GOOGLE_MAPS_API_KEY"
    echo "      • Value: AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0"
    echo "   6. Enable BigQuery API:"
    echo "      • Services (+) → BigQuery API → v2 → Add"
    echo "   7. Test:"
    echo "      • Refresh sheet"
    echo "      • Click: 🗺️ Geographic Map → Show DNO & GSP Boundaries"
    echo "      • Try search interface (API error should be fixed)"
    echo ""
else
    echo ""
    echo "❌ =================================="
    echo "❌  DEPLOYMENT FAILED"
    echo "❌ =================================="
    echo ""
    echo "Check clasp authentication: clasp login"
fi

# Cleanup
echo ""
echo "6️⃣ Cleanup..."
echo "   Temp files in: $LOCAL_TEMP"
echo "   Keep for reference or delete: rm -rf $LOCAL_TEMP"
