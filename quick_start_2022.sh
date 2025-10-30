#!/bin/bash
# Complete 2022 BMRS Datasets - Quick Start Commands
# Run these commands in separate terminals for parallel execution

echo "🚀 COMPLETE 2022 BMRS DATASETS - QUICK START"
echo "=============================================="
echo ""
echo "⚠️  IMPORTANT: Use the correct virtual environment:"
echo "   source .venv_2022_ingest/bin/activate"
echo ""
echo "📋 PHASE 1 - Core Market Data (Quick wins, run in parallel):"
echo ""

# Phase 1 commands (can run all in parallel)
echo "# Terminal 1: FREQ"
echo 'cd "/Users/georgemajor/jibber-jabber 24 august 2025 big bop" && source .venv_2022_ingest/bin/activate && echo "🚀 Starting 2022 FREQ ingestion" && python ingest_elexon_fixed.py --start 2022-01-01 --end 2023-01-01 --only FREQ --log-level INFO --monitor-progress --use-staging-table --batch-size 50 --flush-seconds 180'
echo ""

echo "# Terminal 2: TEMP"
echo 'cd "/Users/georgemajor/jibber-jabber 24 august 2025 big bop" && source .venv_2022_ingest/bin/activate && echo "🚀 Starting 2022 TEMP ingestion" && python ingest_elexon_fixed.py --start 2022-01-01 --end 2023-01-01 --only TEMP --log-level INFO --monitor-progress --use-staging-table --batch-size 50 --flush-seconds 180'
echo ""

echo "# Terminal 3: METADATA"
echo 'cd "/Users/georgemajor/jibber-jabber 24 august 2025 big bop" && source .venv_2022_ingest/bin/activate && echo "🚀 Starting 2022 METADATA ingestion" && python ingest_elexon_fixed.py --start 2022-01-01 --end 2023-01-01 --only METADATA --log-level INFO --monitor-progress --use-staging-table --batch-size 50 --flush-seconds 180'
echo ""

echo "# Terminal 4: MID"
echo 'cd "/Users/georgemajor/jibber-jabber 24 august 2025 big bop" && source .venv_2022_ingest/bin/activate && echo "🚀 Starting 2022 MID ingestion" && python ingest_elexon_fixed.py --start 2022-01-01 --end 2023-01-01 --only MID --log-level INFO --monitor-progress --use-staging-table --batch-size 50 --flush-seconds 180'
echo ""

echo "# Terminal 5: QAS"
echo 'cd "/Users/georgemajor/jibber-jabber 24 august 2025 big bop" && source .venv_2022_ingest/bin/activate && echo "🚀 Starting 2022 QAS ingestion" && python ingest_elexon_fixed.py --start 2022-01-01 --end 2023-01-01 --only QAS --log-level INFO --monitor-progress --use-staging-table --batch-size 50 --flush-seconds 180'
echo ""

echo "# Terminal 6: IMBALNGC"
echo 'cd "/Users/georgemajor/jibber-jabber 24 august 2025 big bop" && source .venv_2022_ingest/bin/activate && echo "🚀 Starting 2022 IMBALNGC ingestion" && python ingest_elexon_fixed.py --start 2022-01-01 --end 2023-01-01 --only IMBALNGC --log-level INFO --monitor-progress --use-staging-table --batch-size 50 --flush-seconds 180'
echo ""

echo "📋 PHASE 2 - Generation Data (after Phase 1 completes):"
echo ""

echo "# Terminal 7: FUELINST"
echo 'cd "/Users/georgemajor/jibber-jabber 24 august 2025 big bop" && source .venv_2022_ingest/bin/activate && echo "🚀 Starting 2022 FUELINST ingestion" && python ingest_elexon_fixed.py --start 2022-01-01 --end 2023-01-01 --only FUELINST --log-level INFO --monitor-progress --use-staging-table --batch-size 50 --flush-seconds 180'
echo ""

echo "# Terminal 8: INDGEN"
echo 'cd "/Users/georgemajor/jibber-jabber 24 august 2025 big bop" && source .venv_2022_ingest/bin/activate && echo "🚀 Starting 2022 INDGEN ingestion" && python ingest_elexon_fixed.py --start 2022-01-01 --end 2023-01-01 --only INDGEN --log-level INFO --monitor-progress --use-staging-table --batch-size 50 --flush-seconds 180'
echo ""

echo "📋 PHASE 3 - High Volume Data (run separately, not in parallel):"
echo ""

echo "# Terminal 9: BOD (LARGE - 2-4 hours)"
echo 'cd "/Users/georgemajor/jibber-jabber 24 august 2025 big bop" && source .venv_2022_ingest/bin/activate && echo "🚀 Starting 2022 BOD ingestion (LARGE DATASET)" && python ingest_elexon_fixed.py --start 2022-01-01 --end 2023-01-01 --only BOD --log-level INFO --monitor-progress --use-staging-table --batch-size 25 --flush-seconds 300'
echo ""

echo "📊 MONITORING:"
echo "To check progress, run in a separate terminal:"
echo 'cd "/Users/georgemajor/jibber-jabber 24 august 2025 big bop" && source .venv_2022_ingest/bin/activate && python bmrs_health_check.py'
echo ""

echo "🎯 EXECUTION STRATEGY:"
echo "1. Start Phase 1 (6 terminals) - these are quick wins"
echo "2. When Phase 1 completes, start Phase 2"
echo "3. Run BOD separately when system is less busy"
echo "4. Continue with remaining datasets using complete_2022_datasets.py"
