#!/bin/bash
# Auto-update Live Dashboard v2 - Runs every 5 minutes via cron
# Logs to: ~/dashboard_v2_updates.log

cd /home/george/GB-Power-Market-JJ

echo "=================================================================" >> ~/dashboard_v2_updates.log
echo "Dashboard update: $(date)" >> ~/dashboard_v2_updates.log

# Run main dashboard update (sparklines, KPIs, gen mix, interconnectors, outages)
# NOTE: Outages are now integrated into main script (no separate call needed)
/usr/bin/python3 update_live_dashboard_v2.py >> ~/dashboard_v2_updates.log 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Main dashboard update successful (includes outages)" >> ~/dashboard_v2_updates.log
else
    echo "❌ Main dashboard update failed" >> ~/dashboard_v2_updates.log
fi

# Run wind chart update (every 5 minutes)
/usr/bin/python3 update_intraday_wind_chart.py >> ~/dashboard_v2_updates.log 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Wind chart update successful" >> ~/dashboard_v2_updates.log
else
    echo "❌ Wind chart update failed" >> ~/dashboard_v2_updates.log
fi

# Run battery BM revenue update (every 5 minutes)
/usr/bin/python3 update_battery_bm_revenue.py >> ~/dashboard_v2_updates.log 2>&1

if [ $? -eq 0 ]; then
    echo "✅ Battery revenue update successful" >> ~/dashboard_v2_updates.log
else
    echo "❌ Battery revenue update failed" >> ~/dashboard_v2_updates.log
fi

echo "" >> ~/dashboard_v2_updates.log
