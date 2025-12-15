#!/bin/bash
# Complete dashboard refresh with all data including unavailability

cd "$(dirname "$0")"

echo "======================================================================"
echo "🔄 COMPLETE DASHBOARD REFRESH"
echo "======================================================================"
echo ""

# 1. Update interconnector breakdown
echo "📡 Step 1/5: Updating interconnector breakdown..."
python3 tools/fix_dashboard_comprehensive.py 2>&1 | tail -10
echo ""

# 2. Refresh main dashboard data (48 SPs)
echo "📊 Step 2/5: Refreshing settlement period data..."
python3 tools/refresh_live_dashboard.py 2>&1 | tail -10
echo ""

# 3. Update dashboard display with freshness indicator
echo "🎨 Step 3/5: Updating dashboard display..."
python3 tools/update_dashboard_display.py 2>&1 | tail -10
echo ""

# 4. Add unavailability data to Dashboard
echo "⚠️  Step 4/5: Adding power station outages..."
python3 add_unavailability_to_dashboard.py 2>&1 | tail -10
echo ""

# 5. Update REMIT Unavailability tab (backup)
echo "📋 Step 5/5: Updating REMIT tab..."
python3 update_unavailability.py 2>&1 | tail -10
echo ""

echo "======================================================================"
echo "✅ COMPLETE REFRESH DONE"
echo "======================================================================"
echo ""
echo "📊 Dashboard updated with:"
echo "   ✅ Interconnectors with country flags (🇫🇷 🇮🇪 🇳🇱 🇧🇪 🇳🇴 🇩🇰)"
echo "   ✅ Data freshness indicator (✅ <10min | ⚠️ 10-60min | 🔴 >60min)"
echo "   ✅ Settlement period data (48 periods)"
echo "   ✅ Power station outages with visual indicators"
echo "   ✅ Auto-refresh timestamp"
echo ""
echo "🌐 View Dashboard:"
echo "   https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
echo ""
