#!/bin/bash
# Check ingestion status after 1 hour deployment
# Run at: 13:47 (1 hour after 12:47 deployment)

echo "=== Waiting 1 hour for cron jobs to execute ==="
echo "Current time: $(date)"
echo "Will check at: $(date -d '+1 hour' '+%Y-%m-%d %H:%M:%S')"
echo ""

sleep 3600  # 1 hour

echo ""
echo "=============================================="
echo "=== INGESTION STATUS CHECK ==="
echo "=============================================="
echo "Time: $(date)"
echo ""

# Check server logs
echo "=== AlmaLinux Server Logs ==="
ssh root@94.237.55.234 'ls -lth /opt/gb-power-ingestion/logs/ && echo "" && tail -20 /opt/gb-power-ingestion/logs/bod_ingest.log 2>&1 | tail -15'

echo ""
echo "=== BigQuery Data Check ==="
cd /home/george/GB-Power-Market-JJ
python3 -c "
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

print('Latest Data:')
tables = [
    ('bmrs_bod', 'settlementDate'),
    ('bmrs_windfor', 'startTime'),
    ('bmrs_indgen', 'settlementDate'),
]

for table, date_col in tables:
    query = f'''
    SELECT 
        MAX(CAST({date_col} AS DATE)) as latest_date,
        COUNT(*) as total_rows
    FROM \`inner-cinema-476211-u9.uk_energy_prod.{table}\`
    WHERE CAST({date_col} AS DATE) >= '2025-12-18'
    '''
    result = list(client.query(query).result())[0]
    print(f'  {table}: {result.latest_date} ({result.total_rows:,} rows since Dec 18)')

print()
print('Fresh Ingestion (last 60 min):')
for table, _ in tables:
    query = f'''
    SELECT COUNT(*) as fresh_rows
    FROM \`inner-cinema-476211-u9.uk_energy_prod.{table}\`
    WHERE CAST(_ingested_utc AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 MINUTE)
    '''
    result = list(client.query(query).result())[0]
    status = '✅' if result.fresh_rows > 0 else '❌'
    print(f'  {status} {table}: {result.fresh_rows:,} rows')
"

echo ""
echo "=== Cron Execution Log ==="
ssh root@94.237.55.234 "grep CRON /var/log/cron | grep 'gb-power-ingestion' | tail -20"

echo ""
echo "=============================================="
echo "Check complete. Updating documentation..."
echo "=============================================="
