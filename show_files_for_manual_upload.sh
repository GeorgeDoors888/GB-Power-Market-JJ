#!/bin/bash
# Quick Manual Upload Helper - Generate file contents for copy-paste

cd /home/george/GB-Power-Market-JJ/appsscript_v3

echo "========================================================================"
echo "  MANUAL UPLOAD HELPER - Copy/Paste These Files"
echo "========================================================================"
echo ""
echo "Open Google Sheets → Extensions → Apps Script"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FILE 1: appsscript.json (OAuth Manifest)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "View → Show manifest file → Click appsscript.json → REPLACE ALL with:"
echo ""
cat appsscript.json
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FILE 2: map_sidebar.gs (Map Backend)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "+ button → Script → Name: map_sidebar → Paste:"
echo ""
echo "# COPY FROM LINE BELOW:"
echo "═════════════════════════════════════════════════════════════════════"
cat map_sidebar.gs
echo "═════════════════════════════════════════════════════════════════════"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FILE 3: map_sidebarh.html (Map UI)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "+ button → HTML → Name: map_sidebarh → Paste:"
echo ""
echo "# COPY FROM LINE BELOW:"
echo "═════════════════════════════════════════════════════════════════════"
cat map_sidebarh.html
echo "═════════════════════════════════════════════════════════════════════"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "FILE 4: MASTER_onOpen.gs (Menu Integration)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Find existing MASTER_onOpen OR + button → Script → Name: MASTER_onOpen → Paste:"
echo ""
echo "# COPY FROM LINE BELOW:"
echo "═════════════════════════════════════════════════════════════════════"
cat MASTER_onOpen.gs
echo "═════════════════════════════════════════════════════════════════════"
echo ""

echo "========================================================================"
echo "✅ AFTER UPLOADING ALL FILES"
echo "========================================================================"
echo ""
echo "1. Authorize new permissions:"
echo "   • Select function: showMapSidebar"
echo "   • Run (▶️) → Review Permissions → Advanced → Allow"
echo ""
echo "2. Add API key:"
echo "   • File → Project Settings → Script Properties"
echo "   • Add: GOOGLE_MAPS_API_KEY = AIzaSyDcOg5CC4rbf0SujJ4JurGWknUlawVnct0"
echo ""
echo "3. Enable BigQuery:"
echo "   • Services (+) → BigQuery API → v2 → Add"
echo ""
echo "4. Test in Google Sheets:"
echo "   • Refresh sheet"
echo "   • 🗺️ Geographic Map → Show DNO & GSP Boundaries"
echo ""
