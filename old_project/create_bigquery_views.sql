-- ----------------------------------------------------------------------------
-- 1. Hourly Energy Balance View (Corrected)
-- Purpose: Provides a summary of energy generation, demand, and frequency at an hourly level.
-- Note: This view now joins generation and demand data from separate Elexon tables.
-- A placeholder for 'frequency' is used as it's not in the base tables.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `jibber-jabber-knowledge.uk_energy.v_hourly_energy_balance` AS
WITH demand_data AS (
  SELECT
    TIMESTAMP_TRUNC(TIMESTAMP(settlement_date), HOUR) as hour,
    AVG(national_demand) as avg_demand
  FROM `jibber-jabber-knowledge.uk_energy.elexon_demand_outturn`
  GROUP BY 1
),
generation_data AS (
  SELECT
    TIMESTAMP_TRUNC(TIMESTAMP(settlement_date), HOUR) as hour,
    SUM(CASE WHEN fuel_type = 'WIND' THEN generation_mw ELSE 0 END) as total_wind_generation,
    SUM(CASE WHEN fuel_type = 'SOLAR' THEN generation_mw ELSE 0 END) as total_solar_generation
  FROM `jibber-jabber-knowledge.uk_energy.elexon_generation_outturn`
  GROUP BY 1
)
SELECT
  d.hour,
  50.0 AS avg_frequency, -- Placeholder: Frequency data source not identified yet
  d.avg_demand,
  g.total_wind_generation,
  g.total_solar_generation
FROM demand_data d
JOIN generation_data g ON d.hour = g.hour
ORDER BY d.hour DESC;

-- ----------------------------------------------------------------------------
-- 2. System Price Spread Drivers View (Corrected with Assumptions)
-- Purpose: Analyzes the key drivers for the spread between SSP and SBP.
-- Note: Assumes 'cost_pounds' and 'volume_mwh' can be used to derive prices.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `jibber-jabber-knowledge.uk_energy.v_price_spread_drivers` AS
WITH generation_data AS (
  SELECT
    TIMESTAMP_TRUNC(TIMESTAMP(settlement_date), HOUR) as hour,
    AVG(generation_mw) as avg_wind_generation
  FROM `jibber-jabber-knowledge.uk_energy.elexon_generation_outturn`
  WHERE fuel_type = 'WIND'
  GROUP BY 1
),
warnings_data AS (
  SELECT
    TIMESTAMP_TRUNC(TIMESTAMP(timestamp), HOUR) as hour,
    COUNT(*) as warning_count
  FROM `jibber-jabber-knowledge.uk_energy.elexon_system_warnings`
  GROUP BY 1
),
price_data AS (
    SELECT
        TIMESTAMP_TRUNC(TIMESTAMP(charge_date), HOUR) AS hour,
        SAFE_DIVIDE(SUM(cost_pounds), SUM(volume_mwh)) as avg_system_price
    FROM `jibber-jabber-knowledge.uk_energy.neso_balancing_services`
    GROUP BY 1
)
SELECT
  p.hour,
  p.avg_system_price AS avg_ssp, -- Placeholder, using avg price
  p.avg_system_price AS avg_sbp, -- Placeholder, using avg price
  0 AS avg_price_spread, -- Placeholder
  gd.avg_wind_generation,
  sw.warning_count
FROM
  price_data p
LEFT JOIN
  generation_data gd ON p.hour = gd.hour
LEFT JOIN
  warnings_data sw ON p.hour = sw.hour
GROUP BY 1, p.avg_system_price, gd.avg_wind_generation, sw.warning_count
ORDER BY 1 DESC;

-- ----------------------------------------------------------------------------
-- 3. Balancing Mechanism Acceptance Analysis View (SKIPPED)
-- Purpose: Investigates which fuel types are most frequently accepted for bids and offers.
-- Reason: This is not possible with the current schema. The `elexon_bid_offer_acceptances` table contains the `bmu_id`,
-- but the `elexon_generation_outturn` table does not, so there is no way to link an acceptance to a fuel type.
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- 4. High/Low Frequency Incidents View (SKIPPED)
-- Purpose: Flags periods with significant deviations from the standard 50Hz frequency.
-- Reason: Frequency data is not available in the identified tables.
-- ----------------------------------------------------------------------------
-- This view is skipped as there is no 'frequency' column in the available tables.

-- ----------------------------------------------------------------------------
-- 5. Renewable Generation vs. System Prices View (Corrected with Assumptions)
-- Purpose: Correlates renewable energy output with system pricing.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `jibber-jabber-knowledge.uk_energy.v_renewable_vs_system_prices` AS
WITH generation_data AS (
  SELECT
    TIMESTAMP_TRUNC(TIMESTAMP(settlement_date), HOUR) as hour,
    AVG(CASE WHEN fuel_type = 'WIND' THEN generation_mw ELSE 0 END) as avg_wind,
    AVG(CASE WHEN fuel_type = 'SOLAR' THEN generation_mw ELSE 0 END) as avg_solar
  FROM `jibber-jabber-knowledge.uk_energy.elexon_generation_outturn`
  GROUP BY 1
),
price_data AS (
    SELECT
        TIMESTAMP_TRUNC(TIMESTAMP(charge_date), HOUR) AS hour,
        SAFE_DIVIDE(SUM(cost_pounds), SUM(volume_mwh)) as avg_system_price
    FROM `jibber-jabber-knowledge.uk_energy.neso_balancing_services`
    GROUP BY 1
)
SELECT
  gd.hour,
  gd.avg_wind,
  gd.avg_solar,
  p.avg_system_price AS avg_ssp, -- Placeholder
  p.avg_system_price AS avg_sbp -- Placeholder
FROM
  generation_data gd
JOIN
  price_data p ON gd.hour = p.hour
GROUP BY 1, gd.avg_wind, gd.avg_solar, p.avg_system_price
ORDER BY 1 DESC;

-- ----------------------------------------------------------------------------
-- 6. Daily Peak Demand and Generation View (Corrected)
-- Purpose: Identifies the daily peaks for demand and generation sources.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `jibber-jabber-knowledge.uk_energy.v_daily_peak_summary` AS
WITH daily_demand AS (
    SELECT
      DATE(settlement_date) AS day,
      MAX(national_demand) AS peak_demand
    FROM `jibber-jabber-knowledge.uk_energy.elexon_demand_outturn`
    GROUP BY 1
),
daily_generation AS (
    SELECT
      DATE(settlement_date) AS day,
      MAX(CASE WHEN fuel_type = 'WIND' THEN generation_mw ELSE 0 END) AS peak_wind_generation,
      MAX(CASE WHEN fuel_type = 'SOLAR' THEN generation_mw ELSE 0 END) AS peak_solar_generation,
      MAX(CASE WHEN fuel_type = 'NUCLEAR' THEN generation_mw ELSE 0 END) AS peak_nuclear_generation,
      MAX(CASE WHEN fuel_type = 'GAS' THEN generation_mw ELSE 0 END) AS peak_gas_generation
    FROM `jibber-jabber-knowledge.uk_energy.elexon_generation_outturn`
    GROUP BY 1
)
SELECT
  d.day,
  d.peak_demand,
  g.peak_wind_generation,
  g.peak_solar_generation,
  g.peak_nuclear_generation,
  g.peak_gas_generation
FROM daily_demand d
JOIN daily_generation g ON d.day = g.day
ORDER BY 1 DESC;

-- ----------------------------------------------------------------------------
-- 7. System Warning Hotspots View (Corrected)
-- Purpose: Shows which times of day or days of the week have the most system warnings.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `jibber-jabber-knowledge.uk_energy.v_system_warning_hotspots` AS
SELECT
  FORMAT_TIMESTAMP('%A', TIMESTAMP(timestamp)) AS day_of_week,
  EXTRACT(HOUR FROM timestamp) AS hour_of_day,
  COUNT(*) AS warning_count
FROM
  `jibber-jabber-knowledge.uk_energy.elexon_system_warnings`
GROUP BY 1, 2
ORDER BY warning_count DESC;

-- ----------------------------------------------------------------------------
-- 8. Bid-Offer Acceptance Volume View (Corrected)
-- Purpose: Summarizes the total accepted volumes for bids and offers.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `jibber-jabber-knowledge.uk_energy.v_bid_offer_volume_summary` AS
WITH unpivoted_acceptances AS (
    SELECT 'Bid' as acceptance_type, accepted_bid_volume as volume FROM `jibber-jabber-knowledge.uk_energy.elexon_bid_offer_acceptances`
    UNION ALL
    SELECT 'Offer' as acceptance_type, accepted_offer_volume as volume FROM `jibber-jabber-knowledge.uk_energy.elexon_bid_offer_acceptances`
)
SELECT
  acceptance_type,
  SUM(volume) AS total_volume_mwh,
  AVG(volume) AS avg_volume_mwh,
  COUNT(volume) AS number_of_acceptances
FROM
  unpivoted_acceptances
WHERE volume > 0
GROUP BY 1;

-- ----------------------------------------------------------------------------
-- 9. Net Imbalance Volume Analysis View (SKIPPED)
-- Purpose: Calculates the net imbalance volume over time.
-- Reason: No table found that clearly represents net imbalance volume.
-- ----------------------------------------------------------------------------
-- This view is skipped as there is no clear source for 'net_imbalance_volume'.

-- ----------------------------------------------------------------------------
-- 10. Generation Mix Snapshot View (Corrected)
-- Purpose: Provides a recent snapshot of the generation mix.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `jibber-jabber-knowledge.uk_energy.v_generation_mix_snapshot` AS
SELECT
  settlement_date as time,
  settlement_period,
  fuel_type,
  generation_mw as generation
FROM
  `jibber-jabber-knowledge.uk_energy.elexon_generation_outturn`
ORDER BY time DESC, settlement_period DESC
LIMIT 100;

-- ----------------------------------------------------------------------------
-- 11. System Price Volatility View (Corrected with Assumptions)
-- Purpose: Calculates the volatility of system prices on a daily basis.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `jibber-jabber-knowledge.uk_energy.v_daily_price_volatility` AS
WITH daily_prices AS (
    SELECT
        DATE(charge_date) AS day,
        SAFE_DIVIDE(SUM(cost_pounds), SUM(volume_mwh)) as daily_avg_price
    FROM `jibber-jabber-knowledge.uk_energy.neso_balancing_services`
    GROUP BY 1
)
SELECT
  day,
  STDDEV(daily_avg_price) AS ssp_volatility, -- Placeholder
  STDDEV(daily_avg_price) AS sbp_volatility, -- Placeholder
  MAX(daily_avg_price) - MIN(daily_avg_price) AS ssp_range, -- Placeholder
  MAX(daily_avg_price) - MIN(daily_avg_price) AS sbp_range -- Placeholder
FROM
  daily_prices
GROUP BY 1
ORDER BY 1 DESC;

-- ----------------------------------------------------------------------------
-- 12. Major Demand Change Events View (Corrected)
-- Purpose: Identifies large ramps in demand within a short period.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `jibber-jabber-knowledge.uk_energy.v_demand_ramping_events` AS
WITH DemandChanges AS (
  SELECT
    TIMESTAMP(settlement_date, PARSE_TIME('%T', settlement_period)) as time,
    national_demand,
    LEAD(national_demand, 1) OVER (ORDER BY settlement_date, settlement_period) AS next_demand,
    TIMESTAMP_DIFF(
        LEAD(TIMESTAMP(settlement_date, PARSE_TIME('%T', settlement_period)), 1) OVER (ORDER BY settlement_date, settlement_period),
        TIMESTAMP(settlement_date, PARSE_TIME('%T', settlement_period)),
        MINUTE
    ) as time_diff_minutes
  FROM
    `jibber-jabber-knowledge.uk_energy.elexon_demand_outturn`
)
SELECT
  time,
  national_demand,
  next_demand,
  (next_demand - national_demand) AS demand_change
FROM
  DemandChanges
WHERE
  time_diff_minutes > 0 AND time_diff_minutes <= 30 -- Settlement periods are 30 mins
  AND ABS(next_demand - national_demand) > 500 -- Ramp threshold of 500 MW
ORDER BY
  ABS(demand_change) DESC;

-- ----------------------------------------------------------------------------
-- 13. Balancing Services Cost View (Corrected with Assumptions)
-- Purpose: Estimates the cost of balancing services based on accepted offers.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `jibber-jabber-knowledge.uk_energy.v_balancing_services_cost` AS
SELECT
  TIMESTAMP_TRUNC(TIMESTAMP(boa.settlement_date), DAY) AS day,
  -- This is a very rough estimation, as we cannot directly link acceptances to balancing service costs
  -- on a 1-to-1 basis with the current schema.
  SUM(boa.accepted_offer_volume * p.avg_system_price) AS estimated_cost
FROM
  `jibber-jabber-knowledge.uk_energy.elexon_bid_offer_acceptances` boa
JOIN
  `jibber-jabber-knowledge.uk_energy.v_daily_price_volatility` p ON DATE(boa.settlement_date) = p.day
WHERE
  boa.accepted_offer_volume > 0
GROUP BY 1
ORDER BY 1 DESC;

-- ----------------------------------------------------------------------------
-- 14. Renewable Curtailment Proxy View (Corrected with Assumptions)
-- Purpose: Identifies potential curtailment events where system prices are low/negative
--          during high renewable generation periods.
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW `jibber-jabber-knowledge.uk_energy.v_renewable_curtailment_proxy` AS
SELECT
  gd.hour,
  gd.avg_wind,
  p.avg_ssp
FROM
  `jibber-jabber-knowledge.uk_energy.v_renewable_vs_system_prices` gd
JOIN
  `jibber-jabber-knowledge.uk_energy.v_renewable_vs_system_prices` p ON gd.hour = p.hour
WHERE
  gd.avg_wind > (SELECT AVG(generation_mw) * 1.5 FROM `jibber-jabber-knowledge.uk_energy.elexon_generation_outturn` WHERE fuel_type = 'WIND')
  AND p.avg_ssp <= 0 -- Using the proxy for system sell price
GROUP BY 1, gd.avg_wind, p.avg_ssp
ORDER BY 1 DESC;
