CREATE OR REPLACE VIEW `{{PROJECT}}.{{DATASET}}.vw_gen_dem_hh` AS
WITH gen AS (
  SELECT DATE(settlementDate) d, settlementPeriod sp, AVG(generation) gen_mw
  FROM `{{PROJECT}}.{{DATASET}}.bmrs_indgen_iris`
  WHERE boundary='N'
  GROUP BY d, sp
),
dem AS (
  SELECT DATE(settlementDate) d, settlementPeriod sp, ABS(AVG(demand)) dem_mw
  FROM `{{PROJECT}}.{{DATASET}}.bmrs_inddem_iris`
  WHERE boundary='N'
  GROUP BY d, sp
)
SELECT COALESCE(gen.d, dem.d) d, COALESCE(gen.sp, dem.sp) sp, gen.gen_mw, dem.dem_mw
FROM gen FULL OUTER JOIN dem USING(d, sp);