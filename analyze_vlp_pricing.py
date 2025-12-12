#!/usr/bin/env python3
"""
VLP & Pricing Analysis Script
Analyzes battery arbitrage opportunities, imbalance prices, and wholesale markets
"""

import sys
from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta

PROJECT_ID = 'inner-cinema-476211-u9'
DATASET = 'uk_energy_prod'

def get_price_volatility(client, days=30):
    """Analyze price volatility for arbitrage opportunities"""
    query = f"""
    SELECT 
        DATE(settlementDate) as date,
        MIN(systemSellPrice) as min_price,
        MAX(systemSellPrice) as max_price,
        AVG(systemSellPrice) as avg_price,
        STDDEV(systemSellPrice) as std_dev,
        MAX(systemSellPrice) - MIN(systemSellPrice) as daily_spread,
        COUNT(*) as periods
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    GROUP BY date
    ORDER BY date DESC
    """
    
    df = client.query(query).to_dataframe()
    return df

def get_imbalance_vs_wholesale(client, days=7):
    """Compare imbalance prices to wholesale for arbitrage premium"""
    query = f"""
    WITH imbalance AS (
        SELECT 
            settlementDate,
            settlementPeriod,
            systemSellPrice as imbalance_price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    ),
    wholesale AS (
        SELECT 
            settlementDate,
            settlementPeriod,
            AVG(price) as wholesale_price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_mid_iris`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
        GROUP BY settlementDate, settlementPeriod
    )
    SELECT 
        i.settlementDate,
        i.settlementPeriod,
        i.imbalance_price,
        w.wholesale_price,
        i.imbalance_price - COALESCE(w.wholesale_price, i.imbalance_price) as premium
    FROM imbalance i
    LEFT JOIN wholesale w
        ON i.settlementDate = w.settlementDate
        AND i.settlementPeriod = w.settlementPeriod
    ORDER BY i.settlementDate DESC, i.settlementPeriod DESC
    """
    
    df = client.query(query).to_dataframe()
    return df

def get_high_price_periods(client, threshold=100, days=30):
    """Find high-price periods (discharge opportunities)"""
    query = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        systemSellPrice as price,
        netImbalanceVolume as niv,
        CASE 
            WHEN EXTRACT(HOUR FROM settlementDate) + (settlementPeriod - 1) * 0.5 BETWEEN 16 AND 19 THEN 'Peak'
            WHEN EXTRACT(HOUR FROM settlementDate) + (settlementPeriod - 1) * 0.5 BETWEEN 0 AND 7 THEN 'Night'
            ELSE 'Day'
        END as time_period
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
      AND systemSellPrice >= {threshold}
    ORDER BY systemSellPrice DESC
    LIMIT 50
    """
    
    df = client.query(query).to_dataframe()
    return df

def get_low_price_periods(client, threshold=30, days=30):
    """Find low-price periods (charge opportunities)"""
    query = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        systemSellPrice as price,
        netImbalanceVolume as niv,
        CASE 
            WHEN EXTRACT(HOUR FROM settlementDate) + (settlementPeriod - 1) * 0.5 BETWEEN 0 AND 7 THEN 'Night'
            WHEN EXTRACT(HOUR FROM settlementDate) + (settlementPeriod - 1) * 0.5 BETWEEN 16 AND 19 THEN 'Peak'
            ELSE 'Day'
        END as time_period
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
      AND systemSellPrice <= {threshold}
      AND systemSellPrice > 0
    ORDER BY systemSellPrice ASC
    LIMIT 50
    """
    
    df = client.query(query).to_dataframe()
    return df

def get_vlp_bid_offers(client, bmu_id='FBPGM002', days=7):
    """Get VLP unit bid-offer data (if available)"""
    # Try IRIS first (more recent)
    query = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        bmUnit,
        pairId,
        offer,
        bid,
        offer - bid as spread,
        levelFrom,
        levelTo,
        levelTo - levelFrom as volume_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_bod_iris`
    WHERE bmUnit = '{bmu_id}'
      AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    ORDER BY settlementDate DESC, settlementPeriod DESC, pairId
    LIMIT 100
    """
    
    try:
        df = client.query(query).to_dataframe()
        if not df.empty:
            return df
    except:
        pass
    
    # Fallback to historical
    query = f"""
    SELECT 
        settlementDate,
        settlementPeriod,
        bmUnit,
        pairId,
        offer,
        bid,
        offer - bid as spread,
        levelFrom,
        levelTo,
        levelTo - levelFrom as volume_mw
    FROM `{PROJECT_ID}.{DATASET}.bmrs_bod`
    WHERE bmUnit = '{bmu_id}'
      AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
    ORDER BY settlementDate DESC, settlementPeriod DESC, pairId
    LIMIT 100
    """
    
    df = client.query(query).to_dataframe()
    return df

def calculate_arbitrage_revenue(client, battery_mw=50, efficiency=0.9, days=30):
    """Estimate battery arbitrage revenue"""
    query = f"""
    WITH daily_prices AS (
        SELECT 
            DATE(settlementDate) as date,
            MIN(systemSellPrice) as min_price,
            MAX(systemSellPrice) as max_price,
            MAX(systemSellPrice) - MIN(systemSellPrice) as spread
        FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
        GROUP BY date
    )
    SELECT 
        date,
        min_price,
        max_price,
        spread,
        -- Revenue = (discharge_price - charge_price) * volume * efficiency
        ROUND(spread * {battery_mw} * 0.5 * {efficiency}, 2) as revenue_per_cycle,
        ROUND(spread * {battery_mw} * 0.5 * {efficiency} * 365, 2) as annualized_revenue
    FROM daily_prices
    ORDER BY date DESC
    """
    
    df = client.query(query).to_dataframe()
    return df

def main():
    print("\n" + "="*80)
    print("VLP & PRICING ANALYSIS")
    print("="*80)
    
    client = bigquery.Client(project=PROJECT_ID, location='US')
    
    # 1. Price Volatility Analysis
    print("\n1. PRICE VOLATILITY (Last 30 Days)")
    print("-" * 80)
    volatility = get_price_volatility(client, days=30)
    print(f"\nTop 10 Most Volatile Days (Arbitrage Opportunity):")
    print(volatility.nlargest(10, 'daily_spread')[['date', 'min_price', 'max_price', 'daily_spread', 'avg_price']].to_string(index=False))
    
    avg_spread = volatility['daily_spread'].mean()
    max_spread = volatility['daily_spread'].max()
    print(f"\nAverage daily spread: £{avg_spread:.2f}/MWh")
    print(f"Maximum daily spread: £{max_spread:.2f}/MWh")
    
    # 2. High Price Periods (Discharge)
    print("\n\n2. HIGH PRICE PERIODS (Discharge Opportunities)")
    print("-" * 80)
    high_prices = get_high_price_periods(client, threshold=100, days=30)
    if not high_prices.empty:
        print(f"\nTop 10 Highest Prices (Last 30 Days):")
        print(high_prices.head(10)[['settlementDate', 'settlementPeriod', 'price', 'time_period']].to_string(index=False))
        print(f"\nAverage high price (>£100): £{high_prices['price'].mean():.2f}/MWh")
    else:
        print("No prices >£100/MWh in last 30 days")
    
    # 3. Low Price Periods (Charge)
    print("\n\n3. LOW PRICE PERIODS (Charge Opportunities)")
    print("-" * 80)
    low_prices = get_low_price_periods(client, threshold=30, days=30)
    if not low_prices.empty:
        print(f"\nTop 10 Lowest Prices (Last 30 Days):")
        print(low_prices.head(10)[['settlementDate', 'settlementPeriod', 'price', 'time_period']].to_string(index=False))
        print(f"\nAverage low price (<£30): £{low_prices['price'].mean():.2f}/MWh")
    else:
        print("No prices <£30/MWh in last 30 days")
    
    # 4. Imbalance vs Wholesale Premium
    print("\n\n4. IMBALANCE vs WHOLESALE PRICE PREMIUM")
    print("-" * 80)
    comparison = get_imbalance_vs_wholesale(client, days=7)
    if not comparison.empty:
        comparison_clean = comparison.dropna(subset=['wholesale_price'])
        if not comparison_clean.empty:
            avg_premium = comparison_clean['premium'].mean()
            max_premium = comparison_clean['premium'].max()
            print(f"\nAverage imbalance premium: £{avg_premium:.2f}/MWh")
            print(f"Maximum premium: £{max_premium:.2f}/MWh")
            print(f"\nTop 5 Premium Periods:")
            print(comparison_clean.nlargest(5, 'premium')[['settlementDate', 'settlementPeriod', 'imbalance_price', 'wholesale_price', 'premium']].to_string(index=False))
        else:
            print("No wholesale price data available for comparison")
    
    # 5. Arbitrage Revenue Estimate
    print("\n\n5. BATTERY ARBITRAGE REVENUE ESTIMATE")
    print("-" * 80)
    print("Assumptions: 50 MW battery, 90% round-trip efficiency, 1 cycle/day")
    revenue = calculate_arbitrage_revenue(client, battery_mw=50, efficiency=0.9, days=30)
    print(f"\nLast 7 Days Revenue Potential:")
    print(revenue.head(7)[['date', 'spread', 'revenue_per_cycle']].to_string(index=False))
    
    avg_daily = revenue['revenue_per_cycle'].mean()
    avg_annual = avg_daily * 365
    print(f"\nAverage daily revenue: £{avg_daily:,.2f}")
    print(f"Estimated annual revenue: £{avg_annual:,.2f}")
    
    # 6. VLP Unit Bid-Offer Analysis
    print("\n\n6. VLP UNIT BID-OFFER ANALYSIS")
    print("-" * 80)
    vlp_units = ['FBPGM002', 'FFSEN005']
    for bmu in vlp_units:
        print(f"\n{bmu}:")
        bids = get_vlp_bid_offers(client, bmu_id=bmu, days=7)
        if not bids.empty:
            print(f"  Found {len(bids)} bid-offer pairs (last 7 days)")
            print(f"  Average spread: £{bids['spread'].mean():.2f}/MWh")
            print(f"  Average volume: {bids['volume_mw'].mean():.1f} MW")
            print(f"\n  Sample (most recent):")
            print(bids.head(3)[['settlementDate', 'settlementPeriod', 'pairId', 'bid', 'offer', 'spread', 'volume_mw']].to_string(index=False))
        else:
            print(f"  No recent bid-offer data (check bmrs_bod historical)")
    
    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
