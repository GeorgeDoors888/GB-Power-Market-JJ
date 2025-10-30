-- Monitor progress of missing dataset ingestion
-- Check if new tables are being created

-- Check if new tables exist
SELECT
  table_name,
  table_type,
  creation_time
FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES`
WHERE table_name LIKE 'bmrs_%'
AND table_name IN ('bmrs_netbsad', 'bmrs_costs', 'bmrs_stor', 'bmrs_ndf', 'bmrs_tsdf')
ORDER BY creation_time DESC;

-- Get row counts for newly created tables
SELECT 'bmrs_netbsad' as table_name, COUNT(*) as row_count
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_netbsad`
UNION ALL
SELECT 'bmrs_costs' as table_name, COUNT(*) as row_count
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_costs`
UNION ALL
SELECT 'bmrs_stor' as table_name, COUNT(*) as row_count
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_stor`
UNION ALL
SELECT 'bmrs_ndf' as table_name, COUNT(*) as row_count
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_ndf`
UNION ALL
SELECT 'bmrs_tsdf' as table_name, COUNT(*) as row_count
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_tsdf`
ORDER BY row_count DESC;
