#!/bin/bash
# Quick Dashboard Update Script
# Run this to manually update the dashboard with latest data

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/.."

echo "🔄 DASHBOARD UPDATE SCRIPT"
echo "=" * 80
echo ""

# Check if Python updater exists
if [ ! -f "realtime_dashboard_updater.py" ]; then
    echo "❌ Error: realtime_dashboard_updater.py not found"
    exit 1
fi

# Check Python version
PYTHON_CMD=$(command -v python3 || command -v python)
if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Error: Python not found"
    exit 1
fi

echo "🐍 Python: $PYTHON_CMD"
echo ""

# Check credentials
if [ ! -f "inner-cinema-credentials.json" ]; then
    echo "⚠️  Warning: BigQuery credentials not found"
    echo "   Expected: inner-cinema-credentials.json"
fi

if [ ! -f "token.pickle" ]; then
    echo "⚠️  Warning: Google Sheets token not found"
    echo "   Expected: token.pickle"
    echo "   Run: python3 update_analysis_bi_enhanced.py (first time)"
fi

echo ""
echo "📊 Updating dashboard..."
echo ""

# Run the updater
$PYTHON_CMD realtime_dashboard_updater.py

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "✅ Dashboard updated successfully!"
    echo ""
    echo "🔗 View dashboard:"
    echo "   https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/edit"
    echo ""
    echo "📝 Check logs:"
    echo "   tail -f logs/dashboard_updater.log"
    echo ""
else
    echo ""
    echo "❌ Update failed with exit code: $EXIT_CODE"
    echo ""
    echo "🔍 Troubleshooting:"
    echo "   1. Check logs: tail -50 logs/dashboard_updater.log"
    echo "   2. Verify credentials: ls -la *credentials.json token.pickle"
    echo "   3. Test BigQuery: python3 -c 'from google.cloud import bigquery; print(\"OK\")'"
    echo ""
    exit $EXIT_CODE
fi
