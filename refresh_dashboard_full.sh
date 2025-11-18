#!/bin/bash
# Comprehensive dashboard refresh with all data sources

cd "$(dirname "$0")"

echo "=================================="
echo "🔄 DASHBOARD COMPREHENSIVE REFRESH"
echo "=================================="
echo ""

# 1. Refresh interconnector breakdown
echo "📡 Step 1/4: Updating interconnector breakdown..."
python3 tools/fix_dashboard_comprehensive.py 2>&1 | tail -20

# 2. Refresh unavailability data
echo ""
echo "⚠️  Step 2/4: Updating REMIT unavailability data..."
python3 update_unavailability.py 2>&1 | tail -15

# 3. Refresh live dashboard data (48 SPs)
echo ""
echo "📊 Step 3/4: Refreshing live dashboard data..."
python3 tools/refresh_live_dashboard.py 2>&1 | tail -10

# 4. Update dashboard display
echo ""
echo "🎨 Step 4/4: Updating dashboard display..."
python3 tools/update_dashboard_display.py 2>&1 | tail -10

echo ""
echo "=================================="
echo "✅ COMPREHENSIVE REFRESH COMPLETE"
echo "=================================="
echo ""
echo "📋 Check Dashboard at:"
echo "   https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8"
echo ""
