"""
Optimal BESS Dispatch Algorithm
Determines optimal charge/discharge schedule to maximize revenue
Considers DC/CM commitments, BM opportunities, and arbitrage
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from datetime import datetime, timedelta
import os

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Battery specifications
BATTERY_POWER_MW = 2.5
BATTERY_CAPACITY_MWH = 5.0
EFFICIENCY = 0.88  # Roundtrip efficiency
SOC_MIN = 0.25  # 0.25 MWh minimum
SOC_MAX = 5.0   # 5.0 MWh maximum

# Revenue rates
DC_RATE = 8.50  # £/MW/h
CM_RATE = 5.14  # £/MW/h
BM_RATE = 25.00  # £/MWh estimated dispatch value
DUOS_RED = 17.64  # £/MWh (NGED-WM HV)
DUOS_GREEN = 0.11  # £/MWh
LEVIES = 98.15  # £/MWh

# Time band definitions (NGED-WM HV)
def is_red_period(hour, dow):
    """Check if hour is RED period (16:00-19:30 weekdays)"""
    if dow >= 5:  # Weekend
        return False
    return 16 <= hour < 19.5  # 16:00-19:30

def is_green_period(hour, dow):
    """Check if hour is GREEN period (off-peak + weekends)"""
    if dow >= 5:  # Weekend = all GREEN
        return True
    return hour < 8 or hour >= 22  # Weekdays 00:00-08:00, 22:00-23:59

def get_duos_rate(hour, dow):
    """Get DUoS rate for time period"""
    if is_red_period(hour, dow):
        return DUOS_RED
    elif is_green_period(hour, dow):
        return DUOS_GREEN
    else:
        return 2.05  # AMBER rate

def forecast_next_24h_prices():
    """Forecast prices for next 24 hours using historical SP-specific averages"""
    print("\n📊 FORECASTING NEXT 24H PRICES...")
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Get current date/time
    now = datetime.now()
    current_dow = now.weekday()
    current_hour = now.hour
    
    # Query last 90 days of price data by SP and DOW
    query = f"""
    WITH prices AS (
        SELECT 
            settlementDate,
            settlementPeriod,
            systemSellPrice as ssp,
            EXTRACT(DAYOFWEEK FROM settlementDate) - 1 as dow,
            FLOOR((settlementPeriod - 1) / 2) as hour
        FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
        WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
            AND settlementDate < CURRENT_DATE()
            AND systemSellPrice IS NOT NULL
    )
    SELECT 
        settlementPeriod,
        dow,
        hour,
        AVG(ssp) as avg_price,
        STDDEV(ssp) as price_volatility,
        COUNT(*) as sample_size
    FROM prices
    GROUP BY settlementPeriod, dow, hour
    ORDER BY settlementPeriod
    """
    
    try:
        df = client.query(query).to_dataframe()
        
        if len(df) > 0:
            print(f"   ✅ Retrieved {len(df)} SP-DOW price patterns")
            
            # Generate forecast for next 24h (48 settlement periods)
            forecast = []
            for sp_offset in range(48):
                # Calculate which SP and DOW
                total_sp = (current_hour * 2 + (now.minute // 30) + sp_offset) % 48 + 1
                days_ahead = (current_hour * 2 + sp_offset) // 48
                forecast_dow = (current_dow + days_ahead) % 7
                forecast_hour = (total_sp - 1) // 2
                
                # Get avg price for this SP + DOW combination
                mask = (df['settlementPeriod'] == total_sp) & (df['dow'] == forecast_dow)
                if mask.sum() > 0:
                    avg_price = df[mask]['avg_price'].iloc[0]
                    volatility = df[mask]['price_volatility'].iloc[0]
                else:
                    # Fallback: avg across all DOWs for this SP
                    mask_sp = df['settlementPeriod'] == total_sp
                    avg_price = df[mask_sp]['avg_price'].mean() if mask_sp.sum() > 0 else 70.0
                    volatility = 30.0
                
                forecast.append({
                    'sp': total_sp,
                    'hour': forecast_hour,
                    'dow': forecast_dow,
                    'price': avg_price,
                    'volatility': volatility,
                    'duos': get_duos_rate(forecast_hour, forecast_dow)
                })
            
            forecast_df = pd.DataFrame(forecast)
            print(f"   📈 Forecast complete: Avg price £{forecast_df['price'].mean():.2f}/MWh")
            print(f"      Price range: £{forecast_df['price'].min():.2f} - £{forecast_df['price'].max():.2f}/MWh")
            
            return forecast_df
        else:
            print("   ⚠️  No historical price data available")
            return None
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def calculate_arbitrage_profit(charge_price, discharge_price, mwh, duos_charge, duos_discharge):
    """Calculate net profit from arbitrage action"""
    # Import cost (charging)
    import_cost = (charge_price + LEVIES + duos_charge) * mwh / EFFICIENCY
    
    # Export revenue (discharging)
    export_revenue = discharge_price * mwh * EFFICIENCY
    
    # DUoS savings (avoided RED import by charging GREEN)
    if duos_charge < duos_discharge:
        duos_saving = (duos_discharge - duos_charge) * mwh
    else:
        duos_saving = 0
    
    # Net profit
    return export_revenue - import_cost + duos_saving

def optimize_dispatch_greedy(forecast_df, initial_soc=2.5):
    """Greedy optimization: identify best charge/discharge opportunities"""
    print("\n🎯 OPTIMIZING DISPATCH SCHEDULE (Greedy Algorithm)...")
    
    if forecast_df is None or len(forecast_df) == 0:
        print("   ❌ No forecast data available")
        return None
    
    # Sort by price to find best charge (low) and discharge (high) opportunities
    low_price_periods = forecast_df.nsmallest(10, 'price')
    high_price_periods = forecast_df.nlargest(10, 'price')
    
    print(f"\n   🔋 CHARGING OPPORTUNITIES (Lowest prices):")
    for idx, row in low_price_periods.head(5).iterrows():
        profit = calculate_arbitrage_profit(
            row['price'], 
            forecast_df['price'].max(), 
            BATTERY_CAPACITY_MWH,
            row['duos'],
            DUOS_RED
        )
        print(f"      SP{row['sp']:2.0f} (H{row['hour']:2.0f}): £{row['price']:6.2f}/MWh, "
              f"DUoS: £{row['duos']:5.2f}/MWh → Potential profit: £{profit:,.0f}")
    
    print(f"\n   ⚡ DISCHARGING OPPORTUNITIES (Highest prices):")
    for idx, row in high_price_periods.head(5).iterrows():
        profit = calculate_arbitrage_profit(
            forecast_df['price'].min(), 
            row['price'], 
            BATTERY_CAPACITY_MWH,
            DUOS_GREEN,
            row['duos']
        )
        print(f"      SP{row['sp']:2.0f} (H{row['hour']:2.0f}): £{row['price']:6.2f}/MWh, "
              f"DUoS: £{row['duos']:5.2f}/MWh → Potential profit: £{profit:,.0f}")
    
    # Simple greedy strategy: charge at lowest, discharge at highest
    best_charge = low_price_periods.iloc[0]
    best_discharge = high_price_periods.iloc[0]
    
    max_profit = calculate_arbitrage_profit(
        best_charge['price'],
        best_discharge['price'],
        BATTERY_CAPACITY_MWH,
        best_charge['duos'],
        best_discharge['duos']
    )
    
    print(f"\n   💰 BEST ARBITRAGE OPPORTUNITY:")
    print(f"      Charge: SP{best_charge['sp']:.0f} @ £{best_charge['price']:.2f}/MWh (DUoS: £{best_charge['duos']:.2f})")
    print(f"      Discharge: SP{best_discharge['sp']:.0f} @ £{best_discharge['price']:.2f}/MWh (DUoS: £{best_discharge['duos']:.2f})")
    print(f"      Capacity: {BATTERY_CAPACITY_MWH} MWh")
    print(f"      Net profit: £{max_profit:,.2f}")
    
    # Generate dispatch schedule
    schedule = []
    for idx, row in forecast_df.iterrows():
        action = 'HOLD'
        mw = 0
        
        if row['sp'] == best_charge['sp']:
            action = 'CHARGE'
            mw = BATTERY_POWER_MW
        elif row['sp'] == best_discharge['sp']:
            action = 'DISCHARGE'
            mw = BATTERY_POWER_MW
        
        schedule.append({
            'sp': row['sp'],
            'hour': row['hour'],
            'price': row['price'],
            'duos': row['duos'],
            'action': action,
            'power_mw': mw
        })
    
    schedule_df = pd.DataFrame(schedule)
    
    print(f"\n   📋 DISPATCH SCHEDULE SUMMARY:")
    print(f"      Charge actions: {len(schedule_df[schedule_df['action'] == 'CHARGE'])}")
    print(f"      Discharge actions: {len(schedule_df[schedule_df['action'] == 'DISCHARGE'])}")
    print(f"      Hold periods: {len(schedule_df[schedule_df['action'] == 'HOLD'])}")
    
    return schedule_df

def calculate_total_revenue(schedule_df):
    """Calculate total revenue including DC, CM, BM, and arbitrage"""
    print("\n💰 TOTAL REVENUE CALCULATION (24h):")
    
    # DC revenue (availability-based, always earned)
    dc_revenue_24h = DC_RATE * BATTERY_POWER_MW * 24
    print(f"   DC Availability: £{dc_revenue_24h:.2f} (£{DC_RATE}/MW/h × {BATTERY_POWER_MW} MW × 24h)")
    
    # CM revenue (availability-based, always earned)
    cm_revenue_24h = CM_RATE * BATTERY_POWER_MW * 24
    print(f"   CM Availability: £{cm_revenue_24h:.2f} (£{CM_RATE}/MW/h × {BATTERY_POWER_MW} MW × 24h)")
    
    # BM revenue (assume 1 dispatch per day for conservative estimate)
    bm_revenue_24h = BM_RATE * BATTERY_CAPACITY_MWH
    print(f"   BM Dispatch: £{bm_revenue_24h:.2f} (£{BM_RATE}/MWh × {BATTERY_CAPACITY_MWH} MWh × 1 dispatch)")
    
    # Arbitrage revenue from schedule
    charge_actions = schedule_df[schedule_df['action'] == 'CHARGE']
    discharge_actions = schedule_df[schedule_df['action'] == 'DISCHARGE']
    
    if len(charge_actions) > 0 and len(discharge_actions) > 0:
        avg_charge_price = charge_actions['price'].mean()
        avg_discharge_price = discharge_actions['price'].mean()
        avg_charge_duos = charge_actions['duos'].mean()
        avg_discharge_duos = discharge_actions['duos'].mean()
        
        arbitrage_revenue = calculate_arbitrage_profit(
            avg_charge_price,
            avg_discharge_price,
            BATTERY_CAPACITY_MWH,
            avg_charge_duos,
            avg_discharge_duos
        )
        print(f"   Arbitrage Profit: £{arbitrage_revenue:.2f}")
    else:
        arbitrage_revenue = 0
        print(f"   Arbitrage Profit: £0.00 (no opportunities)")
    
    total = dc_revenue_24h + cm_revenue_24h + bm_revenue_24h + arbitrage_revenue
    
    print(f"\n   ═══════════════════════════════════")
    print(f"   TOTAL 24h REVENUE: £{total:.2f}")
    print(f"   ═══════════════════════════════════")
    print(f"   Annual projection: £{total * 365:,.0f}/year")
    
    return {
        'dc': dc_revenue_24h,
        'cm': cm_revenue_24h,
        'bm': bm_revenue_24h,
        'arbitrage': arbitrage_revenue,
        'total': total
    }

if __name__ == "__main__":
    # Set credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/home/george/inner-cinema-credentials.json'
    
    print("="*70)
    print("🔋 OPTIMAL BESS DISPATCH ALGORITHM")
    print("="*70)
    print(f"Battery: {BATTERY_POWER_MW} MW / {BATTERY_CAPACITY_MWH} MWh")
    print(f"Efficiency: {EFFICIENCY*100:.0f}%")
    print(f"SOC Range: {SOC_MIN} - {SOC_MAX} MWh")
    
    # Step 1: Forecast prices
    forecast = forecast_next_24h_prices()
    
    # Step 2: Optimize dispatch
    if forecast is not None:
        schedule = optimize_dispatch_greedy(forecast)
        
        # Step 3: Calculate revenue
        if schedule is not None:
            revenue = calculate_total_revenue(schedule)
            
            # Save schedule
            if schedule is not None:
                schedule.to_csv('optimal_dispatch_schedule.csv', index=False)
                print(f"\n✅ Dispatch schedule saved: optimal_dispatch_schedule.csv")
    
    print("="*70)
