-- Energy Tariff Data - BigQuery Views
-- Creates views for current tariff rates and battery cost calculations
-- Run after: ingest_tariff_data_from_sheets.py
-- Author: George Major
-- Date: 21 November 2025

-- ============================================================================
-- View 1: Current Tariff Rates
-- Returns the latest rates for all tariff types
-- ============================================================================

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.vw_current_tariffs` AS
WITH current_date AS (
    SELECT CURRENT_DATE() as today
),

-- TNUoS: Get latest year for typical LV connection
tnuos_current AS (
    SELECT 
        rate_gbp_per_site_day,
        rate_gbp_per_site_year,
        tariff_year
    FROM `inner-cinema-476211-u9.uk_energy_prod.tnuos_tdr_bands`
    WHERE band = 'LV_NoMIC_1'  -- Typical small-scale battery connection
      AND effective_from <= (SELECT today FROM current_date)
    ORDER BY effective_from DESC
    LIMIT 1
),

-- FiT: Get latest year
fit_current AS (
    SELECT 
        implied_rate_p_per_kwh,
        fiscal_year,
        scheme_year
    FROM `inner-cinema-476211-u9.uk_energy_prod.fit_levelisation_rates`
    WHERE effective_from <= (SELECT today FROM current_date)
    ORDER BY effective_from DESC
    LIMIT 1
),

-- RO: Get current obligation year
ro_current AS (
    SELECT 
        buyout_gbp_per_roc,
        obligation_roc_per_mwh,
        recycle_gbp_per_roc,
        -- Calculate effective p/kWh rate
        (buyout_gbp_per_roc + recycle_gbp_per_roc) * obligation_roc_per_mwh / 10 as ro_p_per_kwh,
        obligation_year
    FROM `inner-cinema-476211-u9.uk_energy_prod.ro_rates`
    WHERE effective_from <= (SELECT today FROM current_date)
      AND effective_to >= (SELECT today FROM current_date)
    LIMIT 1
),

-- BSUoS: Get current period
bsuos_current AS (
    SELECT 
        rate_gbp_per_mwh,
        tariff_title,
        effective_from,
        effective_to
    FROM `inner-cinema-476211-u9.uk_energy_prod.bsuos_rates`
    WHERE effective_from <= (SELECT today FROM current_date)
      AND effective_to >= (SELECT today FROM current_date)
      AND publication_status = 'Final'
    LIMIT 1
),

-- CCL: Get current year (full rate, not CCA discounted)
ccl_current AS (
    SELECT 
        electricity_gbp_per_kwh,
        gas_gbp_per_kwh,
        cca_electricity_gbp_per_kwh,
        fiscal_year
    FROM `inner-cinema-476211-u9.uk_energy_prod.ccl_rates`
    WHERE effective_from <= (SELECT today FROM current_date)
    ORDER BY effective_from DESC
    LIMIT 1
)

SELECT
    (SELECT today FROM current_date) as query_date,
    
    -- TNUoS rates
    (SELECT rate_gbp_per_site_day FROM tnuos_current) as tnuos_gbp_site_day,
    (SELECT rate_gbp_per_site_year FROM tnuos_current) as tnuos_gbp_site_year,
    (SELECT tariff_year FROM tnuos_current) as tnuos_year,
    
    -- FiT rates
    (SELECT implied_rate_p_per_kwh FROM fit_current) as fit_p_per_kwh,
    (SELECT fiscal_year FROM fit_current) as fit_year,
    
    -- RO rates
    (SELECT ro_p_per_kwh FROM ro_current) as ro_p_per_kwh,
    (SELECT buyout_gbp_per_roc FROM ro_current) as ro_buyout_gbp_per_roc,
    (SELECT obligation_roc_per_mwh FROM ro_current) as ro_obligation_roc_per_mwh,
    (SELECT obligation_year FROM ro_current) as ro_year,
    
    -- BSUoS rates
    (SELECT rate_gbp_per_mwh FROM bsuos_current) as bsuos_gbp_per_mwh,
    (SELECT tariff_title FROM bsuos_current) as bsuos_tariff,
    (SELECT effective_from FROM bsuos_current) as bsuos_period_start,
    (SELECT effective_to FROM bsuos_current) as bsuos_period_end,
    
    -- CCL rates
    (SELECT electricity_gbp_per_kwh FROM ccl_current) as ccl_gbp_per_kwh,
    (SELECT cca_electricity_gbp_per_kwh FROM ccl_current) as ccl_cca_gbp_per_kwh,
    (SELECT fiscal_year FROM ccl_current) as ccl_year;


-- ============================================================================
-- View 2: Battery Arbitrage Costs
-- Calculates all-in tariff costs for battery storage operations
-- ============================================================================

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.vw_battery_arbitrage_costs` AS
WITH current_rates AS (
    SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.vw_current_tariffs`
)
SELECT
    query_date,
    
    -- ========================================================================
    -- DISCHARGE COSTS (per MWh exported to grid)
    -- ========================================================================
    
    -- FiT levy (p/kWh → £/MWh)
    fit_p_per_kwh * 10 as fit_cost_gbp_per_mwh,
    
    -- RO levy (p/kWh → £/MWh)
    ro_p_per_kwh * 10 as ro_cost_gbp_per_mwh,
    
    -- BSUoS (£/MWh)
    bsuos_gbp_per_mwh as bsuos_cost_gbp_per_mwh_discharge,
    
    -- CCL (£/kWh → £/MWh) - Note: Many generators are CCL exempt
    ccl_gbp_per_kwh * 1000 as ccl_cost_gbp_per_mwh,
    
    -- Total discharge cost
    (fit_p_per_kwh * 10) + 
    (ro_p_per_kwh * 10) + 
    bsuos_gbp_per_mwh + 
    (ccl_gbp_per_kwh * 1000) as total_discharge_cost_gbp_per_mwh,
    
    -- ========================================================================
    -- CHARGE COSTS (per MWh imported from grid)
    -- ========================================================================
    
    -- BSUoS (only charge on imports/exports, not double-counted)
    bsuos_gbp_per_mwh as bsuos_cost_gbp_per_mwh_charge,
    
    -- Total charge cost (typically just BSUoS for storage)
    bsuos_gbp_per_mwh as total_charge_cost_gbp_per_mwh,
    
    -- ========================================================================
    -- FIXED COSTS
    -- ========================================================================
    
    -- TNUoS daily charge
    tnuos_gbp_site_day as fixed_cost_gbp_per_day,
    tnuos_gbp_site_year as fixed_cost_gbp_per_year,
    
    -- ========================================================================
    -- TOTAL COST FOR FULL CYCLE (charge + discharge)
    -- ========================================================================
    
    bsuos_gbp_per_mwh + -- Charge BSUoS
    (fit_p_per_kwh * 10) + -- Discharge FiT
    (ro_p_per_kwh * 10) + -- Discharge RO
    bsuos_gbp_per_mwh + -- Discharge BSUoS
    (ccl_gbp_per_kwh * 1000) -- Discharge CCL (if applicable)
    as total_cycle_cost_gbp_per_mwh,
    
    -- ========================================================================
    -- EXAMPLE CALCULATIONS
    -- ========================================================================
    
    -- For 50 MW battery, 2 cycles/day, 365 days
    -- Annual volume: 50 MW × 2h × 2 cycles × 365 days = 73,000 MWh
    
    -- Annual discharge costs (36,500 MWh/year)
    36500 * ((fit_p_per_kwh * 10) + (ro_p_per_kwh * 10) + bsuos_gbp_per_mwh + (ccl_gbp_per_kwh * 1000)) 
        as example_50mw_discharge_costs_gbp_per_year,
    
    -- Annual charge costs (36,500 MWh/year)
    36500 * bsuos_gbp_per_mwh as example_50mw_charge_costs_gbp_per_year,
    
    -- Annual fixed costs
    365 * tnuos_gbp_site_day as example_50mw_fixed_costs_gbp_per_year,
    
    -- Total annual tariff costs
    (36500 * ((fit_p_per_kwh * 10) + (ro_p_per_kwh * 10) + bsuos_gbp_per_mwh + (ccl_gbp_per_kwh * 1000))) + 
    (36500 * bsuos_gbp_per_mwh) + 
    (365 * tnuos_gbp_site_day) as example_50mw_total_costs_gbp_per_year,
    
    -- ========================================================================
    -- CONTEXT DATA
    -- ========================================================================
    
    tnuos_year,
    fit_year,
    ro_year,
    bsuos_tariff,
    ccl_year

FROM current_rates;


-- ============================================================================
-- View 3: Historical Tariff Rates by Date
-- Enables time-series analysis of tariff costs
-- ============================================================================

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.vw_tariff_rates_by_date` AS
WITH date_spine AS (
    -- Generate all dates from 2016-04-01 to today
    SELECT date
    FROM UNNEST(GENERATE_DATE_ARRAY('2016-04-01', CURRENT_DATE(), INTERVAL 1 DAY)) as date
),

tnuos_by_date AS (
    SELECT 
        d.date,
        t.rate_gbp_per_site_day as tnuos_gbp_site_day,
        t.tariff_year as tnuos_year
    FROM date_spine d
    LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.tnuos_tdr_bands` t
        ON d.date BETWEEN t.effective_from AND t.effective_to
        AND t.band = 'LV_NoMIC_1'
),

fit_by_date AS (
    SELECT 
        d.date,
        f.implied_rate_p_per_kwh as fit_p_per_kwh,
        f.fiscal_year as fit_year
    FROM date_spine d
    LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.fit_levelisation_rates` f
        ON d.date BETWEEN f.effective_from AND f.effective_to
),

ro_by_date AS (
    SELECT 
        d.date,
        (r.buyout_gbp_per_roc + r.recycle_gbp_per_roc) * r.obligation_roc_per_mwh / 10 as ro_p_per_kwh,
        r.obligation_year as ro_year
    FROM date_spine d
    LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.ro_rates` r
        ON d.date BETWEEN r.effective_from AND r.effective_to
),

bsuos_by_date AS (
    SELECT 
        d.date,
        b.rate_gbp_per_mwh as bsuos_gbp_per_mwh,
        b.tariff_title as bsuos_tariff
    FROM date_spine d
    LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bsuos_rates` b
        ON d.date BETWEEN b.effective_from AND b.effective_to
        AND b.publication_status = 'Final'
),

ccl_by_date AS (
    SELECT 
        d.date,
        c.electricity_gbp_per_kwh as ccl_gbp_per_kwh,
        c.fiscal_year as ccl_year
    FROM date_spine d
    LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.ccl_rates` c
        ON d.date >= c.effective_from
    QUALIFY ROW_NUMBER() OVER (PARTITION BY d.date ORDER BY c.effective_from DESC) = 1
)

SELECT
    d.date,
    EXTRACT(YEAR FROM d.date) as year,
    EXTRACT(MONTH FROM d.date) as month,
    FORMAT_DATE('%Y-%m', d.date) as year_month,
    
    -- All tariff rates for this date
    t.tnuos_gbp_site_day,
    f.fit_p_per_kwh,
    r.ro_p_per_kwh,
    b.bsuos_gbp_per_mwh,
    c.ccl_gbp_per_kwh,
    
    -- Total cost per MWh (discharge)
    COALESCE(f.fit_p_per_kwh * 10, 0) +
    COALESCE(r.ro_p_per_kwh * 10, 0) +
    COALESCE(b.bsuos_gbp_per_mwh, 0) +
    COALESCE(c.ccl_gbp_per_kwh * 1000, 0) as total_discharge_cost_gbp_per_mwh,
    
    -- Source years
    t.tnuos_year,
    f.fit_year,
    r.ro_year,
    b.bsuos_tariff,
    c.ccl_year

FROM date_spine d
LEFT JOIN tnuos_by_date t ON d.date = t.date
LEFT JOIN fit_by_date f ON d.date = f.date
LEFT JOIN ro_by_date r ON d.date = r.date
LEFT JOIN bsuos_by_date b ON d.date = b.date
LEFT JOIN ccl_by_date c ON d.date = c.date;


-- ============================================================================
-- Test Queries
-- ============================================================================

-- Get current tariff rates
-- SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.vw_current_tariffs`;

-- Get battery arbitrage costs
-- SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.vw_battery_arbitrage_costs`;

-- Get historical rates for specific date
-- SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.vw_tariff_rates_by_date`
-- WHERE date = '2024-10-01';

-- Get tariff cost trend over time (monthly average)
-- SELECT 
--     year_month,
--     AVG(total_discharge_cost_gbp_per_mwh) as avg_discharge_cost
-- FROM `inner-cinema-476211-u9.uk_energy_prod.vw_tariff_rates_by_date`
-- WHERE date >= '2020-01-01'
-- GROUP BY year_month
-- ORDER BY year_month;
