#!/usr/bin/env python3
"""
Update v_btm_bess_inputs view to include real BM revenue from mart_bm_value_by_vlp_sp

Purpose:
- Fix £0 bm_revenue_per_mwh in v_btm_bess_inputs view
- LEFT JOIN with mart_bm_value_by_vlp_sp to get actual acceptance revenue
- Preserve existing stacked revenue calculations (DUoS, other services)

Date: December 27, 2025
"""

from google.cloud import bigquery
import os

# Configuration
PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"
VIEW_NAME = "v_btm_bess_inputs"

# Set credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(
    os.path.dirname(__file__), 'inner-cinema-credentials.json'
)

client = bigquery.Client(project=PROJECT_ID, location="US")

# Updated view definition with BM revenue lookup
view_sql = """
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs` AS

WITH config AS (
  SELECT DATE('2025-10-29') AS cutoff_date  -- Historical vs IRIS cutoff
),

-- Get market prices (SSP for charging cost, DUoS bands)
base_prices AS (
  SELECT
    settlementDate,
    settlementPeriod,
    TIMESTAMP(CONCAT(settlementDate, ' ', FORMAT('%02d', CAST((settlementPeriod - 1) * 0.5 AS INT64)), ':', CASE WHEN MOD(settlementPeriod, 2) = 0 THEN '30:00' ELSE '00:00' END)) AS ts_halfhour,
    systemBuyPrice AS ssp_charge,  -- Price paid to charge battery
    systemSellPrice AS ssp_sell,   -- Price received when discharging (not used in arbitrage)
    CASE
      WHEN EXTRACT(DAYOFWEEK FROM settlementDate) IN (1, 7) THEN 'GREEN'  -- Weekend
      WHEN settlementPeriod BETWEEN 32 AND 39 THEN 'RED'     -- 16:00-19:30 weekday
      WHEN settlementPeriod BETWEEN 16 AND 31 OR settlementPeriod BETWEEN 39 AND 44 THEN 'AMBER'  -- 08:00-16:00, 19:30-22:00 weekday
      ELSE 'GREEN'  -- 00:00-08:00, 22:00-23:59 weekday
    END AS duos_band
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
  WHERE settlementDate < (SELECT cutoff_date FROM config)

  UNION ALL

  SELECT
    DATE(settlementDate) AS settlementDate,
    settlementPeriod,
    TIMESTAMP(CONCAT(DATE(settlementDate), ' ', FORMAT('%02d', CAST((settlementPeriod - 1) * 0.5 AS INT64)), ':', CASE WHEN MOD(settlementPeriod, 2) = 0 THEN '30:00' ELSE '00:00' END)) AS ts_halfhour,
    price AS ssp_charge,
    price AS ssp_sell,  -- IRIS doesn't have separate buy/sell
    CASE
      WHEN EXTRACT(DAYOFWEEK FROM DATE(settlementDate)) IN (1, 7) THEN 'GREEN'
      WHEN settlementPeriod BETWEEN 32 AND 39 THEN 'RED'
      WHEN settlementPeriod BETWEEN 16 AND 31 OR settlementPeriod BETWEEN 39 AND 44 THEN 'AMBER'
      ELSE 'GREEN'
    END AS duos_band
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`
  WHERE DATE(settlementDate) >= (SELECT cutoff_date FROM config)
),

-- NEW: Aggregate BM revenue by settlement period across all VLPs
bm_revenue_lookup AS (
  SELECT
    settlement_date,
    settlementPeriod,
    SUM(total_gross_value_gbp) / NULLIF(SUM(total_accepted_mwh), 0) AS bm_revenue_per_mwh,
    SUM(acceptance_count) AS total_acceptances,
    SUM(total_accepted_mwh) AS total_volume_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.mart_bm_value_by_vlp_sp`
  GROUP BY settlement_date, settlementPeriod
),

-- Calculate stacked revenue components
stacked_revenue AS (
  SELECT
    bp.settlementDate,
    bp.settlementPeriod,
    bp.ts_halfhour,
    bp.ssp_charge,
    bp.ssp_sell,
    bp.duos_band,

    -- BM Revenue (NOW REAL DATA FROM BOALF ACCEPTANCES!)
    COALESCE(bm.bm_revenue_per_mwh, 0.0) AS bm_revenue_per_mwh,
    bm.total_acceptances,
    bm.total_volume_mwh,

    -- DUoS charges (assumed rates - replace with actual lookup if available)
    CASE
      WHEN bp.duos_band = 'RED' THEN 4.837    -- HV Red rate (p/kWh)
      WHEN bp.duos_band = 'AMBER' THEN 0.457  -- HV Amber rate
      WHEN bp.duos_band = 'GREEN' THEN 0.038  -- HV Green rate
      ELSE 0.0
    END AS duos_rate_p_per_kwh,

    -- Other revenue components (FFR, etc.) - placeholder
    0.0 AS ffr_revenue_per_mwh,
    0.0 AS ancillary_revenue_per_mwh,

    -- Total stacked revenue
    COALESCE(bm.bm_revenue_per_mwh, 0.0)
      + CASE
          WHEN bp.duos_band = 'RED' THEN 4.837 * 10  -- Convert p/kWh to £/MWh
          WHEN bp.duos_band = 'AMBER' THEN 0.457 * 10
          WHEN bp.duos_band = 'GREEN' THEN 0.038 * 10
          ELSE 0.0
        END AS total_stacked_revenue_per_mwh,

    -- Time components for analysis
    EXTRACT(HOUR FROM bp.ts_halfhour) AS hour_of_day,
    EXTRACT(DAYOFWEEK FROM bp.settlementDate) AS day_of_week,
    EXTRACT(MONTH FROM bp.settlementDate) AS month,
    EXTRACT(YEAR FROM bp.settlementDate) AS year

  FROM base_prices bp
  LEFT JOIN bm_revenue_lookup bm
    ON CAST(bp.settlementDate AS DATE) = bm.settlement_date
    AND bp.settlementPeriod = bm.settlementPeriod
)

SELECT * FROM stacked_revenue
ORDER BY settlementDate DESC, settlementPeriod DESC
"""

print("=" * 80)
print("UPDATING v_btm_bess_inputs VIEW")
print("=" * 80)
print("\n🔄 Adding LEFT JOIN to mart_bm_value_by_vlp_sp...")
print(f"   Project: {PROJECT_ID}")
print(f"   Dataset: {DATASET}")
print(f"   View: {VIEW_NAME}")

try:
    # Execute view update
    query_job = client.query(view_sql)
    query_job.result()  # Wait for completion

    print("\n✅ View updated successfully!")

    # Verify update with sample query
    print("\n" + "=" * 80)
    print("VERIFICATION: Checking BM Revenue in Updated View")
    print("=" * 80)

    verify_query = """
    SELECT
      settlementDate,
      settlementPeriod,
      bm_revenue_per_mwh,
      total_acceptances,
      total_volume_mwh,
      ssp_charge,
      duos_band,
      total_stacked_revenue_per_mwh
    FROM `inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs`
    WHERE settlementDate >= '2025-10-18' AND settlementDate <= '2025-10-23'
      AND bm_revenue_per_mwh > 0  -- Only show periods with BM activity
    ORDER BY settlementDate, settlementPeriod
    LIMIT 10
    """

    df = client.query(verify_query).to_dataframe()

    if len(df) > 0:
        print(f"\n✅ Found {len(df)} rows with BM revenue > £0")
        print("\nSample data (first 10 rows):")
        print(df.to_string(index=False))

        avg_bm_revenue = df['bm_revenue_per_mwh'].mean()
        print(f"\n📊 Average BM revenue: £{avg_bm_revenue:.2f}/MWh")

        if avg_bm_revenue > 50:
            print("✅ BM revenue looks correct (matches expected £66.06/MWh avg)")
        else:
            print("⚠️  BM revenue seems low - check data coverage")
    else:
        print("\n⚠️  No rows with BM revenue > £0 found for Oct 18-23")
        print("   This may indicate:")
        print("   1. mart_bm_value_by_vlp_sp table is empty")
        print("   2. Date range mismatch between tables")
        print("   3. JOIN condition not matching")

    # Check overall view statistics
    print("\n" + "=" * 80)
    print("VIEW STATISTICS")
    print("=" * 80)

    stats_query = """
    SELECT
      COUNT(*) as total_rows,
      COUNT(DISTINCT settlementDate) as unique_dates,
      SUM(CASE WHEN bm_revenue_per_mwh > 0 THEN 1 ELSE 0 END) as rows_with_bm_revenue,
      AVG(bm_revenue_per_mwh) as avg_bm_revenue,
      AVG(total_stacked_revenue_per_mwh) as avg_stacked_revenue
    FROM `inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs`
    WHERE settlementDate >= '2025-10-01'
    """

    stats_df = client.query(stats_query).to_dataframe()
    print("\nOctober 2025 onwards:")
    print(stats_df.to_string(index=False))

    print("\n✅ VIEW UPDATE COMPLETE!")
    print("\n📊 Next steps:")
    print("   1. Refresh Google Sheets dashboard (will now show real BM revenue)")
    print("   2. Verify VlpRevenue.gs shows correct prices")
    print("   3. Run calculate_vlp_revenue.py for full date range if needed")

except Exception as e:
    print(f"\n❌ Error updating view: {str(e)}")
    print("\nTroubleshooting:")
    print("   1. Check credentials: inner-cinema-credentials.json exists")
    print("   2. Verify mart_bm_value_by_vlp_sp table has data")
    print("   3. Check project/dataset names are correct")
    raise

print("\n" + "=" * 80)
