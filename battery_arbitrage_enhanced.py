#!/usr/bin/env python3
"""
Enhanced Battery Arbitrage Optimization
Extends battery_arbitrage.py with:
- Price threshold optimization
- Cycle degradation modeling  
- Optimal charge/discharge timing
- Multi-constraint handling (power, SoC, cycles)
"""

from google.cloud import bigquery
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Battery constraints
BATTERY_POWER_MW = 2.5
BATTERY_CAPACITY_MWH = 5.0
SOC_MIN = 0.25  # 0.25 MWh minimum (5% of 5 MWh)
SOC_MAX = 5.0   # Full capacity
CYCLE_WARRANTY = 10000  # Lifetime cycles
ROUNDTRIP_EFFICIENCY = 0.88  # 88% roundtrip efficiency

# Cost assumptions
DUOS_RATES = {
    'RED': 4.837,    # p/kWh
    'AMBER': 0.457,
    'GREEN': 0.038
}
LEVIES_GBP_MWH = 98.15
PPA_EXPORT_PRICE = 150.0  # £/MWh

def get_historical_prices(days=30):
    """Fetch historical SSP/SBP prices for analysis"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=days)
    
    query = f"""
    SELECT 
        CAST(settlementDate AS DATE) as date,
        settlementPeriod as sp,
        systemSellPrice as ssp,
        systemBuyPrice as sbp,
        EXTRACT(DAYOFWEEK FROM settlementDate) as dow,
        -- DUoS band
        CASE
          WHEN EXTRACT(DAYOFWEEK FROM settlementDate) IN (1,7) THEN 'GREEN'
          WHEN settlementPeriod BETWEEN 33 AND 39 THEN 'RED'
          WHEN settlementPeriod BETWEEN 17 AND 44 THEN 'AMBER'
          ELSE 'GREEN'
        END as duos_band
    FROM `{PROJECT_ID}.{DATASET}.bmrs_costs`
    WHERE CAST(settlementDate AS DATE) BETWEEN '{start_date}' AND '{end_date}'
    ORDER BY date, sp
    """
    
    df = client.query(query).to_dataframe()
    return df

def calculate_thresholds(df, percentile_low=25, percentile_high=75):
    """
    Calculate optimal buy/sell thresholds based on price distribution
    """
    # Calculate import costs
    df['duos_rate'] = df['duos_band'].map({
        'RED': DUOS_RATES['RED'] / 100,  # Convert p/kWh to £/MWh
        'AMBER': DUOS_RATES['AMBER'] / 100,
        'GREEN': DUOS_RATES['GREEN'] / 100
    })
    df['import_cost'] = df['sbp'] + df['duos_rate'] + LEVIES_GBP_MWH
    
    # Calculate export revenue
    df['export_revenue'] = PPA_EXPORT_PRICE
    
    # Calculate net profit per MWh
    df['net_profit_per_mwh'] = (df['export_revenue'] - df['import_cost']) * ROUNDTRIP_EFFICIENCY
    
    # Optimal thresholds
    buy_threshold = df['import_cost'].quantile(percentile_low / 100)
    sell_threshold = df['ssp'].quantile(percentile_high / 100)
    
    return {
        'buy_threshold': buy_threshold,
        'sell_threshold': sell_threshold,
        'avg_import_cost': df['import_cost'].mean(),
        'avg_export_revenue': df['export_revenue'].mean(),
        'avg_net_profit': df['net_profit_per_mwh'].mean(),
        'profitable_periods': len(df[df['net_profit_per_mwh'] > 0]),
        'total_periods': len(df)
    }

def forecast_next_day_prices(df, periods_ahead=48):
    """
    Simple moving average forecast (ARIMA requires statsmodels)
    """
    try:
        # Use last 7 days average per settlement period
        forecast_prices = []
        for sp in range(1, periods_ahead + 1):
            sp_prices = df[df['sp'] == sp]['ssp'].tail(7)
            if len(sp_prices) > 0:
                forecast_prices.append(sp_prices.mean())
            else:
                forecast_prices.append(df['ssp'].mean())
        
        forecast_df = pd.DataFrame({
            'forecast_period': range(1, periods_ahead + 1),
            'forecast_ssp': forecast_prices
        })
        
        return forecast_df
    except Exception as e:
        print(f'   ⚠️  Forecast failed: {e}')
        return None

def simulate_arbitrage_strategy(df, thresholds, current_cycles=0):
    """
    Simulate battery operation with cycle constraints
    """
    soc = BATTERY_CAPACITY_MWH / 2  # Start at 50%
    cycles_used = current_cycles
    total_profit = 0
    actions = []
    
    for idx, row in df.iterrows():
        import_cost = row['import_cost']
        export_revenue = row['export_revenue']
        ssp = row['ssp']
        
        # Decision logic with cycle awareness
        max_cycles_remaining = CYCLE_WARRANTY - cycles_used
        
        # BUY (charge) decision
        if (import_cost < thresholds['buy_threshold'] and 
            soc < SOC_MAX - 0.5 and  # Leave headroom
            max_cycles_remaining > 100):  # Preserve cycles if near warranty
            
            charge_mwh = min(BATTERY_POWER_MW * 0.5, SOC_MAX - soc)  # 30 min SP
            cost = charge_mwh * import_cost
            soc += charge_mwh * ROUNDTRIP_EFFICIENCY
            
            actions.append({
                'date': row['date'],
                'sp': row['sp'],
                'action': 'CHARGE',
                'mwh': charge_mwh,
                'price': import_cost,
                'cost': cost,
                'soc': soc
            })
        
        # SELL (discharge) decision  
        elif (ssp > thresholds['sell_threshold'] and 
              soc > SOC_MIN + 0.5):
            
            discharge_mwh = min(BATTERY_POWER_MW * 0.5, soc - SOC_MIN)
            revenue = discharge_mwh * export_revenue
            soc -= discharge_mwh
            cycles_used += discharge_mwh / BATTERY_CAPACITY_MWH  # Cycle = full discharge
            total_profit += revenue - (discharge_mwh * import_cost)  # Approximate cost basis
            
            actions.append({
                'date': row['date'],
                'sp': row['sp'],
                'action': 'DISCHARGE',
                'mwh': discharge_mwh,
                'price': export_revenue,
                'revenue': revenue,
                'soc': soc
            })
    
    return {
        'total_profit': total_profit,
        'cycles_used': cycles_used,
        'final_soc': soc,
        'actions': actions
    }

def main():
    print('\n⚡ ENHANCED BATTERY ARBITRAGE OPTIMIZATION')
    print('='*80)
    
    # Fetch historical data
    print('\n📊 Fetching historical price data (30 days)...')
    df = get_historical_prices(days=30)
    
    if df.empty:
        print('   ❌ No price data available')
        return
    
    print(f'   ✅ Retrieved {len(df)} settlement periods')
    print(f'   Date range: {df["date"].min()} to {df["date"].max()}')
    
    # Calculate optimal thresholds
    print('\n🎯 Calculating optimal price thresholds...')
    thresholds = calculate_thresholds(df)
    
    print(f'   Buy threshold: £{thresholds["buy_threshold"]:.2f}/MWh')
    print(f'   Sell threshold: £{thresholds["sell_threshold"]:.2f}/MWh')
    print(f'   Avg import cost: £{thresholds["avg_import_cost"]:.2f}/MWh')
    print(f'   Avg net profit: £{thresholds["avg_net_profit"]:.2f}/MWh')
    print(f'   Profitable periods: {thresholds["profitable_periods"]}/{thresholds["total_periods"]} ' +
          f'({100*thresholds["profitable_periods"]/thresholds["total_periods"]:.1f}%)')
    
    # Forecast next day
    print('\n🔮 Forecasting next 48 periods (24 hours)...')
    forecast_df = forecast_next_day_prices(df)
    
    if forecast_df is not None:
        print(f'   Next period forecast: £{forecast_df.iloc[0]["forecast_ssp"]:.2f}/MWh')
        print(f'   Max forecast: £{forecast_df["forecast_ssp"].max():.2f}/MWh')
        print(f'   Min forecast: £{forecast_df["forecast_ssp"].min():.2f}/MWh')
    
    # Simulate strategy
    print('\n🔋 Simulating arbitrage strategy...')
    results = simulate_arbitrage_strategy(df, thresholds, current_cycles=0)
    
    print(f'   Total profit: £{results["total_profit"]:,.2f}')
    print(f'   Cycles used: {results["cycles_used"]:.2f} ({100*results["cycles_used"]/CYCLE_WARRANTY:.1f}% of warranty)')
    print(f'   Final SoC: {results["final_soc"]:.2f} MWh')
    print(f'   Actions taken: {len(results["actions"])}')
    
    # Top profitable actions
    if results['actions']:
        actions_df = pd.DataFrame(results['actions'])
        discharge_actions = actions_df[actions_df['action'] == 'DISCHARGE']
        
        if not discharge_actions.empty:
            print(f'\n💰 Top 5 discharge periods:')
            top_discharges = discharge_actions.nlargest(5, 'revenue')
            for _, action in top_discharges.iterrows():
                print(f'   {action["date"]} SP{action["sp"]}: {action["mwh"]:.2f} MWh @ £{action["price"]:.2f} = £{action["revenue"]:.2f}')
    
    # Summary stats
    print('\n📈 SUMMARY STATISTICS')
    print(f'   Battery: {BATTERY_POWER_MW} MW / {BATTERY_CAPACITY_MWH} MWh')
    print(f'   Efficiency: {ROUNDTRIP_EFFICIENCY*100:.0f}%')
    print(f'   Cycle warranty: {CYCLE_WARRANTY:,} cycles')
    print(f'   SoC limits: {SOC_MIN} - {SOC_MAX} MWh')
    print(f'   PPA export: £{PPA_EXPORT_PRICE}/MWh')
    print(f'   Levies: £{LEVIES_GBP_MWH}/MWh')
    
    print('\n✅ Arbitrage optimization complete!')
    print('='*80 + '\n')

if __name__ == '__main__':
    main()
