#!/usr/bin/env python3
"""
Complete BESS Revenue Model Explanation
Prints comprehensive breakdown to understand the entire model
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials

SHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'
TAB_NAME = 'Model_Explanation'
CREDS_PATH = '/home/george/inner-cinema-credentials.json'

# Authenticate
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(CREDS_PATH, scope)
client = gspread.authorize(creds)

# Open sheet
sheet = client.open_by_key(SHEET_ID)

# Create or clear the tab
try:
    ws = sheet.worksheet(TAB_NAME)
    if ws.row_count < 200:
        ws.add_rows(200 - ws.row_count)
    ws.clear()
except:
    ws = sheet.add_worksheet(title=TAB_NAME, rows=200, cols=15)

print(f"✅ Creating complete model explanation in {TAB_NAME} tab...")

row = 1

# Title
ws.update(range_name=f'A{row}:L{row}', values=[[
    'COMPLETE BESS REVENUE MODEL EXPLANATION', '', '', '', '', '', '', '', '', '', '', ''
]])
row += 2

# Battery Specs
ws.update(range_name=f'A{row}:E{row}', values=[['🔋 BATTERY SPECIFICATIONS', '', '', '', '']])
row += 1
ws.update(range_name=f'A{row}:E{row+7}', values=[
    ['Parameter', 'Value', 'Unit', 'Meaning', 'Impact'],
    ['Power Rating', '2.5', 'MW', 'Maximum charge/discharge rate', 'Determines how fast battery operates'],
    ['Energy Capacity', '5.0', 'MWh', 'Total energy storage', 'Determines how much energy stored'],
    ['Roundtrip Efficiency', '88', '%', 'Energy in vs energy out', '12% losses during charge/discharge'],
    ['Duration', '2', 'hours', 'Capacity ÷ Power (5 MWh ÷ 2.5 MW)', 'Can discharge at full power for 2 hours'],
    ['Daily Cycles', '???', 'cycles/day', 'HOW MANY TIMES PER DAY?', '⚠️ CRITICAL: Determines total annual capacity'],
    ['Annual Degradation', '2.5', '%/year', 'Capacity fade', 'Reduces revenue over 15 years'],
    ['', '', '', '', '']
])
row += 9

# The Critical Question
ws.update(range_name=f'A{row}:G{row}', values=[['⚠️ THE CRITICAL QUESTION', '', '', '', '', '', '']])
row += 1
ws.update(range_name=f'A{row}:G{row+6}', values=[
    ['Question', 'Answer', 'Annual Discharge Capacity', 'Current Model Uses', 'Feasible?', 'Impact', ''],
    ['Can battery do 1 cycle/day?', 'YES (standard)', '1,825 MWh/year', '2,170 MWh/year', '❌ NO', 'Model IMPOSSIBLE', ''],
    ['', '', '(365 days × 5 MWh)', '', '', 'Overstates by 19%', ''],
    ['Can battery do 2 cycles/day?', 'MAYBE (intensive)', '3,650 MWh/year', '2,170 MWh/year', '✅ YES', 'Model ACHIEVABLE', ''],
    ['', '', '(365 days × 2 × 5 MWh)', '', '', 'Within capacity', ''],
    ['Can battery do 3+ cycles/day?', 'UNLIKELY (extreme wear)', '5,475+ MWh/year', '2,170 MWh/year', '✅ YES', 'Excess capacity', ''],
    ['', '', '', '', '', '', '']
])
row += 8

# Operating Modes Explained
ws.update(range_name=f'A{row}:H{row}', values=[['📡 OPERATING MODES EXPLAINED', '', '', '', '', '', '', '']])
row += 1
ws.update(range_name=f'A{row}:H{row+12}', values=[
    ['Mode', 'What It Means', 'Payment Type', 'When Active', 'Revenue', 'Discharge?', 'Compatible?', 'Notes'],
    ['', '', '', '', '', '', '', ''],
    ['DC (Dynamic Containment)', 'Hold battery ready for 1-second frequency response', 'Availability', '24/7/365', '£186,150/year', 'Only when grid frequency deviates', 'YES with BM/PPA', 'Pays for being READY, not for actual use'],
    ['', '', '', '8,760 hours/year', '£21.25/hour', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['CM (Capacity Market)', 'Reserve capacity for winter peak demand', 'Availability', 'Winter months', '£112,566/year', 'Only if grid emergency', 'YES with DC/BM/PPA', 'Pays for being AVAILABLE, rarely called'],
    ['', '', '', 'All year contract', '£12.85/hour', '', '', ''],
    ['', '', '', '', '', '', '', ''],
    ['BM (Balancing Mechanism)', 'Discharge when ESO calls to balance grid', 'Utilization', 'When ESO calls', '£91,250/year', 'YES - 2h/day avg', 'YES with DC/CM', 'Pays for ENERGY delivered'],
    ['', '', '', '~730 hours/year', '£25-100/MWh', '', '', 'Actual discharge event'],
    ['', '', '', '', '', '', '', ''],
    ['PPA (Power Purchase)', 'Buy cheap, sell expensive arbitrage', 'Utilization', 'When profitable', '£51,465/year', 'YES - profitable days', 'YES with DC/CM', 'Pays for ENERGY sold'],
    ['', '', '', '~69 days/year', '£150/MWh gross', '', '', 'Actual discharge event']
])
row += 14

# Revenue Model Current
ws.update(range_name=f'A{row}:J{row}', values=[['💰 CURRENT REVENUE MODEL (£502k claimed)', '', '', '', '', '', '', '', '', '']])
row += 1
ws.update(range_name=f'A{row}:J{row+11}', values=[
    ['Revenue Stream', 'Calculation', 'Annual £', '% of Total', 'Type', 'Requires Discharge?', 'MWh Used', 'Hours Used', 'Compatible?', 'Notes'],
    ['', '', '', '', '', '', '', '', '', ''],
    ['DC Availability', '£8.50/MW/h × 2.5 MW × 8,760h', '186,150', '37.1%', 'Baseline', 'NO', '0', '8,760', 'YES', 'Just be ready 24/7'],
    ['CM Availability', '£5.14/MW/h × 2.5 MW × 8,760h', '112,566', '22.4%', 'Baseline', 'NO', '0', '8,760', 'YES', 'Just be available'],
    ['', 'SUBTOTAL BASELINE:', '298,716', '59.5%', '', '', '', '', '', 'These stack - no conflict'],
    ['', '', '', '', '', '', '', '', '', ''],
    ['BM Dispatch', '2.5 MW × 2h × 365 days × £25/MWh', '91,250', '18.2%', 'Utilization', 'YES', '1,825', '730', 'YES', 'Full discharge 2h/day'],
    ['PPA Arbitrage', '5 MWh × 69 days × £150/MWh (gross)', '51,465', '10.2%', 'Utilization', 'YES', '345', '138', 'YES', 'Full cycle 69 days'],
    ['GREEN Savings', '1,825 MWh × £57/MWh saved', '104,591', '20.8%', 'Cost Avoid', 'NO', '0', '0', 'YES', 'Charge GREEN vs RED'],
    ['', 'SUBTOTAL UTILIZATION:', '247,306', '49.2%', '', '', '2,170', '868', '', '⚠️ Requires 2,170 MWh discharge'],
    ['', '', '', '', '', '', '', '', '', ''],
    ['TOTAL GROSS REVENUE', '', '546,022', '108.7%', '', '', '', '', '', '']
])
row += 13

# Costs
ws.update(range_name=f'A{row}:G{row}', values=[['💸 COSTS', '', '', '', '', '', '']])
row += 1
ws.update(range_name=f'A{row}:G{row+7}', values=[
    ['Cost Item', 'Calculation', 'Annual £', '% of Revenue', 'Type', 'Notes', ''],
    ['', '', '', '', '', '', ''],
    ['Electricity Imports', '365 charges × £956/charge', '-348,948', '-69.5%', 'Operating', 'GREEN period charging', ''],
    ['', '(£70 wholesale + £98.15 levies + £0.11 DUoS) × 5.68 MWh', '', '', '', '5.68 = 5.0 ÷ 0.88 efficiency', ''],
    ['', '', '', '', '', '', ''],
    ['OPEX', '5% of gross revenue', '-25,122', '-5.0%', 'Operating', 'Maintenance, insurance, etc', ''],
    ['', '', '', '', '', '', ''],
    ['TOTAL COSTS', '', '-374,070', '-74.5%', '', '', '']
])
row += 9

# Net Profit
ws.update(range_name=f'A{row}:E{row}', values=[['📊 NET PROFIT CALCULATION', '', '', '', '']])
row += 1
ws.update(range_name=f'A{row}:E{row+5}', values=[
    ['Component', 'Amount £', 'Notes', '', ''],
    ['Total Gross Revenue', '546,022', 'All income sources', '', ''],
    ['Total Costs', '-374,070', 'Charging + OPEX', '', ''],
    ['', '', '', '', ''],
    ['NET ANNUAL PROFIT', '171,952', '⚠️ IF 2+ cycles/day possible', '', ''],
    ['', '', '⚠️ IMPOSSIBLE if only 1 cycle/day', '', '']
])
row += 7

# The Physical Constraint Analysis
ws.update(range_name=f'A{row}:I{row}', values=[['🔬 PHYSICAL CONSTRAINT ANALYSIS', '', '', '', '', '', '', '', '']])
row += 1
ws.update(range_name=f'A{row}:I{row+15}', values=[
    ['Scenario', 'Daily Cycles', 'Annual Capacity', 'BM Discharge', 'PPA Discharge', 'Total Used', 'Feasible?', 'Net Profit', 'Comments'],
    ['', '', '', '', '', '', '', '', ''],
    ['CURRENT MODEL', '???', '???', '1,825 MWh', '345 MWh', '2,170 MWh', '???', '£172k', 'Depends on cycle capability'],
    ['Requires:', '', '', '', '', '', '', '', ''],
    ['  • 1 cycle/day', '1.0', '1,825 MWh', '1,825 MWh', '345 MWh', '2,170 MWh', '❌ NO', '—', 'Exceeds by 345 MWh (19%)'],
    ['  • 2 cycles/day', '2.0', '3,650 MWh', '1,825 MWh', '345 MWh', '2,170 MWh', '✅ YES', '£172k', 'Within capacity (60% utilized)'],
    ['  • 3 cycles/day', '3.0', '5,475 MWh', '1,825 MWh', '345 MWh', '2,170 MWh', '✅ YES', '£172k', 'Excess capacity (40% utilized)'],
    ['', '', '', '', '', '', '', '', ''],
    ['ALTERNATIVE IF ONLY 1 CYCLE/DAY:', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', ''],
    ['Scenario A: BM Only', '1.0', '1,825 MWh', '1,825 MWh', '0 MWh', '1,825 MWh', '✅ YES', '£16k', 'All days to BM (low revenue)'],
    ['Scenario B: PPA Priority', '1.0', '1,825 MWh', '1,480 MWh', '345 MWh', '1,825 MWh', '✅ YES', '£51k', '69 days PPA, 296 days BM'],
    ['Scenario C: 50/50 Split', '1.0', '1,825 MWh', '913 MWh', '912 MWh', '1,825 MWh', '✅ YES', '£65k', '183 days each'],
    ['Scenario D: Optimized', '1.0', '1,825 MWh', '~1,100 MWh', '~725 MWh', '1,825 MWh', '✅ YES', '£77k', 'Dynamic allocation by price'],
    ['', '', '', '', '', '', '', '', '']
])
row += 17

# Daily Timeline Examples
ws.update(range_name=f'A{row}:K{row}', values=[['📅 DAILY TIMELINE EXAMPLES', '', '', '', '', '', '', '', '', '', '']])
row += 1
ws.update(range_name=f'A{row}:K{row+25}', values=[
    ['Time', '1 Cycle/Day Model', 'Battery State', 'Action', '', '2 Cycles/Day Model', 'Battery State', 'Action', '', 'Key Difference', ''],
    ['', '', '', '', '', '', '', '', '', '', ''],
    ['00:00-02:00', 'CHARGE (GREEN)', '0 → 5 MWh', 'Import 5.68 MWh @ £168/MWh', '', 'CHARGE #1 (GREEN)', '0 → 5 MWh', 'Import 5.68 MWh', '', 'Same start', ''],
    ['02:00-04:00', 'HOLD (DC/CM ready)', '5 MWh', 'Stand ready for calls', '', 'DISCHARGE #1 (BM)', '5 → 0 MWh', 'ESO call: deliver 5 MWh', '', '← First discharge', ''],
    ['04:00-06:00', 'HOLD (DC/CM ready)', '5 MWh', 'Stand ready', '', 'CHARGE #2', '0 → 5 MWh', 'Import 5.68 MWh again', '', '← Second charge', ''],
    ['06:00-08:00', 'HOLD (DC/CM ready)', '5 MWh', 'Stand ready', '', 'HOLD (DC/CM ready)', '5 MWh', 'Stand ready', '', '', ''],
    ['08:00-10:00', 'HOLD (DC/CM ready)', '5 MWh', 'Stand ready', '', 'HOLD (DC/CM ready)', '5 MWh', 'Stand ready', '', '', ''],
    ['10:00-12:00', 'HOLD (DC/CM ready)', '5 MWh', 'Stand ready', '', 'HOLD (DC/CM ready)', '5 MWh', 'Stand ready', '', '', ''],
    ['12:00-14:00', 'HOLD (DC/CM ready)', '5 MWh', 'Stand ready', '', 'HOLD (DC/CM ready)', '5 MWh', 'Stand ready', '', '', ''],
    ['14:00-16:00', 'HOLD (DC/CM ready)', '5 MWh', 'Stand ready', '', 'HOLD (DC/CM ready)', '5 MWh', 'Stand ready', '', '', ''],
    ['16:00-18:00', 'DISCHARGE (BM)', '5 → 0 MWh', 'ESO call: deliver 5 MWh', '', 'DISCHARGE #2 (PPA)', '5 → 0 MWh', 'Export at high price', '', '← Second discharge', ''],
    ['18:00-20:00', 'EMPTY', '0 MWh', 'Must wait until midnight', '', 'EMPTY', '0 MWh', 'Done for day', '', '', ''],
    ['20:00-22:00', 'EMPTY', '0 MWh', 'Cannot charge (RED period)', '', 'EMPTY', '0 MWh', 'Could charge again?', '', '← Could do 3rd?', ''],
    ['22:00-24:00', 'EMPTY', '0 MWh', 'Wait for GREEN period', '', 'EMPTY', '0 MWh', 'Wait for next day', '', '', ''],
    ['', '', '', '', '', '', '', '', '', '', ''],
    ['DAILY TOTALS:', '', '', '', '', '', '', '', '', '', ''],
    ['Charges', '1', '', '5.68 MWh imported', '', '2', '', '11.36 MWh imported', '', '× 2 charging cost', ''],
    ['Discharges', '1', '', '5 MWh delivered', '', '2', '', '10 MWh delivered', '', '× 2 revenue potential', ''],
    ['Cost', '', '', '£956', '', '', '', '£1,912', '', '× 2 cost', ''],
    ['Revenue (BM only)', '', '', '£125 (5 MWh × £25)', '', '', '', '£250 (10 MWh × £25)', '', '× 2 revenue', ''],
    ['Net (BM only)', '', '', '-£831 loss', '', '', '', '-£1,662 loss', '', 'BM alone unprofitable!', ''],
    ['', '', '', '', '', '', '', '', '', '', ''],
    ['With DC/CM added:', '', '', '+£34/day = -£797', '', '', '', '+£34/day = -£1,628', '', 'Still unprofitable!', ''],
    ['With GREEN savings:', '', '', '+£29/day = -£768', '', '', '', '+£29/day = -£1,599', '', 'Still losing money!', ''],
    ['Need high-value days:', '', '', 'PPA arbitrage', '', '', '', 'BM high prices', '', 'Must maximize utilization revenue', ''],
    ['', '', '', '', '', '', '', '', '', '', '']
])
row += 27

# The Revenue Math Breakdown
ws.update(range_name=f'A{row}:H{row}', values=[['🧮 REVENUE MATH BREAKDOWN', '', '', '', '', '', '', '']])
row += 1
ws.update(range_name=f'A{row}:H{row+20}', values=[
    ['Revenue Source', 'Unit', 'Price', 'Volume/Time', 'Calculation', 'Annual £', 'Requires', 'Notes'],
    ['', '', '', '', '', '', '', ''],
    ['DC Availability', '£/MW/h', '8.50', '2.5 MW × 8,760h', '8.50 × 2.5 × 8,760', '186,150', 'Just be ready', 'Paid every hour you exist'],
    ['', '', '', '', '', '', '', ''],
    ['CM Availability', '£/MW/h', '5.14', '2.5 MW × 8,760h', '5.14 × 2.5 × 8,760', '112,566', 'Just be available', 'Auction-based rate'],
    ['', '', '', '', '', '', '', ''],
    ['BM Revenue (current model)', '£/MWh', '25', '1,825 MWh', '25 × 1,825', '45,625', '1,825 MWh discharge', 'But model claims £91,250!'],
    ['', '', '', '', '', '', '', 'Why? 2× more discharge assumed'],
    ['BM Revenue (if 2 cycles/day)', '£/MWh', '25', '3,650 MWh', '25 × 3,650', '91,250', '3,650 MWh discharge', 'Matches model claim'],
    ['', '', '', '', '', '', '', ''],
    ['PPA Revenue (gross)', '£/MWh', '150', '345 MWh', '150 × 345', '51,750', '345 MWh discharge', 'On 69 profitable days'],
    ['PPA Import Cost', '£/MWh', '-79', '392 MWh', '-79 × 392', '-30,968', '392 MWh import', '345 ÷ 0.88 efficiency'],
    ['PPA Net', '', '', '', '', '20,782', '', 'But model shows £51,465 gross'],
    ['', '', '', '', '', '', '', ''],
    ['GREEN Savings', '£/MWh', '57', '1,825 MWh', '57 × 1,825', '104,025', 'Charge GREEN not RED', 'Cost avoidance, not revenue'],
    ['', '', '', '', '', '', '', '(£168 GREEN vs £226 RED)'],
    ['', '', '', '', '', '', '', ''],
    ['TOTAL if 1 cycle/day:', '', '', '', '', '469,148', '1,825 MWh', 'Original model impossible'],
    ['TOTAL if 2 cycles/day:', '', '', '', '', '514,773', '2,170 MWh', 'Original model achievable'],
    ['', '', '', '', '', '', '', '']
])
row += 22

# The Critical Decision Point
ws.update(range_name=f'A{row}:G{row}', values=[['🎯 THE CRITICAL DECISION POINT', '', '', '', '', '', '']])
row += 1
ws.update(range_name=f'A{row}:G{row+12}', values=[
    ['Question', 'If YES', 'If NO', 'How to Find Out', 'Impact', 'Risk', ''],
    ['', '', '', '', '', '', ''],
    ['Can this battery do', 'Original model is correct', 'Original model overstates', 'Check battery datasheet:', 'Difference of', 'If wrong:', ''],
    ['2+ full cycles per day?', '£502k revenue achievable', 'by £52k/year', '• Daily cycle limit', '£52k/year', 'Investment decision', ''],
    ['', '£172k net profit', 'Only £120k achievable', '• Warranty terms', 'net profit', 'could be wrong', ''],
    ['', '', '', '• Degradation impact', '', '', ''],
    ['', '', '', '', '', '', ''],
    ['Typical industry standard:', '', '', '', '', '', ''],
    ['• 1 cycle/day = standard', '', '', '10-15 year warranty', '', '', ''],
    ['• 2 cycles/day = intensive', '', '', 'Accelerated degradation', '', '', ''],
    ['• 3+ cycles/day = extreme', '', '', 'Warranty may void', '', '', ''],
    ['', '', '', '', '', '', ''],
    ['RECOMMENDATION: Check battery specs BEFORE finalizing financial model', '', '', '', '', '', '']
])
row += 14

# Summary
ws.update(range_name=f'A{row}:F{row}', values=[['📝 SUMMARY', '', '', '', '', '']])
row += 1
ws.update(range_name=f'A{row}:F{row+14}', values=[
    ['Key Point', 'Details', '', '', '', ''],
    ['', '', '', '', '', ''],
    ['1. DC/CM Stack', 'These are AVAILABILITY payments - battery just needs to be ready', '', '', '', ''],
    ['', '£299k/year for being available 24/7', '', '', '', ''],
    ['', 'Can still do BM and PPA while earning DC/CM', '', '', '', ''],
    ['', '', '', '', '', ''],
    ['2. BM/PPA Compete', 'These are UTILIZATION revenues - require actual discharge', '', '', '', ''],
    ['', 'BM: 1,825 MWh claimed (2h/day every day)', '', '', '', ''],
    ['', 'PPA: 345 MWh claimed (69 profitable days)', '', '', '', ''],
    ['', 'Total: 2,170 MWh discharge needed', '', '', '', ''],
    ['', '', '', '', '', ''],
    ['3. Physical Limit', 'Battery capacity: 5 MWh', '', '', '', ''],
    ['', 'If 1 cycle/day: 1,825 MWh/year max → model IMPOSSIBLE', '', '', '', ''],
    ['', 'If 2 cycles/day: 3,650 MWh/year max → model ACHIEVABLE', '', '', '', ''],
    ['4. Action Required', '→ Check battery specification for daily cycle limit', '', '', '', '']
])

print(f"✅ Complete explanation created!")
print(f"📊 View at: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit")
print(f"\nKey sections created:")
print(f"  • Battery specifications")
print(f"  • Operating modes explained")
print(f"  • Revenue model breakdown")
print(f"  • Physical constraints analysis")
print(f"  • Daily timeline comparisons (1 vs 2 cycles)")
print(f"  • Revenue math breakdown")
print(f"  • Critical decision point")
print(f"\n⚠️  ACTION REQUIRED: Check battery datasheet for daily cycle limit!")
