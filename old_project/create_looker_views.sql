-- BigQuery Scripting: Looker Studio–ready views for UK Energy
-- Run this whole script once. It will (re)create views in your dataset.

DECLARE project STRING DEFAULT 'jibber-jabber-knowledge';
DECLARE dataset STRING DEFAULT 'uk_energy';

-- Helper for season labels (1=Mon..7=Sun in BigQuery; we use month)
CREATE TEMP FUNCTION _season(m INT64) AS (
  CASE
    WHEN m IN (12,1,2) THEN 'Winter'
    WHEN m IN (3,4,5)  THEN 'Spring'
    WHEN m IN (6,7,8)  THEN 'Summer'
    ELSE 'Autumn'
  END
);

-- ============================
-- Core BMRS (historical)
-- ============================

-- 1) Bid-Offer Acceptances (VWAP per SP; plus volumes). Good for line/area/box/heatmaps.
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_bod_period AS
WITH bod AS (
  SELECT
    settlement_date,
    settlement_period,
    bmu_id,
    -- per-SP VWAPs (across BMUs)
    SUM(CASE WHEN accepted_offer_volume > 0 THEN offer_price * accepted_offer_volume END) 
      / NULLIF(SUM(CASE WHEN accepted_offer_volume > 0 THEN accepted_offer_volume END),0) AS vwap_offer_price,
    SUM(CASE WHEN accepted_bid_volume > 0 THEN bid_price * accepted_bid_volume END) 
      / NULLIF(SUM(CASE WHEN accepted_bid_volume > 0 THEN accepted_bid_volume END),0) AS vwap_bid_price,
    SUM(accepted_offer_volume) AS accepted_offer_volume_mw,
    SUM(accepted_bid_volume)   AS accepted_bid_volume_mw
  FROM `'''||project||'.'||dataset||'''`.elexon_bid_offer_acceptances
  GROUP BY settlement_date, settlement_period, bmu_id
),
agg AS (
  SELECT
    settlement_date,
    settlement_period,
    TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE) AS timestamp_utc,
    -- Aggregate across BMUs for SP-level view
    AVG(vwap_offer_price) AS vwap_offer_price,  -- mean of BMU-level VWAPs
    AVG(vwap_bid_price)   AS vwap_bid_price,
    SUM(accepted_offer_volume_mw) AS accepted_offer_volume_mw,
    SUM(accepted_bid_volume_mw)   AS accepted_bid_volume_mw
  FROM bod
  GROUP BY settlement_date, settlement_period
)
SELECT
  timestamp_utc,
  DATE(timestamp_utc) AS date,
  EXTRACT(HOUR FROM timestamp_utc) AS hour,
  settlement_period,
  EXTRACT(MONTH FROM timestamp_utc) AS month,
  _season(EXTRACT(MONTH FROM timestamp_utc)) AS season,
  EXTRACT(DAYOFWEEK FROM timestamp_utc) IN (1,7) AS is_weekend,
  vwap_bid_price    AS ssp_vwap,     -- SSP proxy
  vwap_offer_price  AS sbp_vwap,     -- SBP proxy
  (vwap_offer_price - vwap_bid_price) AS spread_gbp_mwh,
  accepted_bid_volume_mw,
  accepted_offer_volume_mw
FROM agg
ORDER BY timestamp_utc;
''';

-- 2) Demand Outturn (great for load profiles, heatmaps, seasonality)
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_demand_outturn_sp AS
SELECT
  TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE) AS timestamp_utc,
  DATE(settlement_date) AS date,
  EXTRACT(HOUR FROM TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE)) AS hour,
  settlement_period,
  EXTRACT(MONTH FROM settlement_date) AS month,
  _season(EXTRACT(MONTH FROM settlement_date)) AS season,
  EXTRACT(DAYOFWEEK FROM settlement_date) IN (1,7) AS is_weekend,
  national_demand                         AS national_demand_mw,
  england_wales_demand                    AS england_wales_demand_mw,
  embedded_wind_generation                AS embedded_wind_mw,
  embedded_solar_generation               AS embedded_solar_mw
FROM `'''||project||'.'||dataset||'''`.elexon_demand_outturn;
''';

-- 3) Generation Outturn mix (stacked area / 100% bars)
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_generation_mix_sp AS
SELECT
  TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE) AS timestamp_utc,
  DATE(settlement_date) AS date,
  EXTRACT(HOUR FROM TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE)) AS hour,
  settlement_period,
  EXTRACT(MONTH FROM settlement_date) AS month,
  _season(EXTRACT(MONTH FROM settlement_date)) AS season,
  EXTRACT(DAYOFWEEK FROM settlement_date) IN (1,7) AS is_weekend,
  fuel_type,
  generation_mw,
  generation_percentage
FROM `'''||project||'.'||dataset||'''`.elexon_generation_outturn;
''';

-- 4) System Warnings (for event overlays / Gantt)
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_system_warnings AS
SELECT
  TIMESTAMP(timestamp) AS timestamp_utc,
  DATE(timestamp) AS date,
  warning_type,
  severity,
  TIMESTAMP(start_time) AS start_ts_utc,
  TIMESTAMP(end_time)   AS end_ts_utc,
  TIMESTAMP_DIFF(COALESCE(TIMESTAMP(end_time), TIMESTAMP(timestamp)),
                 TIMESTAMP(timestamp), MINUTE) AS duration_min,
  affected_regions
FROM `'''||project||'.'||dataset||'''`.elexon_system_warnings;
''';

-- (Optional) Frequency timeseries (line, histogram)
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_frequency_timeseries AS
SELECT
  TIMESTAMP(timestamp) AS timestamp_utc,
  DATE(timestamp) AS date,
  EXTRACT(HOUR FROM TIMESTAMP(timestamp)) AS hour,
  (CAST(frequency_hz AS FLOAT64)) AS frequency_hz,
  (CAST(frequency_hz AS FLOAT64) - 50.0) * 1000.0 AS deviation_mhz
FROM `'''||project||'.'||dataset||'''`.elexon_frequency
''';

-- (Optional) Fuelinst instantaneous (stacked area)
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_fuelinst_timeseries AS
SELECT
  TIMESTAMP(timestamp) AS timestamp_utc,
  DATE(timestamp) AS date,
  fuel_type,
  generation_mw
FROM `'''||project||'.'||dataset||'''`.bmrs_fuelinst
''';

-- ============================
-- NESO (modern ops)
-- ============================

-- 5) Demand: forecast vs actual (join to Outturn). Great for lines, MAPE bars, heatmaps.
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_neso_demand_fc_vs_actual AS
WITH fc AS (
  SELECT
    settlement_date,
    settlement_period,
    forecast_date,
    TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE) AS timestamp_utc,
    AVG(national_demand_forecast) AS demand_fc_mw
  FROM `'''||project||'.'||dataset||'''`.neso_demand_forecasts
  GROUP BY settlement_date, settlement_period, forecast_date
),
act AS (
  SELECT
    settlement_date,
    settlement_period,
    national_demand AS actual_mw
  FROM `'''||project||'.'||dataset||'''`.elexon_demand_outturn
)
SELECT
  fc.timestamp_utc,
  DATE(fc.timestamp_utc) AS date,
  EXTRACT(HOUR FROM fc.timestamp_utc) AS hour,
  fc.settlement_period,
  fc.forecast_date,
  TIMESTAMP_DIFF(TIMESTAMP(DATETIME(fc.forecast_date)), fc.timestamp_utc, HOUR) * (-1) AS lead_hours,
  fc.demand_fc_mw,
  act.actual_mw,
  (act.actual_mw - fc.demand_fc_mw) AS error_mw,
  SAFE_DIVIDE(ABS(act.actual_mw - fc.demand_fc_mw), NULLIF(act.actual_mw,0)) * 100.0 AS mape_pct
FROM fc
LEFT JOIN act USING (settlement_date, settlement_period);
''';

-- 6) Wind: forecast vs actual (scatter/line; bias by lead)
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_neso_wind_fc_vs_actual AS
SELECT
  TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE) AS timestamp_utc,
  DATE(settlement_date) AS date,
  settlement_period,
  wind_farm_id,
  wind_farm_name,
  forecast_output_mw AS fc_mw,
  actual_output_mw   AS act_mw,
  (actual_output_mw - forecast_output_mw) AS error_mw
FROM `'''||project||'.'||dataset||'''`.neso_wind_forecasts
''';

-- 7) Carbon intensity (national & regional). Line, choropleth, bars.
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_neso_carbon_intensity AS
SELECT
  TIMESTAMP(timestamp) AS timestamp_utc,
  DATE(timestamp) AS date,
  region_code,
  carbon_intensity_gco2_kwh AS ci_gco2_kwh,
  renewable_percentage AS renewable_pct,
  fossil_percentage    AS fossil_pct,
  nuclear_percentage   AS nuclear_pct,
  imports_percentage   AS imports_pct
FROM `'''||project||'.'||dataset||'''`.neso_carbon_intensity
''';

-- 8) Balancing services cost/volume (bars/areas; dual-axis possible)
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_neso_balancing_services AS
SELECT
  charge_date AS date,
  settlement_period,
  -- If you have component columns, unpivot in a later iteration.
  cost_pounds              AS cost_gbp,
  volume_mwh               AS volume_mwh,
  bsuos_rate_pounds_mwh    AS rate_gbp_per_mwh
FROM `'''||project||'.'||dataset||'''`.neso_balancing_services
''';

-- 9) Interconnector flows w/ price spread if present (scatter/line)
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_interconnector_flows AS
SELECT
  TIMESTAMP_ADD(TIMESTAMP(DATETIME(trading_date)), INTERVAL (settlement_period-1)*30 MINUTE) AS timestamp_utc,
  DATE(trading_date) AS date,
  settlement_period,
  interconnector_name AS ic_name,
  actual_flow_mw,
  max_import_capacity_mw,
  max_export_capacity_mw,
  day_ahead_price_uk      AS uk_price_gbp_mwh,
  day_ahead_price_foreign AS foreign_price_eur_mwh,
  SAFE_CAST(NULL AS FLOAT64) AS uk_foreign_spread_gbp_mwh  -- set to NULL unless you normalise currency
FROM `'''||project||'.'||dataset||'''`.neso_interconnector_flows
''';

-- ============================
-- Joined “analytics” views
-- ============================

-- 10) Hourly energy balance (refined version of your existing view)
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_hourly_energy_balance AS
WITH gen AS (
  SELECT
    settlement_date,
    EXTRACT(HOUR FROM TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE)) AS hour,
    SUM(CASE WHEN fuel_type = 'WIND'   THEN generation_mw ELSE 0 END) AS wind_mw,
    SUM(CASE WHEN fuel_type = 'SOLAR'  THEN generation_mw ELSE 0 END) AS solar_mw,
    SUM(CASE WHEN fuel_type = 'NUCLEAR'THEN generation_mw ELSE 0 END) AS nuclear_mw,
    SUM(CASE WHEN fuel_type = 'CCGT'   THEN generation_mw ELSE 0 END) AS gas_mw,
    SUM(generation_mw) AS total_gen_mw
  FROM `'''||project||'.'||dataset||'''`.elexon_generation_outturn
  GROUP BY settlement_date, hour
),
dem AS (
  SELECT
    settlement_date,
    EXTRACT(HOUR FROM TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE)) AS hour,
    AVG(national_demand) AS demand_mw
  FROM `'''||project||'.'||dataset||'''`.elexon_demand_outturn
  GROUP BY settlement_date, hour
)
SELECT
  DATE(g.settlement_date) AS date,
  g.hour,
  dem.demand_mw,
  g.wind_mw, g.solar_mw, g.nuclear_mw, g.gas_mw,
  g.total_gen_mw
FROM gen g
LEFT JOIN dem USING (settlement_date, hour)
ORDER BY date, hour
''';

-- 11) Price spread drivers (BOD VWAP + demand, wind, balancing, warnings)
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_price_spread_drivers AS
WITH bod AS (
  SELECT
    settlement_date,
    settlement_period,
    TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE) AS ts,
    SUM(CASE WHEN accepted_offer_volume > 0 THEN offer_price * accepted_offer_volume END)
      / NULLIF(SUM(CASE WHEN accepted_offer_volume > 0 THEN accepted_offer_volume END),0) AS sbp_vwap,
    SUM(CASE WHEN accepted_bid_volume > 0 THEN bid_price * accepted_bid_volume END)
      / NULLIF(SUM(CASE WHEN accepted_bid_volume > 0 THEN accepted_bid_volume END),0) AS ssp_vwap
  FROM `'''||project||'.'||dataset||'''`.elexon_bid_offer_acceptances
  GROUP BY settlement_date, settlement_period
),
dem AS (
  SELECT
    settlement_date, settlement_period,
    AVG(national_demand) AS demand_mw
  FROM `'''||project||'.'||dataset||'''`.elexon_demand_outturn
  GROUP BY settlement_date, settlement_period
),
wind AS (
  SELECT
    settlement_date, settlement_period,
    AVG(COALESCE(actual_output_mw, forecast_output_mw)) AS wind_mw
  FROM `'''||project||'.'||dataset||'''`.neso_wind_forecasts
  GROUP BY settlement_date, settlement_period
),
bal AS (
  SELECT
    charge_date AS settlement_date, settlement_period,
    SUM(cost_pounds) AS balancing_cost_gbp,
    SUM(volume_mwh)  AS balancing_volume_mwh,
    SAFE_DIVIDE(SUM(cost_pounds), NULLIF(SUM(volume_mwh),0)) AS cost_per_mwh
  FROM `'''||project||'.'||dataset||'''`.neso_balancing_services
  GROUP BY settlement_date, settlement_period
),
warn AS (
  SELECT DISTINCT
    ts AS timestamp_utc,
    TRUE AS system_event_flag
  FROM (
    SELECT
      TIMESTAMP(timestamp) AS start_ts,
      TIMESTAMP(COALESCE(end_time, timestamp)) AS end_ts
    FROM `'''||project||'.'||dataset||'''`.elexon_system_warnings
  ), UNNEST(GENERATE_TIMESTAMP_ARRAY(start_ts, end_ts, INTERVAL 30 MINUTE)) AS ts
)
SELECT
  bod.ts AS timestamp_utc,
  DATE(bod.ts) AS date,
  EXTRACT(HOUR FROM bod.ts) AS hour,
  bod.settlement_period,
  (sbp_vwap - ssp_vwap) AS spread_gbp_mwh,
  ssp_vwap, sbp_vwap,
  dem.demand_mw,
  wind.wind_mw,
  bal.balancing_cost_gbp,
  bal.cost_per_mwh,
  IFNULL(warn.system_event_flag, FALSE) AS system_event_flag,
  _season(EXTRACT(MONTH FROM bod.ts)) AS season
FROM bod
LEFT JOIN dem  USING (settlement_date, settlement_period)
LEFT JOIN wind USING (settlement_date, settlement_period)
LEFT JOIN bal  USING (settlement_date, settlement_period)
LEFT JOIN warn ON warn.timestamp_utc = bod.ts
ORDER BY timestamp_utc
''';

-- 12) Forecast accuracy by lead/time-of-day (handy for bars/heatmaps)
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_forecast_accuracy AS
SELECT
  DATE(timestamp_utc) AS date,
  EXTRACT(HOUR FROM timestamp_utc) AS hour,
  lead_hours,
  AVG(mape_pct) AS mape_pct,
  AVG(ABS(error_mw)) AS mae_mw,
  SAFE_DIVIDE(SUM(ABS(error_mw)), NULLIF(SUM(actual_mw),0)) * 100 AS w_mape_pct
FROM `'''||project||'.'||dataset||'''`.v_neso_demand_fc_vs_actual
GROUP BY date, hour, lead_hours
ORDER BY date DESC, hour
''';

-- 13) Interconnector economics (flow vs spread) — if UK & foreign prices align in currency
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_interconnector_economics AS
SELECT
  timestamp_utc,
  date,
  settlement_period,
  ic_name,
  actual_flow_mw,
  uk_price_gbp_mwh,
  foreign_price_eur_mwh,
  uk_price_gbp_mwh - NULL AS price_spread_gbp_mwh  -- fill when FX-normalised
FROM `'''||project||'.'||dataset||'''`.v_interconnector_flows
''';

-- 14) Carbon vs mix (join carbon to generation mix) — good for scatter CI vs fossil share
EXECUTE IMMEDIATE '''
CREATE OR REPLACE VIEW `'''||project||'.'||dataset||'''`.v_carbon_vs_mix AS
WITH mix AS (
  SELECT
    TIMESTAMP_ADD(TIMESTAMP(DATETIME(settlement_date)), INTERVAL (settlement_period-1)*30 MINUTE) AS ts,
    SUM(CASE WHEN fuel_type IN ('WIND','SOLAR') THEN generation_mw ELSE 0 END) AS renewable_mw,
    SUM(CASE WHEN fuel_type IN ('CCGT','COAL','OIL') THEN generation_mw ELSE 0 END) AS fossil_mw,
    SUM(generation_mw) AS total_gen_mw
  FROM `'''||project||'.'||dataset||'''`.elexon_generation_outturn
  GROUP BY ts
),
ci AS (
  SELECT
    TIMESTAMP(timestamp) AS ts,
    AVG(carbon_intensity_gco2_kwh) AS ci_gco2_kwh
  FROM `'''||project||'.'||dataset||'''`.neso_carbon_intensity
  GROUP BY ts
)
SELECT
  m.ts AS timestamp_utc,
  DATE(m.ts) AS date,
  SAFE_DIVIDE(m.renewable_mw, NULLIF(m.total_gen_mw,0)) * 100 AS renewable_pct_calc,
  SAFE_DIVIDE(m.fossil_mw,    NULLIF(m.total_gen_mw,0)) * 100 AS fossil_pct_calc,
  ci.ci_gco2_kwh
FROM mix m
LEFT JOIN ci ON ci.ts = m.ts
ORDER BY timestamp_utc
''';
