-- EBOCF Hybrid View - Upgrade Revenue Coverage from 87% to 98-99%
-- Created: December 18, 2025
-- Purpose: Combine EBOCF pre-calculated cashflows (preferred) with BOD matching (fallback)
--
-- Coverage Strategy:
--   1. EBOCF first (~95% of acceptances with pre-calculated £)
--   2. BOD matching for remaining gaps (~3-4%)
--   3. Track source for transparency
--
-- Expected Result: 98-99% total coverage vs current 87% (BOD-only)

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.boalf_with_ebocf_hybrid` AS

WITH ebocf_revenue AS (
  -- Method 1: EBOCF Pre-Calculated Cashflows (PREFERRED)
  -- No MW→MWh→£ math needed, Elexon does it all
  SELECT
    ebocf.bmUnit,
    CAST(ebocf.settlementDate AS DATE) AS settlementDate,
    ebocf.settlementPeriod,
    -- Generate pseudo acceptance number from composite key
    CONCAT(
      ebocf.bmUnit, '_',
      ebocf.settlementDate, '_',
      CAST(ebocf.settlementPeriod AS STRING), '_',
      ebocf._direction
    ) AS acceptanceNumber,
    ebocf.totalCashflow AS revenue_gbp,
    -- Note: bmrs_ebocf doesn't have volume/price fields in current schema
    -- Only totalCashflow, bidOfferPairCashflows nested structure
    CAST(NULL AS FLOAT64) AS acceptanceVolume_mwh,
    CAST(NULL AS FLOAT64) AS acceptancePrice_gbp_per_mwh,
    'EBOCF' AS source,
    ebocf.bmUnitType,
    ebocf.leadPartyName,
    ebocf.nationalGridBmUnit,
    ebocf._direction AS bidOffer
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_ebocf` AS ebocf
  WHERE CAST(ebocf.settlementDate AS DATE) >= '2022-01-01'
    AND ebocf.totalCashflow IS NOT NULL
    AND ebocf.totalCashflow != 0
),

bod_revenue AS (
  -- Method 2: BOD Matching (FALLBACK for gaps)
  -- Manual MW→MWh→£ calculation using trapezoid integration
  SELECT
    boalf.bmUnit,
    CAST(boalf.settlementDate AS DATE) AS settlementDate,
    boalf.settlementPeriodFrom AS settlementPeriod,
    boalf.acceptanceNumber,
    -- Revenue = Price × Volume
    bod.offer * (
      ((boalf.levelFrom + boalf.levelTo) / 2.0) *
      (TIMESTAMP_DIFF(boalf.timeTo, boalf.timeFrom, SECOND) / 3600.0)
    ) AS revenue_gbp,
    -- Volume (MWh) = Trapezoid integration
    ((boalf.levelFrom + boalf.levelTo) / 2.0) *
    (TIMESTAMP_DIFF(boalf.timeTo, boalf.timeFrom, SECOND) / 3600.0) AS acceptanceVolume_mwh,
    -- Price (£/MWh) from BOD
    bod.offer AS acceptancePrice_gbp_per_mwh,
    'BOD' AS source,
    CAST(NULL AS STRING) AS bmUnitType,
    CAST(NULL AS STRING) AS leadPartyName,
    boalf.nationalGridBmUnit,
    'OFFER' AS bidOffer  -- Simplified: assuming offers (most common for batteries)
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` AS boalf
  INNER JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` AS bod
    ON boalf.bmUnit = bod.bmUnit
    AND boalf.timeFrom = bod.timeFrom
    AND boalf.timeTo = bod.timeTo
    AND boalf.levelFrom = bod.levelFrom
    AND boalf.levelTo = bod.levelTo
    AND boalf.pairId = bod.pairId
  WHERE boalf.settlementDate >= '2022-01-01'
    AND bod.offer IS NOT NULL
    AND bod.offer != 0
    -- Exclude records already in EBOCF (no duplicates)
    -- Match on composite key since EBOCF has no acceptanceNumber
    AND CONCAT(
      boalf.bmUnit, '_',
      CAST(CAST(boalf.settlementDate AS DATE) AS STRING), '_',
      CAST(boalf.settlementPeriodFrom AS STRING), '_',
      'offer'
    ) NOT IN (
      SELECT acceptanceNumber FROM ebocf_revenue
    )
),

combined_revenue AS (
  -- Combine both sources with EBOCF priority
  SELECT * FROM ebocf_revenue
  UNION ALL
  SELECT * FROM bod_revenue
)

-- Final output with metadata
SELECT
  bmUnit,
  settlementDate,
  settlementPeriod,
  acceptanceNumber,
  revenue_gbp,
  acceptanceVolume_mwh,
  acceptancePrice_gbp_per_mwh,
  source,
  bmUnitType,
  leadPartyName,
  nationalGridBmUnit,
  bidOffer,
  -- Add validation flag
  CASE
    WHEN revenue_gbp IS NOT NULL AND revenue_gbp > 0 THEN 'Valid'
    WHEN revenue_gbp IS NOT NULL AND revenue_gbp < 0 THEN 'Negative'
    WHEN revenue_gbp = 0 THEN 'Zero'
    ELSE 'Invalid'
  END AS validation_flag
FROM combined_revenue
WHERE revenue_gbp IS NOT NULL;

-- Usage Examples:
--
-- 1. Total VLP Revenue by Source:
-- SELECT
--   bmUnit,
--   source,
--   SUM(revenue_gbp) as total_revenue,
--   COUNT(*) as acceptance_count
-- FROM `inner-cinema-476211-u9.uk_energy_prod.boalf_with_ebocf_hybrid`
-- WHERE bmUnit IN ('T_FBPGM002', 'T_FFSEN005')
--   AND settlementDate BETWEEN '2025-10-01' AND '2025-10-31'
-- GROUP BY bmUnit, source
-- ORDER BY total_revenue DESC;
--
-- 2. Coverage Analysis:
-- SELECT
--   DATE_TRUNC(settlementDate, MONTH) as month,
--   COUNTIF(source = 'EBOCF') as ebocf_count,
--   COUNTIF(source = 'BOD') as bod_count,
--   COUNT(*) as total,
--   ROUND(100.0 * COUNTIF(source = 'EBOCF') / COUNT(*), 1) as ebocf_coverage_pct
-- FROM `inner-cinema-476211-u9.uk_energy_prod.boalf_with_ebocf_hybrid`
-- GROUP BY month
-- ORDER BY month DESC;
--
-- 3. Gap Period Revenue (Nov 5 - Dec 18):
-- SELECT
--   SUM(revenue_gbp) as total_revenue_gbp,
--   COUNT(*) as acceptance_count,
--   COUNT(DISTINCT bmUnit) as unique_units
-- FROM `inner-cinema-476211-u9.uk_energy_prod.boalf_with_ebocf_hybrid`
-- WHERE settlementDate BETWEEN '2025-11-05' AND '2025-12-18';
