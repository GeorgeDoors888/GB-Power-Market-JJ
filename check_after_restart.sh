#!/bin/bash
# Check server status after restart

echo "=========================================="
echo "SERVER STATUS CHECK AFTER RESTART"
echo "$(date)"
echo "=========================================="
echo ""

echo "🔌 Checking if server is online..."
if ssh -o ConnectTimeout=10 root@94.237.55.234 'echo "✅ Connected!"' 2>/dev/null; then
    echo ""
    
    echo "1️⃣ Server uptime:"
    ssh root@94.237.55.234 'uptime'
    echo ""
    
    echo "2️⃣ Checking IRIS client process..."
    ssh root@94.237.55.234 'ps aux | grep iris-client | grep -v grep' || echo "   ❌ IRIS client not running"
    echo ""
    
    echo "3️⃣ Checking IRIS uploader process..."
    ssh root@94.237.55.234 'ps aux | grep iris_to_bigquery | grep -v grep' || echo "   ❌ IRIS uploader not running"
    echo ""
    
    echo "4️⃣ Checking screen sessions..."
    ssh root@94.237.55.234 'screen -ls'
    echo ""
    
    echo "5️⃣ Last 20 lines of uploader log..."
    ssh root@94.237.55.234 'tail -20 /opt/iris-pipeline/logs/iris_uploader.log 2>/dev/null' || echo "   ⚠️  Log file not found or empty"
    echo ""
    
    echo "6️⃣ Checking current configuration..."
    ssh root@94.237.55.234 'grep -E "MAX_FILES_PER_SCAN|BATCH_SIZE" /opt/iris-pipeline/iris_to_bigquery_unified.py 2>/dev/null | head -3'
    echo ""
    
    echo "=========================================="
    echo "✅ SERVER IS ONLINE"
    echo "=========================================="
    echo ""
    
    # Check if we need to apply the fix
    CURRENT_MAX=$(ssh root@94.237.55.234 'grep "MAX_FILES_PER_SCAN = " /opt/iris-pipeline/iris_to_bigquery_unified.py | head -1' 2>/dev/null)
    if echo "$CURRENT_MAX" | grep -q "1000"; then
        echo "⚠️  MEMORY FIX NEEDED:"
        echo "   Current: MAX_FILES_PER_SCAN = 1000 (causes OOM)"
        echo "   Should be: MAX_FILES_PER_SCAN = 500"
        echo ""
        echo "🔧 Run this to apply fix:"
        echo "   bash apply_memory_fix.sh"
    elif echo "$CURRENT_MAX" | grep -q "500"; then
        echo "✅ Memory fix already applied (MAX_FILES_PER_SCAN = 500)"
        echo ""
        echo "Process should be running optimally!"
    fi
    
else
    echo "   ❌ Cannot connect to server"
    echo ""
    echo "Server might still be booting..."
    echo "Wait 2-3 minutes and try again:"
    echo "   bash check_after_restart.sh"
fi

echo ""
