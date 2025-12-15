#!/usr/bin/env python3
"""
Battery VLP/VTP Market Analysis & Revenue Estimation

Analyzes GB electricity market data for battery storage revenue opportunities:
- System imbalance price volatility (arbitrage opportunities from bmrs_costs)
- ACTUAL battery VLP unit bid-offer behavior (from bmrs_bod/bmrs_bod_iris)
- Wholesale vs imbalance price premiums
- Real battery unit pricing strategies (E_DOLLB-1, T_NURSB-1, etc.)
- Revenue estimation for 50 MW battery with VTP status

Data Sources:
- bmrs_costs: System imbalance prices (SSP/SBP merged since Nov 2015)
- bmrs_bod_iris: Real-time bid-offer data (Oct 28 - present)
- bmrs_mid_iris: Wholesale market prices
- bmu_registration_data: Battery unit identification (31 units found)

Key Discovery: Battery VLP units submit DEFENSIVE pricing:
- High offers (£200-1500/MWh) to avoid unwanted discharge
- Negative bids (-£200 to -£1400/MWh) to get paid to charge
- Spreads of £500-2800/MWh indicate strategic positioning
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

def get_battery_units(client):
    """Get list of battery/storage BMU IDs from registration data"""
    query = f"""
    SELECT DISTINCT 
        elexonbmunit,
        leadpartyname,
        generationcapacity
    FROM `{PROJECT_ID}.{DATASET}.bmu_registration_data`
    WHERE LOWER(fueltype) LIKE '%batt%'
       OR LOWER(fueltype) LIKE '%stor%'
       OR LOWER(fueltype) LIKE '%bess%'
    ORDER BY generationcapacity DESC
    LIMIT 20
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df['elexonbmunit'].tolist() if not df.empty else []
    except:
        # Fallback to known battery units
        return ['E_DOLLB-1', 'T_NURSB-1', 'T_LARKB-1', 'E_ARBRB-1', 'E_BROXB-1', 'E_CATHB-1']

def get_battery_bid_offers(client, days=7):
    """Get ACTUAL battery VLP unit bid-offer data"""
    battery_units = get_battery_units(client)
    
    if not battery_units:
        battery_units = ['E_DOLLB-1', 'T_NURSB-1', 'T_LARKB-1', 'E_ARBRB-1']
    
    # Limit to top 10 for performance
    battery_units = battery_units[:10]
    
    query = f"""
    SELECT 
        bmUnit,
        DATE(settlementDate) as date,
        settlementPeriod,
        AVG(offer) as avg_offer,
        AVG(bid) as avg_bid,
        AVG(offer - bid) as spread,
        AVG(levelTo - levelFrom) as avg_mw_band,
        COUNT(*) as num_pairs
    FROM `{PROJECT_ID}.{DATASET}.bmrs_bod_iris`
    WHERE bmUnit IN UNNEST({battery_units})
      AND settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
      AND offer IS NOT NULL
      AND bid IS NOT NULL
    GROUP BY bmUnit, date, settlementPeriod
    ORDER BY date DESC, spread DESC
    LIMIT 200
    """
    
    try:
        df = client.query(query).to_dataframe()
        return df
    except Exception as e:
        print(f"    Error querying battery bids: {e}")
        return pd.DataFrame()

def get_market_bid_offer_spreads(client, days=7):
    """Get market-wide bid-offer spreads from all units (filtered for realistic values)"""
    query = f"""
    SELECT 
        DATE(settlementDate) as date,
        settlementPeriod,
        bmUnit,
        AVG(offer - bid) as avg_spread,
        MIN(offer - bid) as min_spread,
        MAX(offer - bid) as max_spread,
        COUNT(*) as pairs,
        AVG(levelTo - levelFrom) as avg_volume_mw,
        AVG(offer) as avg_offer,
        AVG(bid) as avg_bid
    FROM `{PROJECT_ID}.{DATASET}.bmrs_bod_iris`
    WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {days} DAY)
      AND offer > 0
      AND bid > 0
      AND offer > bid
      AND offer < 1000  -- Filter extreme outliers (max £1000/MWh realistic)
      AND bid >= -500   -- Filter unrealistic negative bids
      AND (offer - bid) < 500  -- Filter extreme spreads
    GROUP BY date, settlementPeriod, bmUnit
    ORDER BY date DESC, avg_spread DESC
    LIMIT 200
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
        DATE(settlementDate) as date,
        settlementPeriod,
        bmUnit,
        AVG(offer - bid) as avg_spread,
        MIN(offer - bid) as min_spread,
        MAX(offer - bid) as max_spread,
        COUNT(*) as pairs,
        AVG(levelTo - levelFrom) as avg_volume_mw,
        AVG(offer) as avg_offer,
        AVG(bid) as avg_bid
    FROM `{PROJECT_ID}.{DATASET}.bmrs_bod`
    WHERE settlementDate >= '2025-10-20'
      AND offer > 0
      AND bid > 0
      AND offer > bid
      AND offer < 1000
      AND bid >= -500
      AND (offer - bid) < 500
    GROUP BY date, settlementPeriod, bmUnit
    ORDER BY date DESC, avg_spread DESC
    LIMIT 200
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
    
    # 6. ACTUAL BATTERY VLP BID-OFFER ANALYSIS
    print("\n\n6. BATTERY VLP UNIT BID-OFFER ANALYSIS (REAL DATA)")
    print("-" * 80)
    print("Analyzing ACTUAL battery storage unit bidding behavior")
    print("Data source: bmrs_bod_iris (real-time IRIS pipeline)")
    
    battery_bids = get_battery_bid_offers(client, days=7)
    if not battery_bids.empty:
        print(f"\nFound {len(battery_bids)} battery unit bid-offer submissions (last 7 days)")
        
        # Overall statistics
        print(f"\nBattery VLP Bidding Statistics:")
        print(f"  Average offer price: £{battery_bids['avg_offer'].mean():.2f}/MWh")
        print(f"  Average bid price: £{battery_bids['avg_bid'].mean():.2f}/MWh")
        print(f"  Average spread: £{battery_bids['spread'].mean():.2f}/MWh")
        print(f"  Median spread: £{battery_bids['spread'].median():.2f}/MWh")
        
        # Top battery units by activity
        print(f"\nTop 10 Battery Units by Bid-Offer Activity:")
        top_batteries = battery_bids.groupby('bmUnit').agg({
            'num_pairs': 'sum',
            'avg_offer': 'mean',
            'avg_bid': 'mean',
            'spread': 'mean'
        }).nlargest(10, 'num_pairs')
        print(top_batteries.to_string())
        
        # Sample recent bids
        print(f"\nSample Recent Battery Bids (Last 5):")
        recent = battery_bids.head(5)[['date', 'settlementPeriod', 'bmUnit', 'avg_bid', 'avg_offer', 'spread']]
        print(recent.to_string(index=False))
        
        # Interpretation
        print(f"\nKEY INSIGHTS:")
        print(f"  • High offers (£{battery_bids['avg_offer'].mean():.0f}/MWh avg): DEFENSIVE PRICING")
        print(f"    Batteries avoid unwanted discharge by pricing high")
        print(f"  • Negative bids (£{battery_bids['avg_bid'].mean():.0f}/MWh avg): PAID TO CHARGE")
        print(f"    Batteries willing to pay/accept payment to charge during surplus")
        print(f"  • Wide spreads (£{battery_bids['spread'].mean():.0f}/MWh): Strategic positioning")
        print(f"    Not expecting acceptance - waiting for scarcity events")
    else:
        print("  No battery bid-offer data found")
        print("  This may indicate batteries primarily use frequency response,")
        print("  not active BM bidding, or data coverage gap.")
    
    # 7. Market-Wide Bid-Offer Spread Analysis (Non-Battery Units)
    print("\n\n7. MARKET-WIDE BID-OFFER SPREADS (All Units, Filtered)")
    print("-" * 80)
    print("Analyzing market-wide bid-offer spreads from all units")
    print("(Filtered for realistic values: offers <£1000/MWh, spreads <£500/MWh)")
    
    spreads = get_market_bid_offer_spreads(client, days=7)
    if not spreads.empty:
        print(f"\nFound {len(spreads)} unit-period combinations with realistic pricing")
        print(f"\nTop 10 Widest Bid-Offer Spreads (Last 7 Days):")
        top_spreads = spreads.nlargest(10, 'avg_spread')
        print(top_spreads[['date', 'settlementPeriod', 'bmUnit', 'avg_bid', 'avg_offer', 'avg_spread', 'pairs']].to_string(index=False))
        
        print(f"\nOverall Statistics (Realistic Units):")
        print(f"  Average spread: £{spreads['avg_spread'].mean():.2f}/MWh")
        print(f"  Median spread: £{spreads['avg_spread'].median():.2f}/MWh")
        print(f"  Maximum spread: £{spreads['avg_spread'].max():.2f}/MWh")
        print(f"  Units analyzed: {spreads['bmUnit'].nunique()}")
    else:
        print("  No bid-offer data available in recent period")
    
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
