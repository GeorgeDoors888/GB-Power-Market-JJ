#!/bin/bash
# Deploy GB Live Dashboard Sparklines via CLASP

set -e

echo "======================================================================"
echo "🚀 GB LIVE DASHBOARD - SPARKLINE DEPLOYMENT VIA CLASP"
echo "======================================================================"

cd /home/george/GB-Power-Market-JJ/bg-sparklines-clasp

# Check if CLASP is installed
if ! command -v clasp &> /dev/null; then
    echo "❌ CLASP not found. Installing..."
    npm install -g @google/clasp
fi

echo "✅ CLASP installed"

# Check if logged in
if [ ! -f "$HOME/.clasprc.json" ]; then
    echo "🔐 Please log in to CLASP..."
    clasp login
fi

echo "✅ CLASP authenticated"

# Check if .clasp.json has scriptId
SCRIPT_ID=$(cat .clasp.json | grep -o '"scriptId":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SCRIPT_ID" ]; then
    echo "📝 Creating new Apps Script project..."
    clasp create --type sheets --title "GB Live Sparklines" --rootDir .
    
    echo ""
    echo "⚠️  IMPORTANT: Manual step required!"
    echo "======================================================================"
    echo "1. Open https://script.google.com"
    echo "2. Find 'GB Live Sparklines' project"
    echo "3. Go to: Project Settings (⚙️)"
    echo "4. Click: Add container"
    echo "5. Paste spreadsheet ID: 1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I"
    echo "6. Save"
    echo ""
    echo "Then run this script again to push code."
    echo "======================================================================"
    exit 0
fi

echo "✅ Apps Script project linked (ID: $SCRIPT_ID)"

# Push code
echo "📤 Pushing code to Google Apps Script..."
clasp push -f

echo ""
echo "======================================================================"
echo "✅ DEPLOYMENT COMPLETE!"
echo "======================================================================"
echo ""
echo "📋 Next steps:"
echo "   1. Open: https://docs.google.com/spreadsheets/d/1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I/"
echo "   2. Look for menu: ⚡ GB Live Dashboard"
echo "   3. Click: ✨ Write Sparkline Formulas"
echo "   4. Wait 5 seconds"
echo "   5. ✅ Verify sparklines appear in columns C and F"
echo ""
echo "🔧 Optional: Deploy as webhook for Python integration"
echo "   Run: clasp deploy --description 'Sparkline Writer v1'"
echo ""
echo "======================================================================"
