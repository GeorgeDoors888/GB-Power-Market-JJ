-- Simplified VLP View - REAL DATA ONLY
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.v_vlp_revenue_simple` AS

SELECT
  c.settlementDate,
  c.settlementPeriod,
  c.systemBuyPrice AS wholesale_price,
  c.systemSellPrice AS ssp_price,
  
  -- DUoS band
  CASE
    WHEN EXTRACT(DAYOFWEEK FROM c.settlementDate) IN (1,7) THEN 'GREEN'
    WHEN c.settlementPeriod BETWEEN 33 AND 39 THEN 'RED'
    WHEN c.settlementPeriod BETWEEN 17 AND 32 OR c.settlementPeriod BETWEEN 40 AND 44 THEN 'AMBER'
    ELSE 'GREEN'
  END AS duos_band,
  
  -- DUoS rate
  CASE
    WHEN EXTRACT(DAYOFWEEK FROM c.settlementDate) IN (1,7) THEN 0.11
    WHEN c.settlementPeriod BETWEEN 33 AND 39 THEN 17.64
    WHEN c.settlementPeriod BETWEEN 17 AND 32 OR c.settlementPeriod BETWEEN 40 AND 44 THEN 2.05
    ELSE 0.11
  END AS duos_rate,
  
  -- Import cost
  c.systemBuyPrice + 
  CASE
    WHEN EXTRACT(DAYOFWEEK FROM c.settlementDate) IN (1,7) THEN 0.11
    WHEN c.settlementPeriod BETWEEN 33 AND 39 THEN 17.64
    WHEN c.settlementPeriod BETWEEN 17 AND 32 OR c.settlementPeriod BETWEEN 40 AND 44 THEN 2.05
    ELSE 0.11
  END + 98.15 AS import_cost,
  
  -- BM revenue (REAL from bmrs_boalf)
  COALESCE(bm.bm_accepted_mwh, 0) AS bm_accepted_mwh,
  COALESCE(bm.bm_revenue_gbp, 0) AS bm_revenue_gbp,
  
  -- Generation (REAL from bmrs_indgen_iris)
  COALESCE(gen.generation_mwh, 0) AS generation_mwh,
  
  -- Revenue streams
  COALESCE(bm.bm_revenue_gbp, 0) AS r_bm_gbp,
  9.04 * GREATEST(COALESCE(bm.bm_accepted_mwh, 0), COALESCE(gen.generation_mwh, 0)) AS r_cm_gbp,
  150.0 * GREATEST(COALESCE(bm.bm_accepted_mwh, 0), COALESCE(gen.generation_mwh, 0)) AS r_ppa_gbp
  
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs` c

-- BM acceptances (aggregated)
LEFT JOIN (
  SELECT
    settlementDate,
    settlementPeriod,
    SUM((levelTo - levelFrom) * 0.5) AS bm_accepted_mwh,
    SUM((levelTo - levelFrom) * 0.5 * acceptancePrice) AS bm_revenue_gbp
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
  WHERE bmUnit = '2__FBPGM002'
  GROUP BY settlementDate, settlementPeriod
) bm USING (settlementDate, settlementPeriod)

-- Generation (aggregated)
LEFT JOIN (
  SELECT
    settlementDate,
    settlementPeriod,
    SUM(generation * 0.5) AS generation_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen_iris`
  WHERE bmUnit = '2__FBPGM002'
  GROUP BY settlementDate, settlementPeriod
) gen USING (settlementDate, settlementPeriod)

WHERE c.settlementDate >= '2025-10-01'
ORDER BY c.settlementDate, c.settlementPeriod
