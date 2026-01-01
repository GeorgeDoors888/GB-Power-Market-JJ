#!/bin/bash
# Automated Clasp Deployment (Run when network available)

cd /home/george/GB-Power-Market-JJ

echo "========================================================================"
echo "  AUTOMATED APPS SCRIPT DEPLOYMENT VIA CLASP"
echo "========================================================================"
echo ""

# Check clasp authentication
echo "1️⃣ Checking clasp authentication..."
if clasp login --status 2>&1 | grep -q "Logged in"; then
    echo "   ✅ Clasp authenticated"
elif [ -f ~/.clasprc.json ]; then
    echo "   ✅ Clasp credentials found"
else
    echo "   ❌ Not authenticated - run: clasp login"
    exit 1
fi

# Verify files are ready
echo ""
echo "2️⃣ Verifying files in appsscript_v3/..."
FILES_READY=true

check_file() {
    if [ -f "appsscript_v3/$1" ]; then
        SIZE=$(stat -c%s "appsscript_v3/$1")
        echo "   ✅ $1 ($SIZE bytes)"
    else
        echo "   ❌ $1 MISSING!"
        FILES_READY=false
    fi
}

check_file "appsscript.json"
check_file "map_sidebar_v2.html"
check_file "map_sidebar.gs"
check_file "MASTER_onOpen.gs"

if [ "$FILES_READY" = false ]; then
    echo ""
    echo "❌ Missing files - run preparation script first"
    exit 1
fi

# Show what will be pushed
echo ""
echo "3️⃣ Files to be pushed:"
ls -lh appsscript_v3/*.{json,html,gs} 2>/dev/null | awk '{print "   " $9 " (" $5 ")"}'

# Push to Apps Script
echo ""
echo "4️⃣ Pushing to Apps Script..."
echo "   Script ID: $(jq -r .scriptId .clasp.json)"
echo ""

clasp push --force

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ =================================="
    echo "✅  DEPLOYMENT SUCCESSFUL!"
    echo "✅ =================================="
    echo ""
    echo "📋 Next steps (MANUAL):"
    echo ""
    echo "   1. Open Apps Script: Extensions → Apps Script"
    echo ""
    echo "   2. Authorize permissions:"
    echo "      • Select function: showMapSidebar"
    echo "      • Click Run (▶️)"
    echo "      • Click 'Review Permissions'"
    echo "      • Select your Google account"
    echo "      • Click 'Advanced' → 'Go to [project] (unsafe)'"
    echo "      • Click 'Allow'"
    echo ""
    echo "   3. Add API key to Script Properties:"
    echo "      • File → Project Settings"
    echo "      • Script Properties → Add property"
    echo "      • Name: GOOGLE_MAPS_API_KEY"
    echo "      • Value: AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0"
    echo ""
    echo "   4. Enable BigQuery API:"
    echo "      • Services (+) → BigQuery API → v2 → Add"
    echo ""
    echo "   5. Test in Google Sheets:"
    echo "      • Refresh sheet (Command+R)"
    echo "      • Click: 🗺️ Geographic Map → Show DNO & GSP Boundaries"
    echo "      • Try search interface (should work now)"
    echo ""
else
    echo ""
    echo "❌ =================================="
    echo "❌  DEPLOYMENT FAILED"
    echo "❌ =================================="
    echo ""
    echo "Possible causes:"
    echo "   • Network connectivity issue"
    echo "   • Authentication expired (run: clasp login)"
    echo "   • Invalid Script ID in .clasp.json"
    echo ""
    echo "Fallback: Use manual upload guide"
fi
