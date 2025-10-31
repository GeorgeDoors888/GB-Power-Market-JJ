-- ============================================================
-- UNIFIED SCHEMA VIEWS - Bridge Old & New Data Sources
-- ============================================================
-- 
-- Purpose: Create views that unify:
--   1. Historic data (old BMRS API schema)
--   2. Real-time data (new IRIS/Insights API schema)
--
-- Strategy: Create separate tables for IRIS data, then create
--           views that UNION both sources with column mapping
-- ============================================================

-- ============================================================
-- EXAMPLE: bmrs_boalf (Bid-Offer Acceptances)
-- ============================================================

-- Step 1: Create new table for IRIS data
CREATE TABLE IF NOT EXISTS `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris` (
  -- IRIS/Insights API Schema
  dataset STRING,
  settlementDate DATE,
  settlementPeriodFrom INT64,
  settlementPeriodTo INT64,
  timeFrom TIMESTAMP,  -- Note: TIMESTAMP (not DATETIME) to handle ISO 8601
  timeTo TIMESTAMP,
  levelFrom INT64,
  levelTo INT64,
  acceptanceNumber INT64,
  acceptanceTime TIMESTAMP,
  deemedBoFlag BOOLEAN,
  soFlag BOOLEAN,
  amendmentFlag STRING,
  storFlag BOOLEAN,
  rrFlag BOOLEAN,
  nationalGridBmUnit STRING,
  bmUnit STRING,
  -- Metadata
  ingested_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  source STRING DEFAULT 'IRIS'
);

-- Step 2: Create unified view
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_unified` AS
-- Historic data (old schema)
SELECT
  dataset,
  settlementDate,
  settlementPeriod AS settlementPeriodFrom,
  settlementPeriod AS settlementPeriodTo,
  timeFrom,
  timeTo,
  levelFrom,
  levelTo,
  acceptanceNumber,
  acceptanceTime,
  deemedBoFlag,
  soFlag,
  amendmentFlag,
  storFlag,
  rrFlag,
  nationalGridBmUnit,
  bmUnit,
  ingested_utc,
  'HISTORIC' AS source
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`

UNION ALL

-- Real-time IRIS data (new schema)
SELECT
  dataset,
  settlementDate,
  settlementPeriodFrom,
  settlementPeriodTo,
  timeFrom,
  timeTo,
  levelFrom,
  levelTo,
  acceptanceNumber,
  acceptanceTime,
  deemedBoFlag,
  soFlag,
  amendmentFlag,
  storFlag,
  rrFlag,
  nationalGridBmUnit,
  bmUnit,
  ingested_utc,
  source
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`;

-- ============================================================
-- EXAMPLE: bmrs_mils (Maximum Import Limits)
-- ============================================================

-- Step 1: Create new table for IRIS data
CREATE TABLE IF NOT EXISTS `inner-cinema-476211-u9.uk_energy_prod.bmrs_mils_iris` (
  dataset STRING,
  settlementDate DATE,
  settlementPeriod INT64,
  bmUnit STRING,
  maximumImportLimit INT64,
  publishTime TIMESTAMP,
  -- Metadata
  ingested_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  source STRING DEFAULT 'IRIS'
);

-- Step 2: Create unified view
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.bmrs_mils_unified` AS
-- Historic data
SELECT
  dataset,
  settlementDate,
  settlementPeriod,
  bmUnit,
  maximumImportLimit,
  CAST(ingested_utc AS TIMESTAMP) AS publishTime,  -- Map ingested_utc to publishTime
  ingested_utc,
  'HISTORIC' AS source
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mils`

UNION ALL

-- Real-time IRIS data
SELECT
  dataset,
  settlementDate,
  settlementPeriod,
  bmUnit,
  maximumImportLimit,
  publishTime,
  ingested_utc,
  source
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mils_iris`;

-- ============================================================
-- EXAMPLE: bmrs_freq (Frequency)
-- ============================================================

-- Step 1: Create new table for IRIS data
CREATE TABLE IF NOT EXISTS `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris` (
  dataset STRING,
  spotTime TIMESTAMP,      -- Note: Different from historic!
  frequency FLOAT64,
  publishTime TIMESTAMP,
  -- Metadata
  ingested_utc TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  source STRING DEFAULT 'IRIS'
);

-- Step 2: Create unified view
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_unified` AS
-- Historic data (old schema uses reportSnapshotTime)
SELECT
  dataset,
  reportSnapshotTime AS spotTime,
  frequency,
  CAST(ingested_utc AS TIMESTAMP) AS publishTime,
  ingested_utc,
  'HISTORIC' AS source
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`

UNION ALL

-- Real-time IRIS data
SELECT
  dataset,
  spotTime,
  frequency,
  publishTime,
  ingested_utc,
  source
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`;

-- ============================================================
-- QUERY EXAMPLES - How to Use Unified Views
-- ============================================================

-- Example 1: Get latest BOALF acceptances (both sources)
SELECT
  settlementDate,
  settlementPeriodFrom,
  bmUnit,
  acceptanceTime,
  source
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_unified`
WHERE settlementDate >= CURRENT_DATE() - 7
ORDER BY acceptanceTime DESC
LIMIT 100;

-- Example 2: Compare historic vs real-time frequency
SELECT
  DATE(spotTime) as date,
  source,
  AVG(frequency) as avg_freq,
  MIN(frequency) as min_freq,
  MAX(frequency) as max_freq,
  COUNT(*) as measurements
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_unified`
WHERE spotTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
GROUP BY date, source
ORDER BY date DESC;

-- Example 3: Check data overlap/gaps
SELECT
  settlementDate,
  source,
  COUNT(*) as records
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mils_unified`
WHERE settlementDate >= CURRENT_DATE() - 30
GROUP BY settlementDate, source
ORDER BY settlementDate DESC, source;

-- ============================================================
-- MIGRATION STRATEGY
-- ============================================================

-- Phase 1: TESTING (Current)
-- 1. Create *_iris tables for IRIS real-time data
-- 2. Create *_unified views for queries
-- 3. Test with small amounts of IRIS data
-- 4. Validate queries work across both sources

-- Phase 2: TRANSITION
-- 1. Update dashboard to use *_unified views
-- 2. Update all queries to use unified views
-- 3. Monitor data quality from both sources
-- 4. Identify and fix any gaps/overlaps

-- Phase 3: OPTIMIZATION
-- 1. Deduplicate overlapping data
-- 2. Archive very old historic data
-- 3. Consider materialized views for performance
-- 4. Add partitioning/clustering

-- Phase 4: CLEANUP (Future)
-- 1. Once confident, may merge tables
-- 2. Or keep separate for clear data lineage
-- 3. Archive original tables

-- ============================================================
-- BENEFITS OF THIS APPROACH
-- ============================================================

-- ✅ No data loss - both sources preserved
-- ✅ Clear separation - easy to identify source
-- ✅ Query compatibility - views handle mapping
-- ✅ Incremental migration - test before full switch
-- ✅ Rollback possible - keep original tables
-- ✅ Performance - queries only touch needed data
-- ✅ Schema evolution - each source can evolve independently

-- ============================================================
-- NOTES
-- ============================================================

-- 1. Column Mapping:
--    - Old: settlementPeriod → New: settlementPeriodFrom/To
--    - Old: DATETIME → New: TIMESTAMP (for ISO 8601 support)
--    - Old: reportSnapshotTime → New: spotTime (FREQ only)

-- 2. Data Types:
--    - Use TIMESTAMP for all datetime fields (supports timezones)
--    - Use DATE for settlement dates
--    - Use INT64 for settlement periods

-- 3. Metadata:
--    - Add 'source' column to track data origin
--    - Keep ingested_utc for debugging
--    - Consider adding data_version if schema changes

-- 4. Performance:
--    - Views are virtual - no storage overhead
--    - Queries partition prune automatically
--    - Add clustering on frequently filtered columns

-- 5. Testing:
--    - Always test queries with LIMIT first
--    - Check for duplicate records at boundaries
--    - Validate datetime conversions
--    - Monitor query costs
