#!/bin/bash
# Complete Apps Script Deployment - Map Sidebar + OAuth Scope Fix
# Fixes both map deployment and API permission errors

cd /home/george/GB-Power-Market-JJ

echo "========================================================================"
echo "  COMPLETE APPS SCRIPT DEPLOYMENT GUIDE"
echo "========================================================================"
echo ""
echo "🎯 This guide fixes TWO issues:"
echo "   1. Map sidebar deployment (map_sidebarh.html filename + BigQuery)"
echo "   2. API permission errors (UrlFetchApp.fetch OAuth scope)"
echo ""

# ============================================================================
# PART 1: Verify Local Files
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PART 1: Verify Local Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

FILES_OK=true

# Check map files
if [ -f "map_sidebarh.html" ]; then
    SIZE=$(stat -c%s map_sidebarh.html)
    echo "✅ map_sidebarh.html: $SIZE bytes"
else
    echo "❌ map_sidebarh.html NOT FOUND!"
    FILES_OK=false
fi

if [ -f "map_sidebar.gs" ]; then
    SIZE=$(stat -c%s map_sidebar.gs)
    echo "✅ map_sidebar.gs: $SIZE bytes"
else
    echo "❌ map_sidebar.gs NOT FOUND!"
    FILES_OK=false
fi

if [ -f "MASTER_onOpen.gs" ]; then
    SIZE=$(stat -c%s MASTER_onOpen.gs)
    echo "✅ MASTER_onOpen.gs: $SIZE bytes"
else
    echo "❌ MASTER_onOpen.gs NOT FOUND!"
    FILES_OK=false
fi

# Check manifest fix
if [ -f "appsscript_v3/appsscript_FIXED.json" ]; then
    echo "✅ appsscript_FIXED.json: Ready to deploy"
else
    echo "❌ appsscript_FIXED.json NOT FOUND!"
    FILES_OK=false
fi

if [ "$FILES_OK" = false ]; then
    echo ""
    echo "⚠️  CRITICAL: Some files missing! Cannot proceed."
    exit 1
fi

echo ""
echo "✅ All local files verified and ready!"

# ============================================================================
# PART 2: Show File Contents for Copy-Paste
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PART 2: File Locations (For Manual Upload)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📁 Files to copy from:"
echo ""
echo "   Map HTML:    $(pwd)/map_sidebarh.html"
echo "   Map Script:  $(pwd)/map_sidebar.gs"
echo "   Menu Script: $(pwd)/MASTER_onOpen.gs"
echo "   OAuth Fix:   $(pwd)/appsscript_v3/appsscript_FIXED.json"
echo ""
echo "💡 Tip: Use 'cat filename' to view contents for copy-paste"
echo ""

# ============================================================================
# PART 3: Step-by-Step Deployment Instructions
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PART 3: Apps Script Deployment Steps"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
echo "┃ STEP 1: Open Apps Script Editor                                     ┃"
echo "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
echo ""
echo "   In Google Sheets:"
echo "   → Extensions → Apps Script"
echo ""
read -p "   Press ENTER when Apps Script editor is open..."

echo ""
echo "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
echo "┃ STEP 2: Fix OAuth Scopes (CRITICAL - Fixes API Errors)              ┃"
echo "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
echo ""
echo "   🔴 This fixes: 'Specified permissions are not sufficient to call"
echo "      UrlFetchApp.fetch' error"
echo ""
echo "   1. View → Show manifest file (if not visible)"
echo "   2. Click on appsscript.json in left sidebar"
echo "   3. Find the 'oauthScopes' array"
echo "   4. Replace it with (copy from appsscript_FIXED.json):"
echo ""
echo "   \"oauthScopes\": ["
echo "     \"https://www.googleapis.com/auth/spreadsheets\","
echo "     \"https://www.googleapis.com/auth/script.container.ui\","
echo "     \"https://www.googleapis.com/auth/bigquery\","
echo "     \"https://www.googleapis.com/auth/script.external_request\""
echo "   ]"
echo ""
echo "   5. Save manifest (Command+S on Mac)"
echo ""
read -p "   Press ENTER when OAuth scopes are updated..."

echo ""
echo "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
echo "┃ STEP 3: Upload Map Sidebar HTML                                     ┃"
echo "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
echo ""
echo "   1. Click + button → HTML"
echo "   2. Name it EXACTLY: map_sidebarh (NO .html extension!)"
echo "   3. Delete default content"
echo "   4. Copy ALL content from: map_sidebarh.html"
echo ""
echo "   Quick copy command:"
echo "   $ cat $(pwd)/map_sidebarh.html"
echo ""
echo "   5. Paste into Apps Script editor"
echo "   6. Save (Command+S)"
echo ""
read -p "   Press ENTER when map_sidebarh HTML is uploaded..."

echo ""
echo "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
echo "┃ STEP 4: Upload Map Sidebar Script                                   ┃"
echo "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
echo ""
echo "   1. Click + button → Script"
echo "   2. Name it: map_sidebar"
echo "   3. Delete default content"
echo "   4. Copy ALL content from: map_sidebar.gs"
echo ""
echo "   Quick copy command:"
echo "   $ cat $(pwd)/map_sidebar.gs"
echo ""
echo "   5. Paste into Apps Script editor"
echo "   6. Save (Command+S)"
echo ""
read -p "   Press ENTER when map_sidebar.gs is uploaded..."

echo ""
echo "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
echo "┃ STEP 5: Update/Add Menu Integration                                 ┃"
echo "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
echo ""
echo "   1. Look for existing 'MASTER_onOpen.gs' OR create new Script file"
echo "   2. If exists: Replace content"
echo "      If new: Name it 'MASTER_onOpen'"
echo "   3. Copy ALL content from: MASTER_onOpen.gs"
echo ""
echo "   Quick copy command:"
echo "   $ cat $(pwd)/MASTER_onOpen.gs"
echo ""
echo "   4. Paste into Apps Script editor"
echo "   5. Save (Command+S)"
echo ""
read -p "   Press ENTER when MASTER_onOpen.gs is uploaded..."

echo ""
echo "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
echo "┃ STEP 6: Add Google Maps API Key                                     ┃"
echo "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
echo ""
echo "   1. File → Project Settings (or ⚙️ icon in left sidebar)"
echo "   2. Scroll to 'Script Properties' section"
echo "   3. Click 'Add script property'"
echo "   4. Property name: GOOGLE_MAPS_API_KEY"
echo "   5. Property value: AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0"
echo "   6. Click 'Save script properties'"
echo ""
read -p "   Press ENTER when API key is added..."

echo ""
echo "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
echo "┃ STEP 7: Enable BigQuery API                                         ┃"
echo "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
echo ""
echo "   1. In Apps Script editor, find 'Services' (+ icon in left sidebar)"
echo "   2. Search for: BigQuery API"
echo "   3. Version: v2"
echo "   4. Identifier: BigQuery"
echo "   5. Click 'Add'"
echo "   6. Confirm it appears in Services list"
echo ""
read -p "   Press ENTER when BigQuery API is enabled..."

echo ""
echo "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
echo "┃ STEP 8: Authorize All Permissions (CRITICAL)                        ┃"
echo "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
echo ""
echo "   🔐 This authorizes all 4 OAuth scopes:"
echo "      ✅ Spreadsheets access"
echo "      ✅ UI/Sidebar display"
echo "      ✅ BigQuery queries"
echo "      ✅ External API calls (UrlFetchApp.fetch)"
echo ""
echo "   1. Select function dropdown at top: showMapSidebar"
echo "   2. Click Run button (▶️)"
echo "   3. Authorization dialog appears: 'Authorization required'"
echo "   4. Click 'Review Permissions'"
echo "   5. Select your Google account"
echo "   6. Warning appears: Click 'Advanced'"
echo "   7. Click 'Go to [project name] (unsafe)'"
echo "   8. Review permissions:"
echo "      • See, edit, create, delete all spreadsheets"
echo "      • Display third-party web content"
echo "      • Connect to external service (BigQuery)"
echo "      • Connect to external service (External APIs)"
echo "   9. Click 'Allow'"
echo "   10. Wait for 'Execution completed' in log"
echo ""
read -p "   Press ENTER when authorization is complete..."

echo ""
echo "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
echo "┃ STEP 9: Test Map Sidebar                                            ┃"
echo "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
echo ""
echo "   1. Close Apps Script editor"
echo "   2. Back in Google Sheets: Refresh (Command+R on Mac)"
echo "   3. New menu should appear: 🗺️ Geographic Map"
echo "   4. Click: 🗺️ Geographic Map → Show DNO & GSP Boundaries"
echo "   5. Sidebar opens on right side (400px width)"
echo "   6. Map displays UK centered at 54.5°N, 3.5°W"
echo "   7. Click button: 🗺️ Show DNO Regions (14)"
echo "   8. Blue polygons appear (14 DNO boundaries)"
echo "   9. Click any polygon → Details display below buttons"
echo "   10. Click button: 📍 Show GSP Regions (333)"
echo "   11. Green polygons appear (333 GSP boundaries)"
echo ""
echo "   ✅ Success indicators:"
echo "      • Sidebar opens without errors"
echo "      • Map displays UK geography"
echo "      • DNO button loads 14 blue regions"
echo "      • GSP button loads 333 green regions"
echo "      • Clicking polygon shows region details"
echo ""
read -p "   Press ENTER when map test is successful..."

echo ""
echo "┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
echo "┃ STEP 10: Test Search Interface (Verify API Fix)                     ┃"
echo "┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
echo ""
echo "   🔴 This verifies the OAuth scope fix resolved the API error"
echo ""
echo "   1. In Google Sheets, find the search interface"
echo "   2. Try a search (e.g., Organization: 'Elexon Ltd')"
echo "   3. Should NO LONGER show:"
echo "      ❌ 'API Connection Failed: Specified permissions are not"
echo "         sufficient to call UrlFetchApp.fetch'"
echo "   4. Should now show:"
echo "      ✅ Search results or 'No results found'"
echo ""
read -p "   Press ENTER when search test is successful..."

# ============================================================================
# PART 4: Summary & Troubleshooting
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  DEPLOYMENT COMPLETE!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ FIXED ISSUES:"
echo "   1. Map sidebar filename mismatch (map_sidebarh.html)"
echo "   2. OAuth scope for external API calls (script.external_request)"
echo "   3. BigQuery access for GeoJSON queries"
echo "   4. All permissions authorized"
echo ""
echo "🎯 WORKING FEATURES:"
echo "   ✅ Geographic map sidebar with DNO/GSP boundaries"
echo "   ✅ Search interface API calls (no more permission errors)"
echo "   ✅ BigQuery queries from Apps Script"
echo "   ✅ External webhooks and API endpoints"
echo ""
echo "📚 DOCUMENTATION:"
echo "   • Map deployment: $(pwd)/MAP_SIDEBAR_DEPLOYMENT_GUIDE.md"
echo "   • OAuth fix: $(pwd)/OAUTH_SCOPE_FIX_GUIDE.md"
echo "   • Full guide: $(pwd)/fix_and_deploy_map.sh"
echo ""
echo "🔍 TROUBLESHOOTING:"
echo ""
echo "   Error: 'No HTML file named map_sidebarh'"
echo "   Fix: Verify HTML file named exactly 'map_sidebarh' (no .html)"
echo ""
echo "   Error: 'BigQuery is not defined'"
echo "   Fix: Services → Add BigQuery API v2"
echo ""
echo "   Error: 'getMapsApiKey is not defined'"
echo "   Fix: Verify map_sidebar.gs has function getMapsApiKey() (no underscore)"
echo ""
echo "   Error: 'No Maps API key set'"
echo "   Fix: Script Properties → GOOGLE_MAPS_API_KEY = AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0"
echo ""
echo "   Error: 'Permission denied' or 'Insufficient permissions'"
echo "   Fix: Run showMapSidebar() → Review Permissions → Allow"
echo ""
echo "   Error: 'UrlFetchApp.fetch permission error'"
echo "   Fix: appsscript.json must have script.external_request scope"
echo ""
echo "========================================================================"
echo "  🚀 ALL SYSTEMS GO!"
echo "========================================================================"
echo ""
