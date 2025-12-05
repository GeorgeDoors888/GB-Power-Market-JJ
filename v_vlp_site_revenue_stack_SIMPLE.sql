-- VLP Revenue Stack View - SIMPLIFIED VERSION
-- Uses ONLY existing Elexon/IRIS data, no fake tables
-- Created: 5 December 2025

CREATE OR REPLACE VIEW
  `inner-cinema-476211-u9.uk_energy_prod.v_vlp_site_revenue_stack` AS

-- Base timeline from system prices
WITH base AS (
  SELECT
    settlementDate,
    settlementPeriod,
    TIMESTAMP(
      CONCAT(
        CAST(settlementDate AS STRING), " ",
        LPAD(CAST(CAST((settlementPeriod - 1) / 2 AS INT64) AS STRING), 2, "0"), ":",
        LPAD(CAST(MOD(settlementPeriod - 1, 2) * 30 AS STRING), 2, "0"), ":00"
      )
    ) AS ts_halfhour,
    systemBuyPrice AS wholesale_price_gbp_per_mwh,
    systemSellPrice AS ssp_gbp_per_mwh,  -- Same as systemBuyPrice since P305
    
    -- DUoS time bands
    CASE
      WHEN EXTRACT(DAYOFWEEK FROM settlementDate) IN (1,7) THEN 'GREEN'
      WHEN settlementPeriod BETWEEN 33 AND 39 THEN 'RED'
      WHEN settlementPeriod BETWEEN 17 AND 32 OR settlementPeriod BETWEEN 40 AND 44 THEN 'AMBER'
      ELSE 'GREEN'
    END AS duos_band
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
  WHERE settlementDate >= '2025-10-01'  -- Start from October
),

-- DUoS rates (£/MWh)
duos_rates AS (
  SELECT 'RED' AS duos_band, 17.64 AS duos_rate_gbp_per_mwh UNION ALL
  SELECT 'AMBER', 2.05 UNION ALL
  SELECT 'GREEN', 0.11
),

-- Levies (blended RO, FiT, CfD, CCL, BSUoS, TNUoS)
levies AS (
  SELECT 98.15 AS levies_gbp_per_mwh
),

-- PPA price (can make time-varying later)
ppa_price AS (
  SELECT 150.0 AS ppa_price_gbp_per_mwh
),

-- REAL BM ACCEPTANCES from bmrs_boalf for FBPGM002 battery
bm_acceptances AS (
  SELECT
    settlementDate,
    settlementPeriod,
    bmUnit,
    (levelTo - levelFrom) * 0.5 AS accepted_mwh,  -- Convert MW to MWh (30-min period)
    acceptancePrice AS price_gbp_per_mwh,
    bidOfferFlag
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
  WHERE bmUnit = '2__FBPGM002'  -- Flexgen battery with most BM activity
    AND settlementDate >= '2025-10-01'
),

-- Aggregate BM cashflows per settlement period
bm_revenue AS (
  SELECT
    settlementDate,
    settlementPeriod,
    SUM(accepted_mwh) AS bm_accepted_mwh,
    SUM(accepted_mwh * price_gbp_per_mwh) AS bm_revenue_gbp
  FROM bm_acceptances
  GROUP BY settlementDate, settlementPeriod
),

-- REAL GENERATION DATA from bmrs_indgen_iris (if available)
battery_generation AS (
  SELECT
    settlementDate,
    settlementPeriod,
    SUM(CASE WHEN generation > 0 THEN generation * 0.5 ELSE 0 END) AS gen_mwh,
    SUM(CASE WHEN generation < 0 THEN ABS(generation) * 0.5 ELSE 0 END) AS consumption_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen_iris`
  WHERE bmUnit = '2__FBPGM002'
    AND settlementDate >= '2025-10-01'
  GROUP BY settlementDate, settlementPeriod
),

-- Capacity Market (use realistic values for 2.5 MW battery)
cm_params AS (
  SELECT
    'VLP_SITE_001' AS site_id,
    15.08 AS cm_price_gbp_per_kw_year,      -- 2026/27 T-4 clearing
    2400.0 AS derated_kw,                    -- 2.4 MW de-rated
    4000.0 AS expected_annual_discharge_mwh  -- Conservative for 2.5 MW
),

cm_per_mwh AS (
  SELECT
    site_id,
    (cm_price_gbp_per_kw_year * derated_kw) / expected_annual_discharge_mwh AS cm_gbp_per_mwh
  FROM cm_params
),

-- Combine everything
combined AS (
  SELECT
    b.ts_halfhour,
    b.settlementDate,
    b.settlementPeriod,
    
    -- Prices
    b.wholesale_price_gbp_per_mwh,
    b.ssp_gbp_per_mwh,
    dr.duos_rate_gbp_per_mwh,
    lev.levies_gbp_per_mwh,
    ppa.ppa_price_gbp_per_mwh,
    
    -- Full import cost
    b.wholesale_price_gbp_per_mwh + dr.duos_rate_gbp_per_mwh + lev.levies_gbp_per_mwh AS import_cost_gbp_per_mwh,
    
    -- BM data (REAL)
    COALESCE(bm.bm_accepted_mwh, 0) AS bm_accepted_mwh,
    COALESCE(bm.bm_revenue_gbp, 0) AS bm_revenue_gbp,
    
    -- Generation data (REAL if available)
    COALESCE(gen.gen_mwh, 0) AS battery_generation_mwh,
    COALESCE(gen.consumption_mwh, 0) AS battery_consumption_mwh,
    
    -- CM rate
    COALESCE(cm.cm_gbp_per_mwh, 9.04) AS cm_gbp_per_mwh  -- £9.04/MWh default
    
  FROM base b
  LEFT JOIN duos_rates dr ON b.duos_band = dr.duos_band
  CROSS JOIN levies lev
  CROSS JOIN ppa_price ppa
  LEFT JOIN bm_revenue bm USING (settlementDate, settlementPeriod)
  LEFT JOIN battery_generation gen USING (settlementDate, settlementPeriod)
  CROSS JOIN cm_per_mwh cm
)

SELECT
  *,
  
  -- Revenue streams (per settlement period)
  bm_revenue_gbp AS r_bm_gbp,
  
  -- ESO services (placeholder - can add when you have contracts)
  0.0 AS r_eso_gbp,
  
  -- CM revenue (apply to discharge MWh)
  cm_gbp_per_mwh * GREATEST(battery_generation_mwh, bm_accepted_mwh) AS r_cm_gbp,
  
  -- PPA export revenue (on generation)
  ppa_price_gbp_per_mwh * GREATEST(battery_generation_mwh, bm_accepted_mwh) AS r_ppa_gbp,
  
  -- Avoided import (generation displaces grid import)
  import_cost_gbp_per_mwh * GREATEST(battery_generation_mwh, bm_accepted_mwh) AS r_avoided_import_gbp,
  
  -- DSO flex (placeholder)
  0.0 AS r_dso_gbp,
  
  -- Costs
  import_cost_gbp_per_mwh * battery_consumption_mwh AS battery_import_cost_gbp,
  0.0 AS chp_fuel_cost_gbp  -- No CHP for now
  
FROM combined
ORDER BY ts_halfhour
