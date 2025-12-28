#!/usr/bin/env python3
"""
Enhanced NGSEA Detection with Statistical Scoring Algorithm

Detects Network Gas Supply Emergency Acceptances using multi-feature scoring:
- Feature A: Turn-down signature (large negative Δ metered) [2 points]
- Feature B: No matching BOALF or SO-Flag TRUE [2 points]  
- Feature C: FPN mismatch/corrections (BSCP18) [1 point]
- Feature D: NESO constraint cost spike [1 point]

Total Score: 2*A + 2*B + 1*C + 1*D
Flag as NGSEA if score ≥ 5

Usage:
    python3 detect_ngsea_statistical.py [start_date] [end_date]
    
Example:
    python3 detect_ngsea_statistical.py 2024-01-01 2024-12-31
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

# Scoring weights
WEIGHT_A = 2  # Turn-down signature
WEIGHT_B = 2  # No BOALF or SO-Flag
WEIGHT_C = 1  # FPN mismatch
WEIGHT_D = 1  # Constraint cost spike
NGSEA_THRESHOLD = 5  # Flag if score >= 5

# Thresholds
HIGH_PRICE_THRESHOLD = 80.0  # £/MWh
MIN_REDUCTION_MWH = 50.0     # MWh
MIN_UNITS_AFFECTED = 3       # Units


def calculate_feature_a_turndown_signature(client, start_date, end_date):
    """
    Feature A: Large negative Δ metered (turn-down signature)
    
    Criteria:
    - Negative energy > 50 MWh
    - Sudden reduction (compared to previous period)
    - Gas unit (T_* prefix)
    
    Returns: DataFrame with settlement_date, settlement_period, bm_unit_id, score_a
    """
    
    query = f"""
    WITH p114_data AS (
        SELECT 
            settlement_date,
            settlement_period,
            bm_unit_id,
            value2 as energy_mwh,
            system_price,
            LAG(value2) OVER (PARTITION BY bm_unit_id ORDER BY settlement_date, settlement_period) as prev_energy_mwh
        FROM `{PROJECT_ID}.{DATASET}.elexon_p114_s0142_bpi`
        WHERE settlement_date BETWEEN '{start_date}' AND '{end_date}'
          AND bm_unit_id LIKE 'T_%'
          AND settlement_run = 'RF'
    )
    SELECT 
        settlement_date,
        settlement_period,
        bm_unit_id,
        energy_mwh,
        prev_energy_mwh,
        energy_mwh - prev_energy_mwh as delta_mwh,
        system_price,
        CASE 
            WHEN energy_mwh < -{MIN_REDUCTION_MWH} 
                AND ABS(energy_mwh - prev_energy_mwh) > {MIN_REDUCTION_MWH}
            THEN {WEIGHT_A}
            ELSE 0
        END as score_a
    FROM p114_data
    WHERE energy_mwh < -{MIN_REDUCTION_MWH}  -- Significant reduction
    """
    
    return client.query(query).to_dataframe()


def calculate_feature_b_no_boalf_or_soflag(client, start_date, end_date, feature_a_df):
    """
    Feature B: No matching BOALF acceptance OR SO-Flag TRUE
    
    Criteria:
    - P114 shows reduction but no BOALF acceptance found
    - OR BOALF exists with SO-Flag = TRUE (constructed acceptance)
    
    Returns: DataFrame with score_b column added
    """
    
    query = f"""
    WITH boalf_acceptances AS (
        SELECT 
            CAST(settlementDate AS DATE) as settlement_date,
            settlementPeriod as settlement_period,
            bmUnitId as bm_unit_id,
            soFlag,
            COUNT(*) as acceptance_count
        FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
        WHERE CAST(settlementDate AS DATE) BETWEEN '{start_date}' AND '{end_date}'
          AND acceptanceType = 'BID'
          AND bmUnitId LIKE 'T_%'
        GROUP BY settlement_date, settlement_period, bm_unit_id, soFlag
    )
    SELECT 
        settlement_date,
        settlement_period,
        bm_unit_id,
        soFlag,
        acceptance_count
    FROM boalf_acceptances
    """
    
    boalf_df = client.query(query).to_dataframe()
    
    # Merge with Feature A data
    merged = feature_a_df.merge(
        boalf_df,
        on=['settlement_date', 'settlement_period', 'bm_unit_id'],
        how='left'
    )
    
    # Calculate score_b
    merged['score_b'] = merged.apply(lambda row: 
        WEIGHT_B if (pd.isna(row['acceptance_count']) or row['soFlag'] == True) else 0, 
        axis=1
    )
    
    return merged


def calculate_feature_c_fpn_mismatch(client, start_date, end_date, df):
    """
    Feature C: FPN mismatch/corrections (BSCP18 indicator)
    
    Criteria:
    - Compare FPN to actual metered (from P114)
    - Large discrepancy suggests post-event correction
    
    Note: FPN data may not be available - placeholder for future
    """
    
    # TODO: Implement when FPN data available
    # For now, assign 0 (not implemented)
    df['score_c'] = 0
    df['fpn_mismatch_note'] = 'FPN data not available'
    
    return df


def calculate_feature_d_constraint_cost_spike(client, start_date, end_date, df):
    """
    Feature D: NESO constraint cost spike
    
    Criteria:
    - Check if NESO reported high constraint costs on same day
    - Cross-reference with neso_constraint_costs_unified table
    
    Note: Requires NESO data ingestion - placeholder for future
    """
    
    # TODO: Implement when NESO constraint cost data available
    # For now, use system_price as proxy
    df['score_d'] = df['system_price'].apply(lambda x: WEIGHT_D if x > 100 else 0)
    df['constraint_cost_note'] = df['system_price'].apply(
        lambda x: f'System price £{x:.2f}/MWh (proxy for constraint cost)'
    )
    
    return df


def calculate_ngsea_scores(start_date, end_date):
    """
    Main scoring function: Calculate all features and sum scores
    """
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    print(f"\n🧮 CALCULATING NGSEA STATISTICAL SCORES ({start_date} to {end_date})")
    print("="*120)
    print(f"Scoring Algorithm:")
    print(f"  Feature A (Turn-down): {WEIGHT_A} points if reduction >{MIN_REDUCTION_MWH} MWh")
    print(f"  Feature B (No BOALF/SO-Flag): {WEIGHT_B} points if no acceptance or SO-Flag TRUE")
    print(f"  Feature C (FPN mismatch): {WEIGHT_C} point if FPN differs significantly")
    print(f"  Feature D (Constraint cost spike): {WEIGHT_D} point if NESO reports high costs")
    print(f"  NGSEA Threshold: Score ≥ {NGSEA_THRESHOLD}")
    print("="*120)
    print()
    
    # Calculate Feature A (turn-down signature)
    print("📊 [1/4] Calculating Feature A (turn-down signature)...")
    feature_a_df = calculate_feature_a_turndown_signature(client, start_date, end_date)
    print(f"     Found {len(feature_a_df)} periods with significant reductions")
    
    if feature_a_df.empty:
        print("❌ No turn-down signatures found. Cannot proceed with scoring.")
        return None
    
    # Calculate Feature B (no BOALF or SO-Flag)
    print("📊 [2/4] Calculating Feature B (BOALF matching)...")
    df = calculate_feature_b_no_boalf_or_soflag(client, start_date, end_date, feature_a_df)
    no_boalf = len(df[df['score_b'] > 0])
    print(f"     Found {no_boalf} periods with no BOALF or SO-Flag TRUE")
    
    # Calculate Feature C (FPN mismatch)
    print("📊 [3/4] Calculating Feature C (FPN mismatch)...")
    df = calculate_feature_c_fpn_mismatch(client, start_date, end_date, df)
    print(f"     ⚠️ FPN data not available (feature disabled)")
    
    # Calculate Feature D (constraint cost spike)
    print("📊 [4/4] Calculating Feature D (constraint cost spike)...")
    df = calculate_feature_d_constraint_cost_spike(client, start_date, end_date, df)
    high_costs = len(df[df['score_d'] > 0])
    print(f"     Found {high_costs} periods with high constraint costs (proxy: system price >£100/MWh)")
    
    # Calculate total score
    df['total_score'] = df['score_a'] + df['score_b'] + df['score_c'] + df['score_d']
    df['ngsea_flag'] = df['total_score'] >= NGSEA_THRESHOLD
    
    # Sort by score descending
    df = df.sort_values(['total_score', 'system_price'], ascending=[False, False])
    
    return df


def aggregate_ngsea_events(df):
    """
    Aggregate individual unit scores into period-level events
    """
    
    period_summary = df.groupby(['settlement_date', 'settlement_period']).agg({
        'bm_unit_id': 'count',
        'energy_mwh': 'sum',
        'system_price': 'mean',
        'total_score': 'mean',
        'ngsea_flag': 'any',
        'score_a': 'sum',
        'score_b': 'sum',
        'score_c': 'sum',
        'score_d': 'sum'
    }).rename(columns={
        'bm_unit_id': 'units_affected',
        'energy_mwh': 'total_reduction_mwh',
        'system_price': 'avg_system_price',
        'total_score': 'avg_total_score'
    }).reset_index()
    
    # Calculate estimated payment (using system_price as proxy)
    period_summary['estimated_payment_gbp'] = (
        period_summary['total_reduction_mwh'] * 
        period_summary['avg_system_price'] * 
        0.5  # multiplier
    )
    
    # Filter to NGSEA flagged events
    ngsea_events = period_summary[period_summary['ngsea_flag']].copy()
    ngsea_events = ngsea_events.sort_values(['settlement_date', 'settlement_period'])
    
    return ngsea_events


def main():
    """Main execution"""
    
    # Parse command line arguments
    if len(sys.argv) == 3:
        start_date = sys.argv[1]
        end_date = sys.argv[2]
    else:
        # Default: analyze recent 6 months
        start_date = "2024-01-01"
        end_date = "2024-12-31"
        print(f"ℹ️  No date range specified, using: {start_date} to {end_date}")
        print(f"   Usage: python3 {sys.argv[0]} <start_date> <end_date>")
        print()
    
    # Calculate scores
    scores_df = calculate_ngsea_scores(start_date, end_date)
    
    if scores_df is None:
        print("\n❌ No data available for scoring.")
        return
    
    # Aggregate into events
    print("\n📊 AGGREGATING NGSEA EVENTS...")
    events_df = aggregate_ngsea_events(scores_df)
    
    if events_df.empty:
        print(f"❌ No events flagged as NGSEA (score ≥{NGSEA_THRESHOLD})")
        print(f"\n💡 Try lowering threshold or expanding date range.")
        
        # Show top scoring periods even if below threshold
        print(f"\n🔍 TOP 10 HIGHEST SCORING PERIODS (may be below NGSEA threshold):")
        print("-"*120)
        top_scores = scores_df.groupby(['settlement_date', 'settlement_period']).agg({
            'total_score': 'max',
            'system_price': 'mean',
            'energy_mwh': 'sum'
        }).reset_index().nlargest(10, 'total_score')
        print(top_scores.to_string(index=False))
        return
    
    # Display results
    print(f"\n✅ Found {len(events_df)} NGSEA-flagged periods")
    print("="*120)
    print("🚨 DETECTED NGSEA EVENTS")
    print("="*120)
    print()
    
    # Format and display
    display_df = events_df[[
        'settlement_date', 'settlement_period', 'units_affected',
        'total_reduction_mwh', 'avg_system_price', 'estimated_payment_gbp',
        'avg_total_score', 'score_a', 'score_b', 'score_c', 'score_d'
    ]].copy()
    
    display_df['total_reduction_mwh'] = display_df['total_reduction_mwh'].round(2)
    display_df['avg_system_price'] = display_df['avg_system_price'].round(2)
    display_df['estimated_payment_gbp'] = display_df['estimated_payment_gbp'].round(2)
    display_df['avg_total_score'] = display_df['avg_total_score'].round(1)
    
    print(display_df.to_string(index=False))
    
    # Summary statistics
    print("\n" + "="*120)
    print("📊 NGSEA EVENT SUMMARY")
    print("="*120)
    print(f"  Total Events: {len(events_df)} periods")
    print(f"  Unique Days: {events_df['settlement_date'].nunique()} days")
    print(f"  Total Curtailment: {events_df['total_reduction_mwh'].sum():,.2f} MWh")
    print(f"  Total Estimated Payments: £{abs(events_df['estimated_payment_gbp'].sum()):,.2f}")
    print(f"  Average System Price: £{events_df['avg_system_price'].mean():.2f}/MWh")
    print(f"  Average Score: {events_df['avg_total_score'].mean():.1f}")
    print()
    print("  Score Breakdown:")
    print(f"    Feature A (Turn-down): {events_df['score_a'].sum():.0f} total points")
    print(f"    Feature B (No BOALF/SO-Flag): {events_df['score_b'].sum():.0f} total points")
    print(f"    Feature C (FPN mismatch): {events_df['score_c'].sum():.0f} total points")
    print(f"    Feature D (Constraint cost): {events_df['score_d'].sum():.0f} total points")
    print()
    
    # Top 5 events
    print("🔥 TOP 5 HIGHEST SCORING EVENTS:")
    print("-"*120)
    top5 = events_df.nlargest(5, 'avg_total_score')
    for idx, row in top5.iterrows():
        period_start = f"{(row['settlement_period']-1)*30//60:02d}:{(row['settlement_period']-1)*30%60:02d}"
        period_end = f"{row['settlement_period']*30//60:02d}:{row['settlement_period']*30%60:02d}"
        print(f"\n  {row['settlement_date']} Period {row['settlement_period']} ({period_start}-{period_end})")
        print(f"    Score: {row['avg_total_score']:.1f} (A:{row['score_a']:.0f} + B:{row['score_b']:.0f} + C:{row['score_c']:.0f} + D:{row['score_d']:.0f})")
        print(f"    Units affected: {row['units_affected']}")
        print(f"    Total reduction: {abs(row['total_reduction_mwh']):,.2f} MWh")
        print(f"    System price: £{row['avg_system_price']:.2f}/MWh")
        print(f"    Estimated payment: £{abs(row['estimated_payment_gbp']):,.2f}")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    events_file = f"ngsea_events_scored_{timestamp}.csv"
    events_df.to_csv(events_file, index=False)
    print(f"\n💾 Saved period-level events to: {events_file}")
    
    units_file = f"ngsea_units_scored_{timestamp}.csv"
    scores_df.to_csv(units_file, index=False)
    print(f"💾 Saved unit-level scores to: {units_file}")
    
    print("\n" + "="*120)
    print("✅ STATISTICAL NGSEA DETECTION COMPLETE")
    print("="*120)
    print()
    print("📚 Methodology:")
    print("  • Feature A (2 pts): Large negative Δ metered (turn-down signature)")
    print("  • Feature B (2 pts): No BOALF acceptance or SO-Flag TRUE")
    print("  • Feature C (1 pt): FPN mismatch/corrections [NOT YET IMPLEMENTED]")
    print("  • Feature D (1 pt): NESO constraint cost spike [PROXY: system_price >£100]")
    print(f"  • Threshold: Score ≥ {NGSEA_THRESHOLD} flags as NGSEA")
    print()
    print("📖 Related Documentation:")
    print("  • GAS_EMERGENCY_CURTAILMENT_NGSEA_GUIDE.md - NGSEA explanation")
    print("  • NESO_CONSTRAINT_COST_PUBLICATIONS.md - Constraint cost data sources")
    print("  • BSC_SECTION_Q_FRAMEWORK.md - BSC settlement framework")
    print()
    print("🔄 Future Enhancements:")
    print("  • Implement Feature C (FPN data ingestion)")
    print("  • Integrate NESO constraint cost datasets (Feature D)")
    print("  • Machine learning scoring (train on known NGSEA events)")
    print("  • Real-time detection (monitor IRIS feed)")
    print()


if __name__ == "__main__":
    main()
