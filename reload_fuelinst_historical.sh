#!/bin/bash
# FUELINST Historical Data Reload
# Uses fixed stream endpoint to load 2022-2025 data

cd '/Users/georgemajor/GB Power Market JJ'

echo "================================================================================"
echo "FUELINST HISTORICAL DATA RELOAD WITH STREAM ENDPOINT FIX"
echo "================================================================================"
echo ""

# Step 1: Clear corrupted Oct 28-29 data
echo "Step 1: Clearing corrupted Oct 28-29 data..."
./.venv/bin/python -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')
query = \"\"\"
DELETE FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst\`
WHERE settlementDate >= '2025-10-28'
\"\"\"
job = client.query(query)
job.result()
print('✅ Deleted corrupted Oct 28-29 data')
"
echo ""

# Step 2: Reload 2023
echo "Step 2: Reloading 2023 FUELINST data..."
echo "Start time: $(date)"
./.venv/bin/python ingest_elexon_fixed.py \
  --start 2023-01-01 \
  --end 2023-12-31 \
  --only FUELINST \
  --overwrite \
  2>&1 | tee logs/2023_fuelinst_stream_reload.log
echo "End time: $(date)"
echo ""

# Step 3: Reload 2024
echo "Step 3: Reloading 2024 FUELINST data..."
echo "Start time: $(date)"
./.venv/bin/python ingest_elexon_fixed.py \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --only FUELINST \
  --overwrite \
  2>&1 | tee logs/2024_fuelinst_stream_reload.log
echo "End time: $(date)"
echo ""

# Step 4: Reload 2025
echo "Step 4: Reloading 2025 FUELINST data (Jan-Oct)..."
echo "Start time: $(date)"
./.venv/bin/python ingest_elexon_fixed.py \
  --start 2025-01-01 \
  --end 2025-10-29 \
  --only FUELINST \
  --overwrite \
  2>&1 | tee logs/2025_fuelinst_stream_reload.log
echo "End time: $(date)"
echo ""

# Step 5: Verify data quality
echo "Step 5: Verifying data quality..."
./.venv/bin/python -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')

print()
print('📊 FUELINST Data Coverage After Reload:')
print('=' * 80)

query = '''
SELECT 
  EXTRACT(YEAR FROM settlementDate) as year,
  EXTRACT(MONTH FROM settlementDate) as month,
  COUNT(DISTINCT DATE(settlementDate)) as distinct_days,
  COUNT(*) as total_rows,
  MIN(DATE(settlementDate)) as first_date,
  MAX(DATE(settlementDate)) as last_date
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst\`
WHERE settlementDate >= '2022-01-01'
GROUP BY year, month
ORDER BY year, month
'''

results = list(client.query(query).result())

if results:
    print(f'{\"Year\":^6} {\"Month\":^6} {\"Days\":^6} {\"Rows\":>10} {\"First\":^12} {\"Last\":^12}')
    print('-' * 80)
    for row in results:
        print(f'{row.year:^6} {row.month:^6} {row.distinct_days:^6} {row.total_rows:>10,} {str(row.first_date):^12} {str(row.last_date):^12}')
    
    print()
    print('Summary by Year:')
    print('-' * 80)
    
    summary_query = '''
    SELECT 
      EXTRACT(YEAR FROM settlementDate) as year,
      COUNT(DISTINCT DATE(settlementDate)) as distinct_days,
      COUNT(*) as total_rows
    FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst\`
    WHERE settlementDate >= '2022-01-01'
    GROUP BY year
    ORDER BY year
    '''
    
    summary_results = list(client.query(summary_query).result())
    print(f'{\"Year\":^6} {\"Distinct Days\":^14} {\"Total Rows\":>12}')
    print('-' * 40)
    for row in summary_results:
        print(f'{row.year:^6} {row.distinct_days:^14} {row.total_rows:>12,}')
    
    print()
    print('✅ Data reload complete!')
else:
    print('❌ No data found - reload may have failed')
"

echo ""
echo "================================================================================"
echo "RELOAD COMPLETE"
echo "================================================================================"
echo ""
echo "Check logs for details:"
echo "  - logs/2023_fuelinst_stream_reload.log"
echo "  - logs/2024_fuelinst_stream_reload.log"
echo "  - logs/2025_fuelinst_stream_reload.log"
echo ""
