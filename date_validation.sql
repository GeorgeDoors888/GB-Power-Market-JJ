-- Check date ranges for the main tables
SELECT
  'bmrs_bod' as table_name,
  MIN(settlementDate) as min_date,
  MAX(settlementDate) as max_date,
  COUNT(DISTINCT settlementDate) as unique_dates
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`;

SELECT
  'bmrs_freq' as table_name,
  MIN(DATE(publishTime)) as min_date,
  MAX(DATE(publishTime)) as max_date,
  COUNT(DISTINCT DATE(publishTime)) as unique_dates
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_freq`;

SELECT
  'bmrs_fuelinst' as table_name,
  MIN(DATE(publishTime)) as min_date,
  MAX(DATE(publishTime)) as max_date,
  COUNT(DISTINCT DATE(publishTime)) as unique_dates
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`;
