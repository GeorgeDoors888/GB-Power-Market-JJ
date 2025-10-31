#!/usr/bin/env python3
"""
Enhanced Statistical Analysis for GB Power Market
Includes: Price forecasting, correlations, seasonal patterns, and long-term trends
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
START_DATE = "2024-01-01"  # Extended to 1 year
END_DATE = "2025-10-31"

print("=" * 80)
print("📊 ENHANCED GB POWER MARKET STATISTICAL ANALYSIS")
print("=" * 80)
print(f"Project: {PROJECT_ID}")
print(f"Period: {START_DATE} to {END_DATE} (Extended Range)")
print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print()

client = bigquery.Client(project=PROJECT_ID)

# ============================================================================
# 1. BID-OFFER SPREAD ANALYSIS (Battery Arbitrage)
# ============================================================================
print("1️⃣ Analyzing Bid-Offer Spreads - Extended Period")
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
        # Convert to datetime
        df_bod['date'] = pd.to_datetime(df_bod['settlementDate'])
        df_bod['month'] = df_bod['date'].dt.to_period('M')
        df_bod['quarter'] = df_bod['date'].dt.to_period('Q')
        
        bids = df_bod['avg_bid'].dropna()
        offers = df_bod['avg_offer'].dropna()
        spreads = df_bod['avg_spread'].dropna()
        
        # Overall statistics
        tstat, pval = stats.ttest_rel(bids, offers)
        
        print(f"✅ Data Collected:")
        print(f"   • Settlement Periods: {len(df_bod):,}")
        print(f"   • Date Range: {df_bod['date'].min().date()} to {df_bod['date'].max().date()}")
        print(f"   • Duration: {(df_bod['date'].max() - df_bod['date'].min()).days} days")
        print()
        print(f"📊 Overall Statistical Results:")
        print(f"   • Mean Bid Price:   £{bids.mean():.2f}/MWh  (std: £{bids.std():.2f})")
        print(f"   • Mean Offer Price: £{offers.mean():.2f}/MWh  (std: £{offers.std():.2f})")
        print(f"   • Mean Spread:      £{spreads.mean():.2f}/MWh  (std: £{spreads.std():.2f})")
        print(f"   • T-statistic:      {tstat:.3f}")
        print(f"   • P-value:          {pval:.10f} ✅ HIGHLY SIGNIFICANT")
        
        # Profitability analysis
        print()
        print(f"💰 Battery Storage Profitability:")
        profitable_5 = (spreads > 5).sum()
        profitable_10 = (spreads > 10).sum()
        profitable_20 = (spreads > 20).sum()
        print(f"   • Periods with >£5 spread:  {profitable_5:,} ({profitable_5/len(spreads)*100:.1f}%)")
        print(f"   • Periods with >£10 spread: {profitable_10:,} ({profitable_10/len(spreads)*100:.1f}%)")
        print(f"   • Periods with >£20 spread: {profitable_20:,} ({profitable_20/len(spreads)*100:.1f}%)")
        print(f"   • Max spread observed: £{spreads.max():.2f}/MWh")
        print(f"   • Min spread observed: £{spreads.min():.2f}/MWh")
        
        # Seasonal patterns
        print()
        print(f"📅 Seasonal Pattern Analysis:")
        seasonal = df_bod.groupby(df_bod['date'].dt.month)['avg_spread'].mean().sort_values(ascending=False)
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        print(f"   • Highest spread months:")
        for i, (month, spread) in enumerate(seasonal.head(3).items(), 1):
            print(f"      {i}. {month_names[month-1]}: £{spread:.2f}/MWh")
        print(f"   • Lowest spread months:")
        for i, (month, spread) in enumerate(seasonal.tail(3).items(), 1):
            print(f"      {i}. {month_names[month-1]}: £{spread:.2f}/MWh")
        
        # Monthly trend
        print()
        print(f"📈 Monthly Trend Analysis:")
        monthly = df_bod.groupby('month').agg({
            'avg_spread': 'mean',
            'avg_bid': 'mean',
            'avg_offer': 'mean'
        }).tail(12)  # Last 12 months
        
        print(f"   Last 12 Months Average Spreads:")
        for month, row in monthly.iterrows():
            print(f"      {month}: £{row['avg_spread']:.2f}/MWh (Bid: £{row['avg_bid']:.2f}, Offer: £{row['avg_offer']:.2f})")
        
        # Time of day analysis (EXCLUDE clock change periods 49-50)
        print()
        print(f"⏰ Settlement Period Pattern (Intraday - Normal Days Only):")
        df_normal = df_bod[df_bod['settlementPeriod'] <= 48]  # Exclude clock change periods
        by_period = df_normal.groupby('settlementPeriod')['avg_spread'].mean()
        peak_periods = by_period.nlargest(5)
        off_peak_periods = by_period.nsmallest(5)
        print(f"   • Peak spread periods:")
        for period, spread in peak_periods.items():
            hour = (period - 1) * 0.5
            print(f"      Period {period:2d} ({hour:04.1f}h): £{spread:.2f}/MWh")
        print(f"   • Off-peak spread periods:")
        for period, spread in off_peak_periods.items():
            hour = (period - 1) * 0.5
            print(f"      Period {period:2d} ({hour:04.1f}h): £{spread:.2f}/MWh")
        
        # Show clock change periods separately if they exist
        clock_change_periods = df_bod[df_bod['settlementPeriod'] > 48]
        if not clock_change_periods.empty:
            print()
            print(f"   ⚠️  Clock Change Periods (Oct only - 2 days):")
            for period in [49, 50]:
                period_data = clock_change_periods[clock_change_periods['settlementPeriod'] == period]
                if not period_data.empty:
                    spread = period_data['avg_spread'].mean()
                    dates = period_data['settlementDate'].unique()
                    print(f"      Period {period:2d} (Extra hour): £{spread:.2f}/MWh - occurs on {len(dates)} days only")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

print()

# ============================================================================
# 2. PRICE-DEMAND CORRELATION ANALYSIS
# ============================================================================
print("2️⃣ Price-Demand Correlation Analysis")
print("-" * 80)

try:
    # Note: demand_outturn only has recent data (Sept-Oct 2025)
    # So we limit correlation analysis to the overlapping period
    correlation_query = f"""
    WITH prices AS (
      SELECT
        CAST(settlementDate AS DATE) as date,
        settlementPeriod,
        AVG(CAST(bid AS FLOAT64)) as bid_price,
        AVG(CAST(offer AS FLOAT64)) as offer_price,
        AVG(CAST(offer AS FLOAT64) - CAST(bid AS FLOAT64)) as spread
      FROM `{PROJECT_ID}.{DATASET}.bmrs_bod`
      WHERE settlementDate >= '2025-09-01'  -- Recent period only
        AND settlementDate <= '{END_DATE}'
        AND CAST(bid AS FLOAT64) > 0
        AND CAST(offer AS FLOAT64) < 9999
      GROUP BY date, settlementPeriod
    ),
    demand AS (
      SELECT
        CAST(settlementDate AS DATE) as date,
        settlementPeriod,
        AVG(CAST(initialDemandOutturn AS FLOAT64)) as demand_mw
      FROM `{PROJECT_ID}.{DATASET}.demand_outturn`
      WHERE settlementDate >= '2025-09-01'  -- Recent period only
        AND settlementDate <= '{END_DATE}'
        AND initialDemandOutturn IS NOT NULL
      GROUP BY date, settlementPeriod
    )
    SELECT
      p.date,
      p.settlementPeriod,
      p.bid_price,
      p.offer_price,
      p.spread,
      d.demand_mw
    FROM prices p
    INNER JOIN demand d USING (date, settlementPeriod)
    WHERE p.spread IS NOT NULL
      AND d.demand_mw IS NOT NULL
    ORDER BY p.date, p.settlementPeriod
    """
    
    df_corr = client.query(correlation_query).to_dataframe()
    
    if not df_corr.empty and len(df_corr) > 100:
        # Calculate correlations
        corr_bid_demand = df_corr['bid_price'].corr(df_corr['demand_mw'])
        corr_offer_demand = df_corr['offer_price'].corr(df_corr['demand_mw'])
        corr_spread_demand = df_corr['spread'].corr(df_corr['demand_mw'])
        
        print(f"✅ Data Collected:")
        print(f"   • Matched Periods: {len(df_corr):,}")
        print()
        print(f"🔗 Correlation Coefficients (Pearson):")
        print(f"   • Bid Price ↔ Demand:    {corr_bid_demand:+.3f} {'(Strong)' if abs(corr_bid_demand) > 0.5 else '(Moderate)' if abs(corr_bid_demand) > 0.3 else '(Weak)'}")
        print(f"   • Offer Price ↔ Demand:  {corr_offer_demand:+.3f} {'(Strong)' if abs(corr_offer_demand) > 0.5 else '(Moderate)' if abs(corr_offer_demand) > 0.3 else '(Weak)'}")
        print(f"   • Spread ↔ Demand:       {corr_spread_demand:+.3f} {'(Strong)' if abs(corr_spread_demand) > 0.5 else '(Moderate)' if abs(corr_spread_demand) > 0.3 else '(Weak)'}")
        
        # Linear regression: Spread ~ Demand
        from scipy.stats import linregress
        slope, intercept, r_value, p_value, std_err = linregress(df_corr['demand_mw'], df_corr['spread'])
        
        print()
        print(f"📈 Linear Regression: Spread = f(Demand)")
        print(f"   • Slope:       £{slope:.4f}/MW  (spread change per MW demand)")
        print(f"   • Intercept:   £{intercept:.2f}/MWh")
        print(f"   • R²:          {r_value**2:.4f}  (explains {r_value**2*100:.1f}% of variance)")
        print(f"   • P-value:     {p_value:.6e}")
        print(f"   • Std Error:   {std_err:.6f}")
        
        # Price impact of 1000 MW demand change
        print()
        print(f"💡 Market Impact Insights:")
        impact_1000mw = slope * 1000
        print(f"   • Impact of +1,000 MW demand: £{impact_1000mw:+.2f}/MWh spread change")
        print(f"   • Impact of +5,000 MW demand: £{impact_1000mw*5:+.2f}/MWh spread change")
        
        # Demand quartiles and spreads
        df_corr['demand_quartile'] = pd.qcut(df_corr['demand_mw'], 4, labels=['Q1-Low', 'Q2-Med-Low', 'Q3-Med-High', 'Q4-High'])
        quartile_spreads = df_corr.groupby('demand_quartile')['spread'].agg(['mean', 'std', 'min', 'max', 'count'])
        
        print()
        print(f"📊 Spreads by Demand Quartile:")
        print(f"   {'Quartile':<15} {'Mean':>10} {'Std':>8} {'Min':>8} {'Max':>8} {'Count':>8}")
        print(f"   {'-'*15} {'-'*10} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
        for quartile, row in quartile_spreads.iterrows():
            print(f"   {quartile:<15} £{row['mean']:>8.2f} £{row['std']:>6.2f} £{row['min']:>6.2f} £{row['max']:>6.2f} {row['count']:>8.0f}")
        
    else:
        print("⚠️  Insufficient data for correlation analysis")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

print()

# ============================================================================
# 3. GENERATION MIX - EXTENDED ANALYSIS
# ============================================================================
print("3️⃣ Generation Mix Analysis - Extended Period")
print("-" * 80)

try:
    gen_query = f"""
    WITH gen_summary AS (
      SELECT
        fuelType,
        DATE(publishTime) as date,
        AVG(CAST(generation AS FLOAT64)) as avg_generation,
        MAX(CAST(generation AS FLOAT64)) as peak_generation
      FROM `{PROJECT_ID}.{DATASET}.bmrs_fuelinst`
      WHERE DATE(publishTime) >= '{START_DATE}'
        AND DATE(publishTime) <= '{END_DATE}'
        AND generation IS NOT NULL
      GROUP BY fuelType, date
    ),
    overall_stats AS (
      SELECT
        fuelType,
        AVG(avg_generation) as overall_avg,
        MAX(peak_generation) as overall_peak,
        MIN(avg_generation) as overall_min,
        STDDEV(avg_generation) as std_dev,
        COUNT(*) as days_count
      FROM gen_summary
      GROUP BY fuelType
    )
    SELECT * FROM overall_stats
    WHERE overall_avg > 0
    ORDER BY overall_avg DESC
    """
    
    df_gen = client.query(gen_query).to_dataframe()
    
    if not df_gen.empty:
        total_gen = df_gen['overall_avg'].sum()
        
        print(f"✅ Data Collected:")
        print(f"   • Fuel Types: {len(df_gen)}")
        print(f"   • Days Analyzed: ~{df_gen['days_count'].max():.0f}")
        print(f"   • Total Average Generation: {total_gen:,.0f} MW")
        print()
        print(f"⚡ Fuel Type Statistics (Full Period):")
        print(f"   {'Fuel Type':<15} {'Avg MW':>10} {'%':>7} {'Peak MW':>10} {'Min MW':>9} {'Std':>8}")
        print(f"   {'-'*15} {'-'*10} {'-'*7} {'-'*10} {'-'*9} {'-'*8}")
        
        for idx, row in df_gen.head(15).iterrows():
            pct = (row['overall_avg'] / total_gen) * 100
            print(f"   {row['fuelType']:<15} {row['overall_avg']:>10,.0f} {pct:>6.1f}% {row['overall_peak']:>10,.0f} {row['overall_min']:>9,.0f} {row['std_dev']:>8,.0f}")
        
        # Renewable vs Fossil
        print()
        print(f"🌱 Renewable vs Fossil Analysis:")
        renewable_keywords = ['WIND', 'SOLAR', 'BIOMASS', 'HYDRO', 'NPSHYD']
        df_gen['is_renewable'] = df_gen['fuelType'].str.contains('|'.join(renewable_keywords), case=False, na=False)
        
        renewable_gen = df_gen[df_gen['is_renewable']]['overall_avg'].sum()
        fossil_gen = df_gen[~df_gen['is_renewable']]['overall_avg'].sum()
        renewable_pct = (renewable_gen / total_gen) * 100
        
        print(f"   • Renewable:    {renewable_gen:>10,.0f} MW ({renewable_pct:>5.1f}%)")
        print(f"   • Fossil/Other: {fossil_gen:>10,.0f} MW ({100-renewable_pct:>5.1f}%)")
        
        # Renewable capacity factor
        renewable_rows = df_gen[df_gen['is_renewable']]
        if not renewable_rows.empty:
            avg_renewable_peak = renewable_rows['overall_peak'].sum()
            renewable_cf = (renewable_gen / avg_renewable_peak) * 100 if avg_renewable_peak > 0 else 0
            print(f"   • Renewable Capacity Factor: {renewable_cf:.1f}%")
        
    else:
        print("⚠️  No generation data available")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

print()

# ============================================================================
# 4. DEMAND PATTERN ANALYSIS
# ============================================================================
print("4️⃣ Demand Pattern Analysis - Extended Period")
print("-" * 80)

try:
    demand_query = f"""
    WITH demand_summary AS (
      SELECT
        settlementDate,
        settlementPeriod,
        AVG(CAST(initialDemandOutturn AS FLOAT64)) as demand_mw
      FROM `{PROJECT_ID}.{DATASET}.demand_outturn`
      WHERE settlementDate >= '{START_DATE}'
        AND settlementDate <= '{END_DATE}'
        AND initialDemandOutturn IS NOT NULL
      GROUP BY settlementDate, settlementPeriod
    )
    SELECT
      settlementDate,
      settlementPeriod,
      demand_mw
    FROM demand_summary
    ORDER BY settlementDate, settlementPeriod
    """
    
    df_demand = client.query(demand_query).to_dataframe()
    
    if not df_demand.empty:
        df_demand['date'] = pd.to_datetime(df_demand['settlementDate'])
        df_demand['month'] = df_demand['date'].dt.month
        df_demand['day_of_week'] = df_demand['date'].dt.day_name()
        df_demand['quarter'] = df_demand['date'].dt.quarter
        
        print(f"✅ Data Collected:")
        print(f"   • Settlement Periods: {len(df_demand):,}")
        print(f"   • Date Range: {df_demand['date'].min().date()} to {df_demand['date'].max().date()}")
        print()
        print(f"⚡ Overall Demand Statistics:")
        print(f"   • Average Demand:  {df_demand['demand_mw'].mean():>10,.0f} MW")
        print(f"   • Minimum Demand:  {df_demand['demand_mw'].min():>10,.0f} MW")
        print(f"   • Maximum Demand:  {df_demand['demand_mw'].max():>10,.0f} MW")
        print(f"   • Demand Range:    {df_demand['demand_mw'].max() - df_demand['demand_mw'].min():>10,.0f} MW")
        print(f"   • Std Deviation:   {df_demand['demand_mw'].std():>10,.0f} MW")
        print(f"   • Load Factor:     {(df_demand['demand_mw'].mean()/df_demand['demand_mw'].max())*100:>10.1f}%")
        
        # Seasonal patterns
        print()
        print(f"📅 Seasonal Demand Patterns:")
        seasonal_demand = df_demand.groupby('quarter')['demand_mw'].agg(['mean', 'min', 'max'])
        quarter_names = {1: 'Q1 (Winter)', 2: 'Q2 (Spring)', 3: 'Q3 (Summer)', 4: 'Q4 (Autumn)'}
        for quarter, row in seasonal_demand.iterrows():
            print(f"   • {quarter_names[quarter]}: Avg {row['mean']:,.0f} MW  (Range: {row['min']:,.0f} - {row['max']:,.0f} MW)")
        
        # Day of week patterns
        print()
        print(f"📊 Weekly Demand Pattern:")
        weekly = df_demand.groupby('day_of_week')['demand_mw'].mean()
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekly = weekly.reindex(day_order)
        for day, demand in weekly.items():
            is_weekend = day in ['Saturday', 'Sunday']
            print(f"   • {day:<10}: {demand:>8,.0f} MW {'(Weekend)' if is_weekend else ''}")
        
        # Settlement period patterns
        print()
        print(f"⏰ Intraday Demand Pattern (by Settlement Period):")
        by_period = df_demand.groupby('settlementPeriod')['demand_mw'].mean()
        peak_demand_periods = by_period.nlargest(5)
        low_demand_periods = by_period.nsmallest(5)
        
        print(f"   Peak Demand Periods:")
        for period, demand in peak_demand_periods.items():
            hour = (period - 1) * 0.5
            print(f"      Period {period:2d} ({hour:04.1f}h): {demand:>8,.0f} MW")
        
        print(f"   Low Demand Periods:")
        for period, demand in low_demand_periods.items():
            hour = (period - 1) * 0.5
            print(f"      Period {period:2d} ({hour:04.1f}h): {demand:>8,.0f} MW")
        
    else:
        print("⚠️  No demand data available")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")

print()

# ============================================================================
# 5. PREDICTIVE INSIGHTS
# ============================================================================
print("5️⃣ Simple Predictive Analysis (Moving Averages)")
print("-" * 80)

try:
    # Use spread data for trend analysis
    if 'df_bod' in locals() and not df_bod.empty:
        # Calculate 30-day and 90-day moving averages
        df_bod_daily = df_bod.groupby('date')['avg_spread'].mean().reset_index()
        df_bod_daily = df_bod_daily.sort_values('date')
        df_bod_daily['ma_30'] = df_bod_daily['avg_spread'].rolling(window=30, min_periods=1).mean()
        df_bod_daily['ma_90'] = df_bod_daily['avg_spread'].rolling(window=90, min_periods=1).mean()
        
        # Recent trend
        recent_30_days = df_bod_daily.tail(30)
        current_avg = recent_30_days['avg_spread'].mean()
        ma_30_current = recent_30_days['ma_30'].iloc[-1]
        ma_90_current = df_bod_daily['ma_90'].iloc[-1]
        
        print(f"✅ Trend Analysis (Bid-Offer Spreads):")
        print(f"   • Last 30 days average:   £{current_avg:.2f}/MWh")
        print(f"   • 30-day moving average:  £{ma_30_current:.2f}/MWh")
        print(f"   • 90-day moving average:  £{ma_90_current:.2f}/MWh")
        print()
        
        # Trend direction
        if ma_30_current > ma_90_current:
            trend = "📈 UPWARD"
            implication = "Spreads are increasing - favorable for battery storage"
        elif ma_30_current < ma_90_current:
            trend = "📉 DOWNWARD"
            implication = "Spreads are decreasing - less favorable for battery storage"
        else:
            trend = "➡️  STABLE"
            implication = "Spreads are stable"
        
        print(f"   📊 Trend Direction: {trend}")
        print(f"   💡 Implication: {implication}")
        
        # Volatility
        recent_std = recent_30_days['avg_spread'].std()
        overall_std = df_bod_daily['avg_spread'].std()
        
        print()
        print(f"   📊 Volatility Analysis:")
        print(f"   • Recent (30d) std dev:  £{recent_std:.2f}/MWh")
        print(f"   • Overall std dev:       £{overall_std:.2f}/MWh")
        print(f"   • Volatility status:     {'Higher than average' if recent_std > overall_std else 'Lower than average'}")
        
except Exception as e:
    print(f"⚠️  Could not perform trend analysis: {str(e)}")

print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("✅ ENHANCED ANALYSIS COMPLETE")
print("=" * 80)
print(f"📅 Period Analyzed: {START_DATE} to {END_DATE}")
print(f"📊 Duration: ~{(pd.to_datetime(END_DATE) - pd.to_datetime(START_DATE)).days} days")
print(f"🗂️  Analyses Performed:")
print(f"   1. ✅ Bid-Offer Spread Analysis (Extended + Seasonal)")
print(f"   2. ✅ Price-Demand Correlation Analysis")
print(f"   3. ✅ Generation Mix Analysis (Extended)")
print(f"   4. ✅ Demand Pattern Analysis (Extended)")
print(f"   5. ✅ Predictive Trend Analysis (Moving Averages)")
print(f"⏱️  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()
print("💡 Key Insights:")
print("   • Extended analysis reveals long-term trends and seasonal patterns")
print("   • Price-demand correlations help predict market behavior")
print("   • Moving averages indicate current trend direction")
print("   • Quarterly and daily patterns inform trading strategies")
print()
print("🚀 Recommended Actions:")
print("   1. Use seasonal patterns for long-term battery dispatch planning")
print("   2. Monitor price-demand correlation for real-time decisions")
print("   3. Track moving averages to identify trend changes")
print("   4. Analyze peak demand periods for maximum arbitrage")
print("=" * 80)
