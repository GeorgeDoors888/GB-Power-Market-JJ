#!/usr/bin/env python3
"""
Deploy BM Dashboard Views to BigQuery
Creates optimized views for real-time dashboard queries
"""

from google.cloud import bigquery

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

def create_views():
    """Create BigQuery views for dashboard"""
    
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    print("=" * 80)
    print("📊 CREATING BM DASHBOARD VIEWS")
    print("=" * 80)
    print()
    
    # View 1: Settlement Period Aggregates
    print("Creating v_bm_market_sp...")
    sp_view = f"""
    CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET}.v_bm_market_sp` AS
    
    WITH boav_agg AS (
      SELECT 
        DATE(CAST(settlementDate AS STRING)) AS settlement_date,
        settlementPeriod AS settlement_period,
        SUM(CASE WHEN _direction = 'offer' THEN totalVolumeAccepted ELSE 0 END) AS offer_mwh,
        SUM(CASE WHEN _direction = 'bid' THEN totalVolumeAccepted ELSE 0 END) AS bid_mwh,
        COUNT(DISTINCT nationalGridBmUnit) AS active_bmus,
        COUNT(DISTINCT acceptanceId) AS acceptance_count
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boav`
      GROUP BY settlement_date, settlement_period
    ),
    ebocf_agg AS (
      SELECT 
        DATE(CAST(settlementDate AS STRING)) AS settlement_date,
        settlementPeriod AS settlement_period,
        SUM(CASE WHEN _direction = 'offer' THEN totalCashflow ELSE 0 END) AS offer_cashflow_gbp,
        SUM(CASE WHEN _direction = 'bid' THEN totalCashflow ELSE 0 END) AS bid_cashflow_gbp
      FROM `{PROJECT_ID}.{DATASET}.bmrs_ebocf`
      GROUP BY settlement_date, settlement_period
    )
    
    SELECT
      COALESCE(boav_agg.settlement_date, ebocf_agg.settlement_date) AS settlement_date,
      COALESCE(boav_agg.settlement_period, ebocf_agg.settlement_period) AS settlement_period,
      COALESCE(offer_cashflow_gbp, 0) + COALESCE(bid_cashflow_gbp, 0) AS total_cashflow_gbp,
      COALESCE(offer_cashflow_gbp, 0) AS offer_cashflow_gbp,
      COALESCE(bid_cashflow_gbp, 0) AS bid_cashflow_gbp,
      COALESCE(offer_mwh, 0) AS offer_mwh,
      COALESCE(bid_mwh, 0) AS bid_mwh,
      COALESCE(offer_mwh, 0) - COALESCE(bid_mwh, 0) AS net_mwh,
      ABS(COALESCE(offer_mwh, 0)) + ABS(COALESCE(bid_mwh, 0)) AS total_volume_mwh,
      SAFE_DIVIDE(
        COALESCE(offer_cashflow_gbp, 0) + COALESCE(bid_cashflow_gbp, 0),
        NULLIF(ABS(COALESCE(offer_mwh, 0)) + ABS(COALESCE(bid_mwh, 0)), 0)
      ) AS ewap_gbp_mwh,
      COALESCE(acceptance_count, 0) AS acceptance_count,
      COALESCE(active_bmus, 0) AS active_bmus,
      CURRENT_TIMESTAMP() AS query_time
    
    FROM boav_agg
    FULL OUTER JOIN ebocf_agg 
      ON boav_agg.settlement_date = ebocf_agg.settlement_date
      AND boav_agg.settlement_period = ebocf_agg.settlement_period
    """
    
    client.query(sp_view).result()
    print("   ✅ Created v_bm_market_sp")
    print()
    
    # View 2: Battery Daily Summary
    print("Creating v_bm_battery_daily...")
    battery_view = f"""
    CREATE OR REPLACE VIEW `{PROJECT_ID}.{DATASET}.v_bm_battery_daily` AS
    
    WITH battery_totals AS (
      SELECT 
        DATE(CAST(boav.settlementDate AS STRING)) AS settlement_date,
        boav.nationalGridBmUnit,
        meta.fuelType AS technology,
        meta.registeredCapacity AS capacity_mw,
        SUM(CASE WHEN boav._direction = 'offer' THEN ebocf.totalCashflow ELSE 0 END) AS offer_revenue,
        SUM(CASE WHEN boav._direction = 'bid' THEN ebocf.totalCashflow ELSE 0 END) AS bid_revenue,
        SUM(CASE WHEN boav._direction = 'offer' THEN boav.totalVolumeAccepted ELSE 0 END) AS offer_mwh,
        SUM(CASE WHEN boav._direction = 'bid' THEN boav.totalVolumeAccepted ELSE 0 END) AS bid_mwh,
        COUNT(DISTINCT boav.settlementPeriod) AS active_sps
      FROM `{PROJECT_ID}.{DATASET}.bmrs_boav` boav
      LEFT JOIN `{PROJECT_ID}.{DATASET}.bmrs_ebocf` ebocf
        ON boav.nationalGridBmUnit = ebocf.nationalGridBmUnit
        AND boav.settlementDate = ebocf.settlementDate
        AND boav.settlementPeriod = ebocf.settlementPeriod
        AND boav._direction = ebocf._direction
      LEFT JOIN `{PROJECT_ID}.{DATASET}.bmu_metadata` meta
        ON boav.nationalGridBmUnit = meta.nationalGridBmUnit
      WHERE meta.fuelType IN ('PS', 'BESS', 'Battery')
      GROUP BY settlement_date, nationalGridBmUnit, technology, capacity_mw
    )
    
    SELECT
      settlement_date,
      nationalGridBmUnit AS bmu_id,
      technology,
      capacity_mw,
      offer_revenue + bid_revenue AS net_revenue,
      offer_revenue,
      bid_revenue,
      ABS(offer_mwh) + ABS(bid_mwh) AS total_mwh,
      offer_mwh,
      bid_mwh,
      SAFE_DIVIDE(offer_revenue + bid_revenue, ABS(offer_mwh) + ABS(bid_mwh)) AS vwap,
      SAFE_DIVIDE(offer_revenue + bid_revenue, capacity_mw) AS revenue_per_mw_day,
      active_sps,
      RANK() OVER (PARTITION BY settlement_date ORDER BY (offer_revenue + bid_revenue) DESC) AS daily_rank
    FROM battery_totals
    WHERE offer_revenue + bid_revenue > 0
    """
    
    client.query(battery_view).result()
    print("   ✅ Created v_bm_battery_daily")
    print()
    
    # Test queries
    print("Testing views...")
    
    test1 = f"""
    SELECT COUNT(*) as sp_count, MIN(settlement_date) as min_date, MAX(settlement_date) as max_date
    FROM `{PROJECT_ID}.{DATASET}.v_bm_market_sp`
    """
    result1 = list(client.query(test1).result())[0]
    print(f"   v_bm_market_sp: {result1.sp_count:,} settlement periods ({result1.min_date} to {result1.max_date})")
    
    test2 = f"""
    SELECT COUNT(*) as record_count, COUNT(DISTINCT bmu_id) as unique_bmus
    FROM `{PROJECT_ID}.{DATASET}.v_bm_battery_daily`
    """
    result2 = list(client.query(test2).result())[0]
    print(f"   v_bm_battery_daily: {result2.record_count:,} records, {result2.unique_bmus} unique batteries")
    print()
    
    print("=" * 80)
    print("✅ VIEWS CREATED SUCCESSFULLY")
    print("=" * 80)
    print()
    print("Usage in Google Sheets:")
    print(f'  =QUERY("{PROJECT_ID}.{DATASET}.v_bm_market_sp", "SELECT * WHERE settlement_date = CURRENT_DATE() ORDER BY settlement_period DESC LIMIT 12")')
    print(f'  =QUERY("{PROJECT_ID}.{DATASET}.v_bm_battery_daily", "SELECT * WHERE settlement_date = CURRENT_DATE() AND daily_rank <= 10 ORDER BY net_revenue DESC")')
    print()

if __name__ == "__main__":
    create_views()
