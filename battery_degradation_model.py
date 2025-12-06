#!/usr/bin/env python3
"""
Battery Degradation Modeling
Models capacity fade over 15-year lifetime and impact on revenue
"""

import pandas as pd
import numpy as np

# Battery specs
INITIAL_CAPACITY_MWH = 5.0
INITIAL_POWER_MW = 2.5
LIFETIME_YEARS = 15
ANNUAL_DEGRADATION = 0.025  # 2.5% per year

# Revenue rates (from bess_revenue_stack_analyzer.py)
DC_RATE = 8.50  # £/MW/h
CM_RATE = 5.14  # £/MW/h
BM_RATE = 25.00  # £/MWh
GREEN_SAVING = 104591  # £/year (fixed)
PPA_PROFIT = 23.00  # £/MWh

def calculate_degradation_profile():
    """Calculate capacity and power degradation over lifetime"""
    
    years = np.arange(0, LIFETIME_YEARS + 1)
    
    # Capacity degrades linearly
    capacity_mwh = INITIAL_CAPACITY_MWH * (1 - ANNUAL_DEGRADATION * years)
    
    # Power degrades proportionally (C-rate maintained)
    power_mw = INITIAL_POWER_MW * (1 - ANNUAL_DEGRADATION * years)
    
    return pd.DataFrame({
        'Year': years,
        'Capacity_MWh': capacity_mwh,
        'Power_MW': power_mw,
        'Degradation_%': ANNUAL_DEGRADATION * years * 100
    })

def calculate_revenue_with_degradation():
    """Calculate annual revenue considering degradation"""
    
    degradation = calculate_degradation_profile()
    
    revenues = []
    
    for _, row in degradation.iterrows():
        year = int(row['Year'])
        capacity = row['Capacity_MWh']
        power = row['Power_MW']
        
        # Availability-based revenues (scale with power)
        dc_revenue = DC_RATE * power * 8760
        cm_revenue = CM_RATE * power * 8760
        
        # Utilization-based revenues (scale with capacity)
        bm_revenue = BM_RATE * capacity * 2 * 365  # 2h/day
        ppa_revenue = PPA_PROFIT * capacity * 1 * 365 * 0.188  # 18.8% profitable
        
        # Fixed savings (doesn't degrade)
        green_revenue = GREEN_SAVING
        
        total = dc_revenue + cm_revenue + bm_revenue + ppa_revenue + green_revenue
        
        revenues.append({
            'Year': year,
            'Capacity_MWh': capacity,
            'Power_MW': power,
            'DC_Revenue': dc_revenue,
            'CM_Revenue': cm_revenue,
            'BM_Revenue': bm_revenue,
            'PPA_Revenue': ppa_revenue,
            'Green_Saving': green_revenue,
            'Total_Revenue': total,
            'Revenue_Loss_vs_Year0': 0 if year == 0 else revenues[0]['Total_Revenue'] - total
        })
    
    return pd.DataFrame(revenues)

def calculate_npv_with_degradation(discount_rate=0.08):
    """Calculate NPV considering degradation"""
    
    revenue_df = calculate_revenue_with_degradation()
    
    capex = INITIAL_POWER_MW * 1000 * 400  # £400/kW
    opex_rate = 0.05  # 5% of revenue
    
    cashflows = []
    
    for _, row in revenue_df.iterrows():
        year = int(row['Year'])
        revenue = row['Total_Revenue']
        opex = revenue * opex_rate
        net_cashflow = revenue - opex
        
        if year == 0:
            net_cashflow -= capex
        
        pv = net_cashflow / ((1 + discount_rate) ** year)
        
        cashflows.append({
            'Year': year,
            'Revenue': revenue,
            'OPEX': opex,
            'Net_Cashflow': net_cashflow,
            'PV': pv
        })
    
    cashflow_df = pd.DataFrame(cashflows)
    npv = cashflow_df['PV'].sum()
    
    return npv, cashflow_df

def main():
    print('\n🔋 BATTERY DEGRADATION MODELING')
    print('='*80)
    print(f'Initial: {INITIAL_POWER_MW} MW / {INITIAL_CAPACITY_MWH} MWh')
    print(f'Degradation: {ANNUAL_DEGRADATION*100}% per year')
    print(f'Lifetime: {LIFETIME_YEARS} years')
    print('='*80)
    
    # Degradation profile
    print('\n📉 DEGRADATION PROFILE')
    deg_df = calculate_degradation_profile()
    print(deg_df.to_string(index=False))
    
    # Revenue with degradation
    print('\n\n💰 ANNUAL REVENUE WITH DEGRADATION')
    revenue_df = calculate_revenue_with_degradation()
    
    print(f'\nYear 0 (new): £{revenue_df.iloc[0]["Total_Revenue"]:,.0f}')
    print(f'Year 5: £{revenue_df.iloc[5]["Total_Revenue"]:,.0f} ({revenue_df.iloc[5]["Revenue_Loss_vs_Year0"]:,.0f} loss)')
    print(f'Year 10: £{revenue_df.iloc[10]["Total_Revenue"]:,.0f} ({revenue_df.iloc[10]["Revenue_Loss_vs_Year0"]:,.0f} loss)')
    print(f'Year 15: £{revenue_df.iloc[15]["Total_Revenue"]:,.0f} ({revenue_df.iloc[15]["Revenue_Loss_vs_Year0"]:,.0f} loss)')
    
    # NPV calculation
    print('\n\n💹 NPV WITH DEGRADATION')
    npv, cashflow_df = calculate_npv_with_degradation()
    
    print(f'NPV @ 8% discount: £{npv:,.0f}')
    print(f'Total revenue (15 years): £{revenue_df["Total_Revenue"].sum():,.0f}')
    print(f'Avg annual revenue: £{revenue_df["Total_Revenue"].mean():,.0f}')
    
    # Save results
    revenue_df.to_csv('battery_degradation_analysis.csv', index=False)
    print(f'\n✅ Saved: battery_degradation_analysis.csv')
    
    print('='*80 + '\n')

if __name__ == '__main__':
    main()
