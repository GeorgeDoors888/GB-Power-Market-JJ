#!/bin/bash
# Automated Live Dashboard v2 Complete Updater
# Runs every 5 minutes via cron
# CORRECT SPREADSHEET: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
# Updates: KPIs, 48-period sparklines, generation mix, interconnectors, outages, constraints

cd /home/george/GB-Power-Market-JJ

# Create logs directory if not exists
mkdir -p logs

# Run complete updater and log output (SAME AS update_live_dashboard_v2.py but with sparklines)
/usr/bin/python3 update_gb_live_complete.py >> logs/live_dashboard_v2_complete.log 2>&1

# Rotate log if it gets too big (keep last 1000 lines)
if [ -f logs/bg_live_updater.log ]; then
    tail -n 1000 logs/bg_live_updater.log > logs/bg_live_updater.log.tmp
    mv logs/bg_live_updater.log.tmp logs/bg_live_updater.log
fi
