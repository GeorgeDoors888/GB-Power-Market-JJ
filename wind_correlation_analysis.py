#!/usr/bin/env python3
"""
Wind Correlation Analysis
Analyzes correlation between wind generation and prices, frequency response opportunities
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def get_wind_and_price_data(days=90):
    """Fetch wind generation and price data"""
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    WITH wind_data AS (
        SELECT 
            CAST(settlementDate AS DATE) as date,
            settlementPeriod as sp,
            SUM(generation) as total_wind_mw
        FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
        WHERE fuelType = 'WIND'
          AND CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
        GROUP BY date, sp
    ),
    price_data AS (
        SELECT 
            CAST(settlementDate AS DATE) as date,
            settlementPeriod as sp,
            systemSellPrice as ssp,
            systemBuyPrice as sbp
        FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
        WHERE CAST(settlementDate AS DATE) >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    )
    SELECT 
        w.date,
        w.sp,
        w.total_wind_mw,
        p.ssp,
        p.sbp,
        EXTRACT(DAYOFWEEK FROM w.date) as dow,
        EXTRACT(HOUR FROM TIMESTAMP_ADD(CAST(w.date AS TIMESTAMP), INTERVAL (w.sp - 1) * 30 MINUTE)) as hour
    FROM wind_data w
    JOIN price_data p ON w.date = p.date AND w.sp = p.sp
    ORDER BY w.date, w.sp
    """
    
    print(f'   Fetching {days} days of data...')
    df = client.query(query).to_dataframe()
    return df

def calculate_correlations(df):
    """Calculate correlation coefficients"""
    
    correlations = {
        'wind_vs_ssp': df['total_wind_mw'].corr(df['ssp']),
        'wind_vs_sbp': df['total_wind_mw'].corr(df['sbp'])
    }
    
    return correlations

def analyze_by_wind_quantile(df):
    """Analyze prices at different wind generation levels"""
    
    # Define quantiles
    df['wind_quantile'] = pd.qcut(df['total_wind_mw'], q=4, labels=['Low', 'Medium-Low', 'Medium-High', 'High'])
    
    quantile_stats = df.groupby('wind_quantile').agg({
        'total_wind_mw': ['mean', 'min', 'max'],
        'ssp': ['mean', 'min', 'max'],
        'sbp': ['mean']
    }).round(2)
    
    return quantile_stats

def identify_negative_price_events(df):
    """Find periods with negative prices (usually high wind)"""
    
    negative = df[df['ssp'] < 0].copy()
    
    if len(negative) > 0:
        negative = negative.sort_values('ssp')
    
    return negative

def main():
    print('\n🌬️  WIND CORRELATION ANALYSIS')
    print('='*80)
    
    # Fetch data
    print('\n📊 Fetching wind and price data...')
    df = get_wind_and_price_data(days=90)
    
    print(f'   ✅ Retrieved {len(df):,} settlement periods')
    print(f'   Date range: {df["date"].min()} to {df["date"].max()}')
    
    # Overall correlations
    print('\n📈 CORRELATION ANALYSIS')
    corr = calculate_correlations(df)
    print(f'   Wind vs SSP: {corr["wind_vs_ssp"]:.3f}')
    print(f'   Wind vs SBP: {corr["wind_vs_sbp"]:.3f}')
    
    if corr['wind_vs_ssp'] < -0.3:
        print('   ✅ Strong NEGATIVE correlation - high wind = low prices!')
    elif corr['wind_vs_ssp'] < -0.1:
        print('   ⚠️  Moderate negative correlation')
    else:
        print('   ℹ️  Weak or no correlation')
    
    # Quantile analysis
    print('\n📊 PRICE BY WIND GENERATION LEVEL')
    quantile_stats = analyze_by_wind_quantile(df)
    print(quantile_stats.to_string())
    
    # Negative price events
    print('\n⚡ NEGATIVE PRICE EVENTS (High Wind Opportunities)')
    negative = identify_negative_price_events(df)
    
    if len(negative) > 0:
        print(f'   Found {len(negative)} periods with negative prices')
        print(f'   Most negative: £{negative.iloc[0]["ssp"]:.2f}/MWh on {negative.iloc[0]["date"]} SP{negative.iloc[0]["sp"]}')
        print(f'   Avg wind during negative prices: {negative["total_wind_mw"].mean():,.0f} MW')
        print('\n   Top 10 most negative periods:')
        print(negative[['date', 'sp', 'ssp', 'total_wind_mw']].head(10).to_string(index=False))
    else:
        print('   No negative price events in last 90 days')
    
    # High wind insights
    print('\n\n💡 BATTERY OPPORTUNITY INSIGHTS')
    high_wind = df[df['total_wind_mw'] > df['total_wind_mw'].quantile(0.75)]
    low_wind = df[df['total_wind_mw'] < df['total_wind_mw'].quantile(0.25)]
    
    print(f'   High wind (top 25%):')
    print(f'      Avg price: £{high_wind["ssp"].mean():.2f}/MWh')
    charging_opportunities = len(high_wind[high_wind["ssp"] < 60])
    charging_pct = 100 * charging_opportunities / len(high_wind)
    print(f'      Profitable for charging: {charging_opportunities} periods ({charging_pct:.1f}%)')
    
    print(f'   Low wind (bottom 25%):')
    print(f'      Avg price: £{low_wind["ssp"].mean():.2f}/MWh')
    discharge_opportunities = len(low_wind[low_wind["ssp"] > 100])
    discharge_pct = 100 * discharge_opportunities / len(low_wind)
    print(f'      Good for discharging: {discharge_opportunities} periods ({discharge_pct:.1f}%)')
    
    price_diff = low_wind['ssp'].mean() - high_wind['ssp'].mean()
    print(f'\n   Price differential: £{price_diff:.2f}/MWh (charge during high wind, discharge during low wind)')
    
    # Save results
    df.to_csv('wind_price_correlation.csv', index=False)
    print(f'\n✅ Saved: wind_price_correlation.csv')
    print('='*80 + '\n')

if __name__ == '__main__':
    main()
