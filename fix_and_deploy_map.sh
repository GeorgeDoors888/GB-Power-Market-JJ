#!/bin/bash
# Fix Map Sidebar Filename Mismatch and Provide Deployment Instructions

cd /home/george/GB-Power-Market-JJ

echo "=================================="
echo "  MAP SIDEBAR DEPLOYMENT FIX"
echo "=================================="
echo ""

# Check current situation
echo "1️⃣  Current File Status:"
echo "----------------------------------------"
if [ -f "map_sidebar.html" ]; then
    echo "✅ Found: map_sidebar.html ($(stat -c%s map_sidebar.html) bytes)"
    NEEDS_RENAME=true
else
    echo "❌ Not found: map_sidebar.html"
    NEEDS_RENAME=false
fi

if [ -f "map_sidebarh.html" ]; then
    echo "✅ Found: map_sidebarh.html ($(stat -c%s map_sidebarh.html) bytes)"
    ALREADY_CORRECT=true
else
    echo "❌ Not found: map_sidebarh.html"
    ALREADY_CORRECT=false
fi

if [ -f "map_sidebar.gs" ]; then
    echo "✅ Found: map_sidebar.gs ($(stat -c%s map_sidebar.gs) bytes)"
else
    echo "❌ Not found: map_sidebar.gs"
fi

echo ""
echo "2️⃣  Checking Code Reference:"
echo "----------------------------------------"
if grep -q "createHtmlOutputFromFile('map_sidebarh')" map_sidebar.gs; then
    echo "✅ Code references: 'map_sidebarh' (correct)"
    CODE_EXPECTS_H=true
else
    echo "⚠️  Code references: 'map_sidebar' (without h)"
    CODE_EXPECTS_H=false
fi

echo ""
echo "3️⃣  Problem Diagnosis:"
echo "----------------------------------------"

if [ "$CODE_EXPECTS_H" = true ] && [ "$NEEDS_RENAME" = true ]; then
    echo "🔴 MISMATCH DETECTED!"
    echo ""
    echo "   Problem: Code wants 'map_sidebarh' but file is 'map_sidebar.html'"
    echo "   Result: Apps Script will show error 'No HTML file named map_sidebarh'"
    echo ""
    echo "   Fix: Rename map_sidebar.html → map_sidebarh.html"
    echo ""
    echo "   Applying fix now..."
    mv map_sidebar.html map_sidebarh.html
    if [ $? -eq 0 ]; then
        echo "   ✅ Renamed successfully!"
        echo "   File is now: map_sidebarh.html"
    else
        echo "   ❌ Rename failed"
        exit 1
    fi
elif [ "$ALREADY_CORRECT" = true ]; then
    echo "✅ NO ISSUES - Filename already correct (map_sidebarh.html)"
else
    echo "⚠️  Cannot determine issue - manual check needed"
fi

echo ""
echo "4️⃣  Final File Check:"
echo "----------------------------------------"
ls -lh map_sidebar*.html map_sidebar.gs 2>/dev/null || echo "Some files missing"

echo ""
echo "5️⃣  Deployment Instructions:"
echo "=========================================="
echo ""
echo "📤 STEP 1: Open Apps Script Editor"
echo "   In Google Sheets: Extensions → Apps Script"
echo ""
echo "📤 STEP 2: Upload HTML File"
echo "   • Click + button → HTML"
echo "   • Name it: map_sidebarh (NO .html extension!)"
echo "   • Copy content from: map_sidebarh.html"
echo "   • Save (Command+S)"
echo ""
echo "📤 STEP 3: Upload GS File"
echo "   • Click + button → Script"
echo "   • Name it: map_sidebar"
echo "   • Copy content from: map_sidebar.gs"
echo "   • Save (Command+S)"
echo ""
echo "📤 STEP 4: Update/Add MASTER_onOpen.gs"
echo "   • Find existing MASTER_onOpen.gs OR create new Script"
echo "   • Copy content from: MASTER_onOpen.gs"
echo "   • Save (Command+S)"
echo ""
echo "⚙️  STEP 5: Configure Script Properties"
echo "   1. File → Project Settings (or ⚙️ icon)"
echo "   2. Scroll to 'Script Properties'"
echo "   3. Click 'Add script property'"
echo "   4. Property: GOOGLE_MAPS_API_KEY"
echo "   5. Value: AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0"
echo "   6. Click 'Save script properties'"
echo ""
echo "⚙️  STEP 6: Enable BigQuery API"
echo "   1. Services (+ icon in left sidebar)"
echo "   2. Find 'BigQuery API'"
echo "   3. Version: v2"
echo "   4. Click 'Add'"
echo ""
echo "⚙️  STEP 7: Update OAuth Scopes (appsscript.json)"
echo "   1. View → Show manifest file"
echo "   2. Find appsscript.json in left sidebar"
echo "   3. Ensure 'oauthScopes' contains:"
echo '      "https://www.googleapis.com/auth/spreadsheets"'
echo '      "https://www.googleapis.com/auth/script.container.ui"'
echo '      "https://www.googleapis.com/auth/bigquery"'
echo ""
echo "🔐 STEP 8: Authorize Permissions"
echo "   1. Select function: showMapSidebar"
echo "   2. Click Run (▶️)"
echo "   3. Click 'Review Permissions'"
echo "   4. Select your Google account"
echo "   5. Click 'Advanced' → 'Go to [project] (unsafe)'"
echo "   6. Click 'Allow'"
echo ""
echo "✅ STEP 9: Test in Google Sheets"
echo "   1. Close Apps Script editor"
echo "   2. In Google Sheets, refresh (Command+R)"
echo "   3. Menu: 🗺️ Geographic Map → Show DNO & GSP Boundaries"
echo "   4. Sidebar should appear with map and 4 buttons"
echo "   5. Click 'Show DNO Regions' → Blue polygons appear"
echo "   6. Click 'Show GSP Regions' → Green polygons appear"
echo ""
echo "=========================================="
echo "✅ READY FOR DEPLOYMENT!"
echo "=========================================="
