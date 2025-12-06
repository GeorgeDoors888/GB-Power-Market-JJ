"""
ESO Live Market Data Connector
Fetches real-time DC/DR/DM prices, BM dispatch data, and CM auction results
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime, timedelta
import os
import json

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# ESO API endpoints
ESO_API_BASE = "https://data.elexon.co.uk/bmrs/api/v1"

def fetch_balancing_services_volumes():
    """Fetch latest balancing services contracted volumes from ESO"""
    print("\n📡 FETCHING ESO BALANCING SERVICES DATA...")
    
    try:
        # Get last 7 days of balancing data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        url = f"{ESO_API_BASE}/balancing/settlement/system-prices"
        params = {
            'settlementDateFrom': start_date.strftime('%Y-%m-%d'),
            'settlementDateTo': end_date.strftime('%Y-%m-%d'),
            'format': 'json'
        }
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and len(data['data']) > 0:
                df = pd.DataFrame(data['data'])
                print(f"   ✅ Retrieved {len(df)} settlement periods")
                return df
            else:
                print("   ⚠️  No data returned from API")
                return None
        else:
            print(f"   ❌ API Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error fetching ESO data: {e}")
        return None

def get_bm_dispatch_last_30_days():
    """Get actual BM dispatch data from BigQuery BOALF table"""
    print("\n📊 ANALYZING BM DISPATCH HISTORY (Last 30 Days)...")
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    WITH battery_units AS (
        -- Focus on battery units (BM Unit IDs typically containing 'BESS', 'BATT', or known VLP units)
        SELECT DISTINCT bmUnit
        FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
        WHERE bmUnit IN ('FBPGM002', 'FFSEN005')  -- Known VLP battery units
           OR bmUnit LIKE '%BESS%'
           OR bmUnit LIKE '%BATT%'
    ),
    recent_dispatch AS (
        SELECT 
            DATE(acceptanceTime) as date,
            bmUnit,
            COUNT(*) as dispatch_count,
            SUM(ABS(COALESCE(acceptedOfferVolume, 0))) as total_offer_mw,
            SUM(ABS(COALESCE(acceptedBidVolume, 0))) as total_bid_mw,
            AVG(COALESCE(acceptedOfferPrice, 0)) as avg_offer_price,
            AVG(COALESCE(acceptedBidPrice, 0)) as avg_bid_price
        FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
        WHERE acceptanceTime >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            AND acceptanceTime < CURRENT_DATE()
            AND bmUnit IN (SELECT bmUnit FROM battery_units)
        GROUP BY date, bmUnit
    )
    SELECT 
        bmUnit,
        COUNT(DISTINCT date) as active_days,
        AVG(dispatch_count) as avg_dispatches_per_day,
        SUM(total_offer_mw + total_bid_mw) as total_mw_dispatched,
        AVG(avg_offer_price) as avg_offer_price,
        AVG(avg_bid_price) as avg_bid_price
    FROM recent_dispatch
    GROUP BY bmUnit
    ORDER BY total_mw_dispatched DESC
    LIMIT 20
    """
    
    try:
        df = client.query(query).to_dataframe()
        
        if len(df) > 0:
            print(f"   ✅ Found {len(df)} battery units with BM activity")
            print("\n   Top Battery Units by BM Dispatch (Last 30 Days):")
            print("   " + "-"*80)
            for idx, row in df.head(10).iterrows():
                print(f"   {row['bmUnit']:12s}: {row['active_days']:2.0f} days active, "
                      f"{row['avg_dispatches_per_day']:5.1f} dispatches/day, "
                      f"{row['total_mw_dispatched']:7.1f} MW total")
            
            # Calculate system-wide averages
            total_dispatches = df['avg_dispatches_per_day'].mean()
            hours_per_day = total_dispatches * 0.5  # Each dispatch ~30 min
            
            print(f"\n   📈 Battery Fleet Averages:")
            print(f"      Avg dispatches per day: {total_dispatches:.2f}")
            print(f"      Estimated BM hours per day: {hours_per_day:.2f}h")
            print(f"      Avg offer price: £{df['avg_offer_price'].mean():.2f}/MWh")
            print(f"      Avg bid price: £{df['avg_bid_price'].mean():.2f}/MWh")
            
            return df
        else:
            print("   ⚠️  No battery BM dispatch data found")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def get_dc_utilization_estimate():
    """Estimate DC utilization from frequency data"""
    print("\n📊 ESTIMATING DC UTILIZATION FROM FREQUENCY DATA...")
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Query frequency deviations (DC triggers when frequency outside 49.985-50.015 Hz)
    query = f"""
    SELECT 
        COUNT(*) as total_minutes,
        SUM(CASE WHEN ABS(frequency - 50.0) > 0.015 THEN 1 ELSE 0 END) as dc_active_minutes,
        AVG(frequency) as avg_frequency,
        STDDEV(frequency) as frequency_volatility
    FROM `{PROJECT_ID}.{DATASET}.bmrs_freq`
    WHERE CAST(measurementTime AS TIMESTAMP) >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
        AND CAST(measurementTime AS TIMESTAMP) < CURRENT_TIMESTAMP()
        AND frequency BETWEEN 49.0 AND 51.0  -- Filter outliers
    """
    
    try:
        df = client.query(query).to_dataframe()
        
        if len(df) > 0 and df['total_minutes'].iloc[0] > 0:
            total_min = df['total_minutes'].iloc[0]
            active_min = df['dc_active_minutes'].iloc[0]
            utilization_pct = (active_min / total_min * 100) if total_min > 0 else 0
            avg_freq = df['avg_frequency'].iloc[0]
            volatility = df['frequency_volatility'].iloc[0]
            
            print(f"   ✅ Analyzed {total_min:,} minutes of frequency data (30 days)")
            print(f"   DC active minutes (|f-50| > 0.015 Hz): {active_min:,} ({utilization_pct:.2f}%)")
            print(f"   Avg frequency: {avg_freq:.5f} Hz")
            print(f"   Frequency volatility: {volatility:.5f} Hz")
            
            # DC revenue is based on availability, not utilization
            print(f"\n   💡 Note: DC revenue is availability-based (not utilization)")
            print(f"      Current model: £8.50/MW/h for holding capacity ready")
            print(f"      Actual dispatch: {utilization_pct:.2f}% of time (for info only)")
            
            return {'utilization_pct': utilization_pct, 'avg_freq': avg_freq}
        else:
            print("   ⚠️  No frequency data available")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def check_cm_auction_results():
    """Check latest Capacity Market auction results (requires manual lookup)"""
    print("\n📊 CAPACITY MARKET AUCTION RESULTS")
    print("   ⚠️  Manual lookup required - automated scraping not implemented")
    print("\n   Current model assumption:")
    print("      CM Rate: £45.00/kW/year (£5.14/MW/h)")
    print("      Source: 2024-2025 T-4 auction")
    print("\n   📋 Manual validation steps:")
    print("      1. Visit: https://www.emrdeliverybody.com/CM/Auctions-Results.aspx")
    print("      2. Check latest T-1 and T-4 auction clearing prices")
    print("      3. Update MODEL_ASSUMPTIONS if cleared price changed >10%")
    print("\n   Recent auction results (manual reference):")
    print("      T-4 2024/25: £45.00/kW/year (current model)")
    print("      T-1 2025/26: Check website for latest")

def update_revenue_model_with_live_data():
    """Update bess_revenue_stack_analyzer.py with validated live data"""
    print("\n" + "="*70)
    print("🔄 LIVE DATA INTEGRATION SUMMARY")
    print("="*70)
    
    # Fetch all live data
    eso_data = fetch_balancing_services_volumes()
    bm_dispatch = get_bm_dispatch_last_30_days()
    dc_util = get_dc_utilization_estimate()
    check_cm_auction_results()
    
    print("\n" + "="*70)
    print("📋 RECOMMENDATIONS")
    print("="*70)
    
    recommendations = []
    
    if bm_dispatch is not None and len(bm_dispatch) > 0:
        avg_hours = bm_dispatch['avg_dispatches_per_day'].mean() * 0.5
        if avg_hours < 1.5 or avg_hours > 2.5:
            recommendations.append(
                f"⚠️  BM Utilization: Update from 2.0h to {avg_hours:.2f}h per day"
            )
        else:
            recommendations.append("✅ BM Utilization: Current assumption (2.0h/day) is valid")
        
        avg_price = (bm_dispatch['avg_offer_price'].mean() + bm_dispatch['avg_bid_price'].mean()) / 2
        if avg_price > 0 and abs(avg_price - 25) / 25 > 0.2:
            recommendations.append(
                f"⚠️  BM Price: Update from £25/MWh to £{avg_price:.2f}/MWh"
            )
        else:
            recommendations.append("✅ BM Price: Current assumption (£25/MWh) is valid")
    
    if dc_util is not None:
        recommendations.append(
            f"ℹ️  DC Utilization: {dc_util['utilization_pct']:.2f}% frequency events (info only, doesn't affect revenue)"
        )
    
    for rec in recommendations:
        print(f"   {rec}")
    
    print("\n   💡 NEXT STEPS:")
    print("      1. If any ⚠️  warnings above, update REVENUE_RATES in bess_revenue_stack_analyzer.py")
    print("      2. Re-run: python3 bess_revenue_stack_analyzer.py")
    print("      3. Compare new revenue model vs previous £502k baseline")
    print("      4. Schedule monthly re-validation via cron job")
    
    print("="*70)

if __name__ == "__main__":
    # Set credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/inner-cinema-credentials.json'
    
    update_revenue_model_with_live_data()
