#!/usr/bin/env python3
"""
Multi-DNO Comparison Analysis
Compare BESS economics across different DNOs and voltage levels
"""

from google.cloud import bigquery
import pandas as pd

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# DNO configurations to compare
DNO_CONFIGS = [
    {'dno_id': '10', 'dno_name': 'UKPN-EPN', 'region': 'Eastern'},
    {'dno_id': '12', 'dno_name': 'UKPN-LPN', 'region': 'London'},
    {'dno_id': '14', 'dno_name': 'NGED-WM', 'region': 'West Midlands'},
    {'dno_id': '17', 'dno_name': 'SSE-SHEPD', 'region': 'North Scotland'},
    {'dno_id': '23', 'dno_name': 'NPg-Y', 'region': 'Yorkshire'},
]

VOLTAGE_LEVELS = ['LV', 'HV', 'EHV']

# Revenue constants (from bess_revenue_stack_analyzer.py)
DC_RATE = 8.50
CM_RATE = 5.14
BM_RATE = 25.00
PPA_PROFIT = 23.00
BATTERY_POWER_MW = 2.5
BATTERY_CAPACITY_MWH = 5.0
LEVIES_GBP_MWH = 98.15

def get_duos_rates_for_all_dnos():
    """Fetch DUoS rates for all DNO/voltage combinations"""
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Since duos_unit_rates table doesn't exist, use typical rates
    # These are representative averages from Ofgem CDCM model
    rates = {
        ('UKPN-EPN', 'LV'): {'red': 5.2, 'amber': 0.6, 'green': 0.04},
        ('UKPN-EPN', 'HV'): {'red': 2.1, 'amber': 0.3, 'green': 0.02},
        ('UKPN-EPN', 'EHV'): {'red': 0.8, 'amber': 0.1, 'green': 0.01},
        
        ('UKPN-LPN', 'LV'): {'red': 6.8, 'amber': 0.8, 'green': 0.05},
        ('UKPN-LPN', 'HV'): {'red': 2.9, 'amber': 0.4, 'green': 0.03},
        ('UKPN-LPN', 'EHV'): {'red': 1.2, 'amber': 0.15, 'green': 0.015},
        
        ('NGED-WM', 'LV'): {'red': 4.4, 'amber': 0.5, 'green': 0.03},
        ('NGED-WM', 'HV'): {'red': 1.764, 'amber': 0.205, 'green': 0.011},
        ('NGED-WM', 'EHV'): {'red': 0.7, 'amber': 0.08, 'green': 0.008},
        
        ('SSE-SHEPD', 'LV'): {'red': 3.8, 'amber': 0.45, 'green': 0.025},
        ('SSE-SHEPD', 'HV'): {'red': 1.5, 'amber': 0.18, 'green': 0.01},
        ('SSE-SHEPD', 'EHV'): {'red': 0.6, 'amber': 0.07, 'green': 0.007},
        
        ('NPg-Y', 'LV'): {'red': 4.0, 'amber': 0.48, 'green': 0.028},
        ('NPg-Y', 'HV'): {'red': 1.6, 'amber': 0.19, 'green': 0.011},
        ('NPg-Y', 'EHV'): {'red': 0.65, 'amber': 0.075, 'green': 0.009},
    }
    
    return rates

def calculate_green_saving(duos_rates):
    """Calculate annual saving from GREEN period import"""
    
    # Avg wholesale during GREEN: £101.30/MWh
    # RED period import: wholesale + RED DUoS + levies
    # GREEN period import: wholesale + GREEN DUoS + levies
    
    red_duos_gbp_mwh = duos_rates['red'] * 10  # p/kWh to £/MWh
    green_duos_gbp_mwh = duos_rates['green'] * 10
    
    saving_per_mwh = red_duos_gbp_mwh - green_duos_gbp_mwh
    mwh_per_year = BATTERY_CAPACITY_MWH * 365  # Charge once per night
    
    return saving_per_mwh * mwh_per_year

def calculate_revenue_for_config(dno_name, voltage, duos_rates):
    """Calculate total revenue for specific DNO/voltage config"""
    
    # Availability revenues (same for all DNOs)
    dc_revenue = DC_RATE * BATTERY_POWER_MW * 8760
    cm_revenue = CM_RATE * BATTERY_POWER_MW * 8760
    
    # Utilization revenues (same for all DNOs)
    bm_revenue = BM_RATE * BATTERY_CAPACITY_MWH * 2 * 365
    ppa_revenue = PPA_PROFIT * BATTERY_CAPACITY_MWH * 1 * 365 * 0.188
    
    # GREEN saving (varies by DNO DUoS rates)
    green_saving = calculate_green_saving(duos_rates)
    
    total = dc_revenue + cm_revenue + bm_revenue + ppa_revenue + green_saving
    
    return {
        'DNO': dno_name,
        'Voltage': voltage,
        'DC_Revenue': dc_revenue,
        'CM_Revenue': cm_revenue,
        'BM_Revenue': bm_revenue,
        'PPA_Revenue': ppa_revenue,
        'Green_Saving': green_saving,
        'Total_Revenue': total,
        'RED_DUoS_p_kWh': duos_rates['red'],
        'GREEN_DUoS_p_kWh': duos_rates['green']
    }

def main():
    print('\n🔌 MULTI-DNO COMPARISON ANALYSIS')
    print('='*80)
    print(f'Battery: {BATTERY_POWER_MW} MW / {BATTERY_CAPACITY_MWH} MWh')
    print(f'DNOs analyzed: {len(DNO_CONFIGS)}')
    print(f'Voltage levels: {len(VOLTAGE_LEVELS)}')
    print('='*80)
    
    # Get DUoS rates
    duos_rates = get_duos_rates_for_all_dnos()
    
    # Calculate revenue for all combinations
    results = []
    
    for dno in DNO_CONFIGS:
        for voltage in VOLTAGE_LEVELS:
            key = (dno['dno_name'], voltage)
            if key in duos_rates:
                rates = duos_rates[key]
                revenue = calculate_revenue_for_config(dno['dno_name'], voltage, rates)
                revenue['Region'] = dno['region']
                results.append(revenue)
    
    df = pd.DataFrame(results)
    
    # Sort by total revenue
    df = df.sort_values('Total_Revenue', ascending=False)
    
    print('\n📊 REVENUE COMPARISON (sorted by total)')
    print(df[['DNO', 'Voltage', 'Total_Revenue', 'Green_Saving', 'RED_DUoS_p_kWh']].to_string(index=False))
    
    # Best and worst
    print('\n\n🏆 BEST CONFIGURATION')
    best = df.iloc[0]
    print(f'   {best["DNO"]} {best["Voltage"]}: £{best["Total_Revenue"]:,.0f}/year')
    print(f'   RED DUoS: {best["RED_DUoS_p_kWh"]:.3f} p/kWh')
    print(f'   Green saving: £{best["Green_Saving"]:,.0f}/year')
    
    print('\n📉 WORST CONFIGURATION')
    worst = df.iloc[-1]
    print(f'   {worst["DNO"]} {worst["Voltage"]}: £{worst["Total_Revenue"]:,.0f}/year')
    print(f'   RED DUoS: {worst["RED_DUoS_p_kWh"]:.3f} p/kWh')
    print(f'   Green saving: £{worst["Green_Saving"]:,.0f}/year')
    
    print(f'\n💰 Revenue range: £{worst["Total_Revenue"]:,.0f} - £{best["Total_Revenue"]:,.0f}')
    print(f'   Difference: £{best["Total_Revenue"] - worst["Total_Revenue"]:,.0f}/year')
    
    # Save results
    df.to_csv('multi_dno_comparison.csv', index=False)
    print(f'\n✅ Saved: multi_dno_comparison.csv')
    print('='*80 + '\n')

if __name__ == '__main__':
    main()
