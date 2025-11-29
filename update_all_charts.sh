#!/bin/bash
# Master script to update all chart data for Dashboard V3
cd /Users/georgemajor/GB-Power-Market-JJ

echo "🚀 DASHBOARD V3 - UPDATING ALL CHART DATA"
echo "==========================================="

echo ""
echo "1️⃣ Updating wind performance data..."
python3 update_wind_data.py

echo ""
echo "2️⃣ Updating system frequency data..."
python3 update_frequency.py

echo ""
echo "3️⃣ Updating BM costs data..."
python3 update_bm_costs.py

echo ""
echo "4️⃣ Updating outages data..."
python3 update_outages.py

echo ""
echo "✅ ALL CHART DATA UPDATED!"
echo "📊 Open Google Sheets and run buildAllCharts() from Apps Script"
echo "🎨 Run formatDashboard() to apply styling"
