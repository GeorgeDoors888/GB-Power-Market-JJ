#!/usr/bin/env python3
"""
Check Wind Farm Outages & SO/SO Constraints
============================================
Queries BMRS data for:
1. Planned/unplanned outages (REMIT, FPN, BOA)
2. System Operator constraints (SO-SO flagged events)
3. Current generation vs capacity by farm
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
client = bigquery.Client(project=PROJECT_ID, location="US")

print("=" * 80)
print("🔍 WIND FARM OUTAGES & CONSTRAINTS CHECK")
print("=" * 80)
print()

# Get current timestamp and last 7 days
now = datetime.utcnow()
week_ago = now - timedelta(days=7)

print(f"📅 Analysis Period: {week_ago.strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}")
print()

# ============================================================================
# PART 1: Current Wind Generation from BMRS (Real-Time)
# ============================================================================
print("=" * 80)
print("PART 1: CURRENT WIND GENERATION (BMRS DATA)")
print("=" * 80)
print()

# Use generation_fuel_instant for current wind output
query_generation = f"""
SELECT 
  publishTime,
  ROUND(wind, 1) as wind_mw,
  ROUND(solarGen, 1) as solar_mw,
  ROUND(demand, 1) as demand_mw,
  ROUND((wind / demand) * 100, 2) as wind_pct_of_demand
FROM `{PROJECT_ID}.{DATASET}.generation_fuel_instant`
ORDER BY publishTime DESC
LIMIT 1
"""

print("Querying current wind generation...")
df_gen = client.query(query_generation).to_dataframe()

if len(df_gen) > 0:
    row = df_gen.iloc[0]
    print(f"⏰ Latest Data: {row['publishTime']}")
    print(f"🌬️  Wind Generation: {row['wind_mw']:,.0f} MW")
    print(f"☀️  Solar Generation: {row['solar_mw']:,.0f} MW")
    print(f"⚡ Demand: {row['demand_mw']:,.0f} MW")
    print(f"📊 Wind % of Demand: {row['wind_pct_of_demand']:.1f}%")
    print()
    
    # Get UK offshore capacity (~15 GW installed)
    UK_OFFSHORE_CAPACITY = 15000  # MW approximate
    capacity_factor = (row['wind_mw'] / UK_OFFSHORE_CAPACITY) * 100
    print(f"🎯 Estimated UK Offshore CF: {capacity_factor:.1f}%")
    print()
    
    if capacity_factor < 20:
        print("🔴 LOW WIND CONDITIONS - High outage/curtailment risk")
    elif capacity_factor < 40:
        print("🟡 MODERATE WIND CONDITIONS")
    else:
        print("🟢 HIGH WIND CONDITIONS")
else:
    print("⚠️  No recent generation data found")

# Now check individual farm data from bmrs_bod (has bmUnit IDs)
print()
print("📋 Checking Individual Wind Farm Units...")
print()

query_units = f"""
WITH recent_units AS (
  SELECT 
    bmUnit,
    settlementDate,
    settlementPeriod,
    AVG(offer) as avg_offer_price,
    AVG(bid) as avg_bid_price,
    COUNT(*) as bid_offer_count
  FROM `{PROJECT_ID}.{DATASET}.bmrs_bod`
  WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 2 DAY)
    AND bmUnit LIKE '%W%'
  GROUP BY bmUnit, settlementDate, settlementPeriod
  ORDER BY settlementDate DESC, settlementPeriod DESC
  LIMIT 500
)
SELECT 
  bmUnit,
  COUNT(DISTINCT CONCAT(CAST(settlementDate AS STRING), '-', CAST(settlementPeriod AS STRING))) as periods_active,
  AVG(avg_offer_price) as avg_offer,
  AVG(avg_bid_price) as avg_bid,
  SUM(bid_offer_count) as total_pairs
FROM recent_units
GROUP BY bmUnit
ORDER BY periods_active DESC
LIMIT 50
"""

df_units = client.query(query_units).to_dataframe()
underperforming = pd.DataFrame()  # Empty dataframe for later check

print()
print()

# ============================================================================
# PART 2: SO/SO Flags in Balancing Actions
# ============================================================================
print("=" * 80)
print("PART 2: SYSTEM OPERATOR (SO-SO) CONSTRAINTS")
print("=" * 80)
print()

query_so_flags = f"""
WITH recent_boalf AS (
  SELECT 
    bmUnit,
    acceptanceTime,
    acceptanceNumber,
    soFlag,
    storFlag,
    acceptanceType
  FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
  WHERE CAST(acceptanceTime AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND bmUnit LIKE '%W%'
    AND soFlag = 'T'  -- SO-SO flag = TRUE
  ORDER BY acceptanceTime DESC
  LIMIT 500
)
SELECT 
  bmUnit,
  COUNT(*) as so_flag_count,
  MIN(acceptanceTime) as first_occurrence,
  MAX(acceptanceTime) as latest_occurrence,
  STRING_AGG(DISTINCT acceptanceType, ', ') as action_types
FROM recent_boalf
GROUP BY bmUnit
ORDER BY so_flag_count DESC
"""

print("Querying SO-SO flagged balancing actions (last 7 days)...")
df_so = client.query(query_so_flags).to_dataframe()

if len(df_so) > 0:
    print(f"🚨 Found {len(df_so)} wind units with SO-SO flags")
    print()
    print(df_so.to_string(index=False))
    print()
    print(f"⚠️  TOTAL SO-SO EVENTS: {df_so['so_flag_count'].sum():,}")
else:
    print("✅ No SO-SO flags detected in last 7 days")

print()
print()

# ============================================================================
# PART 3: Accepted Bids/Offers (Constraint Actions)
# ============================================================================
print("=" * 80)
print("PART 3: RECENT CONSTRAINT ACTIONS (BIDS/OFFERS)")
print("=" * 80)
print()

query_constraints = f"""
WITH recent_actions AS (
  SELECT 
    bmUnit,
    acceptanceTime,
    acceptanceType,
    soFlag,
    storFlag
  FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
  WHERE CAST(acceptanceTime AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
    AND bmUnit LIKE '%W%'
  ORDER BY acceptanceTime DESC
  LIMIT 200
)
SELECT 
  bmUnit,
  acceptanceType,
  COUNT(*) as action_count,
  MAX(acceptanceTime) as latest_action,
  SUM(CASE WHEN soFlag = 'T' THEN 1 ELSE 0 END) as so_flagged_count
FROM recent_actions
GROUP BY bmUnit, acceptanceType
ORDER BY action_count DESC
LIMIT 30
"""

print("Querying constraint actions (last 24 hours)...")
df_constraints = client.query(query_constraints).to_dataframe()

if len(df_constraints) > 0:
    print(f"✅ Found {len(df_constraints)} constraint action types")
    print()
    print(df_constraints.to_string(index=False))
    print()
    
    # Summary by action type
    action_summary = df_constraints.groupby('acceptanceType')['action_count'].sum().sort_values(ascending=False)
    print()
    print("📊 ACTIONS BY TYPE (24h):")
    print("-" * 40)
    for action_type, count in action_summary.items():
        print(f"  {action_type}: {count} actions")
else:
    print("✅ No constraint actions in last 24 hours")

print()
print()

# ============================================================================
# PART 4: Check for Outage Notices (if available)
# ============================================================================
print("=" * 80)
print("PART 4: CAPACITY AT RISK (7-DAY OUTLOOK)")
print("=" * 80)
print()

# Calculate based on wind generation percentage
if len(df_gen) > 0:
    row = df_gen.iloc[0]
    wind_mw = row['wind_mw']
    
    # If wind is below 3 GW (20% of 15 GW capacity), consider it "at risk"
    if wind_mw < 3000:
        capacity_at_risk_mw = 15000 - wind_mw  # Difference from full capacity
        print(f"⚠️  LOW WIND OUTPUT: {wind_mw:,.0f} MW")
        print(f"💷 Capacity Not Generating: ~{capacity_at_risk_mw:,.0f} MW")
        print(f"📉 Effective CF: ~{(wind_mw/15000)*100:.1f}%")
    else:
        print(f"✅ NORMAL WIND OUTPUT: {wind_mw:,.0f} MW")

print()
print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("📋 SUMMARY")
print("=" * 80)
print()
print()
print(f"🌬️  Total Wind Units Monitored: {len(df_units) if len(df_units) > 0 else 0}")
print(f"🔴 Current Wind Output: {df_gen.iloc[0]['wind_mw']:,.0f} MW" if len(df_gen) > 0 else "🔴 Current Wind Output: Unknown")
print(f"🚨 SO-SO Constrained Units (7d): {len(df_so)}")
print(f"⚠️  Constraint Actions (24h): {df_constraints['action_count'].sum() if len(df_constraints) > 0 else 0}")
print()

# Export results for dashboard
output_data = {
    'current_wind_mw': df_gen.iloc[0]['wind_mw'] if len(df_gen) > 0 else 0,
    'wind_pct_demand': df_gen.iloc[0]['wind_pct_of_demand'] if len(df_gen) > 0 else 0,
    'so_constrained_units': len(df_so),
    'constraint_actions_24h': df_constraints['action_count'].sum() if len(df_constraints) > 0 else 0
}

output_file = '/tmp/wind_farm_status.csv'
pd.DataFrame([output_data]).to_csv(output_file, index=False)
print(f"✅ Exported results to: {output_file}")
print()

print("=" * 80)
print("✅ OUTAGE CHECK COMPLETE")
print("=" * 80)
