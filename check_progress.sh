#!/bin/bash
# Quick progress checker - run this anytime
# Usage: ./check_progress.sh

echo ""
echo "================================================================================"
echo "📊 EXTRACTION PROGRESS CHECK"
echo "================================================================================"
echo ""

# SSH into server and check BigQuery
ssh root@94.237.55.15 'docker exec driveindexer bash -c "
source /app/.env
python3 << EOF
from src.auth.google_auth import bq_client
c = bq_client()
r = list(c.query(\"SELECT COUNT(*) cnt, COUNT(DISTINCT doc_id) docs FROM \\\`inner-cinema-476211-u9.uk_energy_insights.chunks\\\`\").result())[0]
print(f\"✅ Documents processed: {r.docs:,} / 140,434\")
print(f\"📊 Progress: {(r.docs/140434*100):.2f}%\")
print(f\"📦 Text chunks created: {r.cnt:,}\")
if r.docs > 0:
    print(f\"📏 Average chunks/doc: {r.cnt/r.docs:.1f}\")
remaining = 140434 - r.docs
print(f\"⏳ Remaining: {remaining:,} documents ({(remaining/140434*100):.1f}%)\")
EOF
"'

echo ""
echo "================================================================================"
echo "💡 Run this script again to check updated progress"
echo "================================================================================"
echo ""
