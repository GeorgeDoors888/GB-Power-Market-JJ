#!/bin/bash
# Monitor the robust extraction progress

echo "📊 ROBUST EXTRACTION MONITOR"
echo "======================================================================"

# Check if process is running
if docker exec driveindexer test -f /tmp/robust_extract.pid 2>/dev/null; then
    PID=$(docker exec driveindexer cat /tmp/robust_extract.pid 2>/dev/null)
    echo "✅ Extraction process running (PID: $PID)"
else
    echo "⚠️  PID file not found"
fi

# Show last 30 lines of log
echo ""
echo "📋 Recent Log Output:"
echo "----------------------------------------------------------------------"
docker exec driveindexer tail -30 /tmp/robust_extraction.log 2>/dev/null || echo "Log file not yet created"

# Check chunks table
echo ""
echo "----------------------------------------------------------------------"
echo "📊 Database Status:"
echo "----------------------------------------------------------------------"
docker exec driveindexer python << 'PYEOF'
import sys
sys.path.insert(0, "/app")
from dotenv import load_dotenv
load_dotenv("/app/.env")
from src.auth.google_auth import bq_client

bq = bq_client()

# Get current status
query = """
SELECT 
  (SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_insights.documents_clean`) as total_docs,
  (SELECT COUNT(DISTINCT doc_id) FROM `inner-cinema-476211-u9.uk_energy_insights.chunks`) as processed_docs,
  (SELECT COUNT(*) FROM `inner-cinema-476211-u9.uk_energy_insights.chunks`) as total_chunks
"""
result = bq.query(query).result()
for row in result:
    total = row.total_docs
    processed = row.processed_docs
    chunks = row.total_chunks
    remaining = total - processed
    progress = (processed / total * 100) if total > 0 else 0
    
    print(f"  Total documents: {total:,}")
    print(f"  Processed: {processed:,} ({progress:.2f}%)")
    print(f"  Remaining: {remaining:,}")
    print(f"  Total chunks created: {chunks:,}")
    if processed > 0:
        print(f"  Avg chunks/doc: {chunks/processed:.1f}")
PYEOF

echo ""
echo "======================================================================"
echo "💡 Run this script again to check progress"
echo "   Command: ./monitor_robust_extraction.sh"
