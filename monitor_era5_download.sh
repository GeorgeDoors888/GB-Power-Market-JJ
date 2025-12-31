#!/bin/bash
# Monitor ERA5 CDS download progress

echo "=================================="
echo "ERA5 CDS DOWNLOAD MONITOR"
echo "=================================="
echo ""

# Check if process is running
PID=$(cat /tmp/era5_cds_download.pid 2>/dev/null)
if [ -n "$PID" ] && ps -p $PID > /dev/null 2>&1; then
    echo "✅ Download process running (PID: $PID)"
    echo ""
else
    echo "❌ Download process not running"
    echo ""
fi

# Log file stats
if [ -f /tmp/era5_cds_download.log ]; then
    LOG_SIZE=$(du -h /tmp/era5_cds_download.log | cut -f1)
    LOG_LINES=$(wc -l < /tmp/era5_cds_download.log)
    echo "📊 Log file: ${LOG_SIZE} (${LOG_LINES} lines)"
    echo ""
    
    # Count successes and failures
    COMPLETED=$(grep -c "✅ Chunk" /tmp/era5_cds_download.log 2>/dev/null || echo "0")
    FAILED=$(grep -c "❌ Chunk" /tmp/era5_cds_download.log 2>/dev/null || echo "0")
    FARMS=$(grep -c "🌬️ Farm" /tmp/era5_cds_download.log 2>/dev/null || echo "0")
    UPLOADED=$(grep -c "✅ Uploaded" /tmp/era5_cds_download.log 2>/dev/null || echo "0")
    TOO_LARGE=$(grep -c "cost limits exceeded" /tmp/era5_cds_download.log 2>/dev/null || echo "0")
    
    echo "📈 Progress:"
    echo "   Farms processed: $FARMS / 41"
    echo "   Chunks completed: $COMPLETED"
    echo "   Chunks failed: $FAILED"
    echo "   BigQuery uploads: $UPLOADED"
    echo "   'Too large' errors: $TOO_LARGE"
    echo ""
    
    # Show last few log entries
    echo "📜 Last 15 log entries:"
    tail -15 /tmp/era5_cds_download.log
else
    echo "❌ Log file not found: /tmp/era5_cds_download.log"
fi
