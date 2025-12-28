#!/usr/bin/env python3
"""
Detect Network Gas Supply Emergency Acceptance (NGSEA) Events in P114 Data

This script analyzes P114 settlement data to identify potential gas emergency
curtailment events where generators were paid to turn down.

Key indicators:
- High system prices (>£80/MWh) indicating supply stress
- Negative energy (reductions) for gas units
- Clustered timing (multiple units same period)
- Negative revenue (generators paid to reduce)

Usage:
    python3 detect_ngsea_events.py [start_date] [end_date]
    
Example:
    python3 detect_ngsea_events.py 2024-01-01 2024-12-31
"""

import os
import sys
from datetime import datetime
from google.cloud import bigquery
import pandas as pd

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

# Thresholds
HIGH_PRICE_THRESHOLD = 80.0  # £/MWh - indicates supply stress
MIN_REDUCTION_MWH = 50.0     # MWh - minimum curtailment to consider
MIN_UNITS_AFFECTED = 3       # Minimum units for event classification

def detect_ngsea_candidates(start_date, end_date):
    """
    Detect potential NGSEA events by finding periods with:
    - High system prices
    - Multiple gas units curtailed
    - Large negative energy volumes
    """
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    WITH curtailments AS (
        SELECT 
            settlement_date,
            settlement_period,
            bm_unit_id,
            value2 as energy_mwh,
            system_price,
            value2 * system_price * multiplier as revenue_gbp,
            settlement_run
        FROM `{PROJECT_ID}.{DATASET}.elexon_p114_s0142_bpi`
        WHERE settlement_date BETWEEN '{start_date}' AND '{end_date}'
          AND value2 < -{MIN_REDUCTION_MWH}  -- Significant reductions only
          AND bm_unit_id LIKE 'T_%'  -- Thermal generators (mostly gas)
          AND settlement_run = 'RF'  -- Final settlement only
          AND system_price > {HIGH_PRICE_THRESHOLD}  -- High price periods
    ),
    period_summary AS (
        SELECT 
            settlement_date,
            settlement_period,
            COUNT(DISTINCT bm_unit_id) as units_affected,
            SUM(energy_mwh) as total_reduction_mwh,
            AVG(system_price) as avg_system_price,
            SUM(revenue_gbp) as total_payment_gbp,
            STRING_AGG(bm_unit_id, ', ' ORDER BY energy_mwh ASC) as affected_units
        FROM curtailments
        GROUP BY settlement_date, settlement_period
        HAVING COUNT(DISTINCT bm_unit_id) >= {MIN_UNITS_AFFECTED}  -- Multiple units = event
    )
    SELECT 
        settlement_date,
        settlement_period,
        units_affected,
        ROUND(total_reduction_mwh, 2) as total_reduction_mwh,
        ROUND(avg_system_price, 2) as avg_system_price,
        ROUND(total_payment_gbp, 2) as total_payment_gbp,
        affected_units
    FROM period_summary
    ORDER BY settlement_date, settlement_period
    """
    
    print(f"\n🔍 DETECTING NGSEA EVENTS ({start_date} to {end_date})")
    print("="*120)
    print(f"Criteria: System price >{HIGH_PRICE_THRESHOLD:.0f} £/MWh, {MIN_UNITS_AFFECTED}+ units curtailed, {MIN_REDUCTION_MWH:.0f}+ MWh reduction")
    print("="*120)
    print()
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        print("❌ No NGSEA candidate events found in specified period.")
        print(f"\nThis could mean:")
        print(f"  • No gas emergencies occurred")
        print(f"  • System prices stayed below £{HIGH_PRICE_THRESHOLD}/MWh")
        print(f"  • Curtailments were smaller than {MIN_REDUCTION_MWH} MWh")
        print(f"  • P114 data not yet available for this period")
        return None
    
    print(f"✅ Found {len(df)} potential NGSEA periods\n")
    print(df.to_string(index=False))
    print()
    
    # Summary statistics
    total_events = len(df)
    total_reductions = df['total_reduction_mwh'].sum()
    total_payments = df['total_payment_gbp'].sum()
    avg_price = df['avg_system_price'].mean()
    unique_days = df['settlement_date'].nunique()
    
    print("\n" + "="*120)
    print("📊 NGSEA EVENT SUMMARY")
    print("="*120)
    print(f"  Event Periods: {total_events}")
    print(f"  Unique Days: {unique_days}")
    print(f"  Total Curtailment: {total_reductions:,.2f} MWh")
    print(f"  Total Payments: £{abs(total_payments):,.2f}")
    print(f"  Average System Price: £{avg_price:.2f}/MWh")
    print(f"  Average Payment per Period: £{abs(total_payments)/total_events:,.2f}")
    print()
    
    # Top 5 most expensive events
    print("\n🔥 TOP 5 MOST EXPENSIVE CURTAILMENT PERIODS:")
    print("-"*120)
    top5 = df.nlargest(5, 'total_payment_gbp', keep='first')
    for idx, row in top5.iterrows():
        period_start = f"{(row['settlement_period']-1)*30//60:02d}:{(row['settlement_period']-1)*30%60:02d}"
        period_end = f"{row['settlement_period']*30//60:02d}:{row['settlement_period']*30%60:02d}"
        print(f"\n  {row['settlement_date']} Period {row['settlement_period']} ({period_start}-{period_end})")
        print(f"    Units affected: {row['units_affected']}")
        print(f"    Total reduction: {row['total_reduction_mwh']:,.2f} MWh")
        print(f"    System price: £{row['avg_system_price']:.2f}/MWh")
        print(f"    Payment to generators: £{abs(row['total_payment_gbp']):,.2f}")
        print(f"    Units: {row['affected_units'][:100]}{'...' if len(row['affected_units']) > 100 else ''}")
    
    return df


def analyze_ngsea_by_unit(start_date, end_date):
    """
    Analyze which units were most frequently curtailed during NGSEA events
    """
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    query = f"""
    SELECT 
        bm_unit_id,
        COUNT(DISTINCT CONCAT(settlement_date, '-', settlement_period)) as periods_curtailed,
        COUNT(DISTINCT settlement_date) as days_curtailed,
        SUM(value2) as total_reduction_mwh,
        AVG(system_price) as avg_price,
        SUM(value2 * system_price * multiplier) as total_payment_gbp
    FROM `{PROJECT_ID}.{DATASET}.elexon_p114_s0142_bpi`
    WHERE settlement_date BETWEEN '{start_date}' AND '{end_date}'
      AND value2 < -{MIN_REDUCTION_MWH}
      AND bm_unit_id LIKE 'T_%'
      AND settlement_run = 'RF'
      AND system_price > {HIGH_PRICE_THRESHOLD}
    GROUP BY bm_unit_id
    HAVING COUNT(*) >= 3  -- At least 3 curtailment events
    ORDER BY total_payment_gbp ASC
    LIMIT 20
    """
    
    print("\n" + "="*120)
    print("🏭 TOP 20 MOST FREQUENTLY CURTAILED UNITS")
    print("="*120)
    print()
    
    df = client.query(query).to_dataframe()
    
    if df.empty:
        print("❌ No units with significant curtailment history found.")
        return None
    
    print(df.to_string(index=False))
    print()
    print("💡 Interpretation:")
    print("  • Negative 'total_payment_gbp' = generator RECEIVED payment")
    print("  • Negative 'total_reduction_mwh' = generator REDUCED output")
    print("  • Units with most curtailments likely have best negative bid prices")
    print()
    
    return df


def main():
    """Main execution"""
    
    # Parse command line arguments
    if len(sys.argv) == 3:
        start_date = sys.argv[1]
        end_date = sys.argv[2]
    else:
        # Default: analyze full available dataset
        start_date = "2021-10-01"
        end_date = "2024-12-31"
        print(f"ℹ️  No date range specified, using full available period: {start_date} to {end_date}")
        print(f"   Usage: python3 {sys.argv[0]} <start_date> <end_date>")
        print()
    
    # Detect NGSEA events
    events_df = detect_ngsea_candidates(start_date, end_date)
    
    if events_df is not None:
        # Analyze by unit
        units_df = analyze_ngsea_by_unit(start_date, end_date)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        events_file = f"ngsea_events_{timestamp}.csv"
        units_file = f"ngsea_units_{timestamp}.csv"
        
        events_df.to_csv(events_file, index=False)
        print(f"\n💾 Saved event data to: {events_file}")
        
        if units_df is not None:
            units_df.to_csv(units_file, index=False)
            print(f"💾 Saved unit data to: {units_file}")
    
    print("\n" + "="*120)
    print("✅ NGSEA DETECTION COMPLETE")
    print("="*120)
    print()
    print("📚 Related Documentation:")
    print("  • GAS_EMERGENCY_CURTAILMENT_NGSEA_GUIDE.md - Detailed NGSEA explanation")
    print("  • BSC_SECTION_Q_FRAMEWORK.md - BSC settlement data framework")
    print("  • P114_SETTLEMENT_VALUE_EXPLAINED.md - Settlement calculation mechanics")
    print()


if __name__ == "__main__":
    main()
