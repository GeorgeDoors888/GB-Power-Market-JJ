-- EBOCF Hybrid View - Using Existing boalf_with_prices
-- Created: December 18, 2025
-- Purpose: Combine EBOCF pre-calculated cashflows with existing BOD-matched data
--
-- Strategy:
--   1. EBOCF data (pre-calculated cashflows from Elexon)
--   2. Existing boalf_with_prices data (already has BOD matching done)
--   3. Simple UNION ALL for maximum coverage
--
-- Expected: ~98-99% coverage (EBOCF ~95% + BOD ~87% with overlap)

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.boalf_with_ebocf_hybrid` AS

WITH ebocf_revenue AS (
  -- Method 1: EBOCF Pre-Calculated Cashflows
  SELECT
    ebocf.bmUnit,
    CAST(ebocf.settlementDate AS DATE) AS settlementDate,
    ebocf.settlementPeriod,
    ebocf.totalCashflow AS revenue_gbp,
    CAST(NULL AS FLOAT64) AS acceptanceVolume_mwh,
    CAST(NULL AS FLOAT64) AS acceptancePrice_gbp_per_mwh,
    'EBOCF' AS source,
    ebocf.bmUnitType,
    ebocf.leadPartyName,
    ebocf.nationalGridBmUnit,
    ebocf._direction AS acceptanceType
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf` AS ebocf
  WHERE CAST(ebocf.settlementDate AS DATE) >= '2022-01-01'
    AND ebocf.totalCashflow IS NOT NULL
    AND ABS(ebocf.totalCashflow) > 0.01  -- Filter near-zero cashflows
),

bod_revenue AS (
  -- Method 2: BOD Matching (from existing boalf_with_prices)
  SELECT
    bmUnit,
    settlement_date AS settlementDate,
    settlementPeriod,
    revenue_estimate_gbp AS revenue_gbp,
    acceptanceVolume AS acceptanceVolume_mwh,
    acceptancePrice AS acceptancePrice_gbp_per_mwh,
    'BOD' AS source,
    CAST(NULL AS STRING) AS bmUnitType,
    CAST(NULL AS STRING) AS leadPartyName,
    CAST(NULL AS STRING) AS nationalGridBmUnit,
    acceptanceType
  FROM `inner-cinema-476211-u9.uk_energy_prod.boalf_with_prices`
  WHERE settlement_date >= '2022-01-01'
    AND revenue_estimate_gbp IS NOT NULL
    AND revenue_estimate_gbp > 0
)

-- Combine both sources (EBOCF first for priority in queries)
SELECT
  bmUnit,
  settlementDate,
  settlementPeriod,
  revenue_gbp,
  acceptanceVolume_mwh,
  acceptancePrice_gbp_per_mwh,
  source,
  bmUnitType,
  leadPartyName,
  nationalGridBmUnit,
  acceptanceType,
  CASE
    WHEN revenue_gbp IS NOT NULL AND revenue_gbp > 0 THEN 'Valid'
    WHEN revenue_gbp IS NOT NULL AND revenue_gbp < 0 THEN 'Negative'
    WHEN revenue_gbp = 0 THEN 'Zero'
    ELSE 'Invalid'
  END AS validation_flag
FROM (
  SELECT * FROM ebocf_revenue
  UNION ALL
  SELECT * FROM bod_revenue
)
WHERE revenue_gbp IS NOT NULL
ORDER BY settlementDate DESC, settlementPeriod DESC;
