-- BMRS Data Validation Queries
-- Comprehensive validation of ingested BMRS datasets in BigQuery

-- 1. Get overview of all tables in the dataset
SELECT
  table_name,
  table_type,
  creation_time
FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES`
WHERE table_type = 'BASE_TABLE'
AND table_name LIKE 'bmrs_%'
ORDER BY table_name;

-- 2. Check data completeness and date ranges for each BMRS table
SELECT
  'bmrs_bod' as table_name,
  COUNT(*) as total_rows,
  MIN(settlementDate) as min_date,
  MAX(settlementDate) as max_date,
  COUNT(DISTINCT settlementDate) as unique_dates,
  DATE_DIFF(MAX(settlementDate), MIN(settlementDate), DAY) + 1 as expected_days
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
WHERE settlementDate IS NOT NULL

UNION ALL

SELECT
  'bmrs_freq' as table_name,
  COUNT(*) as total_rows,
  MIN(DATE(publishTime)) as min_date,
  MAX(DATE(publishTime)) as max_date,
  COUNT(DISTINCT DATE(publishTime)) as unique_dates,
  DATE_DIFF(MAX(DATE(publishTime)), MIN(DATE(publishTime)), DAY) + 1 as expected_days
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_freq`
WHERE publishTime IS NOT NULL

UNION ALL

SELECT
  'bmrs_uou2t3yw' as table_name,
  COUNT(*) as total_rows,
  MIN(DATE(publishTime)) as min_date,
  MAX(DATE(publishTime)) as max_date,
  COUNT(DISTINCT DATE(publishTime)) as unique_dates,
  DATE_DIFF(MAX(DATE(publishTime)), MIN(DATE(publishTime)), DAY) + 1 as expected_days
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_uou2t3yw`
WHERE publishTime IS NOT NULL

UNION ALL

SELECT
  'bmrs_mils' as table_name,
  COUNT(*) as total_rows,
  MIN(settlementDate) as min_date,
  MAX(settlementDate) as max_date,
  COUNT(DISTINCT settlementDate) as unique_dates,
  DATE_DIFF(MAX(settlementDate), MIN(settlementDate), DAY) + 1 as expected_days
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_mils`
WHERE settlementDate IS NOT NULL

UNION ALL

SELECT
  'bmrs_mels' as table_name,
  COUNT(*) as total_rows,
  MIN(settlementDate) as min_date,
  MAX(settlementDate) as max_date,
  COUNT(DISTINCT settlementDate) as unique_dates,
  DATE_DIFF(MAX(settlementDate), MIN(settlementDate), DAY) + 1 as expected_days
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_mels`
WHERE settlementDate IS NOT NULL

ORDER BY total_rows DESC;

-- 3. Check for data quality issues
-- Check for NULL values in key columns
SELECT
  'bmrs_bod' as table_name,
  'settlementDate' as column_name,
  COUNT(*) as null_count,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`), 2) as null_percentage
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
WHERE settlementDate IS NULL

UNION ALL

SELECT
  'bmrs_freq' as table_name,
  'publishTime' as column_name,
  COUNT(*) as null_count,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_freq`), 2) as null_percentage
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_freq`
WHERE publishTime IS NULL

UNION ALL

SELECT
  'bmrs_uou2t3yw' as table_name,
  'publishTime' as column_name,
  COUNT(*) as null_count,
  ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_uou2t3yw`), 2) as null_percentage
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_uou2t3yw`
WHERE publishTime IS NULL;

-- 4. Check for duplicate records using hash keys
SELECT
  'bmrs_bod' as table_name,
  COUNT(*) as total_records,
  COUNT(DISTINCT _hash_key) as unique_hash_keys,
  COUNT(*) - COUNT(DISTINCT _hash_key) as potential_duplicates
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`

UNION ALL

SELECT
  'bmrs_freq' as table_name,
  COUNT(*) as total_records,
  COUNT(DISTINCT _hash_key) as unique_hash_keys,
  COUNT(*) - COUNT(DISTINCT _hash_key) as potential_duplicates
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_freq`

UNION ALL

SELECT
  'bmrs_uou2t3yw' as table_name,
  COUNT(*) as total_records,
  COUNT(DISTINCT _hash_key) as unique_hash_keys,
  COUNT(*) - COUNT(DISTINCT _hash_key) as potential_duplicates
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_uou2t3yw`

UNION ALL

SELECT
  'bmrs_mils' as table_name,
  COUNT(*) as total_records,
  COUNT(DISTINCT _hash_key) as unique_hash_keys,
  COUNT(*) - COUNT(DISTINCT _hash_key) as potential_duplicates
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_mils`

UNION ALL

SELECT
  'bmrs_mels' as table_name,
  COUNT(*) as total_records,
  COUNT(DISTINCT _hash_key) as unique_hash_keys,
  COUNT(*) - COUNT(DISTINCT _hash_key) as potential_duplicates
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_mels`;

-- 5. Check recent ingestion activity
SELECT
  table_name,
  COUNT(*) as records_count,
  MAX(_ingested_utc) as latest_ingestion,
  MIN(_ingested_utc) as earliest_ingestion,
  COUNT(DISTINCT DATE(_ingested_utc)) as ingestion_days
FROM (
  SELECT 'bmrs_bod' as table_name, _ingested_utc FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
  UNION ALL
  SELECT 'bmrs_freq' as table_name, _ingested_utc FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_freq`
  UNION ALL
  SELECT 'bmrs_uou2t3yw' as table_name, _ingested_utc FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_uou2t3yw`
  UNION ALL
  SELECT 'bmrs_mils' as table_name, _ingested_utc FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_mils`
  UNION ALL
  SELECT 'bmrs_mels' as table_name, _ingested_utc FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_mels`
)
WHERE _ingested_utc IS NOT NULL
GROUP BY table_name
ORDER BY latest_ingestion DESC;
