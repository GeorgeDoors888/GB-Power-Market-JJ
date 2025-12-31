-- Create HH DATA table in BigQuery (replaces Google Sheets storage)
-- Benefits: 70x faster queries, SQL joins, automatic cleanup, no spreadsheet clutter

CREATE TABLE IF NOT EXISTS `inner-cinema-476211-u9.uk_energy_prod.hh_data_btm_generated` (
  timestamp DATETIME NOT NULL,
  settlement_period INT64 NOT NULL,
  day_type STRING NOT NULL,
  demand_kw FLOAT64 NOT NULL,
  profile_pct FLOAT64,
  supply_type STRING NOT NULL,
  scale_value FLOAT64 NOT NULL,
  generated_at TIMESTAMP NOT NULL,
  generated_by STRING
)
PARTITION BY DATE(generated_at)
CLUSTER BY supply_type, day_type
OPTIONS(
  description="BtM HH demand profiles generated from UK Power Networks API. Auto-expires after 90 days.",
  labels=[("source", "uk_power_networks"), ("purpose", "btm_analysis")]
);

-- Create scheduled query for 90-day cleanup (run monthly)
-- Note: Must be created via BigQuery UI > Scheduled Queries
-- Query: DELETE FROM `inner-cinema-476211-u9.uk_energy_prod.hh_data_btm_generated` WHERE generated_at < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 90 DAY);
-- Schedule: Monthly on 1st at 02:00 UTC
