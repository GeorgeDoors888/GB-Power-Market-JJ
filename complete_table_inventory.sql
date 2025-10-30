-- Check all BMRS tables and their row counts to see what data we have
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
SELECT 'bmrs_fuelhh' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fuelhh`
UNION ALL
SELECT 'bmrs_imbalngc' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_imbalngc`
UNION ALL
SELECT 'bmrs_itsdo' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_itsdo`
UNION ALL
SELECT 'bmrs_inddem' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_inddem`
UNION ALL
SELECT 'bmrs_indgen' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_indgen`
UNION ALL
SELECT 'bmrs_indo' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_indo`
UNION ALL
SELECT 'bmrs_fou2t14d' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fou2t14d`
UNION ALL
SELECT 'bmrs_fou2t3yw' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_fou2t3yw`
UNION ALL
SELECT 'bmrs_uou2t3yw' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_uou2t3yw`
UNION ALL
SELECT 'bmrs_mdp' as table_name, COUNT(*) as row_count FROM `jibber-jabber-knowledge.uk_energy_insights.bmrs_mdp`
ORDER BY row_count DESC;
