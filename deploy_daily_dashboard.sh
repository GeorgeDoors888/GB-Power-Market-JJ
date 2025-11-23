#!/bin/bash
# Deploy Daily Dashboard Auto-Updater to UpCloud Server
# Run this script from local machine

echo "=================================================="
echo "DAILY DASHBOARD DEPLOYMENT TO UPCLOUD"
echo "=================================================="
echo ""

UPCLOUD_IP="94.237.55.234"
REMOTE_DIR="/root/GB-Power-Market-JJ"

echo "📤 Uploading Python script..."
scp daily_dashboard_auto_updater.py root@${UPCLOUD_IP}:${REMOTE_DIR}/

echo ""
echo "📤 Uploading Apps Script (for manual installation)..."
scp daily_dashboard_charts.gs root@${UPCLOUD_IP}:${REMOTE_DIR}/

echo ""
echo "📤 Uploading documentation..."
scp DAILY_DASHBOARD_SETUP.md root@${UPCLOUD_IP}:${REMOTE_DIR}/

echo ""
echo "✅ Files uploaded!"
echo ""
echo "🔧 Setting up cron job..."

ssh root@${UPCLOUD_IP} << 'ENDSSH'
cd /root/GB-Power-Market-JJ

# Check if cron job already exists
if crontab -l | grep -q "daily_dashboard_auto_updater.py"; then
    echo "⚠️  Cron job already exists"
else
    echo "➕ Adding cron job (every 30 minutes)..."
    (crontab -l 2>/dev/null; echo "*/30 * * * * cd /root/GB-Power-Market-JJ && /usr/bin/python3 daily_dashboard_auto_updater.py >> logs/daily_dashboard.log 2>&1") | crontab -
    echo "✅ Cron job added"
fi

echo ""
echo "🧪 Testing script..."
python3 daily_dashboard_auto_updater.py

ENDSSH

echo ""
echo "=================================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=================================================="
echo ""
echo "📋 NEXT STEPS:"
echo "1. Open Google Sheets: https://docs.google.com/spreadsheets/d/12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8/"
echo "2. Go to Extensions → Apps Script"
echo "3. Create new file: DailyDashboardCharts"
echo "4. Copy contents of daily_dashboard_charts.gs"
echo "5. Run function: setupAutoRefreshTrigger"
echo "6. Run function: refreshAllCharts"
echo ""
echo "📊 Check Dashboard rows 18-29 for KPIs"
echo "📈 Check chart sheets: Chart_Prices, Chart_Demand_Gen, etc."
echo ""
echo "📝 Monitor logs:"
echo "   ssh root@${UPCLOUD_IP} 'tail -f /root/GB-Power-Market-JJ/logs/daily_dashboard.log'"
