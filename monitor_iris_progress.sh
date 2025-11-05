#!/bin/bash
# Monitor IRIS uploader progress
# Created: 2025-11-04 22:21 UTC

echo ""
echo "======================================================================"
echo "  IRIS Uploader Status - $(date '+%Y-%m-%d %H:%M:%S UTC')"
echo "======================================================================"
echo ""

ssh root@94.237.55.234 '
cd /opt/iris-pipeline

echo "📊 Files Remaining:"
mels=$(find iris-clients/python/iris_data/MELS -name "*.json" 2>/dev/null | wc -l)
mils=$(find iris-clients/python/iris_data/MILS -name "*.json" 2>/dev/null | wc -l)
indo=$(find iris-clients/python/iris_data/INDO -name "*.json" 2>/dev/null | wc -l)
inddem=$(find iris-clients/python/iris_data/INDDEM -name "*.json" 2>/dev/null | wc -l)
indgen=$(find iris-clients/python/iris_data/INDGEN -name "*.json" 2>/dev/null | wc -l)

printf "   %-10s %,8d files\n" "MELS:" $mels
printf "   %-10s %,8d files\n" "MILS:" $mils
printf "   %-10s %,8d files (🎯 TARGET)\n" "INDO:" $indo
printf "   %-10s %,8d files\n" "INDDEM:" $inddem
printf "   %-10s %,8d files\n" "INDGEN:" $indgen

total=$((mels + mils + indo + inddem + indgen))
printf "   %-10s %,8d files\n" "TOTAL:" $total

echo ""
echo "⚡ Recent Activity (last 20 lines):"
tail -20 logs/iris_uploader.log | grep -E "✅|Cycle|📦|ERROR" | tail -10

echo ""
echo "🔄 Process Status:"
if ps aux | grep "python3 iris_to_bigquery_unified.py" | grep -v grep > /dev/null; then
    echo "   ✅ Running"
    ps aux | grep "python3 iris_to_bigquery_unified.py" | grep -v grep | awk "{printf \"   PID %s, CPU %.1f%%, MEM %.1f%%\\n\", \$2, \$3, \$4}"
else
    echo "   ❌ Not running!"
fi
'

echo ""
echo "======================================================================"
echo ""
