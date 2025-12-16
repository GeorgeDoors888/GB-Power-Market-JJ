-- ============================================================================
-- BOALF Analysis Views and Tables
-- ============================================================================
-- Purpose: Create production-ready views for battery arbitrage analysis
--          and audit compliance using derived BOALF acceptance prices
--
-- Dependencies: bmrs_boalf_complete table (created by derive_boalf_prices.py)
--
-- Views:
--   1. boalf_with_prices       - Filtered to Valid records only, analysis-ready
--   2. boalf_outliers_excluded - Audit table for regulatory compliance
--
-- Usage:
--   bq query --project_id=inner-cinema-476211-u9 < create_boalf_analysis_views.sql
-- ============================================================================

-- ============================================================================
-- 1. Analysis View: Valid Acceptance Prices Only
-- ============================================================================
-- Filters to validation_flag='Valid' records per Elexon B1610 Section 4.3
-- Adds computed fields for revenue analysis and unit categorization
-- ============================================================================

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.boalf_with_prices` AS
WITH valid_acceptances AS (
  SELECT 
    -- Primary keys
    acceptanceNumber,
    acceptanceTime,
    bmUnit,
    settlementDate,
    settlementPeriod,
    
    -- Time periods
    timeFrom,
    timeTo,
    
    -- Levels (MW)
    levelFrom,
    levelTo,
    
    -- Derived price fields
    acceptancePrice,      -- £/MWh from BOD matching
    acceptanceVolume,     -- MWh (ABS of level change)
    acceptanceType,       -- BID | OFFER | UNKNOWN
    
    -- Metadata flags
    soFlag,               -- System Operator flag
    storFlag,             -- STOR flag
    rrFlag,               -- Replacement Reserve flag
    deemedBoFlag,         -- Deemed Bid-Offer flag
    
    -- Source tracking
    _price_source,        -- BOD_MATCH | BOD_REALTIME | UNMATCHED
    _matched_pairId,      -- BOD pairId used for matching
    _ingested_utc         -- Upload timestamp
    
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
  WHERE validation_flag = 'Valid'  -- Elexon B1610 compliant only
),

enriched AS (
  SELECT 
    *,
    
    -- Revenue estimate (£) = Price (£/MWh) × Volume (MWh)
    ROUND(acceptancePrice * acceptanceVolume, 2) AS revenue_estimate_gbp,
    
    -- Unit categorization for analysis
    CASE
      -- VLP Battery units (primary analysis targets)
      WHEN bmUnit LIKE 'F%M%' AND bmUnit IN (
        'FBPGM002',  -- Flexgen Battery
        'FFSEN005',  -- Gresham House / Harmony Energy
        'FSSEN001',  -- Statkraft Staunch (assumed)
        'FBRGM003'   -- Broombank (assumed)
      ) THEN 'VLP_Battery'
      
      -- Transmission-connected generation
      WHEN bmUnit LIKE 'T_%' THEN 'Transmission_Generation'
      
      -- Interconnectors
      WHEN bmUnit IN ('E_ELEC', 'E_IFA', 'E_IFA2', 'E_NEMO', 'E_NRWL', 'E_MOYL', 'E_NSL') 
        THEN 'Interconnector'
      
      -- Embedded generation (distribution-connected)
      WHEN bmUnit LIKE 'E_%' THEN 'Embedded_Generation'
      
      -- Demand (negative generation)
      WHEN bmUnit LIKE 'D_%' THEN 'Demand'
      
      ELSE 'Other'
    END AS unit_category,
    
    -- Settlement period hour (0-23) for time-of-day analysis
    FLOOR((settlementPeriod - 1) / 2) AS settlement_hour,
    
    -- Date components for aggregation
    DATE(settlementDate) AS settlement_date,
    EXTRACT(YEAR FROM settlementDate) AS year,
    EXTRACT(MONTH FROM settlementDate) AS month,
    EXTRACT(DAYOFWEEK FROM settlementDate) AS day_of_week,  -- 1=Sunday, 7=Saturday
    
    -- Peak vs Off-peak classification (DUoS Red band proxy)
    CASE
      WHEN EXTRACT(DAYOFWEEK FROM settlementDate) IN (1, 7) THEN 'Weekend'  -- Sunday or Saturday
      WHEN FLOOR((settlementPeriod - 1) / 2) BETWEEN 16 AND 19 THEN 'Peak'  -- 16:00-20:00 weekdays
      WHEN FLOOR((settlementPeriod - 1) / 2) BETWEEN 8 AND 15 THEN 'Shoulder'  -- 08:00-16:00 weekdays
      ELSE 'Off_Peak'  -- 00:00-08:00, 20:00-00:00 weekdays
    END AS time_band
    
  FROM valid_acceptances
)

SELECT * FROM enriched
ORDER BY settlementDate, settlementPeriod, acceptanceNumber;


-- ============================================================================
-- 2. Audit Table: Excluded Acceptances
-- ============================================================================
-- Stores all acceptances filtered out by Elexon B1610 validation rules
-- Required for regulatory compliance and audit trail
-- ============================================================================

CREATE OR REPLACE TABLE `inner-cinema-476211-u9.uk_energy_prod.boalf_outliers_excluded` 
PARTITION BY DATE(settlementDate)
CLUSTER BY validation_flag, bmUnit
AS
SELECT 
  -- Primary keys
  acceptanceNumber,
  acceptanceTime,
  bmUnit,
  settlementDate,
  settlementPeriod,
  
  -- Original levels and derived fields
  levelFrom,
  levelTo,
  acceptancePrice,
  acceptanceVolume,
  acceptanceType,
  
  -- Validation status (WHY excluded)
  validation_flag,  -- Price_Outlier | SO_Test | Low_Volume | Unmatched
  
  -- Detailed exclusion reason
  CASE validation_flag
    WHEN 'Price_Outlier' THEN CONCAT(
      'Acceptance price (£', 
      ROUND(acceptancePrice, 2), 
      '/MWh) exceeds Elexon B1610 ±£1,000/MWh threshold'
    )
    WHEN 'SO_Test' THEN CONCAT(
      'System Operator test/system record (soFlag=',
      CAST(soFlag AS STRING),
      ') per Elexon B1610 Section 4.3 exclusion criteria'
    )
    WHEN 'Low_Volume' THEN CONCAT(
      'Acceptance volume (',
      ROUND(acceptanceVolume, 4),
      ' MWh) below 0.001 MWh regulatory threshold'
    )
    WHEN 'Unmatched' THEN 
      'No matching BOD submission found (bmUnit + settlementDate + period)'
    ELSE 'Unknown exclusion reason'
  END AS exclusion_reason,
  
  -- Metadata flags
  soFlag,
  storFlag,
  rrFlag,
  deemedBoFlag,
  
  -- Source tracking
  _price_source,
  _matched_pairId,
  _ingested_utc,
  
  -- Audit timestamp
  CURRENT_TIMESTAMP() AS _excluded_at
  
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
WHERE validation_flag != 'Valid'  -- All non-valid records
ORDER BY settlementDate, settlementPeriod, validation_flag;


-- ============================================================================
-- Usage Examples
-- ============================================================================

-- Example 1: Battery arbitrage revenue for October 2025
-- SELECT 
--   bmUnit,
--   COUNT(*) AS num_offers,
--   ROUND(AVG(acceptancePrice), 2) AS avg_offer_price,
--   ROUND(SUM(revenue_estimate_gbp), 2) AS total_revenue_gbp
-- FROM `inner-cinema-476211-u9.uk_energy_prod.boalf_with_prices`
-- WHERE unit_category = 'VLP_Battery'
--   AND acceptanceType = 'OFFER'
--   AND DATE(settlementDate) BETWEEN '2025-10-01' AND '2025-10-31'
-- GROUP BY bmUnit
-- ORDER BY total_revenue_gbp DESC;

-- Example 2: Peak vs Off-peak price comparison
-- SELECT 
--   time_band,
--   COUNT(*) AS num_acceptances,
--   ROUND(AVG(acceptancePrice), 2) AS avg_price,
--   ROUND(MIN(acceptancePrice), 2) AS min_price,
--   ROUND(MAX(acceptancePrice), 2) AS max_price
-- FROM `inner-cinema-476211-u9.uk_energy_prod.boalf_with_prices`
-- WHERE acceptanceType = 'OFFER'
--   AND DATE(settlementDate) BETWEEN '2025-10-17' AND '2025-10-23'
-- GROUP BY time_band
-- ORDER BY avg_price DESC;

-- Example 3: Validation flag audit summary
-- SELECT 
--   validation_flag,
--   COUNT(*) AS num_records,
--   ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage,
--   COUNT(DISTINCT bmUnit) AS num_units,
--   ROUND(MIN(acceptancePrice), 2) AS min_price,
--   ROUND(MAX(acceptancePrice), 2) AS max_price
-- FROM `inner-cinema-476211-u9.uk_energy_prod.boalf_outliers_excluded`
-- WHERE DATE(settlementDate) BETWEEN '2025-10-01' AND '2025-10-31'
-- GROUP BY validation_flag
-- ORDER BY num_records DESC;

-- ============================================================================
-- Grant Permissions (if needed)
-- ============================================================================
-- GRANT `roles/bigquery.dataViewer` ON TABLE 
--   `inner-cinema-476211-u9.uk_energy_prod.boalf_with_prices` 
--   TO 'user:your-email@domain.com';
-- 
-- GRANT `roles/bigquery.dataViewer` ON TABLE 
--   `inner-cinema-476211-u9.uk_energy_prod.boalf_outliers_excluded` 
--   TO 'user:compliance-team@domain.com';
