#!/usr/bin/env python3
"""
BESS Revenue Stack Analyzer
Multi-stream revenue optimization: BM + FFR + CM + DCR + PPA
Shows how stacking revenues makes BESS profitable despite PPA-only losses
"""

from google.cloud import bigquery
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import numpy as np

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
SHEET_ID = '1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA'
CREDS_PATH = '/home/george/inner-cinema-credentials.json'

# Battery specs
BATTERY_POWER_MW = 2.5
BATTERY_CAPACITY_MWH = 5.0
ROUNDTRIP_EFFICIENCY = 0.88

# Cost assumptions (NGED West Midlands HV)
DUOS_RATES = {'RED': 17.64, 'AMBER': 2.05, 'GREEN': 0.11}
LEVIES_GBP_MWH = 98.15
PPA_EXPORT_PRICE = 150.0

# Revenue stream assumptions (£/MW/h or £/MWh)
# These are CONSERVATIVE estimates from National Grid ESO contracts
REVENUE_RATES = {
    'Dynamic Containment (DC)': {
        'rate_gbp_mw_h': 8.50,  # £/MW/h (typical clearing price)
        'availability_hours': 24,  # Can provide 24/7
        'description': 'Fast frequency response <1s'
    },
    'Dynamic Regulation (DR)': {
        'rate_gbp_mw_h': 6.00,  # £/MW/h
        'availability_hours': 24,
        'description': 'Frequency regulation ±0.2Hz'
    },
    'Dynamic Moderation (DM)': {
        'rate_gbp_mw_h': 4.50,  # £/MW/h
        'availability_hours': 24,
        'description': 'Frequency support ±0.5Hz'
    },
    'Capacity Market (CM)': {
        'rate_gbp_kw_year': 45.00,  # £/kW/year (2024-2025 clearing)
        'rate_gbp_mw_h': 5.14,  # Annualized: £45/kW/yr ÷ 8760h = £5.14/MW/h
        'availability_hours': 24,
        'description': '4-hour duration, winter availability'
    },
    'Balancing Mechanism (BM)': {
        'rate_gbp_mwh': 25.00,  # £/MWh (avg accepted bid premium over SSP)
        'utilization_hours_per_day': 2,  # Called ~2 hours/day on avg
        'description': 'Grid balancing dispatch'
    },
    'Wholesale Arbitrage (PPA)': {
        'rate_gbp_mwh': 23.00,  # £/MWh profit when trading in profitable periods only
        'utilization_hours_per_day': 1,  # Trade during 18.8% of periods when profitable
        'description': 'Buy low, sell high (only during profitable periods)'
    }
}

def calculate_annual_revenues():
    """Calculate annual revenue from each stream"""
    
    print('\n💰 BESS REVENUE STACK ANALYSIS')
    print('='*80)
    print(f'Battery: {BATTERY_POWER_MW} MW / {BATTERY_CAPACITY_MWH} MWh')
    print(f'Analysis period: 1 year (8,760 hours)')
    print('='*80)
    
    revenues = []
    
    # Frequency response services (DC, DR, DM - mutually exclusive)
    # Battery can only provide ONE at a time, choose highest value
    print('\n⚡ FREQUENCY RESPONSE SERVICES (Mutually Exclusive)')
    print('   Choose highest value:')
    
    fr_services = []
    for service in ['Dynamic Containment (DC)', 'Dynamic Regulation (DR)', 'Dynamic Moderation (DM)']:
        rate = REVENUE_RATES[service]['rate_gbp_mw_h']
        hours = REVENUE_RATES[service]['availability_hours'] * 365
        annual_revenue = rate * BATTERY_POWER_MW * hours
        
        fr_services.append({
            'service': service,
            'rate': rate,
            'annual_revenue': annual_revenue
        })
        
        print(f'   {service}: £{rate:.2f}/MW/h × {BATTERY_POWER_MW} MW × {hours:,}h = £{annual_revenue:,.0f}/year')
    
    # Select best FR service
    best_fr = max(fr_services, key=lambda x: x['annual_revenue'])
    revenues.append({
        'Service': best_fr['service'],
        'Type': 'Availability',
        'Rate': f"£{best_fr['rate']:.2f}/MW/h",
        'Annual Revenue (£)': best_fr['annual_revenue'],
        'Monthly Revenue (£)': best_fr['annual_revenue'] / 12,
        'Notes': REVENUE_RATES[best_fr['service']]['description']
    })
    
    print(f'\n   ✅ SELECTED: {best_fr["service"]} = £{best_fr["annual_revenue"]:,.0f}/year')
    
    # Capacity Market (can stack with FR)
    print('\n🔋 CAPACITY MARKET (Stackable with FR)')
    cm_rate = REVENUE_RATES['Capacity Market (CM)']['rate_gbp_mw_h']
    cm_hours = 8760  # Annual availability
    cm_annual = cm_rate * BATTERY_POWER_MW * cm_hours
    
    print(f'   £{cm_rate:.2f}/MW/h × {BATTERY_POWER_MW} MW × {cm_hours:,}h = £{cm_annual:,.0f}/year')
    
    revenues.append({
        'Service': 'Capacity Market (CM)',
        'Type': 'Availability',
        'Rate': f"£{cm_rate:.2f}/MW/h",
        'Annual Revenue (£)': cm_annual,
        'Monthly Revenue (£)': cm_annual / 12,
        'Notes': REVENUE_RATES['Capacity Market (CM)']['description']
    })
    
    # Balancing Mechanism (utilization-based, stackable)
    print('\n⚖️  BALANCING MECHANISM (Utilization-based, stackable)')
    bm_rate = REVENUE_RATES['Balancing Mechanism (BM)']['rate_gbp_mwh']
    bm_hours_per_day = REVENUE_RATES['Balancing Mechanism (BM)']['utilization_hours_per_day']
    bm_mwh_per_year = BATTERY_CAPACITY_MWH * bm_hours_per_day * 365
    bm_annual = bm_rate * bm_mwh_per_year
    
    print(f'   £{bm_rate:.2f}/MWh × {BATTERY_CAPACITY_MWH} MWh × {bm_hours_per_day}h/day × 365 days = £{bm_annual:,.0f}/year')
    print(f'   (Assumes called {bm_hours_per_day} hours/day on average)')
    
    revenues.append({
        'Service': 'Balancing Mechanism (BM)',
        'Type': 'Utilization',
        'Rate': f"£{bm_rate:.2f}/MWh",
        'Annual Revenue (£)': bm_annual,
        'Monthly Revenue (£)': bm_annual / 12,
        'Notes': REVENUE_RATES['Balancing Mechanism (BM)']['description']
    })
    
    # Wholesale Arbitrage (ONLY trade during profitable periods)
    print('\n📈 WHOLESALE ARBITRAGE (PPA-only, profitable periods)')
    # From analysis: 18.8% of periods are profitable
    # When profitable, avg profit is ~£23/MWh (from GREEN periods analysis)
    # Best periods: SP49-50 midnight have £23.39/MWh avg profit
    ppa_avg_profit_when_profitable = 23.00  # £/MWh conservative estimate
    profitable_fraction = 0.188  # 18.8% of periods
    ppa_hours_per_day = REVENUE_RATES['Wholesale Arbitrage (PPA)']['utilization_hours_per_day']
    ppa_mwh_per_year = BATTERY_CAPACITY_MWH * ppa_hours_per_day * 365 * profitable_fraction
    ppa_annual = ppa_avg_profit_when_profitable * ppa_mwh_per_year
    
    print(f'   £{ppa_avg_profit_when_profitable:.2f}/MWh × {BATTERY_CAPACITY_MWH} MWh × {ppa_hours_per_day}h/day × 365 days × {profitable_fraction:.1%}')
    print(f'   = £{ppa_annual:,.0f}/year (ONLY trade when profitable)')
    
    revenues.append({
        'Service': 'Wholesale Arbitrage (PPA)',
        'Type': 'Utilization',
        'Rate': f"£{ppa_avg_profit_when_profitable:.2f}/MWh",
        'Annual Revenue (£)': ppa_annual,
        'Monthly Revenue (£)': ppa_annual / 12,
        'Notes': f'Trade only during profitable 18.8% of periods (avg profit £{ppa_avg_profit_when_profitable}/MWh)'
    })
    
    return pd.DataFrame(revenues)

def calculate_green_import_opportunity():
    """Calculate revenue from importing during GREEN DUoS periods"""
    
    print('\n\n🌙 GREEN PERIOD IMPORT OPTIMIZATION')
    print('='*80)
    
    # GREEN periods: 00:00-08:00 + 22:00-23:59 (10h weekdays) + All weekend (48h)
    # = (10h × 5 days) + (48h) = 98 hours/week = 5,096 hours/year
    
    green_hours_weekday = 10  # 00:00-08:00 + 22:00-23:59
    green_hours_weekend = 48  # All weekend
    green_hours_per_week = (green_hours_weekday * 5) + green_hours_weekend
    green_hours_per_year = green_hours_per_week * 52
    
    # Average wholesale price during GREEN periods (from our analysis)
    # GREEN band had avg import cost £199.56/MWh, minus DUoS £0.11 and levies £98.15 = £101.30/MWh wholesale
    green_avg_wholesale = 101.30
    
    # Import during cheap GREEN periods, export during expensive periods
    # Assume can charge fully once per night (5 MWh)
    charges_per_year = 365  # Once per night
    mwh_imported = BATTERY_CAPACITY_MWH * charges_per_year
    
    # Cost saving vs RED period import
    red_import_cost = 256.87  # From analysis
    green_import_cost = 199.56  # From analysis
    saving_per_mwh = red_import_cost - green_import_cost
    
    annual_saving = saving_per_mwh * mwh_imported
    
    print(f'GREEN period availability: {green_hours_per_year:,} hours/year')
    print(f'   Weekdays: {green_hours_weekday}h/day × 5 days = 50h/week')
    print(f'   Weekends: 48h/week')
    print(f'   Total: {green_hours_per_week}h/week')
    
    print(f'\nImport cost comparison:')
    print(f'   RED period import: £{red_import_cost:.2f}/MWh')
    print(f'   GREEN period import: £{green_import_cost:.2f}/MWh')
    print(f'   Saving: £{saving_per_mwh:.2f}/MWh')
    
    print(f'\nAnnual import optimization:')
    print(f'   Charges per year: {charges_per_year} (once per night)')
    print(f'   MWh imported: {mwh_imported:,.0f} MWh/year')
    print(f'   Annual saving: £{saving_per_mwh:.2f}/MWh × {mwh_imported:,.0f} MWh = £{annual_saving:,.0f}/year')
    
    return annual_saving

def create_summary_table(revenue_df, green_saving):
    """Create comprehensive summary table"""
    
    print('\n\n📊 COMPREHENSIVE REVENUE STACK SUMMARY')
    print('='*80)
    
    # Total revenue
    total_annual = revenue_df['Annual Revenue (£)'].sum() + green_saving
    
    # Add green saving as a row
    green_row = pd.DataFrame([{
        'Service': 'Green Period Import Optimization',
        'Type': 'Cost Saving',
        'Rate': 'Variable',
        'Annual Revenue (£)': green_saving,
        'Monthly Revenue (£)': green_saving / 12,
        'Notes': 'Import during cheap GREEN periods vs expensive RED'
    }])
    
    full_df = pd.concat([revenue_df, green_row], ignore_index=True)
    
    # Add totals row
    totals_row = pd.DataFrame([{
        'Service': 'TOTAL REVENUE STACK',
        'Type': '',
        'Rate': '',
        'Annual Revenue (£)': total_annual,
        'Monthly Revenue (£)': total_annual / 12,
        'Notes': 'All revenue streams combined'
    }])
    
    full_df = pd.concat([full_df, totals_row], ignore_index=True)
    
    # Print table
    print('\nREVENUE BREAKDOWN:')
    print(full_df.to_string(index=False))
    
    # IRR calculation
    print('\n\n💹 INVESTMENT ANALYSIS')
    print('='*80)
    
    capex = BATTERY_POWER_MW * 1000 * 400  # £400/kW typical BESS cost = £1M for 2.5MW
    opex_annual = total_annual * 0.05  # 5% of revenue (O&M, insurance)
    net_annual = total_annual - opex_annual
    
    print(f'CAPEX (estimated): £{capex:,.0f}')
    print(f'   @ £400/kW × {BATTERY_POWER_MW * 1000} kW')
    
    print(f'\nAnnual Revenue: £{total_annual:,.0f}/year')
    print(f'Annual OPEX (5%): £{opex_annual:,.0f}/year')
    print(f'Net Annual: £{net_annual:,.0f}/year')
    
    simple_payback = capex / net_annual
    print(f'\nSimple Payback: {simple_payback:.1f} years')
    
    # IRR calculation (simple NPV method)
    discount_rate = 0.08  # 8% WACC
    years = 15  # Battery life
    npv = sum([net_annual / ((1 + discount_rate) ** year) for year in range(1, years + 1)]) - capex
    
    print(f'NPV @ 8% discount over {years} years: £{npv:,.0f}')
    
    if npv > 0:
        print(f'✅ PROJECT VIABLE (Positive NPV)')
    else:
        print(f'❌ PROJECT NOT VIABLE (Negative NPV)')
    
    # Estimated IRR (iterative approximation)
    for irr_test in range(1, 50):
        irr = irr_test / 100
        test_npv = sum([net_annual / ((1 + irr) ** year) for year in range(1, years + 1)]) - capex
        if test_npv < 0:
            estimated_irr = (irr_test - 1)
            break
    else:
        estimated_irr = 50
    
    print(f'Estimated IRR: ~{estimated_irr}%')
    
    return full_df

def write_to_google_sheets(revenue_df):
    """Write revenue stack analysis to Google Sheets"""
    
    print('\n\n📝 Writing to Google Sheets...')
    
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(CREDS_PATH, scopes=scope)
    gc = gspread.authorize(creds)
    ss = gc.open_by_key(SHEET_ID)
    
    # Create or get Revenue_Stack sheet
    try:
        rev_sheet = ss.worksheet('BESS_Revenue_Stack')
        rev_sheet.clear()
    except:
        rev_sheet = ss.add_worksheet('BESS_Revenue_Stack', rows=100, cols=15)
    
    # Write header
    rev_sheet.update(values=[['BESS REVENUE STACK ANALYSIS']], range_name='A1')
    rev_sheet.update(values=[[f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}']], range_name='A2')
    rev_sheet.update(values=[[f'Battery: {BATTERY_POWER_MW} MW / {BATTERY_CAPACITY_MWH} MWh']], range_name='A3')
    
    # Write revenue table
    table_data = [revenue_df.columns.tolist()] + revenue_df.values.tolist()
    rev_sheet.update(values=table_data, range_name='A5')
    
    # Format headers
    rev_sheet.format('A1', {'textFormat': {'bold': True, 'fontSize': 14}})
    rev_sheet.format('A5:F5', {
        'textFormat': {'bold': True},
        'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
        'horizontalAlignment': 'CENTER'
    })
    
    # Format totals row
    totals_row = len(table_data) + 4
    rev_sheet.format(f'A{totals_row}:F{totals_row}', {
        'textFormat': {'bold': True, 'fontSize': 12},
        'backgroundColor': {'red': 0.0, 'green': 0.8, 'blue': 0.0}
    })
    
    # Format currency columns
    currency_ranges = [f'D6:E{totals_row}']
    for range_name in currency_ranges:
        rev_sheet.format(range_name, {
            'numberFormat': {'type': 'CURRENCY', 'pattern': '£#,##0.00'}
        })
    
    print(f'   ✅ Written to BESS_Revenue_Stack sheet')
    print(f'   🔗 View: https://docs.google.com/spreadsheets/d/{SHEET_ID}/')

def main():
    # Calculate revenues
    revenue_df = calculate_annual_revenues()
    
    # Calculate green period optimization
    green_saving = calculate_green_import_opportunity()
    
    # Create summary
    full_df = create_summary_table(revenue_df, green_saving)
    
    # Write to sheets
    write_to_google_sheets(full_df)
    
    print('\n✅ Revenue stack analysis complete!')
    print('='*80 + '\n')

if __name__ == '__main__':
    main()
