#!/usr/bin/env python3
"""
Self-Balancing Unit Detection

Purpose: Identify BM Units that settle via P114 but do NOT receive
         ESO balancing instructions (BOALF acceptances).

Key Insight: Self-balancing units (batteries, small renewables, portfolios)
             operate autonomously, adjusting output to match Physical
             Notifications without requiring ESO intervention.

Method: Anti-join P114 settlement data with BOALF acceptances.
"""

from google.cloud import bigquery
import pandas as pd
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

def detect_self_balancing_units(
    start_date: str = '2024-01-01',
    end_date: str = '2024-12-31',
    min_mwh: float = 100.0,  # Minimum total energy to qualify
    settlement_run: str = 'II'
):
    """
    Identify self-balancing BM units

    Args:
        start_date: Analysis start (YYYY-MM-DD)
        end_date: Analysis end (YYYY-MM-DD)
        min_mwh: Minimum absolute MWh to include (filters tiny/test units)
        settlement_run: P114 run to analyze
    """

    print(f"""
{'='*100}
SELF-BALANCING UNIT DETECTION
{'='*100}
Period: {start_date} to {end_date}
P114 Run: {settlement_run}
Min Energy: {min_mwh:,.0f} MWh
{'='*100}
""")

    query = f"""
    -- Step 1: Find all units in P114 settlement
    WITH p114_units AS (
      SELECT
        bm_unit_id,
        COUNT(DISTINCT settlement_date) as days_in_p114,
        SUM(ABS(value2)) as total_abs_mwh,
        SUM(value2 * system_price * multiplier) as total_revenue_gbp,
        AVG(system_price) as avg_system_price
      FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
      WHERE settlement_date >= '{start_date}'
        AND settlement_date <= '{end_date}'
        AND settlement_run = '{settlement_run}'
      GROUP BY bm_unit_id
      HAVING SUM(ABS(value2)) >= {min_mwh}
    ),

    -- Step 2: Find all units in BOALF (balancing acceptances)
    boalf_units AS (
      SELECT
        bmUnit,
        COUNT(DISTINCT CAST(settlementDate AS DATE)) as days_in_boalf,
        COUNT(*) as total_acceptances,
        SUM(ABS(acceptanceVolume)) as total_abs_mwh,
        SUM(acceptanceVolume * acceptancePrice) as total_boa_revenue_gbp
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
      WHERE CAST(settlementDate AS DATE) >= '{start_date}'
        AND CAST(settlementDate AS DATE) <= '{end_date}'
      GROUP BY bmUnit
    ),

    -- Step 3: Identify self-balancing units (in P114 but NOT in BOALF)
    self_balancing AS (
      SELECT
        p.bm_unit_id,
        p.days_in_p114,
        p.total_abs_mwh as p114_mwh,
        p.total_revenue_gbp as p114_revenue_gbp,
        p.avg_system_price,
        CASE
          -- Categorize by naming convention (rough heuristic)
          WHEN p.bm_unit_id LIKE '%BESS%' OR p.bm_unit_id LIKE '%STOR%' THEN 'Battery'
          WHEN p.bm_unit_id LIKE '%WIND%' OR p.bm_unit_id LIKE 'E_%' THEN 'Wind'
          WHEN p.bm_unit_id LIKE '%SOLAR%' OR p.bm_unit_id LIKE '%PV%' THEN 'Solar'
          WHEN p.bm_unit_id LIKE 'T_%' THEN 'Transmission'
          WHEN p.bm_unit_id LIKE '2__%' THEN 'Embedded'
          WHEN p.bm_unit_id LIKE 'FB%' OR p.bm_unit_id LIKE 'FF%' THEN 'Flex/Battery (VLP)'
          ELSE 'Other'
        END as technology_guess
      FROM p114_units p
      LEFT JOIN boalf_units b ON p.bm_unit_id = b.bmUnit
      WHERE b.bmUnit IS NULL  -- Anti-join: exists in P114 but NOT in BOALF
    ),

    -- Step 4: Hybrid units (appear in BOTH P114 and BOALF)
    hybrid_units AS (
      SELECT
        p.bm_unit_id,
        p.days_in_p114,
        b.days_in_boalf,
        p.total_abs_mwh as p114_mwh,
        b.total_abs_mwh as boalf_mwh,
        p.total_revenue_gbp as p114_revenue_gbp,
        b.total_boa_revenue_gbp as boa_revenue_gbp,
        b.total_acceptances,
        ROUND((b.total_abs_mwh / p.total_abs_mwh * 100), 1) as boalf_share_pct
      FROM p114_units p
      INNER JOIN boalf_units b ON p.bm_unit_id = b.bmUnit
    )

    SELECT * FROM self_balancing
    ORDER BY p114_revenue_gbp DESC
    """

    print("📊 Querying P114 and BOALF data...")
    df = client.query(query).to_dataframe()

    print(f"   ✅ Found {len(df):,} self-balancing units\n")

    if len(df) == 0:
        print("⚠️  No self-balancing units found (all units receive BOAs)")
        return None

    # Summary statistics
    total_self_balancing_mwh = df['p114_mwh'].sum()
    total_self_balancing_revenue = df['p114_revenue_gbp'].sum()

    print(f"{'='*100}")
    print(f"📈 SELF-BALANCING MARKET SUMMARY")
    print(f"{'='*100}\n")
    print(f"   Total Self-Balancing Units:  {len(df):,}")
    print(f"   Total Energy (P114):          {total_self_balancing_mwh:,.0f} MWh")
    print(f"   Total Revenue (P114):         £{total_self_balancing_revenue:,.2f}")
    print(f"   Avg Revenue/MWh:              £{total_self_balancing_revenue / total_self_balancing_mwh:.2f}/MWh\n")

    # Technology breakdown
    print(f"{'='*100}")
    print(f"⚡ TECHNOLOGY BREAKDOWN")
    print(f"{'='*100}\n")

    tech_summary = df.groupby('technology_guess').agg({
        'bm_unit_id': 'count',
        'p114_mwh': 'sum',
        'p114_revenue_gbp': 'sum'
    }).reset_index()
    tech_summary = tech_summary.sort_values('p114_revenue_gbp', ascending=False)

    print(f"{'Technology':<25} {'Units':<8} {'MWh':<18} {'Revenue':<20} {'%':<8}")
    print(f"{'-'*85}")
    for _, row in tech_summary.iterrows():
        pct = (row['p114_revenue_gbp'] / total_self_balancing_revenue * 100)
        print(f"{row['technology_guess']:<25} {int(row['bm_unit_id']):<8} "
              f"{row['p114_mwh']:>16,.0f} £{row['p114_revenue_gbp']:>17,.2f} {pct:>6.1f}%")

    # Top self-balancing units
    print(f"\n{'='*100}")
    print(f"🏆 TOP 20 SELF-BALANCING UNITS (by revenue)")
    print(f"{'='*100}\n")

    top_units = df.nlargest(20, 'p114_revenue_gbp')
    print(f"{'Unit ID':<15} {'Tech':<20} {'Days':<6} {'MWh':<15} {'Revenue':<18} {'£/MWh':<10}")
    print(f"{'-'*95}")
    for _, row in top_units.iterrows():
        rev_per_mwh = row['p114_revenue_gbp'] / row['p114_mwh'] if row['p114_mwh'] != 0 else 0
        print(f"{row['bm_unit_id']:<15} {row['technology_guess']:<20} {int(row['days_in_p114']):<6} "
              f"{row['p114_mwh']:>13,.0f} £{row['p114_revenue_gbp']:>15,.2f} £{rev_per_mwh:>8.2f}")

    # VLP batteries specifically
    vlp_batteries = df[df['bm_unit_id'].isin(['FBPGM002', 'FFSEN005'])]
    if len(vlp_batteries) > 0:
        print(f"\n{'='*100}")
        print(f"🔋 VLP BATTERY UNITS (Confirmed Self-Balancing)")
        print(f"{'='*100}\n")
        for _, row in vlp_batteries.iterrows():
            print(f"   {row['bm_unit_id']}:")
            print(f"      Days Active:  {int(row['days_in_p114'])}")
            print(f"      Energy:       {row['p114_mwh']:,.0f} MWh")
            print(f"      Revenue:      £{row['p114_revenue_gbp']:,.2f}")
            print(f"      Avg Price:    £{row['avg_system_price']:.2f}/MWh\n")

    # Calculate hybrid units for comparison
    print(f"\n{'='*100}")
    print(f"📊 HYBRID UNITS COMPARISON (Units with BOTH P114 and BOALF)")
    print(f"{'='*100}\n")

    hybrid_query = f"""
    WITH p114_units AS (
      SELECT
        bm_unit_id,
        SUM(ABS(value2)) as total_abs_mwh,
        SUM(value2 * system_price * multiplier) as total_revenue_gbp
      FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
      WHERE settlement_date >= '{start_date}'
        AND settlement_date <= '{end_date}'
        AND settlement_run = '{settlement_run}'
      GROUP BY bm_unit_id
      HAVING SUM(ABS(value2)) >= {min_mwh}
    ),
    boalf_units AS (
      SELECT
        bmUnit,
        COUNT(*) as total_acceptances,
        SUM(ABS(acceptanceVolume)) as total_abs_mwh,
        SUM(acceptanceVolume * acceptancePrice) as total_boa_revenue_gbp
      FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
      WHERE CAST(settlementDate AS DATE) >= '{start_date}'
        AND CAST(settlementDate AS DATE) <= '{end_date}'
      GROUP BY bmUnit
    )
    SELECT
      COUNT(*) as hybrid_count,
      SUM(p.total_abs_mwh) as hybrid_p114_mwh,
      SUM(b.total_abs_mwh) as hybrid_boalf_mwh,
      SUM(p.total_revenue_gbp) as hybrid_p114_revenue,
      SUM(b.total_boa_revenue_gbp) as hybrid_boa_revenue
    FROM p114_units p
    INNER JOIN boalf_units b ON p.bm_unit_id = b.bmUnit
    """

    hybrid_df = client.query(hybrid_query).to_dataframe()

    if len(hybrid_df) > 0 and hybrid_df.iloc[0]['hybrid_count'] > 0:
        hybrid_row = hybrid_df.iloc[0]
        print(f"   Hybrid Units (ESO-directed + self-balance): {int(hybrid_row['hybrid_count']):,}")
        print(f"   P114 Energy:         {hybrid_row['hybrid_p114_mwh']:,.0f} MWh")
        print(f"   BOALF Energy:        {hybrid_row['hybrid_boalf_mwh']:,.0f} MWh")
        print(f"   P114 Revenue:        £{hybrid_row['hybrid_p114_revenue']:,.2f}")
        print(f"   BOA Revenue:         £{hybrid_row['hybrid_boa_revenue']:,.2f}\n")

        # Market share calculation
        total_p114_mwh = total_self_balancing_mwh + hybrid_row['hybrid_p114_mwh']
        self_balance_share = (total_self_balancing_mwh / total_p114_mwh * 100)

        print(f"   Market Share:")
        print(f"      Self-Balancing:   {self_balance_share:5.1f}% of settlement volume")
        print(f"      Hybrid/ESO-dir:   {100 - self_balance_share:5.1f}% of settlement volume")

    # Save results
    output_file = f'self_balancing_units_{start_date}_to_{end_date}.csv'
    df.to_csv(output_file, index=False)
    print(f"\n💾 Results saved to: {output_file}")

    print(f"\n{'='*100}")
    print(f"✅ Analysis complete")
    print(f"{'='*100}\n")

    return df


if __name__ == '__main__':
    import sys

    # Parse command-line arguments
    if len(sys.argv) > 1:
        start_date = sys.argv[1]
        end_date = sys.argv[2] if len(sys.argv) > 2 else '2024-12-31'
        min_mwh = float(sys.argv[3]) if len(sys.argv) > 3 else 100.0
    else:
        # Default: Oct 2024 (our test data)
        start_date = '2024-10-11'
        end_date = '2024-10-13'
        min_mwh = 1.0  # Lower threshold for 3-day test

    # Detect self-balancing units
    results = detect_self_balancing_units(
        start_date=start_date,
        end_date=end_date,
        min_mwh=min_mwh,
        settlement_run='II'
    )
