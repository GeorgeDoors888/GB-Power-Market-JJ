#!/bin/bash
# Quick Start Guide - BESS Integration (Option A)

cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║         BESS DASHBOARD - OPTION A INTEGRATION                  ║
║         Extend Existing Tab with Enhanced Analysis             ║
╚════════════════════════════════════════════════════════════════╝

📊 SHEET STRUCTURE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Rows 1-14:   DNO Lookup (postcode → rates) ✅ PRESERVED
  Rows 15-20:  HH Profile Generator ✅ PRESERVED
  Rows 27-50:  BtM PPA Cost Analysis ✅ PRESERVED
  Row 58:      Divider ─────────────
  Row 59:      Enhanced Analysis Header 🆕
  Rows 60+:    6-Stream Revenue Model 🆕

🚀 DEPLOYMENT (5 STEPS)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Step 1: Test Integration
  python3 test_bess_integration.py

Step 2: Deploy BigQuery View
  bq query --use_legacy_sql=false < bigquery_views/v_bess_cashflow_inputs.sql

Step 3: Run Pipeline
  python3 dashboard_pipeline.py

Step 4: Deploy Apps Script
  1. Open: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc/
  2. Extensions → Apps Script
  3. Paste: apps_script_enhanced/bess_integration.gs
  4. Run: formatBESSEnhanced()

Step 5: Verify
  python3 test_bess_integration.py

📈 REVENUE STREAMS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Existing (Rows 27-50):          Enhanced (Rows 60+):
  ✓ BtM PPA Profit                ✓ FR (£150-350k)
  ✓ VLP £12/MWh                   ✓ Arbitrage (£50-150k)
  ✓ DC £195k/year                 ✓ BM/BOA (£80-200k)
                                   ✓ VLP P444 (£10-70k)
                                   ✓ BTM Savings (£140-360k)
                                   ✓ Capacity Market (£68k)
                                   ✓ Degradation (-£100-300k)

📁 KEY FILES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Modified:
    bess_profit_model_enhanced.py    (added start_row=60)
    dashboard_pipeline.py             (integrated update)
    apps_script_enhanced/bess_integration.gs (format rows 60+)

  Preserved:
    dno_lookup_python.py             (unchanged)
    generate_hh_profile.py           (unchanged)
    update_btm_ppa_from_bigquery.py  (unchanged)

  New:
    test_bess_integration.py         (verification)
    BESS_INTEGRATION_COMPLETE.md     (full docs)

🔧 AUTOMATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Cron (every 15 minutes):
    */15 * * * * cd ~/GB-Power-Market-JJ && python3 dashboard_pipeline.py >> logs/pipeline.log 2>&1

  Manual updates:
    python3 update_btm_ppa_from_bigquery.py  # Rows 27-50 only
    python3 dashboard_pipeline.py            # Rows 60+ (preserves 1-50)

🎯 VERIFY SUCCESS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ DNO auto-trigger works (edit A6/B6)
  ✓ HH profile button works
  ✓ BtM PPA updates via update_btm_ppa_from_bigquery.py
  ✓ Enhanced analysis populates row 60+
  ✓ No conflicts or overwrites
  ✓ Shared DNO rates (B10-D10) used by both
  ✓ Menu items work: Refresh DNO, Generate HH, Format Enhanced

📚 DOCUMENTATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  BESS_INTEGRATION_COMPLETE.md    - This summary
  BESS_INTEGRATION_PLAN.md        - Full architecture (22KB)
  BESS_DASHBOARD_IMPLEMENTATION.md - Technical details
  DEPLOYMENT_CHECKLIST.md         - Step-by-step guide

📞 SUPPORT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Repository: https://github.com/GeorgeDoors888/GB-Power-Market-JJ
  Maintainer: george@upowerenergy.uk
  Status: ✅ Ready for Production

EOF
