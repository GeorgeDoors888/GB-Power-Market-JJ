-- Create view to map Settlement Periods (1-48) to DUoS charges by DNO
-- This enables battery arbitrage analysis with full network cost visibility

-- View 1: Map each SP to its DUoS time band (Red/Amber/Green) for each DNO
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.gb_power.vw_duos_sp_time_bands` AS
WITH sp_numbers AS (
  -- Generate all 48 settlement periods
  SELECT sp
  FROM UNNEST(GENERATE_ARRAY(1, 48)) AS sp
),
sp_times AS (
  -- Map SP to actual time
  SELECT 
    sp,
    TIME(EXTRACT(HOUR FROM TIMESTAMP_SECONDS((sp - 1) * 1800)), 
         EXTRACT(MINUTE FROM TIMESTAMP_SECONDS((sp - 1) * 1800)), 0) as sp_start_time,
    TIME(EXTRACT(HOUR FROM TIMESTAMP_SECONDS(sp * 1800)), 
         EXTRACT(MINUTE FROM TIMESTAMP_SECONDS(sp * 1800)), 0) as sp_end_time
  FROM sp_numbers
),
dno_sp_bands AS (
  -- For each DNO, map each SP to its time band
  SELECT 
    tb.dno_key,
    sp.sp,
    sp.sp_start_time,
    tb.time_band_name,
    tb.time_band_type,
    tb.season,
    tb.day_type,
    tb.start_time,
    tb.end_time,
    tb.start_month,
    tb.end_month
  FROM `inner-cinema-476211-u9.gb_power.duos_time_bands` tb
  CROSS JOIN sp_times sp
  WHERE sp.sp BETWEEN tb.start_settlement_period AND tb.end_settlement_period
)
SELECT DISTINCT
  dno_key,
  sp,
  sp_start_time,
  time_band_name as duos_band,  -- Red, Amber, or Green
  season,
  day_type,
  start_month,
  end_month
FROM dno_sp_bands
ORDER BY dno_key, sp;


-- View 2: Get DUoS charges (p/kWh) for each SP by DNO and voltage level
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.gb_power.vw_duos_charges_by_sp` AS
WITH sp_bands AS (
  SELECT * FROM `inner-cinema-476211-u9.gb_power.vw_duos_sp_time_bands`
),
current_rates AS (
  -- Get latest applicable rates
  SELECT 
    dno_key,
    time_band_name,
    voltage_level,
    unit_rate_p_kwh,
    fixed_charge_p_mpan_day,
    capacity_charge_p_kva_day,
    effective_from,
    effective_to
  FROM `inner-cinema-476211-u9.gb_power.duos_unit_rates`
  WHERE effective_to >= CURRENT_DATE()
)
SELECT 
  sb.dno_key,
  sb.sp,
  sb.sp_start_time,
  sb.duos_band,
  sb.season,
  sb.day_type,
  r.voltage_level,
  r.unit_rate_p_kwh as duos_p_per_kwh,
  r.unit_rate_p_kwh * 10 as duos_gbp_per_mwh,  -- Convert to £/MWh
  r.fixed_charge_p_mpan_day,
  r.capacity_charge_p_kva_day,
  CASE sb.duos_band
    WHEN 'Red' THEN 1
    WHEN 'Amber' THEN 2
    WHEN 'Green' THEN 3
    ELSE 4
  END as band_priority,
  r.effective_from,
  r.effective_to
FROM sp_bands sb
LEFT JOIN current_rates r
  ON sb.dno_key = r.dno_key
  AND sb.duos_band = r.time_band_name
ORDER BY sb.dno_key, sb.sp, r.voltage_level;


-- View 3: Complete battery arbitrage cost calculation with DUoS
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.gb_power.vw_battery_costs_with_duos` AS
WITH tariff_costs AS (
  -- Get the latest tariff costs (FiT, RO, BSUoS, CCL)
  SELECT 
    fit_p_per_kwh * 10 as fit_gbp_per_mwh,
    ro_p_per_kwh * 10 as ro_gbp_per_mwh,
    bsuos_gbp_per_mwh,
    ccl_gbp_per_kwh * 1000 as ccl_gbp_per_mwh,
    (fit_p_per_kwh * 10) + (ro_p_per_kwh * 10) + bsuos_gbp_per_mwh + (ccl_gbp_per_kwh * 1000) as total_discharge_tariffs_gbp_per_mwh,
    bsuos_gbp_per_mwh as total_charge_tariffs_gbp_per_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.vw_battery_arbitrage_costs`
  LIMIT 1
),
duos_by_sp_lv AS (
  -- Get LV DUoS charges for each SP (most common for batteries)
  SELECT 
    dno_key,
    sp,
    duos_band,
    duos_gbp_per_mwh,
    season,
    day_type
  FROM `inner-cinema-476211-u9.gb_power.vw_duos_charges_by_sp`
  WHERE voltage_level = 'LV'
)
SELECT 
  d.dno_key,
  d.sp,
  d.sp_start_time,
  d.duos_band,
  d.season,
  d.day_type,
  
  -- DUoS charges
  d.duos_gbp_per_mwh as duos_charge_gbp_per_mwh,
  d.duos_gbp_per_mwh as duos_discharge_gbp_per_mwh,
  
  -- Tariff charges (from national schemes)
  t.fit_gbp_per_mwh,
  t.ro_gbp_per_mwh,
  t.bsuos_gbp_per_mwh,
  t.ccl_gbp_per_mwh,
  
  -- Total discharge costs (sell to grid)
  d.duos_gbp_per_mwh + t.total_discharge_tariffs_gbp_per_mwh as total_discharge_cost_gbp_per_mwh,
  
  -- Total charge costs (buy from grid)
  d.duos_gbp_per_mwh + t.total_charge_tariffs_gbp_per_mwh as total_charge_cost_gbp_per_mwh,
  
  -- Full cycle cost (charge + discharge)
  (d.duos_gbp_per_mwh * 2) + t.total_discharge_tariffs_gbp_per_mwh + t.total_charge_tariffs_gbp_per_mwh as total_cycle_cost_gbp_per_mwh,
  
  -- Cost breakdown percentages
  ROUND(d.duos_gbp_per_mwh / NULLIF((d.duos_gbp_per_mwh * 2) + t.total_discharge_tariffs_gbp_per_mwh + t.total_charge_tariffs_gbp_per_mwh, 0) * 100, 1) as duos_pct_of_total,
  ROUND(t.total_discharge_tariffs_gbp_per_mwh / NULLIF((d.duos_gbp_per_mwh * 2) + t.total_discharge_tariffs_gbp_per_mwh + t.total_charge_tariffs_gbp_per_mwh, 0) * 100, 1) as tariffs_pct_of_total

FROM duos_by_sp_lv d
CROSS JOIN tariff_costs t
ORDER BY d.dno_key, d.sp;


-- View 4: DNO Reference with License IDs
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.gb_power.vw_dno_license_reference` AS
SELECT 
  'UKPN_EPN' as dno_key,
  'C5' as license_id,
  'UK Power Networks - Eastern' as dno_name,
  'Eastern England' as region
UNION ALL SELECT 'UKPN_LPN', 'C6', 'UK Power Networks - London', 'London'
UNION ALL SELECT 'UKPN_SPN', 'C7', 'UK Power Networks - South Eastern', 'South East England'
UNION ALL SELECT 'NGED_EM', 'C8', 'National Grid ED - East Midlands', 'East Midlands'
UNION ALL SELECT 'NGED_WM', 'C9', 'National Grid ED - West Midlands', 'West Midlands'
UNION ALL SELECT 'NGED_SW', 'C10', 'National Grid ED - South West', 'South West England'
UNION ALL SELECT 'NGED_SWALES', 'C11', 'National Grid ED - South Wales', 'South Wales'
UNION ALL SELECT 'SSEN_SEPD', 'C12', 'SSE - Southern Electric', 'South England'
UNION ALL SELECT 'SSEN_SHEPD', 'C13', 'SSE - Scottish Hydro', 'North Scotland'
UNION ALL SELECT 'NPG_NORT', 'C14', 'Northern Powergrid - North East', 'North East England'
UNION ALL SELECT 'NPG_YORK', 'C15', 'Northern Powergrid - Yorkshire', 'Yorkshire'
UNION ALL SELECT 'ENWL', 'C16', 'Electricity North West', 'North West England'
UNION ALL SELECT 'SPEN_SPD', 'C17', 'SP Energy Networks - SP Distribution', 'Central Scotland'
UNION ALL SELECT 'SPEN_MANWEB', 'C18', 'SP Energy Networks - Manweb', 'North Wales & Merseyside';
