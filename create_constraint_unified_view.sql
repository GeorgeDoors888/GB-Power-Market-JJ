-- Unified NESO Constraint Breakdown View
-- Combines all FY tables with robust date handling (handles both DATE and DATETIME strings)

CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.v_neso_constraints_unified` AS

SELECT
  CAST(SUBSTR(Date, 1, 10) AS DATE) as constraint_date,
  EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as year,
  EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as month,
  EXTRACT(QUARTER FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as quarter,

  CASE
    WHEN EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) >= 4
    THEN EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE))
    ELSE EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) - 1
  END as financial_year,

  CAST(`Thermal constraints cost` AS FLOAT64) as thermal_cost_gbp,
  CAST(`Voltage constraints cost` AS FLOAT64) as voltage_cost_gbp,
  CAST(`Reducing largest loss cost` AS FLOAT64) as largest_loss_cost_gbp,
  CAST(`Increasing system inertia cost` AS FLOAT64) as inertia_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) as thermal_volume_mwh,
  CAST(`Voltage constraints volume` AS FLOAT64) as voltage_volume_mwh,
  CAST(`Reducing largest loss volume` AS FLOAT64) as largest_loss_volume_mwh,
  CAST(`Increasing system inertia volume` AS FLOAT64) as inertia_volume_mwh,

  CAST(`Thermal constraints cost` AS FLOAT64) +
  CAST(`Voltage constraints cost` AS FLOAT64) +
  CAST(`Reducing largest loss cost` AS FLOAT64) +
  CAST(`Increasing system inertia cost` AS FLOAT64) as total_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) +
  CAST(`Voltage constraints volume` AS FLOAT64) +
  CAST(`Reducing largest loss volume` AS FLOAT64) +
  CAST(`Increasing system inertia volume` AS FLOAT64) as total_volume_mwh,

  'FY2017-2018' as source_table
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_constraint_breakdown_2017_2018`
UNION ALL

SELECT
  CAST(SUBSTR(Date, 1, 10) AS DATE) as constraint_date,
  EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as year,
  EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as month,
  EXTRACT(QUARTER FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as quarter,

  CASE
    WHEN EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) >= 4
    THEN EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE))
    ELSE EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) - 1
  END as financial_year,

  CAST(`Thermal constraints cost` AS FLOAT64) as thermal_cost_gbp,
  CAST(`Voltage constraints cost` AS FLOAT64) as voltage_cost_gbp,
  CAST(`Reducing largest loss cost` AS FLOAT64) as largest_loss_cost_gbp,
  CAST(`Increasing system inertia cost` AS FLOAT64) as inertia_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) as thermal_volume_mwh,
  CAST(`Voltage constraints volume` AS FLOAT64) as voltage_volume_mwh,
  CAST(`Reducing largest loss volume` AS FLOAT64) as largest_loss_volume_mwh,
  CAST(`Increasing system inertia volume` AS FLOAT64) as inertia_volume_mwh,

  CAST(`Thermal constraints cost` AS FLOAT64) +
  CAST(`Voltage constraints cost` AS FLOAT64) +
  CAST(`Reducing largest loss cost` AS FLOAT64) +
  CAST(`Increasing system inertia cost` AS FLOAT64) as total_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) +
  CAST(`Voltage constraints volume` AS FLOAT64) +
  CAST(`Reducing largest loss volume` AS FLOAT64) +
  CAST(`Increasing system inertia volume` AS FLOAT64) as total_volume_mwh,

  'FY2018-2019' as source_table
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_constraint_breakdown_2018_2019`
UNION ALL

SELECT
  CAST(SUBSTR(Date, 1, 10) AS DATE) as constraint_date,
  EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as year,
  EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as month,
  EXTRACT(QUARTER FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as quarter,

  CASE
    WHEN EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) >= 4
    THEN EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE))
    ELSE EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) - 1
  END as financial_year,

  CAST(`Thermal constraints cost` AS FLOAT64) as thermal_cost_gbp,
  CAST(`Voltage constraints cost` AS FLOAT64) as voltage_cost_gbp,
  CAST(`Reducing largest loss cost` AS FLOAT64) as largest_loss_cost_gbp,
  CAST(`Increasing system inertia cost` AS FLOAT64) as inertia_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) as thermal_volume_mwh,
  CAST(`Voltage constraints volume` AS FLOAT64) as voltage_volume_mwh,
  CAST(`Reducing largest loss volume` AS FLOAT64) as largest_loss_volume_mwh,
  CAST(`Increasing system inertia volume` AS FLOAT64) as inertia_volume_mwh,

  CAST(`Thermal constraints cost` AS FLOAT64) +
  CAST(`Voltage constraints cost` AS FLOAT64) +
  CAST(`Reducing largest loss cost` AS FLOAT64) +
  CAST(`Increasing system inertia cost` AS FLOAT64) as total_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) +
  CAST(`Voltage constraints volume` AS FLOAT64) +
  CAST(`Reducing largest loss volume` AS FLOAT64) +
  CAST(`Increasing system inertia volume` AS FLOAT64) as total_volume_mwh,

  'FY2019-2020' as source_table
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_constraint_breakdown_2019_2020`
UNION ALL

SELECT
  CAST(SUBSTR(Date, 1, 10) AS DATE) as constraint_date,
  EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as year,
  EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as month,
  EXTRACT(QUARTER FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as quarter,

  CASE
    WHEN EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) >= 4
    THEN EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE))
    ELSE EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) - 1
  END as financial_year,

  CAST(`Thermal constraints cost` AS FLOAT64) as thermal_cost_gbp,
  CAST(`Voltage constraints cost` AS FLOAT64) as voltage_cost_gbp,
  CAST(`Reducing largest loss cost` AS FLOAT64) as largest_loss_cost_gbp,
  CAST(`Increasing system inertia cost` AS FLOAT64) as inertia_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) as thermal_volume_mwh,
  CAST(`Voltage constraints volume` AS FLOAT64) as voltage_volume_mwh,
  CAST(`Reducing largest loss volume` AS FLOAT64) as largest_loss_volume_mwh,
  CAST(`Increasing system inertia volume` AS FLOAT64) as inertia_volume_mwh,

  CAST(`Thermal constraints cost` AS FLOAT64) +
  CAST(`Voltage constraints cost` AS FLOAT64) +
  CAST(`Reducing largest loss cost` AS FLOAT64) +
  CAST(`Increasing system inertia cost` AS FLOAT64) as total_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) +
  CAST(`Voltage constraints volume` AS FLOAT64) +
  CAST(`Reducing largest loss volume` AS FLOAT64) +
  CAST(`Increasing system inertia volume` AS FLOAT64) as total_volume_mwh,

  'FY2020-2021' as source_table
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_constraint_breakdown_2020_2021`
UNION ALL

SELECT
  CAST(SUBSTR(Date, 1, 10) AS DATE) as constraint_date,
  EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as year,
  EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as month,
  EXTRACT(QUARTER FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as quarter,

  CASE
    WHEN EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) >= 4
    THEN EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE))
    ELSE EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) - 1
  END as financial_year,

  CAST(`Thermal constraints cost` AS FLOAT64) as thermal_cost_gbp,
  CAST(`Voltage constraints cost` AS FLOAT64) as voltage_cost_gbp,
  CAST(`Reducing largest loss cost` AS FLOAT64) as largest_loss_cost_gbp,
  CAST(`Increasing system inertia cost` AS FLOAT64) as inertia_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) as thermal_volume_mwh,
  CAST(`Voltage constraints volume` AS FLOAT64) as voltage_volume_mwh,
  CAST(`Reducing largest loss volume` AS FLOAT64) as largest_loss_volume_mwh,
  CAST(`Increasing system inertia volume` AS FLOAT64) as inertia_volume_mwh,

  CAST(`Thermal constraints cost` AS FLOAT64) +
  CAST(`Voltage constraints cost` AS FLOAT64) +
  CAST(`Reducing largest loss cost` AS FLOAT64) +
  CAST(`Increasing system inertia cost` AS FLOAT64) as total_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) +
  CAST(`Voltage constraints volume` AS FLOAT64) +
  CAST(`Reducing largest loss volume` AS FLOAT64) +
  CAST(`Increasing system inertia volume` AS FLOAT64) as total_volume_mwh,

  'FY2021-2022' as source_table
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_constraint_breakdown_2021_2022`
UNION ALL

SELECT
  CAST(SUBSTR(Date, 1, 10) AS DATE) as constraint_date,
  EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as year,
  EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as month,
  EXTRACT(QUARTER FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as quarter,

  CASE
    WHEN EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) >= 4
    THEN EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE))
    ELSE EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) - 1
  END as financial_year,

  CAST(`Thermal constraints cost` AS FLOAT64) as thermal_cost_gbp,
  CAST(`Voltage constraints cost` AS FLOAT64) as voltage_cost_gbp,
  CAST(`Reducing largest loss cost` AS FLOAT64) as largest_loss_cost_gbp,
  CAST(`Increasing system inertia cost` AS FLOAT64) as inertia_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) as thermal_volume_mwh,
  CAST(`Voltage constraints volume` AS FLOAT64) as voltage_volume_mwh,
  CAST(`Reducing largest loss volume` AS FLOAT64) as largest_loss_volume_mwh,
  CAST(`Increasing system inertia volume` AS FLOAT64) as inertia_volume_mwh,

  CAST(`Thermal constraints cost` AS FLOAT64) +
  CAST(`Voltage constraints cost` AS FLOAT64) +
  CAST(`Reducing largest loss cost` AS FLOAT64) +
  CAST(`Increasing system inertia cost` AS FLOAT64) as total_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) +
  CAST(`Voltage constraints volume` AS FLOAT64) +
  CAST(`Reducing largest loss volume` AS FLOAT64) +
  CAST(`Increasing system inertia volume` AS FLOAT64) as total_volume_mwh,

  'FY2022-2023' as source_table
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_constraint_breakdown_2022_2023`
UNION ALL

SELECT
  CAST(SUBSTR(Date, 1, 10) AS DATE) as constraint_date,
  EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as year,
  EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as month,
  EXTRACT(QUARTER FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as quarter,

  CASE
    WHEN EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) >= 4
    THEN EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE))
    ELSE EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) - 1
  END as financial_year,

  CAST(`Thermal constraints cost` AS FLOAT64) as thermal_cost_gbp,
  CAST(`Voltage constraints cost` AS FLOAT64) as voltage_cost_gbp,
  CAST(`Reducing largest loss cost` AS FLOAT64) as largest_loss_cost_gbp,
  CAST(`Increasing system inertia cost` AS FLOAT64) as inertia_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) as thermal_volume_mwh,
  CAST(`Voltage constraints volume` AS FLOAT64) as voltage_volume_mwh,
  CAST(`Reducing largest loss volume` AS FLOAT64) as largest_loss_volume_mwh,
  CAST(`Increasing system inertia volume` AS FLOAT64) as inertia_volume_mwh,

  CAST(`Thermal constraints cost` AS FLOAT64) +
  CAST(`Voltage constraints cost` AS FLOAT64) +
  CAST(`Reducing largest loss cost` AS FLOAT64) +
  CAST(`Increasing system inertia cost` AS FLOAT64) as total_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) +
  CAST(`Voltage constraints volume` AS FLOAT64) +
  CAST(`Reducing largest loss volume` AS FLOAT64) +
  CAST(`Increasing system inertia volume` AS FLOAT64) as total_volume_mwh,

  'FY2023-2024' as source_table
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_constraint_breakdown_2023_2024`
UNION ALL

SELECT
  CAST(SUBSTR(Date, 1, 10) AS DATE) as constraint_date,
  EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as year,
  EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as month,
  EXTRACT(QUARTER FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as quarter,

  CASE
    WHEN EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) >= 4
    THEN EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE))
    ELSE EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) - 1
  END as financial_year,

  CAST(`Thermal constraints cost` AS FLOAT64) as thermal_cost_gbp,
  CAST(`Voltage constraints cost` AS FLOAT64) as voltage_cost_gbp,
  CAST(`Reducing largest loss cost` AS FLOAT64) as largest_loss_cost_gbp,
  CAST(`Increasing system inertia cost` AS FLOAT64) as inertia_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) as thermal_volume_mwh,
  CAST(`Voltage constraints volume` AS FLOAT64) as voltage_volume_mwh,
  CAST(`Reducing largest loss volume` AS FLOAT64) as largest_loss_volume_mwh,
  CAST(`Increasing system inertia volume` AS FLOAT64) as inertia_volume_mwh,

  CAST(`Thermal constraints cost` AS FLOAT64) +
  CAST(`Voltage constraints cost` AS FLOAT64) +
  CAST(`Reducing largest loss cost` AS FLOAT64) +
  CAST(`Increasing system inertia cost` AS FLOAT64) as total_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) +
  CAST(`Voltage constraints volume` AS FLOAT64) +
  CAST(`Reducing largest loss volume` AS FLOAT64) +
  CAST(`Increasing system inertia volume` AS FLOAT64) as total_volume_mwh,

  'FY2024-2025' as source_table
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_constraint_breakdown_2024_2025`
UNION ALL

SELECT
  CAST(SUBSTR(Date, 1, 10) AS DATE) as constraint_date,
  EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as year,
  EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as month,
  EXTRACT(QUARTER FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) as quarter,

  CASE
    WHEN EXTRACT(MONTH FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) >= 4
    THEN EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE))
    ELSE EXTRACT(YEAR FROM CAST(SUBSTR(Date, 1, 10) AS DATE)) - 1
  END as financial_year,

  CAST(`Thermal constraints cost` AS FLOAT64) as thermal_cost_gbp,
  CAST(`Voltage constraints cost` AS FLOAT64) as voltage_cost_gbp,
  CAST(`Reducing largest loss cost` AS FLOAT64) as largest_loss_cost_gbp,
  CAST(`Increasing system inertia cost` AS FLOAT64) as inertia_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) as thermal_volume_mwh,
  CAST(`Voltage constraints volume` AS FLOAT64) as voltage_volume_mwh,
  CAST(`Reducing largest loss volume` AS FLOAT64) as largest_loss_volume_mwh,
  CAST(`Increasing system inertia volume` AS FLOAT64) as inertia_volume_mwh,

  CAST(`Thermal constraints cost` AS FLOAT64) +
  CAST(`Voltage constraints cost` AS FLOAT64) +
  CAST(`Reducing largest loss cost` AS FLOAT64) +
  CAST(`Increasing system inertia cost` AS FLOAT64) as total_cost_gbp,

  CAST(`Thermal constraints volume` AS FLOAT64) +
  CAST(`Voltage constraints volume` AS FLOAT64) +
  CAST(`Reducing largest loss volume` AS FLOAT64) +
  CAST(`Increasing system inertia volume` AS FLOAT64) as total_volume_mwh,

  'FY2025-2026' as source_table
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_constraint_breakdown_2025_2026`;
