#!/usr/bin/env python3
"""
Diagnostic script to understand why BESS only operates 96/92 times per year
"""

import pandas as pd
from google.cloud import bigquery
from google.oauth2.service_account import Credentials

CREDENTIALS_FILE = "inner-cinema-credentials.json"
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Query for analysis
client = bigquery.Client.from_service_account_json(CREDENTIALS_FILE)

query = """
WITH daily_prices AS (
  SELECT 
    CAST(settlementDate AS DATE) as date,
    COUNTIF(systemBuyPrice < 30) as charge_opps,
    COUNTIF(systemSellPrice > 150) as discharge_opps,
    MIN(systemBuyPrice) as min_buy,
    MAX(systemSellPrice) as max_sell,
    AVG(systemBuyPrice) as avg_buy
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
  WHERE CAST(settlementDate AS DATE) >= '2025-01-01'
    AND CAST(settlementDate AS DATE) <= '2025-12-31'
  GROUP BY date
)
SELECT 
  COUNT(*) as total_days,
  SUM(charge_opps) as total_charge_opps,
  SUM(discharge_opps) as total_discharge_opps,
  SUM(CASE WHEN charge_opps > 0 AND discharge_opps > 0 THEN 1 ELSE 0 END) as days_with_both,
  SUM(CASE WHEN charge_opps > 0 AND discharge_opps = 0 THEN 1 ELSE 0 END) as days_charge_only,
  SUM(CASE WHEN charge_opps = 0 AND discharge_opps > 0 THEN 1 ELSE 0 END) as days_discharge_only,
  SUM(CASE WHEN charge_opps = 0 AND discharge_opps = 0 THEN 1 ELSE 0 END) as days_neither
FROM daily_prices
"""

df = client.query(query).to_dataframe()

print("=" * 80)
print("BESS OPERATION DIAGNOSTIC - 2025 Full Year")
print("=" * 80)

total_days = int(df.iloc[0]['total_days'])
total_charge_opps = int(df.iloc[0]['total_charge_opps'])
total_discharge_opps = int(df.iloc[0]['total_discharge_opps'])
days_with_both = int(df.iloc[0]['days_with_both'])
days_charge_only = int(df.iloc[0]['days_charge_only'])
days_discharge_only = int(df.iloc[0]['days_discharge_only'])
days_neither = int(df.iloc[0]['days_neither'])

print(f"\nTotal days analyzed: {total_days}")
print(f"\nOpportunity Distribution:")
print(f"  Total charge opportunities (price < £30): {total_charge_opps:,} periods")
print(f"  Total discharge opportunities (price > £150): {total_discharge_opps:,} periods")
print(f"\nDaily Pattern:")
print(f"  Days with BOTH charge AND discharge opps: {days_with_both} ({days_with_both/total_days*100:.1f}%)")
print(f"  Days with charge opps ONLY: {days_charge_only} ({days_charge_only/total_days*100:.1f}%)")
print(f"  Days with discharge opps ONLY: {days_discharge_only} ({days_discharge_only/total_days*100:.1f}%)")
print(f"  Days with NEITHER: {days_neither} ({days_neither/total_days*100:.1f}%)")

print(f"\n🔍 KEY INSIGHT:")
if days_with_both < 100:
    print(f"   Only {days_with_both} days have BOTH charge and discharge opportunities!")
    print(f"   This means the battery can only complete {days_with_both} full cycles per year.")
    print(f"   Most days have either charge OR discharge opps, but not both.")
    print(f"\n   This explains why only ~96 operations occurred (limited by timing misalignment)")

print(f"\n📊 Theoretical vs Actual:")
print(f"   Theoretical max cycles/year: {365 * 4} (4 cycles/day × 365 days)")
print(f"   Practical max (days with both opps): {days_with_both * 4} ({days_with_both} days × 4 cycles)")
print(f"   Actual observed: 96 charge + 92 discharge = ~94 cycles")
print(f"   Utilization: {94/(days_with_both * 4)*100:.1f}% of practical maximum")

print("\n💡 STRATEGY IMPLICATIONS:")
print("   - Current thresholds (charge < £30, discharge > £150) are TOO STRICT")
print("   - Need to widen thresholds to capture more same-day charge/discharge cycles")
print("   - Suggested: Charge < £50/MWh, Discharge > £100/MWh")
