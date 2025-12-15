#!/bin/bash
#
# Quick Dashboard Refresh Script
# Pulls latest data from BigQuery and updates Google Sheets
#

cd "$(dirname "$0")/tools" || exit 1

echo "🔄 Refreshing GB Power Market Dashboard..."
echo ""

/opt/homebrew/bin/python3 refresh_live_dashboard.py

echo ""
echo "✅ Done! Check your Google Sheets dashboard:"
echo "   https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/"
