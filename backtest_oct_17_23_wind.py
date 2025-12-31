#!/usr/bin/env python3
"""
Wind Forecast Backtest Analysis - Oct 17-23, 2025
Analyzes wind forecast errors and market correlation during high-wind event
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
from datetime import datetime

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
LOCATION = "US"

# Use available dates (data starts Oct 26, 2025)
BACKTEST_START = '2025-10-26'
BACKTEST_END = '2025-12-30'  # Use all available data

def main():
    print("=" * 70)
    print("Wind Forecast Backtest Analysis: Oct 17-23, 2025")
    print("=" * 70)
    
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    # Query 1: Daily wind forecast metrics
    print("\n📊 Querying daily wind forecast metrics...")
    daily_query = f"""
    SELECT *
    FROM `{PROJECT_ID}.{DATASET}.wind_forecast_error_daily`
    WHERE settlement_date BETWEEN '{BACKTEST_START}' AND '{BACKTEST_END}'
    ORDER BY settlement_date
    """
    
    daily_df = client.query(daily_query).to_dataframe()
    
    print("\n=== Daily Wind Forecast Metrics ===")
    # Use actual column names: bias_mw instead of avg_error_mw
    print(daily_df[['settlement_date', 'wape_percent', 'bias_mw', 
                    'num_large_ramp_misses', 'avg_actual_mw']].to_string(index=False))
    
    print(f"\n📈 Summary ({len(daily_df)} days):")
    print(f"   Average WAPE: {daily_df['wape_percent'].mean():.1f}%")
    print(f"   Average Bias: {daily_df['bias_mw'].mean():.0f} MW")
    print(f"   Total Ramp Misses: {daily_df['num_large_ramp_misses'].sum():.0f}")
    print(f"   Avg Actual Wind: {daily_df['avg_actual_mw'].mean():.0f} MW")
    
    # Query 2: Imbalance prices
    print("\n💰 Querying imbalance prices...")
    price_query = f"""
    SELECT 
        DATE(settlementDate) as date,
        AVG(systemSellPrice) as avg_ssp,
        MIN(systemSellPrice) as min_ssp,
        MAX(systemSellPrice) as max_ssp,
        STDDEV(systemSellPrice) as stddev_ssp
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE DATE(settlementDate) BETWEEN '{BACKTEST_START}' AND '{BACKTEST_END}'
    GROUP BY date
    ORDER BY date
    """
    
    price_df = client.query(price_query).to_dataframe()
    
    print("\n=== Imbalance Prices (SSP) ===")
    print(price_df.to_string(index=False))
    
    print(f"\n💷 Price Summary:")
    print(f"   Average SSP: £{price_df['avg_ssp'].mean():.2f}/MWh")
    print(f"   Max SSP: £{price_df['max_ssp'].max():.2f}/MWh")
    print(f"   Min SSP: £{price_df['min_ssp'].min():.2f}/MWh")
    print(f"   Volatility (avg stddev): £{price_df['stddev_ssp'].mean():.2f}/MWh")
    
    # Query 3: Detailed correlation analysis
    print("\n🔗 Analyzing wind error vs price correlation...")
    correlation_query = f"""
    SELECT
        w.settlement_date,
        w.settlement_period,
        w.error_mw,
        w.abs_error_mw,
        w.forecast_mw,
        w.actual_mw_total,
        c.systemSellPrice as ssp
    FROM `{PROJECT_ID}.{DATASET}.wind_forecast_error_sp` w
    JOIN `{PROJECT_ID}.{DATASET}.bmrs_costs` c
        ON w.settlement_date = DATE(c.settlementDate)
        AND w.settlement_period = c.settlementPeriod
    WHERE w.settlement_date BETWEEN '{BACKTEST_START}' AND '{BACKTEST_END}'
    ORDER BY w.settlement_date, w.settlement_period
    """
    
    corr_df = client.query(correlation_query).to_dataframe()
    
    # Calculate Pearson correlation
    error = corr_df['error_mw'].values
    ssp = corr_df['ssp'].values
    corr = np.corrcoef(error, ssp)[0, 1]
    
    print(f"\n=== Wind Error vs Price Correlation ===")
    print(f"Pearson Correlation: {corr:.3f}")
    print(f"Sample Size: {len(corr_df)} settlement periods")
    
    if corr < -0.2:
        print(f"\n✅ NEGATIVE CORRELATION ({corr:.3f})")
        print("   Interpretation: Wind shortfalls (negative error) → Higher prices")
        print("   Trading Strategy: Discharge batteries when NESO under-forecasts")
    elif corr > 0.2:
        print(f"\n✅ POSITIVE CORRELATION ({corr:.3f})")
        print("   Interpretation: Wind surplus (positive error) → Higher prices")
    else:
        print(f"\n⚠️ WEAK CORRELATION ({corr:.3f})")
        print("   Wind errors do not strongly drive prices during this period")
        print("   Other factors (demand, gas, constraints) may dominate")
    
    # Large error analysis
    print("\n📉 Analyzing large wind errors...")
    
    large_positive = corr_df[corr_df['error_mw'] > 1000]  # Over-forecast
    large_negative = corr_df[corr_df['error_mw'] < -1000]  # Under-forecast
    normal = corr_df[(corr_df['error_mw'] >= -1000) & (corr_df['error_mw'] <= 1000)]
    
    print(f"\nLarge OVER-forecast (>1 GW, actual > forecast):")
    print(f"   Count: {len(large_positive)} periods ({len(large_positive)/len(corr_df)*100:.1f}%)")
    if len(large_positive) > 0:
        print(f"   Avg SSP: £{large_positive['ssp'].mean():.2f}/MWh")
        print(f"   Min SSP: £{large_positive['ssp'].min():.2f}/MWh")
        print(f"   → System LONG (excess wind), prices typically LOW")
    
    print(f"\nLarge UNDER-forecast (<-1 GW, actual < forecast):")
    print(f"   Count: {len(large_negative)} periods ({len(large_negative)/len(corr_df)*100:.1f}%)")
    if len(large_negative) > 0:
        print(f"   Avg SSP: £{large_negative['ssp'].mean():.2f}/MWh")
        print(f"   Max SSP: £{large_negative['ssp'].max():.2f}/MWh")
        print(f"   → System SHORT (wind deficit), prices typically HIGH")
    
    print(f"\nNormal periods (±1 GW):")
    print(f"   Count: {len(normal)} periods ({len(normal)/len(corr_df)*100:.1f}%)")
    print(f"   Avg SSP: £{normal['ssp'].mean():.2f}/MWh")
    
    # Calculate price impact
    if len(large_negative) > 0 and len(normal) > 0:
        price_impact_negative = large_negative['ssp'].mean() - normal['ssp'].mean()
        print(f"\n💰 Price Impact of Wind Shortfall: +£{price_impact_negative:.2f}/MWh")
        
        if price_impact_negative > 10:
            print(f"   ✅ SIGNIFICANT: Wind under-forecast creates trading opportunity")
            print(f"   Strategy: Discharge batteries during forecast misses")
        else:
            print(f"   ⚠️ MODEST: Small price premium for wind errors")
    
    if len(large_positive) > 0 and len(normal) > 0:
        price_impact_positive = large_positive['ssp'].mean() - normal['ssp'].mean()
        print(f"\n💰 Price Impact of Wind Surplus: {price_impact_positive:+.2f}/MWh")
        
        if price_impact_positive < -10:
            print(f"   ✅ SIGNIFICANT: Wind over-forecast depresses prices")
            print(f"   Strategy: Charge batteries during excess wind periods")
    
    # Hour-of-day analysis
    print("\n⏰ Hour-of-Day Analysis...")
    corr_df['hour'] = corr_df['settlement_period'].apply(lambda sp: ((sp - 1) // 2))
    
    hourly_stats = corr_df.groupby('hour').agg({
        'error_mw': 'mean',
        'absolute_error_mw': 'mean',
        'ssp': 'mean'
    }).round(1)
    
    print("\nTop 5 hours by average forecast error:")
    top_error_hours = hourly_stats.nlargest(5, 'absolute_error_mw')
    print(top_error_hours.to_string())
    
    print("\n" + "=" * 70)
    print("✅ BACKTEST ANALYSIS COMPLETE")
    print("=" * 70)
    
    print("\n📋 KEY FINDINGS:")
    print(f"1. NESO forecast accuracy: {daily_df['wape_percent'].mean():.1f}% WAPE")
    print(f"2. Wind-price correlation: {corr:.3f}")
    print(f"3. Large errors occurred in {(len(large_positive) + len(large_negative))/len(corr_df)*100:.1f}% of periods")
    print(f"4. Price volatility: £{price_df['stddev_ssp'].mean():.2f}/MWh average stddev")
    
    print("\n🔬 NEXT STEPS FOR ECMWF VALIDATION:")
    print("1. Download ECMWF archive data for Oct 17-23 (requires historical access)")
    print("2. Compare ECMWF 06z forecast to NESO 06:00 forecast")
    print("3. Measure lead time: When did ECMWF detect wind drops vs NESO?")
    print("4. Calculate precision/recall for >1.5 GW wind drop alerts")
    print("5. Estimate trading value of 4-10 hour early warning")
    
    print("\n📝 ECMWF Historical Data Access:")
    print("   URL: https://www.ecmwf.int/en/forecasts/datasets/archive-datasets")
    print("   Note: Historical ECMWF data requires CDS API key (free registration)")
    print("   Alternative: Use real-time ECMWF from today forward for validation")
    
    return 0

if __name__ == "__main__":
    exit(main())
