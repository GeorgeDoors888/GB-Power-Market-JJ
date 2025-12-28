#!/usr/bin/env python3
"""
Review discharge allocation scenarios for BESS revenue model.
Prints detailed breakdown to Google Sheets for review.
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Configuration
SHEET_ID = "1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA"
REVIEW_TAB = "Discharge_Allocation_Review"

# Setup Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('inner-cinema-credentials.json', scope)
client = gspread.authorize(creds)
sheet = client.open_by_key(SHEET_ID)

# Create or get review tab
try:
    ws = sheet.worksheet(REVIEW_TAB)
    ws.clear()
except:
    ws = sheet.add_worksheet(title=REVIEW_TAB, rows=200, cols=15)

print(f"✅ Writing discharge allocation review to: {REVIEW_TAB}")

# Battery specs
CAPACITY_MWH = 5.0
POWER_MW = 2.5
EFFICIENCY = 0.88
DAYS_PER_YEAR = 365

# Current model assumptions
BM_HOURS_PER_DAY = 2
BM_PRICE_PER_MWH = 25
PPA_PROFITABLE_DAYS = 69  # 18.8% of 365
PPA_NET_PROFIT_PER_MWH = 23  # After costs
DC_ANNUAL = 186_150
CM_ANNUAL = 112_566

row = 1

# ==================== HEADER ====================
ws.update(f'A{row}:O{row}', [[
    ['🔋 BESS DISCHARGE ALLOCATION REVIEW', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
]], value_input_option='USER_ENTERED')
row += 1

ws.update(f'A{row}:O{row}', [[
    ['Generated: 2025-12-05', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
]], value_input_option='USER_ENTERED')
row += 2

# ==================== BATTERY SPECS ====================
ws.update(f'A{row}:C{row}', [[
    ['📊 BATTERY SPECIFICATIONS', '', '']
]], value_input_option='USER_ENTERED')
row += 1

specs_data = [
    ['Parameter', 'Value', 'Unit'],
    ['Power Rating', POWER_MW, 'MW'],
    ['Energy Capacity', CAPACITY_MWH, 'MWh'],
    ['Roundtrip Efficiency', f'{EFFICIENCY*100}%', ''],
    ['Annual Cycles Available', DAYS_PER_YEAR, 'cycles/year'],
    ['Max Annual Discharge', CAPACITY_MWH * DAYS_PER_YEAR, 'MWh/year'],
    ['Max Annual Charge', CAPACITY_MWH / EFFICIENCY * DAYS_PER_YEAR, 'MWh/year'],
]

ws.update(f'A{row}', [specs_data], value_input_option='USER_ENTERED')
row += len(specs_data) + 2

# ==================== CURRENT MODEL ANALYSIS ====================
ws.update(f'A{row}:O{row}', [[
    ['⚠️ CURRENT MODEL CLAIMED DISCHARGE', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
]], value_input_option='USER_ENTERED')
row += 1

current_model = [
    ['Revenue Stream', 'Days Used', 'Hours/Day', 'Total Hours', 'Energy/Cycle', 'Total MWh', 'Price/MWh', 'Revenue £', 'Notes'],
    ['', '', '', '', '', '', '', '', ''],
    ['BM Dispatch', 365, 2, 730, f'{POWER_MW * BM_HOURS_PER_DAY}', POWER_MW * BM_HOURS_PER_DAY * 365, BM_PRICE_PER_MWH, 91_250, 'Every day, 2h discharge'],
    ['PPA Arbitrage', 69, 'varies', 138, CAPACITY_MWH, CAPACITY_MWH * 69, 23, 51_465, 'Profitable days only, full cycle'],
    ['', '', '', '', '', '', '', '', ''],
    ['TOTAL CLAIMED', '365 + 69', '868h', '868', '', (POWER_MW * 2 * 365) + (CAPACITY_MWH * 69), '', 142_715, '⚠️ OVERLAP ISSUE'],
    ['', '', '', '', '', '', '', '', ''],
    ['Physical Maximum', 365, 'varies', 8760, CAPACITY_MWH, CAPACITY_MWH * 365, '', '', 'One cycle per day'],
    ['', '', '', '', '', '', '', '', ''],
    ['OVERCLAIM', '', '', '', '', ((POWER_MW * 2 * 365) + (CAPACITY_MWH * 69)) - (CAPACITY_MWH * 365), '', '', f'{(((POWER_MW * 2 * 365) + (CAPACITY_MWH * 69)) / (CAPACITY_MWH * 365) - 1)*100:.1f}% over limit'],
]

ws.update(f'A{row}', [current_model], value_input_option='USER_ENTERED')
row += len(current_model) + 2

# ==================== THE PROBLEM ====================
ws.update(f'A{row}:O{row}', [[
    ['🚨 THE PROBLEM EXPLAINED', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
]], value_input_option='USER_ENTERED')
row += 1

problem_data = [
    ['Issue', 'Description', 'Impact'],
    ['', '', ''],
    ['BM Assumption', f'Battery discharges {POWER_MW} MW for 2 hours every day = {POWER_MW * 2} MWh/day', f'{POWER_MW * 2 * 365:,.0f} MWh/year'],
    ['PPA Assumption', f'Battery also does full {CAPACITY_MWH} MWh cycles on 69 profitable days', f'{CAPACITY_MWH * 69:,.0f} MWh/year'],
    ['Total Claimed', f'Both BM and PPA happening', f'{(POWER_MW * 2 * 365) + (CAPACITY_MWH * 69):,.0f} MWh/year'],
    ['', '', ''],
    ['Physical Reality', f'Battery can only discharge {CAPACITY_MWH} MWh per day maximum', f'{CAPACITY_MWH * 365:,.0f} MWh/year'],
    ['', '', ''],
    ['Overclaim', f'Model assumes {((POWER_MW * 2 * 365) + (CAPACITY_MWH * 69)) / (CAPACITY_MWH * 365):.2f}x physical capacity', f'{((POWER_MW * 2 * 365) + (CAPACITY_MWH * 69)) - (CAPACITY_MWH * 365):,.0f} MWh impossible'],
    ['', '', ''],
    ['Root Cause', 'BM uses 5 MWh/day (2h × 2.5 MW) EVERY day, leaving no capacity for PPA full cycles', 'Days must be allocated: either BM or PPA, not both'],
]

ws.update(f'A{row}', [problem_data], value_input_option='USER_ENTERED')
row += len(problem_data) + 2

# ==================== CORRECTED SCENARIOS ====================
ws.update(f'A{row}:O{row}', [[
    ['✅ CORRECTED ALLOCATION SCENARIOS', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
]], value_input_option='USER_ENTERED')
row += 1

ws.update(f'A{row}:O{row}', [[
    ['Each scenario properly allocates 365 daily cycles without exceeding physical capacity', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
]], value_input_option='USER_ENTERED')
row += 2

# Scenario A: BM Only
scenario_a_title = ['🔵 SCENARIO A: BM PRIORITY (Conservative)', '', '', '', '', '', '', '', '']
ws.update(f'A{row}:I{row}', [scenario_a_title], value_input_option='USER_ENTERED')
row += 1

bm_days_a = 365
bm_mwh_a = POWER_MW * 2 * bm_days_a
bm_revenue_a = bm_mwh_a * BM_PRICE_PER_MWH
ppa_days_a = 0
ppa_mwh_a = 0
ppa_revenue_a = 0
total_discharge_a = bm_mwh_a + ppa_mwh_a
utilization_revenue_a = bm_revenue_a + ppa_revenue_a
total_revenue_a = DC_ANNUAL + CM_ANNUAL + utilization_revenue_a

scenario_a_data = [
    ['Allocation', 'Days', 'MWh Discharged', '£/MWh', 'Revenue £', 'Notes'],
    ['BM Dispatch', bm_days_a, f'{bm_mwh_a:,.0f}', BM_PRICE_PER_MWH, f'{bm_revenue_a:,.0f}', 'All 365 days allocated to BM'],
    ['PPA Arbitrage', ppa_days_a, f'{ppa_mwh_a:,.0f}', PPA_NET_PROFIT_PER_MWH, f'{ppa_revenue_a:,.0f}', 'No days left for PPA'],
    ['', '', '', '', '', ''],
    ['Total Discharge', 365, f'{total_discharge_a:,.0f}', '', '', f'Within {CAPACITY_MWH * 365:,.0f} MWh limit ✅'],
    ['', '', '', '', '', ''],
    ['DC Availability', '', '', '', f'{DC_ANNUAL:,.0f}', '24/7 ready state'],
    ['CM Availability', '', '', '', f'{CM_ANNUAL:,.0f}', 'Stackable with DC'],
    ['Utilization Revenue', '', '', '', f'{utilization_revenue_a:,.0f}', 'BM only'],
    ['', '', '', '', '', ''],
    ['TOTAL REVENUE', '', '', '', f'{total_revenue_a:,.0f}', ''],
    ['Less: Charging Costs', '', '', '', '-348,948', 'GREEN period charging'],
    ['Less: OPEX (5%)', '', '', '', '-25,122', ''],
    ['', '', '', '', '', ''],
    ['NET PROFIT', '', '', '', f'{total_revenue_a - 348_948 - 25_122:,.0f}', f'{((total_revenue_a - 348_948 - 25_122)/total_revenue_a)*100:.1f}% margin'],
]

ws.update(f'A{row}', [scenario_a_data], value_input_option='USER_ENTERED')
row += len(scenario_a_data) + 2

# Scenario B: Split Allocation
scenario_b_title = ['🟢 SCENARIO B: SPLIT ALLOCATION (Balanced)', '', '', '', '', '', '', '', '']
ws.update(f'A{row}:I{row}', [scenario_b_title], value_input_option='USER_ENTERED')
row += 1

ppa_days_b = 69
ppa_mwh_b = CAPACITY_MWH * ppa_days_b
ppa_revenue_b = ppa_mwh_b * PPA_NET_PROFIT_PER_MWH
bm_days_b = 365 - ppa_days_b
bm_mwh_b = POWER_MW * 2 * bm_days_b
bm_revenue_b = bm_mwh_b * BM_PRICE_PER_MWH
total_discharge_b = bm_mwh_b + ppa_mwh_b
utilization_revenue_b = bm_revenue_b + ppa_revenue_b
total_revenue_b = DC_ANNUAL + CM_ANNUAL + utilization_revenue_b

scenario_b_data = [
    ['Allocation', 'Days', 'MWh Discharged', '£/MWh', 'Revenue £', 'Notes'],
    ['PPA Arbitrage', ppa_days_b, f'{ppa_mwh_b:,.0f}', PPA_NET_PROFIT_PER_MWH, f'{ppa_revenue_b:,.0f}', 'Prioritize profitable days first'],
    ['BM Dispatch', bm_days_b, f'{bm_mwh_b:,.0f}', BM_PRICE_PER_MWH, f'{bm_revenue_b:,.0f}', 'Remaining days for BM'],
    ['', '', '', '', '', ''],
    ['Total Discharge', 365, f'{total_discharge_b:,.0f}', '', '', f'Within {CAPACITY_MWH * 365:,.0f} MWh limit ✅'],
    ['', '', '', '', '', ''],
    ['DC Availability', '', '', '', f'{DC_ANNUAL:,.0f}', '24/7 ready state'],
    ['CM Availability', '', '', '', f'{CM_ANNUAL:,.0f}', 'Stackable with DC'],
    ['Utilization Revenue', '', '', '', f'{utilization_revenue_b:,.0f}', 'PPA + BM split'],
    ['', '', '', '', '', ''],
    ['TOTAL REVENUE', '', '', '', f'{total_revenue_b:,.0f}', ''],
    ['Less: Charging Costs', '', '', '', '-348,948', 'GREEN period charging'],
    ['Less: OPEX (5%)', '', '', '', '-25,122', ''],
    ['', '', '', '', '', ''],
    ['NET PROFIT', '', '', '', f'{total_revenue_b - 348_948 - 25_122:,.0f}', f'{((total_revenue_b - 348_948 - 25_122)/total_revenue_b)*100:.1f}% margin'],
]

ws.update(f'A{row}', [scenario_b_data], value_input_option='USER_ENTERED')
row += len(scenario_b_data) + 2

# Scenario C: Dynamic Optimization
scenario_c_title = ['🟡 SCENARIO C: DYNAMIC OPTIMIZATION (Maximum Value)', '', '', '', '', '', '', '', '']
ws.update(f'A{row}:I{row}', [scenario_c_title], value_input_option='USER_ENTERED')
row += 1

# Optimized allocation estimate
high_bm_days_c = 150  # Days with BM >£100/MWh
high_bm_mwh_c = POWER_MW * 2 * high_bm_days_c
high_bm_revenue_c = high_bm_mwh_c * 100  # £100/MWh

ppa_days_c = 69
ppa_mwh_c = CAPACITY_MWH * ppa_days_c
ppa_revenue_c = ppa_mwh_c * PPA_NET_PROFIT_PER_MWH

moderate_bm_days_c = 365 - high_bm_days_c - ppa_days_c
moderate_bm_mwh_c = POWER_MW * 2 * moderate_bm_days_c
moderate_bm_revenue_c = moderate_bm_mwh_c * BM_PRICE_PER_MWH

total_discharge_c = high_bm_mwh_c + ppa_mwh_c + moderate_bm_mwh_c
utilization_revenue_c = high_bm_revenue_c + ppa_revenue_c + moderate_bm_revenue_c
total_revenue_c = DC_ANNUAL + CM_ANNUAL + utilization_revenue_c

scenario_c_data = [
    ['Allocation', 'Days', 'MWh Discharged', '£/MWh Avg', 'Revenue £', 'Notes'],
    ['High-Value BM', high_bm_days_c, f'{high_bm_mwh_c:,.0f}', '100', f'{high_bm_revenue_c:,.0f}', 'BM price >£100/MWh days'],
    ['PPA Arbitrage', ppa_days_c, f'{ppa_mwh_c:,.0f}', PPA_NET_PROFIT_PER_MWH, f'{ppa_revenue_c:,.0f}', 'Good spread days'],
    ['Moderate BM', moderate_bm_days_c, f'{moderate_bm_mwh_c:,.0f}', BM_PRICE_PER_MWH, f'{moderate_bm_revenue_c:,.0f}', 'Fill remaining capacity'],
    ['', '', '', '', '', ''],
    ['Total Discharge', 365, f'{total_discharge_c:,.0f}', '', '', f'Within {CAPACITY_MWH * 365:,.0f} MWh limit ✅'],
    ['', '', '', '', '', ''],
    ['DC Availability', '', '', '', f'{DC_ANNUAL:,.0f}', '24/7 ready state'],
    ['CM Availability', '', '', '', f'{CM_ANNUAL:,.0f}', 'Stackable with DC'],
    ['Utilization Revenue', '', '', '', f'{utilization_revenue_c:,.0f}', 'Optimized mix'],
    ['', '', '', '', '', ''],
    ['TOTAL REVENUE', '', '', '', f'{total_revenue_c:,.0f}', ''],
    ['Less: Charging Costs', '', '', '', '-348,948', 'GREEN period charging'],
    ['Less: OPEX (5%)', '', '', '', '-25,122', ''],
    ['', '', '', '', '', ''],
    ['NET PROFIT', '', '', '', f'{total_revenue_c - 348_948 - 25_122:,.0f}', f'{((total_revenue_c - 348_948 - 25_122)/total_revenue_c)*100:.1f}% margin'],
]

ws.update(f'A{row}', [scenario_c_data], value_input_option='USER_ENTERED')
row += len(scenario_c_data) + 2

# ==================== COMPARISON SUMMARY ====================
ws.update(f'A{row}:O{row}', [[
    ['📊 SCENARIO COMPARISON', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
]], value_input_option='USER_ENTERED')
row += 1

comparison_data = [
    ['Metric', 'Current Model', 'Scenario A', 'Scenario B', 'Scenario C', 'Best'],
    ['', '(INCORRECT)', '(BM Only)', '(Split)', '(Optimized)', ''],
    ['', '', '', '', '', ''],
    ['Total Discharge MWh', f'{(POWER_MW * 2 * 365) + (CAPACITY_MWH * 69):,.0f}', f'{total_discharge_a:,.0f}', f'{total_discharge_b:,.0f}', f'{total_discharge_c:,.0f}', ''],
    ['Within Physical Limit?', '❌ NO', '✅ YES', '✅ YES', '✅ YES', 'All corrected'],
    ['', '', '', '', '', ''],
    ['BM Revenue £', '91,250', f'{bm_revenue_a:,.0f}', f'{bm_revenue_b:,.0f}', f'{moderate_bm_revenue_c + high_bm_revenue_c:,.0f}', 'Scenario C'],
    ['PPA Revenue £', '51,465', f'{ppa_revenue_a:,.0f}', f'{ppa_revenue_b:,.0f}', f'{ppa_revenue_c:,.0f}', 'Scenario B/C'],
    ['Utilization Revenue £', '142,715', f'{utilization_revenue_a:,.0f}', f'{utilization_revenue_b:,.0f}', f'{utilization_revenue_c:,.0f}', 'Scenario C'],
    ['', '', '', '', '', ''],
    ['DC + CM Revenue £', '298,716', '298,716', '298,716', '298,716', 'Same all'],
    ['Total Revenue £', '441,431', f'{total_revenue_a:,.0f}', f'{total_revenue_b:,.0f}', f'{total_revenue_c:,.0f}', 'Scenario C'],
    ['', '', '', '', '', ''],
    ['Charging Costs £', '-348,948', '-348,948', '-348,948', '-348,948', 'Same all'],
    ['OPEX £', '-25,122', '-25,122', '-25,122', '-25,122', 'Same all'],
    ['', '', '', '', '', ''],
    ['NET PROFIT £', f'{441_431 - 348_948 - 25_122:,.0f}', f'{total_revenue_a - 348_948 - 25_122:,.0f}', f'{total_revenue_b - 348_948 - 25_122:,.0f}', f'{total_revenue_c - 348_948 - 25_122:,.0f}', 'Scenario C'],
    ['', '', '', '', '', ''],
    ['vs Current Model', '0%', f'{((total_revenue_a - 348_948 - 25_122) / (441_431 - 348_948 - 25_122) - 1)*100:+.1f}%', f'{((total_revenue_b - 348_948 - 25_122) / (441_431 - 348_948 - 25_122) - 1)*100:+.1f}%', f'{((total_revenue_c - 348_948 - 25_122) / (441_431 - 348_948 - 25_122) - 1)*100:+.1f}%', ''],
]

ws.update(f'A{row}', [comparison_data], value_input_option='USER_ENTERED')
row += len(comparison_data) + 2

# ==================== RECOMMENDATIONS ====================
ws.update(f'A{row}:O{row}', [[
    ['💡 RECOMMENDATIONS', '', '', '', '', '', '', '', '', '', '', '', '', '', '']
]], value_input_option='USER_ENTERED')
row += 1

recommendations = [
    ['Priority', 'Action', 'Impact', 'Notes'],
    ['', '', '', ''],
    ['1. CRITICAL', 'Correct discharge allocation in revenue model', 'Remove physical impossibility', 'Current model claims 119% of capacity'],
    ['2. HIGH', 'Implement Scenario C (Dynamic Optimization)', f'+£{(total_revenue_c - 348_948 - 25_122) - (441_431 - 348_948 - 25_122):,.0f}/year vs current', 'Maximizes value by prioritizing high-price BM'],
    ['3. MEDIUM', 'Validate BM price assumptions', '£25-100/MWh range', 'Check actual accepted BM prices in BOALF'],
    ['4. MEDIUM', 'Validate BM dispatch frequency', '2h/day assumption', 'May be optimistic, check historical data'],
    ['5. LOW', 'Model partial cycles', 'Further optimization', 'Battery can do <5 MWh discharges'],
    ['', '', '', ''],
    ['NEXT STEPS', '', '', ''],
    ['', '1. Review scenarios above', '', 'Choose preferred allocation strategy'],
    ['', '2. Update revenue model with correct discharge allocation', '', 'Either Scenario B or C'],
    ['', '3. Recalculate financial metrics (IRR, payback, NPV)', '', 'Based on corrected revenue'],
    ['', '4. Validate assumptions with actual market data', '', 'BM prices, dispatch frequency, PPA spreads'],
]

ws.update(f'A{row}', [recommendations], value_input_option='USER_ENTERED')

print(f"\n✅ Review complete!")
print(f"\n📊 Scenario Summary:")
print(f"   Current Model (INCORRECT): Net profit £{441_431 - 348_948 - 25_122:,.0f}/year (exceeds capacity)")
print(f"   Scenario A (BM Only):      Net profit £{total_revenue_a - 348_948 - 25_122:,.0f}/year")
print(f"   Scenario B (Split):        Net profit £{total_revenue_b - 348_948 - 25_122:,.0f}/year")
print(f"   Scenario C (Optimized):    Net profit £{total_revenue_c - 348_948 - 25_122:,.0f}/year")
print(f"\n🔗 View at: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid={ws.id}")
