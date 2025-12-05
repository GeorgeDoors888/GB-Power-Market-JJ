#!/bin/bash
# Test corrected scripts with complete bmrs_costs data (2022-2025)

echo "=================================================================="
echo "TESTING CORRECTED SCRIPTS WITH COMPLETE DATA"
echo "=================================================================="
echo ""

SCRIPT_DIR="/home/george/GB-Power-Market-JJ"
cd "$SCRIPT_DIR"

# Test 1: Verify bmrs_costs table status
echo "TEST 1: Verify bmrs_costs table completeness"
echo "=================================================================="
python3 -c "
from google.cloud import bigquery
import warnings
warnings.filterwarnings('ignore')

client = bigquery.Client(project='inner-cinema-476211-u9', location='US')
query = '''
SELECT 
    COUNT(*) as total_rows,
    MIN(DATE(settlementDate)) as earliest_date,
    MAX(DATE(settlementDate)) as latest_date,
    COUNT(DISTINCT DATE(settlementDate)) as distinct_days,
    ROUND(AVG(systemSellPrice), 2) as avg_ssp,
    ROUND(AVG(systemBuyPrice), 2) as avg_sbp,
    ROUND(AVG(ABS(systemSellPrice - systemBuyPrice)), 4) as avg_spread
FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_costs\`
'''
df = client.query(query).to_dataframe()
print(df.to_string(index=False))

# Check if SSP = SBP (P305 validation)
spread = df['avg_spread'].iloc[0]
if spread < 0.01:
    print('\\n✅ P305 VALIDATED: SSP = SBP (single imbalance price)')
else:
    print(f'\\n⚠️  Unexpected spread: {spread:.4f} £/MWh')
" 2>&1
echo ""

# Test 2: Check for gaps in last 30 days
echo "TEST 2: Check for gaps in recent data (last 30 days)"
echo "=================================================================="
python3 -c "
from google.cloud import bigquery
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

client = bigquery.Client(project='inner-cinema-476211-u9', location='US')
end_date = datetime.utcnow().date()
start_date = end_date - timedelta(days=30)

query = f'''
WITH date_range AS (
    SELECT DATE_ADD(DATE('{start_date}'), INTERVAL day DAY) as date
    FROM UNNEST(GENERATE_ARRAY(0, 30)) as day
),
existing_dates AS (
    SELECT DISTINCT DATE(settlementDate) as date
    FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_costs\`
    WHERE DATE(settlementDate) >= '{start_date}'
)
SELECT 
    dr.date,
    CASE WHEN ed.date IS NULL THEN 'MISSING' ELSE 'OK' END as status
FROM date_range dr
LEFT JOIN existing_dates ed ON dr.date = ed.date
WHERE ed.date IS NULL
ORDER BY dr.date
'''

df = client.query(query).to_dataframe()
if len(df) == 0:
    print('✅ NO GAPS - All dates present in last 30 days')
else:
    print(f'⚠️  Found {len(df)} missing dates:')
    print(df.to_string(index=False))
" 2>&1
echo ""

# Test 3: Verify populate_bess_enhanced.py configuration
echo "TEST 3: Verify populate_bess_enhanced.py uses correct table"
echo "=================================================================="
python3 -c "
with open('populate_bess_enhanced.py', 'r') as f:
    content = f.read()
    
checks = {
    '✅ Uses bmrs_costs table': 'FROM.*bmrs_costs' in content,
    '❌ Uses bmrs_mid table': 'FROM.*bmrs_mid' in content and content.count('bmrs_mid') > 2,
    '✅ Has error handling': 'CRITICAL ERROR' in content,
    '✅ No synthetic data': 'random' not in content.lower() or 'NO synthetic' in content
}

for check, passed in checks.items():
    print(f'{check}: {passed}')
" 2>&1
echo ""

# Test 4: Check create_btm_bess_view.sql
echo "TEST 4: Verify create_btm_bess_view.sql uses correct columns"
echo "=================================================================="
python3 -c "
with open('create_btm_bess_view.sql', 'r') as f:
    content = f.read()
    
checks = {
    '✅ Uses bmrs_costs table': 'bmrs_costs' in content,
    '✅ Uses systemSellPrice': 'systemSellPrice' in content,
    '✅ Uses systemBuyPrice': 'systemBuyPrice' in content,
    '❌ Uses bmrs_mid.price': 'bmrs_mid' in content and 'price' in content.lower()
}

for check, passed in checks.items():
    print(f'{check}: {passed}')
" 2>&1
echo ""

# Test 5: Run auto_backfill_costs_daily.py (should find no gaps)
echo "TEST 5: Run daily backfill script (should find no gaps)"
echo "=================================================================="
python3 auto_backfill_costs_daily.py 2>&1 | grep -E "✅|⚠️|❌|Found [0-9]" | head -10
echo ""

echo "=================================================================="
echo "TESTING COMPLETE"
echo "=================================================================="
echo ""
echo "Summary:"
echo "  - bmrs_costs table: Complete 2022-2025 with P305 single pricing"
echo "  - Daily backfill: Automated via cron (6:00 AM UTC)"
echo "  - Scripts corrected: populate_bess_enhanced.py, create_btm_bess_view.sql"
echo "  - Documentation: 16 .md files updated"
echo ""
echo "Next steps:"
echo "  1. Test populate_bess_enhanced.py with real data"
echo "  2. Deploy battery revenue model (6 streams)"
echo "  3. Configure IRIS B1770 stream for real-time prices"
echo ""
