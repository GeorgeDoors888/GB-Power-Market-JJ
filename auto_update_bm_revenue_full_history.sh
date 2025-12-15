#!/bin/bash
# Auto-update BM Revenue Analysis - Full History
# Runs daily at 5:00 AM to refresh comprehensive BM revenue data

cd /home/george/GB-Power-Market-JJ

echo "=================================================================" >> logs/bm_revenue_full_history.log
echo "BM Revenue Full History update: $(date)" >> logs/bm_revenue_full_history.log

/usr/bin/python3 update_bm_revenue_full_history.py >> logs/bm_revenue_full_history.log 2>&1

if [ $? -eq 0 ]; then
    echo "✅ BM Revenue Full History update successful" >> logs/bm_revenue_full_history.log
else
    echo "❌ BM Revenue Full History update failed" >> logs/bm_revenue_full_history.log
fi

echo "" >> logs/bm_revenue_full_history.log
