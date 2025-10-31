#!/bin/bash

# IRIS Overnight Monitoring Script
# Runs every 5 minutes and logs system health
# Usage: ./iris_overnight_monitor.sh

LOG_FILE="iris_overnight_monitor.log"
ALERT_FILE="iris_overnight_alerts.log"

# Configuration
CLIENT_PID=81929
PROCESSOR_PID=15141
MAX_FILE_BACKLOG=50000
MAX_DATA_LAG_MINUTES=10
CHECK_INTERVAL=300  # 5 minutes

echo "========================================" | tee -a "$LOG_FILE"
echo "🌙 IRIS Overnight Monitoring Started" | tee -a "$LOG_FILE"
echo "Started: $(date)" | tee -a "$LOG_FILE"
echo "Check Interval: ${CHECK_INTERVAL}s (5 minutes)" | tee -a "$LOG_FILE"
echo "Will run until manually stopped (Ctrl+C)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"

# Function to check process status
check_process() {
    local pid=$1
    local name=$2
    
    if ps -p $pid > /dev/null 2>&1; then
        echo "✅ $name (PID: $pid) - Running"
        return 0
    else
        echo "❌ $name (PID: $pid) - STOPPED"
        echo "⚠️ ALERT: $name stopped at $(date)" >> "$ALERT_FILE"
        return 1
    fi
}

# Function to count files in iris_data
count_files() {
    local count=$(find iris-clients/python/iris_data -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    echo "$count"
}

# Function to check BigQuery data lag
check_data_lag() {
    local latest_time=$(bq query --format=csv --use_legacy_sql=false --max_rows=1 \
        'SELECT MAX(ingested_utc) as latest 
         FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`' 2>/dev/null | tail -1)
    
    if [ -z "$latest_time" ] || [ "$latest_time" = "latest" ]; then
        echo "ERROR: Could not query BigQuery"
        return 999
    fi
    
    # Calculate lag in minutes (approximate)
    local current_epoch=$(date +%s)
    local latest_epoch=$(date -j -f "%Y-%m-%d %H:%M:%S" "$latest_time" +%s 2>/dev/null || echo 0)
    
    if [ "$latest_epoch" = "0" ]; then
        echo "ERROR: Could not parse timestamp"
        return 999
    fi
    
    local lag_seconds=$((current_epoch - latest_epoch))
    local lag_minutes=$((lag_seconds / 60))
    
    echo "$lag_minutes"
}

# Function to get record counts
get_record_counts() {
    bq query --format=csv --use_legacy_sql=false \
        'SELECT 
            "BOD" as dataset, COUNT(*) as records FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
         UNION ALL SELECT "BOALF", COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
         UNION ALL SELECT "MELS", COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mels_iris`
         UNION ALL SELECT "FREQ", COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
         ORDER BY records DESC' 2>/dev/null | tail -n +2
}

# Function to check for errors in logs
check_recent_errors() {
    local error_count=$(tail -100 iris_processor.log 2>/dev/null | grep -i "error\|exception\|failed" | wc -l | tr -d ' ')
    echo "$error_count"
}

# Counter for iterations
iteration=0

# Main monitoring loop
while true; do
    iteration=$((iteration + 1))
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
    echo "📊 Check #$iteration - $timestamp" | tee -a "$LOG_FILE"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" | tee -a "$LOG_FILE"
    
    # 1. Process Status
    echo "" | tee -a "$LOG_FILE"
    echo "🔧 Process Status:" | tee -a "$LOG_FILE"
    client_status=$(check_process $CLIENT_PID "IRIS Client")
    processor_status=$(check_process $PROCESSOR_PID "IRIS Processor")
    echo "$client_status" | tee -a "$LOG_FILE"
    echo "$processor_status" | tee -a "$LOG_FILE"
    
    # Alert if either process stopped
    if ! echo "$client_status" | grep -q "✅"; then
        echo "🚨 CRITICAL: IRIS Client stopped!" | tee -a "$LOG_FILE" "$ALERT_FILE"
    fi
    if ! echo "$processor_status" | grep -q "✅"; then
        echo "🚨 CRITICAL: IRIS Processor stopped!" | tee -a "$LOG_FILE" "$ALERT_FILE"
    fi
    
    # 2. File Backlog
    echo "" | tee -a "$LOG_FILE"
    echo "📁 File Backlog:" | tee -a "$LOG_FILE"
    file_count=$(count_files)
    echo "   Files pending: $file_count" | tee -a "$LOG_FILE"
    
    if [ "$file_count" -gt "$MAX_FILE_BACKLOG" ]; then
        echo "⚠️  WARNING: File backlog exceeds $MAX_FILE_BACKLOG" | tee -a "$LOG_FILE" "$ALERT_FILE"
    fi
    
    # 3. Data Lag
    echo "" | tee -a "$LOG_FILE"
    echo "⏱️  Data Lag:" | tee -a "$LOG_FILE"
    data_lag=$(check_data_lag)
    
    if [ "$data_lag" = "ERROR: Could not query BigQuery" ] || [ "$data_lag" = "ERROR: Could not parse timestamp" ] || [ "$data_lag" = "999" ]; then
        echo "   ⚠️  Could not determine data lag (BigQuery query failed)" | tee -a "$LOG_FILE"
    else
        echo "   Latest data: $data_lag minutes ago" | tee -a "$LOG_FILE"
        
        if [ "$data_lag" -gt "$MAX_DATA_LAG_MINUTES" ]; then
            echo "⚠️  WARNING: Data lag exceeds $MAX_DATA_LAG_MINUTES minutes!" | tee -a "$LOG_FILE" "$ALERT_FILE"
        fi
    fi
    
    # 4. Record Counts (every 3rd check to reduce BigQuery queries)
    if [ $((iteration % 3)) -eq 0 ]; then
        echo "" | tee -a "$LOG_FILE"
        echo "📈 Record Counts:" | tee -a "$LOG_FILE"
        get_record_counts | while IFS=',' read dataset records; do
            echo "   $dataset: $records records" | tee -a "$LOG_FILE"
        done
    fi
    
    # 5. Recent Errors
    echo "" | tee -a "$LOG_FILE"
    echo "🐛 Recent Errors (last 100 log lines):" | tee -a "$LOG_FILE"
    error_count=$(check_recent_errors)
    echo "   Error count: $error_count" | tee -a "$LOG_FILE"
    
    if [ "$error_count" -gt 10 ]; then
        echo "⚠️  WARNING: High error count in recent logs!" | tee -a "$LOG_FILE" "$ALERT_FILE"
    fi
    
    # 6. System Resources
    echo "" | tee -a "$LOG_FILE"
    echo "💻 System Resources:" | tee -a "$LOG_FILE"
    if ps -p $PROCESSOR_PID -o %cpu,%mem | tail -1 > /dev/null 2>&1; then
        ps -p $PROCESSOR_PID -o %cpu,%mem | tail -1 | awk '{printf "   Processor: CPU %.1f%%, Memory %.1f%%\n", $1, $2}' | tee -a "$LOG_FILE"
    fi
    
    # 7. Disk Space
    disk_usage=$(df -h . | tail -1 | awk '{print $5}')
    echo "   Disk usage: $disk_usage" | tee -a "$LOG_FILE"
    
    # 8. Summary
    echo "" | tee -a "$LOG_FILE"
    if echo "$client_status $processor_status" | grep -q "❌"; then
        echo "❌ Status: CRITICAL - Service(s) down" | tee -a "$LOG_FILE"
    elif [ "$file_count" -gt "$MAX_FILE_BACKLOG" ] || [ "$error_count" -gt 10 ]; then
        echo "⚠️  Status: WARNING - Issues detected" | tee -a "$LOG_FILE"
    else
        echo "✅ Status: HEALTHY - All systems operational" | tee -a "$LOG_FILE"
    fi
    
    echo "" | tee -a "$LOG_FILE"
    echo "Next check in 5 minutes..." | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    # Wait 5 minutes
    sleep $CHECK_INTERVAL
done
