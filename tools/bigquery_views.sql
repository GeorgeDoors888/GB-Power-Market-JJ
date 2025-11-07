-- BigQuery views for extended analytics
-- Run with: bq query --use_legacy_sql=false < tools/bigquery_views.sql

-- BOD/BOALF per day + SP for quick joins (usable for extended charts)
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_ops.v_bod_boalf_sp` AS
SELECT
  COALESCE(bod.settlement_date, boalf.delivery_date) AS d,
  COALESCE(bod.settlement_period, boalf.settlement_period) AS sp,
  COALESCE(bod.bm_unit_id, boalf.bm_unit_id) AS bmu_id,
  AVG(bod.accepted_price) AS bod_price,
  SUM(boalf.accepted_volume_mwh) AS boalf_mwh,
  AVG(boalf.accepted_price) AS boalf_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` bod
FULL OUTER JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` boalf
  ON bod.settlement_date = boalf.delivery_date
 AND bod.settlement_period = boalf.settlement_period
 AND bod.bm_unit_id = boalf.bm_unit_id
GROUP BY d, sp, bmu_id;
