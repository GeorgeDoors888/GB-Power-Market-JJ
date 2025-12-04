-- GB Power Market - Unified BTM BESS Input View (Historical + IRIS Real-Time)
-- 
-- Single source of truth for battery optimizer
-- Combines historical data (Jan 2022 - Oct 2025) with IRIS real-time (Nov 2025+)
--
-- Usage: SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs`

CREATE OR REPLACE VIEW
  `inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs` AS

WITH 
-- CUTOFF DATE between historical and real-time data
config AS (
  SELECT DATE('2025-10-29') AS cutoff_date
),

-- Base prices: UNION historical bmrs_costs + real-time bmrs_mid_iris
base_prices AS (
  -- Historical data (Jan 2022 - Oct 28, 2025)
  SELECT
    settlementDate,
    settlementPeriod,
    
    -- Create timestamp for half-hour period
    DATETIME(TIMESTAMP(CONCAT(
      CAST(settlementDate AS STRING), ' ',
      LPAD(CAST(CAST(FLOOR((settlementPeriod-1) / 2) AS INT64) AS STRING), 2, '0'), ':',
      LPAD(CAST(MOD(CAST(settlementPeriod-1 AS INT64), 2) * 30 AS STRING), 2, '0'), ':00'
    ))) AS ts_halfhour,

    systemBuyPrice AS ssp_charge,
    systemSellPrice AS ssp_sell,
    
    -- Determine DUoS band (RED/AMBER/GREEN)
    CASE
      WHEN settlementPeriod BETWEEN 33 AND 39  -- 16:00-19:30
           AND EXTRACT(DAYOFWEEK FROM settlementDate) NOT IN (1,7)  -- Weekdays only
      THEN 'RED'
      
      WHEN (settlementPeriod BETWEEN 17 AND 32  -- 08:00-16:00
         OR settlementPeriod BETWEEN 40 AND 44)  -- 19:30-22:00
           AND EXTRACT(DAYOFWEEK FROM settlementDate) NOT IN (1,7)
      THEN 'AMBER'
      
      ELSE 'GREEN'  -- All other times + weekends
    END AS duos_band,
    
    -- Extract time components for analysis
    EXTRACT(HOUR FROM DATETIME(TIMESTAMP(CONCAT(
      CAST(settlementDate AS STRING), ' ',
      LPAD(CAST(CAST(FLOOR((settlementPeriod-1) / 2) AS INT64) AS STRING), 2, '0'), ':00:00'
    )))) AS hour_of_day,
    EXTRACT(DAYOFWEEK FROM settlementDate) AS day_of_week,
    EXTRACT(MONTH FROM settlementDate) AS month
    
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`, config
  WHERE systemBuyPrice IS NOT NULL
    AND CAST(settlementDate AS DATE) < config.cutoff_date
  
  UNION ALL
  
  -- Real-time IRIS data (Oct 29, 2025 onwards)
  SELECT
    CAST(settlementDate AS DATE) AS settlementDate,
    settlementPeriod,
    
    -- Create timestamp for half-hour period
    DATETIME(TIMESTAMP(CONCAT(
      CAST(settlementDate AS STRING), ' ',
      LPAD(CAST(CAST(FLOOR((settlementPeriod-1) / 2) AS INT64) AS STRING), 2, '0'), ':',
      LPAD(CAST(MOD(CAST(settlementPeriod-1 AS INT64), 2) * 30 AS STRING), 2, '0'), ':00'
    ))) AS ts_halfhour,

    -- IRIS only has single price - use as both buy and sell (conservative estimate)
    price AS ssp_charge,
    price AS ssp_sell,
    
    -- Determine DUoS band (RED/AMBER/GREEN)
    CASE
      WHEN settlementPeriod BETWEEN 33 AND 39
           AND EXTRACT(DAYOFWEEK FROM CAST(settlementDate AS DATE)) NOT IN (1,7)
      THEN 'RED'
      
      WHEN (settlementPeriod BETWEEN 17 AND 32
         OR settlementPeriod BETWEEN 40 AND 44)
           AND EXTRACT(DAYOFWEEK FROM CAST(settlementDate AS DATE)) NOT IN (1,7)
      THEN 'AMBER'
      
      ELSE 'GREEN'
    END AS duos_band,
    
    -- Extract time components
    EXTRACT(HOUR FROM DATETIME(TIMESTAMP(CONCAT(
      CAST(settlementDate AS STRING), ' ',
      LPAD(CAST(CAST(FLOOR((settlementPeriod-1) / 2) AS INT64) AS STRING), 2, '0'), ':00:00'
    )))) AS hour_of_day,
    EXTRACT(DAYOFWEEK FROM CAST(settlementDate AS DATE)) AS day_of_week,
    EXTRACT(MONTH FROM CAST(settlementDate AS DATE)) AS month
    
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid_iris`, config
  WHERE price IS NOT NULL
    AND CAST(settlementDate AS DATE) >= config.cutoff_date
),

duos_rates AS (
  -- DUoS charges per band (HV voltage example: NGED West Midlands)
  SELECT 'RED' AS band, 17.64 AS duos_rate
  UNION ALL SELECT 'AMBER', 4.57
  UNION ALL SELECT 'GREEN', 1.11
),

levies AS (
  SELECT
    12.50 AS tnuos_per_mwh,   -- Transmission Network Use of System
    4.50 AS bsuos_per_mwh,    -- Balancing Services Use of System
    7.75 AS ccl_per_mwh,      -- Climate Change Levy
    61.90 AS ro_per_mwh,      -- Renewables Obligation
    11.50 AS fit_per_mwh,     -- Feed-in Tariff
    98.15 AS levies_per_mwh  -- Total: TNUoS £12.50 + BSUoS £4.50 + CCL £7.75 + RO £61.90 + FiT £11.50
),

-- BM VLP revenues: UNION historical boalf + IRIS boalf
bm_vlp_revenues AS (
  -- Historical acceptances
  SELECT
    a.settlementDate,
    a.settlementPeriodFrom AS settlementPeriod,
    COUNT(*) AS bm_acceptance_count,
    AVG(
      CASE 
        WHEN a.levelTo > a.levelFrom AND b.offer IS NOT NULL 
        THEN (a.levelTo - a.levelFrom) * b.offer * 0.5
        WHEN a.levelTo < a.levelFrom AND b.bid IS NOT NULL
        THEN (a.levelFrom - a.levelTo) * ABS(b.bid) * 0.5
        ELSE 0
      END
    ) AS bm_revenue_per_mwh,
    MAX(b.offer) AS bm_max_offer,
    MIN(b.bid) AS bm_min_bid
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` a
  CROSS JOIN config
  LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` b
    ON a.bmUnit = b.bmUnit
    AND a.settlementDate = b.settlementDate
    AND a.settlementPeriodFrom = b.settlementPeriod
    AND a.levelFrom = b.levelFrom
    AND a.levelTo = b.levelTo
  WHERE a.bmUnit IN ('2__FBPGM001', '2__FBPGM002')
    AND CAST(a.settlementDate AS DATE) < config.cutoff_date
  GROUP BY 1, 2
  
  UNION ALL
  
  -- Real-time IRIS acceptances
  SELECT
    CAST(a.settlementDate AS DATE) AS settlementDate,
    a.settlementPeriodFrom AS settlementPeriod,
    COUNT(*) AS bm_acceptance_count,
    AVG(
      CASE 
        WHEN a.levelTo > a.levelFrom AND b.offer IS NOT NULL 
        THEN (a.levelTo - a.levelFrom) * b.offer * 0.5
        WHEN a.levelTo < a.levelFrom AND b.bid IS NOT NULL
        THEN (a.levelFrom - a.levelTo) * ABS(b.bid) * 0.5
        ELSE 0
      END
    ) AS bm_revenue_per_mwh,
    MAX(b.offer) AS bm_max_offer,
    MIN(b.bid) AS bm_min_bid
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris` a
  CROSS JOIN config
  LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris` b
    ON a.bmUnit = b.bmUnit
    AND CAST(a.settlementDate AS DATE) = CAST(b.settlementDate AS DATE)
    AND a.settlementPeriodFrom = b.settlementPeriod
    AND a.levelFrom = b.levelFrom
    AND a.levelTo = b.levelTo
  WHERE a.bmUnit IN ('2__FBPGM001', '2__FBPGM002')
    AND CAST(a.settlementDate AS DATE) >= config.cutoff_date
  GROUP BY 1, 2
),

-- Dynamic Containment revenue (annualized contract value)
dc_revenue_estimate AS (
  SELECT 
    195458.0 AS dc_annual_revenue,
    2482.0 AS annual_mwh_discharged,  -- From PPA analysis
    195458.0 / 2482.0 AS dc_revenue_per_mwh
),

-- Dynamic Moderation revenue (estimated)
dm_revenue_estimate AS (
  SELECT 
    100000.0 AS dm_annual_revenue,
    2482.0 AS annual_mwh_discharged,
    100000.0 / 2482.0 AS dm_revenue_per_mwh
),

-- Dynamic Regulation revenue (estimated)
dr_revenue_estimate AS (
  SELECT 
    150000.0 AS dr_annual_revenue,
    2482.0 AS annual_mwh_discharged,
    150000.0 / 2482.0 AS dr_revenue_per_mwh
),

-- Capacity Market revenue
cm_revenue_estimate AS (
  SELECT 
    31250.0 AS cm_annual_revenue,
    2482.0 AS annual_mwh_discharged,
    31250.0 / 2482.0 AS cm_revenue_per_mwh
),

-- Triad periods (3 highest peak demand half-hours Nov-Feb, weekdays 4-7pm)
triad_periods AS (
  SELECT
    settlementDate,
    settlementPeriod,
    TRUE AS is_triad_period,
    100000.0 / 2482.0 AS triad_value_per_mwh  -- £100k annual / 2482 MWh
  FROM (
    SELECT 
      settlementDate,
      settlementPeriod,
      ROW_NUMBER() OVER (
        PARTITION BY EXTRACT(YEAR FROM settlementDate)
        ORDER BY settlementPeriod DESC
      ) as rn
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
    WHERE EXTRACT(MONTH FROM settlementDate) BETWEEN 11 AND 2  -- Nov-Feb
      AND settlementPeriod BETWEEN 33 AND 39  -- 4-7pm
      AND EXTRACT(DAYOFWEEK FROM settlementDate) NOT IN (1,7)  -- Weekdays
  )
  WHERE rn <= 3  -- Top 3 peaks
),

-- System stress indicator (high BM activity = revenue opportunity)
system_stress AS (
  -- Historical
  SELECT
    a.settlementDate,
    a.settlementPeriodFrom AS settlementPeriod,
    COUNT(DISTINCT a.bmUnit) AS bm_units_active,
    CASE 
      WHEN COUNT(DISTINCT a.bmUnit) > 50 THEN TRUE
      WHEN COUNT(*) > 100 THEN TRUE
      ELSE FALSE
    END AS high_stress_period
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` a
  CROSS JOIN config
  WHERE CAST(a.settlementDate AS DATE) < config.cutoff_date
  GROUP BY 1, 2
  
  UNION ALL
  
  -- Real-time IRIS
  SELECT
    CAST(a.settlementDate AS DATE) AS settlementDate,
    a.settlementPeriodFrom AS settlementPeriod,
    COUNT(DISTINCT a.bmUnit) AS bm_units_active,
    CASE 
      WHEN COUNT(DISTINCT a.bmUnit) > 50 THEN TRUE
      WHEN COUNT(*) > 100 THEN TRUE
      ELSE FALSE
    END AS high_stress_period
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris` a
  CROSS JOIN config
  WHERE CAST(a.settlementDate AS DATE) >= config.cutoff_date
  GROUP BY 1, 2
),

ppa_config AS (
  -- PPA discharge price
  SELECT 150.0 AS ppa_price
)

-- Final SELECT: Join all revenue streams
SELECT
    bp.ts_halfhour,
    bp.settlementDate,
    bp.settlementPeriod,
    bp.hour_of_day,
    bp.day_of_week,
    bp.month,
    bp.duos_band,
    
    -- Costs
    bp.ssp_charge,
    dr.duos_rate AS duos_charge,
    lev.levies_per_mwh,
    
    -- PPA Revenue (discharge at £150/MWh when site demand exists)
    ppa.ppa_price,
    
    -- VLP Revenue Streams (ALL STACKABLE)
    COALESCE(bm.bm_revenue_per_mwh, 0) AS bm_revenue_per_mwh,
    COALESCE(bm.bm_acceptance_count, 0) AS bm_acceptance_count,
    COALESCE(bm.bm_max_offer, 0) AS bm_max_offer,
    COALESCE(bm.bm_min_bid, 0) AS bm_min_bid,
    dc.dc_revenue_per_mwh,
    dc.dc_annual_revenue,
    dm.dm_revenue_per_mwh,
    dm.dm_annual_revenue,
    dr_est.dr_revenue_per_mwh,
    dr_est.dr_annual_revenue,
    cm.cm_revenue_per_mwh,
    cm.cm_annual_revenue,
    COALESCE(tp.triad_value_per_mwh, 0) AS triad_value_per_mwh,
    
    -- System stress indicators
    COALESCE(ss.bm_units_active, 0) AS bm_units_active,
    COALESCE(ss.high_stress_period, FALSE) AS high_stress_period,
    
    -- Negative pricing flag (GET PAID TO CHARGE!)
    CASE WHEN bp.ssp_charge < 0 THEN TRUE ELSE FALSE END AS negative_pricing,
    CASE WHEN bp.ssp_charge < 0 THEN ABS(bp.ssp_charge) ELSE 0 END AS paid_to_charge_amount,
    
    -- Total stacked revenue per MWh (all services combined)
    ppa.ppa_price + 
    COALESCE(bm.bm_revenue_per_mwh, 0) + 
    dc.dc_revenue_per_mwh + 
    dm.dm_revenue_per_mwh + 
    dr_est.dr_revenue_per_mwh + 
    cm.cm_revenue_per_mwh + 
    COALESCE(tp.triad_value_per_mwh, 0) AS total_stacked_revenue_per_mwh,
    
    -- Computed totals
    bp.ssp_charge + dr.duos_rate + lev.levies_per_mwh AS total_cost_per_mwh,
    
    -- Net profit per MWh (all revenues - all costs)
    (ppa.ppa_price + 
     COALESCE(bm.bm_revenue_per_mwh, 0) + 
     dc.dc_revenue_per_mwh + 
     dm.dm_revenue_per_mwh + 
     dr_est.dr_revenue_per_mwh + 
     cm.cm_revenue_per_mwh + 
     COALESCE(tp.triad_value_per_mwh, 0)) - 
    (bp.ssp_charge + dr.duos_rate + lev.levies_per_mwh) AS net_margin_per_mwh,
    
    -- Trading signals (optimizer uses these)
    CASE
      WHEN bp.ssp_charge < 0 THEN 'CHARGE_PAID'  -- Negative pricing!
      WHEN (ppa.ppa_price + COALESCE(bm.bm_revenue_per_mwh, 0) + dc.dc_revenue_per_mwh) - 
           (bp.ssp_charge + dr.duos_rate + lev.levies_per_mwh) > 50 
      THEN 'DISCHARGE_HIGH'
      WHEN (ppa.ppa_price + COALESCE(bm.bm_revenue_per_mwh, 0) + dc.dc_revenue_per_mwh) - 
           (bp.ssp_charge + dr.duos_rate + lev.levies_per_mwh) > 20 
      THEN 'DISCHARGE_MODERATE'
      WHEN bp.ssp_charge + dr.duos_rate + lev.levies_per_mwh < 120  -- Below PPA break-even
      THEN 'CHARGE_CHEAP'
      ELSE 'HOLD'
    END AS trading_signal
    
FROM base_prices bp
CROSS JOIN duos_rates dr
CROSS JOIN levies lev
CROSS JOIN ppa_config ppa
CROSS JOIN dc_revenue_estimate dc
CROSS JOIN dm_revenue_estimate dm
CROSS JOIN dr_revenue_estimate dr_est
CROSS JOIN cm_revenue_estimate cm
LEFT JOIN bm_vlp_revenues bm
  ON bp.settlementDate = bm.settlementDate
  AND bp.settlementPeriod = bm.settlementPeriod
LEFT JOIN triad_periods tp
  ON bp.settlementDate = tp.settlementDate
  AND bp.settlementPeriod = tp.settlementPeriod
LEFT JOIN system_stress ss
  ON bp.settlementDate = ss.settlementDate
  AND bp.settlementPeriod = ss.settlementPeriod
WHERE bp.duos_band = dr.band
ORDER BY bp.settlementDate DESC, bp.settlementPeriod DESC;
