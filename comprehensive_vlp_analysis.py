#!/usr/bin/env python3
"""
Comprehensive VLP Revenue Analysis
Queries all available BigQuery data sources for detailed VLP analysis
"""

import pandas as pd
from google.cloud import bigquery
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import json

PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'
VLP_UNITS = ['2__FBPGM001', '2__FBPGM002']

creds = Credentials.from_service_account_file('inner-cinema-credentials.json', scopes=['https://www.googleapis.com/auth/bigquery'])
client = bigquery.Client(project=PROJECT_ID, credentials=creds, location='US')

print("="*100)
print("COMPREHENSIVE VLP REVENUE ANALYSIS - BP GAS MARKETING")
print("="*100)
print()

# Data collection dictionary
analysis_data = {
    'metadata': {
        'analysis_date': datetime.now().isoformat(),
        'vlp_units': VLP_UNITS,
        'vlp_operator': 'BP Gas Marketing Limited',
        'capacity_mw': {'2__FBPGM001': 33.6, '2__FBPGM002': 50.3, 'total': 83.9},
        'analysis_period': '2025-01-01 to 2025-10-31'
    },
    'balancing_actions': {},
    'price_analysis': {},
    'frequency_response': {},
    'generation_data': {},
    'statistical_analysis': {},
    'revenue_breakdown': {}
}

# ==================================================================================
# SECTION 1: DETAILED BALANCING ACTIONS ANALYSIS
# ==================================================================================
print("SECTION 1: BALANCING MECHANISM ACTIONS (bmrs_boalf)")
print("="*100)

boalf_query = f"""
WITH vlp_actions AS (
  SELECT 
    bmUnit,
    CAST(settlementDate AS DATE) as date,
    settlementPeriodFrom as period,
    levelFrom,
    levelTo,
    (levelTo - levelFrom) as mw_change,
    acceptanceNumber,
    CAST(acceptanceTime AS STRING) as acceptance_time,
    EXTRACT(HOUR FROM acceptanceTime) as hour,
    EXTRACT(DAYOFWEEK FROM settlementDate) as day_of_week,
    EXTRACT(MONTH FROM settlementDate) as month
  FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
  WHERE bmUnit IN ('2__FBPGM001', '2__FBPGM002')
    AND settlementDate >= '2025-01-01'
    AND settlementDate <= '2025-10-31'
)
SELECT 
  bmUnit,
  COUNT(*) as total_actions,
  SUM(ABS(mw_change)) as total_mw_traded,
  AVG(ABS(mw_change)) as avg_mw_per_action,
  MAX(ABS(mw_change)) as max_mw_action,
  MIN(ABS(mw_change)) as min_mw_action,
  STDDEV(ABS(mw_change)) as stddev_mw,
  COUNT(DISTINCT date) as trading_days,
  AVG(CASE WHEN hour BETWEEN 7 AND 19 THEN 1 ELSE 0 END) * 100 as pct_daytime_actions,
  AVG(CASE WHEN day_of_week IN (1, 7) THEN 1 ELSE 0 END) * 100 as pct_weekend_actions
FROM vlp_actions
GROUP BY bmUnit
ORDER BY bmUnit
"""

print("Querying balancing actions...")
df_boalf_summary = client.query(boalf_query).to_dataframe()
print(df_boalf_summary.to_string(index=False))
print()

analysis_data['balancing_actions']['summary'] = df_boalf_summary.to_dict('records')

# Get hourly distribution
hourly_query = f"""
SELECT 
  EXTRACT(HOUR FROM acceptanceTime) as hour,
  COUNT(*) as action_count,
  AVG(ABS(levelTo - levelFrom)) as avg_mw
FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
WHERE bmUnit IN ('2__FBPGM001', '2__FBPGM002')
  AND settlementDate >= '2025-01-01'
  AND settlementDate <= '2025-10-31'
GROUP BY hour
ORDER BY hour
"""

print("Analyzing hourly distribution...")
df_hourly = client.query(hourly_query).to_dataframe()
analysis_data['balancing_actions']['hourly_distribution'] = df_hourly.to_dict('records')
print(f"✅ Hourly distribution: Peak hour {df_hourly.loc[df_hourly['action_count'].idxmax(), 'hour']:.0f}:00 ({df_hourly['action_count'].max():.0f} actions)")
print()

# Get monthly trends
monthly_query = f"""
SELECT 
  EXTRACT(MONTH FROM settlementDate) as month,
  FORMAT_DATE('%B', settlementDate) as month_name,
  COUNT(*) as actions,
  SUM(ABS(levelTo - levelFrom)) as total_mw,
  COUNT(DISTINCT bmUnit) as active_units
FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
WHERE bmUnit IN ('2__FBPGM001', '2__FBPGM002')
  AND settlementDate >= '2025-01-01'
  AND settlementDate <= '2025-10-31'
GROUP BY month, month_name
ORDER BY month
"""

print("Analyzing monthly trends...")
df_monthly = client.query(monthly_query).to_dataframe()
analysis_data['balancing_actions']['monthly_trends'] = df_monthly.to_dict('records')
print(df_monthly.to_string(index=False))
print()

# ==================================================================================
# SECTION 2: SYSTEM PRICE CORRELATION ANALYSIS
# ==================================================================================
print("\nSECTION 2: SYSTEM PRICE CORRELATION (bmrs_costs)")
print("="*100)

price_query = f"""
WITH daily_prices AS (
  SELECT 
    CAST(settlementDate AS DATE) as date,
    AVG(systemBuyPrice) as avg_buy,
    AVG(systemSellPrice) as avg_sell,
    MAX(systemSellPrice) as max_sell,
    MIN(systemBuyPrice) as min_buy,
    (MAX(systemSellPrice) - MIN(systemBuyPrice)) as daily_spread,
    STDDEV(systemSellPrice) as price_volatility,
    COUNT(*) as periods
  FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
  WHERE settlementDate >= '2025-01-01'
    AND settlementDate <= '2025-10-31'
    AND systemSellPrice IS NOT NULL
    AND systemBuyPrice IS NOT NULL
  GROUP BY date
),
vlp_action_days AS (
  SELECT 
    CAST(settlementDate AS DATE) as date,
    COUNT(*) as vlp_actions
  FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
  WHERE bmUnit IN ('2__FBPGM001', '2__FBPGM002')
    AND settlementDate >= '2025-01-01'
    AND settlementDate <= '2025-10-31'
  GROUP BY date
)
SELECT 
  dp.*,
  COALESCE(vad.vlp_actions, 0) as vlp_actions
FROM daily_prices dp
LEFT JOIN vlp_action_days vad ON dp.date = vad.date
ORDER BY dp.date
"""

print("Querying system prices and VLP correlations...")
df_prices = client.query(price_query).to_dataframe()

# Calculate correlation
if len(df_prices) > 0:
    correlation = df_prices[['daily_spread', 'vlp_actions']].corr().iloc[0, 1]
    high_spread_days = df_prices[df_prices['daily_spread'] > 100]
    
    print(f"Total Days Analyzed: {len(df_prices)}")
    print(f"Avg Daily Spread: £{df_prices['daily_spread'].mean():.2f}/MWh")
    print(f"Max Daily Spread: £{df_prices['daily_spread'].max():.2f}/MWh on {df_prices.loc[df_prices['daily_spread'].idxmax(), 'date']}")
    print(f"High Spread Days (>£100/MWh): {len(high_spread_days)} days")
    print(f"Correlation (Spread vs VLP Actions): {correlation:.3f}")
    print()
    
    analysis_data['price_analysis'] = {
        'total_days': int(len(df_prices)),
        'avg_daily_spread': float(df_prices['daily_spread'].mean()),
        'max_daily_spread': float(df_prices['daily_spread'].max()),
        'high_spread_days': int(len(high_spread_days)),
        'correlation_spread_actions': float(correlation),
        'high_spread_summary': high_spread_days[['date', 'daily_spread', 'vlp_actions']].head(10).to_dict('records')
    }

# ==================================================================================
# SECTION 3: GENERATION OUTPUT ANALYSIS
# ==================================================================================
print("\nSECTION 3: GENERATION OUTPUT (bmrs_indgen_iris)")
print("="*100)

# Check if VLP units appear in generation data
gen_query = f"""
SELECT 
  dataset as bm_unit,
  COUNT(*) as records,
  SUM(generation) as total_generation_mwh,
  AVG(generation) as avg_generation_mw,
  MAX(generation) as max_generation_mw,
  MIN(CASE WHEN generation > 0 THEN generation END) as min_positive_generation
FROM `{PROJECT_ID}.{DATASET}.bmrs_indgen_iris`
WHERE UPPER(dataset) LIKE '%FBPGM%'
  AND settlementDate >= '2025-01-01'
GROUP BY dataset
ORDER BY total_generation_mwh DESC
"""

print("Querying generation data...")
try:
    df_gen = client.query(gen_query).to_dataframe()
    if len(df_gen) > 0:
        print(df_gen.to_string(index=False))
        analysis_data['generation_data'] = df_gen.to_dict('records')
    else:
        print("⚠️  No generation data found for VLP units (may not report via indgen)")
        analysis_data['generation_data'] = None
except Exception as e:
    print(f"⚠️  Generation query error: {e}")
    analysis_data['generation_data'] = None

print()

# ==================================================================================
# SECTION 4: FREQUENCY RESPONSE ANALYSIS
# ==================================================================================
print("\nSECTION 4: FREQUENCY RESPONSE (bmrs_freq_iris)")
print("="*100)

freq_query = f"""
SELECT 
  AVG(frequency) as avg_frequency,
  MIN(frequency) as min_frequency,
  MAX(frequency) as max_frequency,
  STDDEV(frequency) as frequency_volatility,
  COUNT(CASE WHEN frequency < 49.8 THEN 1 END) as low_freq_events,
  COUNT(CASE WHEN frequency > 50.2 THEN 1 END) as high_freq_events,
  COUNT(*) as total_measurements
FROM `{PROJECT_ID}.{DATASET}.bmrs_freq_iris`
WHERE measurementTime >= TIMESTAMP('2025-11-01')
"""

print("Analyzing grid frequency volatility (FFR opportunity indicator)...")
try:
    df_freq = client.query(freq_query).to_dataframe()
    
    if len(df_freq) > 0 and df_freq.iloc[0]['total_measurements'] > 0:
        stats = df_freq.iloc[0]
        print(f"Recent month (Nov-Dec 2025):")
        print(f"  Avg Frequency: {stats['avg_frequency']:.3f} Hz")
        print(f"  Low Freq Events (<49.8 Hz): {stats['low_freq_events']:.0f}")
        print(f"  High Freq Events (>50.2 Hz): {stats['high_freq_events']:.0f}")
        print(f"  Avg Volatility: {stats['frequency_volatility']:.4f} Hz")
        print()
        
        analysis_data['frequency_response'] = {
            'avg_frequency_hz': float(stats['avg_frequency']),
            'low_freq_events': int(stats['low_freq_events']),
            'high_freq_events': int(stats['high_freq_events']),
            'avg_volatility': float(stats['frequency_volatility']),
            'ffr_opportunity_score': float((stats['low_freq_events'] + stats['high_freq_events']) / stats['total_measurements'] * 100)
        }
    else:
        print("⚠️  No recent frequency data available")
        analysis_data['frequency_response'] = None
except Exception as e:
    print(f"⚠️  Frequency query error: {e}")
    analysis_data['frequency_response'] = None

# ==================================================================================
# SECTION 5: ADVANCED STATISTICAL ANALYSIS
# ==================================================================================
print("\nSECTION 5: STATISTICAL ANALYSIS")
print("="*100)

# Price volatility analysis
volatility_query = f"""
WITH period_prices AS (
  SELECT 
    CAST(settlementDate AS DATE) as date,
    settlementPeriod,
    systemSellPrice,
    systemBuyPrice,
    (systemSellPrice - systemBuyPrice) as spread,
    EXTRACT(HOUR FROM TIMESTAMP(settlementDate)) + (settlementPeriod - 1) * 0.5 as hour_decimal
  FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
  WHERE settlementDate >= '2025-01-01'
    AND settlementDate <= '2025-10-31'
    AND systemSellPrice IS NOT NULL
    AND systemBuyPrice IS NOT NULL
)
SELECT 
  COUNT(*) as total_periods,
  AVG(spread) as avg_spread,
  STDDEV(spread) as stddev_spread,
  APPROX_QUANTILES(spread, 100)[OFFSET(25)] as q25_spread,
  APPROX_QUANTILES(spread, 100)[OFFSET(50)] as median_spread,
  APPROX_QUANTILES(spread, 100)[OFFSET(75)] as q75_spread,
  APPROX_QUANTILES(spread, 100)[OFFSET(95)] as q95_spread,
  COUNT(CASE WHEN spread > 50 THEN 1 END) as high_spread_periods,
  COUNT(CASE WHEN spread > 100 THEN 1 END) as very_high_spread_periods,
  COUNT(CASE WHEN spread < 0 THEN 1 END) as negative_spread_periods
FROM period_prices
"""

print("Calculating price spread statistics...")
df_stats = client.query(volatility_query).to_dataframe()

if len(df_stats) > 0:
    stats = df_stats.iloc[0]
    print(f"Total Settlement Periods: {stats['total_periods']:,.0f}")
    print(f"Average Spread: £{stats['avg_spread']:.2f}/MWh")
    print(f"Std Dev: £{stats['stddev_spread']:.2f}/MWh")
    print(f"Quartiles: Q1=£{stats['q25_spread']:.2f}, Median=£{stats['median_spread']:.2f}, Q3=£{stats['q75_spread']:.2f}")
    print(f"95th Percentile: £{stats['q95_spread']:.2f}/MWh")
    print(f"High Spread Periods (>£50): {stats['high_spread_periods']:,.0f} ({stats['high_spread_periods']/stats['total_periods']*100:.1f}%)")
    print(f"Very High Spread (>£100): {stats['very_high_spread_periods']:,.0f} ({stats['very_high_spread_periods']/stats['total_periods']*100:.1f}%)")
    print()
    
    analysis_data['statistical_analysis'] = {
        'total_periods': int(stats['total_periods']),
        'spread_statistics': {
            'mean': float(stats['avg_spread']),
            'stddev': float(stats['stddev_spread']),
            'q25': float(stats['q25_spread']),
            'median': float(stats['median_spread']),
            'q75': float(stats['q75_spread']),
            'q95': float(stats['q95_spread'])
        },
        'high_opportunity_periods': {
            'above_50': int(stats['high_spread_periods']),
            'above_100': int(stats['very_high_spread_periods']),
            'pct_profitable': float(stats['high_spread_periods']/stats['total_periods']*100)
        }
    }

# ==================================================================================
# SECTION 6: REVENUE CALCULATION (MULTI-STREAM)
# ==================================================================================
print("\nSECTION 6: MULTI-STREAM REVENUE CALCULATION")
print("="*100)

capacity_mw = 83.9
trading_days = int(df_boalf_summary['trading_days'].sum() / len(df_boalf_summary))
total_actions = int(df_boalf_summary['total_actions'].sum())
avg_mw_per_action = float(df_boalf_summary['avg_mw_per_action'].mean())

print(f"VLP Capacity: {capacity_mw} MW")
print(f"Trading Days (2025): {trading_days}")
print(f"Total Actions: {total_actions:,}")
print(f"Avg MW per Action: {avg_mw_per_action:.2f}")
print()

# 1. Energy Arbitrage (2 cycles/day)
cycles_per_day = 2
efficiency = 0.85
annual_mwh = capacity_mw * cycles_per_day * trading_days
arbitrage_margin = float(df_prices['daily_spread'].mean() / 2) if len(df_prices) > 0 else 60
arbitrage_revenue = annual_mwh * arbitrage_margin * efficiency

print(f"1. ENERGY ARBITRAGE:")
print(f"   Annual MWh: {annual_mwh:,.0f}")
print(f"   Margin: £{arbitrage_margin:.2f}/MWh")
print(f"   Revenue: £{arbitrage_revenue:,.0f}/yr")
print()

# 2. Frequency Response (50% capacity)
ffr_capacity = capacity_mw * 0.5
ffr_rate = 15  # £/MW/hr
ffr_revenue = ffr_capacity * ffr_rate * 8760

print(f"2. FREQUENCY RESPONSE (FFR/DCL):")
print(f"   Committed Capacity: {ffr_capacity:.1f} MW")
print(f"   Rate: £{ffr_rate}/MW/hr")
print(f"   Revenue: £{ffr_revenue:,.0f}/yr")
print()

# 3. Dynamic Containment (30% capacity)
dc_capacity = capacity_mw * 0.3
dc_rate = 7
dc_revenue = dc_capacity * dc_rate * 8760

print(f"3. DYNAMIC CONTAINMENT:")
print(f"   Committed Capacity: {dc_capacity:.1f} MW")
print(f"   Rate: £{dc_rate}/MW/hr")
print(f"   Revenue: £{dc_revenue:,.0f}/yr")
print()

# 4. Balancing Mechanism Premiums
bm_premium_per_action = 5  # £/MW per action
bm_revenue = total_actions * avg_mw_per_action * bm_premium_per_action * (365 / 304)

print(f"4. BALANCING MECHANISM PREMIUMS:")
print(f"   Actions: {total_actions:,}")
print(f"   Premium: £{bm_premium_per_action}/MW")
print(f"   Revenue: £{bm_revenue:,.0f}/yr")
print()

# Total
total_revenue = arbitrage_revenue + ffr_revenue + dc_revenue + bm_revenue

print("="*100)
print("TOTAL REVENUE SUMMARY:")
print("="*100)
print(f"Energy Arbitrage:       £{arbitrage_revenue:>12,.0f}/yr  ({arbitrage_revenue/total_revenue*100:>5.1f}%)")
print(f"Frequency Response:     £{ffr_revenue:>12,.0f}/yr  ({ffr_revenue/total_revenue*100:>5.1f}%)")
print(f"Dynamic Containment:    £{dc_revenue:>12,.0f}/yr  ({dc_revenue/total_revenue*100:>5.1f}%)")
print(f"BM Premiums:            £{bm_revenue:>12,.0f}/yr  ({bm_revenue/total_revenue*100:>5.1f}%)")
print("-" * 100)
print(f"TOTAL ANNUAL REVENUE:   £{total_revenue:>12,.0f}/yr")
print(f"Revenue per MW:         £{total_revenue/capacity_mw:>12,.0f}/MW/yr")
print()

analysis_data['revenue_breakdown'] = {
    'arbitrage': {'revenue': float(arbitrage_revenue), 'percentage': float(arbitrage_revenue/total_revenue*100)},
    'ffr': {'revenue': float(ffr_revenue), 'percentage': float(ffr_revenue/total_revenue*100)},
    'dc': {'revenue': float(dc_revenue), 'percentage': float(dc_revenue/total_revenue*100)},
    'bm_premiums': {'revenue': float(bm_revenue), 'percentage': float(bm_revenue/total_revenue*100)},
    'total': {'revenue': float(total_revenue), 'per_mw': float(total_revenue/capacity_mw)}
}

# Investment analysis
capex_per_mw = 500_000
total_capex = capex_per_mw * capacity_mw
payback = total_capex / total_revenue
roi = (total_revenue / total_capex) * 100

print("INVESTMENT ANALYSIS:")
print("="*100)
print(f"CAPEX: £{total_capex:,.0f} (£{capex_per_mw:,}/MW)")
print(f"Payback Period: {payback:.1f} years")
print(f"Annual ROI: {roi:.1f}%")
print(f"NPV (10yr, 8% discount): £{sum([(total_revenue / (1.08**year)) for year in range(1, 11)]) - total_capex:,.0f}")
print()

analysis_data['investment_analysis'] = {
    'capex': float(total_capex),
    'capex_per_mw': float(capex_per_mw),
    'payback_years': float(payback),
    'annual_roi_percent': float(roi),
    'viability': 'VIABLE' if payback < 10 and roi > 10 else 'MARGINAL' if payback < 15 else 'NOT VIABLE'
}

# Save analysis data
print("Saving analysis data...")
with open('vlp_analysis_data.json', 'w') as f:
    json.dump(analysis_data, f, indent=2, default=str)

print("✅ Analysis complete! Data saved to vlp_analysis_data.json")
print()
print("="*100)
