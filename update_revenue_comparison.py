#!/usr/bin/env python3
"""
Update BESS Revenue Stack sheet with detailed comparison of allocation scenarios
Shows current model vs corrected physical constraints
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Google Sheets setup
SHEET_ID = "1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc"
TAB_NAME = "Revenue_Analysis_Comparison"
CREDS_PATH = '/home/george/inner-cinema-credentials.json'

# Authenticate
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, scope)
client = gspread.authorize(creds)

# Open sheet
sheet = client.open_by_key(SHEET_ID)

# Create or clear the comparison tab
try:
    ws = sheet.worksheet(TAB_NAME)
    # Ensure enough rows
    if ws.row_count < 150:
        ws.add_rows(150 - ws.row_count)
    ws.clear()
except:
    ws = sheet.add_worksheet(title=TAB_NAME, rows=150, cols=20)

print(f"✅ Updating {TAB_NAME} tab...")

# Header
row = 1
ws.update(f'A{row}:H{row}', [[
    'BESS REVENUE MODEL ANALYSIS - PHYSICAL CONSTRAINTS REVIEW',
    '', '', '', '', '', '', ''
]])
ws.update(f'A{row}:H{row}', [['']*8], raw=False)  # Format will be applied separately

row += 2

# Battery Specifications
ws.update(f'A{row}:D{row}', [['⚡ BATTERY SPECIFICATIONS', '', '', '']])
row += 1
ws.update(f'A{row}:D{row+5}', [
    ['Parameter', 'Value', 'Unit', 'Notes'],
    ['Power Capacity', '2.5', 'MW', 'Maximum charge/discharge rate'],
    ['Energy Capacity', '5.0', 'MWh', 'Storage capacity per cycle'],
    ['Roundtrip Efficiency', '88%', '', '12% losses per cycle'],
    ['Daily Cycles', '1', 'cycle/day', 'Conservative operation'],
    ['Annual Energy Limit', '1,825', 'MWh/year', '5 MWh × 365 days']
])
row += 7

# Physical Constraints Analysis
ws.update(f'A{row}:G{row}', [['🔬 PHYSICAL CONSTRAINTS ANALYSIS', '', '', '', '', '', '']])
row += 1
ws.update(f'A{row}:G{row+4}', [
    ['Scenario', 'BM Days', 'BM MWh', 'PPA Days', 'PPA MWh', 'Total MWh', 'Status'],
    ['Current Model (as shown)', '365', '1,825', '69', '345', '2,170', '❌ EXCEEDS LIMIT'],
    ['Physical Reality', '365', '1,825', '0', '0', '1,825', '✅ Within limit'],
    ['', '', '', '', '', '', ''],
    ['Problem: Current model claims battery discharges 2,170 MWh when max is 1,825 MWh', '', '', '', '', '', '']
])
row += 6

# Scenario Comparison Table
ws.update(f'A{row}:H{row}', [['📊 REVENUE SCENARIOS - CORRECTED ALLOCATION', '', '', '', '', '', '', '']])
row += 1

scenarios_header = ['Scenario', 'BM Days', 'BM Revenue', 'PPA Days', 'PPA Revenue', 'Utilization Total', 'Total Revenue', 'Net Profit']
ws.update(f'A{row}:H{row}', [scenarios_header])
row += 1

# Current Model (Incorrect)
ws.update(f'A{row}:H{row}', [[
    '❌ CURRENT MODEL (Impossible)',
    '365 (2h/day)',
    '£91,250',
    '69 (simultaneous)',
    '£51,465',
    '£142,715',
    '£502,448',
    '£127,378'
]])
row += 1

# Scenario A: BM Only
ws.update(f'A{row}:H{row}', [[
    'Scenario A: BM Priority',
    '365',
    '£91,250',
    '0',
    '£0',
    '£91,250',
    '£390,250',
    '£16,180'
]])
row += 1

# Scenario B: PPA Priority
ws.update(f'A{row}:H{row}', [[
    'Scenario B: PPA Priority',
    '296',
    '£74,000',
    '69',
    '£51,750',
    '£125,750',
    '£424,750',
    '£50,680'
]])
row += 1

# Scenario C: High BM Days Only
ws.update(f'A{row}:H{row}', [[
    'Scenario C: High BM Only (£100+)',
    '150',
    '£75,000',
    '0',
    '£0',
    '£75,000',
    '£374,000',
    '£0'
]])
row += 1

# Scenario D: Dynamic Optimization
ws.update(f'A{row}:H{row}', [[
    'Scenario D: Optimized Mix',
    '200 high',
    '£100,000',
    '69',
    '£51,750',
    '£151,750',
    '£450,750',
    '£76,680'
]])
row += 2

# Detailed Breakdown Section
ws.update(f'A{row}:H{row}', [['📋 DETAILED SCENARIO BREAKDOWN', '', '', '', '', '', '', '']])
row += 2

# Scenario A Details
ws.update(f'A{row}:E{row}', [['SCENARIO A: BM PRIORITY (Conservative)', '', '', '', '']])
row += 1
ws.update(f'A{row}:E{row+9}', [
    ['Revenue Component', 'Calculation', 'Amount', '% of Total', 'Notes'],
    ['DC Availability', '£8.50/MW/h × 2.5MW × 8,760h', '£186,150', '47.7%', 'Frequency response'],
    ['CM Availability', '£5.14/MW/h × 2.5MW × 8,760h', '£112,566', '28.8%', 'Capacity market'],
    ['BM Dispatch', '365 days × 5 MWh × £25/MWh', '£91,250', '23.4%', 'All days to BM'],
    ['PPA Arbitrage', '0 days', '£0', '0.0%', 'No PPA allocation'],
    ['GROSS REVENUE', '', '£390,250', '100.0%', ''],
    ['Charging Cost', '365 × £956', '-£348,948', '-89.4%', 'GREEN period'],
    ['OPEX (5%)', '5% of gross', '-£25,122', '-6.4%', 'Maintenance'],
    ['TOTAL COSTS', '', '-£374,070', '-95.9%', ''],
    ['NET PROFIT', '', '£16,180', '4.1%', 'Annual profit']
])
row += 12

# Scenario B Details
ws.update(f'A{row}:E{row}', [['SCENARIO B: PPA PRIORITY (Balanced)', '', '', '', '']])
row += 1
ws.update(f'A{row}:E{row+9}', [
    ['Revenue Component', 'Calculation', 'Amount', '% of Total', 'Notes'],
    ['DC Availability', '£8.50/MW/h × 2.5MW × 8,760h', '£186,150', '43.8%', 'Frequency response'],
    ['CM Availability', '£5.14/MW/h × 2.5MW × 8,760h', '£112,566', '26.5%', 'Capacity market'],
    ['BM Dispatch', '296 days × 5 MWh × £25/MWh', '£74,000', '17.4%', 'Non-PPA days'],
    ['PPA Arbitrage', '69 days × 5 MWh × £150/MWh gross', '£51,750', '12.2%', 'Profitable periods'],
    ['GROSS REVENUE', '', '£424,750', '100.0%', ''],
    ['Charging Cost', '365 × £956', '-£348,948', '-82.2%', 'GREEN period'],
    ['OPEX (5%)', '5% of gross', '-£25,122', '-5.9%', 'Maintenance'],
    ['TOTAL COSTS', '', '-£374,070', '-88.1%', ''],
    ['NET PROFIT', '', '£50,680', '11.9%', 'Annual profit']
])
row += 12

# Scenario D Details
ws.update(f'A{row}:E{row}', [['SCENARIO D: OPTIMIZED MIX (Recommended)', '', '', '', '']])
row += 1
ws.update(f'A{row}:E{row+10}', [
    ['Revenue Component', 'Calculation', 'Amount', '% of Total', 'Notes'],
    ['DC Availability', '£8.50/MW/h × 2.5MW × 8,760h', '£186,150', '41.3%', 'Frequency response'],
    ['CM Availability', '£5.14/MW/h × 2.5MW × 8,760h', '£112,566', '25.0%', 'Capacity market'],
    ['BM High Price Days', '200 days × 5 MWh × £100/MWh', '£100,000', '22.2%', 'BM price >£100'],
    ['PPA Arbitrage', '69 days × 5 MWh × £150/MWh gross', '£51,750', '11.5%', 'Good spread days'],
    ['Remaining Days', '96 days at low/zero revenue', '£0', '0.0%', 'Not economical'],
    ['GROSS REVENUE', '', '£450,750', '100.0%', ''],
    ['Charging Cost', '365 × £956', '-£348,948', '-77.4%', 'GREEN period'],
    ['OPEX (5%)', '5% of gross', '-£25,122', '-5.6%', 'Maintenance'],
    ['TOTAL COSTS', '', '-£374,070', '-83.0%', ''],
    ['NET PROFIT', '', '£76,680', '17.0%', 'Annual profit']
])
row += 13

# Key Insights
ws.update(f'A{row}:F{row}', [['💡 KEY INSIGHTS', '', '', '', '', '']])
row += 1
ws.update(f'A{row}:F{row+10}', [
    ['Issue', 'Finding', 'Impact', 'Recommendation', '', ''],
    ['Physical Limit', 'Battery can discharge max 1,825 MWh/year', 'Current model claims 2,170 MWh', 'Use Scenario B or D', '', ''],
    ['Time Availability', 'BM (730h) + PPA (138h) = 868h fits in 8,760h', 'No time conflict', 'Both can operate', '', ''],
    ['Energy Constraint', 'Each day: 1 full cycle (5 MWh) maximum', 'Cannot do full BM + full PPA same day', 'Allocate days between uses', '', ''],
    ['Revenue Reality', 'Scenario D (optimized): £451k gross, £77k net', '£51k lower than current model', 'More realistic expectation', '', ''],
    ['Best Strategy', 'Prioritize highest value per day', 'BM on high-price days (£100+)', 'Dynamic daily optimization', '', ''],
    ['', '', '', '', '', ''],
    ['Current Model Error', 'Assumes simultaneous full BM + PPA discharge', 'Overstates by £52k/year', 'Must choose per day', '', ''],
    ['', '', '', '', '', ''],
    ['RECOMMENDATION', 'Implement Scenario D with dynamic dispatch optimizer', '', '', '', ''],
    ['Expected Net Profit', '£76,680/year (vs £127k claimed)', '', '', '', '']
])
row += 13

# Dispatch Logic Table
ws.update(f'A{row}:E{row}', [['🎯 OPTIMAL DISPATCH LOGIC (Scenario D)', '', '', '', '']])
row += 1
ws.update(f'A{row}:E{row+7}', [
    ['Day Type', 'Condition', 'Action', 'Expected Days/Year', 'Revenue/Day'],
    ['High BM Price', 'BM price >£100/MWh', 'Discharge to BM', '~200 days', '£500'],
    ['Good PPA Spread', 'Arbitrage spread >£50/MWh + no BM call', 'Charge cheap/sell expensive', '~69 days', '£750'],
    ['Moderate BM', 'BM price £50-100/MWh', 'Discharge to BM', '~50 days', '£250'],
    ['Low Activity', 'BM price <£50, poor arbitrage', 'Stay ready (DC/CM only)', '~46 days', '£0'],
    ['', '', '', '', ''],
    ['Total', '', '', '365 days', '£151,750 utilization'],
    ['Plus DC/CM baseline', '', '', '', '£299,000 availability']
])
row += 10

# Comparison Summary
ws.update(f'A{row}:D{row}', [['📈 FINANCIAL COMPARISON SUMMARY', '', '', '']])
row += 1
ws.update(f'A{row}:D{row+8}', [
    ['Metric', 'Current Model', 'Scenario D (Optimized)', 'Change'],
    ['Gross Revenue', '£502,448', '£450,750', '-£51,698 (-10.3%)'],
    ['Total Costs', '-£399,192', '-£374,070', '+£25,122 (better)'],
    ['Net Profit', '£127,378', '£76,680', '-£50,698 (-39.8%)'],
    ['', '', '', ''],
    ['IRR (unlevered)', '47%', '~12-15% (est)', 'Needs recalculation'],
    ['Payback Period', '2.1 years', '~8-10 years (est)', 'Needs recalculation'],
    ['Physical Feasibility', '❌ Impossible (2,170 MWh)', '✅ Achievable (1,825 MWh)', 'Within limits'],
    ['', '', '', '']
])
row += 10

# Action Items
ws.update(f'A{row}:C{row}', [['✅ NEXT STEPS', '', '']])
row += 1
ws.update(f'A{row}:C{row+5}', [
    ['Priority', 'Action Item', 'Owner'],
    ['HIGH', 'Review scenarios and select preferred allocation strategy', 'Team'],
    ['HIGH', 'Recalculate IRR, NPV, payback with corrected revenue (£451k vs £502k)', 'Finance'],
    ['MEDIUM', 'Implement dynamic dispatch optimizer for Scenario D', 'Technical'],
    ['MEDIUM', 'Update all financial models and presentations with corrected figures', 'All'],
    ['LOW', 'Monitor actual BM dispatch vs model assumptions', 'Operations']
])

print("✅ Revenue comparison analysis complete!")
print(f"📊 View at: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid={ws.id}")
print("\nScenarios created:")
print("  - Current Model: £502k revenue (physically impossible - 2,170 MWh discharge)")
print("  - Scenario A: £390k revenue, £16k net (BM only)")
print("  - Scenario B: £425k revenue, £51k net (PPA priority)")
print("  - Scenario D: £451k revenue, £77k net (optimized mix - RECOMMENDED)")
print("\n⚠️  Current model overstates net profit by £51k/year due to physical constraints")
