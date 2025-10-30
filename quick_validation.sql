-- Quick validation of available BMRS tables
-- Check what tables actually exist first

-- 1. List all BMRS tables that exist
SELECT
  table_name
FROM `jibber-jabber-knowledge.uk_energy_insights.INFORMATION_SCHEMA.TABLES`
WHERE table_name LIKE 'bmrs_%'
AND table_type = 'BASE_TABLE'
ORDER BY table_name;

-- 2. Check a few confirmed tables from your list
SELECT 'bmrs_bod' as table_name, COUNT(*) as row_count
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`;

SELECT 'bmrs_freq' as table_name, COUNT(*) as row_count
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_freq`;

SELECT 'bmrs_fuelinst' as table_name, COUNT(*) as row_count
FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`;
