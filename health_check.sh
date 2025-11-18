#!/bin/bash
# IRIS Pipeline Health Check
# Runs every 5 minutes via cron to detect failures

SCRIPT_DIR="/opt/iris-pipeline"
LOG_DIR="$SCRIPT_DIR/logs"
ALERT_FILE="$SCRIPT_DIR/alerts.txt"
PROJECT_ID="inner-cinema-476211-u9"

# Function to send alert
send_alert() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ALERT: $1" | tee -a "$ALERT_FILE"
}

# Function to restart pipeline
restart_pipeline() {
    send_alert "🔄 Restarting IRIS pipeline..."
    cd "$SCRIPT_DIR"
    ./start_iris_pipeline.sh >> "$LOG_DIR/health_check.log" 2>&1
}

echo "$(date '+%Y-%m-%d %H:%M:%S') - Running health check..." >> "$LOG_DIR/health_check.log"

# Check 1: Is uploader running?
if ! screen -ls | grep -q iris_uploader; then
    send_alert "❌ IRIS UPLOADER IS DOWN!"
    restart_pipeline
    exit 1
fi

# Check 2: Is client running?
if ! screen -ls | grep -q iris_client; then
    send_alert "❌ IRIS CLIENT IS DOWN!"
    restart_pipeline
    exit 1
fi

# Check 3: Uploader log activity (should update every ~5 minutes)
if [ -f "$LOG_DIR/iris_uploader.log" ]; then
    # Get last log timestamp
    LAST_LOG=$(tail -1 "$LOG_DIR/iris_uploader.log" 2>/dev/null | grep -oE '^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}')
    
    if [ -n "$LAST_LOG" ]; then
        LAST_EPOCH=$(date -d "$LAST_LOG" +%s 2>/dev/null || echo 0)
        NOW_EPOCH=$(date +%s)
        AGE=$((NOW_EPOCH - LAST_EPOCH))
        
        # Alert if no activity for 15 minutes
        if [ $AGE -gt 900 ]; then
            send_alert "⚠️ Uploader log stale! Last update: $((AGE/60)) minutes ago"
            send_alert "Last log entry: $LAST_LOG"
            # Don't restart yet, just alert
        fi
    fi
fi

# Check 4: BigQuery data freshness
export GOOGLE_APPLICATION_CREDENTIALS="$SCRIPT_DIR/service_account.json"

python3 - <<'PYEOF'
from google.cloud import bigquery
from datetime import datetime
import pandas as pd
import sys

try:
    client = bigquery.Client(project='inner-cinema-476211-u9')
    
    # Check critical tables
    tables = {
        'bmrs_fuelinst_iris': 'Fuel Generation',
        'bmrs_indo_iris': 'Interconnectors'
    }
    
    alerts = []
    
    for table, name in tables.items():
        query = f"""
        SELECT MAX(publishTime) as latest_time
        FROM `inner-cinema-476211-u9.uk_energy_prod.{table}`
        WHERE publishTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 DAY)
        """
        
        df = client.query(query).to_dataframe()
        latest = df.iloc[0]['latest_time']
        
        if latest and pd.notna(latest):
            age_hours = (datetime.now(latest.tzinfo) - latest).total_seconds() / 3600
            
            # Alert if data is >3 hours old (allows some buffer)
            if age_hours > 3:
                alerts.append(f"⚠️ {name} ({table}): {age_hours:.1f}h old (expected <2h)")
        else:
            alerts.append(f"❌ {name} ({table}): NO DATA")
    
    if alerts:
        for alert in alerts:
            print(alert, file=sys.stderr)
        sys.exit(1)
    
    print("✅ BigQuery data is fresh")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Health check error: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

BQ_CHECK_STATUS=$?

if [ $BQ_CHECK_STATUS -ne 0 ]; then
    send_alert "⚠️ BigQuery data is stale! Check IRIS pipeline."
    # Don't auto-restart for stale data (might be backlog processing)
fi

# Check 5: Disk space
DISK_USAGE=$(df -h "$SCRIPT_DIR" | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    send_alert "⚠️ Disk usage high: ${DISK_USAGE}%"
fi

# All checks passed
echo "$(date '+%Y-%m-%d %H:%M:%S') - ✅ Health check passed" >> "$LOG_DIR/health_check.log"
exit 0
