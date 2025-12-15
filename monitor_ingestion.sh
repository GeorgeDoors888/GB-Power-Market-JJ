#!/bin/bash
# Monitor 3-year BOAV/EBOCF ingestion progress

echo "═══════════════════════════════════════════════════════════════"
echo "  BM SETTLEMENT DATA INGESTION - PROGRESS MONITOR"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check running processes
PROCS=$(ps aux | grep "[p]ython3 ingest_bm_3years" | wc -l)
echo "🔄 Active ingestion processes: $PROCS"
echo ""

# Check BigQuery data
python3 << 'PYEND'
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')

# BOAV coverage
query = '''
SELECT 
  COUNT(*) as total_records,
  COUNT(DISTINCT DATE(CAST(settlementDate AS STRING))) as total_days,
  MIN(DATE(CAST(settlementDate AS STRING))) as min_date,
  MAX(DATE(CAST(settlementDate AS STRING))) as max_date
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boav`
'''
row = list(client.query(query).result())[0]

print(f"📊 BOAV Table:")
print(f"   Records: {row.total_records:,}")
print(f"   Days: {row.total_days} / 1,443 ({row.total_days/1443*100:.1f}%)")
print(f"   Range: {row.min_date} to {row.max_date}")

# EBOCF coverage
query2 = 'SELECT COUNT(*) as cnt FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf`'
row2 = list(client.query(query2).result())[0]
print(f"\n📊 EBOCF Table:")
print(f"   Records: {row2.cnt:,}")

# Estimate completion
target_days = 1443  # 3 years
remaining_days = target_days - row.total_days
if remaining_days > 0:
    # ~96 requests per day at 100/min = 0.96 min/day = ~1 min/day
    # With 4 parallel processes, ~15 seconds per day
    est_hours = (remaining_days * 60 / 100) / 60 / 4  # 4 parallel processes
    print(f"\n⏱️  Estimated completion: {est_hours:.1f} hours")
else:
    print(f"\n✅ COMPLETE!")
PYEND

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "Monitor continuously: watch -n 60 /home/george/GB-Power-Market-JJ/monitor_ingestion.sh"
echo "═══════════════════════════════════════════════════════════════"
