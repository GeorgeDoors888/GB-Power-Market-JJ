#!/bin/bash
# Deploy diagnostic test from iMac

set -e

echo "📋 Deploying Diagnostic Test to Apps Script"
echo "============================================"
echo ""

# Copy diagnostic file to iMac
echo "1️⃣ Copying DiagnosticMapTest.gs to iMac..."
scp /home/george/GB-Power-Market-JJ/appsscript_v3/DiagnosticMapTest.gs \
    george@192.168.1.245:/Users/george/temp/appsscript_v3/

echo ""
echo "2️⃣ Deploying via clasp on iMac..."
ssh george@192.168.1.245 << 'ENDSSH'
cd /Users/george/temp/appsscript_v3
echo "Files to deploy:"
ls -lh DiagnosticMapTest.gs

echo ""
echo "Pushing to Apps Script..."
clasp push --force

echo ""
echo "✅ Deployment complete!"
ENDSSH

echo ""
echo "================================================"
echo "✅ DIAGNOSTIC DEPLOYED!"
echo "================================================"
echo ""
echo "📝 NOW DO THIS IN GOOGLE SHEETS:"
echo ""
echo "1. Open: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/edit"
echo ""
echo "2. Extensions → Apps Script"
echo ""
echo "3. In left sidebar, click: DiagnosticMapTest.gs"
echo ""
echo "4. Select function dropdown (top): testMapSidebarDeployment"
echo ""
echo "5. Click ▶️ Run"
echo ""
echo "6. View → Execution log"
echo ""
echo "This will show EXACTLY what's wrong!"
echo ""
echo "================================================"
