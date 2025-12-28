#!/usr/bin/env python3
"""
Consolidate KPI layout: Column K = Name + Value + Description combined, Column L = Sparkline
Replace ⚡ with ⚡ throughout
Add Week/Month/Year views for same KPIs
Fix frequency display issue
"""

import sys

print("""
═══════════════════════════════════════════════════════════════
KPI LAYOUT CONSOLIDATION PLAN
═══════════════════════════════════════════════════════════════

CURRENT LAYOUT (K13-K22):
  K: KPI Name                    | L: Value      | M: Description | N-S: Sparkline (merged 6 cols)
  --------------------------------|---------------|----------------|--------------------------------
  Real-time imbalance price      | £0.00/MWh     | SSP=SBP        | ▁▂▃▅▇█ (sparkline chart)

NEW CONSOLIDATED LAYOUT (K13-K22):
  K: Combined (Name + Value + Desc)               | L: Sparkline
  -------------------------------------------------|--------------------------------
  Real-time imbalance price • £0.00/MWh • SSP=SBP | ▁▂▃▅▇█ (sparkline chart)

BENEFITS:
  ✓ More compact, professional appearance
  ✓ Easier to read single-line KPIs
  ✓ Frees up columns M-S for additional data
  ✓ Consistent with user's requested format

NEW SECTIONS TO ADD:
  1. K13-K22: 24-HOUR VIEW (existing, reformatted)
  2. K24-K33: 7-DAY (WEEKLY) VIEW
  3. K35-K44: 30-DAY (MONTHLY) VIEW
  4. K46-K55: 12-MONTH (YEARLY) VIEW

All sections will have same 10 KPIs:
  • Real-time imbalance price / Period average
  • 7-Day Average → Rolling average for timeframe
  • 30-Day Average → Rolling average for timeframe
  • Deviation from baseline
  • Period High
  • Period Low
  • Total BM Cashflow
  • EWAP Offer
  • EWAP Bid
  • Dispatch Intensity

FREQUENCY FIX:
  Issue: Shows "+0.000 Hz" instead of actual frequency (e.g., "50.023 Hz")
  Root cause: Using latest_freq from physics_df which may be 0 if no recent data
  Fix: Query bmrs_freq_iris directly for last 5-minute average, fallback to bmrs_freq historical

EMOJI REPLACEMENT:
  ⚡ → ⚡ (rocket to lightning bolt throughout codebase)

═══════════════════════════════════════════════════════════════
""")

print("⚠️  IMPORTANT: This script provides the PLAN for update_live_metrics.py changes.")
print("⚠️  Actual implementation requires editing update_live_metrics.py directly.")
print("")
print("📋 CHANGES REQUIRED IN update_live_metrics.py:")
print("")
print("1. Modify K13-K22 combined_kpis array:")
print("   - Change from 9 columns [Name, Value, Desc, Spark, '', '', '', '', Flag]")
print("   - To 2 columns [Combined_Text, Sparkline]")
print("   - Format: 'Name • Value • Description' in column K")
print("   - Sparkline goes in column L")
print("")
print("2. Add query functions for Week/Month/Year views:")
print("   - get_system_price_weekly(bq_client) - 7 days of data")
print("   - get_system_price_monthly(bq_client) - 30 days of data")
print("   - get_system_price_yearly(bq_client) - 365 days of data")
print("")
print("3. Fix frequency display in L48 (Grid Frequency row):")
print("   - Add direct query to bmrs_freq_iris for last 5 minutes")
print("   - Format as '{freq:.3f} Hz' without '+' sign")
print("")
print("4. Update header text:")
print("   - K12: '⚡ MARKET DYNAMICS - 24 HOUR VIEW' (replace 📊 Bar with ⚡)")
print("   - K23: '⚡ MARKET DYNAMICS - 7 DAY VIEW' (new)")
print("   - K34: '⚡ MARKET DYNAMICS - 30 DAY VIEW' (new)")
print("   - K45: '⚡ MARKET DYNAMICS - 12 MONTH VIEW' (new)")
print("")
print("5. Update cell merge operations:")
print("   - K12:L12 (header for 24h view) - only 2 columns now")
print("   - Remove N13:S13, N14:S14, etc. merges")
print("   - Sparklines now single column L, no merge needed")
print("")
print("6. Update cache.queue_update calls:")
print("   - K13:L22 (not K13:S22) for 24h view")
print("   - K24:L33 for weekly view")
print("   - K35:L44 for monthly view")
print("   - K46:L55 for yearly view")
print("")

# Sample code for the new layout
sample_code = """
# EXAMPLE IMPLEMENTATION (insert into update_live_metrics.py around line 1140):

# K12 HEADER ROW (merged K12:L12 only - 2 columns)
cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'K12', [['⚡ MARKET DYNAMICS - 24 HOUR VIEW']])

# POPULATE K13:L22 (10 rows x 2 cols: K=Combined text, L=Sparkline)
combined_kpis = [
    [f'Real-time imbalance price • £{latest_price:.2f}/MWh • SSP=SBP {condition}', spark_current],
    [f'7-Day Average • £{avg_7d:.2f}/MWh • Rolling mean', spark_7d],
    [f'30-Day Average • £{avg_30d:.2f}/MWh • Rolling mean', spark_30d],
    [f'Deviation from 7d • {deviation:+.1f}% • vs 7-day avg', spark_dev],
    [f'30-Day High • £{max_30d:.2f}/MWh • Max price', spark_high],
    [f'30-Day Low • £{min_30d:.2f}/MWh • Min price', spark_low],
    [f'Total BM Cashflow • £{total_cashflow/1000:.1f}k • Σ(Vol × Price)', spark_cashflow],
    [f'EWAP Offer • £{avg_ewap_offer:.2f}/MWh • Energy-weighted avg', spark_ewap_offer],
    [f'EWAP Bid • £{latest_bm["ewap_bid"]:.2f}/MWh • Energy-weighted avg', spark_ewap_bid],
    [f'Dispatch Intensity • {avg_dispatch:.1f}/hr • Acceptances/hour • {workhorse_index:.1f}% active', spark_dispatch]
]

cache.queue_update(SPREADSHEET_ID, 'Live Dashboard v2', 'K13:L22', combined_kpis)

# FREQUENCY FIX (around line 1185 in get_frequency_physics or display section):
# Query latest frequency directly
freq_query = f'''
WITH latest_freq AS (
  SELECT AVG(frequency) as freq
  FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
  WHERE CAST(measurementTime AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 5 MINUTE)
)
SELECT freq FROM latest_freq
'''
latest_freq_result = bq_client.query(freq_query).to_dataframe()
latest_freq = latest_freq_result['freq'].iloc[0] if len(latest_freq_result) > 0 and latest_freq_result['freq'].iloc[0] > 0 else 50.0

# Then in physics_rows update (around line 1203):
physics_rows = [
    [f'Grid Frequency • {latest_freq:.3f} Hz', spark_freq, freq_state],  # Removed '+' sign
    [f'Freq Range (Min-Max) • {min_freq_overall:.3f} - {max_freq_overall:.3f} Hz', spark_freq_min, ''],
    [f'Net Imbalance Vol (NIV) • {total_niv:+.0f} MWh', spark_niv, niv_state],
    [f'Avg Frequency • {avg_freq:.3f} Hz', spark_freq_max, '']
]
"""

print(sample_code)

print("")
print("═══════════════════════════════════════════════════════════════")
print("📁 FILES TO UPDATE:")
print("   1. update_live_metrics.py - Main KPI layout changes (lines 1130-1220)")
print("   2. Complete script will be generated in next step")
print("═══════════════════════════════════════════════════════════════")
print("")
print("✅ Plan documented. Ready to implement changes to update_live_metrics.py")
