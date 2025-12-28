#!/usr/bin/env python3
"""
VLP Revenue Reconciliation: BMRS vs P114 Settlement Data

Purpose: Compare £2.79M BMRS revenue estimate (from bmrs_boalf_complete acceptances)
         against actual P114 settlement data to validate accuracy and identify discrepancies.

Methodology:
1. Extract BMRS balancing acceptances (bid-offer data with prices) per BM unit/period
2. Extract P114 settlement data (actual settlement with system prices) per BM unit/period
3. JOIN on bmUnitId + settlementDate + settlementPeriod for per-period reconciliation
4. Calculate variance: (BMRS revenue - P114 settlement) for each period
5. Aggregate by unit, date, and overall to identify patterns

Key Tables:
- bmrs_boalf_complete: BMRS balancing acceptances with prices (derived from BOD matching)
- elexon_p114_s0142_bpi: P114 actual settlement data (per-unit BPI records with system prices)

Output:
- Summary statistics (total variance, percentage difference)
- Period-level discrepancies (>1% variance)
- Date-level patterns (which dates have highest variance)
- Unit-level comparison (FBPGM002 vs FFSEN005)

Expected Outcome:
- Variance <5%: Revenue model validated ✅
- Variance 5-10%: Investigate methodology (timing, run selection, price sources)
- Variance >10%: Data quality issues or fundamental model error
"""

from google.cloud import bigquery
import pandas as pd
import os
from datetime import datetime

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

def reconcile_vlp_revenue(
    start_date: str = '2024-10-01',
    end_date: str = '2024-10-31',
    settlement_run: str = 'II',
    vlp_units: list = ['FBPGM002', 'FFSEN005']
):
    """
    Reconcile VLP revenue between BMRS and P114 data

    Args:
        start_date: Analysis start date (YYYY-MM-DD)
        end_date: Analysis end date (YYYY-MM-DD)
        settlement_run: P114 settlement run to use (II/SF/R1/R2/R3/RF)
        vlp_units: List of VLP BM unit IDs to analyze
    """

    print(f"""
{'='*100}
VLP REVENUE RECONCILIATION: BMRS vs P114
{'='*100}
Period: {start_date} to {end_date}
Settlement Run: {settlement_run}
VLP Units: {', '.join(vlp_units)}
{'='*100}
""")

    # Step 1: Extract BMRS revenue (from balancing acceptances)
    print("📊 Step 1: Extracting BMRS revenue data...")
    bmrs_query = f"""
    WITH bmrs_revenue AS (
      SELECT
        bmUnit as bm_unit_id,
        settlement_date,
        settlementPeriod as settlement_period,
        SUM(revenue_estimate_gbp) as bmrs_revenue_gbp,
        SUM(acceptanceVolume) as bmrs_mwh,
        COUNT(*) as bmrs_acceptance_count,
        AVG(acceptancePrice) as avg_bmrs_price
      FROM `inner-cinema-476211-u9.uk_energy_prod.boalf_with_prices`
      WHERE bmUnit IN UNNEST({vlp_units})
        AND settlement_date >= '{start_date}'
        AND settlement_date <= '{end_date}'
      GROUP BY bm_unit_id, settlement_date, settlement_period
    )
    SELECT * FROM bmrs_revenue
    ORDER BY settlement_date, bm_unit_id, settlement_period
    """

    bmrs_df = client.query(bmrs_query).to_dataframe()
    print(f"   ✅ BMRS: {len(bmrs_df):,} period records")
    print(f"   📅 Date range: {bmrs_df['settlement_date'].min()} to {bmrs_df['settlement_date'].max()}")
    print(f"   💷 Total BMRS revenue: £{bmrs_df['bmrs_revenue_gbp'].sum():,.2f}")

    # Step 2: Extract P114 settlement data
    print("\n📊 Step 2: Extracting P114 settlement data...")
    p114_query = f"""
    WITH p114_settlement AS (
      SELECT
        bm_unit_id,
        settlement_date,
        settlement_period,
        SUM(value2 * system_price * multiplier) as p114_revenue_gbp,  -- value2=MWh, system_price=£/MWh
        SUM(value2) as p114_mwh,
        AVG(system_price) as avg_system_price,
        COUNT(*) as p114_record_count
      FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
      WHERE bm_unit_id IN UNNEST({vlp_units})
        AND settlement_run = '{settlement_run}'
        AND settlement_date >= '{start_date}'
        AND settlement_date <= '{end_date}'
      GROUP BY bm_unit_id, settlement_date, settlement_period
    )
    SELECT * FROM p114_settlement
    ORDER BY settlement_date, bm_unit_id, settlement_period
    """

    p114_df = client.query(p114_query).to_dataframe()
    print(f"   ✅ P114: {len(p114_df):,} period records")
    print(f"   📅 Date range: {p114_df['settlement_date'].min()} to {p114_df['settlement_date'].max()}")
    print(f"   💷 Total P114 revenue: £{p114_df['p114_revenue_gbp'].sum():,.2f}")

    # Step 3: Merge BMRS and P114 data
    print("\n📊 Step 3: Merging BMRS and P114 data...")
    merged_df = pd.merge(
        bmrs_df,
        p114_df,
        on=['bm_unit_id', 'settlement_date', 'settlement_period'],
        how='outer',
        indicator=True
    )

    # Calculate variance
    merged_df['variance_gbp'] = merged_df['bmrs_revenue_gbp'] - merged_df['p114_revenue_gbp']
    merged_df['variance_pct'] = (
        merged_df['variance_gbp'] / merged_df['p114_revenue_gbp'].abs() * 100
    ).replace([float('inf'), -float('inf')], None)

    print(f"   ✅ Merged: {len(merged_df):,} total period records")
    print(f"   📊 Match status:")
    print(f"      Both: {(merged_df['_merge'] == 'both').sum():,} periods")
    print(f"      BMRS only: {(merged_df['_merge'] == 'left_only').sum():,} periods")
    print(f"      P114 only: {(merged_df['_merge'] == 'right_only').sum():,} periods")

    # Step 4: Summary statistics
    print(f"\n{'='*100}")
    print("📈 SUMMARY STATISTICS")
    print(f"{'='*100}")

    matched_df = merged_df[merged_df['_merge'] == 'both']

    if len(matched_df) > 0:
        total_bmrs = matched_df['bmrs_revenue_gbp'].sum()
        total_p114 = matched_df['p114_revenue_gbp'].sum()
        total_variance = total_bmrs - total_p114
        total_variance_pct = (total_variance / abs(total_p114) * 100) if total_p114 != 0 else None

        print(f"\n💷 Revenue Comparison (Matched Periods Only):")
        print(f"   BMRS Total:     £{total_bmrs:>15,.2f}")
        print(f"   P114 Total:     £{total_p114:>15,.2f}")
        print(f"   Variance:       £{total_variance:>15,.2f} ({total_variance_pct:+.2f}%)")

        print(f"\n⚡ Volume Comparison:")
        total_bmrs_mwh = matched_df['bmrs_mwh'].sum()
        total_p114_mwh = matched_df['p114_mwh'].sum()
        print(f"   BMRS Total:     {total_bmrs_mwh:>15,.2f} MWh")
        print(f"   P114 Total:     {total_p114_mwh:>15,.2f} MWh")
        print(f"   Variance:       {total_bmrs_mwh - total_p114_mwh:>15,.2f} MWh")

        print(f"\n💰 Price Comparison:")
        avg_bmrs_price = matched_df['avg_bmrs_price'].mean()
        avg_p114_price = matched_df['avg_system_price'].mean()
        print(f"   BMRS Avg:       £{avg_bmrs_price:>15,.2f}/MWh")
        print(f"   P114 Avg:       £{avg_p114_price:>15,.2f}/MWh")
        print(f"   Variance:       £{avg_bmrs_price - avg_p114_price:>15,.2f}/MWh")

        # Variance distribution
        print(f"\n📊 Variance Distribution:")
        print(f"   Periods with <1% variance:   {(matched_df['variance_pct'].abs() < 1).sum():>6,} ({(matched_df['variance_pct'].abs() < 1).sum() / len(matched_df) * 100:.1f}%)")
        print(f"   Periods with 1-5% variance:  {((matched_df['variance_pct'].abs() >= 1) & (matched_df['variance_pct'].abs() < 5)).sum():>6,} ({((matched_df['variance_pct'].abs() >= 1) & (matched_df['variance_pct'].abs() < 5)).sum() / len(matched_df) * 100:.1f}%)")
        print(f"   Periods with 5-10% variance: {((matched_df['variance_pct'].abs() >= 5) & (matched_df['variance_pct'].abs() < 10)).sum():>6,} ({((matched_df['variance_pct'].abs() >= 5) & (matched_df['variance_pct'].abs() < 10)).sum() / len(matched_df) * 100:.1f}%)")
        print(f"   Periods with >10% variance:  {(matched_df['variance_pct'].abs() >= 10).sum():>6,} ({(matched_df['variance_pct'].abs() >= 10).sum() / len(matched_df) * 100:.1f}%)")

    # Step 5: Unit-level breakdown
    print(f"\n{'='*100}")
    print("🔋 UNIT-LEVEL BREAKDOWN")
    print(f"{'='*100}")

    for unit in vlp_units:
        unit_df = matched_df[matched_df['bm_unit_id'] == unit]
        if len(unit_df) > 0:
            unit_bmrs = unit_df['bmrs_revenue_gbp'].sum()
            unit_p114 = unit_df['p114_revenue_gbp'].sum()
            unit_variance = unit_bmrs - unit_p114
            unit_variance_pct = (unit_variance / abs(unit_p114) * 100) if unit_p114 != 0 else None

            print(f"\n{unit}:")
            print(f"   Periods:        {len(unit_df):>6,}")
            print(f"   BMRS Revenue:   £{unit_bmrs:>12,.2f}")
            print(f"   P114 Revenue:   £{unit_p114:>12,.2f}")
            print(f"   Variance:       £{unit_variance:>12,.2f} ({unit_variance_pct:+.2f}%)")

    # Step 6: Top variance periods
    print(f"\n{'='*100}")
    print("⚠️  TOP 20 VARIANCE PERIODS (by absolute £ variance)")
    print(f"{'='*100}")

    top_variance = matched_df.nlargest(20, 'variance_gbp', keep='all')[
        ['bm_unit_id', 'settlement_date', 'settlement_period',
         'bmrs_revenue_gbp', 'p114_revenue_gbp', 'variance_gbp', 'variance_pct']
    ]

    print(f"\n{'Unit':<12} {'Date':<12} {'Period':<7} {'BMRS £':<12} {'P114 £':<12} {'Var £':<12} {'Var %':<10}")
    print(f"{'-'*85}")
    for _, row in top_variance.iterrows():
        print(f"{row['bm_unit_id']:<12} {str(row['settlement_date']):<12} {row['settlement_period']:<7} "
              f"£{row['bmrs_revenue_gbp']:>10,.2f} £{row['p114_revenue_gbp']:>10,.2f} "
              f"£{row['variance_gbp']:>10,.2f} {row['variance_pct']:>8.1f}%")

    # Step 7: Date-level aggregation
    print(f"\n{'='*100}")
    print("📅 DATE-LEVEL SUMMARY (Top 10 dates by absolute variance)")
    print(f"{'='*100}")

    date_summary = matched_df.groupby('settlement_date').agg({
        'bmrs_revenue_gbp': 'sum',
        'p114_revenue_gbp': 'sum',
        'variance_gbp': 'sum',
        'bm_unit_id': 'count'
    }).reset_index()
    date_summary['variance_pct'] = (
        date_summary['variance_gbp'] / date_summary['p114_revenue_gbp'].abs() * 100
    )
    date_summary = date_summary.nlargest(10, 'variance_gbp', keep='all')

    print(f"\n{'Date':<12} {'Periods':<8} {'BMRS £':<15} {'P114 £':<15} {'Variance £':<15} {'Variance %':<12}")
    print(f"{'-'*95}")
    for _, row in date_summary.iterrows():
        print(f"{str(row['settlement_date']):<12} {int(row['bm_unit_id']):<8} "
              f"£{row['bmrs_revenue_gbp']:>12,.2f} £{row['p114_revenue_gbp']:>12,.2f} "
              f"£{row['variance_gbp']:>12,.2f} {row['variance_pct']:>10.1f}%")

    # Step 8: Data quality checks
    print(f"\n{'='*100}")
    print("🔍 DATA QUALITY CHECKS")
    print(f"{'='*100}")

    print(f"\nMissing Data:")
    print(f"   BMRS only (no P114 match): {(merged_df['_merge'] == 'left_only').sum():>6,} periods")
    print(f"   P114 only (no BMRS match): {(merged_df['_merge'] == 'right_only').sum():>6,} periods")

    if (merged_df['_merge'] == 'left_only').sum() > 0:
        print(f"\n   Sample BMRS-only periods:")
        bmrs_only = merged_df[merged_df['_merge'] == 'left_only'].head(5)[
            ['bm_unit_id', 'settlement_date', 'settlement_period', 'bmrs_revenue_gbp']
        ]
        for _, row in bmrs_only.iterrows():
            print(f"      {row['bm_unit_id']} {row['settlement_date']} Period {row['settlement_period']}: £{row['bmrs_revenue_gbp']:.2f}")

    if (merged_df['_merge'] == 'right_only').sum() > 0:
        print(f"\n   Sample P114-only periods:")
        p114_only = merged_df[merged_df['_merge'] == 'right_only'].head(5)[
            ['bm_unit_id', 'settlement_date', 'settlement_period', 'p114_revenue_gbp']
        ]
        for _, row in p114_only.iterrows():
            print(f"      {row['bm_unit_id']} {row['settlement_date']} Period {row['settlement_period']}: £{row['p114_revenue_gbp']:.2f}")

    # Save results to CSV
    output_file = f'vlp_reconciliation_{start_date}_to_{end_date}_{settlement_run}.csv'
    merged_df.to_csv(output_file, index=False)
    print(f"\n💾 Results saved to: {output_file}")

    # Overall assessment
    print(f"\n{'='*100}")
    print("🎯 ASSESSMENT")
    print(f"{'='*100}")

    if len(matched_df) > 0 and total_variance_pct is not None:
        if abs(total_variance_pct) < 5:
            print(f"✅ VALIDATED: Variance {abs(total_variance_pct):.2f}% is within acceptable range (<5%)")
            print(f"   Revenue model is accurate, BMRS estimate £{abs(total_bmrs):,.2f} closely matches P114 settlement.")
        elif abs(total_variance_pct) < 10:
            print(f"⚠️  INVESTIGATE: Variance {abs(total_variance_pct):.2f}% requires further analysis")
            print(f"   Check methodology: timing differences, settlement run selection, or price source discrepancies.")
        else:
            print(f"❌ SIGNIFICANT VARIANCE: {abs(total_variance_pct):.2f}% indicates data quality issues or model error")
            print(f"   Review: BPI value calculation, system price extraction, BMRS acceptance matching.")
    else:
        print(f"⚠️  INCOMPLETE: No matched periods found, cannot assess variance")
        print(f"   Check: Date range coverage, settlement run availability, VLP unit IDs.")

    print(f"\n{'='*100}")
    print(f"Analysis complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*100}\n")

    return merged_df


if __name__ == '__main__':
    import sys

    # Parse command-line arguments
    if len(sys.argv) > 1:
        start_date = sys.argv[1]
        end_date = sys.argv[2] if len(sys.argv) > 2 else start_date
        settlement_run = sys.argv[3] if len(sys.argv) > 3 else 'II'
    else:
        # Default: Oct 2024 (our test data range)
        start_date = '2024-10-11'
        end_date = '2024-10-13'
        settlement_run = 'II'

    # Run reconciliation
    results = reconcile_vlp_revenue(
        start_date=start_date,
        end_date=end_date,
        settlement_run=settlement_run,
        vlp_units=['FBPGM002', 'FFSEN005']
    )
