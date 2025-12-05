-- v_bess_cashflow_inputs: Unified per-SP cashflow for BESS revenue engine
-- Combines: FR auctions, BM BOAs, VLP events, wholesale prices, imbalance, system data
-- Usage: Python dashboard_pipeline.py reads this for BESS sheet population

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.v_bess_cashflow_inputs` AS

WITH 
  -- Settlement periods timeline (48 per day)
  sp_timeline AS (
    SELECT 
      TIMESTAMP_ADD(
        TIMESTAMP_TRUNC(settlement_date, DAY),
        INTERVAL (settlement_period - 1) * 30 MINUTE
      ) AS settlement_datetime,
      settlement_date,
      settlement_period
    FROM UNNEST(GENERATE_DATE_ARRAY('2024-01-01', CURRENT_DATE())) AS settlement_date
    CROSS JOIN UNNEST(GENERATE_ARRAY(1, 48)) AS settlement_period
  ),
  
  -- FR availability auctions (DC/DR/DM)
  fr_avail AS (
    SELECT
      dc.settlement_datetime,
      dc.service_type,
      dc.clearing_price_gbp_mw_h,
      dc.contracted_mw,
      dc.availability_hours,
      dc.availability_payment_gbp
    FROM `inner-cinema-476211-u9.uk_energy_prod.eso_dc_clearances` dc
  ),
  
  -- FR utilization/performance
  fr_util AS (
    SELECT
      settlement_datetime,
      delivered_mw,
      utilisation_price_gbp_mwh,
      utilisation_payment_gbp,
      deviation_penalty_gbp
    FROM `inner-cinema-476211-u9.uk_energy_prod.eso_dc_performance`
  ),
  
  -- BM Bid-Offer Acceptances
  bm_boa AS (
    SELECT
      TIMESTAMP_TRUNC(acceptanceTime, HOUR) AS settlement_datetime,
      SUM(acceptedVolume) AS accepted_volume_mwh,
      AVG(acceptancePrice) AS avg_boa_price_gbp_mwh,
      SUM(acceptedVolume * acceptancePrice) AS boa_revenue_gbp
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
    GROUP BY 1
  ),
  
  -- VLP flexibility events (DFS + DNO flex)
  vlp_flex AS (
    SELECT
      event_datetime AS settlement_datetime,
      delivered_mwh,
      price_gbp_mwh AS vlp_price_gbp_mwh,
      payment_gbp AS vlp_payment_gbp,
      scrp_gbp_mwh,  -- Supplier Compensation Reference Price (P444)
      supplier_compensation_gbp,
      vlp_compensation_gbp
    FROM `inner-cinema-476211-u9.uk_energy_prod.vlp_dfs_events`
  ),
  
  -- System prices (SSP/SBP for imbalance/arbitrage)
  sys_prices AS (
    SELECT
      TIMESTAMP_TRUNC(settlementDate, HOUR) AS settlement_datetime,
      AVG(systemSellPrice) AS ssp_gbp_mwh,
      AVG(systemBuyPrice) AS sbp_gbp_mwh,
      AVG((systemSellPrice + systemBuyPrice) / 2) AS mid_price_gbp_mwh,
      AVG(ABS(systemSellPrice - systemBuyPrice)) AS imbalance_spread_gbp_mwh
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
    GROUP BY 1
  ),
  
  -- Wholesale day-ahead/intraday (if available)
  wholesale AS (
    SELECT
      timestamp AS settlement_datetime,
      price_gbp_mwh AS wholesale_price_gbp_mwh,
      source
    FROM `inner-cinema-476211-u9.uk_energy_prod.wholesale_prices`
  ),
  
  -- Non-energy levies (RO, FiT, CfD, BSUoS, CCL)
  levies AS (
    SELECT
      2025 AS year,  -- TODO: parameterize
      SUM(rate_gbp_per_mwh) AS total_levies_gbp_mwh
    FROM `inner-cinema-476211-u9.uk_energy_prod.non_energy_levy_rates`
    WHERE year = 2025 AND scenario = 'central'
  ),
  
  -- DUoS RAG rates (time-of-use)
  duos_rag AS (
    SELECT
      EXTRACT(HOUR FROM TIMESTAMP('2025-01-01 00:00:00') + INTERVAL sp * 30 MINUTE) AS hour_of_day,
      EXTRACT(DAYOFWEEK FROM TIMESTAMP('2025-01-01')) AS day_of_week,
      CASE
        WHEN EXTRACT(DAYOFWEEK FROM TIMESTAMP('2025-01-01')) IN (1, 7) THEN 'Green'  -- Weekend
        WHEN EXTRACT(HOUR FROM TIMESTAMP('2025-01-01 00:00:00') + INTERVAL sp * 30 MINUTE) BETWEEN 16 AND 19 THEN 'Red'
        WHEN EXTRACT(HOUR FROM TIMESTAMP('2025-01-01 00:00:00') + INTERVAL sp * 30 MINUTE) BETWEEN 8 AND 15 THEN 'Amber'
        WHEN EXTRACT(HOUR FROM TIMESTAMP('2025-01-01 00:00:00') + INTERVAL sp * 30 MINUTE) BETWEEN 20 AND 21 THEN 'Amber'
        ELSE 'Green'
      END AS duos_band,
      CASE
        WHEN EXTRACT(DAYOFWEEK FROM TIMESTAMP('2025-01-01')) IN (1, 7) THEN 0.5  -- Green weekend
        WHEN EXTRACT(HOUR FROM TIMESTAMP('2025-01-01 00:00:00') + INTERVAL sp * 30 MINUTE) BETWEEN 16 AND 19 THEN 25.0  -- Red peak
        WHEN EXTRACT(HOUR FROM TIMESTAMP('2025-01-01 00:00:00') + INTERVAL sp * 30 MINUTE) BETWEEN 8 AND 15 THEN 8.0  -- Amber
        WHEN EXTRACT(HOUR FROM TIMESTAMP('2025-01-01 00:00:00') + INTERVAL sp * 30 MINUTE) BETWEEN 20 AND 21 THEN 8.0
        ELSE 1.5
      END AS duos_rate_gbp_mwh
    FROM UNNEST(GENERATE_ARRAY(1, 48)) AS sp
  ),
  
  -- BESS dispatch schedule (from optimizer or manual)
  bess_dispatch AS (
    SELECT
      settlement_datetime,
      power_mw,  -- positive=discharge, negative=charge
      soc_mwh,
      market_type  -- 'FR', 'BM', 'ARBITRAGE', 'VLP'
    FROM `inner-cinema-476211-u9.uk_energy_prod.bess_dispatch`
  )

-- Main query: join all components
SELECT
  t.settlement_datetime,
  t.settlement_date,
  t.settlement_period,
  
  -- Asset ID (parameterize in Python)
  'BESS_2P5MW_5MWH' AS asset_id,
  2025 AS year,
  
  -- BESS dispatch
  COALESCE(bd.power_mw, 0.0) AS bess_power_mw,
  COALESCE(bd.power_mw * 0.5, 0.0) AS bess_mwh,  -- 30-min periods
  COALESCE(bd.soc_mwh, 2.5) AS soc_mwh,
  COALESCE(bd.market_type, 'IDLE') AS market_type,
  
  -- Prices
  COALESCE(sp.ssp_gbp_mwh, 0.0) AS ssp_gbp_mwh,
  COALESCE(sp.sbp_gbp_mwh, 0.0) AS sbp_gbp_mwh,
  COALESCE(sp.mid_price_gbp_mwh, 50.0) AS mid_price_gbp_mwh,
  COALESCE(sp.imbalance_spread_gbp_mwh, 5.0) AS imbalance_spread_gbp_mwh,
  COALESCE(w.wholesale_price_gbp_mwh, sp.mid_price_gbp_mwh, 50.0) AS wholesale_price_gbp_mwh,
  
  -- Levies & network charges
  COALESCE((SELECT total_levies_gbp_mwh FROM levies), 20.0) AS levies_gbp_mwh,
  COALESCE(dr.duos_rate_gbp_mwh, 5.0) AS duos_rate_gbp_mwh,
  COALESCE(dr.duos_band, 'Green') AS duos_band,
  
  -- Import price (wholesale + levies + DUoS + BSUoS)
  COALESCE(sp.mid_price_gbp_mwh, 50.0) + 
  COALESCE((SELECT total_levies_gbp_mwh FROM levies), 20.0) +
  COALESCE(dr.duos_rate_gbp_mwh, 5.0) +
  5.0 AS import_price_gbp_mwh,  -- +5 for BSUoS
  
  -- FR revenue components
  COALESCE(fr_a.availability_payment_gbp, 0.0) AS fr_availability_gbp,
  COALESCE(fr_u.utilisation_payment_gbp, 0.0) AS fr_utilisation_gbp,
  COALESCE(fr_u.deviation_penalty_gbp, 0.0) AS fr_penalty_gbp,
  
  -- BM BOA revenue
  COALESCE(boa.boa_revenue_gbp, 0.0) AS boa_revenue_gbp,
  
  -- VLP flexibility revenue (with P444 compensation)
  COALESCE(vf.vlp_payment_gbp, 0.0) AS vlp_payment_gbp,
  COALESCE(vf.scrp_gbp_mwh, 150.0) AS scrp_gbp_mwh,
  COALESCE(vf.supplier_compensation_gbp, 0.0) AS supplier_compensation_gbp,
  COALESCE(vf.vlp_compensation_gbp, 0.0) AS vlp_compensation_gbp,
  
  -- Baseline demand for BTM calculations
  0.0 AS baseline_import_mwh,  -- TODO: wire actual baseline
  0.0 AS avoided_import_mwh

FROM sp_timeline t
LEFT JOIN bess_dispatch bd USING (settlement_datetime)
LEFT JOIN fr_avail fr_a USING (settlement_datetime)
LEFT JOIN fr_util fr_u USING (settlement_datetime)
LEFT JOIN bm_boa boa USING (settlement_datetime)
LEFT JOIN vlp_flex vf USING (settlement_datetime)
LEFT JOIN sys_prices sp USING (settlement_datetime)
LEFT JOIN wholesale w USING (settlement_datetime)
LEFT JOIN duos_rag dr ON EXTRACT(HOUR FROM t.settlement_datetime) = dr.hour_of_day

WHERE t.settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
ORDER BY t.settlement_datetime;
