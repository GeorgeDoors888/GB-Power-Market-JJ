#!/usr/bin/env python3
"""
PPA Profit Calculator
Finds settlement periods where PPA price > (System Buy + DUoS + Fixed Costs)
"""
from google.cloud import bigquery
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# Constants
PPA_PRICE = 150.0  # £/MWh (from B39)
DUOS_RED = 17.64   # £/MWh (1.764 p/kWh)
DUOS_AMBER = 2.05  # £/MWh (0.205 p/kWh)
DUOS_GREEN = 0.11  # £/MWh (0.011 p/kWh)

# Fixed costs per MWh
TNUOS = 12.50
BSUOS = 4.50
CCL = 7.75
RO = 61.90
FIT = 11.50
FIXED_COSTS = TNUOS + BSUOS + CCL + RO + FIT  # £98.15/MWh

# BigQuery setup
client = bigquery.Client.from_service_account_json(
    '/Users/georgemajor/GB-Power-Market-JJ/inner-cinema-credentials.json'
)

# UNIFIED ARCHITECTURE: Historical (Elexon API) + Real-Time (IRIS)
# bmrs_costs: Historical data up to Oct 28, 2025 (Elexon API backfill)
# bmrs_mid_iris: Real-time IRIS stream data for recent periods
# Use UNION to get complete timeline
query = """
WITH combined AS (
  -- Historical: bmrs_costs (System Buy Price from balancing mechanism)
  SELECT 
    settlementDate,
    settlementPeriod,
    MAX(systemBuyPrice) as system_buy_price,
    MAX(netImbalanceVolume) as volume,
    'historical' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
  WHERE CAST(settlementDate AS DATE) >= '2025-10-18'
    AND CAST(settlementDate AS DATE) < '2025-11-01'  -- Historical cutoff
    AND systemBuyPrice IS NOT NULL
  GROUP BY settlementDate, settlementPeriod
  
  UNION ALL
  
  -- Real-time: bmrs_mid_iris (Market Index Price as proxy for System Buy)
  -- Note: MIP is reference price; for actual settlements use bmrs_costs when available
  SELECT 
    settlementDate,
    settlementPeriod,
    MAX(price) as system_buy_price,
    NULL as volume,
    'iris' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
  WHERE CAST(settlementDate AS DATE) >= '2025-11-01'
    AND price IS NOT NULL
  GROUP BY settlementDate, settlementPeriod
)
SELECT * FROM combined
ORDER BY settlementDate DESC, settlementPeriod ASC
"""

print("=" * 80)
print("PPA PROFIT ANALYSIS - UNIFIED DATA (Historical + IRIS)")
print("=" * 80)
print(f"PPA Contract Price: £{PPA_PRICE:.2f}/MWh")
print(f"Fixed Costs: £{FIXED_COSTS:.2f}/MWh (TNUoS + BSUoS + CCL + RO + FiT)")
print()
print("Data Sources:")
print("  • Historical (Oct 18-28): bmrs_costs (System Buy Price)")
print("  • Real-time (Nov 1-30): bmrs_mid_iris (Market Index Price)")
print()

results = client.query(query).result()

# Map periods to time bands
def get_time_band(period):
    """Map settlement period to RED/AMBER/GREEN band
    
    Settlement Period to Time Mapping:
    - Period 1 = 00:00-00:30, Period 2 = 00:30-01:00, etc.
    - 48 periods per day (30-min intervals)
    
    DUoS Time Bands (NGED West Midlands HV):
    - RED: 16:00-19:30 = Periods 33-39 (highest rate: 17.64 p/kWh)
    - AMBER: 08:00-16:00 + 19:30-22:00 = Periods 17-32, 40-44 (2.05 p/kWh)
    - GREEN: 00:00-08:00 + 22:00-23:59 = Periods 1-16, 45-48 (0.11 p/kWh)
    """
    if 33 <= period <= 39:  # RED: 16:00-19:30
        return 'RED', DUOS_RED
    elif (17 <= period <= 32) or (40 <= period <= 44):  # AMBER: 08:00-16:00, 19:30-22:00
        return 'AMBER', DUOS_AMBER
    else:  # GREEN: 00:00-08:00, 22:00-23:59
        return 'GREEN', DUOS_GREEN

profitable_periods = []
all_periods = []

for row in results:
    date = row.settlementDate
    period = row.settlementPeriod
    system_buy = row.system_buy_price
    volume = row.volume
    
    band, duos = get_time_band(period)
    total_cost = system_buy + FIXED_COSTS + duos
    profit = PPA_PRICE - total_cost
    
    period_data = {
        'date': date,
        'period': period,
        'band': band,
        'system_buy': system_buy,
        'duos': duos,
        'fixed': FIXED_COSTS,
        'total_cost': total_cost,
        'profit': profit,
        'volume': volume
    }
    
    all_periods.append(period_data)
    
    if profit > 0:
        profitable_periods.append(period_data)

if not all_periods:
    print("❌ No data found")
    exit(1)

print(f"{'Date':<12} {'SP':<4} {'Band':<7} {'Sys Buy':<10} {'DUoS':<8} {'Total Cost':<12} {'Profit':<10}")
print("-" * 75)

# Show profitable periods
for pp in profitable_periods[:30]:
    print(f"{pp['date']!s:<12} {pp['period']:<4} {pp['band']:<7} £{pp['system_buy']:<9.2f} £{pp['duos']:<7.2f} £{pp['total_cost']:<11.2f} £{pp['profit']:<9.2f}")

if len(profitable_periods) > 30:
    print(f"... and {len(profitable_periods) - 30} more profitable periods")

print("\n" + "=" * 80)
print("SUMMARY - PROFITABILITY ANALYSIS")
print("=" * 80)
print(f"Total Periods Analyzed: {len(all_periods)}")
print(f"Profitable Periods: {len(profitable_periods)} ({len(profitable_periods)/len(all_periods)*100:.1f}%)")
print(f"Unprofitable Periods: {len(all_periods) - len(profitable_periods)} ({(len(all_periods) - len(profitable_periods))/len(all_periods)*100:.1f}%)")

if profitable_periods:
    avg_profit = sum(p['profit'] for p in profitable_periods) / len(profitable_periods)
    total_profit = sum(p['profit'] for p in profitable_periods)
    max_profit_period = max(profitable_periods, key=lambda x: x['profit'])
    min_profit_period = min(profitable_periods, key=lambda x: x['profit'])
    
    print(f"\n💰 Profit Metrics:")
    print(f"   Average Profit: £{avg_profit:.2f}/MWh")
    print(f"   Total Potential Profit: £{total_profit:.2f}")
    print(f"   Best Period: {max_profit_period['date']!s} SP{max_profit_period['period']} → £{max_profit_period['profit']:.2f}/MWh profit")
    print(f"   Worst Profitable Period: £{min_profit_period['profit']:.2f}/MWh profit")
    
    # Breakdown by band
    red_profitable = [p for p in profitable_periods if p['band'] == 'RED']
    amber_profitable = [p for p in profitable_periods if p['band'] == 'AMBER']
    green_profitable = [p for p in profitable_periods if p['band'] == 'GREEN']
    
    print(f"\n📊 Profitable Periods by DUoS Band:")
    print(f"   RED (16:00-19:30):   {len(red_profitable):3d} periods ({len(red_profitable)/len(profitable_periods)*100:5.1f}%) - £{DUOS_RED:.2f}/MWh DUoS")
    print(f"   AMBER (08:00-16:00): {len(amber_profitable):3d} periods ({len(amber_profitable)/len(profitable_periods)*100:5.1f}%) - £{DUOS_AMBER:.2f}/MWh DUoS")
    print(f"   GREEN (Off-peak):    {len(green_profitable):3d} periods ({len(green_profitable)/len(profitable_periods)*100:5.1f}%) - £{DUOS_GREEN:.2f}/MWh DUoS")
    
    if red_profitable:
        avg_red = sum(p['profit'] for p in red_profitable) / len(red_profitable)
        print(f"      Avg RED profit: £{avg_red:.2f}/MWh")
    if amber_profitable:
        avg_amber = sum(p['profit'] for p in amber_profitable) / len(amber_profitable)
        print(f"      Avg AMBER profit: £{avg_amber:.2f}/MWh")
    if green_profitable:
        avg_green = sum(p['profit'] for p in green_profitable) / len(green_profitable)
        print(f"      Avg GREEN profit: £{avg_green:.2f}/MWh")

# Cost breakdown analysis
print(f"\n💷 Cost Structure Analysis:")
print(f"   PPA Contract Price: £{PPA_PRICE:.2f}/MWh")
print(f"   Fixed Costs: £{FIXED_COSTS:.2f}/MWh")
print(f"      • TNUoS: £{TNUOS:.2f}/MWh")
print(f"      • BSUoS: £{BSUOS:.2f}/MWh")
print(f"      • CCL:   £{CCL:.2f}/MWh")
print(f"      • RO:    £{RO:.2f}/MWh")
print(f"      • FiT:   £{FIT:.2f}/MWh")

avg_system_buy = sum(p['system_buy'] for p in all_periods) / len(all_periods)
avg_profitable_buy = sum(p['system_buy'] for p in profitable_periods) / len(profitable_periods) if profitable_periods else 0
avg_unprofitable_buy = sum(p['system_buy'] for p in all_periods if p['profit'] <= 0) / (len(all_periods) - len(profitable_periods)) if (len(all_periods) - len(profitable_periods)) > 0 else 0

print(f"\n📈 System Buy Price Analysis:")
print(f"   Average (all periods): £{avg_system_buy:.2f}/MWh")
print(f"   Average (profitable): £{avg_profitable_buy:.2f}/MWh")
print(f"   Average (unprofitable): £{avg_unprofitable_buy:.2f}/MWh")
print(f"   Break-even threshold: £{PPA_PRICE - FIXED_COSTS - DUOS_GREEN:.2f}/MWh (GREEN band)")
print(f"   Break-even threshold: £{PPA_PRICE - FIXED_COSTS - DUOS_AMBER:.2f}/MWh (AMBER band)")
print(f"   Break-even threshold: £{PPA_PRICE - FIXED_COSTS - DUOS_RED:.2f}/MWh (RED band)")

# Calculate daily average
if all_periods:
    dates = set(p['date'] for p in all_periods)
    avg_profitable_per_day = len(profitable_periods) / len(dates)
    avg_profit_per_day = total_profit / len(dates)
    print(f"\n📅 Daily Metrics:")
    print(f"   Total Days Analyzed: {len(dates)}")
    print(f"   Avg Profitable Periods/Day: {avg_profitable_per_day:.1f} of 48")
    print(f"   Avg Profit/Day: £{avg_profit_per_day:.2f}")
    print(f"   Expected Monthly Profit (30 days): £{avg_profit_per_day * 30:.2f}")

# Volume opportunity (assuming 1 MWh per period)
print(f"\n⚡ Volume Opportunity (assuming 1 MWh export per period):")
print(f"   Total MWh opportunity: {len(profitable_periods)} MWh")
print(f"   Total revenue potential: £{total_profit:.2f}")
print(f"   Best case scenario (100% dispatch): {len(profitable_periods)/len(all_periods)*100:.1f}% of total periods")

print("\n✅ Analysis complete")
