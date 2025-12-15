CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs` AS

WITH 
  -- 1. Time & Period Definition
  TimeBase AS (
    SELECT
      settlementDate AS settlement_date,
      settlementPeriod AS settlement_period,
      TIMESTAMP_ADD(CAST(settlementDate AS TIMESTAMP), INTERVAL (settlementPeriod - 1) * 30 MINUTE) AS sp_start_utc,
      0.5 AS sp_duration_hours,
      CASE 
        WHEN EXTRACT(DAYOFWEEK FROM settlementDate) IN (1, 7) THEN 'Weekend'
        ELSE 'Weekday'
      END AS day_type
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
    WHERE settlementDate >= '2024-01-01' -- Adjust start date as needed
  ),

  -- 2. System Prices (Imbalance)
  SystemPrices AS (
    SELECT
      settlementDate,
      settlementPeriod,
      systemSellPrice AS ssp_price_gbp_mwh,
      systemBuyPrice AS sbp_price_gbp_mwh
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
  ),

  -- 3. Wholesale Prices (Market Index)
  WholesalePrices AS (
    SELECT
      settlementDate,
      settlementPeriod,
      price AS wholesale_price_id, -- Intraday / MID price
      volume
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
  ),

  -- 4. DUoS Time Bands (Example Logic for UKPN-EPN)
  DuosLogic AS (
    SELECT
      settlement_date,
      settlement_period,
      sp_start_utc,
      CASE
        -- Weekday Red: 16:00 - 19:00 (SPs 33-38)
        WHEN day_type = 'Weekday' AND settlement_period BETWEEN 33 AND 38 THEN 'Red'
        -- Weekday Amber: 07:00-16:00 (15-32), 19:00-23:00 (39-46)
        WHEN day_type = 'Weekday' AND (settlement_period BETWEEN 15 AND 32 OR settlement_period BETWEEN 39 AND 46) THEN 'Amber'
        -- All other times Green
        ELSE 'Green'
      END AS duos_band
    FROM TimeBase
  ),

  -- 5. DUoS Rates (Hardcoded for now, should be a join)
  DuosRates AS (
    SELECT 'Red' as band, 4.837 as import_rate, 0.0 as export_credit UNION ALL
    SELECT 'Amber', 0.457, 0.0 UNION ALL
    SELECT 'Green', 0.038, 0.0
  )

SELECT
  t.settlement_date,
  t.settlement_period,
  t.sp_start_utc,
  t.sp_duration_hours,
  
  -- Site Metadata (Placeholders)
  '_P' AS gsp_id,
  'North Scotland' AS dno_region,
  'BMU_BESS_01' AS bm_unit_id_bess,
  'BMU_CHP_01' AS bm_unit_id_chp,
  TRUE AS is_bess_baselined,
  TRUE AS is_chp_baselined,

  -- Baseline & Meter Data (Placeholders - would come from Meter Data tables)
  0.0 AS baseline_bess_mwh,
  0.0 AS baseline_chp_mwh,
  0.0 AS actual_bess_mwh,
  0.0 AS actual_chp_mwh,
  0.0 AS deviation_bess_mwh,
  0.0 AS deviation_chp_mwh,

  -- Market Prices
  COALESCE(sp.ssp_price_gbp_mwh, 0) AS ssp_price_gbp_mwh,
  COALESCE(sp.sbp_price_gbp_mwh, 0) AS sbp_price_gbp_mwh,
  COALESCE(wp.wholesale_price_id, 0) AS wholesale_price_da, -- Using ID as proxy for DA if missing
  COALESCE(wp.wholesale_price_id, 0) AS wholesale_price_id,
  
  -- Contract Prices (Placeholders)
  150.0 AS ppa_price_gbp_mwh,
  
  -- Service Prices (Placeholders)
  220.0 AS bm_offer_price_bess,
  -50.0 AS bm_bid_price_bess,
  15.0 AS eso_util_price_bess,
  10.0 AS eso_avail_price_bess,
  0.0 AS dso_avail_price_bess,
  5.0 AS cm_price_gbp_kw_yr,

  -- Network Costs
  d.duos_band,
  dr.import_rate AS duos_import_gbp_mwh,
  10.0 AS tnuos_import_gbp_mwh, -- Estimate
  5.0 AS bsuos_import_gbp_mwh,  -- Estimate
  25.0 AS levies_import_gbp_mwh, -- RO/FiT/CfD Estimate
  
  -- Calculated Full Import Cost
  (COALESCE(wp.wholesale_price_id, 0) + dr.import_rate + 10.0 + 5.0 + 25.0) AS full_import_cost_gbp_mwh,

  -- BESS Costs (Efficiency adjusted)
  -- Charge Cost = Import Cost
  (COALESCE(wp.wholesale_price_id, 0) + dr.import_rate + 10.0 + 5.0 + 25.0) AS bess_charge_cost_gbp_mwh,
  -- Discharge Cost = Opportunity Cost or Fuel? Usually 0 marginal cost for battery, but efficiency loss matters
  0.0 AS bess_discharge_cost_gbp_mwh,

  -- CHP Costs
  80.0 AS chp_fuel_cost_gbp_mwh_el, -- Gas price converted
  20.0 AS chp_heat_value_gbp_mwh_th,
  60.0 AS chp_marginal_cost_gbp_mwh, -- Net cost

  -- Flags
  FALSE AS event_day_flag,
  FALSE AS bm_acceptance_flag,
  FALSE AS wholesale_activity_flag

FROM TimeBase t
LEFT JOIN SystemPrices sp ON t.settlement_date = sp.settlementDate AND t.settlement_period = sp.settlementPeriod
LEFT JOIN WholesalePrices wp ON t.settlement_date = wp.settlementDate AND t.settlement_period = wp.settlementPeriod
LEFT JOIN DuosLogic d ON t.settlement_date = d.settlement_date AND t.settlement_period = d.settlement_period
LEFT JOIN DuosRates dr ON d.duos_band = dr.band
WHERE t.settlement_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY);
