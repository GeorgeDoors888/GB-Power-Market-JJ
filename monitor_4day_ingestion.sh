#!/bin/bash
"""
Monitor 4-Day Ingestion Progress
Tracks the progress of the complete 4-day Elexon data ingestion
"""

echo "🔍 4-Day Elexon Ingestion Monitor"
echo "================================="
echo "⏰ Current time: $(date)"
echo ""

# Check if ingestion process is running
if pgrep -f "ingest_4day_complete.py" > /dev/null; then
    echo "✅ 4-day ingestion is RUNNING"
    PID=$(pgrep -f "ingest_4day_complete.py")
    echo "🆔 Process ID: $PID"

    # Show process start time
    START_TIME=$(ps -o lstart= -p $PID 2>/dev/null)
    if [ ! -z "$START_TIME" ]; then
        echo "🚀 Started: $START_TIME"
    fi
else
    echo "⭕ 4-day ingestion is NOT running"
fi

echo ""
echo "📊 Recent BigQuery Dataset Activity:"
echo "====================================="

# Check for recent ingestion activity in logs (if any)
if [ -f "logs/ingestion_4day.log" ]; then
    echo "📄 Last 5 lines from ingestion log:"
    tail -5 logs/ingestion_4day.log
else
    echo "📄 No specific 4-day ingestion log found"
fi

echo ""
echo "🔄 Background Python Processes:"
echo "==============================="
ps aux | grep python | grep -E "(ingest|elexon)" | grep -v grep | head -5

echo ""
echo "💾 Recent BigQuery Activity:"
echo "============================"

# Show recent activity if bq is available
if command -v bq &> /dev/null; then
    echo "🔍 Checking recent dataset updates..."
    # This would need proper authentication, but we'll show the command
    echo "📋 To check latest data: bq query --use_legacy_sql=false 'SELECT _dataset, MAX(_ingested_utc) as last_update FROM \`jibber-jabber-knowledge.uk_energy_insights.*\` WHERE _ingested_utc >= \"2025-09-16\" GROUP BY _dataset ORDER BY last_update DESC LIMIT 10'"
else
    echo "📋 BigQuery CLI not available for checking updates"
fi

echo ""
echo "🎯 Expected Processing Groups:"
echo "=============================="
echo "1. 🔥 High Frequency: FREQ, FUELINST, BOD, BOALF, COSTS, DISBSAD"
echo "2. ⚖️  Settlement: MELS, MILS, QAS, NETBSAD, PN, QPN"
echo "3. 📈 Forecasts: NDF, TSDF, INDDEM, INDGEN, FUELHH"
echo "4. ⚡ Generation: UOU2T3YW, UOU2T14D, UOU2T52W, B1610, B1620"
echo "5. ⚖️  Balancing: MID, RDRI, RDRE, RURE, RURI, LOLPDRM"
echo "6. 🖥️  System Data: SYSWARN, SYSDEM, TEMP, WINDFOR, ITSDO"

echo ""
echo "📅 Target Date Range: 2025-09-16 to 2025-09-20 (4 days)"
echo "🔄 Run this monitor script again to check progress: ./monitor_4day_ingestion.sh"
