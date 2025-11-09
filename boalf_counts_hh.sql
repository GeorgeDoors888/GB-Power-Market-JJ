CREATE OR REPLACE VIEW `{{PROJECT}}.{{DATASET}}.vw_boalf_counts_hh` AS
SELECT DATE(settlementDate) d, settlementPeriod sp, COUNT(*) boalf_count, AVG(acceptedVolumeMW) boalf_avg_mw
FROM `{{PROJECT}}.{{DATASET}}.bmrs_boalf`
GROUP BY d, sp;