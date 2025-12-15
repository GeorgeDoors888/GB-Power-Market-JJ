-- ============================================================================
-- BM MARKET SP VIEW - Settlement Period Level Aggregates
-- ============================================================================
-- Purpose: Provides clean, aggregated BM data at settlement period level
-- for real-time dashboard KPIs and trending
--
-- Usage in Google Sheets:
--   =QUERY(v_bm_market_sp, "SELECT * WHERE settlement_date = CURRENT_DATE() ORDER BY settlement_period DESC LIMIT 12")
--
-- Author: George Major
-- Date: 2025-12-14
-- ============================================================================

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.v_bm_market_sp` AS

WITH
-- Aggregate acceptance volumes by SP
boav_agg AS (
  SELECT 
    DATE(CAST(settlementDate AS STRING)) AS settlement_date,
    settlementPeriod AS settlement_period,
    SUM(CASE WHEN _direction = 'offer' THEN totalVolumeAccepted ELSE 0 END) AS offer_mwh,
    SUM(CASE WHEN _direction = 'bid' THEN totalVolumeAccepted ELSE 0 END) AS bid_mwh,
    COUNT(DISTINCT nationalGridBmUnit) AS active_bmus,
    COUNT(DISTINCT acceptanceId) AS acceptance_count
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boav`
  GROUP BY settlement_date, settlement_period
),

-- Aggregate cashflows by SP
ebocf_agg AS (
  SELECT 
    DATE(CAST(settlementDate AS STRING)) AS settlement_date,
    settlementPeriod AS settlement_period,
    SUM(CASE WHEN _direction = 'offer' THEN totalCashflow ELSE 0 END) AS offer_cashflow_gbp,
    SUM(CASE WHEN _direction = 'bid' THEN totalCashflow ELSE 0 END) AS bid_cashflow_gbp
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf`
  GROUP BY settlement_date, settlement_period
)

-- Combine and calculate KPIs
SELECT
  COALESCE(boav_agg.settlement_date, ebocf_agg.settlement_date) AS settlement_date,
  COALESCE(boav_agg.settlement_period, ebocf_agg.settlement_period) AS settlement_period,
  
  -- Revenue KPIs
  COALESCE(offer_cashflow_gbp, 0) + COALESCE(bid_cashflow_gbp, 0) AS total_cashflow_gbp,
  COALESCE(offer_cashflow_gbp, 0) AS offer_cashflow_gbp,
  COALESCE(bid_cashflow_gbp, 0) AS bid_cashflow_gbp,
  
  -- Volume KPIs
  COALESCE(offer_mwh, 0) AS offer_mwh,
  COALESCE(bid_mwh, 0) AS bid_mwh,
  COALESCE(offer_mwh, 0) - COALESCE(bid_mwh, 0) AS net_mwh,
  ABS(COALESCE(offer_mwh, 0)) + ABS(COALESCE(bid_mwh, 0)) AS total_volume_mwh,
  
  -- Price KPIs
  SAFE_DIVIDE(
    COALESCE(offer_cashflow_gbp, 0) + COALESCE(bid_cashflow_gbp, 0),
    NULLIF(ABS(COALESCE(offer_mwh, 0)) + ABS(COALESCE(bid_mwh, 0)), 0)
  ) AS ewap_gbp_mwh,  -- Energy Weighted Average Price
  
  -- Activity KPIs
  COALESCE(acceptance_count, 0) AS acceptance_count,
  COALESCE(active_bmus, 0) AS active_bmus,
  
  -- Timestamp for real-time tracking
  CURRENT_TIMESTAMP() AS query_time

FROM boav_agg
FULL OUTER JOIN ebocf_agg 
  ON boav_agg.settlement_date = ebocf_agg.settlement_date
  AND boav_agg.settlement_period = ebocf_agg.settlement_period

ORDER BY settlement_date DESC, settlement_period DESC;


-- ============================================================================
-- BM BATTERY SUMMARY VIEW - Daily Battery Performance
-- ============================================================================
-- Purpose: Top performing batteries for dashboard display
-- ============================================================================

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.v_bm_battery_daily` AS

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
    
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boav` boav
  LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf` ebocf
    ON boav.nationalGridBmUnit = ebocf.nationalGridBmUnit
    AND boav.settlementDate = ebocf.settlementDate
    AND boav.settlementPeriod = ebocf.settlementPeriod
    AND boav._direction = ebocf._direction
  LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmu_metadata` meta
    ON boav.nationalGridBmUnit = meta.nationalGridBmUnit
    
  WHERE meta.fuelType IN ('PS', 'BESS', 'Battery')  -- Battery technologies only
  
  GROUP BY settlement_date, nationalGridBmUnit, technology, capacity_mw
)

SELECT
  settlement_date,
  nationalGridBmUnit AS bmu_id,
  technology,
  capacity_mw,
  
  -- Revenue
  offer_revenue + bid_revenue AS net_revenue,
  offer_revenue,
  bid_revenue,
  
  -- Volume
  ABS(offer_mwh) + ABS(bid_mwh) AS total_mwh,
  offer_mwh,
  bid_mwh,
  
  -- Performance KPIs
  SAFE_DIVIDE(offer_revenue + bid_revenue, ABS(offer_mwh) + ABS(bid_mwh)) AS vwap,
  SAFE_DIVIDE(offer_revenue + bid_revenue, capacity_mw) AS revenue_per_mw_day,
  active_sps,
  
  -- Rankings
  RANK() OVER (PARTITION BY settlement_date ORDER BY (offer_revenue + bid_revenue) DESC) AS daily_rank

FROM battery_totals

WHERE offer_revenue + bid_revenue > 0  -- Only show revenue-generating units

ORDER BY settlement_date DESC, net_revenue DESC;
