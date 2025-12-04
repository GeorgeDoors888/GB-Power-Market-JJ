#!/usr/bin/env python3
"""
Current Week Revenue & Cost Analysis

Queries BigQuery for actual this-week data to show:
- Revenue sources and amounts
- Cost components and amounts
- Real system prices
"""

import os
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../inner-cinema-credentials.json"

print("=" * 80)
print("THIS WEEK'S REVENUE SOURCES & COSTS (BtM PPA System)")
print("=" * 80)
print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# Connect to BigQuery
client = bigquery.Client(project="inner-cinema-476211-u9", location="US")

# Get this week's date range
today = datetime.now().date()
week_start = today - timedelta(days=today.weekday())  # Monday
week_end = week_start + timedelta(days=6)  # Sunday

print(f"Week: {week_start} to {week_end} (Mon-Sun)")

# ============================================================================
# 1. SYSTEM PRICES (THIS WEEK)
# ============================================================================

print("\n" + "=" * 80)
print("1️⃣  SYSTEM BUY PRICES (This Week by DUoS Band)")
print("=" * 80)

sql_prices = f"""
WITH prices_with_band AS (
  SELECT
    settlementDate,
    settlementPeriod,
    systemBuyPrice,
    EXTRACT(DAYOFWEEK FROM settlementDate) AS dow,
    CASE
      WHEN EXTRACT(DAYOFWEEK FROM settlementDate) BETWEEN 2 AND 6
           AND settlementPeriod BETWEEN 33 AND 39
        THEN 'RED'
      WHEN EXTRACT(DAYOFWEEK FROM settlementDate) BETWEEN 2 AND 6
           AND ((settlementPeriod BETWEEN 17 AND 32) OR (settlementPeriod BETWEEN 40 AND 44))
        THEN 'AMBER'
      ELSE 'GREEN'
    END AS duos_band
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
  WHERE settlementDate >= '{week_start}'
    AND settlementDate <= '{week_end}'
    AND systemBuyPrice IS NOT NULL
)
SELECT
  duos_band,
  COUNT(*) as periods,
  ROUND(AVG(systemBuyPrice), 2) AS avg_price,
  ROUND(MIN(systemBuyPrice), 2) AS min_price,
  ROUND(MAX(systemBuyPrice), 2) AS max_price,
  ROUND(STDDEV(systemBuyPrice), 2) AS std_dev
FROM prices_with_band
GROUP BY duos_band
ORDER BY duos_band
"""

try:
    df_prices = client.query(sql_prices).to_dataframe()
    
    if not df_prices.empty:
        print("\n📊 System Buy Prices by Band:")
        print(f"{'Band':<10} {'Periods':<10} {'Average':<12} {'Min':<12} {'Max':<12} {'Std Dev':<10}")
        print("-" * 80)
        
        total_import_costs = {}
        
        for _, row in df_prices.iterrows():
            band = row['duos_band']
            avg = row['avg_price']
            
            # Add DUoS and levies
            duos_rates = {'RED': 17.64, 'AMBER': 2.05, 'GREEN': 0.11}
            levies = 98.15
            
            total_cost = avg + duos_rates[band] + levies
            total_import_costs[band] = total_cost
            
            print(f"{band:<10} {int(row['periods']):<10} £{avg:<11.2f} £{row['min_price']:<11.2f} £{row['max_price']:<11.2f} £{row['std_dev']:<9.2f}")
        
        print("\n💰 Total Import Costs (System Buy + DUoS + Levies):")
        for band in ['GREEN', 'AMBER', 'RED']:
            if band in total_import_costs:
                duos = {'RED': 17.64, 'AMBER': 2.05, 'GREEN': 0.11}[band]
                sbp = total_import_costs[band] - duos - 98.15
                print(f"   {band:<6}: £{sbp:>6.2f} + £{duos:>5.2f} + £98.15 = £{total_import_costs[band]:.2f}/MWh")
    else:
        print("⚠️  No price data available for this week")
        total_import_costs = {'GREEN': 164.09, 'AMBER': 174.11, 'RED': 208.72}
except Exception as e:
    print(f"⚠️  Could not fetch this week's prices: {e}")
    print("Using recent 180-day averages instead")
    total_import_costs = {'GREEN': 164.09, 'AMBER': 174.11, 'RED': 208.72}

# ============================================================================
# 2. REVENUE SOURCES
# ============================================================================

print("\n" + "=" * 80)
print("2️⃣  REVENUE SOURCES (Annual Estimates)")
print("=" * 80)

PPA_PRICE = 150.0
VLP_UPLIFT = 12.0
VLP_PARTICIPATION = 0.20
DC_REVENUE = 195458

print("\n💷 Revenue Streams:")
print(f"{'Source':<30} {'Rate/Price':<20} {'Volume/Capacity':<20} {'Annual Revenue':<20}")
print("-" * 90)

# Revenue 1: PPA Contract Sales
site_demand_mwh = 2.5 * 8760  # 2.5 MW constant
ppa_revenue_theoretical = site_demand_mwh * PPA_PRICE

print(f"{'1. PPA Contract Sales':<30} £{PPA_PRICE}/MWh          {site_demand_mwh:,.0f} MWh         £{ppa_revenue_theoretical:,.0f}")

# Revenue 2: VLP/BM Payments
vlp_revenue_theoretical = 0  # Currently zero due to no charging
print(f"{'2. VLP/BM Payments':<30} £{VLP_UPLIFT}/MWh          0 MWh (no charging)  £{vlp_revenue_theoretical:,.0f}")

# Revenue 3: Dynamic Containment
print(f"{'3. Dynamic Containment':<30} Contract             5.0 MWh capacity     £{DC_REVENUE:,.0f}")

# Revenue 4: Curtailment (try to get real data)
sql_curtailment = f"""
SELECT
  COUNT(*) as acceptance_count,
  SUM(CASE WHEN bidOfferFlag = 'B' THEN (levelTo - levelFrom) * 0.5 ELSE 0 END) AS curtailment_mwh,
  SUM(CASE WHEN bidOfferFlag = 'B' THEN (levelTo - levelFrom) * 0.5 * acceptancePrice ELSE 0 END) AS curtailment_revenue
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
WHERE settlementDate >= '{week_start}'
  AND settlementDate <= '{week_end}'
  AND bmUnit IN ('2__FBPGM001', '2__FBPGM002')
"""

try:
    df_curtail = client.query(sql_curtailment).to_dataframe()
    if not df_curtail.empty and df_curtail.iloc[0]['acceptance_count'] > 0:
        curtail_mwh = df_curtail.iloc[0]['curtailment_mwh']
        curtail_rev = df_curtail.iloc[0]['curtailment_revenue']
        curtail_annual = curtail_rev * 52 if curtail_rev > 0 else 0
        print(f"{'4. Curtailment (BM Bids)':<30} Variable             {curtail_mwh:.0f} MWh this week    £{curtail_annual:,.0f} (annualized)")
    else:
        print(f"{'4. Curtailment (BM Bids)':<30} Variable             0 MWh                £0")
except:
    print(f"{'4. Curtailment (BM Bids)':<30} Variable             Data unavailable     £0")

print("-" * 90)
print(f"{'TOTAL THEORETICAL REVENUE':<50} £{ppa_revenue_theoretical + DC_REVENUE:,.0f}/year")

# ============================================================================
# 3. COST COMPONENTS
# ============================================================================

print("\n" + "=" * 80)
print("3️⃣  COST COMPONENTS (Per MWh Imported)")
print("=" * 80)

print("\n💸 Cost Breakdown:")
print(f"{'Cost Component':<30} {'Rate':<15} {'Type':<20} {'Notes':<30}")
print("-" * 95)

# Fixed costs (per MWh)
costs = [
    ("System Buy Price (GREEN)", f"£{total_import_costs.get('GREEN', 164.09) - 98.15 - 0.11:.2f}/MWh", "Variable (market)", "Wholesale energy cost"),
    ("System Buy Price (AMBER)", f"£{total_import_costs.get('AMBER', 174.11) - 98.15 - 2.05:.2f}/MWh", "Variable (market)", "Wholesale energy cost"),
    ("System Buy Price (RED)", f"£{total_import_costs.get('RED', 208.72) - 98.15 - 17.64:.2f}/MWh", "Variable (market)", "Wholesale energy cost"),
    ("", "", "", ""),
    ("DUoS - GREEN Band", "£0.11/MWh", "Fixed (DNO)", "Distribution charge"),
    ("DUoS - AMBER Band", "£2.05/MWh", "Fixed (DNO)", "Distribution charge"),
    ("DUoS - RED Band", "£17.64/MWh", "Fixed (DNO)", "Distribution charge"),
    ("", "", "", ""),
    ("TNUoS (Transmission)", "£12.50/MWh", "Fixed (levy)", "National Grid transmission"),
    ("BSUoS (Balancing)", "£4.50/MWh", "Fixed (levy)", "System balancing costs"),
    ("CCL (Climate Levy)", "£7.75/MWh", "Fixed (levy)", "Carbon tax"),
    ("RO (Renewables)", "£61.90/MWh", "Fixed (levy)", "Renewable obligation"),
    ("FiT (Feed-in Tariff)", "£11.50/MWh", "Fixed (levy)", "Feed-in tariff support"),
]

levy_total = 98.15

for cost in costs:
    if cost[0]:
        print(f"{cost[0]:<30} {cost[1]:<15} {cost[2]:<20} {cost[3]:<30}")

print("-" * 95)
print(f"{'TOTAL FIXED LEVIES':<30} £{levy_total}/MWh")

# ============================================================================
# 4. THIS WEEK'S PROFITABILITY
# ============================================================================

print("\n" + "=" * 80)
print("4️⃣  THIS WEEK'S PROFITABILITY ANALYSIS")
print("=" * 80)

print(f"\n📊 Import Costs vs PPA Price (£{PPA_PRICE}/MWh):")
print(f"{'Band':<10} {'Total Cost':<15} {'PPA Price':<15} {'Profit/Loss':<15} {'Status':<20}")
print("-" * 75)

for band in ['GREEN', 'AMBER', 'RED']:
    if band in total_import_costs:
        cost = total_import_costs[band]
        diff = PPA_PRICE - cost
        status = "✅ Profitable" if diff > 0 else "❌ Loss"
        print(f"{band:<10} £{cost:<14.2f} £{PPA_PRICE:<14.2f} £{diff:<14.2f} {status:<20}")

# Battery charging decision
can_charge_any = any(total_import_costs.get(b, 999) < 120 for b in ['GREEN', 'AMBER'])

print(f"\n🔋 Battery Charging Decision:")
print(f"   Charging Threshold: £120/MWh (PPA price - £30 margin)")
print(f"   Can charge GREEN? {'✅ YES' if total_import_costs.get('GREEN', 999) < 120 else '❌ NO'} (£{total_import_costs.get('GREEN', 0):.2f} vs £120)")
print(f"   Can charge AMBER? {'✅ YES' if total_import_costs.get('AMBER', 999) < 120 else '❌ NO'} (£{total_import_costs.get('AMBER', 0):.2f} vs £120)")
print(f"   Can charge RED?   ❌ NO (never profitable)")

if not can_charge_any:
    print(f"\n❌ RESULT: Battery will NOT charge this week")
    print(f"   All import costs exceed profitable threshold")
    print(f"   BtM PPA revenue: £0")
    print(f"   Only revenue: Dynamic Containment (£{DC_REVENUE:,.0f}/year)")
else:
    print(f"\n✅ RESULT: Battery CAN charge this week")

# ============================================================================
# 5. SUMMARY TABLE
# ============================================================================

print("\n" + "=" * 80)
print("5️⃣  WEEKLY SUMMARY")
print("=" * 80)

# Estimate actual costs for this week
hours_in_week = 168
red_hours_week = 3.5 * 5  # 3.5h/day weekdays
amber_hours_week = 10.5 * 5
green_hours_week = hours_in_week - red_hours_week - amber_hours_week

site_mw = 2.5
green_mwh_week = green_hours_week * site_mw
amber_mwh_week = amber_hours_week * site_mw
red_mwh_week = red_hours_week * site_mw

green_cost_week = green_mwh_week * total_import_costs.get('GREEN', 164.09)
amber_cost_week = amber_mwh_week * total_import_costs.get('AMBER', 174.11)
# Don't import RED if unprofitable
red_cost_week = 0 if total_import_costs.get('RED', 999) > PPA_PRICE else red_mwh_week * total_import_costs['RED']

total_cost_week = green_cost_week + amber_cost_week + red_cost_week
total_revenue_week = (green_mwh_week + amber_mwh_week) * PPA_PRICE  # No RED revenue if not imported
total_profit_week = total_revenue_week - total_cost_week

print(f"\n📅 This Week's Estimated Performance:")
print(f"{'Period':<15} {'Volume':<15} {'Cost':<20} {'Revenue':<20} {'Profit':<20}")
print("-" * 90)
print(f"{'GREEN':<15} {green_mwh_week:,.1f} MWh      £{green_cost_week:,.0f}           £{green_mwh_week * PPA_PRICE:,.0f}           £{green_mwh_week * PPA_PRICE - green_cost_week:,.0f}")
print(f"{'AMBER':<15} {amber_mwh_week:,.1f} MWh      £{amber_cost_week:,.0f}           £{amber_mwh_week * PPA_PRICE:,.0f}           £{amber_mwh_week * PPA_PRICE - amber_cost_week:,.0f}")
print(f"{'RED':<15} {0 if total_import_costs.get('RED', 999) > PPA_PRICE else red_mwh_week:,.1f} MWh      £{red_cost_week:,.0f}           £0                   £{-red_cost_week:,.0f}")
print(f"{'Battery':<15} {'0 MWh':<15} £0                   £0                   £0")
print("-" * 90)
print(f"{'TOTAL':<15} {green_mwh_week + amber_mwh_week:,.1f} MWh      £{total_cost_week:,.0f}           £{total_revenue_week:,.0f}           £{total_profit_week:,.0f}")
print(f"\n{'DC Revenue':<15} {'N/A':<15} £0                   £{DC_REVENUE/52:,.0f}           £{DC_REVENUE/52:,.0f}")
print(f"{'TOTAL PROFIT':<15} {'(this week)':<15} £{total_cost_week:,.0f}           £{total_revenue_week + DC_REVENUE/52:,.0f}           £{total_profit_week + DC_REVENUE/52:,.0f}")

print("\n" + "=" * 80)
print("END OF ANALYSIS")
print("=" * 80)
