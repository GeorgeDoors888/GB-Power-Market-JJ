#!/usr/bin/env python3
"""
BtM PPA Revenue - Worked Example

This script demonstrates the revenue and cost calculations with realistic numbers.
Shows both current market conditions (unprofitable) and historical conditions (profitable).
"""

import pandas as pd
from datetime import datetime

print("=" * 80)
print("BtM PPA REVENUE CALCULATION - WORKED EXAMPLE")
print("=" * 80)

# ============================================================================
# CONFIGURATION
# ============================================================================

print("\n📋 CONFIGURATION")
print("-" * 80)

# Battery specs
BESS_CAPACITY_MWH = 5.0
BESS_POWER_MW = 2.5
BESS_EFFICIENCY = 0.85
MAX_CYCLES_PER_DAY = 4
SITE_DEMAND_MW = 2.5

print(f"Battery Capacity: {BESS_CAPACITY_MWH} MWh")
print(f"Battery Power: {BESS_POWER_MW} MW")
print(f"Round-trip Efficiency: {BESS_EFFICIENCY * 100}%")
print(f"Max Cycles/Day: {MAX_CYCLES_PER_DAY}")
print(f"Site Demand: {SITE_DEMAND_MW} MW (constant)")

# PPA contract
PPA_PRICE = 150.0  # £/MWh
print(f"\n💰 PPA Contract Price: £{PPA_PRICE}/MWh")

# Fixed levies (paid on import/charging)
TNUOS_RATE = 12.50
BSUOS_RATE = 4.50
CCL_RATE = 7.75
RO_RATE = 61.90
FIT_RATE = 11.50
TOTAL_LEVIES = TNUOS_RATE + BSUOS_RATE + CCL_RATE + RO_RATE + FIT_RATE

print(f"\n📊 Fixed Levies (paid on import):")
print(f"   TNUoS (Transmission): £{TNUOS_RATE}/MWh")
print(f"   BSUoS (Balancing): £{BSUOS_RATE}/MWh")
print(f"   CCL (Climate): £{CCL_RATE}/MWh")
print(f"   RO (Renewables): £{RO_RATE}/MWh")
print(f"   FiT (Feed-in Tariff): £{FIT_RATE}/MWh")
print(f"   TOTAL LEVIES: £{TOTAL_LEVIES}/MWh")

# DUoS rates (NGED West Midlands)
DUOS_RED = 17.64
DUOS_AMBER = 2.05
DUOS_GREEN = 0.11

print(f"\n🔴🟡🟢 DUoS Rates (NGED West Midlands):")
print(f"   RED:   £{DUOS_RED}/MWh")
print(f"   AMBER: £{DUOS_AMBER}/MWh")
print(f"   GREEN: £{DUOS_GREEN}/MWh")

# Annual hours by band
RED_HOURS = 910      # SP 33-39 weekdays
AMBER_HOURS = 1690   # SP 17-32, 40-44 weekdays
GREEN_HOURS = 6160   # All other times

print(f"\n⏰ Annual Hours by Band:")
print(f"   RED:   {RED_HOURS:,} hours/year (16:00-19:30 weekdays)")
print(f"   AMBER: {AMBER_HOURS:,} hours/year (08:00-16:00, 19:30-22:00 weekdays)")
print(f"   GREEN: {GREEN_HOURS:,} hours/year (nights + weekends)")

# ============================================================================
# SCENARIO 1: CURRENT MARKET (DEC 2025) - UNPROFITABLE
# ============================================================================

print("\n" + "=" * 80)
print("SCENARIO 1: CURRENT MARKET CONDITIONS (Dec 2025)")
print("=" * 80)

# Current system buy prices from BigQuery (last 180 days)
current_prices = {
    'green': 65.83,
    'amber': 73.91,
    'red': 92.93
}

print(f"\n💵 System Buy Prices (actual from BigQuery):")
print(f"   GREEN: £{current_prices['green']:.2f}/MWh")
print(f"   AMBER: £{current_prices['amber']:.2f}/MWh")
print(f"   RED:   £{current_prices['red']:.2f}/MWh")

# Calculate total import costs
current_costs = {
    'green': current_prices['green'] + DUOS_GREEN + TOTAL_LEVIES,
    'amber': current_prices['amber'] + DUOS_AMBER + TOTAL_LEVIES,
    'red': current_prices['red'] + DUOS_RED + TOTAL_LEVIES
}

print(f"\n📊 Total Import Costs (System Buy + DUoS + Levies):")
print(f"   GREEN: £{current_prices['green']:.2f} + £{DUOS_GREEN:.2f} + £{TOTAL_LEVIES:.2f} = £{current_costs['green']:.2f}/MWh")
print(f"   AMBER: £{current_prices['amber']:.2f} + £{DUOS_AMBER:.2f} + £{TOTAL_LEVIES:.2f} = £{current_costs['amber']:.2f}/MWh")
print(f"   RED:   £{current_prices['red']:.2f} + £{DUOS_RED:.2f} + £{TOTAL_LEVIES:.2f} = £{current_costs['red']:.2f}/MWh")

print(f"\n❌ PROBLEM: All costs exceed PPA price of £{PPA_PRICE}/MWh")
print(f"   GREEN loss: £{current_costs['green'] - PPA_PRICE:.2f}/MWh")
print(f"   AMBER loss: £{current_costs['amber'] - PPA_PRICE:.2f}/MWh")
print(f"   RED loss:   £{current_costs['red'] - PPA_PRICE:.2f}/MWh")

print(f"\n🔋 Battery Decision: DO NOT CHARGE (all periods unprofitable)")
print(f"   Charged: 0 MWh")
print(f"   Discharged: 0 MWh")
print(f"   Cycles: 0")
print(f"   BtM PPA Profit: £0")

# ============================================================================
# SCENARIO 2: HISTORICAL MARKET (2023) - PROFITABLE
# ============================================================================

print("\n" + "=" * 80)
print("SCENARIO 2: HISTORICAL CONDITIONS (2023) - PROFITABLE")
print("=" * 80)

# Historical system buy prices (typical 2023 values)
historical_prices = {
    'green': 30.0,
    'amber': 45.0,
    'red': 75.0
}

print(f"\n💵 System Buy Prices (historical 2023):")
print(f"   GREEN: £{historical_prices['green']:.2f}/MWh")
print(f"   AMBER: £{historical_prices['amber']:.2f}/MWh")
print(f"   RED:   £{historical_prices['red']:.2f}/MWh")

# Calculate total import costs
historical_costs = {
    'green': historical_prices['green'] + DUOS_GREEN + TOTAL_LEVIES,
    'amber': historical_prices['amber'] + DUOS_AMBER + TOTAL_LEVIES,
    'red': historical_prices['red'] + DUOS_RED + TOTAL_LEVIES
}

print(f"\n📊 Total Import Costs:")
print(f"   GREEN: £{historical_prices['green']:.2f} + £{DUOS_GREEN:.2f} + £{TOTAL_LEVIES:.2f} = £{historical_costs['green']:.2f}/MWh ✅ Profitable!")
print(f"   AMBER: £{historical_prices['amber']:.2f} + £{DUOS_AMBER:.2f} + £{TOTAL_LEVIES:.2f} = £{historical_costs['amber']:.2f}/MWh ⚠️  Marginal")
print(f"   RED:   £{historical_prices['red']:.2f} + £{DUOS_RED:.2f} + £{TOTAL_LEVIES:.2f} = £{historical_costs['red']:.2f}/MWh ❌ Loss")

# Charging threshold (PPA - margin)
CHARGING_THRESHOLD = 120.0  # £/MWh

print(f"\n🔋 Battery Charging Strategy:")
print(f"   Charging Threshold: £{CHARGING_THRESHOLD}/MWh (PPA price - £30 margin)")

can_charge_green = historical_costs['green'] < CHARGING_THRESHOLD
can_charge_amber = historical_costs['amber'] < CHARGING_THRESHOLD

print(f"   Can charge GREEN? {'✅ YES' if can_charge_green else '❌ NO'} (£{historical_costs['green']:.2f} vs £{CHARGING_THRESHOLD})")
print(f"   Can charge AMBER? {'✅ YES' if can_charge_amber else '❌ NO'} (£{historical_costs['amber']:.2f} vs £{CHARGING_THRESHOLD})")
print(f"   Can charge RED?   ❌ NO (never profitable)")

# Calculate charging volumes
max_charge_mwh_year = MAX_CYCLES_PER_DAY * 365.25 * BESS_CAPACITY_MWH

if can_charge_green:
    green_available = GREEN_HOURS * BESS_POWER_MW
    green_charge_mwh = min(green_available, max_charge_mwh_year)
    remaining_capacity = max_charge_mwh_year - green_charge_mwh
else:
    green_charge_mwh = 0
    remaining_capacity = max_charge_mwh_year

if can_charge_amber and remaining_capacity > 0:
    amber_available = AMBER_HOURS * BESS_POWER_MW
    amber_charge_mwh = min(amber_available, remaining_capacity)
else:
    amber_charge_mwh = 0

red_charge_mwh = 0  # Never charge during RED

total_charged = green_charge_mwh + amber_charge_mwh + red_charge_mwh
total_discharged = total_charged * BESS_EFFICIENCY
cycles = total_charged / BESS_CAPACITY_MWH if BESS_CAPACITY_MWH > 0 else 0

print(f"\n📈 CHARGING BREAKDOWN:")
print(f"   GREEN: {green_charge_mwh:,.0f} MWh @ £{historical_costs['green']:.2f}/MWh = £{green_charge_mwh * historical_costs['green']:,.0f}")
print(f"   AMBER: {amber_charge_mwh:,.0f} MWh @ £{historical_costs['amber']:.2f}/MWh = £{amber_charge_mwh * historical_costs['amber']:,.0f}")
print(f"   RED:   {red_charge_mwh:,.0f} MWh (never charge)")
print(f"   ---")
print(f"   TOTAL CHARGED: {total_charged:,.0f} MWh")
print(f"   CHARGING COST: £{(green_charge_mwh * historical_costs['green'] + amber_charge_mwh * historical_costs['amber']):,.0f}")
print(f"   Battery Cycles: {cycles:.1f} cycles/year")

print(f"\n⚡ AFTER 85% EFFICIENCY:")
print(f"   Available for discharge: {total_discharged:,.0f} MWh")

# Calculate discharge strategy (RED first, then AMBER)
red_demand = RED_HOURS * SITE_DEMAND_MW
amber_demand = AMBER_HOURS * SITE_DEMAND_MW
green_demand = GREEN_HOURS * SITE_DEMAND_MW

if total_discharged >= red_demand:
    battery_red = red_demand
    battery_amber = min(amber_demand, total_discharged - battery_red)
else:
    battery_red = total_discharged
    battery_amber = 0

battery_green = 0  # Never discharge during green (direct import is profitable)

print(f"\n📉 DISCHARGE STRATEGY (Priority: RED > AMBER > GREEN):")
print(f"   Site demand RED:   {red_demand:,.0f} MWh/year")
print(f"   Battery serves RED: {battery_red:,.0f} MWh ({battery_red/red_demand*100:.1f}% coverage)")
print(f"   Site demand AMBER: {amber_demand:,.0f} MWh/year")
print(f"   Battery serves AMBER: {battery_amber:,.0f} MWh")
print(f"   Site demand GREEN: {green_demand:,.0f} MWh/year")
print(f"   Battery serves GREEN: {battery_green:,.0f} MWh (direct import cheaper)")

# STREAM 2: Battery + VLP Revenue
VLP_AVG_UPLIFT = 12.0  # £/MWh
VLP_PARTICIPATION = 0.20

total_battery_discharge = battery_red + battery_amber
ppa_revenue_s2 = total_battery_discharge * PPA_PRICE
vlp_revenue = total_battery_discharge * VLP_PARTICIPATION * VLP_AVG_UPLIFT
charging_cost = green_charge_mwh * historical_costs['green'] + amber_charge_mwh * historical_costs['amber']

stream2_profit = ppa_revenue_s2 + vlp_revenue - charging_cost

print(f"\n💰 STREAM 2: Battery + VLP Revenue")
print(f"   Discharge volume: {total_battery_discharge:,.0f} MWh")
print(f"   PPA revenue: {total_battery_discharge:,.0f} × £{PPA_PRICE} = £{ppa_revenue_s2:,.0f}")
print(f"   VLP revenue: {total_battery_discharge:,.0f} × {VLP_PARTICIPATION:.0%} × £{VLP_AVG_UPLIFT} = £{vlp_revenue:,.0f}")
print(f"   Total revenue: £{ppa_revenue_s2 + vlp_revenue:,.0f}")
print(f"   Charging cost: £{charging_cost:,.0f}")
print(f"   ---")
print(f"   STREAM 2 PROFIT: £{stream2_profit:,.0f}")

# STREAM 1: Direct Import (remaining demand)
stream1_red = 0  # RED never profitable (£{historical_costs['red']:.2f} > £150)
stream1_amber = amber_demand - battery_amber if historical_costs['amber'] < PPA_PRICE else 0
stream1_green = green_demand if historical_costs['green'] < PPA_PRICE else 0

stream1_green_revenue = stream1_green * PPA_PRICE
stream1_green_cost = stream1_green * historical_costs['green']
stream1_green_profit = stream1_green_revenue - stream1_green_cost

stream1_amber_revenue = stream1_amber * PPA_PRICE
stream1_amber_cost = stream1_amber * historical_costs['amber']
stream1_amber_profit = stream1_amber_revenue - stream1_amber_cost

stream1_profit = stream1_green_profit + stream1_amber_profit

print(f"\n💰 STREAM 1: Direct Import (remaining demand)")
print(f"   GREEN: {stream1_green:,.0f} MWh")
print(f"     Revenue: £{stream1_green_revenue:,.0f}")
print(f"     Cost: £{stream1_green_cost:,.0f}")
print(f"     Profit: £{stream1_green_profit:,.0f}")
print(f"   AMBER: {stream1_amber:,.0f} MWh")
print(f"     Revenue: £{stream1_amber_revenue:,.0f}")
print(f"     Cost: £{stream1_amber_cost:,.0f}")
print(f"     Profit: £{stream1_amber_profit:,.0f}")
print(f"   RED: {stream1_red:,.0f} MWh (not imported - too expensive)")
print(f"   ---")
print(f"   STREAM 1 PROFIT: £{stream1_profit:,.0f}")

# Total BtM PPA profit
btm_ppa_profit = stream1_profit + stream2_profit
dc_revenue = 195458
total_profit = btm_ppa_profit + dc_revenue

print(f"\n" + "=" * 80)
print(f"💷 TOTAL ANNUAL PROFIT")
print(f"=" * 80)
print(f"   Stream 1 (Direct Import): £{stream1_profit:,.0f}")
print(f"   Stream 2 (Battery + VLP):  £{stream2_profit:,.0f}")
print(f"   BtM PPA Subtotal:          £{btm_ppa_profit:,.0f}")
print(f"   Dynamic Containment:       £{dc_revenue:,.0f}")
print(f"   ---")
print(f"   TOTAL PROFIT:              £{total_profit:,.0f}")

# ============================================================================
# KEY INSIGHTS
# ============================================================================

print(f"\n" + "=" * 80)
print(f"🔑 KEY INSIGHTS")
print(f"=" * 80)

print(f"\n1. Battery Value comes from AVOIDING RED LOSSES:")
print(f"   - RED import cost: £{historical_costs['red']:.2f}/MWh")
print(f"   - PPA revenue: £{PPA_PRICE}/MWh")
print(f"   - Loss per MWh: £{historical_costs['red'] - PPA_PRICE:.2f}")
print(f"   - Annual RED demand: {red_demand:,.0f} MWh")
print(f"   - Without battery loss: £{(historical_costs['red'] - PPA_PRICE) * red_demand:,.0f}")
print(f"   - Battery avoids: £{(historical_costs['red'] - PPA_PRICE) * battery_red:,.0f}")

print(f"\n2. Arbitrage Profit is SMALL:")
print(f"   - Charge GREEN @ £{historical_costs['green']:.2f}/MWh")
print(f"   - Discharge for £{PPA_PRICE}/MWh + £{VLP_AVG_UPLIFT * VLP_PARTICIPATION:.2f} VLP")
print(f"   - Gross margin: £{PPA_PRICE + VLP_AVG_UPLIFT * VLP_PARTICIPATION - historical_costs['green']:.2f}/MWh")
print(f"   - After 15% losses: £{(PPA_PRICE + VLP_AVG_UPLIFT * VLP_PARTICIPATION - historical_costs['green']) * BESS_EFFICIENCY:.2f}/MWh")

print(f"\n3. Fixed Levies are EXPENSIVE:")
print(f"   - Levies: £{TOTAL_LEVIES}/MWh (66% of total GREEN cost)")
print(f"   - Paid on ALL imports (charging + direct)")
print(f"   - Annual levy cost: £{(green_charge_mwh + stream1_green) * TOTAL_LEVIES:,.0f}")

print(f"\n4. Current Market vs Historical:")
print(f"   - 2023 GREEN: £{historical_prices['green']:.2f}/MWh → Total £{historical_costs['green']:.2f} ✅ Profitable")
print(f"   - 2025 GREEN: £{current_prices['green']:.2f}/MWh → Total £{current_costs['green']:.2f} ❌ Unprofitable")
print(f"   - System prices doubled, making BtM PPA unviable")

print(f"\n5. Break-even Analysis:")
print(f"   - Need GREEN < £{CHARGING_THRESHOLD - DUOS_GREEN - TOTAL_LEVIES:.2f}/MWh to charge profitably")
print(f"   - Currently: £{current_prices['green']:.2f}/MWh (£{current_prices['green'] - (CHARGING_THRESHOLD - DUOS_GREEN - TOTAL_LEVIES):.2f}/MWh over threshold)")

# ============================================================================
# SCENARIO 3: OPTIMAL CONDITIONS - MAXIMUM PROFITABILITY
# ============================================================================

print("\n" + "=" * 80)
print("SCENARIO 3: OPTIMAL CONDITIONS (Low System Prices)")
print("=" * 80)

# Optimal system buy prices (e.g., high wind periods in 2022)
optimal_prices = {
    'green': 15.0,   # Very low overnight prices
    'amber': 35.0,
    'red': 65.0
}

print(f"\n💵 System Buy Prices (optimal conditions):")
print(f"   GREEN: £{optimal_prices['green']:.2f}/MWh (overnight high wind)")
print(f"   AMBER: £{optimal_prices['amber']:.2f}/MWh")
print(f"   RED:   £{optimal_prices['red']:.2f}/MWh")

# Calculate total import costs
optimal_costs = {
    'green': optimal_prices['green'] + DUOS_GREEN + TOTAL_LEVIES,
    'amber': optimal_prices['amber'] + DUOS_AMBER + TOTAL_LEVIES,
    'red': optimal_prices['red'] + DUOS_RED + TOTAL_LEVIES
}

print(f"\n📊 Total Import Costs:")
print(f"   GREEN: £{optimal_prices['green']:.2f} + £{DUOS_GREEN:.2f} + £{TOTAL_LEVIES:.2f} = £{optimal_costs['green']:.2f}/MWh ✅ PROFITABLE!")
print(f"   AMBER: £{optimal_prices['amber']:.2f} + £{DUOS_AMBER:.2f} + £{TOTAL_LEVIES:.2f} = £{optimal_costs['amber']:.2f}/MWh ✅ PROFITABLE!")
print(f"   RED:   £{optimal_prices['red']:.2f} + £{DUOS_RED:.2f} + £{TOTAL_LEVIES:.2f} = £{optimal_costs['red']:.2f}/MWh ❌ Loss")

print(f"\n🔋 Battery Charging Strategy:")
print(f"   Charging Threshold: £{CHARGING_THRESHOLD}/MWh")

can_charge_green_opt = optimal_costs['green'] < CHARGING_THRESHOLD
can_charge_amber_opt = optimal_costs['amber'] < CHARGING_THRESHOLD

print(f"   Can charge GREEN? {'✅ YES' if can_charge_green_opt else '❌ NO'} (£{optimal_costs['green']:.2f} vs £{CHARGING_THRESHOLD})")
print(f"   Can charge AMBER? {'✅ YES' if can_charge_amber_opt else '❌ NO'} (£{optimal_costs['amber']:.2f} vs £{CHARGING_THRESHOLD})")
print(f"   Can charge RED?   ❌ NO (never profitable)")

# Calculate charging volumes
if can_charge_green_opt:
    green_available_opt = GREEN_HOURS * BESS_POWER_MW
    green_charge_opt = min(green_available_opt, max_charge_mwh_year)
    remaining_opt = max_charge_mwh_year - green_charge_opt
else:
    green_charge_opt = 0
    remaining_opt = max_charge_mwh_year

if can_charge_amber_opt and remaining_opt > 0:
    amber_available_opt = AMBER_HOURS * BESS_POWER_MW
    amber_charge_opt = min(amber_available_opt, remaining_opt)
else:
    amber_charge_opt = 0

red_charge_opt = 0

total_charged_opt = green_charge_opt + amber_charge_opt
total_discharged_opt = total_charged_opt * BESS_EFFICIENCY
cycles_opt = total_charged_opt / BESS_CAPACITY_MWH

green_charging_cost_opt = green_charge_opt * optimal_costs['green']
amber_charging_cost_opt = amber_charge_opt * optimal_costs['amber']
total_charging_cost_opt = green_charging_cost_opt + amber_charging_cost_opt

print(f"\n📈 CHARGING BREAKDOWN:")
print(f"   GREEN: {green_charge_opt:,.0f} MWh @ £{optimal_costs['green']:.2f}/MWh = £{green_charging_cost_opt:,.0f}")
print(f"   AMBER: {amber_charge_opt:,.0f} MWh @ £{optimal_costs['amber']:.2f}/MWh = £{amber_charging_cost_opt:,.0f}")
print(f"   RED:   {red_charge_opt:,.0f} MWh (never charge)")
print(f"   ---")
print(f"   TOTAL CHARGED: {total_charged_opt:,.0f} MWh")
print(f"   CHARGING COST: £{total_charging_cost_opt:,.0f}")
print(f"   Battery Cycles: {cycles_opt:.1f} cycles/year")
print(f"   Average charging cost: £{total_charging_cost_opt/total_charged_opt if total_charged_opt > 0 else 0:.2f}/MWh")

print(f"\n⚡ AFTER 85% EFFICIENCY:")
print(f"   Available for discharge: {total_discharged_opt:,.0f} MWh")

# Discharge strategy
if total_discharged_opt >= red_demand:
    battery_red_opt = red_demand
    battery_amber_opt = min(amber_demand, total_discharged_opt - battery_red_opt)
else:
    battery_red_opt = total_discharged_opt
    battery_amber_opt = 0

battery_green_opt = 0
total_battery_discharge_opt = battery_red_opt + battery_amber_opt

print(f"\n📉 DISCHARGE STRATEGY:")
print(f"   RED demand: {red_demand:,.0f} MWh")
print(f"   Battery serves RED: {battery_red_opt:,.0f} MWh ({battery_red_opt/red_demand*100:.1f}% coverage) ✅")
print(f"   AMBER demand: {amber_demand:,.0f} MWh")
print(f"   Battery serves AMBER: {battery_amber_opt:,.0f} MWh ({battery_amber_opt/amber_demand*100:.1f}% coverage)")

# STREAM 2
ppa_revenue_s2_opt = total_battery_discharge_opt * PPA_PRICE
vlp_revenue_opt = total_battery_discharge_opt * VLP_PARTICIPATION * VLP_AVG_UPLIFT
stream2_revenue_opt = ppa_revenue_s2_opt + vlp_revenue_opt
stream2_profit_opt = stream2_revenue_opt - total_charging_cost_opt

print(f"\n💰 STREAM 2: Battery + VLP Revenue")
print(f"   Discharge volume: {total_battery_discharge_opt:,.0f} MWh")
print(f"   PPA revenue: {total_battery_discharge_opt:,.0f} × £{PPA_PRICE} = £{ppa_revenue_s2_opt:,.0f}")
print(f"   VLP revenue: {total_battery_discharge_opt:,.0f} × {VLP_PARTICIPATION:.0%} × £{VLP_AVG_UPLIFT} = £{vlp_revenue_opt:,.0f}")
print(f"   Total revenue: £{stream2_revenue_opt:,.0f}")
print(f"   Charging cost: £{total_charging_cost_opt:,.0f}")
print(f"   ---")
print(f"   STREAM 2 PROFIT: £{stream2_profit_opt:,.0f}")
print(f"   Margin: {stream2_profit_opt/stream2_revenue_opt*100 if stream2_revenue_opt > 0 else 0:.1f}%")

# STREAM 1
stream1_red_opt = 0  # RED never profitable
stream1_amber_opt = amber_demand - battery_amber_opt if optimal_costs['amber'] < PPA_PRICE else 0
stream1_green_opt = green_demand if optimal_costs['green'] < PPA_PRICE else 0

stream1_green_revenue_opt = stream1_green_opt * PPA_PRICE
stream1_green_cost_opt = stream1_green_opt * optimal_costs['green']
stream1_green_profit_opt = stream1_green_revenue_opt - stream1_green_cost_opt

stream1_amber_revenue_opt = stream1_amber_opt * PPA_PRICE
stream1_amber_cost_opt = stream1_amber_opt * optimal_costs['amber']
stream1_amber_profit_opt = stream1_amber_revenue_opt - stream1_amber_cost_opt

stream1_profit_opt = stream1_green_profit_opt + stream1_amber_profit_opt

print(f"\n💰 STREAM 1: Direct Import (remaining demand)")
print(f"   GREEN: {stream1_green_opt:,.0f} MWh")
print(f"     Revenue: £{stream1_green_revenue_opt:,.0f}")
print(f"     Cost: £{stream1_green_cost_opt:,.0f}")
print(f"     Profit: £{stream1_green_profit_opt:,.0f}")
print(f"   AMBER: {stream1_amber_opt:,.0f} MWh")
print(f"     Revenue: £{stream1_amber_revenue_opt:,.0f}")
print(f"     Cost: £{stream1_amber_cost_opt:,.0f}")
print(f"     Profit: £{stream1_amber_profit_opt:,.0f}")
print(f"   RED: {stream1_red_opt:,.0f} MWh (not imported)")
print(f"   ---")
print(f"   STREAM 1 PROFIT: £{stream1_profit_opt:,.0f}")

# Total
btm_ppa_profit_opt = stream1_profit_opt + stream2_profit_opt
total_profit_opt = btm_ppa_profit_opt + dc_revenue

print(f"\n" + "=" * 80)
print(f"💷 TOTAL ANNUAL PROFIT (OPTIMAL CONDITIONS)")
print(f"=" * 80)
print(f"   Stream 1 (Direct Import): £{stream1_profit_opt:,.0f}")
print(f"   Stream 2 (Battery + VLP):  £{stream2_profit_opt:,.0f}")
print(f"   BtM PPA Subtotal:          £{btm_ppa_profit_opt:,.0f}")
print(f"   Dynamic Containment:       £{dc_revenue:,.0f}")
print(f"   ---")
print(f"   TOTAL PROFIT:              £{total_profit_opt:,.0f}")

# RED loss avoidance
red_loss_without_battery = (optimal_costs['red'] - PPA_PRICE) * red_demand
red_loss_with_battery = (optimal_costs['red'] - PPA_PRICE) * (red_demand - battery_red_opt)
red_savings = red_loss_without_battery - red_loss_with_battery

print(f"\n🎯 BATTERY VALUE PROPOSITION:")
print(f"   RED loss without battery: £{abs(red_loss_without_battery):,.0f}")
print(f"   RED loss with battery: £{abs(red_loss_with_battery):,.0f}")
print(f"   SAVINGS FROM BATTERY: £{abs(red_savings):,.0f}")
print(f"   Battery effectively SAVES £{abs(red_savings)/battery_red_opt:.2f}/MWh discharged")

print(f"\n📊 COMPARISON: No Battery vs With Battery:")
print(f"   Without Battery BtM PPA: £{stream1_profit_opt + stream1_green_profit_opt:,.0f} (all direct import)")
print(f"   With Battery BtM PPA: £{btm_ppa_profit_opt:,.0f}")
print(f"   Battery Contribution: £{btm_ppa_profit_opt - (stream1_profit_opt + stream1_green_profit_opt):,.0f}")

print(f"\n" + "=" * 80)
print(f"END OF WORKED EXAMPLE")
print(f"=" * 80)
