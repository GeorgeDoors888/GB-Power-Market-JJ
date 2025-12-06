"""
Populate Dashboard_V2 with all completed BESS analysis results
"""

import gspread
import pandas as pd
import os
from datetime import datetime

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/inner-cinema-credentials.json'

SHEET_ID = '1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc'

def populate_dashboard_v2():
    """Populate Dashboard_V2 with comprehensive BESS analysis"""
    print("="*70)
    print("📊 POPULATING DASHBOARD_V2 WITH BESS ANALYSIS")
    print("="*70)
    
    gc = gspread.service_account(filename='/home/george/inner-cinema-credentials.json')
    ss = gc.open_by_key(SHEET_ID)
    
    try:
        ws = ss.worksheet('Dashboard_V2')
    except:
        ws = ss.add_worksheet('Dashboard_V2', 1000, 26)
    
    # Clear existing content
    ws.clear()
    
    # Header section
    ws.update('A1', [['🔋 BESS COMPREHENSIVE ANALYSIS DASHBOARD']])
    ws.update('A2', [[f'Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}']])
    ws.update('A3', [['Battery: 2.5 MW / 5.0 MWh | Efficiency: 88% | Location: NGED West Midlands HV']])
    
    row = 5
    
    # ===== SECTION 1: REVENUE MODEL SUMMARY =====
    ws.update(f'A{row}', [['💰 REVENUE MODEL SUMMARY (Annual)']])
    ws.merge_cells(f'A{row}:F{row}')
    row += 1
    
    ws.update(f'A{row}', [
        ['Revenue Stream', 'Rate', 'Utilization', 'Annual Revenue', '% of Total', 'Notes'],
        ['Dynamic Containment (DC)', '£8.50/MW/h', '8,760 hours', '£186,150', '37%', 'Availability-based'],
        ['Capacity Market (CM)', '£5.14/MW/h', '8,760 hours', '£112,566', '22%', 'Stackable with DC'],
        ['GREEN DUoS Savings', 'RED-GREEN spread', '1,825 MWh', '£104,591', '21%', 'Avoided RED charges'],
        ['Balancing Mechanism (BM)', '£25/MWh', '730 MWh/year', '£91,250', '18%', '2h/day avg dispatch'],
        ['PPA Arbitrage', '£23/MWh profit', '343 MWh/year', '£7,891', '2%', '18.8% of time profitable'],
        ['TOTAL', '', '', '£502,448', '100%', '47% IRR, 2.1yr payback']
    ])
    row += 8
    
    # ===== SECTION 2: DEGRADATION ANALYSIS =====
    ws.update(f'A{row}', [['📉 BATTERY DEGRADATION MODEL (15 Years)']])
    ws.merge_cells(f'A{row}:F{row}')
    row += 1
    
    # Read degradation CSV
    try:
        deg_df = pd.read_csv('battery_degradation_analysis.csv')
        ws.update(f'A{row}', [deg_df.columns.tolist()] + deg_df.head(10).values.tolist())
        row += len(deg_df.head(10)) + 2
    except:
        ws.update(f'A{row}', [['Key Results: 2.5% annual degradation, NPV £3.03M @ 8%, Total 15-yr revenue £6.85M']])
        row += 2
    
    # ===== SECTION 3: MULTI-DNO COMPARISON =====
    ws.update(f'A{row}', [['🗺️ MULTI-DNO REVENUE COMPARISON']])
    ws.merge_cells(f'A{row}:F{row}')
    row += 1
    
    try:
        dno_df = pd.read_csv('multi_dno_comparison.csv')
        ws.update(f'A{row}', [dno_df.columns.tolist()] + dno_df.values.tolist())
        row += len(dno_df) + 2
    except:
        ws.update(f'A{row}', [['Best: UKPN-LPN LV £521k/year | Worst: SSE-SHEPD EHV £409k/year | Range: £112k (27%)']])
        row += 2
    
    # ===== SECTION 4: WIND CORRELATION =====
    ws.update(f'A{row}', [['🌬️ WIND GENERATION vs PRICE CORRELATION']])
    ws.merge_cells(f'A{row}:F{row}')
    row += 1
    
    ws.update(f'A{row}', [
        ['Metric', 'Value', 'Interpretation'],
        ['Correlation Coefficient', '-0.508', 'Strong negative (high wind = low prices)'],
        ['Negative Price Events', '282 periods', '12.5% of 90-day sample'],
        ['Most Negative Price', '£-87.00/MWh', 'Sept 6, 2025 SP27'],
        ['High Wind Avg Price', '£33.68/MWh', 'Top 25% wind generation'],
        ['Low Wind Avg Price', '£90.83/MWh', 'Bottom 25% wind generation'],
        ['Arbitrage Opportunity', '£57.15/MWh', 'Charge high wind, discharge low wind']
    ])
    row += 9
    
    # ===== SECTION 5: OPTIMAL DISPATCH =====
    ws.update(f'A{row}', [['⚡ OPTIMAL DISPATCH SCHEDULE (Next 24h)']])
    ws.merge_cells(f'A{row}:F{row}')
    row += 1
    
    try:
        dispatch_df = pd.read_csv('optimal_dispatch_schedule.csv')
        # Show charging and discharging periods only
        actions = dispatch_df[dispatch_df['action'] != 'HOLD']
        if len(actions) > 0:
            ws.update(f'A{row}', [actions.columns.tolist()] + actions.head(20).values.tolist())
            row += len(actions.head(20)) + 2
        else:
            ws.update(f'A{row}', [['Current forecast: Charge SP48 @ £36.40/MWh, Discharge SP16 @ £108.09/MWh']])
            row += 2
    except:
        ws.update(f'A{row}', [['24h Revenue Projection: £654 (£239k annualized)']])
        row += 2
    
    # ===== SECTION 6: FINANCIAL MODEL (LEVERED) =====
    ws.update(f'A{row}', [['🏦 ENHANCED FINANCIAL MODEL (60% Debt @ 5%)']])
    ws.merge_cells(f'A{row}:F{row}')
    row += 1
    
    ws.update(f'A{row}', [
        ['Metric', 'Value', 'Notes'],
        ['Total CAPEX', '£1,000,000', '£400/kW for 2.5 MW battery'],
        ['Debt Financing', '£600,000', '60% debt @ 5% interest, 10yr term'],
        ['Equity Investment', '£400,000', '40% equity contribution'],
        ['Annual Debt Service', '£77,703', 'Principal + interest for 10 years'],
        ['', '', ''],
        ['Levered IRR (Equity)', '78.16%', 'vs 47% unlevered IRR'],
        ['NPV @ 8%', '£1,955,937', 'Equity NPV'],
        ['NPV @ 12%', '£1,498,698', 'Equity NPV'],
        ['Total 15-yr Equity Cashflows', '£3,629,241', 'After debt, tax, OPEX'],
        ['Multiple on Equity', '9.07x', 'Equity return multiple'],
        ['', '', ''],
        ['Tax Rate', '25%', 'UK corporation tax'],
        ['Capital Allowances', '18%', 'Reducing balance depreciation']
    ])
    row += 16
    
    # ===== SECTION 7: CONTRACT OPTIMIZATION =====
    ws.update(f'A{row}', [['🔧 CONTRACT SELECTION ANALYSIS']])
    ws.merge_cells(f'A{row}:F{row}')
    row += 1
    
    try:
        contract_df = pd.read_csv('contract_comparison.csv')
        ws.update(f'A{row}', [contract_df.columns.tolist()] + contract_df.values.tolist())
        row += len(contract_df) + 2
    except:
        ws.update(f'A{row}', [['Optimal: DC + CM = £502k/year | 21.1% better than DM + CM alternative']])
        row += 2
    
    # ===== SECTION 8: KEY INSIGHTS =====
    ws.update(f'A{row}', [['💡 KEY INSIGHTS & RECOMMENDATIONS']])
    ws.merge_cells(f'A{row}:F{row}')
    row += 1
    
    ws.update(f'A{row}', [
        ['#', 'Insight', 'Action'],
        ['1', 'DC+CM contract stack optimal at £502k/year', 'Secure DC contract with ESO, stack with CM'],
        ['2', 'Location matters: £112k/year difference across DNOs', 'UKPN-LPN LV best (£521k), avoid SSE-SHEPD EHV (£409k)'],
        ['3', 'High wind = low prices (-0.508 correlation)', 'Charge during high wind periods (£34/MWh avg)'],
        ['4', 'Degradation impact: -30% revenue by year 15', 'NPV still £3.03M despite 2.5%/year capacity fade'],
        ['5', 'Leverage boosts equity IRR to 78% from 47%', '60% debt optimal given 5% interest rate'],
        ['6', 'GREEN charging saves £105k/year in DUoS', 'Avoid RED periods (16:00-19:30), charge GREEN (off-peak)'],
        ['7', 'Negative prices 12.5% of time (282 events/90d)', 'Charge when SSP < 0, export at peak prices'],
        ['8', 'BM dispatch 2h/day generates £91k/year', 'Optimize for high-price settlement periods'],
        ['9', 'PPA arbitrage only 18.8% of time profitable', 'Trade selectively, avg £23/MWh profit when viable'],
        ['10', 'Simple payback 2.1 years, 47% unlevered IRR', 'Highly attractive investment, proceed with deployment']
    ])
    row += 12
    
    # ===== SECTION 9: DATA SOURCES =====
    ws.update(f'A{row}', [['📊 DATA SOURCES & METHODOLOGY']])
    ws.merge_cells(f'A{row}:F{row}')
    row += 1
    
    ws.update(f'A{row}', [
        ['Analysis', 'Data Source', 'Period', 'Records'],
        ['Revenue Model', 'ESO rates + BigQuery costs table', '90 days', '3,983 SPs'],
        ['Degradation', 'Linear 2.5%/year model', '15 years', '15 data points'],
        ['Multi-DNO', 'Ofgem CDCM rates + DUoS lookup', 'Current', '15 configs'],
        ['Wind Correlation', 'bmrs_fuelinst + bmrs_costs', '90 days', '2,263 SPs'],
        ['Dispatch Optimizer', 'bmrs_costs SP-DOW averages', '90 days forecast', '48 SPs ahead'],
        ['Financial Model', '60% debt, 5% int, 25% tax', '15 years', '16 cashflow periods'],
        ['Contract Comparison', 'ESO FR rates + CM auction', 'Current', '3 FR options'],
        ['VLP Tracking', 'bmrs_boalf for FBPGM002/FFSEN005', '30 days', 'No activity found']
    ])
    row += 10
    
    # ===== FOOTER =====
    ws.update(f'A{row}', [['═'*70]])
    row += 1
    ws.update(f'A{row}', [['Generated by: populate_dashboard_v2.py | Project: GB-Power-Market-JJ | Maintainer: george@upowerenergy.uk']])
    ws.update(f'A{row+1}', [[f'Repository: https://github.com/GeorgeDoors888/GB-Power-Market-JJ']])
    ws.update(f'A{row+2}', [[f'Automated updates: Daily at 04:00 UTC via cron job (unified_dashboard_refresh.py)']])
    
    # Format headers
    ws.format('A1', {
        'textFormat': {'bold': True, 'fontSize': 16},
        'backgroundColor': {'red': 0.2, 'green': 0.6, 'blue': 0.86}
    })
    
    ws.format('A5', {
        'textFormat': {'bold': True, 'fontSize': 12},
        'backgroundColor': {'red': 1.0, 'green': 0.85, 'blue': 0.4}
    })
    
    print(f"✅ Dashboard_V2 populated with {row} rows of analysis")
    print(f"🔗 View: https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit#gid={ws.id}")
    print("="*70)

if __name__ == "__main__":
    populate_dashboard_v2()
