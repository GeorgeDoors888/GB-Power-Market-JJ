-- v_btm_bess_inputs: SIMPLIFIED view for BTM BESS greedy vs optimized dispatch
-- Uses bmrs_mid for market index price (simplified SSP/SBP proxy)

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs` AS

WITH system_prices AS (
  -- Get market prices from bmrs_mid (MID = Market Index Data)
  -- Use price as proxy for both SSP (charge) and SBP (discharge)
  SELECT
    TIMESTAMP_ADD(
      CAST(settlementDate AS TIMESTAMP),
      INTERVAL (settlementPeriod - 1) * 30 MINUTE
    ) AS ts_halfhour,
    price AS ssp,  -- Use market price as SSP proxy
    price * 0.95 AS sbp,  -- SBP typically 5% lower
    volume AS imbalance_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 60 DAY)  -- Use 60 days for older data
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
