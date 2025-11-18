#!/usr/bin/env python3
"""
Enhanced Battery Profit Analysis with Duration & Advanced Metrics
=================================================================

Calculates:
1. Profit per cycle (if duration known)
2. Revenue per MW capacity
3. Cycle efficiency (implied utilization)
4. ROI estimates (if CAPEX assumed)
5. Comparison: VLP vs Direct performance

Usage:
    .venv/bin/python battery_profit_analysis.py
"""

import os
import pandas as pd
from google.cloud import bigquery
from datetime import datetime

# ==================== CONFIG ====================
PROJECT_ID = "inner-cinema-476211-u9"
DATASET_ID = "uk_energy_prod"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

# Battery duration assumptions (hours) - typical UK BESS
# Source: Most UK grid-scale batteries are 1-2 hour duration
DURATION_HOURS = {
    "default": 2.0,  # Most common
    "T_DOREW-1": 2.0,
    "T_DOREW-2": 2.0,
    "T_SOKYW-1": 1.5,
    "T_CREAW-1": 2.0,
    "T_LIMKW-1": 2.0,
}

# CAPEX estimates (£/kWh) for ROI calculation
# Source: UK BESS costs 2023-2025
CAPEX_PER_KWH = 200  # £200/kWh typical for 2-hour BESS

# Analysis period
ANALYSIS_DAYS = 365

def get_battery_revenue_data():
    """Load latest battery revenue analysis results"""
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    WITH market_prices AS (
      SELECT 
        settlementDate,
        settlementPeriod,
        AVG(CASE WHEN price > 0 THEN price END) as avg_price_gbp_mwh
      FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_mid`
      WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {ANALYSIS_DAYS} DAY)
        AND price > 0
      GROUP BY settlementDate, settlementPeriod
    ),
    battery_acceptances AS (
      SELECT 
        boalf.bmUnit,
        boalf.settlementDate,
        boalf.settlementPeriodFrom,
        boalf.levelFrom,
        boalf.levelTo,
        (boalf.levelTo - boalf.levelFrom) as mw_change,
        boalf.acceptanceNumber,
        prices.avg_price_gbp_mwh,
        
        -- Categorize action type
        CASE 
          WHEN (boalf.levelTo - boalf.levelFrom) > 0 THEN 'discharge'
          WHEN (boalf.levelTo - boalf.levelFrom) < 0 THEN 'charge'
          ELSE 'neutral'
        END as action_type,
        
        -- Calculate revenue/cost for this acceptance
        CASE 
          WHEN (boalf.levelTo - boalf.levelFrom) > 0
          THEN (boalf.levelTo - boalf.levelFrom) * COALESCE(prices.avg_price_gbp_mwh, 0) * 0.5
          WHEN (boalf.levelTo - boalf.levelFrom) < 0
          THEN ABS(boalf.levelTo - boalf.levelFrom) * COALESCE(prices.avg_price_gbp_mwh, 0) * 0.5
          ELSE 0 
        END as gbp_value
        
      FROM `{PROJECT_ID}.{DATASET_ID}.bmrs_boalf` boalf
      LEFT JOIN market_prices prices
        ON boalf.settlementDate = prices.settlementDate 
        AND boalf.settlementPeriodFrom = prices.settlementPeriod
      WHERE boalf.settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL {ANALYSIS_DAYS} DAY)
        AND (boalf.bmUnit LIKE '%B-%' OR boalf.bmUnit LIKE '%B-_')  -- Battery filter
    ),
    battery_stats AS (
      SELECT 
        bmUnit,
        COUNT(*) as total_acceptances,
        COUNT(DISTINCT settlementDate) as active_days,
        
        -- Discharge stats
        COUNT(CASE WHEN action_type = 'discharge' THEN 1 END) as discharge_count,
        SUM(CASE WHEN action_type = 'discharge' THEN mw_change END) as total_mw_discharged,
        SUM(CASE WHEN action_type = 'discharge' THEN gbp_value END) as discharge_revenue_gbp,
        AVG(CASE WHEN action_type = 'discharge' THEN avg_price_gbp_mwh END) as avg_discharge_price,
        MAX(CASE WHEN action_type = 'discharge' THEN mw_change END) as max_discharge_mw,
        
        -- Charge stats
        COUNT(CASE WHEN action_type = 'charge' THEN 1 END) as charge_count,
        SUM(CASE WHEN action_type = 'charge' THEN ABS(mw_change) END) as total_mw_charged,
        SUM(CASE WHEN action_type = 'charge' THEN gbp_value END) as charge_cost_gbp,
        AVG(CASE WHEN action_type = 'charge' THEN avg_price_gbp_mwh END) as avg_charge_price,
        MAX(CASE WHEN action_type = 'charge' THEN ABS(mw_change) END) as max_charge_mw,
        
        -- Net
        SUM(CASE WHEN action_type = 'discharge' THEN gbp_value 
                 WHEN action_type = 'charge' THEN -gbp_value 
                 ELSE 0 END) as net_revenue_gbp,
        
        -- Capacity proxy
        MAX(GREATEST(ABS(levelFrom), ABS(levelTo))) as max_capacity_mw,
        AVG(ABS(mw_change)) as avg_action_size_mw
        
      FROM battery_acceptances
      GROUP BY bmUnit
    )
    SELECT * FROM battery_stats
    WHERE total_acceptances > 100  -- Filter to active batteries
    ORDER BY net_revenue_gbp DESC
    """
    
    df = client.query(query).to_dataframe()
    return df

def enhance_with_duration_analysis(df):
    """Add duration-based metrics"""
    
    # Add duration (hours) and energy capacity (MWh)
    df['duration_hours'] = df['bmUnit'].map(DURATION_HOURS).fillna(DURATION_HOURS['default'])
    df['energy_capacity_mwh'] = df['max_capacity_mw'] * df['duration_hours']
    
    # Calculate cycles (discharge count = approximate full cycles)
    df['estimated_cycles'] = df['discharge_count']
    
    # Profit per cycle
    df['profit_per_cycle_gbp'] = df['net_revenue_gbp'] / df['estimated_cycles'].replace(0, 1)
    
    # Revenue per MW of capacity
    df['revenue_per_mw_gbp'] = df['net_revenue_gbp'] / df['max_capacity_mw'].replace(0, 1)
    
    # Revenue per MWh of energy capacity
    df['revenue_per_mwh_capacity_gbp'] = df['net_revenue_gbp'] / df['energy_capacity_mwh'].replace(0, 1)
    
    # Utilization metrics
    df['avg_cycles_per_day'] = df['estimated_cycles'] / df['active_days'].replace(0, 1)
    df['utilization_pct'] = (df['avg_cycles_per_day'] / 2.0) * 100  # 2 cycles/day = 100%
    
    # Arbitrage efficiency (how much spread captured per cycle)
    df['price_spread_captured_per_cycle'] = (
        (df['avg_discharge_price'] - df['avg_charge_price']).fillna(0)
    )
    
    # Round-trip efficiency proxy (revenue vs cost ratio)
    df['round_trip_efficiency_pct'] = (
        (df['discharge_revenue_gbp'] / df['charge_cost_gbp'].replace(0, 1)) * 100
    ).clip(upper=100)
    
    # ROI calculation (simple payback period)
    df['capex_estimate_gbp'] = df['energy_capacity_mwh'] * 1000 * CAPEX_PER_KWH
    df['simple_payback_years'] = df['capex_estimate_gbp'] / df['net_revenue_gbp'].replace(0, 1)
    df['annual_roi_pct'] = (df['net_revenue_gbp'] / df['capex_estimate_gbp']) * 100
    
    # Energy throughput (MWh)
    df['total_energy_discharged_mwh'] = df['total_mw_discharged'] * 0.5  # MW * 0.5h per SP
    df['total_energy_charged_mwh'] = df['total_mw_charged'] * 0.5
    
    return df

def identify_vlp_batteries(df):
    """Add VLP classification (simplified - based on BMU naming patterns)"""
    vlp_patterns = ['E_', 'T_', '2__', 'C__', 'M__']
    
    def is_vlp(bmu):
        return any(bmu.startswith(p) for p in vlp_patterns)
    
    df['is_vlp'] = df['bmUnit'].apply(is_vlp)
    df['operator_type'] = df['is_vlp'].map({True: 'VLP', False: 'Direct'})
    
    return df

def generate_summary_stats(df):
    """Generate summary statistics by operator type"""
    
    summary = []
    
    for op_type in ['VLP', 'Direct']:
        subset = df[df['operator_type'] == op_type]
        
        if len(subset) == 0:
            continue
            
        stats = {
            'operator_type': op_type,
            'n_batteries': len(subset),
            'total_capacity_mw': subset['max_capacity_mw'].sum(),
            'total_energy_capacity_mwh': subset['energy_capacity_mwh'].sum(),
            'total_net_revenue_gbp': subset['net_revenue_gbp'].sum(),
            'avg_profit_per_cycle': subset['profit_per_cycle_gbp'].mean(),
            'avg_revenue_per_mw': subset['revenue_per_mw_gbp'].mean(),
            'avg_cycles_per_day': subset['avg_cycles_per_day'].mean(),
            'avg_utilization_pct': subset['utilization_pct'].mean(),
            'avg_spread_captured': subset['price_spread_captured_per_cycle'].mean(),
            'avg_roi_pct': subset['annual_roi_pct'].mean(),
            'avg_payback_years': subset['simple_payback_years'].mean(),
            'avg_rt_efficiency': subset['round_trip_efficiency_pct'].mean(),
        }
        
        summary.append(stats)
    
    return pd.DataFrame(summary)

def format_currency(val):
    """Format as currency with K/M suffix"""
    if abs(val) >= 1_000_000:
        return f"£{val/1_000_000:.2f}M"
    elif abs(val) >= 1_000:
        return f"£{val/1_000:.1f}K"
    else:
        return f"£{val:.0f}"

def print_report(df, summary_df):
    """Print comprehensive analysis report"""
    
    print("\n" + "="*80)
    print("🔋 ENHANCED BATTERY PROFIT ANALYSIS")
    print("="*80)
    print(f"Analysis Period: Last {ANALYSIS_DAYS} days")
    print(f"Batteries Analyzed: {len(df)}")
    print(f"Assumptions: {DURATION_HOURS['default']}-hour duration (default), £{CAPEX_PER_KWH}/kWh CAPEX")
    print("="*80)
    
    print("\n📊 TOP 10 PERFORMERS (by Net Revenue)\n")
    
    top10 = df.nlargest(10, 'net_revenue_gbp')
    
    for idx, row in top10.iterrows():
        print(f"{row['bmUnit']} [{row['operator_type']}]")
        print(f"  💰 Net Revenue: {format_currency(row['net_revenue_gbp'])} over {row['active_days']} days")
        print(f"  ⚡ Capacity: {row['max_capacity_mw']:.1f} MW × {row['duration_hours']:.1f}h = {row['energy_capacity_mwh']:.1f} MWh")
        print(f"  🔄 Cycles: {row['estimated_cycles']:,.0f} total ({row['avg_cycles_per_day']:.2f}/day)")
        print(f"  💵 Profit per Cycle: {format_currency(row['profit_per_cycle_gbp'])}")
        print(f"  📈 Revenue per MW: {format_currency(row['revenue_per_mw_gbp'])}/MW")
        print(f"  📊 Utilization: {row['utilization_pct']:.1f}%")
        print(f"  💱 Spread Captured: £{row['price_spread_captured_per_cycle']:.2f}/MWh per cycle")
        print(f"  🔋 Round-trip Efficiency: {row['round_trip_efficiency_pct']:.1f}%")
        print(f"  💎 Annual ROI: {row['annual_roi_pct']:.1f}% | Payback: {row['simple_payback_years']:.1f} years")
        print(f"  📦 Energy Throughput: {row['total_energy_discharged_mwh']:.0f} MWh discharged")
        print()
    
    print("="*80)
    print("🏆 VLP vs DIRECT OPERATOR COMPARISON")
    print("="*80)
    
    for _, row in summary_df.iterrows():
        print(f"\n{row['operator_type']} Operators:")
        print(f"  Batteries: {row['n_batteries']}")
        print(f"  Total Capacity: {row['total_capacity_mw']:.0f} MW ({row['total_energy_capacity_mwh']:.0f} MWh)")
        print(f"  Total Revenue: {format_currency(row['total_net_revenue_gbp'])}")
        print(f"  Avg Profit/Cycle: {format_currency(row['avg_profit_per_cycle'])}")
        print(f"  Avg Revenue/MW: {format_currency(row['avg_revenue_per_mw'])}/MW")
        print(f"  Avg Cycles/Day: {row['avg_cycles_per_day']:.2f}")
        print(f"  Avg Utilization: {row['avg_utilization_pct']:.1f}%")
        print(f"  Avg Spread Captured: £{row['avg_spread_captured']:.2f}/MWh")
        print(f"  Avg ROI: {row['avg_roi_pct']:.1f}%/year")
        print(f"  Avg Payback: {row['avg_payback_years']:.1f} years")
        print(f"  Avg RT Efficiency: {row['avg_rt_efficiency']:.1f}%")
    
    print("\n" + "="*80)
    print("💡 KEY INSIGHTS")
    print("="*80)
    
    # Calculate insights
    vlp_row = summary_df[summary_df['operator_type'] == 'VLP'].iloc[0] if len(summary_df[summary_df['operator_type'] == 'VLP']) > 0 else None
    direct_row = summary_df[summary_df['operator_type'] == 'Direct'].iloc[0] if len(summary_df[summary_df['operator_type'] == 'Direct']) > 0 else None
    
    if vlp_row is not None and direct_row is not None:
        print(f"\n1. UTILIZATION:")
        print(f"   VLP: {vlp_row['avg_cycles_per_day']:.2f} cycles/day ({vlp_row['avg_utilization_pct']:.1f}%)")
        print(f"   Direct: {direct_row['avg_cycles_per_day']:.2f} cycles/day ({direct_row['avg_utilization_pct']:.1f}%)")
        
        print(f"\n2. PROFITABILITY:")
        print(f"   VLP: {format_currency(vlp_row['avg_profit_per_cycle'])}/cycle")
        print(f"   Direct: {format_currency(direct_row['avg_profit_per_cycle'])}/cycle")
        
        print(f"\n3. EFFICIENCY:")
        print(f"   VLP: £{vlp_row['avg_spread_captured']:.2f}/MWh spread captured")
        print(f"   Direct: £{direct_row['avg_spread_captured']:.2f}/MWh spread captured")
        
        print(f"\n4. ROI:")
        print(f"   VLP: {vlp_row['avg_roi_pct']:.1f}% annual return")
        print(f"   Direct: {direct_row['avg_roi_pct']:.1f}% annual return")
    
    # Top performer
    best = df.nlargest(1, 'profit_per_cycle_gbp').iloc[0]
    print(f"\n5. BEST PERFORMER:")
    print(f"   {best['bmUnit']} [{best['operator_type']}]")
    print(f"   {format_currency(best['profit_per_cycle_gbp'])}/cycle")
    print(f"   {best['avg_cycles_per_day']:.2f} cycles/day")
    print(f"   {best['annual_roi_pct']:.1f}% annual ROI")
    
    print("\n" + "="*80)

def main():
    print("⏳ Loading battery revenue data from BigQuery...")
    df = get_battery_revenue_data()
    
    print(f"✅ Loaded {len(df)} batteries with acceptance data")
    
    print("🔧 Calculating duration-based metrics...")
    df = enhance_with_duration_analysis(df)
    
    print("🏢 Identifying VLP operators...")
    df = identify_vlp_batteries(df)
    
    print("📊 Generating summary statistics...")
    summary_df = generate_summary_stats(df)
    
    # Generate report
    print_report(df, summary_df)
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"battery_profit_analysis_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    print(f"\n💾 Detailed results saved: {output_file}")
    
    summary_file = f"battery_profit_summary_{timestamp}.csv"
    summary_df.to_csv(summary_file, index=False)
    print(f"💾 Summary stats saved: {summary_file}")
    
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main()
