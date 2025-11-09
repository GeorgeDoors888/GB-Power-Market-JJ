CREATE OR REPLACE VIEW `{{PROJECT}}.{{DATASET}}.vw_prices_hh` AS
SELECT DATE(settlementDate) AS d,
       settlementPeriod     AS sp,
       MAX(CASE WHEN dataProvider='N2EXMIDP' THEN price END) AS ssp,
       MAX(CASE WHEN dataProvider='APXMIDP' THEN price END) AS sbp
FROM `{{PROJECT}}.{{DATASET}}.bmrs_mid`
GROUP BY d, sp;