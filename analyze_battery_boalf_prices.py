#!/usr/bin/env python3
"""
Battery Arbitrage Analysis with BOD Acceptance Prices

Purpose: Calculate 2 MWh battery revenue using actual BM acceptance prices
         from bmrs_boalf_complete (BOD-derived) vs settlement proxy (disbsad)

Comparison:
- BOD acceptance prices: Individual unit prices (£85-110/MWh Oct 17)
- disbsad settlement: Volume-weighted average (£79.83/MWh Oct 17-23)

Constraints:
- 2 MWh battery capacity
- 2 cycles per day maximum (DUoS time band restrictions)
- 90% round-trip efficiency
- Peak hours: 16:00-19:30 (DUoS Red band)
"""

from google.cloud import bigquery
import pandas as pd
from datetime import datetime, timedelta
import logging

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Battery specs
BATTERY_CAPACITY_MWH = 2.0
MAX_CYCLES_PER_DAY = 2
ROUND_TRIP_EFFICIENCY = 0.90
CHARGE_EFFICIENCY = 0.95
DISCHARGE_EFFICIENCY = 0.95

# DUoS time bands (approximation)
PEAK_HOURS_START = 16  # 16:00
PEAK_HOURS_END = 20    # 19:30 (SP 39 = 19:30)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def get_boalf_prices(client, start_date, end_date, unit_filter=None):
    """
    Get BM acceptance prices from boalf_with_prices view
    
    Returns: DataFrame with acceptance prices by settlement period
    """
    
    unit_clause = f"AND bmUnit = '{unit_filter}'" if unit_filter else ""
    
    query = f"""
    SELECT 
      settlement_date,
      settlementPeriod,
      settlement_hour,
      time_band,
      acceptanceType,
      AVG(acceptancePrice) as avg_price,
      MIN(acceptancePrice) as min_price,
      MAX(acceptancePrice) as max_price,
      COUNT(*) as num_acceptances,
      SUM(acceptanceVolume) as total_volume_mw
    FROM `{PROJECT_ID}.{DATASET}.boalf_with_prices`
    WHERE settlement_date BETWEEN '{start_date}' AND '{end_date}'
      {unit_clause}
    GROUP BY settlement_date, settlementPeriod, settlement_hour, time_band, acceptanceType
    ORDER BY settlement_date, settlementPeriod, acceptanceType
    """
    
    logging.info(f"Fetching BOALF prices for {start_date} to {end_date}...")
    return client.query(query).to_dataframe()


def get_disbsad_prices(client, start_date, end_date):
    """
    Get settlement proxy prices from disbsad (volume-weighted average)
    
    Returns: DataFrame with settlement prices by period
    """
    
    query = f"""
    SELECT 
      DATE(settlementDate) as settlement_date,
      settlementPeriod,
      FLOOR((settlementPeriod - 1) / 2) as settlement_hour,
      SUM(cost) / SUM(volume) as price_gbp_per_mwh,
      SUM(volume) as total_volume_mw,
      COUNT(*) as num_records
    FROM `{PROJECT_ID}.{DATASET}.bmrs_disbsad`
    WHERE DATE(settlementDate) BETWEEN '{start_date}' AND '{end_date}'
      AND volume > 0
    GROUP BY settlement_date, settlementPeriod, settlement_hour
    ORDER BY settlement_date, settlementPeriod
    """
    
    logging.info(f"Fetching disbsad prices for {start_date} to {end_date}...")
    return client.query(query).to_dataframe()


def calculate_arbitrage_revenue(df_prices, price_col='price'):
    """
    Calculate optimal battery arbitrage revenue with 2 cycles/day constraint
    
    Strategy:
    - Charge during 2 lowest-price periods
    - Discharge during 2 highest-price periods
    - Apply efficiency losses
    """
    
    results = []
    
    for date in df_prices['settlement_date'].unique():
        day_data = df_prices[df_prices['settlement_date'] == date].copy()
        
        if len(day_data) < 4:  # Need at least 2 charge + 2 discharge periods
            continue
        
        # Sort by price to find optimal charge/discharge periods
        day_data = day_data.sort_values(price_col)
        
        # Find 2 cheapest periods for charging
        charge_periods = day_data.nsmallest(2, price_col)
        charge_cost = charge_periods[price_col].sum() * BATTERY_CAPACITY_MWH / CHARGE_EFFICIENCY
        
        # Find 2 most expensive periods for discharging
        discharge_periods = day_data.nlargest(2, price_col)
        discharge_revenue = discharge_periods[price_col].sum() * BATTERY_CAPACITY_MWH * DISCHARGE_EFFICIENCY
        
        # Net revenue
        net_revenue = discharge_revenue - charge_cost
        
        # Calculate effective spread
        avg_discharge_price = discharge_periods[price_col].mean()
        avg_charge_price = charge_periods[price_col].mean()
        spread = avg_discharge_price - avg_charge_price
        
        results.append({
            'date': date,
            'charge_price_avg': avg_charge_price,
            'discharge_price_avg': avg_discharge_price,
            'price_spread': spread,
            'charge_cost_gbp': charge_cost,
            'discharge_revenue_gbp': discharge_revenue,
            'net_revenue_gbp': net_revenue,
            'charge_periods': ','.join(map(str, charge_periods['settlementPeriod'].tolist())),
            'discharge_periods': ','.join(map(str, discharge_periods['settlementPeriod'].tolist()))
        })
    
    return pd.DataFrame(results)


def compare_price_sources(boalf_df, disbsad_df):
    """
    Compare BOALF acceptance prices vs disbsad settlement proxy
    """
    
    logging.info("\n" + "="*80)
    logging.info("PRICE SOURCE COMPARISON")
    logging.info("="*80)
    
    # Merge on date and period
    merged = pd.merge(
        boalf_df.groupby(['settlement_date', 'settlementPeriod'])['avg_price'].mean().reset_index(),
        disbsad_df[['settlement_date', 'settlementPeriod', 'price_gbp_per_mwh']],
        on=['settlement_date', 'settlementPeriod'],
        how='inner'
    )
    
    merged['price_diff'] = merged['avg_price'] - merged['price_gbp_per_mwh']
    merged['price_diff_pct'] = (merged['price_diff'] / merged['price_gbp_per_mwh'] * 100)
    
    logging.info(f"\nMatched periods: {len(merged)}")
    logging.info(f"\nBOALF acceptance prices:")
    logging.info(f"  Average: £{merged['avg_price'].mean():.2f}/MWh")
    logging.info(f"  Range: £{merged['avg_price'].min():.2f} to £{merged['avg_price'].max():.2f}/MWh")
    
    logging.info(f"\nDisbsad settlement proxy:")
    logging.info(f"  Average: £{merged['price_gbp_per_mwh'].mean():.2f}/MWh")
    logging.info(f"  Range: £{merged['price_gbp_per_mwh'].min():.2f} to £{merged['price_gbp_per_mwh'].max():.2f}/MWh")
    
    logging.info(f"\nPrice difference (BOALF - disbsad):")
    logging.info(f"  Average: £{merged['price_diff'].mean():.2f}/MWh ({merged['price_diff_pct'].mean():.1f}%)")
    logging.info(f"  Std dev: £{merged['price_diff'].std():.2f}/MWh")
    
    return merged


def main():
    """Main analysis execution"""
    
    logging.info("="*80)
    logging.info("BATTERY ARBITRAGE ANALYSIS - BOD ACCEPTANCE PRICES")
    logging.info("="*80)
    logging.info(f"Battery: {BATTERY_CAPACITY_MWH} MWh capacity")
    logging.info(f"Cycles: {MAX_CYCLES_PER_DAY} per day")
    logging.info(f"Efficiency: {ROUND_TRIP_EFFICIENCY*100}% round-trip")
    logging.info("")
    
    # Initialize BigQuery client
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    # Analysis periods
    periods = [
        ("2025-10-17", "2025-10-23", "High-price week"),
        ("2025-10-24", "2025-10-25", "Low-price weekend"),
        ("2025-10-01", "2025-10-31", "Full October")
    ]
    
    for start_date, end_date, period_name in periods:
        logging.info("\n" + "="*80)
        logging.info(f"Period: {period_name} ({start_date} to {end_date})")
        logging.info("="*80)
        
        # Get BOALF acceptance prices (OFFER only for discharge revenue)
        boalf_df = get_boalf_prices(client, start_date, end_date)
        boalf_offers = boalf_df[boalf_df['acceptanceType'] == 'OFFER'].copy()
        
        if len(boalf_offers) == 0:
            logging.warning(f"No BOALF OFFER data for {period_name}")
            continue
        
        # Get disbsad settlement proxy
        disbsad_df = get_disbsad_prices(client, start_date, end_date)
        
        # Calculate revenue using BOALF prices
        logging.info("\n📊 BOALF Acceptance Prices Analysis:")
        boalf_revenue = calculate_arbitrage_revenue(boalf_offers, price_col='avg_price')
        
        if len(boalf_revenue) > 0:
            logging.info(f"  Days analyzed: {len(boalf_revenue)}")
            logging.info(f"  Total revenue: £{boalf_revenue['net_revenue_gbp'].sum():.2f}")
            logging.info(f"  Average daily: £{boalf_revenue['net_revenue_gbp'].mean():.2f}")
            logging.info(f"  Best day: £{boalf_revenue['net_revenue_gbp'].max():.2f}")
            logging.info(f"  Worst day: £{boalf_revenue['net_revenue_gbp'].min():.2f}")
            logging.info(f"  Average spread: £{boalf_revenue['price_spread'].mean():.2f}/MWh")
        
        # Calculate revenue using disbsad prices
        logging.info("\n📊 Disbsad Settlement Proxy Analysis:")
        disbsad_revenue = calculate_arbitrage_revenue(disbsad_df, price_col='price_gbp_per_mwh')
        
        if len(disbsad_revenue) > 0:
            logging.info(f"  Days analyzed: {len(disbsad_revenue)}")
            logging.info(f"  Total revenue: £{disbsad_revenue['net_revenue_gbp'].sum():.2f}")
            logging.info(f"  Average daily: £{disbsad_revenue['net_revenue_gbp'].mean():.2f}")
            logging.info(f"  Best day: £{disbsad_revenue['net_revenue_gbp'].max():.2f}")
            logging.info(f"  Worst day: £{disbsad_revenue['net_revenue_gbp'].min():.2f}")
            logging.info(f"  Average spread: £{disbsad_revenue['price_spread'].mean():.2f}/MWh")
        
        # Compare revenue estimates
        if len(boalf_revenue) > 0 and len(disbsad_revenue) > 0:
            boalf_total = boalf_revenue['net_revenue_gbp'].sum()
            disbsad_total = disbsad_revenue['net_revenue_gbp'].sum()
            diff = boalf_total - disbsad_total
            diff_pct = (diff / disbsad_total * 100) if disbsad_total != 0 else 0
            
            logging.info("\n💰 REVENUE COMPARISON:")
            logging.info(f"  BOALF total: £{boalf_total:.2f}")
            logging.info(f"  Disbsad total: £{disbsad_total:.2f}")
            logging.info(f"  Difference: £{diff:.2f} ({diff_pct:+.1f}%)")
            
            if diff > 0:
                logging.info(f"  ✅ BOALF shows £{diff:.2f} higher revenue potential")
            else:
                logging.info(f"  ⚠️  Disbsad shows £{abs(diff):.2f} higher (unexpected)")
        
        # Price source comparison
        if len(boalf_offers) > 0 and len(disbsad_df) > 0:
            compare_price_sources(boalf_offers, disbsad_df)
    
    logging.info("\n" + "="*80)
    logging.info("✅ ANALYSIS COMPLETE")
    logging.info("="*80)
    logging.info("\nKey Findings:")
    logging.info("1. BOALF provides individual acceptance prices (more granular)")
    logging.info("2. Disbsad provides settlement averages (broader market view)")
    logging.info("3. Price differences indicate actual vs average market clearing")
    logging.info("4. Higher BOALF prices = VLP units accepting at premium rates")


if __name__ == "__main__":
    main()
