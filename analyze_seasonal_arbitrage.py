#!/usr/bin/env python3
"""
Seasonal Arbitrage Analysis - Full Historical Dataset
Analyzes ALL settlement periods to identify:
- Summer vs Winter profitability
- Monthly patterns
- Time-of-day patterns
- Optimal trading windows
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
from datetime import datetime

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Battery and cost constants
ROUNDTRIP_EFFICIENCY = 0.88
PPA_EXPORT_PRICE = 150.0  # £/MWh
LEVIES_GBP_MWH = 98.15

# DUoS rates (NGED West Midlands HV)
DUOS_RATES = {
    'RED': 17.64,    # £/MWh
    'AMBER': 2.05,
    'GREEN': 0.11
}

def get_all_historical_prices():
    """Fetch ALL historical price data from bmrs_costs"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT 
        CAST(settlementDate AS DATE) as date,
        EXTRACT(YEAR FROM settlementDate) as year,
        EXTRACT(MONTH FROM settlementDate) as month,
        EXTRACT(DAYOFWEEK FROM settlementDate) as dow,
        settlementPeriod as sp,
        systemSellPrice as ssp,
        systemBuyPrice as sbp,
        -- DUoS band logic
        CASE
          WHEN EXTRACT(DAYOFWEEK FROM settlementDate) IN (1,7) THEN 'GREEN'
          WHEN settlementPeriod BETWEEN 33 AND 39 THEN 'RED'
          WHEN settlementPeriod BETWEEN 17 AND 44 THEN 'AMBER'
          ELSE 'GREEN'
        END as duos_band,
        -- Season
        CASE
          WHEN EXTRACT(MONTH FROM settlementDate) IN (12, 1, 2) THEN 'Winter'
          WHEN EXTRACT(MONTH FROM settlementDate) IN (3, 4, 5) THEN 'Spring'
          WHEN EXTRACT(MONTH FROM settlementDate) IN (6, 7, 8) THEN 'Summer'
          ELSE 'Autumn'
        END as season
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE CAST(settlementDate AS DATE) >= '2020-01-01'
      AND CAST(settlementDate AS DATE) < '2025-12-01'
    ORDER BY date, sp
    """
    
    print('\n📊 Fetching ALL historical price data...')
    print(f'   Dataset: {PROJECT_ID}.{DATASET}.bmrs_costs')
    print(f'   Date range: 2020-01-01 to 2025-12-01')
    
    df = client.query(query).to_dataframe()
    
    print(f'   ✅ Retrieved {len(df):,} settlement periods')
    print(f'   Date range: {df["date"].min()} to {df["date"].max()}')
    print(f'   Years: {df["year"].nunique()} ({df["year"].min()}-{df["year"].max()})')
    
    return df

def calculate_arbitrage_profitability(df):
    """Calculate import costs and arbitrage profitability for each period"""
    
    # Map DUoS rates
    df['duos_cost'] = df['duos_band'].map(DUOS_RATES)
    
    # Calculate total import cost
    df['import_cost'] = df['sbp'] + df['duos_cost'] + LEVIES_GBP_MWH
    
    # Export revenue (fixed PPA)
    df['export_revenue'] = PPA_EXPORT_PRICE
    
    # Net profit per MWh (accounting for efficiency)
    df['net_profit_per_mwh'] = (df['export_revenue'] - df['import_cost']) * ROUNDTRIP_EFFICIENCY
    
    # Profitable flag
    df['is_profitable'] = df['net_profit_per_mwh'] > 0
    
    return df

def analyze_seasonal_patterns(df):
    """Analyze profitability by season"""
    
    print('\n' + '='*80)
    print('SEASONAL ARBITRAGE ANALYSIS')
    print('='*80)
    
    # Overall statistics
    total_periods = len(df)
    profitable_periods = df['is_profitable'].sum()
    profitable_pct = 100 * profitable_periods / total_periods
    
    print(f'\n📈 OVERALL STATISTICS')
    print(f'   Total periods: {total_periods:,}')
    print(f'   Profitable periods: {profitable_periods:,} ({profitable_pct:.1f}%)')
    print(f'   Unprofitable periods: {total_periods - profitable_periods:,} ({100-profitable_pct:.1f}%)')
    print(f'   Avg import cost: £{df["import_cost"].mean():.2f}/MWh')
    print(f'   Avg net profit: £{df["net_profit_per_mwh"].mean():.2f}/MWh')
    
    # By season
    print(f'\n🌍 BY SEASON')
    seasonal_stats = df.groupby('season').agg({
        'is_profitable': ['sum', 'count', 'mean'],
        'import_cost': 'mean',
        'sbp': 'mean',
        'net_profit_per_mwh': 'mean'
    }).round(2)
    
    for season in ['Winter', 'Spring', 'Summer', 'Autumn']:
        if season in seasonal_stats.index:
            stats = seasonal_stats.loc[season]
            total = stats[('is_profitable', 'count')]
            profitable = stats[('is_profitable', 'sum')]
            pct = stats[('is_profitable', 'mean')] * 100
            avg_cost = stats[('import_cost', 'mean')]
            avg_wholesale = stats[('sbp', 'mean')]
            avg_profit = stats[('net_profit_per_mwh', 'mean')]
            
            print(f'\n   {season}:')
            print(f'      Profitable: {profitable:,.0f}/{total:,.0f} periods ({pct:.1f}%)')
            print(f'      Avg import cost: £{avg_cost:.2f}/MWh')
            print(f'      Avg wholesale: £{avg_wholesale:.2f}/MWh')
            print(f'      Avg profit: £{avg_profit:.2f}/MWh')
    
    # By year
    print(f'\n📅 BY YEAR')
    yearly_stats = df.groupby('year').agg({
        'is_profitable': ['sum', 'count', 'mean'],
        'import_cost': 'mean',
        'sbp': 'mean',
        'net_profit_per_mwh': 'mean'
    }).round(2)
    
    for year in sorted(df['year'].unique()):
        stats = yearly_stats.loc[year]
        total = stats[('is_profitable', 'count')]
        profitable = stats[('is_profitable', 'sum')]
        pct = stats[('is_profitable', 'mean')] * 100
        avg_cost = stats[('import_cost', 'mean')]
        avg_profit = stats[('net_profit_per_mwh', 'mean')]
        
        print(f'   {year}: {profitable:,.0f}/{total:,.0f} profitable ({pct:.1f}%) | ' +
              f'Avg cost: £{avg_cost:.2f}/MWh | Avg profit: £{avg_profit:.2f}/MWh')
    
    # By month
    print(f'\n📆 BY MONTH (All Years Combined)')
    monthly_stats = df.groupby('month').agg({
        'is_profitable': ['sum', 'count', 'mean'],
        'import_cost': 'mean',
        'sbp': 'mean'
    }).round(2)
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    for month in range(1, 13):
        if month in monthly_stats.index:
            stats = monthly_stats.loc[month]
            total = stats[('is_profitable', 'count')]
            profitable = stats[('is_profitable', 'sum')]
            pct = stats[('is_profitable', 'mean')] * 100
            avg_cost = stats[('import_cost', 'mean')]
            avg_wholesale = stats[('sbp', 'mean')]
            
            print(f'   {month_names[month-1]}: {profitable:,.0f}/{total:,.0f} ({pct:.1f}%) | ' +
                  f'Import: £{avg_cost:.2f} | Wholesale: £{avg_wholesale:.2f}')
    
    # By DUoS band
    print(f'\n⚡ BY DUoS BAND')
    band_stats = df.groupby('duos_band').agg({
        'is_profitable': ['sum', 'count', 'mean'],
        'import_cost': 'mean',
        'net_profit_per_mwh': 'mean'
    }).round(2)
    
    for band in ['GREEN', 'AMBER', 'RED']:
        if band in band_stats.index:
            stats = band_stats.loc[band]
            total = stats[('is_profitable', 'count')]
            profitable = stats[('is_profitable', 'sum')]
            pct = stats[('is_profitable', 'mean')] * 100
            avg_cost = stats[('import_cost', 'mean')]
            avg_profit = stats[('net_profit_per_mwh', 'mean')]
            
            print(f'   {band:6s}: {profitable:,.0f}/{total:,.0f} ({pct:.1f}%) | ' +
                  f'Import: £{avg_cost:.2f} | Profit: £{avg_profit:.2f}')
    
    # Best and worst periods
    print(f'\n💰 TOP 10 MOST PROFITABLE PERIODS')
    top_periods = df.nlargest(10, 'net_profit_per_mwh')[
        ['date', 'sp', 'season', 'duos_band', 'sbp', 'import_cost', 'net_profit_per_mwh']
    ]
    for idx, row in top_periods.iterrows():
        print(f'   {row["date"]} SP{row["sp"]:2d} ({row["season"]:6s}, {row["duos_band"]:5s}): ' +
              f'Wholesale £{row["sbp"]:6.2f} | Import £{row["import_cost"]:6.2f} | ' +
              f'Profit £{row["net_profit_per_mwh"]:6.2f}/MWh')
    
    print(f'\n📉 TOP 10 WORST PERIODS (Highest Losses)')
    worst_periods = df.nsmallest(10, 'net_profit_per_mwh')[
        ['date', 'sp', 'season', 'duos_band', 'sbp', 'import_cost', 'net_profit_per_mwh']
    ]
    for idx, row in worst_periods.iterrows():
        print(f'   {row["date"]} SP{row["sp"]:2d} ({row["season"]:6s}, {row["duos_band"]:5s}): ' +
              f'Wholesale £{row["sbp"]:6.2f} | Import £{row["import_cost"]:6.2f} | ' +
              f'Loss £{row["net_profit_per_mwh"]:6.2f}/MWh')

def analyze_time_of_day_patterns(df):
    """Analyze profitability by settlement period (time of day)"""
    
    print(f'\n\n⏰ TIME-OF-DAY ANALYSIS (Settlement Period)')
    print('='*80)
    
    sp_stats = df.groupby('sp').agg({
        'is_profitable': ['sum', 'count', 'mean'],
        'import_cost': 'mean',
        'sbp': 'mean',
        'net_profit_per_mwh': 'mean'
    }).round(2)
    
    # Convert SP to time
    def sp_to_time(sp):
        hours = (sp - 1) // 2
        minutes = 30 if (sp - 1) % 2 == 1 else 0
        return f'{hours:02d}:{minutes:02d}'
    
    print('\n   Top 10 Most Profitable Settlement Periods:')
    top_sp = sp_stats.sort_values(('net_profit_per_mwh', 'mean'), ascending=False).head(10)
    for sp, stats in top_sp.iterrows():
        pct = stats[('is_profitable', 'mean')] * 100
        avg_profit = stats[('net_profit_per_mwh', 'mean')]
        avg_cost = stats[('import_cost', 'mean')]
        print(f'   SP{sp:2d} ({sp_to_time(sp)}): {pct:.1f}% profitable | ' +
              f'Import: £{avg_cost:.2f} | Profit: £{avg_profit:.2f}')
    
    print('\n   Top 10 Least Profitable Settlement Periods:')
    worst_sp = sp_stats.sort_values(('net_profit_per_mwh', 'mean'), ascending=True).head(10)
    for sp, stats in worst_sp.iterrows():
        pct = stats[('is_profitable', 'mean')] * 100
        avg_profit = stats[('net_profit_per_mwh', 'mean')]
        avg_cost = stats[('import_cost', 'mean')]
        print(f'   SP{sp:2d} ({sp_to_time(sp)}): {pct:.1f}% profitable | ' +
              f'Import: £{avg_cost:.2f} | Loss: £{avg_profit:.2f}')

def main():
    print('\n🔋 COMPREHENSIVE SEASONAL ARBITRAGE ANALYSIS')
    print('='*80)
    print(f'PPA Export Price: £{PPA_EXPORT_PRICE}/MWh')
    print(f'Roundtrip Efficiency: {ROUNDTRIP_EFFICIENCY*100}%')
    print(f'Levies: £{LEVIES_GBP_MWH}/MWh')
    print(f'DUoS Rates (NGED West Midlands HV):')
    print(f'   RED: £{DUOS_RATES["RED"]}/MWh')
    print(f'   AMBER: £{DUOS_RATES["AMBER"]}/MWh')
    print(f'   GREEN: £{DUOS_RATES["GREEN"]}/MWh')
    
    # Fetch data
    df = get_all_historical_prices()
    
    # Calculate profitability
    print('\n💰 Calculating arbitrage profitability...')
    df = calculate_arbitrage_profitability(df)
    
    # Analyze patterns
    analyze_seasonal_patterns(df)
    analyze_time_of_day_patterns(df)
    
    # Save results
    print('\n\n💾 Saving results to CSV...')
    output_file = 'seasonal_arbitrage_analysis.csv'
    
    summary = df.groupby(['year', 'month', 'season']).agg({
        'is_profitable': ['sum', 'count', 'mean'],
        'import_cost': ['mean', 'min', 'max'],
        'sbp': ['mean', 'min', 'max'],
        'net_profit_per_mwh': ['mean', 'min', 'max']
    }).round(2)
    
    summary.to_csv(output_file)
    print(f'   ✅ Saved: {output_file}')
    
    print('\n✅ Analysis complete!')
    print('='*80 + '\n')

if __name__ == '__main__':
    main()
