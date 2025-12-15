#!/bin/bash
# Update dashboard data and refresh
set -e

echo "🔄 Updating BigQuery table..."
python3 build_publication_table_current.py

echo ""
echo "✅ BigQuery table updated!"
echo ""
echo "📊 Now refresh Google Sheets:"
echo "   1. Open: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit"
echo "   2. Make sure 'Live Dashboard' tab is active"
echo "   3. Click: GB Live Dashboard → Force Refresh Dashboard"
