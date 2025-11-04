#!/bin/bash

# 📊 Quick Commands for Google Sheets Export

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║        📊 Google Drive → Sheets Export Commands             ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

echo "🔧 SETUP (one-time):"
echo "--------------------------------------------------------------"
echo "# Update UpCloud deployment with Sheets support"
echo "./update-deployment-sheets.sh"
echo ""

echo "📊 EXPORT METADATA:"
echo "--------------------------------------------------------------"
echo "# Run the export (creates Google Sheet(s) automatically)"
echo "ssh root@94.237.55.15 'docker exec driveindexer python scripts/export_to_sheets.py'"
echo ""

echo "🔍 VERIFICATION:"
echo "--------------------------------------------------------------"
echo "# Check if script is installed"
echo "ssh root@94.237.55.15 'docker exec driveindexer ls -la scripts/export_to_sheets.py'"
echo ""
echo "# Test gspread library"
echo "ssh root@94.237.55.15 'docker exec driveindexer python -c \"import gspread; print(\\\"✅ Ready\\\")\"'"
echo ""

echo "📋 MONITORING:"
echo "--------------------------------------------------------------"
echo "# View export logs"
echo "ssh root@94.237.55.15 'docker logs driveindexer --tail 50'"
echo ""
echo "# Check installed packages"
echo "ssh root@94.237.55.15 'docker exec driveindexer pip list | grep gspread'"
echo ""

echo "🔄 FULL PIPELINE WITH EXPORT:"
echo "--------------------------------------------------------------"
echo "# Index → Extract → Embeddings → Export to Sheets"
echo "ssh root@94.237.55.15 << 'EOF'"
echo "docker exec driveindexer python -m src.cli index-drive"
echo "docker exec driveindexer python -m src.cli extract"
echo "docker exec driveindexer python -m src.cli build-embeddings"
echo "docker exec driveindexer python scripts/export_to_sheets.py"
echo "EOF"
echo ""

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  ℹ️  Full documentation: SHEETS_EXPORT_GUIDE.md              ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
