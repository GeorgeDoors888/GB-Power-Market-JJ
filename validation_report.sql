-- BMRS Data Validation Report
-- Based on validation results from 2025-09-20

-- Get row counts for all main BMRS tables
SELECT 'bmrs_bod' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_bod`
UNION ALL
SELECT 'bmrs_boalf' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_boalf`
UNION ALL
SELECT 'bmrs_freq' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_freq`
UNION ALL
SELECT 'bmrs_fuelinst' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelinst`
UNION ALL
SELECT 'bmrs_disbsad' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_disbsad`
ORDER BY row_count DESC;
