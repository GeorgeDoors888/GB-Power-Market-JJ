#!/usr/bin/env python3
"""
VLP Revenue Calculator - P114 Settlement Data

Purpose: Calculate TRUE VLP battery revenue using P114 settlement data
         (imbalance settlement) instead of BOALF acceptances.

Key Insight: VLP batteries (FBPGM002, FFSEN005) self-balance and do NOT
             appear in BOALF. Revenue comes from imbalance pricing, not
             explicit balancing acceptances.

Formula: Revenue = value2 (MWh) × system_price (£/MWh) × multiplier

Data Source: elexon_p114_s0142_bpi (actual settlement metered volumes)
Comparison: Original £2.79M estimate from mart_bm_value_by_vlp_sp (BOALF-based)
"""

from google.cloud import bigquery
import pandas as pd
import os
from datetime import datetime

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

def calculate_vlp_p114_revenue(
    start_date: str = '2022-01-01',
    end_date: str = '2025-12-28',
    settlement_run: str = None,  # None = use all available
    vlp_units: list = ['FBPGM002', 'FFSEN005']
):
    """
    Calculate VLP revenue from P114 settlement data

    Args:
        start_date: Analysis start (YYYY-MM-DD)
        end_date: Analysis end (YYYY-MM-DD)
        settlement_run: Specific run (II/SF/R1/R2/R3/RF) or None for all
        vlp_units: List of VLP BM unit IDs
    """

    print(f"""
{'='*100}
VLP REVENUE CALCULATION: P114 Settlement Data (Imbalance Revenue)
{'='*100}
Period: {start_date} to {end_date}
Settlement Run: {settlement_run or 'All Available'}
VLP Units: {', '.join(vlp_units)}
{'='*100}
""")

    # Build query with optional run filter
    run_filter = f"AND settlement_run = '{settlement_run}'" if settlement_run else ""

    query = f"""
    WITH daily_settlement AS (
      SELECT
        bm_unit_id,
        settlement_date,
        settlement_run,
        settlement_period,
        value2 as mwh,
        system_price,
        multiplier,
        (value2 * system_price * multiplier) as period_revenue_gbp
      FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
      WHERE bm_unit_id IN UNNEST({vlp_units})
        AND settlement_date >= '{start_date}'
        AND settlement_date <= '{end_date}'
        {run_filter}
    ),
    daily_summary AS (
      SELECT
        bm_unit_id,
        settlement_date,
        settlement_run,
        SUM(period_revenue_gbp) as daily_revenue_gbp,
        SUM(mwh) as daily_mwh,
        AVG(system_price) as avg_system_price,
        COUNT(*) as periods_active
      FROM daily_settlement
      GROUP BY bm_unit_id, settlement_date, settlement_run
    ),
    unit_summary AS (
      SELECT
        bm_unit_id,
        COUNT(DISTINCT settlement_date) as days_active,
        SUM(daily_revenue_gbp) as total_revenue_gbp,
        SUM(daily_mwh) as total_mwh,
        AVG(daily_revenue_gbp) as avg_daily_revenue_gbp,
        AVG(daily_mwh) as avg_daily_mwh,
        AVG(avg_system_price) as avg_system_price_weighted,
        MIN(settlement_date) as earliest_date,
        MAX(settlement_date) as latest_date
      FROM daily_summary
      GROUP BY bm_unit_id
    )
    SELECT * FROM unit_summary
    ORDER BY total_revenue_gbp DESC
    """

    print("📊 Querying P114 settlement data...")
    df = client.query(query).to_dataframe()

    if len(df) == 0:
        print("⚠️  No data found for specified parameters")
        print(f"   Check: Date range, settlement run availability, VLP unit IDs")
        return None

    print(f"   ✅ Retrieved {len(df)} VLP unit(s)\n")

    # Display unit-level results
    print(f"{'='*100}")
    print(f"📈 VLP UNIT REVENUE SUMMARY")
    print(f"{'='*100}\n")

    total_revenue = 0
    total_mwh = 0
    total_days = 0

    for _, row in df.iterrows():
        print(f"🔋 {row['bm_unit_id']}:")
        print(f"   Period:           {row['earliest_date']} to {row['latest_date']}")
        print(f"   Days Active:      {row['days_active']:,}")
        print(f"   Total Revenue:    £{row['total_revenue_gbp']:,.2f}")
        print(f"   Total Energy:     {row['total_mwh']:,.2f} MWh")
        print(f"   Avg Daily Revenue: £{row['avg_daily_revenue_gbp']:,.2f}")
        print(f"   Avg Daily Energy:  {row['avg_daily_mwh']:,.2f} MWh")
        print(f"   Avg System Price:  £{row['avg_system_price_weighted']:.2f}/MWh")
        print(f"   Implied Revenue Rate: £{row['total_revenue_gbp'] / row['total_mwh']:.2f}/MWh\n")

        total_revenue += row['total_revenue_gbp']
        total_mwh += row['total_mwh']
        total_days = max(total_days, row['days_active'])

    # Aggregate summary
    print(f"{'='*100}")
    print(f"💷 TOTAL VLP REVENUE (P114 Settlement)")
    print(f"{'='*100}")
    print(f"   Combined Revenue:  £{total_revenue:,.2f}")
    print(f"   Combined Energy:   {total_mwh:,.2f} MWh")
    print(f"   Max Days Active:   {total_days:,}")
    print(f"   Avg Revenue/MWh:   £{total_revenue / total_mwh:.2f}/MWh\n")

    # Comparison with original estimate
    print(f"{'='*100}")
    print(f"📊 COMPARISON WITH ORIGINAL ESTIMATE")
    print(f"{'='*100}")
    original_estimate = 2_790_000  # £2.79M from mart_bm_value_by_vlp_sp (BOALF-based)
    variance = total_revenue - original_estimate
    variance_pct = (variance / original_estimate * 100) if original_estimate != 0 else 0

    print(f"   Original Estimate (BOALF):  £{original_estimate:,.2f}")
    print(f"   P114 Actual:                £{total_revenue:,.2f}")
    print(f"   Variance:                   £{variance:>+,.2f} ({variance_pct:+.1f}%)\n")

    if abs(variance_pct) < 10:
        print(f"   ✅ VALIDATED: Variance within 10% tolerance")
    elif abs(variance_pct) < 25:
        print(f"   ⚠️  INVESTIGATE: Variance {abs(variance_pct):.1f}% requires review")
    else:
        print(f"   ❌ SIGNIFICANT VARIANCE: {abs(variance_pct):.1f}% indicates model error")

    print(f"\n   Likely Explanation:")
    if total_revenue < original_estimate * 0.5:
        print(f"      • Original estimate used proxy data (not actual VLP units)")
        print(f"      • VLP units don't appear in BOALF → estimate was for different units")
    elif abs(variance_pct) < 10:
        print(f"      • P114 settlement closely matches BOALF estimate")
        print(f"      • Original methodology was sound despite wrong data source")
    else:
        print(f"      • Different settlement runs (II vs RF)")
        print(f"      • Time period mismatch")
        print(f"      • Additional revenue sources not in P114 (e.g., frequency response availability payments)")

    # Monthly breakdown
    print(f"\n{'='*100}")
    print(f"📅 MONTHLY REVENUE BREAKDOWN")
    print(f"{'='*100}\n")

    monthly_query = f"""
    SELECT
      bm_unit_id,
      EXTRACT(YEAR FROM settlement_date) as year,
      EXTRACT(MONTH FROM settlement_date) as month,
      COUNT(DISTINCT settlement_date) as days,
      SUM(value2 * system_price * multiplier) as monthly_revenue_gbp,
      SUM(value2) as monthly_mwh,
      AVG(system_price) as avg_price
    FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
    WHERE bm_unit_id IN UNNEST({vlp_units})
      AND settlement_date >= '{start_date}'
      AND settlement_date <= '{end_date}'
      {run_filter}
    GROUP BY bm_unit_id, year, month
    ORDER BY year DESC, month DESC, monthly_revenue_gbp DESC
    LIMIT 24  -- Last 24 months
    """

    monthly_df = client.query(monthly_query).to_dataframe()

    if len(monthly_df) > 0:
        print(f"{'Unit':<12} {'Month':<10} {'Days':<6} {'Revenue':<15} {'MWh':<12} {'Avg £/MWh':<12}")
        print(f"{'-'*80}")
        for _, row in monthly_df.iterrows():
            month_str = f"{int(row['year'])}-{int(row['month']):02d}"
            print(f"{row['bm_unit_id']:<12} {month_str:<10} {int(row['days']):<6} "
                  f"£{row['monthly_revenue_gbp']:>12,.2f} {row['monthly_mwh']:>10,.2f} "
                  f"£{row['avg_price']:>10.2f}")

    # Save results
    output_file = f'vlp_p114_revenue_{start_date}_to_{end_date}.csv'
    df.to_csv(output_file, index=False)
    print(f"\n💾 Results saved to: {output_file}")

    # Settlement run distribution (if not filtered)
    if not settlement_run:
        print(f"\n{'='*100}")
        print(f"🔄 SETTLEMENT RUN DISTRIBUTION")
        print(f"{'='*100}\n")

        run_query = f"""
        SELECT
          settlement_run,
          COUNT(DISTINCT settlement_date) as distinct_dates,
          SUM(value2 * system_price * multiplier) as run_revenue_gbp
        FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
        WHERE bm_unit_id IN UNNEST({vlp_units})
          AND settlement_date >= '{start_date}'
          AND settlement_date <= '{end_date}'
        GROUP BY settlement_run
        ORDER BY
          CASE settlement_run
            WHEN 'RF' THEN 1
            WHEN 'R3' THEN 2
            WHEN 'R2' THEN 3
            WHEN 'R1' THEN 4
            WHEN 'SF' THEN 5
            WHEN 'II' THEN 6
            WHEN 'DF' THEN 7
            ELSE 8
          END
        """

        run_df = client.query(run_query).to_dataframe()

        if len(run_df) > 0:
            print(f"{'Run':<6} {'Dates':<8} {'Revenue':<18} {'% of Total':<12}")
            print(f"{'-'*50}")
            for _, row in run_df.iterrows():
                run_pct = (row['run_revenue_gbp'] / total_revenue * 100) if total_revenue != 0 else 0
                print(f"{row['settlement_run']:<6} {int(row['distinct_dates']):<8} "
                      f"£{row['run_revenue_gbp']:>15,.2f} {run_pct:>10.1f}%")

            print(f"\n   Note: Overlapping dates across runs. Use canonical view for deduplication.")

    print(f"\n{'='*100}")
    print(f"Analysis complete: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*100}\n")

    return df


if __name__ == '__main__':
    import sys

    # Parse command-line arguments
    if len(sys.argv) > 1:
        start_date = sys.argv[1]
        end_date = sys.argv[2] if len(sys.argv) > 2 else '2025-12-28'
        settlement_run = sys.argv[3] if len(sys.argv) > 3 else None
    else:
        # Default: Full available range
        start_date = '2024-10-11'  # Currently we only have Oct 11-13
        end_date = '2024-10-13'
        settlement_run = 'II'

    # Calculate revenue
    results = calculate_vlp_p114_revenue(
        start_date=start_date,
        end_date=end_date,
        settlement_run=settlement_run,
        vlp_units=['FBPGM002', 'FFSEN005']
    )
