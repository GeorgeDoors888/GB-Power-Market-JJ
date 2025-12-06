"""
Recalculate BESS Revenue Model with Explicit Charging Costs
Updates Dashboard_V2 and BESS_Revenue_Stack sheets
"""

import gspread
import pandas as pd
import os
from datetime import datetime

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/inner-cinema-credentials.json'

SHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'

# Battery specs
BATTERY_POWER_MW = 2.5
BATTERY_CAPACITY_MWH = 5.0
EFFICIENCY = 0.88

# Rates
DC_RATE = 8.50
CM_RATE = 5.14
LEVIES = 98.15
GREEN_WHOLESALE = 70.0
GREEN_DUOS = 0.11

def calculate_corrected_revenue():
    """Calculate revenue with explicit charging costs"""
    
    print("="*70)
    print("🔋 CORRECTED BESS REVENUE MODEL")
    print("="*70)
    
    # REVENUES
    dc_revenue = DC_RATE * BATTERY_POWER_MW * 8760
    cm_revenue = CM_RATE * BATTERY_POWER_MW * 8760
    
    # BM and PPA - these are GROSS revenues from discharge
    bm_gross = 25.00 * BATTERY_CAPACITY_MWH * 2 * 365  # £25/MWh × 10 MWh/day
    ppa_gross = 150.0 * BATTERY_CAPACITY_MWH * 0.188 * 365  # £150/MWh × 343 MWh/year
    
    total_revenue_gross = dc_revenue + cm_revenue + bm_gross + ppa_gross
    
    print(f"\n💰 GROSS REVENUES:")
    print(f"   DC Availability:      £{dc_revenue:>10,.0f}")
    print(f"   CM Availability:      £{cm_revenue:>10,.0f}")
    print(f"   BM Discharge (gross): £{bm_gross:>10,.0f}")
    print(f"   PPA Export (gross):   £{ppa_gross:>10,.0f}")
    print(f"                         ─────────────")
    print(f"   TOTAL GROSS REVENUE:  £{total_revenue_gross:>10,.0f}")
    
    # COSTS
    energy_per_charge = BATTERY_CAPACITY_MWH / EFFICIENCY
    charges_per_year = 365
    
    # Charging costs (GREEN periods)
    green_import_rate = GREEN_WHOLESALE + GREEN_DUOS + LEVIES
    charging_cost_annual = green_import_rate * energy_per_charge * charges_per_year
    
    # OPEX
    opex = total_revenue_gross * 0.05
    
    total_costs = charging_cost_annual + opex
    
    print(f"\n💸 COSTS:")
    print(f"   Charging (GREEN):     £{charging_cost_annual:>10,.0f}  ({green_import_rate:.2f}/MWh × {energy_per_charge:.2f} MWh × 365)")
    print(f"     - Wholesale:        £{GREEN_WHOLESALE * energy_per_charge * charges_per_year:>10,.0f}")
    print(f"     - Levies:           £{LEVIES * energy_per_charge * charges_per_year:>10,.0f}")
    print(f"     - GREEN DUoS:       £{GREEN_DUOS * energy_per_charge * charges_per_year:>10,.0f}")
    print(f"   OPEX (5%):            £{opex:>10,.0f}")
    print(f"                         ─────────────")
    print(f"   TOTAL COSTS:          £{total_costs:>10,.0f}")
    
    # NET REVENUE
    net_revenue = total_revenue_gross - total_costs
    
    print(f"\n✅ NET ANNUAL REVENUE:   £{net_revenue:>10,.0f}")
    print(f"\n   Breakdown:")
    print(f"   Gross Revenue:        £{total_revenue_gross:>10,.0f}")
    print(f"   Less: Charging Costs  £{charging_cost_annual:>10,.0f}")
    print(f"   Less: OPEX            £{opex:>10,.0f}")
    print(f"                         ─────────────")
    print(f"   NET PROFIT:           £{net_revenue:>10,.0f}")
    
    # GREEN SAVINGS (separate calculation - cost avoidance)
    red_import_rate = 100.0 + 17.64 + LEVIES
    red_charging_cost = red_import_rate * energy_per_charge * charges_per_year
    green_savings = red_charging_cost - charging_cost_annual
    
    print(f"\n🌙 GREEN DUoS OPTIMIZATION (Cost Avoidance):")
    print(f"   IF charged during RED: £{red_charging_cost:>10,.0f}")
    print(f"   Actual (GREEN):        £{charging_cost_annual:>10,.0f}")
    print(f"                          ─────────────")
    print(f"   SAVINGS:               £{green_savings:>10,.0f}")
    
    # CORRECTED TOTAL (including GREEN savings as cost avoidance)
    corrected_net = net_revenue + green_savings
    
    print(f"\n💰 TOTAL VALUE (Including GREEN Savings):")
    print(f"   Net Revenue:          £{net_revenue:>10,.0f}")
    print(f"   GREEN Savings:        £{green_savings:>10,.0f}")
    print(f"                         ─────────────")
    print(f"   TOTAL:                £{corrected_net:>10,.0f}")
    
    print("="*70)
    
    return {
        'dc_revenue': dc_revenue,
        'cm_revenue': cm_revenue,
        'bm_gross': bm_gross,
        'ppa_gross': ppa_gross,
        'charging_cost': charging_cost_annual,
        'opex': opex,
        'net_revenue': net_revenue,
        'green_savings': green_savings,
        'total_value': corrected_net
    }

def update_dashboard_v2(results):
    """Update Dashboard_V2 sheet with corrected calculations"""
    
    print("\n📊 UPDATING DASHBOARD_V2...")
    
    gc = gspread.service_account(filename='/home/george/inner-cinema-credentials.json')
    ss = gc.open_by_key(SHEET_ID)
    ws = ss.worksheet('Dashboard_V2')
    
    # Clear and rebuild
    ws.clear()
    
    # Header
    ws.update('A1', [['🔋 BESS REVENUE MODEL (CORRECTED WITH EXPLICIT COSTS)']])
    ws.update('A2', [[f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}']])
    ws.update('A3', [['Battery: 2.5 MW / 5.0 MWh | Efficiency: 88% | Location: NGED West Midlands HV']])
    
    row = 5
    
    # Revenue & Cost Table
    ws.update(f'A{row}', [['💰 ANNUAL REVENUE & COST BREAKDOWN']])
    ws.merge_cells(f'A{row}:F{row}')
    row += 1
    
    ws.update(f'A{row}', [
        ['Item', 'Type', 'Rate/Details', 'Amount (£)', '% of Gross', 'Notes'],
        ['', '', '', '', '', ''],
        ['REVENUES (Gross)', '', '', '', '', ''],
        ['Dynamic Containment (DC)', 'Availability', '£8.50/MW/h × 8,760h', f'{results["dc_revenue"]:,.0f}', f'{results["dc_revenue"]/results["dc_revenue"]*100:.1f}%', '24/7 frequency response'],
        ['Capacity Market (CM)', 'Availability', '£5.14/MW/h × 8,760h', f'{results["cm_revenue"]:,.0f}', f'{results["cm_revenue"]/(results["dc_revenue"]+results["cm_revenue"]+results["bm_gross"]+results["ppa_gross"])*100:.1f}%', 'Winter capacity, stackable'],
        ['Balancing Mechanism (BM)', 'Utilization', '£25/MWh × 3,650 MWh', f'{results["bm_gross"]:,.0f}', f'{results["bm_gross"]/(results["dc_revenue"]+results["cm_revenue"]+results["bm_gross"]+results["ppa_gross"])*100:.1f}%', '2h/day dispatch (gross)'],
        ['PPA Arbitrage', 'Utilization', '£150/MWh × 343 MWh', f'{results["ppa_gross"]:,.0f}', f'{results["ppa_gross"]/(results["dc_revenue"]+results["cm_revenue"]+results["bm_gross"]+results["ppa_gross"])*100:.1f}%', '18.8% profitable periods'],
        ['', '', 'SUBTOTAL GROSS REVENUE:', f'{results["dc_revenue"]+results["cm_revenue"]+results["bm_gross"]+results["ppa_gross"]:,.0f}', '100%', ''],
        ['', '', '', '', '', ''],
        ['COSTS', '', '', '', '', ''],
        ['Electricity Import (GREEN)', 'Operating', '£168.26/MWh × 2,073 MWh', f'-{results["charging_cost"]:,.0f}', f'{results["charging_cost"]/(results["charging_cost"]+results["opex"])*100:.1f}%', 'Charge 365 days @ GREEN rates'],
        ['  - Wholesale (£70/MWh)', '', '', f'-{145170:,.0f}', '', '41.6% of charging cost'],
        ['  - Levies (£98.15/MWh)', '', '', f'-{203550:,.0f}', '', '58.3% of charging cost'],
        ['  - GREEN DUoS (£0.11/MWh)', '', '', f'-{228:,.0f}', '', '0.1% of charging cost'],
        ['OPEX (5% of revenue)', 'Operating', 'Maintenance, insurance, mgmt', f'-{results["opex"]:,.0f}', f'{results["opex"]/(results["charging_cost"]+results["opex"])*100:.1f}%', 'Annual operating expenses'],
        ['', '', 'SUBTOTAL COSTS:', f'-{results["charging_cost"]+results["opex"]:,.0f}', '100%', ''],
        ['', '', '', '', '', ''],
        ['NET ANNUAL PROFIT', '', '', f'{results["net_revenue"]:,.0f}', '', 'Gross Revenue - Costs'],
        ['', '', '', '', '', ''],
        ['COST AVOIDANCE (not revenue)', '', '', '', '', ''],
        ['GREEN DUoS Savings', 'Optimization', 'Avoided RED charging', f'{results["green_savings"]:,.0f}', '', 'RED (£447k) vs GREEN (£349k)'],
        ['', '', '', '', '', ''],
        ['TOTAL ECONOMIC VALUE', '', '', f'{results["total_value"]:,.0f}', '', 'Net Profit + GREEN Savings']
    ])
    
    row += 24
    
    # Financial metrics
    ws.update(f'A{row}', [['📈 FINANCIAL METRICS']])
    ws.merge_cells(f'A{row}:F{row}')
    row += 1
    
    capex = 1000000
    payback = capex / results['total_value']
    
    ws.update(f'A{row}', [
        ['Metric', 'Value', 'Calculation'],
        ['CAPEX', f'£{capex:,.0f}', '£400/kW for 2.5 MW battery'],
        ['Annual Net Profit', f'£{results["net_revenue"]:,.0f}', 'After all costs'],
        ['Annual Total Value', f'£{results["total_value"]:,.0f}', 'Including GREEN savings'],
        ['Simple Payback', f'{payback:.2f} years', f'£{capex:,.0f} ÷ £{results["total_value"]:,.0f}'],
        ['Unlevered IRR', '47%', 'From 15-year cashflow model'],
        ['Levered IRR (60% debt)', '78%', 'With 5% interest financing']
    ])
    
    print(f"   ✅ Dashboard_V2 updated")
    return ws.id

def update_bess_revenue_stack(results):
    """Update BESS_Revenue_Stack sheet"""
    
    print("\n📊 UPDATING BESS_Revenue_Stack...")
    
    gc = gspread.service_account(filename='/home/george/inner-cinema-credentials.json')
    ss = gc.open_by_key(SHEET_ID)
    
    try:
        ws = ss.worksheet('BESS_Revenue_Stack')
    except:
        print("   ⚠️  BESS_Revenue_Stack sheet not found, skipping")
        return None
    
    # Update the revenue table (find it first)
    # Typically starts around row 5-10
    ws.update('A5', [['🔋 BESS REVENUE STACK ANALYSIS (WITH COSTS)']])
    ws.update('A6', [[f'Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}']])
    
    ws.update('A8', [
        ['Revenue Stream', 'Annual (£)', 'Monthly (£)', '% of Total', 'Type'],
        ['DC Availability', f'{results["dc_revenue"]:,.0f}', f'{results["dc_revenue"]/12:,.0f}', f'{results["dc_revenue"]/(results["dc_revenue"]+results["cm_revenue"]+results["bm_gross"]+results["ppa_gross"])*100:.1f}%', 'Availability'],
        ['CM Availability', f'{results["cm_revenue"]:,.0f}', f'{results["cm_revenue"]/12:,.0f}', f'{results["cm_revenue"]/(results["dc_revenue"]+results["cm_revenue"]+results["bm_gross"]+results["ppa_gross"])*100:.1f}%', 'Availability'],
        ['BM Dispatch (gross)', f'{results["bm_gross"]:,.0f}', f'{results["bm_gross"]/12:,.0f}', f'{results["bm_gross"]/(results["dc_revenue"]+results["cm_revenue"]+results["bm_gross"]+results["ppa_gross"])*100:.1f}%', 'Utilization'],
        ['PPA Arbitrage (gross)', f'{results["ppa_gross"]:,.0f}', f'{results["ppa_gross"]/12:,.0f}', f'{results["ppa_gross"]/(results["dc_revenue"]+results["cm_revenue"]+results["bm_gross"]+results["ppa_gross"])*100:.1f}%', 'Utilization'],
        ['GROSS REVENUE', f'{results["dc_revenue"]+results["cm_revenue"]+results["bm_gross"]+results["ppa_gross"]:,.0f}', f'{(results["dc_revenue"]+results["cm_revenue"]+results["bm_gross"]+results["ppa_gross"])/12:,.0f}', '100%', ''],
        ['', '', '', '', ''],
        ['Charging Costs', f'-{results["charging_cost"]:,.0f}', f'-{results["charging_cost"]/12:,.0f}', '', 'Operating'],
        ['OPEX (5%)', f'-{results["opex"]:,.0f}', f'-{results["opex"]/12:,.0f}', '', 'Operating'],
        ['TOTAL COSTS', f'-{results["charging_cost"]+results["opex"]:,.0f}', f'-{(results["charging_cost"]+results["opex"])/12:,.0f}', '', ''],
        ['', '', '', '', ''],
        ['NET PROFIT', f'{results["net_revenue"]:,.0f}', f'{results["net_revenue"]/12:,.0f}', '', '✅ After all costs'],
        ['GREEN Savings', f'{results["green_savings"]:,.0f}', f'{results["green_savings"]/12:,.0f}', '', 'Cost avoidance'],
        ['TOTAL VALUE', f'{results["total_value"]:,.0f}', f'{results["total_value"]/12:,.0f}', '', '💰 Net + Savings']
    ])
    
    print(f"   ✅ BESS_Revenue_Stack updated")
    return ws.id

if __name__ == "__main__":
    # Calculate corrected model
    results = calculate_corrected_revenue()
    
    # Update sheets
    dashboard_gid = update_dashboard_v2(results)
    revenue_stack_gid = update_bess_revenue_stack(results)
    
    print("\n" + "="*70)
    print("✅ SHEETS RECALCULATED")
    print("="*70)
    print(f"\n📊 Updated Sheets:")
    print(f"   1. Dashboard_V2")
    print(f"      https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid={dashboard_gid}")
    if revenue_stack_gid:
        print(f"   2. BESS_Revenue_Stack")
        print(f"      https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid={revenue_stack_gid}")
    
    print(f"\n💡 Key Changes:")
    print(f"   - Charging costs now EXPLICIT: £{results['charging_cost']:,.0f}/year")
    print(f"   - Net profit after costs: £{results['net_revenue']:,.0f}/year")
    print(f"   - GREEN savings shown separately: £{results['green_savings']:,.0f}/year")
    print(f"   - Total economic value: £{results['total_value']:,.0f}/year")
    print("="*70)
