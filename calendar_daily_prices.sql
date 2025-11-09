CREATE OR REPLACE VIEW `{{PROJECT}}.{{DATASET}}.vw_daily_prices` AS
WITH hh AS (
  SELECT DATE(settlementDate) d, settlementPeriod sp,
         AVG(CASE WHEN dataProvider='N2EXMIDP' THEN price END) ssp,
         AVG(CASE WHEN dataProvider='APXMIDP' THEN price END) sbp
  FROM `{{PROJECT}}.{{DATASET}}.bmrs_mid`
  GROUP BY d, sp
)
SELECT d, AVG(ssp) ssp_day, AVG(sbp) sbp_day FROM hh GROUP BY d;