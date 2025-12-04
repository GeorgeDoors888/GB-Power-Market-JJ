-- BigQuery Table Schemas for FR Revenue Optimizer
-- ================================================
-- Project: inner-cinema-476211-u9
-- Dataset: uk_energy_prod
-- Date: 1 December 2025

-- =============================================================================
-- 1. FR Clearing Prices Table
-- =============================================================================
-- Stores Dynamic Containment, Dynamic Moderation, and Dynamic Regulation 
-- clearing prices per EFA block

CREATE TABLE IF NOT EXISTS `inner-cinema-476211-u9.uk_energy_prod.fr_clearing_prices` (
  efa_date DATE NOT NULL,
  efa_block INT64 NOT NULL,                         -- 1-6 (6 × 4-hour blocks per day)
  service STRING NOT NULL,                          -- 'DC', 'DM', 'DR'
  clearing_price_gbp_per_mw_h FLOAT64 NOT NULL,     -- £/MW/h
  block_start TIMESTAMP NOT NULL,
  block_end TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY efa_date
CLUSTER BY service, efa_block
OPTIONS(
  description="Frequency response clearing prices per EFA block (DC/DM/DR)",
  labels=[("source", "neso"), ("type", "pricing")]
);

-- Example data:
-- efa_date    | efa_block | service | price | block_start         | block_end
-- 2025-01-01  | 1         | 'DC'    | 2.82  | 2025-01-01 00:00:00 | 2025-01-01 04:00:00
-- 2025-01-01  | 1         | 'DM'    | 4.00  | 2025-01-01 00:00:00 | 2025-01-01 04:00:00
-- 2025-01-01  | 1         | 'DR'    | 4.45  | 2025-01-01 00:00:00 | 2025-01-01 04:00:00


-- =============================================================================
-- 2. BESS Asset Configuration Table
-- =============================================================================
-- Stores battery configuration parameters for optimization

CREATE TABLE IF NOT EXISTS `inner-cinema-476211-u9.uk_energy_prod.bess_asset_config` (
  asset_id STRING NOT NULL,
  asset_name STRING,
  p_max_mw FLOAT64 NOT NULL,                         -- Maximum power (MW)
  e_max_mwh FLOAT64 NOT NULL,                        -- Energy capacity (MWh)
  roundtrip_efficiency FLOAT64 NOT NULL,             -- 0.85 = 85%
  degradation_cost_gbp_per_mwh FLOAT64 NOT NULL,     -- £/MWh cycling cost
  fr_utilisation_factor FLOAT64 NOT NULL,            -- Fraction of full cycling FR causes (e.g. 0.1)
  min_price_threshold_gbp_per_mw_h FLOAT64,          -- Minimum price to participate
  location STRING,
  gsp_group STRING,
  dno STRING,
  commissioned_date DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
OPTIONS(
  description="BESS asset configuration for revenue optimization",
  labels=[("type", "config")]
);

-- Example row for 2.5 MW / 5 MWh battery:
-- INSERT INTO `inner-cinema-476211-u9.uk_energy_prod.bess_asset_config` VALUES (
--   'BESS_2P5MW_5MWH',
--   'Example 2.5MW Battery',
--   2.5,              -- p_max_mw
--   5.0,              -- e_max_mwh (2 hour duration)
--   0.85,             -- roundtrip_efficiency (85%)
--   5.0,              -- degradation_cost_gbp_per_mwh (£5/MWh)
--   0.1,              -- fr_utilisation_factor (10% cycling for FR)
--   1.0,              -- min_price_threshold (£1/MW/h minimum)
--   'South West',
--   '_J',
--   'NGED West Midlands',
--   '2024-01-01',
--   CURRENT_TIMESTAMP(),
--   CURRENT_TIMESTAMP()
-- );


-- =============================================================================
-- 3. BESS FR Schedule Output Table
-- =============================================================================
-- Stores optimization results - which service to provide per EFA block

CREATE TABLE IF NOT EXISTS `inner-cinema-476211-u9.uk_energy_prod.bess_fr_schedule` (
  asset_id STRING NOT NULL,
  efa_date DATE NOT NULL,
  efa_block INT64 NOT NULL,
  block_start TIMESTAMP NOT NULL,
  block_end TIMESTAMP NOT NULL,
  best_service STRING NOT NULL,                      -- 'DC', 'DM', 'DR', or 'IDLE'
  p_mw FLOAT64 NOT NULL,                             -- Power allocated (MW)
  availability_revenue_gbp FLOAT64 NOT NULL,         -- Revenue from availability payment
  degradation_cost_gbp FLOAT64 NOT NULL,             -- Cost of degradation
  net_margin_gbp FLOAT64 NOT NULL,                   -- Net profit for this block
  dc_price_gbp_per_mw_h FLOAT64,                     -- DC price this block (for reference)
  dm_price_gbp_per_mw_h FLOAT64,                     -- DM price this block
  dr_price_gbp_per_mw_h FLOAT64,                     -- DR price this block
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY efa_date
CLUSTER BY asset_id, best_service
OPTIONS(
  description="Optimized FR service schedule per BESS asset per EFA block",
  labels=[("type", "schedule"), ("source", "optimizer")]
);


-- =============================================================================
-- 4. Useful Queries
-- =============================================================================

-- Get daily revenue summary for an asset
/*
SELECT 
  efa_date,
  COUNT(*) as blocks,
  SUM(CASE WHEN best_service = 'DC' THEN 1 ELSE 0 END) as dc_blocks,
  SUM(CASE WHEN best_service = 'DM' THEN 1 ELSE 0 END) as dm_blocks,
  SUM(CASE WHEN best_service = 'DR' THEN 1 ELSE 0 END) as dr_blocks,
  SUM(CASE WHEN best_service = 'IDLE' THEN 1 ELSE 0 END) as idle_blocks,
  SUM(availability_revenue_gbp) as total_revenue,
  SUM(degradation_cost_gbp) as total_degradation,
  SUM(net_margin_gbp) as total_net_margin
FROM `inner-cinema-476211-u9.uk_energy_prod.bess_fr_schedule`
WHERE asset_id = 'BESS_2P5MW_5MWH'
  AND efa_date BETWEEN '2025-01-01' AND '2025-01-31'
GROUP BY efa_date
ORDER BY efa_date;
*/

-- Get monthly service mix and revenue
/*
SELECT 
  FORMAT_DATE('%Y-%m', efa_date) as month,
  best_service,
  COUNT(*) as blocks,
  SUM(availability_revenue_gbp) as revenue,
  SUM(net_margin_gbp) as net_margin,
  AVG(CASE 
    WHEN best_service = 'DC' THEN dc_price_gbp_per_mw_h
    WHEN best_service = 'DM' THEN dm_price_gbp_per_mw_h
    WHEN best_service = 'DR' THEN dr_price_gbp_per_mw_h
  END) as avg_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bess_fr_schedule`
WHERE asset_id = 'BESS_2P5MW_5MWH'
GROUP BY month, best_service
ORDER BY month, best_service;
*/

-- Compare actual vs if always chose DC
/*
WITH actual AS (
  SELECT 
    SUM(net_margin_gbp) as actual_margin
  FROM `inner-cinema-476211-u9.uk_energy_prod.bess_fr_schedule`
  WHERE asset_id = 'BESS_2P5MW_5MWH'
    AND efa_date BETWEEN '2025-01-01' AND '2025-01-31'
),
always_dc AS (
  SELECT 
    SUM(net_margin_gbp) as dc_only_margin
  FROM `inner-cinema-476211-u9.uk_energy_prod.bess_fr_schedule`
  WHERE asset_id = 'BESS_2P5MW_5MWH'
    AND efa_date BETWEEN '2025-01-01' AND '2025-01-31'
    AND best_service = 'DC'
)
SELECT 
  actual.actual_margin,
  always_dc.dc_only_margin,
  actual.actual_margin - always_dc.dc_only_margin as optimization_value,
  ROUND((actual.actual_margin - always_dc.dc_only_margin) / always_dc.dc_only_margin * 100, 1) as improvement_pct
FROM actual, always_dc;
*/
