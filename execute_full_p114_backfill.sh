#!/bin/bash
#
# Full P114 S0142 Backfill Execution (2022-2025)
# Hybrid Strategy: RF for 2022-2023, R3 for 2024, II for 2025
# Based on S0142_BACKFILL_STRATEGY.md
#

set -e

PROJECT_DIR="/home/george/GB-Power-Market-JJ"
LOG_DIR="$PROJECT_DIR/logs/p114_backfill"
mkdir -p "$LOG_DIR"

echo "========================================================================"
echo "P114 S0142 FULL BACKFILL EXECUTION"
echo "========================================================================"
echo "Start Time: $(date)"
echo "Strategy: Hybrid (RF/R3/II)"
echo "Expected: ~400M records, 110-150 hours"
echo "========================================================================"
echo ""

# Phase 1: RF for 2022-2023 (most accurate, 28-month lag satisfied)
echo "📦 PHASE 1: RF Runs for 2022-2023 Settlement Data"
echo "   Expected: ~200M records, ~60 hours"
echo "   Query Window: generation_date 2024-06-01 to 2025-12-28"
echo ""

# Note: P114 portal queries by generation_date, not settlement_date
# RF runs for 2022 settlement data were generated in 2024
# We query by settlement_date but portal returns files by generation date

python3 "$PROJECT_DIR/ingest_p114_batch.py" 2022-01-01 2022-12-31 RF 2>&1 | tee "$LOG_DIR/phase1_2022_rf.log"
python3 "$PROJECT_DIR/ingest_p114_batch.py" 2023-01-01 2023-12-31 RF 2>&1 | tee "$LOG_DIR/phase1_2023_rf.log"

echo ""
echo "✅ Phase 1 Complete: RF data for 2022-2023"
echo ""

# Phase 2: R3 for 2024 (RF not yet available, R3 is 14-month lag)
echo "📦 PHASE 2: R3 Runs for 2024 Settlement Data"
echo "   Expected: ~100M records, ~35 hours"
echo "   Query Window: generation_date 2024-03-01 to 2025-12-28"
echo ""

python3 "$PROJECT_DIR/ingest_p114_batch.py" 2024-01-01 2024-12-31 R3 2>&1 | tee "$LOG_DIR/phase2_2024_r3.log"

echo ""
echo "✅ Phase 2 Complete: R3 data for 2024"
echo ""

# Phase 3: II for 2025 (only run available for current year)
echo "📦 PHASE 3: II Runs for 2025 Settlement Data"
echo "   Expected: ~100M records, ~35 hours"
echo "   Query Window: generation_date 2025-01-02 to 2025-12-28"
echo ""

python3 "$PROJECT_DIR/ingest_p114_batch.py" 2025-01-01 2025-12-28 II 2>&1 | tee "$LOG_DIR/phase3_2025_ii.log"

echo ""
echo "✅ Phase 3 Complete: II data for 2025"
echo ""

# Summary and Validation
echo "========================================================================"
echo "📊 BACKFILL EXECUTION COMPLETE"
echo "========================================================================"
echo "End Time: $(date)"
echo ""

python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

query = '''
SELECT
  settlement_run,
  EXTRACT(YEAR FROM settlement_date) as year,
  COUNT(DISTINCT settlement_date) as days,
  COUNT(DISTINCT bm_unit_id) as units,
  COUNT(*) as records,
  MIN(settlement_date) as earliest,
  MAX(settlement_date) as latest
FROM \`inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi\`
GROUP BY settlement_run, year
ORDER BY year, settlement_run
'''

print('📊 P114 Data Coverage After Backfill:')
print('='*90)
df = client.query(query).to_dataframe()
print(df.to_string(index=False))
print('')
print(f'Total Records: {df[\"records\"].sum():,}')
"

echo ""
echo "🔍 Validation Queries:"
echo "  1. Check VLP units present:"
echo "     SELECT COUNT(*) FROM p114_settlement_canonical WHERE bm_unit_id IN ('FBPGM002', 'FFSEN005')"
echo ""
echo "  2. Check period completeness:"
echo "     SELECT settlement_date, COUNT(DISTINCT settlement_period) as periods"
echo "     FROM p114_settlement_canonical GROUP BY settlement_date HAVING periods != 48"
echo ""
echo "  3. Check canonical view deduplication:"
echo "     SELECT settlement_run, COUNT(*) FROM p114_settlement_canonical GROUP BY settlement_run"
echo ""
echo "✅ Full backfill execution complete. See logs in: $LOG_DIR"
