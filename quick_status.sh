#!/bin/bash
# Quick monitoring commands for extraction progress

echo "🚀 EXTRACTION QUICK STATUS"
echo "======================================================================"
echo ""

# Get current database status
ssh root@94.237.55.15 'docker exec driveindexer python /tmp/check_extraction_status.py'

echo ""
echo "======================================================================"
echo "📊 SYSTEM RESOURCES"
echo "======================================================================"

# Get CPU and load
ssh root@94.237.55.15 'top -bn1 | head -5'

echo ""
echo "======================================================================"
echo "📈 RECENT PROCESSING SPEED"
echo "======================================================================"

# Get latest speed from log
ssh root@94.237.55.15 'docker exec driveindexer tail -n 50 /tmp/continuous_extraction.log | grep "docs/sec" | tail -1'

echo ""
echo "======================================================================"
echo "⏰ ESTIMATED COMPLETION"
echo "======================================================================"

# Calculate ETA
REMAINING=$(ssh root@94.237.55.15 'docker exec driveindexer python -c "
from google.cloud import bigquery
client = bigquery.Client()
query = \"SELECT COUNT(*) as remaining FROM \\\`inner-cinema-476211-u9.uk_energy_insights.documents_clean\\\` d LEFT JOIN (SELECT DISTINCT doc_id FROM \\\`inner-cinema-476211-u9.uk_energy_insights.chunks\\\`) c ON d.doc_id = c.doc_id WHERE c.doc_id IS NULL AND d.mime_type IN (\\\"application/pdf\\\", \\\"application/vnd.openxmlformats-officedocument.wordprocessingml.document\\\", \\\"application/vnd.openxmlformats-officedocument.presentationml.presentation\\\")\"
result = list(client.query(query).result())
print(result[0].remaining)
"' 2>/dev/null)

if [ ! -z "$REMAINING" ]; then
    # Assume 0.8 docs/sec (conservative)
    SECONDS_REMAINING=$((REMAINING * 2))  # 1/0.8 = 1.25, round to 2 for safety
    HOURS_REMAINING=$((SECONDS_REMAINING / 3600))
    DAYS_REMAINING=$((HOURS_REMAINING / 24))
    
    echo "📊 Remaining documents: $REMAINING"
    echo "⏱️  At 0.8 docs/sec:"
    echo "   - ${HOURS_REMAINING} hours"
    echo "   - ${DAYS_REMAINING} days"
    echo ""
    echo "🎯 Expected completion: $(date -v+${DAYS_REMAINING}d '+%B %d, %Y at %H:%M')"
fi

echo ""
echo "======================================================================"
echo "💡 COMMANDS"
echo "======================================================================"
echo "Full monitor: ./monitor_continuous.sh"
echo "Live logs: ssh root@94.237.55.15 'docker exec driveindexer tail -f /tmp/continuous_extraction.log'"
echo "Stop: ssh root@94.237.55.15 'docker exec driveindexer python -c \"import os, signal; pid = int(open(\"/tmp/continuous_extract.pid\").read()); os.kill(pid, signal.SIGTERM)\"'"
echo "======================================================================"
