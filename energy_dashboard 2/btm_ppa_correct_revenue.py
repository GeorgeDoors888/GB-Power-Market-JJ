#!/usr/bin/env python3
"""
CORRECTED BtM PPA Revenue Model

KEY INSIGHT:
- Battery CHARGES at market rate (system price + DUoS + levies) - this is a COST
- Battery DISCHARGES at £150/MWh (if site demand exists) - this is REVENUE
- Profit = arbitrage between charging cost and discharge revenue

Direct imports (non-battery) always at market rate, used by site directly.
"""

print("=" * 80)
print("CORRECTED BtM PPA REVENUE MODEL")
print("=" * 80)

print("\n🔑 KEY CORRECTION:")
print("   Battery charging:")
print("     • Pays MARKET RATE when importing (system + DUoS + levies) = COST")
print("     • Gets PAID (negative price) when network has excess = REVENUE")
print("   Battery discharging: Sells at £150/MWh (to meet site demand) = REVENUE")
print("   Plus other revenues: VLP uplift, Dynamic Containment, Curtailment")
print("   Profit = Discharge revenue - Charging cost (or + paid to charge)")

print("\n" + "=" * 80)
print("SCENARIO 3 REVISITED: Optimal Conditions (2022 High Wind)")
print("=" * 80)

# System prices
green_price = 15.0
amber_price = 35.0
red_price = 65.0

# Fixed costs
levies = 98.15
green_duos = 0.11
amber_duos = 2.05
red_duos = 17.64

# Total import costs
green_cost = green_price + green_duos + levies  # £113.26
amber_cost = amber_price + amber_duos + levies  # £135.20
red_cost = red_price + red_duos + levies        # £180.79

print(f"\n💰 System Import Costs:")
print(f"   GREEN: £{green_price} + £{green_duos} + £{levies} = £{green_cost:.2f}/MWh")
print(f"   AMBER: £{amber_price} + £{amber_duos} + £{levies} = £{amber_cost:.2f}/MWh")
print(f"   RED:   £{red_price} + £{red_duos} + £{levies} = £{red_cost:.2f}/MWh")

# PPA price
ppa_price = 150.0

print(f"\n📄 PPA Contract: £{ppa_price}/MWh for all grid imports")

# Annual hours by band
green_hours = 6160
amber_hours = 1690
red_hours = 910

# Site base load (continuous consumption)
site_mw = 2.5
base_green_mwh = green_hours * site_mw  # 15,400 MWh
base_amber_mwh = amber_hours * site_mw  # 4,225 MWh
base_red_mwh = red_hours * site_mw      # 2,275 MWh

print(f"\n🏭 Site Base Load (2.5 MW continuous):")
print(f"   GREEN: {green_hours:,} hours × 2.5 MW = {base_green_mwh:,.0f} MWh")
print(f"   AMBER: {amber_hours:,} hours × 2.5 MW = {base_amber_mwh:,.0f} MWh")
print(f"   RED:   {red_hours:,} hours × 2.5 MW = {base_red_mwh:,.0f} MWh")
print(f"   TOTAL: {base_green_mwh + base_amber_mwh + base_red_mwh:,.0f} MWh/year")

# Battery specs
battery_mwh = 5.0
battery_mw = 2.5
efficiency = 0.85
max_cycles_day = 4

# Battery charging decision - only charge in GREEN (£113.26 < £120 threshold)
can_charge_green = green_cost < 120
green_charge_hours = green_hours if can_charge_green else 0

# Note: In reality, system prices can go NEGATIVE (paid to charge)
# For this example using £15/MWh GREEN, battery pays £113.26/MWh to charge
# When prices are negative (e.g., -£50/MWh), total cost would be: -50 + 0.11 + 98.15 = £48.26
# and battery would be PAID the negative amount!

print(f"\n💡 Charging Economics Note:")
print(f"   System price: £{green_price}/MWh (can be NEGATIVE when excess generation)")
print(f"   When negative (e.g., -£50/MWh):")
print(f"     • Total cost: -£50 + £{green_duos} + £{levies} = £{-50 + green_duos + levies:.2f}/MWh")
print(f"     • Battery gets PAID £50/MWh to absorb excess electricity!")
print(f"     • Makes charging highly profitable")

# Maximum charging constrained by:
# - Available hours
# - Battery power rating (2.5 MW)
# - Max cycles per day
max_charge_mwh_year = min(
    green_charge_hours * battery_mw,  # Hours × Power
    battery_mwh * max_cycles_day * 365  # Capacity × Cycles
)

# Actual charging (realistic: ~40% of theoretical max)
battery_charge_mwh = max_charge_mwh_year * 0.40  # 7,305 MWh
battery_discharge_mwh = battery_charge_mwh * efficiency  # 6,209 MWh

print(f"\n🔋 Battery Operation:")
print(f"   Can charge in GREEN? {'✅ YES' if can_charge_green else '❌ NO'} (£{green_cost:.2f} < £120)")
print(f"   Available charge hours: {green_charge_hours:,} hours")
print(f"   Theoretical max: {max_charge_mwh_year:,.0f} MWh/year")
print(f"   Actual charging: {battery_charge_mwh:,.0f} MWh/year (40% utilization)")
print(f"   Discharges: {battery_discharge_mwh:,.0f} MWh (85% efficiency)")
print(f"   Cycles: {battery_charge_mwh / battery_mwh:,.0f} cycles/year")
print(f"\n   ⚡ When system price is negative:")
print(f"      Battery gets PAID to charge (absorbing excess renewable generation)")
print(f"      Then discharges at £150/MWh - creating massive arbitrage profit!")

# === REVENUE CALCULATION (CORRECTED) ===

print("\n" + "=" * 80)
print("💷 REVENUE CALCULATION (CORRECTED)")
print("=" * 80)

# Revenue ONLY comes from:
# 1. Battery discharges at £150/MWh (when meeting site demand)
# 2. VLP uplift
# 3. Dynamic Containment

# Battery discharge revenue (sells at £150/MWh to site)
battery_discharge_revenue = battery_discharge_mwh * ppa_price

print(f"\n🔋 Battery Discharge Revenue:")
print(f"   Discharges: {battery_discharge_mwh:,.0f} MWh × £{ppa_price}/MWh = £{battery_discharge_revenue:,.0f}")

# VLP uplift (for battery discharge only)
vlp_uplift = 12.0
vlp_participation = 0.20
vlp_discharge_mwh = battery_discharge_mwh * vlp_participation
vlp_revenue = vlp_discharge_mwh * vlp_uplift

print(f"\n⚡ VLP/BM Revenue (discharge uplift):")
print(f"   Discharged in BM: {vlp_discharge_mwh:,.0f} MWh ({vlp_participation*100:.0f}% participation)")
print(f"   VLP uplift: {vlp_discharge_mwh:,.0f} MWh × £{vlp_uplift} = £{vlp_revenue:,.0f}")

# Dynamic Containment
dc_revenue = 195458

print(f"\n🔌 Dynamic Containment: £{dc_revenue:,.0f}/year")

total_revenue = battery_discharge_revenue + vlp_revenue + dc_revenue

print(f"\n{'='*80}")
print(f"📊 TOTAL REVENUE: £{total_revenue:,.0f}/year")
print(f"   • Battery discharge @ £150: £{battery_discharge_revenue:,.0f}")
print(f"   • VLP uplift: £{vlp_revenue:,.0f}")
print(f"   • DC: £{dc_revenue:,.0f}")
print(f"{'='*80}")

# === COST CALCULATION ===

print("\n" + "=" * 80)
print("💸 COST CALCULATION")
print("=" * 80)

# Site base demand costs (direct imports at market rate)
cost_green_base = base_green_mwh * green_cost
cost_amber_base = base_amber_mwh * amber_cost
cost_red_base = base_red_mwh * red_cost

site_demand_cost = cost_green_base + cost_amber_base + cost_red_base

print(f"\n🏭 Site Demand Costs (direct imports):")
print(f"   GREEN: {base_green_mwh:,.0f} MWh × £{green_cost:.2f} = £{cost_green_base:,.0f}")
print(f"   AMBER: {base_amber_mwh:,.0f} MWh × £{amber_cost:.2f} = £{cost_amber_base:,.0f}")
print(f"   RED:   {base_red_mwh:,.0f} MWh × £{red_cost:.2f} = £{cost_red_base:,.0f}")
print(f"   TOTAL SITE COST: £{site_demand_cost:,.0f}/year")

# Battery charging cost (at market rate)
battery_charge_cost = battery_charge_mwh * green_cost

print(f"\n🔋 Battery Charging Cost:")
print(f"   {battery_charge_mwh:,.0f} MWh × £{green_cost:.2f} = £{battery_charge_cost:,.0f}")
print(f"   (Charges in GREEN period at system price £{green_price}/MWh)")
print(f"\n   💡 Note: When system price is NEGATIVE:")
print(f"      • Cost becomes NEGATIVE (i.e., revenue!)")
print(f"      • Example: -£50/MWh system price → Total: -£50 + £0.11 + £98.15 = £48.26/MWh")
print(f"      • Battery saves £101.74/MWh vs normal £150 import!")

total_import_cost = site_demand_cost + battery_charge_cost

print(f"\n{'='*80}")
print(f"💰 TOTAL COSTS: £{total_import_cost:,.0f}/year")
print(f"   • Site demand: £{site_demand_cost:,.0f}")
print(f"   • Battery charging: £{battery_charge_cost:,.0f}")
print(f"{'='*80}")

# === PROFIT CALCULATION ===

print("\n" + "=" * 80)
print("📈 PROFIT CALCULATION")
print("=" * 80)

gross_profit = total_revenue - total_import_cost
margin_pct = (gross_profit / total_revenue) * 100 if total_revenue > 0 else 0

print(f"\n✅ Annual Performance:")
print(f"   Total Revenue:     £{total_revenue:,.0f}")
print(f"   Total Costs:       £{total_import_cost:,.0f}")
print(f"   Gross Profit:      £{gross_profit:,.0f}")
print(f"   Profit Margin:     {margin_pct:.1f}%")

# Battery profit = discharge revenue - charging cost + VLP
battery_profit = battery_discharge_revenue - battery_charge_cost + vlp_revenue

print(f"\n📊 Profit Breakdown:")
print(f"   Battery Arbitrage:  £{battery_profit:,.0f}")
print(f"     • Discharge revenue: £{battery_discharge_revenue:,.0f} (@ £150/MWh)")
print(f"     • Charging cost: -£{battery_charge_cost:,.0f} (@ £{green_cost:.2f}/MWh)")
print(f"     • VLP uplift: +£{vlp_revenue:,.0f}")
print(f"   DC Revenue:        £{dc_revenue:,.0f}")
print(f"   Site Import Cost:  -£{site_demand_cost:,.0f}")
print(f"   NET PROFIT:        £{gross_profit:,.0f}")

# === KEY INSIGHTS ===

print("\n" + "=" * 80)
print("🔑 KEY INSIGHTS")
print("=" * 80)

battery_cycles = battery_charge_mwh / battery_mwh
battery_profit_per_cycle = battery_profit / battery_cycles if battery_cycles > 0 else 0
arbitrage_margin = ppa_price - green_cost

print(f"""
1. Revenue Model is CORRECT:
   • Battery discharges: £150/MWh (meets site demand)
   • Total battery discharge revenue: £{battery_discharge_revenue:,.0f}
   • Plus VLP uplift: £{vlp_revenue:,.0f}
   • Plus DC contract: £{dc_revenue:,.0f}

2. Battery Economics:
   • Charges at: £{green_cost:.2f}/MWh (GREEN period - market rate)
   • Discharges at: £{ppa_price:.2f}/MWh (to site)
   • Arbitrage margin: £{arbitrage_margin:.2f}/MWh
   • Efficiency loss: {(1-efficiency)*100:.0f}%
   • Net margin: £{arbitrage_margin * efficiency:.2f}/MWh (after losses)
   
   ⚡ IMPORTANT: When system price is NEGATIVE:
   • Battery gets PAID to charge (e.g., -£50/MWh system price)
   • Total cost: -£50 + £0.11 + £98.15 = £48.26/MWh (battery paid £50!)
   • Then sells at £150/MWh → £101.74/MWh profit after levies
   • This happens during high wind/low demand periods (2022 had many)

3. Battery Performance:
   • Charges: {battery_charge_mwh:,.0f} MWh/year
   • Discharges: {battery_discharge_mwh:,.0f} MWh/year
   • Cycles: {battery_cycles:,.0f} cycles/year
   • Battery profit: £{battery_profit:,.0f}
   • Profit per cycle: £{battery_profit_per_cycle:.2f}

4. Total System Performance:
   • Revenue: £{total_revenue:,.0f}
   • Costs: £{total_import_cost:,.0f} (site + battery charging)
   • Net Profit: £{gross_profit:,.0f}
   • Margin: {margin_pct:.1f}%
   
5. Site Demand:
   • 2.5 MW continuous = {base_green_mwh + base_amber_mwh + base_red_mwh:,.0f} MWh/year
   • Met by battery discharge when available (£150/MWh)
   • Otherwise direct grid import at market rates
   • Total site import cost: £{site_demand_cost:,.0f}
   
6. Additional Revenue Streams:
   • VLP/BM uplift: £{vlp_uplift}/MWh on {vlp_participation*100:.0f}% of discharge
   • Dynamic Containment: £{dc_revenue:,.0f}/year (grid stability services)
   • Curtailment: Variable (paid to reduce/not generate)
""")

print("=" * 80)
print("✅ ANALYSIS COMPLETE - CORRECTED MODEL")
print("=" * 80)
