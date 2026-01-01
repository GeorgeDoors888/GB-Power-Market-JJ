#!/bin/bash
# Quick diagnostic deployment

set -e

echo "📋 Deploying diagnostic test to Apps Script..."
echo ""

cd /home/george/GB-Power-Market-JJ/appsscript_v3

echo "Files to deploy:"
ls -lh DiagnosticMapTest.gs

echo ""
echo "Pushing to Apps Script..."
clasp push --force

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 NEXT STEPS:"
echo "1. Open Google Sheets"
echo "2. Go to Extensions → Apps Script"
echo "3. Select 'DiagnosticMapTest.gs' from file list"
echo "4. Run function: testMapSidebarDeployment"
echo "5. View logs in Execution log panel"
echo ""
echo "This will tell us exactly what's wrong!"
