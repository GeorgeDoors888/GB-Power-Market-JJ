#!/bin/bash
# Automated Live Dashboard v2 Complete Updater
# Runs every 5 minutes via cron
# CORRECT SPREADSHEET: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

cd /home/george/GB-Power-Market-JJ

# Create logs directory if not exists
mkdir -p logs

# Run CORRECT updater (update_live_dashboard_v2.py - NOT update_gb_live_complete.py!)
/usr/bin/python3 update_live_dashboard_v2.py >> logs/live_dashboard_v2_complete.log 2>&1

# Rotate log if it gets too big (keep last 1000 lines)
if [ -f logs/live_dashboard_v2_complete.log ]; then
    tail -n 1000 logs/live_dashboard_v2_complete.log > logs/live_dashboard_v2_complete.log.tmp
    mv logs/live_dashboard_v2_complete.log.tmp logs/live_dashboard_v2_complete.log
fi
