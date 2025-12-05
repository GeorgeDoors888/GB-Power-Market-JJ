-- MINIMAL VLP VIEW - Uses only bmrs_boalf + bmrs_costs (REAL data)
-- Battery: 2__FBPGM002 (Flexgen with 1,609 BM acceptances in Oct 17-23)

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.v_vlp_revenue_minimal` AS

WITH bm_agg AS (
  -- Aggregate BM acceptances per settlement period
  SELECT
    CAST(settlementDate AS DATE) AS settlementDate,
    settlementPeriodFrom AS settlementPeriod,
    SUM((levelTo - levelFrom) * 0.5) AS bm_mwh,  -- Convert MW to MWh  
    SUM((levelTo - levelFrom) * 0.5 * CAST(SPLIT(bmUnit, '__')[OFFSET(1)] AS FLOAT64)) AS bm_revenue  -- Placeholder: need actual acceptancePrice
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
  WHERE bmUnit = '2__FBPGM002'
    AND CAST(settlementDate AS DATE) >= '2025-10-01'
  GROUP BY settlementDate, settlementPeriod
)

SELECT
  c.settlementDate,
  c.settlementPeriod,
  c.systemBuyPrice AS wholesale_price,
  
  -- DUoS bands and rates
  CASE
    WHEN EXTRACT(DAYOFWEEK FROM c.settlementDate) IN (1,7) THEN 'GREEN'
    WHEN c.settlementPeriod BETWEEN 33 AND 39 THEN 'RED'
    WHEN c.settlementPeriod BETWEEN 17 AND 44 THEN 'AMBER'
    ELSE 'GREEN'
  END AS duos_band,
  
  CASE
    WHEN EXTRACT(DAYOFWEEK FROM c.settlementDate) IN (1,7) THEN 0.11
    WHEN c.settlementPeriod BETWEEN 33 AND 39 THEN 17.64
    WHEN c.settlementPeriod BETWEEN 17 AND 44 THEN 2.05
    ELSE 0.11
  END AS duos_rate,
  
  -- Full import cost (wholesale + DUoS + levies)
  c.systemBuyPrice + 
  CASE
    WHEN EXTRACT(DAYOFWEEK FROM c.settlementDate) IN (1,7) THEN 0.11
    WHEN c.settlementPeriod BETWEEN 33 AND 39 THEN 17.64
    WHEN c.settlementPeriod BETWEEN 17 AND 44 THEN 2.05
    ELSE 0.11
  END + 98.15 AS import_cost,
  
  -- BM data (REAL)
  COALESCE(bm.bm_mwh, 0) AS bm_accepted_mwh,
  COALESCE(bm.bm_revenue, 0) AS bm_revenue_gbp,
  
  -- Revenue streams
  COALESCE(bm.bm_revenue, 0) AS r_bm_gbp,
  9.04 * ABS(COALESCE(bm.bm_mwh, 0)) AS r_cm_gbp,  -- CM: £9.04/MWh
  150.0 * ABS(COALESCE(bm.bm_mwh, 0)) AS r_ppa_gbp,  -- PPA export
  (c.systemBuyPrice + 98.15) * ABS(COALESCE(bm.bm_mwh, 0)) AS r_avoided_import_gbp,  -- Avoided import value
  0.0 AS r_eso_gbp,  -- Placeholder for ESO services
  0.0 AS r_dso_gbp   -- Placeholder for DSO flex
  
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs` c
LEFT JOIN bm_agg bm USING (settlementDate, settlementPeriod)
WHERE c.settlementDate >= '2025-10-01'
ORDER BY c.settlementDate, c.settlementPeriod
