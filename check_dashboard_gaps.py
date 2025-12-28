#!/usr/bin/env python3
"""Quick check: What BigQuery data is NOT in the dashboard"""
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

print("\n🔍 KEY DATASETS IN BIGQUERY NOT YET IN DASHBOARD:")
print("="*80)

# Check key tables
key_tables = {
    '🆕 P114 Settlement (NEW Dec 2025)': [
        'elexon_p114_s0142_bpi',
        'p114_settlement_canonical', 
        'mart_vlp_revenue_p114'
    ],
    '⚡ Balancing Mechanism': [
        'bmrs_disbsad',
        'bmrs_netbsad',
        'boalf_with_prices'
    ],
    '🌊 Generation Data': [
        'bmrs_indgen',
        'bmrs_b1610',
        'bmrs_b1620',
        'demand_outturn_hybrid'
    ],
    '💨 Wind Forecasts': [
        'bmrs_windfor',
        'bmrs_windfor_iris'
    ],
    '⚠️  Outages': [
        'bmrs_remit_unavailability',
        'bmrs_uo'
    ],
    '🔌 Interconnectors': [
        'bmrs_interfuelhh'
    ]
}

for category, tables in key_tables.items():
    print(f"\n{category}:")
    for table_name in tables:
        try:
            table = client.get_table(f'inner-cinema-476211-u9.uk_energy_prod.{table_name}')
            rows = table.num_rows if table.num_rows else 0
            gb = (table.num_bytes / (1024**3)) if table.num_bytes else 0
            status = "✅" if rows > 0 else "⚠️ "
            print(f"  {status} {table_name:<35} {rows:>12,} rows  {gb:>6.1f} GB")
        except:
            print(f"  ❌ {table_name:<35} NOT FOUND")

print("\n\n💡 TOP RECOMMENDATIONS:")
print("-"*80)
print("""
1. ADD P114 SETTLEMENT DATA (highest priority):
   - 23.5M records of TRUE VLP revenue (not BM acceptances)
   - Run: python3 update_dashboard_p114.py
   
2. ADD WIND FORECAST TRACKING:
   - Compare forecast vs actual generation
   - Forecast accuracy metrics
   
3. ADD OUTAGES DASHBOARD:
   - 177k+ REMIT outage messages
   - Show capacity offline by fuel type
   
4. ADD SYSTEM IMBALANCE DATA:
   - bmrs_disbsad: Settlement adjustment (512k rows)
   - Shows system long/short position
""")
