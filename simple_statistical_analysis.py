#!/usr/bin/env python3
"""
Simple Statistical Analysis for GB Power Market
Uses YOUR actual table structure from inner-cinema-476211-u9
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
from scipy import stats
import sys
from datetime import datetime

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
START_DATE = "2025-10-01"
END_DATE = "2025-10-31"

print("=" * 80)
print("📊 GB POWER MARKET STATISTICAL ANALYSIS")
print("=" * 80)
print(f"Project: {PROJECT_ID}")
print(f"Period: {START_DATE} to {END_DATE}")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print()

client = bigquery.Client(project=PROJECT_ID)

# ============================================================================
# 1. BID-OFFER SPREAD ANALYSIS (Battery Arbitrage)
# ============================================================================
print("1️⃣ Analyzing Bid-Offer Spreads (Battery Arbitrage Opportunities)")
print("-" * 80)

try:
    bod_query = f"""
    WITH daily_prices AS (
      SELECT
        settlementDate,
        settlementPeriod,
        AVG(CAST(bid AS FLOAT64)) as avg_bid,
        AVG(CAST(offer AS FLOAT64)) as avg_offer,
        AVG(CAST(offer AS FLOAT64) - CAST(bid AS FLOAT64)) as avg_spread,
        COUNT(DISTINCT bmUnit) as num_units
      FROM `{PROJECT_ID}.{DATASET}.bmrs_bod`
      WHERE settlementDate >= '{START_DATE}'
        AND settlementDate <= '{END_DATE}'
        AND bid IS NOT NULL 
        AND offer IS NOT NULL
        AND CAST(bid AS FLOAT64) > 0
        AND CAST(offer AS FLOAT64) < 9999
      GROUP BY settlementDate, settlementPeriod
    )
    SELECT * FROM daily_prices
    ORDER BY settlementDate, settlementPeriod
    """
    
    df_bod = client.query(bod_query).to_dataframe()
    
    if not df_bod.empty:
        bids = df_bod['avg_bid'].dropna()
        offers = df_bod['avg_offer'].dropna()
        spreads = df_bod['avg_spread'].dropna()
        
        # Paired t-test (same periods)
        if len(bids) > 1 and len(offers) > 1:
            tstat, pval = stats.ttest_rel(bids, offers)
            
            print(f"✅ Data Collected:")
            print(f"   • Settlement Periods: {len(df_bod)}")
            print(f"   • Date Range: {df_bod['settlementDate'].min()} to {df_bod['settlementDate'].max()}")
            print(f"   • Units Analyzed: {df_bod['num_units'].mean():.0f} per period")
            print()
            print(f"📊 Statistical Results:")
            print(f"   • Mean Bid Price:   £{bids.mean():.2f}/MWh  (std: £{bids.std():.2f})")
            print(f"   • Mean Offer Price: £{offers.mean():.2f}/MWh  (std: £{offers.std():.2f})")
            print(f"   • Mean Spread:      £{spreads.mean():.2f}/MWh  (std: £{spreads.std():.2f})")
            print(f"   • T-statistic:      {tstat:.3f}")
            print(f"   • P-value:          {pval:.6f} {'✅ SIGNIFICANT' if pval < 0.05 else '⚠️  not significant'}")
            print()
            print(f"💡 Battery Storage Insights:")
            profitable = (spreads > 5).sum()
            high_profit = (spreads > 10).sum()
            print(f"   • Profitable periods (>£5 spread):  {profitable} ({profitable/len(spreads)*100:.1f}%)")
            print(f"   • High-profit periods (>£10 spread): {high_profit} ({high_profit/len(spreads)*100:.1f}%)")
            print(f"   • Max spread observed: £{spreads.max():.2f}/MWh")
            print(f"   • Min spread observed: £{spreads.min():.2f}/MWh")
    else:
        print("⚠️  No data available for this period")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print()

# ============================================================================
# 2. FREQUENCY STABILITY ANALYSIS
# ============================================================================
print("2️⃣ Analyzing System Frequency (Grid Stability)")
print("-" * 80)

try:
    freq_query = f"""
    WITH freq_stats AS (
      SELECT
        DATE(measurementTime) as date,
        AVG(CAST(frequency AS FLOAT64)) as avg_freq,
        MIN(CAST(frequency AS FLOAT64)) as min_freq,
        MAX(CAST(frequency AS FLOAT64)) as max_freq,
        STDDEV(CAST(frequency AS FLOAT64)) as freq_std,
        COUNTIF(CAST(frequency AS FLOAT64) < 49.8 OR CAST(frequency AS FLOAT64) > 50.2) as out_of_range,
        COUNT(*) as total_readings
      FROM `{PROJECT_ID}.{DATASET}.bmrs_freq`
      WHERE DATE(measurementTime) >= '{START_DATE}'
        AND DATE(measurementTime) <= '{END_DATE}'
        AND frequency IS NOT NULL
      GROUP BY date
    )
    SELECT * FROM freq_stats
    ORDER BY date
    """
    
    df_freq = client.query(freq_query).to_dataframe()
    
    if not df_freq.empty:
        print(f"✅ Data Collected:")
        print(f"   • Days Analyzed: {len(df_freq)}")
        print(f"   • Total Readings: {df_freq['total_readings'].sum():,.0f}")
        print()
        print(f"⚡ Frequency Statistics:")
        print(f"   • Mean Frequency:   {df_freq['avg_freq'].mean():.4f} Hz")
        print(f"   • Overall Std Dev:  {df_freq['freq_std'].mean():.4f} Hz")
        print(f"   • Minimum Recorded: {df_freq['min_freq'].min():.4f} Hz")
        print(f"   • Maximum Recorded: {df_freq['max_freq'].max():.4f} Hz")
        print()
        print(f"📊 Grid Stability Metrics:")
        out_count = df_freq['out_of_range'].sum()
        total_count = df_freq['total_readings'].sum()
        stability = (1 - out_count/total_count) * 100
        print(f"   • In-Range Readings (49.8-50.2 Hz): {stability:.2f}%")
        print(f"   • Out-of-Range Events: {out_count:,.0f}")
        print(f"   • Stability Rating: {'✅ EXCELLENT' if stability > 99 else '✅ GOOD' if stability > 95 else '⚠️  FAIR' if stability > 90 else '❌ POOR'}")
        
        # Day with worst stability
        worst_day = df_freq.loc[df_freq['out_of_range'].idxmax()]
        print(f"   • Worst Day: {worst_day['date']} ({worst_day['out_of_range']} events)")
    else:
        print("⚠️  No frequency data available")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print()

# ============================================================================
# 3. GENERATION MIX ANALYSIS
# ============================================================================
print("3️⃣ Analyzing Generation Mix (Fuel Types)")
print("-" * 80)

try:
    gen_query = f"""
    WITH gen_summary AS (
      SELECT
        fuelType,
        AVG(CAST(generation AS FLOAT64)) as avg_generation,
        MAX(CAST(generation AS FLOAT64)) as peak_generation,
        MIN(CAST(generation AS FLOAT64)) as min_generation,
        COUNT(*) as reading_count
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
      WHERE DATE(publishTime) >= '{START_DATE}'
        AND DATE(publishTime) <= '{END_DATE}'
        AND generation IS NOT NULL
      GROUP BY fuelType
    )
    SELECT * FROM gen_summary
    WHERE avg_generation > 0
    ORDER BY avg_generation DESC
    LIMIT 15
    """
    
    df_gen = client.query(gen_query).to_dataframe()
    
    if not df_gen.empty:
        total_gen = df_gen['avg_generation'].sum()
        print(f"✅ Data Collected:")
        print(f"   • Fuel Types: {len(df_gen)}")
        print(f"   • Total Average Generation: {total_gen:,.0f} MW")
        print()
        print(f"⚡ Top Fuel Types by Average Generation:")
        print(f"   {'Fuel Type':<20} {'Avg MW':>10} {'%':>8} {'Peak MW':>10}")
        print(f"   {'-'*20} {'-'*10} {'-'*8} {'-'*10}")
        
        for idx, row in df_gen.iterrows():
            pct = (row['avg_generation'] / total_gen) * 100
            print(f"   {row['fuelType']:<20} {row['avg_generation']:>10,.0f} {pct:>7.1f}% {row['peak_generation']:>10,.0f}")
        
        # Renewable analysis
        renewable_keywords = ['WIND', 'SOLAR', 'BIOMASS', 'HYDRO']
        renewable_gen = df_gen[df_gen['fuelType'].str.contains('|'.join(renewable_keywords), case=False, na=False)]['avg_generation'].sum()
        renewable_pct = (renewable_gen / total_gen) * 100
        
        print()
        print(f"🌱 Renewable Energy:")
        print(f"   • Renewable Generation: {renewable_gen:,.0f} MW ({renewable_pct:.1f}% of total)")
        print(f"   • Fossil/Other: {total_gen - renewable_gen:,.0f} MW ({100-renewable_pct:.1f}%)")
    else:
        print("⚠️  No generation data available")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print()

# ============================================================================
# 4. DEMAND ANALYSIS
# ============================================================================
print("4️⃣ Analyzing System Demand")
print("-" * 80)

try:
    demand_query = f"""
    WITH demand_summary AS (
      SELECT
        settlementDate,
        settlementPeriod,
        AVG(CAST(initialDemandOutturn AS FLOAT64)) as avg_demand
      FROM `{PROJECT_ID}.{DATASET}.demand_outturn`
      WHERE settlementDate >= '{START_DATE}'
        AND settlementDate <= '{END_DATE}'
        AND initialDemandOutturn IS NOT NULL
      GROUP BY settlementDate, settlementPeriod
    )
    SELECT
      MIN(avg_demand) as min_demand,
      MAX(avg_demand) as max_demand,
      AVG(avg_demand) as overall_avg,
      STDDEV(avg_demand) as std_dev,
      COUNT(*) as periods
    FROM demand_summary
    """
    
    df_demand = client.query(demand_query).to_dataframe()
    
    if not df_demand.empty and df_demand['periods'].iloc[0] > 0:
        row = df_demand.iloc[0]
        print(f"✅ Data Collected:")
        print(f"   • Settlement Periods: {row['periods']:.0f}")
        print()
        print(f"⚡ Demand Statistics:")
        print(f"   • Average Demand: {row['overall_avg']:,.0f} MW")
        print(f"   • Minimum Demand: {row['min_demand']:,.0f} MW")
        print(f"   • Maximum Demand: {row['max_demand']:,.0f} MW")
        print(f"   • Demand Range:   {row['max_demand'] - row['min_demand']:,.0f} MW")
        print(f"   • Std Deviation:  {row['std_dev']:,.0f} MW")
        print()
        print(f"💡 Load Factor: {(row['overall_avg']/row['max_demand'])*100:.1f}%")
    else:
        print("⚠️  No demand data available")
except Exception as e:
    print(f"❌ Error: {str(e)}")

print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("✅ ANALYSIS COMPLETE")
print("=" * 80)
print(f"📅 Period Analyzed: {START_DATE} to {END_DATE}")
print(f"🗂️  Tables Used:")
print(f"   • bmrs_bod (Bid-Offer Data)")
print(f"   • bmrs_freq (System Frequency)")
print(f"   • bmrs_fuelinst (Generation Mix)")
print(f"   • demand_outturn (System Demand)")
print(f"⏱️  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
print("💡 Key Takeaways:")
print("   1. Use bid-offer spreads to identify battery arbitrage windows")
print("   2. Monitor frequency stability for grid health assessment")
print("   3. Track renewable generation percentage for market trends")
print("   4. Analyze demand patterns for forecasting and planning")
print()
print("🚀 Next Steps:")
print("   • Extend date range for longer-term analysis")
print("   • Add price correlation analysis")
print("   • Create forecasting models")
print("   • Export results to dashboard")
print("=" * 80)
