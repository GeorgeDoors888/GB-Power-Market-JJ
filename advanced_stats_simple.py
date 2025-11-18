#!/usr/bin/env python3
"""
Advanced Statistical Analysis - Simplified Version
Runs faster with better error handling and progress updates
"""

import os
import pathlib
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

from google.cloud import bigquery
from pandas_gbq import to_gbq

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
sns.set_style("whitegrid")

# ==================== CONFIG ====================
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_SOURCE = "uk_energy_prod"
DATASET_ANALYTICS = "uk_energy_analysis"
LOCATION = "US"

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

# Shorter date range for faster testing
DATE_START = "2025-01-01"  # Last 10 months only
DATE_END = "2025-11-01"

OUTDIR = pathlib.Path("./output")
OUTDIR.mkdir(exist_ok=True)

print("\n" + "="*80)
print("🔬 ADVANCED STATISTICAL ANALYSIS - SIMPLIFIED")
print("="*80)
print(f"Date range: {DATE_START} to {DATE_END} (faster)")
print()

# ==================== LOAD DATA ====================
def load_data_simple():
    """Load minimal data for analysis"""
    client = bigquery.Client(project=PROJECT_ID, location=LOCATION)
    
    print("📊 Loading price and volume data...")
    
    # Simpler query - just prices and basic metrics
    query = f"""
    SELECT 
        TIMESTAMP_ADD(TIMESTAMP(settlementDate), INTERVAL (settlementPeriod - 1) * 30 MINUTE) as ts,
        settlementDate as date,
        settlementPeriod as period,
        AVG(CASE WHEN price > 0 THEN price END) as price,
        COUNT(*) as volume
    FROM `{PROJECT_ID}.{DATASET_SOURCE}.bmrs_mid`
    WHERE settlementDate BETWEEN DATE('{DATE_START}') AND DATE('{DATE_END}')
    GROUP BY settlementDate, settlementPeriod
    ORDER BY settlementDate, settlementPeriod
    """
    
    print("   Executing query...")
    df = client.query(query).to_dataframe()
    print(f"✅ Loaded {len(df):,} rows")
    
    if df.empty:
        raise ValueError("No data returned")
    
    # Add calendar features
    print("   Adding calendar features...")
    df['date'] = pd.to_datetime(df['date'])
    df['month'] = df['date'].dt.month
    df['dow'] = df['date'].dt.dayofweek
    df['hour'] = df['ts'].dt.hour
    df['is_weekend'] = df['dow'] >= 5
    
    def season(m):
        if m in (12, 1, 2): return "Winter"
        elif m in (3, 4, 5): return "Spring"
        elif m in (6, 7, 8): return "Summer"
        else: return "Autumn"
    
    df['season'] = df['month'].apply(season)
    
    print(f"   Date range: {df['date'].min()} to {df['date'].max()}")
    print(f"   Price range: £{df['price'].min():.2f} to £{df['price'].max():.2f}/MWh")
    
    return df

# ==================== ANALYSES ====================

def ttest_weekend_weekday(df):
    """T-test: Weekend vs Weekday prices"""
    print("\n1️⃣  T-test: Weekend vs Weekday prices")
    
    weekday = df[~df['is_weekend']]['price'].dropna()
    weekend = df[df['is_weekend']]['price'].dropna()
    
    if len(weekday) < 10 or len(weekend) < 10:
        print("   ⚠️  Not enough data")
        return pd.DataFrame()
    
    t_stat, p_val = stats.ttest_ind(weekday, weekend, equal_var=False)
    
    print(f"   Weekday mean: £{weekday.mean():.2f}/MWh (n={len(weekday):,})")
    print(f"   Weekend mean: £{weekend.mean():.2f}/MWh (n={len(weekend):,})")
    print(f"   Difference: £{weekend.mean() - weekday.mean():.2f}/MWh")
    print(f"   t-statistic: {t_stat:.3f}, p-value: {p_val:.6f}")
    print(f"   {'✅ Significant' if p_val < 0.05 else '❌ Not significant'} (α=0.05)")
    
    return pd.DataFrame([{
        'test': 'Weekend_vs_Weekday',
        'weekday_mean': float(weekday.mean()),
        'weekend_mean': float(weekend.mean()),
        'difference': float(weekend.mean() - weekday.mean()),
        't_stat': float(t_stat),
        'p_value': float(p_val),
        'significant': p_val < 0.05
    }])

def anova_seasonal(df):
    """ANOVA: Seasonal price differences"""
    print("\n2️⃣  ANOVA: Seasonal price differences")
    
    groups = [group['price'].dropna().values for _, group in df.groupby('season')]
    groups = [g for g in groups if len(g) > 10]
    
    if len(groups) < 2:
        print("   ⚠️  Not enough seasonal data")
        return pd.DataFrame()
    
    f_stat, p_val = stats.f_oneway(*groups)
    
    season_means = df.groupby('season')['price'].mean()
    
    print(f"   F-statistic: {f_stat:.3f}, p-value: {p_val:.6f}")
    print(f"   {'✅ Significant' if p_val < 0.05 else '❌ Not significant'} (α=0.05)")
    print("\n   Seasonal means:")
    for season, mean in season_means.items():
        print(f"   {season:8s}: £{mean:.2f}/MWh")
    
    return pd.DataFrame([{
        'f_stat': float(f_stat),
        'p_value': float(p_val),
        'significant': p_val < 0.05,
        **{f"{season.lower()}_mean": float(mean) for season, mean in season_means.items()}
    }])

def correlation_analysis(df):
    """Simple correlation"""
    print("\n3️⃣  Correlation: Price vs Volume")
    
    corr = df[['price', 'volume']].corr().loc['price', 'volume']
    
    print(f"   Correlation: {corr:.3f}")
    print(f"   {'Positive' if corr > 0 else 'Negative'} relationship")
    
    # Simple scatter plot
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(df['volume'], df['price'], alpha=0.3, s=1)
    ax.set_xlabel('Volume (count)')
    ax.set_ylabel('Price (£/MWh)')
    ax.set_title(f'Price vs Volume (r={corr:.3f})')
    ax.grid(True, alpha=0.3)
    
    plot_path = OUTDIR / "price_volume_correlation.png"
    fig.savefig(plot_path, bbox_inches='tight', dpi=150)
    plt.close(fig)
    print(f"   📊 Saved plot: {plot_path}")
    
    return pd.DataFrame([{'correlation': float(corr)}])

def seasonal_boxplot(df):
    """Create seasonal price boxplot"""
    print("\n4️⃣  Seasonal price distribution")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    df.boxplot(column='price', by='season', ax=ax)
    ax.set_xlabel('Season')
    ax.set_ylabel('Price (£/MWh)')
    ax.set_title('Price Distribution by Season')
    plt.suptitle('')  # Remove default title
    ax.grid(True, alpha=0.3)
    
    plot_path = OUTDIR / "seasonal_prices.png"
    fig.savefig(plot_path, bbox_inches='tight', dpi=150)
    plt.close(fig)
    print(f"   📊 Saved plot: {plot_path}")
    
    return pd.DataFrame()

def price_trends(df):
    """Weekly price trends"""
    print("\n5️⃣  Weekly price trends")
    
    # Aggregate by week
    df['week'] = df['date'].dt.to_period('W')
    weekly = df.groupby('week')['price'].agg(['mean', 'std', 'min', 'max']).reset_index()
    weekly['week'] = weekly['week'].dt.to_timestamp()
    
    fig, ax = plt.subplots(figsize=(14, 6))
    ax.plot(weekly['week'], weekly['mean'], linewidth=2, label='Mean')
    ax.fill_between(weekly['week'], 
                     weekly['mean'] - weekly['std'],
                     weekly['mean'] + weekly['std'],
                     alpha=0.2, label='±1 StdDev')
    ax.set_xlabel('Week')
    ax.set_ylabel('Price (£/MWh)')
    ax.set_title('Weekly Price Trends')
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    
    plot_path = OUTDIR / "weekly_trends.png"
    fig.savefig(plot_path, bbox_inches='tight', dpi=150)
    plt.close(fig)
    print(f"   📊 Saved plot: {plot_path}")
    
    print(f"   Avg price: £{weekly['mean'].mean():.2f}/MWh")
    print(f"   Min week: £{weekly['mean'].min():.2f}/MWh")
    print(f"   Max week: £{weekly['mean'].max():.2f}/MWh")
    
    return weekly[['week', 'mean', 'std', 'min', 'max']]

def write_bq(df, table_name):
    """Write to BigQuery"""
    if df.empty:
        print(f"   ⚠️  {table_name}: Empty, skipping")
        return
    
    full_table = f"{PROJECT_ID}.{DATASET_ANALYTICS}.{table_name}"
    
    try:
        to_gbq(df, full_table, project_id=PROJECT_ID, 
               if_exists='replace', location=LOCATION)
        print(f"   ✅ Wrote {len(df)} rows to {table_name}")
    except Exception as e:
        print(f"   ❌ Failed to write {table_name}: {e}")

# ==================== MAIN ====================
def main():
    try:
        # Load data
        df = load_data_simple()
        
        print("\n" + "="*80)
        print("🔬 RUNNING ANALYSES")
        print("="*80)
        
        # Run analyses
        ttest_df = ttest_weekend_weekday(df)
        write_bq(ttest_df, 'ttest_weekend_weekday')
        
        anova_df = anova_seasonal(df)
        write_bq(anova_df, 'anova_seasonal')
        
        corr_df = correlation_analysis(df)
        write_bq(corr_df, 'correlation_price_volume')
        
        seasonal_boxplot(df)
        
        trends_df = price_trends(df)
        write_bq(trends_df, 'weekly_price_trends')
        
        print("\n" + "="*80)
        print("✅ ANALYSIS COMPLETE!")
        print("="*80)
        print(f"\n📊 Outputs:")
        print(f"   BigQuery tables: {PROJECT_ID}.{DATASET_ANALYTICS}.*")
        print(f"   Plots: {OUTDIR}/*.png")
        print()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
