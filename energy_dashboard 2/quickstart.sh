#!/bin/bash
# Quick Start Script for GB Energy Dashboard

set -e

echo "════════════════════════════════════════════════════════════"
echo "GB Energy Dashboard - Quick Start"
echo "════════════════════════════════════════════════════════════"

cd "$(dirname "$0")"

# Check credentials
if [ ! -f "../inner-cinema-credentials.json" ]; then
    echo "❌ Error: inner-cinema-credentials.json not found"
    exit 1
fi

export GOOGLE_APPLICATION_CREDENTIALS="../inner-cinema-credentials.json"
echo "✅ Credentials loaded"

# Create output directory
mkdir -p out
echo "✅ Output directory ready"

# Test BtM PPA module
echo ""
echo "🧪 Testing BtM PPA Module..."
python3 test_btm_ppa.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ BtM PPA module working!"
    echo "📊 Chart saved: out/test_btm_ppa.png"
    echo ""
    echo "════════════════════════════════════════════════════════════"
    echo "Next Steps:"
    echo "  1. Open out/test_btm_ppa.png to view the chart"
    echo "  2. Run full dashboard: python3 dashboard.py"
    echo "  3. Check Google Sheets for updated KPIs"
    echo "════════════════════════════════════════════════════════════"
else
    echo ""
    echo "❌ Test failed - see error above"
    exit 1
fi
