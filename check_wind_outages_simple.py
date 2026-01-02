#!/usr/bin/env python3
"""
Quick Wind Farm Status Check
Queries current wind generation and SO/SO constraints
"""

from google.cloud import bigquery
from datetime import datetime
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
client = bigquery.Client(project=PROJECT_ID, location="US")

print("🌬️  WIND FARM STATUS CHECK")
print("=" * 80)
print()

# ============================================================================
# 1. Current Wind Generation (All UK)
# ============================================================================
query_wind = f"""
WITH latest_wind AS (
  SELECT 
    PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', publishTime) as pub_time,
    SUM(CASE WHEN fuelType = 'WIND' THEN generation ELSE 0 END) as wind_mw
  FROM `{PROJECT_ID}.{DATASET}.generation_fuel_instant`
  WHERE fuelType IN ('WIND', 'WINDOFF', 'WINDON')  -- All wind types
  GROUP BY publishTime
  ORDER BY publishTime DESC
  LIMIT 1
)
SELECT 
  pub_time,
  wind_mw,
  ROUND((wind_mw / 30000.0) * 100, 1) as cf_pct  -- ~30 GW total UK wind capacity
FROM latest_wind
"""

print("📊 CURRENT WIND GENERATION")
print("-" * 80)
df_wind = client.query(query_wind).to_dataframe()
if len(df_wind) > 0:
    row = df_wind.iloc[0]
    print(f"⏰ Time: {row['pub_time']}")
    print(f"🌬️  Wind Output: {row['wind_mw']:,.0f} MW")
    print(f"📈 Capacity Factor: ~{row['cf_pct']:.1f}%")
    print()
    
    if row['cf_pct'] < 20:
        print("🔴 STATUS: LOW WIND - Calm conditions or curtailment")
    elif row['cf_pct'] < 40:
        print("🟡 STATUS: MODERATE WIND")
    else:
        print("🟢 STATUS: HIGH WIND")
else:
    print("⚠️  No data available")

print()
print()

# ============================================================================
# 2. SO/SO Constrained Units (Last 7 Days)
# ============================================================================
query_so = f"""
SELECT 
  bmUnit,
  COUNT(*) as so_events,
  MAX(CAST(acceptanceTime AS TIMESTAMP)) as latest_event
FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
WHERE CAST(acceptanceTime AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  AND soFlag = 'T'
  AND bmUnit LIKE '%W%'  -- Wind units
GROUP BY bmUnit
ORDER BY so_events DESC
LIMIT 20
"""

print("🚨 SO/SO CONSTRAINED UNITS (Last 7 Days)")
print("-" * 80)
df_so = client.query(query_so).to_dataframe()
if len(df_so) > 0:
    print(df_so.to_string(index=False))
    print()
    print(f"⚠️  Total Units Constrained: {len(df_so)}")
    print(f"⚠️  Total SO-SO Events: {df_so['so_events'].sum():,}")
else:
    print("✅ No SO/SO constraints detected")

print()
print()

# ============================================================================
# 3. Recent Balancing Actions (Last 24h)
# ============================================================================
query_actions = f"""
SELECT 
  acceptanceType,
  COUNT(*) as action_count,
  COUNT(DISTINCT bmUnit) as unique_units
FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
WHERE CAST(acceptanceTime AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
  AND bmUnit LIKE '%W%'
GROUP BY acceptanceType
ORDER BY action_count DESC
"""

print("⚡ BALANCING ACTIONS (Last 24 Hours)")
print("-" * 80)
df_actions = client.query(query_actions).to_dataframe()
if len(df_actions) > 0:
    print(df_actions.to_string(index=False))
    print()
    print(f"📊 Total Actions: {df_actions['action_count'].sum():,}")
else:
    print("✅ No balancing actions")

print()
print()

# ============================================================================
# 4. Export for Dashboard
# ============================================================================
summary = {
    'timestamp': datetime.utcnow().isoformat(),
    'wind_mw': df_wind.iloc[0]['wind_mw'] if len(df_wind) > 0 else 0,
    'wind_cf_pct': df_wind.iloc[0]['cf_pct'] if len(df_wind) > 0 else 0,
    'so_constrained_units': len(df_so),
    'total_so_events_7d': df_so['so_events'].sum() if len(df_so) > 0 else 0,
    'balancing_actions_24h': df_actions['action_count'].sum() if len(df_actions) > 0 else 0
}

output_file = '/tmp/wind_status_summary.csv'
pd.DataFrame([summary]).to_csv(output_file, index=False)

print("=" * 80)
print("✅ ANALYSIS COMPLETE")
print("=" * 80)
print(f"📁 Results saved to: {output_file}")
print()

# Print summary
print("📋 SUMMARY:")
print(f"  Wind Output: {summary['wind_mw']:,.0f} MW ({summary['wind_cf_pct']:.1f}% CF)")
print(f"  SO-Constrained Units: {summary['so_constrained_units']}")
print(f"  Balancing Actions (24h): {summary['balancing_actions_24h']}")
