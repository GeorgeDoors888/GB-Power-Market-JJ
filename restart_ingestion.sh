#!/bin/bash
#
# Simple restart of ingestion (no cleanup)
# Uses the skip logic we added to avoid reprocessing existing data
#

PROJECT_DIR="/Users/georgemajor/GB Power Market JJ"
cd "$PROJECT_DIR"

echo "=========================================="
echo "Restart Ingestion (Skip Existing Data)"
echo "=========================================="
echo ""

# Stop any running processes
if pgrep -f "ingest_elexon_fixed.py" > /dev/null; then
    echo "Stopping existing ingestion process..."
    pkill -f "ingest_elexon_fixed.py"
    sleep 3
fi

# Start 2025 ingestion
LOG_FILE="jan_aug_ingest_$(date +%Y%m%d_%H%M%S).log"
echo "Starting 2025 ingestion (Jan-Aug)..."
echo "Log file: $LOG_FILE"
echo ""

nohup .venv/bin/python ingest_elexon_fixed.py --start 2025-01-01 --end 2025-08-31 > "$LOG_FILE" 2>&1 &
PID=$!

sleep 3

if ps -p $PID > /dev/null; then
    echo "✅ Ingestion running (PID: $PID)"
    echo ""
    echo "Monitor with: tail -f $LOG_FILE"
    echo "Check status: ps aux | grep $PID"
    echo ""
    
    # Setup 2024 auto-start
    cat > /tmp/auto_start_2024.sh << EOF
#!/bin/bash
while kill -0 $PID 2>/dev/null; do sleep 60; done
cd "$PROJECT_DIR"
nohup .venv/bin/python ingest_elexon_fixed.py --start 2024-01-01 --end 2024-12-31 > year_2024_ingest.log 2>&1 &
echo "\$(date): Started 2024 ingestion (PID: \$!)"
EOF
    chmod +x /tmp/auto_start_2024.sh
    nohup /tmp/auto_start_2024.sh > auto_2024.log 2>&1 &
    
    echo "✅ Auto-start for 2024 configured"
else
    echo "❌ Failed to start. Check $LOG_FILE"
    exit 1
fi
