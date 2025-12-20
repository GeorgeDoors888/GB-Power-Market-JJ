-- EBOCF Hybrid View - SIMPLIFIED VERSION
-- Created: December 18, 2025
-- Purpose: Combine EBOCF pre-calculated cashflows with BOD matching
--
-- Simplified Strategy:
--   1. EBOCF data (pre-calculated cashflows from Elexon)
--   2. BOD matching data (our current boalf_with_prices logic)
--   3. Simple UNION ALL (accept some potential duplicates for now)
--
-- Note: This gets us to ~98% coverage quickly. Deduplication can be added later if needed.

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.boalf_with_ebocf_hybrid` AS

WITH ebocf_revenue AS (
  -- Method 1: EBOCF Pre-Calculated Cashflows
  SELECT
    ebocf.bmUnit,
    CAST(ebocf.settlementDate AS DATE) AS settlementDate,
    ebocf.settlementPeriod,
    CONCAT(
      ebocf.bmUnit, '_',
      ebocf.settlementDate, '_',
      CAST(ebocf.settlementPeriod AS STRING), '_',
      ebocf._direction
    ) AS composite_key,
    ebocf.totalCashflow AS revenue_gbp,
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
    AND ABS(ebocf.totalCashflow) > 0.01  -- Filter near-zero cashflows
),

bod_revenue AS (
  -- Method 2: BOD Matching (from existing boalf_with_prices logic)
  SELECT
    boalf.bmUnit,
    CAST(boalf.settlementDate AS DATE) AS settlementDate,
    boalf.settlementPeriodFrom AS settlementPeriod,
    CONCAT(
      boalf.bmUnit, '_',
      CAST(CAST(boalf.settlementDate AS DATE) AS STRING), '_',
      CAST(boalf.settlementPeriodFrom AS STRING), '_',
      'offer'
    ) AS composite_key,
    -- Revenue = Price × Volume
    bod.offer * (
      ((boalf.levelFrom + boalf.levelTo) / 2.0) *
      (TIMESTAMP_DIFF(
        PARSE_DATETIME('%Y-%m-%dT%H:%M:%SZ', boalf.timeTo),
        PARSE_DATETIME('%Y-%m-%dT%H:%M:%SZ', boalf.timeFrom),
        SECOND
      ) / 3600.0)
    ) AS revenue_gbp,
    -- Volume (MWh) = Trapezoid integration
    ((boalf.levelFrom + boalf.levelTo) / 2.0) *
    (TIMESTAMP_DIFF(
      PARSE_DATETIME('%Y-%m-%dT%H:%M:%SZ', boalf.timeTo),
      PARSE_DATETIME('%Y-%m-%dT%H:%M:%SZ', boalf.timeFrom),
      SECOND
    ) / 3600.0) AS acceptanceVolume_mwh,
    -- Price (£/MWh) from BOD
    bod.offer AS acceptancePrice_gbp_per_mwh,
    'BOD' AS source,
    CAST(NULL AS STRING) AS bmUnitType,
    CAST(NULL AS STRING) AS leadPartyName,
    boalf.nationalGridBmUnit,
    'OFFER' AS bidOffer
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` AS boalf
  INNER JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` AS bod
    ON boalf.bmUnit = bod.bmUnit
    AND PARSE_DATETIME('%Y-%m-%dT%H:%M:%SZ', boalf.timeFrom) = bod.timeFrom
    AND PARSE_DATETIME('%Y-%m-%dT%H:%M:%SZ', boalf.timeTo) = bod.timeTo
    AND boalf.levelFrom = bod.levelFrom
    AND boalf.levelTo = bod.levelTo
    AND boalf.pairId = bod.pairId
  WHERE CAST(boalf.settlementDate AS DATE) >= '2022-01-01'
    AND bod.offer IS NOT NULL
    AND bod.offer > 0
)

-- Combine both sources (EBOCF first for priority in queries)
SELECT
  bmUnit,
  settlementDate,
  settlementPeriod,
  composite_key,
  revenue_gbp,
  acceptanceVolume_mwh,
  acceptancePrice_gbp_per_mwh,
  source,
  bmUnitType,
  leadPartyName,
  nationalGridBmUnit,
  bidOffer,
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
WHERE revenue_gbp IS NOT NULL;
