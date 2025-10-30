-- Simple BMRS Data Validation Queries
-- Basic validation of ingested BMRS datasets

-- 1. List all BMRS tables
SELECT
  table_name,
  table_type
FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES`
WHERE table_name LIKE 'bmrs_%'
ORDER BY table_name;

-- 2. Check row counts for main BMRS tables
SELECT 'bmrs_bod' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
UNION ALL
SELECT 'bmrs_boalf' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_boalf`
UNION ALL
SELECT 'bmrs_freq' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_freq`
UNION ALL
SELECT 'bmrs_fuelinst' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
UNION ALL
SELECT 'bmrs_disbsad' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_disbsad`
UNION ALL
SELECT 'bmrs_mils' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_mils`
UNION ALL
SELECT 'bmrs_mels' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_mels`
UNION ALL
SELECT 'bmrs_uou2t3yw' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_uou2t3yw`
ORDER BY row_count DESC;

-- 3. Check date ranges for key tables
SELECT
  'bmrs_bod' as table_name,
  MIN(settlementDate) as min_date,
  MAX(settlementDate) as max_date,
  COUNT(DISTINCT settlementDate) as unique_dates
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
UNION ALL
SELECT
  'bmrs_freq' as table_name,
  MIN(publishTime) as min_date,
  MAX(publishTime) as max_date,
  COUNT(DISTINCT DATE(publishTime)) as unique_dates
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_freq`
UNION ALL
SELECT
  'bmrs_fuelinst' as table_name,
  MIN(publishTime) as min_date,
  MAX(publishTime) as max_date,
  COUNT(DISTINCT DATE(publishTime)) as unique_dates
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
ORDER BY table_name;

-- 4. Sample data from key tables
SELECT 'bmrs_bod sample' as info, dataset, settlementDate, settlementPeriod, bmUnit
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
LIMIT 5;

SELECT 'bmrs_freq sample' as info, dataset, publishTime, frequency
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_freq`
LIMIT 5;

SELECT 'bmrs_fuelinst sample' as info, dataset, publishTime, fuelType, generation
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
LIMIT 5;
