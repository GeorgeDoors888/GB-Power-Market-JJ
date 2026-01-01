#!/bin/bash
# Re-authenticate clasp and deploy from iMac

echo "========================================================================"
echo "  CLASP RE-AUTHENTICATION & DEPLOYMENT"
echo "========================================================================"
echo ""

# Step 1: Re-authenticate clasp
echo "1️⃣ Re-authenticating clasp..."
echo "   This will open a browser for Google sign-in"
echo ""

clasp login

if [ $? -ne 0 ]; then
    echo "❌ Authentication failed"
    exit 1
fi

echo ""
echo "✅ Authentication successful"
echo ""

# Step 2: Navigate to temp directory
TEMP_DIR="$HOME/temp_apps_script_deploy"

if [ ! -d "$TEMP_DIR" ]; then
    echo "❌ Temp directory not found: $TEMP_DIR"
    echo "   Run deploy_from_imac.sh first to copy files"
    exit 1
fi

cd "$TEMP_DIR"

# Step 3: Verify files
echo "2️⃣ Verifying files..."
if [ ! -f ".clasp.json" ]; then
    echo "❌ .clasp.json not found"
    exit 1
fi

if [ ! -f "appsscript.json" ]; then
    echo "❌ appsscript.json not found"
    exit 1
fi

echo "   ✅ All required files present"
echo ""

# Step 4: Show what will be pushed
echo "3️⃣ Files to push:"
ls -lh *.{json,html,gs} 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'
echo ""

# Step 5: Push to Apps Script
echo "4️⃣ Pushing to Apps Script..."
echo "   Script ID: $(cat .clasp.json | grep scriptId | cut -d'"' -f4)"
echo ""

clasp push --force

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ =================================="
    echo "✅  DEPLOYMENT SUCCESSFUL!"
    echo "✅ =================================="
    echo ""
    echo "📋 What was deployed:"
    echo "   ✅ appsscript.json - Fixed OAuth scopes:"
    echo "      • spreadsheets (full access, not .currentonly)"
    echo "      • script.container.ui (sidebars/menus)"
    echo "      • bigquery (map GeoJSON queries)"
    echo "      • script.external_request (API calls - fixes UrlFetchApp error)"
    echo ""
    echo "   ✅ map_sidebarh.html - Map sidebar UI"
    echo "   ✅ map_sidebar.gs - Map backend with BigQuery"
    echo "   ✅ MASTER_onOpen.gs - Menu integration"
    echo "   ✅ Existing files preserved (Code.gs, etc.)"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  NEXT STEPS (Manual - In Google Sheets)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🔐 STEP 1: Authorize New OAuth Scopes"
    echo "   1. Open your Google Sheet"
    echo "   2. Extensions → Apps Script"
    echo "   3. Select function dropdown: showMapSidebar"
    echo "   4. Click Run (▶️)"
    echo "   5. Dialog: 'Authorization required'"
    echo "   6. Click 'Review Permissions'"
    echo "   7. Select your Google account"
    echo "   8. Warning: Click 'Advanced'"
    echo "   9. Click 'Go to [Untitled project] (unsafe)'"
    echo "   10. Review permissions (4 scopes) → Click 'Allow'"
    echo "   11. Wait for 'Execution completed'"
    echo ""
    echo "🔑 STEP 2: Add Google Maps API Key"
    echo "   1. In Apps Script editor: File → Project Settings"
    echo "   2. Scroll to 'Script Properties'"
    echo "   3. Click 'Add script property'"
    echo "   4. Property name: GOOGLE_MAPS_API_KEY"
    echo "   5. Property value: AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0"
    echo "   6. Click 'Save script properties'"
    echo ""
    echo "📊 STEP 3: Enable BigQuery API"
    echo "   1. In Apps Script editor: Services (+ icon in left sidebar)"
    echo "   2. Search: BigQuery API"
    echo "   3. Version: v2"
    echo "   4. Identifier: BigQuery"
    echo "   5. Click 'Add'"
    echo "   6. Confirm it appears in Services list"
    echo ""
    echo "✅ STEP 4: Test Map Sidebar"
    echo "   1. Close Apps Script editor"
    echo "   2. Back in Google Sheets: Refresh (Command+R)"
    echo "   3. New menu appears: 🗺️ Geographic Map"
    echo "   4. Click: 🗺️ Geographic Map → Show DNO & GSP Boundaries"
    echo "   5. Sidebar opens with map (UK centered)"
    echo "   6. Click: 🗺️ Show DNO Regions (14)"
    echo "      → Blue polygons appear"
    echo "   7. Click: 📍 Show GSP Regions (333)"
    echo "      → Green polygons appear"
    echo "   8. Click any polygon → Details display below"
    echo ""
    echo "🔍 STEP 5: Test Search Interface (Verify API Fix)"
    echo "   1. Try search interface in your sheet"
    echo "   2. Should NO LONGER show:"
    echo "      ❌ 'API Connection Failed: Specified permissions'"
    echo "         'are not sufficient to call UrlFetchApp.fetch'"
    echo "   3. Should now show:"
    echo "      ✅ Search results or 'No results found'"
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "🎯 Issues Fixed:"
    echo "   ✅ OAuth scope: spreadsheets.currentonly → spreadsheets"
    echo "   ✅ OAuth scope added: bigquery (for map GeoJSON)"
    echo "   ✅ OAuth scope added: script.external_request (for API calls)"
    echo "   ✅ Map sidebar files deployed correctly"
    echo "   ✅ Filename mismatch resolved (map_sidebarh.html)"
    echo ""
    echo "📖 For troubleshooting, see:"
    echo "   • OAUTH_SCOPE_FIX_GUIDE.md (on Dell server)"
    echo "   • MAP_SIDEBAR_DEPLOYMENT_GUIDE.md (on Dell server)"
    echo ""
else
    echo ""
    echo "❌ =================================="
    echo "❌  DEPLOYMENT FAILED"
    echo "❌ =================================="
    echo ""
    echo "Troubleshooting:"
    echo "   1. Check authentication: clasp login"
    echo "   2. Verify Script ID in .clasp.json"
    echo "   3. Check you have editor access to the Google Sheet"
    echo ""
fi

echo ""
echo "📁 Temp files location: $TEMP_DIR"
echo "   You can delete after testing: rm -rf $TEMP_DIR"
