-- GB Power Market - Unified BTM BESS Input View
-- 
-- Single source of truth for battery optimizer
-- Provides all cost and revenue components per half-hour settlement period
--
-- Usage: SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs`

CREATE OR REPLACE VIEW
  `inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs` AS

WITH base_prices AS (
  SELECT
    settlementDate,
    settlementPeriod,
    
    -- Create timestamp for half-hour period
    DATETIME(TIMESTAMP(CONCAT(
      CAST(settlementDate AS STRING), ' ',
      LPAD(CAST(CAST(FLOOR((settlementPeriod-1) / 2) AS INT64) AS STRING), 2, '0'), ':',
      LPAD(CAST(MOD(CAST(settlementPeriod-1 AS INT64), 2) * 30 AS STRING), 2, '0')
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
    
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
  WHERE systemBuyPrice IS NOT NULL
),

duos_rates AS (
  SELECT 'RED' AS duos_band, 17.64 AS duos_rate UNION ALL
  SELECT 'AMBER', 2.05 UNION ALL
  SELECT 'GREEN', 0.11
),

levies AS (
  SELECT
    98.15 AS levies_per_mwh  -- Total: TNUoS £12.50 + BSUoS £4.50 + CCL £7.75 + RO £61.90 + FiT £11.50
),

bm_vlp_revenues AS (
  -- VLP revenue from balancing mechanism acceptances joined with bid-offer prices
  SELECT
    a.settlementDate,
    a.settlementPeriodFrom AS settlementPeriod,
    COUNT(*) AS bm_acceptance_count,
    AVG(
      CASE 
        WHEN a.levelTo > a.levelFrom AND b.offer IS NOT NULL 
        THEN (a.levelTo - a.levelFrom) * b.offer * 0.5  -- Discharge: use offer price, convert MW to MWh
        WHEN a.levelTo < a.levelFrom AND b.bid IS NOT NULL
        THEN (a.levelFrom - a.levelTo) * ABS(b.bid) * 0.5  -- Charge: use bid price
        ELSE 0
      END
    ) AS bm_revenue_per_mwh,
    MAX(b.offer) AS bm_max_offer,
    MIN(b.bid) AS bm_min_bid
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` a
  LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` b
    ON a.bmUnit = b.bmUnit
    AND a.settlementDate = b.settlementDate
    AND a.settlementPeriodFrom = b.settlementPeriod
    AND a.levelFrom = b.levelFrom
    AND a.levelTo = b.levelTo
  WHERE a.bmUnit IN ('2__FBPGM001', '2__FBPGM002')  -- Flexgen VLP units
  GROUP BY 1, 2
),

-- Dynamic Containment revenue (annualized contract value)
dc_revenue_estimate AS (
  SELECT 
    195458.0 AS dc_annual_revenue,
    195458.0 / 17520 AS dc_per_halfhour,  -- £11.15 per half-hour
    195458.0 / 17520 / 2.5 AS dc_revenue_per_mwh  -- £4.46 per MWh for 2.5 MW battery
),

-- Dynamic Moderation revenue (estimated)
dm_revenue_estimate AS (
  SELECT
    100000.0 AS dm_annual_revenue,
    100000.0 / 17520 AS dm_per_halfhour,
    100000.0 / 17520 / 2.5 AS dm_revenue_per_mwh
),

-- Dynamic Regulation revenue (estimated)
dr_revenue_estimate AS (
  SELECT
    150000.0 AS dr_annual_revenue,
    150000.0 / 17520 AS dr_per_halfhour,
    150000.0 / 17520 / 2.5 AS dr_revenue_per_mwh
),

-- Capacity Market revenue
capacity_market AS (
  SELECT
    31250.0 AS cm_annual_revenue,  -- £12.50/kW/year × 2,500 kW
    31250.0 / 17520 AS cm_per_halfhour,
    31250.0 / 17520 / 2.5 AS cm_revenue_per_mwh
),

-- Triad avoidance value (identify potential triad periods)
triad_periods AS (
  SELECT
    settlementDate,
    settlementPeriod,
    CASE 
      WHEN EXTRACT(MONTH FROM settlementDate) BETWEEN 11 AND 2  -- Nov-Feb
        AND EXTRACT(DAYOFWEEK FROM settlementDate) NOT IN (1,7)  -- Weekdays
        AND settlementPeriod BETWEEN 33 AND 39  -- 16:00-19:30 (RED period)
      THEN 40.0  -- £40/kW potential savings = £100k for 2.5 MW
      ELSE 0
    END AS triad_value_per_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
),

-- System stress indicator (high BM activity = high revenue opportunity)
system_stress AS (
  SELECT
    settlementDate,
    settlementPeriodFrom AS settlementPeriod,
    COUNT(DISTINCT bmUnit) AS bm_units_active,
    -- Stress based on acceptance volume, not price (no price in boalf table)
    CASE 
      WHEN COUNT(DISTINCT bmUnit) > 50 THEN TRUE
      WHEN COUNT(*) > 100 THEN TRUE  -- High acceptance count = system stress
      ELSE FALSE
    END AS high_stress_period
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
  GROUP BY 1, 2
),

ppa_config AS (
  -- PPA discharge price
  SELECT 150.0 AS ppa_price
),

joined AS (
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
    
    -- PPA profitability (can import when total cost < £150)
    CASE 
      WHEN (bp.ssp_charge + dr.duos_rate + lev.levies_per_mwh) < ppa.ppa_price 
      THEN ppa.ppa_price - (bp.ssp_charge + dr.duos_rate + lev.levies_per_mwh)
      ELSE 0
    END AS ppa_import_profit_per_mwh
    
  FROM base_prices bp
  LEFT JOIN duos_rates dr
    ON bp.duos_band = dr.duos_band
  CROSS JOIN levies lev
  CROSS JOIN ppa_config ppa
  CROSS JOIN capacity_market cm
  CROSS JOIN dc_revenue_estimate dc
  CROSS JOIN dm_revenue_estimate dm
  CROSS JOIN dr_revenue_estimate dr_est
  LEFT JOIN bm_vlp_revenues bm
    ON bp.settlementDate = bm.settlementDate
   AND bp.settlementPeriod = bm.settlementPeriod
  LEFT JOIN triad_periods tp
    ON bp.settlementDate = tp.settlementDate
   AND bp.settlementPeriod = tp.settlementPeriod
  LEFT JOIN system_stress ss
    ON bp.settlementDate = ss.settlementDate
   AND bp.settlementPeriod = ss.settlementPeriod
)

SELECT 
  *,
  -- Charging signals (will be refined by optimizer)
  CASE 
    WHEN negative_pricing THEN TRUE  -- Always charge when paid to do so!
    WHEN total_cost_per_mwh < 120 THEN TRUE  -- Profitable threshold
    ELSE FALSE 
  END AS can_charge_profitably,
  
  -- Discharge signals
  CASE 
    WHEN net_margin_per_mwh > 0 THEN TRUE  -- Profitable to discharge
    WHEN high_stress_period THEN TRUE  -- High BM revenue opportunity
    WHEN triad_value_per_mwh > 0 THEN TRUE  -- Triad avoidance opportunity
    ELSE FALSE 
  END AS can_discharge_profitably,
  
  -- Service stacking compatibility
  CASE 
    WHEN negative_pricing THEN 'CHARGE_NEGATIVE'
    WHEN high_stress_period AND net_margin_per_mwh > 50 THEN 'DISCHARGE_HIGH_VALUE'
    WHEN triad_value_per_mwh > 0 THEN 'DISCHARGE_TRIAD'
    WHEN ppa_import_profit_per_mwh > 10 THEN 'IMPORT_PROFITABLE'
    WHEN net_margin_per_mwh > 20 THEN 'DISCHARGE_MODERATE'
    WHEN total_cost_per_mwh < 120 THEN 'CHARGE_CHEAP'
    ELSE 'IDLE'
  END AS recommended_action,
  
  -- Revenue opportunity score (0-100)
  LEAST(100, GREATEST(0,
    (net_margin_per_mwh * 0.5) +  -- 50% weight on margin
    (CASE WHEN high_stress_period THEN 20 ELSE 0 END) +  -- 20 points for stress
    (CASE WHEN negative_pricing THEN 30 ELSE 0 END) +  -- 30 points for negative pricing
    (triad_value_per_mwh * 0.5)  -- 50% of triad value
  )) AS opportunity_score
  
FROM joined
ORDER BY ts_halfhour;
