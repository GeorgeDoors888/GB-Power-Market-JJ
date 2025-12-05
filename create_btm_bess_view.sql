-- v_btm_bess_inputs: CORRECTED view for BTM BESS greedy vs optimized dispatch
-- Uses bmrs_costs for REAL systemSellPrice/systemBuyPrice (NOT bmrs_mid!)

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs` AS

WITH system_prices AS (
  -- Get REAL system prices from bmrs_costs (SSP/SBP imbalance pricing)
  -- NOTE: bmrs_costs has data through Oct 28, 2025 only (38-day gap to present)
  SELECT
    TIMESTAMP_ADD(
      CAST(settlementDate AS TIMESTAMP),
      INTERVAL (settlementPeriod - 1) * 30 MINUTE
    ) AS ts_halfhour,
    systemSellPrice AS ssp,  -- REAL SSP (charge price when system short)
    systemBuyPrice AS sbp,   -- REAL SBP (discharge price when system long)
    netImbalanceVolume AS imbalance_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
  WHERE settlementDate >= DATE_SUB(DATE('2025-10-28'), INTERVAL 90 DAY)  -- Last 90 days of available data
    AND settlementDate <= '2025-10-28'  -- Data cutoff date
    AND systemSellPrice IS NOT NULL
    AND systemBuyPrice IS NOT NULL
),

duos_bands AS (
  -- Fixed DUoS rates for UKPN-EPN HV
  SELECT 'Red' AS time_band, 4.837 AS duos_gbp_per_mwh
  UNION ALL SELECT 'Amber', 0.457
  UNION ALL SELECT 'Green', 0.038
),

levies AS (
  -- Fixed levies (CCL, RO, FiT, BSUoS etc) - assumed £15/MWh total
  SELECT
    ts_halfhour,
    15.0 AS levies_per_mwh
  FROM UNNEST(GENERATE_TIMESTAMP_ARRAY(
    TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 DAY),
    CURRENT_TIMESTAMP(),
    INTERVAL 30 MINUTE
  )) AS ts_halfhour
),

ppa_prices AS (
  -- PPA offtake price (example: £60/MWh fixed)
  SELECT
    ts_halfhour,
    60.0 AS ppa_price
  FROM UNNEST(GENERATE_TIMESTAMP_ARRAY(
    TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 DAY),
    CURRENT_TIMESTAMP(),
    INTERVAL 30 MINUTE
  )) AS ts_halfhour
)

-- Combine all streams
SELECT
  sp.ts_halfhour,
  sp.ssp,
  sp.sbp,
  sp.imbalance_mwh,
  
  -- Charging cost = SSP + DUoS + levies
  sp.ssp AS ssp_charge,
  4.837 AS duos_charge,  -- Use Red rate (worst case)
  COALESCE(lev.levies_per_mwh, 0) AS levies_per_mwh,
  
  -- Revenue streams (simplified estimates)
  COALESCE(ppa.ppa_price, 0) AS ppa_price,
  10.0 AS bm_revenue_per_mwh,  -- Estimated BM revenue
  10.0 AS dc_revenue_per_mwh,  -- Estimated DC revenue
  5.0 AS cm_revenue_per_mwh,   -- Estimated CM revenue
  0.0 AS other_revenue_per_mwh

FROM system_prices sp
LEFT JOIN levies lev USING (ts_halfhour)
LEFT JOIN ppa_prices ppa USING (ts_halfhour)

WHERE sp.ts_halfhour >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 60 DAY)
ORDER BY sp.ts_halfhour;
