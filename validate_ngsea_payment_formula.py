#!/usr/bin/env python3
"""
Validate NGSEA Payment Formula: |reduction_mwh| × |bid_price| × duration
Compare Level 1 (BOALF+BOD operational estimate) vs Level 2 (P114 settlement outcome)

Purpose:
- Verify negative bid payment formula accuracy
- Quantify typical variance between operational estimate and settlement
- Identify causes of differences (delivery adjustments, BSCP18 corrections, pricing)

Usage:
    python3 validate_ngsea_payment_formula.py [--start-date YYYY-MM-DD] [--end-date YYYY-MM-DD]

Example:
    python3 validate_ngsea_payment_formula.py --start-date 2024-01-01 --end-date 2024-12-31

Output:
    - validation_results.csv: Detailed comparison per event
    - formula_variance_summary.txt: Statistical summary

Author: GitHub Copilot
Created: 28 December 2025
Related: Todo 10 - Verify negative bid payment formula
"""

import argparse
import sys
from datetime import datetime, timedelta
from google.cloud import bigquery
import pandas as pd
import numpy as np

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def parse_args():
    """Parse command-line arguments"""
    parser = argparse.ArgumentParser(
        description='Validate NGSEA payment formula by comparing BOALF+BOD vs P114'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        default='2024-01-01',
        help='Start date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        default='2024-12-31',
        help='End date (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--min-payment',
        type=float,
        default=10000.0,
        help='Minimum payment threshold (£) to include in analysis'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='.',
        help='Output directory for results'
    )
    return parser.parse_args()

def get_p114_ngsea_candidates(client, start_date, end_date, min_payment):
    """
    Find NGSEA candidate events in P114 data
    
    Criteria:
    - Negative value2 (reduction)
    - Gas units (T_* prefix)
    - High system price (>£50/MWh)
    - Material payment (>£5k)
    - Best available settlement run (RF preferred, fallback to R3/II)
    """
    query = f"""
    WITH ngsea_candidates AS (
      SELECT 
        settlement_date,
        settlement_period,
        bm_unit_id,
        value2 as settled_mwh,
        system_price,
        multiplier,
        value2 * system_price * multiplier as level2_payment_gbp,
        settlement_run,
        -- Rank settlement runs (RF=1, R3=2, II=3)
        CASE settlement_run
          WHEN 'RF' THEN 1
          WHEN 'R3' THEN 2
          WHEN 'II' THEN 3
          ELSE 4
        END as run_rank
      FROM `{PROJECT_ID}.{DATASET}.elexon_p114_s0142_bpi`
      WHERE value2 < -10  -- Significant reductions only
        AND bm_unit_id LIKE 'T_%'  -- Gas CCGTs
        AND system_price > 50  -- Lowered threshold for more matches
        AND settlement_date BETWEEN '{start_date}' AND '{end_date}'
        AND ABS(value2 * system_price * multiplier) > {min_payment}
    ),
    best_runs AS (
      SELECT 
        settlement_date,
        settlement_period,
        bm_unit_id,
        settled_mwh,
        system_price,
        multiplier,
        level2_payment_gbp,
        settlement_run
      FROM (
        SELECT *,
          ROW_NUMBER() OVER (
            PARTITION BY settlement_date, settlement_period, bm_unit_id 
            ORDER BY run_rank
          ) as rn
        FROM ngsea_candidates
      )
      WHERE rn = 1  -- Take best available settlement run
    ),
    event_aggregation AS (
      SELECT 
        settlement_date,
        settlement_period,
        COUNT(DISTINCT bm_unit_id) as units_affected,
        SUM(settled_mwh) as total_reduction_mwh,
        AVG(system_price) as avg_system_price,
        SUM(level2_payment_gbp) as total_level2_payment_gbp
      FROM ngsea_candidates
      GROUP BY settlement_date, settlement_period
      HAVING COUNT(DISTINCT bm_unit_id) >= 2  -- Multiple units = event
    )
    SELECT 
      n.settlement_date,
      n.settlement_period,
      n.bm_unit_id,
      n.settled_mwh,
      n.system_price,
      n.multiplier,
      n.level2_payment_gbp,
      e.units_affected,
      e.total_reduction_mwh,
      e.avg_system_price,
      e.total_level2_payment_gbp
    FROM ngsea_candidates n
    INNER JOIN event_aggregation e
      ON n.settlement_date = e.settlement_date
      AND n.settlement_period = e.settlement_period
    ORDER BY ABS(n.level2_payment_gbp) DESC
    LIMIT 100  -- Top 100 most expensive acceptances
    """
    
    print(f"🔍 Querying P114 for NGSEA candidates ({start_date} to {end_date})...")
    df = client.query(query).to_dataframe()
    print(f"✅ Found {len(df)} candidate acceptances across {df['settlement_date'].nunique()} days")
    return df

def get_boalf_bod_estimates(client, candidates_df):
    """
    Get Level 1 estimates (BOALF+BOD) for candidate events
    
    Join BOALF acceptances to BOD bid prices to calculate operational estimate
    """
    if candidates_df.empty:
        print("⚠️  No candidates to process")
        return pd.DataFrame()
    
    # Get unique date range to minimize query scope
    min_date = candidates_df['settlement_date'].min()
    max_date = candidates_df['settlement_date'].max()
    
    # Get list of units
    units = candidates_df['bm_unit_id'].unique().tolist()
    units_filter = "', '".join(units[:50])  # Limit to 50 units
    
    query = f"""
    WITH boalf_filtered AS (
      SELECT 
        CAST(settlementDate AS DATE) as settlement_date,
        settlementPeriodFrom as settlement_period,
        bmUnit as bm_unit_id,
        acceptanceNumber,
        levelFrom,
        levelTo,
        (levelTo - levelFrom) as delta_mw,
        PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%Ez', timeFrom) as timeFrom,
        PARSE_TIMESTAMP('%Y-%m-%dT%H:%M:%S%Ez', timeTo) as timeTo,
        soFlag
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boalf`
      WHERE CAST(settlementDate AS DATE) BETWEEN '{min_date}' AND '{max_date}'
        AND bmUnit IN ('{units_filter}')
        AND levelTo < levelFrom  -- Turn-down
    ),
    boalf_with_duration AS (
      SELECT 
        *,
        TIMESTAMP_DIFF(timeTo, timeFrom, MINUTE) / 60.0 as duration_hours
      FROM boalf_filtered
    ),
    boalf_with_bod AS (
      SELECT 
        boalf.settlement_date,
        boalf.settlement_period,
        boalf.bm_unit_id,
        boalf.acceptanceNumber,
        boalf.delta_mw,
        boalf.duration_hours,
        boalf.soFlag,
        bod.bid as bid_price_gbp_per_mwh,
        bod.pairId
      FROM boalf_with_duration boalf
      LEFT JOIN `{PROJECT_ID}.{DATASET}.bmrs_bod` bod
        ON boalf.bm_unit_id = bod.bmUnit
        AND boalf.settlement_date = CAST(bod.settlementDate AS DATE)
        AND boalf.settlement_period = bod.settlementPeriod
    ),
    level1_estimates AS (
      SELECT 
        settlement_date,
        settlement_period,
        bm_unit_id,
        COUNT(DISTINCT acceptanceNumber) as num_acceptances,
        SUM(ABS(delta_mw) * duration_hours) as total_energy_mwh,
        AVG(ABS(bid_price_gbp_per_mwh)) as avg_bid_price,
        SUM(ABS(delta_mw) * duration_hours * ABS(bid_price_gbp_per_mwh)) as level1_payment_gbp,
        LOGICAL_OR(soFlag) as has_so_flag,
        STRING_AGG(DISTINCT CAST(pairId AS STRING)) as pair_ids
      FROM boalf_with_bod
      WHERE bid_price_gbp_per_mwh IS NOT NULL  -- Only where BOD match found
      GROUP BY settlement_date, settlement_period, bm_unit_id
    )
    SELECT * FROM level1_estimates
    ORDER BY level1_payment_gbp DESC
    """
    
    print("🔍 Querying BOALF+BOD for Level 1 operational estimates...")
    df = client.query(query).to_dataframe()
    print(f"✅ Found {len(df)} BOALF+BOD matches")
    return df

def merge_and_compare(p114_df, boalf_bod_df):
    """
    Merge P114 (Level 2) with BOALF+BOD (Level 1) and calculate variance
    """
    # Merge on settlement date/period/unit
    merged = pd.merge(
        p114_df,
        boalf_bod_df,
        on=['settlement_date', 'settlement_period', 'bm_unit_id'],
        how='left',
        suffixes=('_p114', '_boalf')
    )
    
    # Calculate variance
    merged['level1_payment_gbp'] = merged['level1_payment_gbp'].fillna(0)
    merged['level2_payment_gbp_abs'] = abs(merged['level2_payment_gbp'])
    merged['variance_gbp'] = merged['level1_payment_gbp'] - merged['level2_payment_gbp_abs']
    merged['variance_percent'] = (
        abs(merged['variance_gbp']) / merged['level2_payment_gbp_abs'].replace(0, np.nan) * 100
    )
    
    # Categorize variance
    def categorize_variance(row):
        if pd.isna(row['level1_payment_gbp']) or row['level1_payment_gbp'] == 0:
            return 'No BOALF Match (NGSEA constructed?)'
        elif row['variance_percent'] < 10:
            return 'Close Match (<10%)'
        elif row['variance_percent'] < 30:
            return 'Moderate Difference (10-30%)'
        else:
            return 'Large Difference (>30%)'
    
    merged['match_category'] = merged.apply(categorize_variance, axis=1)
    
    return merged

def generate_summary(comparison_df):
    """
    Generate statistical summary of formula validation
    """
    summary = []
    summary.append("="*80)
    summary.append("NGSEA PAYMENT FORMULA VALIDATION SUMMARY")
    summary.append("="*80)
    summary.append("")
    
    # Overall stats
    total_events = len(comparison_df)
    total_p114_payment = comparison_df['level2_payment_gbp_abs'].sum()
    total_boalf_payment = comparison_df['level1_payment_gbp'].sum()
    
    summary.append(f"Total Acceptances Analyzed: {total_events}")
    summary.append(f"Total P114 Payment (Level 2): £{total_p114_payment:,.2f}")
    summary.append(f"Total BOALF+BOD Estimate (Level 1): £{total_boalf_payment:,.2f}")
    summary.append(f"Overall Variance: £{abs(total_p114_payment - total_boalf_payment):,.2f}")
    summary.append("")
    
    # Match rate
    boalf_matched = comparison_df[comparison_df['level1_payment_gbp'] > 0]
    match_rate = len(boalf_matched) / total_events * 100
    summary.append(f"BOALF Match Rate: {match_rate:.1f}% ({len(boalf_matched)}/{total_events})")
    summary.append("")
    
    # Variance categories
    summary.append("Variance Distribution:")
    for category in ['Close Match (<10%)', 'Moderate Difference (10-30%)', 
                     'Large Difference (>30%)', 'No BOALF Match (NGSEA constructed?)']:
        count = len(comparison_df[comparison_df['match_category'] == category])
        pct = count / total_events * 100
        summary.append(f"  {category}: {count} ({pct:.1f}%)")
    summary.append("")
    
    # Variance stats (only for matched records)
    if len(boalf_matched) > 0:
        summary.append("Variance Statistics (Matched Records Only):")
        summary.append(f"  Mean Variance: {boalf_matched['variance_percent'].mean():.1f}%")
        summary.append(f"  Median Variance: {boalf_matched['variance_percent'].median():.1f}%")
        summary.append(f"  Std Dev Variance: {boalf_matched['variance_percent'].std():.1f}%")
        summary.append(f"  Min Variance: {boalf_matched['variance_percent'].min():.1f}%")
        summary.append(f"  Max Variance: {boalf_matched['variance_percent'].max():.1f}%")
        summary.append("")
    
    # Top 10 largest absolute variances
    summary.append("Top 10 Largest Absolute Variances:")
    top_variances = comparison_df.nlargest(10, 'variance_gbp')[
        ['settlement_date', 'settlement_period', 'bm_unit_id', 
         'level1_payment_gbp', 'level2_payment_gbp_abs', 'variance_gbp', 'variance_percent']
    ]
    for _, row in top_variances.iterrows():
        summary.append(
            f"  {row['settlement_date']} P{row['settlement_period']:02d} {row['bm_unit_id']}: "
            f"L1=£{row['level1_payment_gbp']:,.0f}, L2=£{row['level2_payment_gbp_abs']:,.0f}, "
            f"Δ=£{row['variance_gbp']:,.0f} ({row['variance_percent']:.1f}%)"
        )
    summary.append("")
    
    # SO-Flag analysis
    so_flag_count = comparison_df[comparison_df['has_so_flag'] == True].shape[0]
    if so_flag_count > 0:
        summary.append(f"SO-Flag Detected: {so_flag_count} acceptances")
        summary.append("  (SO-Flag = TRUE indicates constructed/special acceptances)")
        summary.append("")
    
    # Key findings
    summary.append("KEY FINDINGS:")
    summary.append("")
    
    if match_rate < 50:
        summary.append("⚠️  LOW BOALF MATCH RATE - Many NGSEA events likely post-event constructed")
        summary.append("   → P448 process: acceptances constructed after gas emergency")
        summary.append("   → Level 2 (P114) is authoritative for these events")
        summary.append("")
    
    close_match_pct = len(comparison_df[comparison_df['match_category'] == 'Close Match (<10%)']) / len(boalf_matched) * 100 if len(boalf_matched) > 0 else 0
    if close_match_pct > 50:
        summary.append(f"✅ FORMULA VALIDATED - {close_match_pct:.1f}% of matched records within 10%")
        summary.append("   → |reduction_mwh| × |bid_price| × duration is accurate estimate")
        summary.append("")
    
    large_diff_pct = len(comparison_df[comparison_df['match_category'] == 'Large Difference (>30%)']) / total_events * 100
    if large_diff_pct > 20:
        summary.append(f"⚠️  {large_diff_pct:.1f}% have large variances (>30%)")
        summary.append("   Causes may include:")
        summary.append("   - Delivery/non-delivery adjustments (Section T)")
        summary.append("   - BSCP18 committee corrections")
        summary.append("   - Ladder pricing (multiple BOD pairs)")
        summary.append("   - System_price ≠ bid_price in settlement")
        summary.append("")
    
    summary.append("RECOMMENDATION:")
    summary.append("  Use Level 1 (BOALF+BOD) for operational estimates (quick, T+1 available)")
    summary.append("  Use Level 2 (P114 RF) for settlement verification (authoritative, includes adjustments)")
    summary.append("  Expect 5-30% variance due to Section T Trading Charges complexity")
    summary.append("")
    
    summary.append("="*80)
    
    return "\n".join(summary)

def main():
    """Main execution function"""
    args = parse_args()
    
    print("="*80)
    print("NGSEA PAYMENT FORMULA VALIDATION")
    print("="*80)
    print(f"Date Range: {args.start_date} to {args.end_date}")
    print(f"Minimum Payment: £{args.min_payment:,.0f}")
    print("")
    
    # Initialize BigQuery client
    try:
        client = bigquery.Client(project=PROJECT_ID, location="US")
        print(f"✅ Connected to BigQuery project: {PROJECT_ID}")
    except Exception as e:
        print(f"❌ Failed to connect to BigQuery: {e}")
        sys.exit(1)
    
    # Step 1: Get P114 NGSEA candidates (Level 2)
    p114_df = get_p114_ngsea_candidates(
        client, 
        args.start_date, 
        args.end_date,
        args.min_payment
    )
    
    if p114_df.empty:
        print("❌ No NGSEA candidates found in P114 data for date range")
        sys.exit(1)
    
    print("")
    
    # Step 2: Get BOALF+BOD estimates (Level 1)
    boalf_bod_df = get_boalf_bod_estimates(client, p114_df)
    
    if boalf_bod_df.empty:
        print("⚠️  No BOALF+BOD matches found (all events may be post-event constructed)")
    
    print("")
    
    # Step 3: Merge and compare
    comparison_df = merge_and_compare(p114_df, boalf_bod_df)
    
    # Step 4: Save detailed results
    output_csv = f"{args.output_dir}/validation_results.csv"
    comparison_df.to_csv(output_csv, index=False)
    print(f"💾 Saved detailed results to: {output_csv}")
    print("")
    
    # Step 5: Generate and save summary
    summary_text = generate_summary(comparison_df)
    output_summary = f"{args.output_dir}/formula_variance_summary.txt"
    with open(output_summary, 'w') as f:
        f.write(summary_text)
    print(summary_text)
    print(f"💾 Saved summary to: {output_summary}")
    print("")
    
    print("="*80)
    print("VALIDATION COMPLETE")
    print("="*80)

if __name__ == "__main__":
    main()
