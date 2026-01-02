# Data Schema Reference - Weather & Yield Drop Analysis
**Created**: January 2, 2026  
**Purpose**: Schema documentation for ERA5 weather data and wind yield drop analysis

---

## 📊 ERA5_WEATHER_DATA_COMPLETE

### Table Information
- **Table ID**: `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_complete`
- **Type**: BigQuery table (partitioned by DATE(timestamp))
- **Rows**: ~1,348,464 observations
- **Coverage**: 21 offshore wind farms, 2020-01-01 to 2025-11-30
- **Purpose**: Historic weather data with gust + pressure (backfilled Jan 1, 2026)

### Schema (11 columns)

| Column Name | Data Type | Mode | Description | Unit |
|-------------|-----------|------|-------------|------|
| **farm_name** | STRING | REQUIRED | Wind farm name | - |
| **timestamp** | TIMESTAMP | REQUIRED | Observation time (UTC) | ISO 8601 |
| **wind_speed_100m_kmh** | FLOAT64 | NULLABLE | Wind speed at 100m hub height | km/h |
| **wind_speed_100m_ms** | FLOAT64 | NULLABLE | Wind speed at 100m hub height | m/s |
| **wind_gusts_10m_kmh** | FLOAT64 | NULLABLE | Wind gusts at 10m | km/h |
| **wind_gusts_10m_ms** | FLOAT64 | NULLABLE | Wind gusts at 10m | m/s |
| **surface_pressure_hpa** | FLOAT64 | NULLABLE | Surface atmospheric pressure | hPa |
| **temperature_2m_c** | FLOAT64 | NULLABLE | Air temperature at 2m | °C |
| **relative_humidity_2m_pct** | FLOAT64 | NULLABLE | Relative humidity at 2m | % |
| **precipitation_mm** | FLOAT64 | NULLABLE | Total precipitation | mm |
| **wind_direction_100m_deg** | FLOAT64 | NULLABLE | Wind direction at 100m | degrees |

### Derived Metrics (Calculated in Queries)

| Metric | Formula | Purpose |
|--------|---------|---------|
| **Dew Point** | `Td = T - ((100-RH)/5)` | Icing risk indicator |
| **Dew Point Spread** | `T - Td` | Small spread (≤2°C) = high icing risk |
| **Gust Factor** | `wind_gusts_10m_ms / wind_speed_100m_ms` | Turbulence detection (>1.4 = high) |
| **Pressure Change** | `surface_pressure - LAG(surface_pressure, 3)` | Upstream signal (±3-5 hPa/3h) |
| **Wind Speed m/s** | `wind_speed_100m_kmh / 3.6` | Conversion (already in table) |

### Sample Query
```sql
SELECT 
    farm_name,
    timestamp,
    wind_speed_100m_ms,
    wind_gusts_10m_ms,
    surface_pressure_hpa,
    temperature_2m_c,
    relative_humidity_2m_pct,
    -- Derived metrics
    temperature_2m_c - ((100 - relative_humidity_2m_pct) / 5) as dew_point_c,
    temperature_2m_c - (temperature_2m_c - ((100 - relative_humidity_2m_pct) / 5)) as dew_point_spread,
    wind_gusts_10m_ms / NULLIF(wind_speed_100m_ms, 0) as gust_factor
FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_complete`
WHERE farm_name = 'Hornsea One'
  AND DATE(timestamp) >= '2025-01-01'
ORDER BY timestamp
```

---

## 📉 WIND YIELD DROP ANALYSIS DATA

### Source
- **NOT a dedicated table** - Analysis computed on-demand from multiple sources
- **Output**: CSV file `wave_weather_generation_combined.csv` or `wind_yield_drops_analysis.csv`
- **Script**: `analyze_wind_yield_drops_upstream.py`

### Data Sources (Joined)

1. **bmrs_pn** (Physical Notifications - Actual Generation)
   - `bmUnit` - BM unit ID (e.g., 'T_HOWAO-1')
   - `settlementDate` - Settlement date
   - `settlementPeriod` - 1-48 (30-min periods)
   - `levelTo` - MW generation level

2. **era5_weather_data_complete** (Weather Conditions)
   - All columns listed above
   - Matched to wind farm location + timestamp

3. **cmems_waves_uk_grid** (Wave Data)
   - `sig_wave_height_m` - Significant wave height
   - Matched to farm location + time

### Analysis Output Schema

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| **farm_name** | STRING | Wind farm name | 'Hornsea One' |
| **month** | STRING | Month identifier | '2024-10' |
| **hour** | INTEGER | Hour of day (0-23) | 15 |
| **timestamp** | TIMESTAMP | Observation time | '2024-10-17 15:00:00' |
| **capacity_factor_pct** | FLOAT | Capacity factor | 32.5 |
| **prev_cf** | FLOAT | Previous hour CF | 43.6 |
| **cf_change** | FLOAT | CF change (drop) | -11.1 |
| **wind_speed_100m_ms** | FLOAT | Current wind speed | 8.2 |
| **prev_wind** | FLOAT | Previous wind speed | 12.5 |
| **wind_change** | FLOAT | Wind change | -4.3 |
| **temperature_2m_c** | FLOAT | Temperature | 12.5 |
| **prev_temp** | FLOAT | Previous temp | 12.8 |
| **temp_change** | FLOAT | Temp change | -0.3 |
| **humidity_pct** | FLOAT | Relative humidity | 78.0 |
| **prev_humidity** | FLOAT | Previous humidity | 82.0 |
| **humidity_change** | FLOAT | Humidity change | -4.0 |
| **sig_wave_height_m** | FLOAT | Wave height | 1.8 |
| **prev_wave** | FLOAT | Previous wave height | 2.1 |
| **wave_change** | FLOAT | Wave change | -0.3 |
| **drop_category** | STRING | Cause classification | 'Calm Arrival' |

### Drop Categories (Classified)

| Category | Criteria | Description |
|----------|----------|-------------|
| **Storm Curtailment** | `wind_change > 5` AND `wind_speed > 25` | Wind exceeded cut-out speed |
| **Calm Arrival** | `wind_change < -5` AND `wind_speed < 20` | Wind dropped below optimal |
| **Turbulence/Transients** | `wind_change` varies AND `gust_factor > 1.4` | High turbulence, unstable flow |
| **Direction Shift** | `wind_speed` stable AND `direction_change > 30°` | Wind direction change (turbine yaw lag) |
| **Other/Mixed** | None of above | Complex interactions or unknown |

### Key Statistics from Analysis

**542 significant yield drops analyzed** (>5% CF decrease):
- **Calm Arrival**: 20% (108 events) - Wind drops 20-35 m/s → High pressure
- **Turbulence/Transients**: 21% (114 events) - Rapid fluctuations, frontal passages
- **Storm Curtailment**: 10% (54 events) - Wind exceeds 25 m/s cut-out
- **Direction Shift**: 4% (22 events) - Wind direction change, speed stable
- **Other/Mixed**: 45% (244 events) - Complex weather interactions

**Critical Finding**: 78% of drops caused by wind **DECREASING**, not increasing (storm curtailment only 10%)

---

## 🔗 JOINING WEATHER TO GENERATION DATA

### Standard Join Pattern

```sql
-- Join weather to wind generation
WITH generation AS (
  SELECT 
    bmUnit,
    TIMESTAMP(CONCAT(CAST(settlementDate AS STRING), ' ', 
      FORMAT('%02d', (settlementPeriod - 1) DIV 2), ':', 
      FORMAT('%02d', ((settlementPeriod - 1) MOD 2) * 30), ':00')) as gen_timestamp,
    levelTo as generation_mw
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_pn`
  WHERE bmUnit IN ('T_HOWAO-1', 'T_HOWAO-2')  -- Hornsea One
),

weather AS (
  SELECT 
    farm_name,
    timestamp as weather_timestamp,
    wind_speed_100m_ms,
    wind_gusts_10m_ms,
    surface_pressure_hpa,
    temperature_2m_c
  FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_complete`
  WHERE farm_name = 'Hornsea One'
)

SELECT 
  g.bmUnit,
  g.gen_timestamp,
  g.generation_mw,
  w.wind_speed_100m_ms,
  w.wind_gusts_10m_ms,
  w.surface_pressure_hpa
FROM generation g
LEFT JOIN weather w
  ON TIMESTAMP_DIFF(g.gen_timestamp, w.weather_timestamp, MINUTE) BETWEEN -30 AND 30
ORDER BY g.gen_timestamp
```

### Farm Name to BM Unit Mapping

Use `wind_farm_to_bmu` table:
```sql
SELECT 
  farm_name,
  bmu_id,
  capacity_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.wind_farm_to_bmu`
WHERE farm_name = 'Hornsea One'
```

---

## 🎯 ICING RISK ANALYSIS SCHEMA

### Proposed Table: `wind_icing_risk_events`

| Column | Type | Description |
|--------|------|-------------|
| **farm_name** | STRING | Wind farm |
| **timestamp** | TIMESTAMP | Event timestamp |
| **icing_risk_level** | STRING | 'HIGH', 'MEDIUM', 'LOW' |
| **temperature_c** | FLOAT | Air temperature |
| **dew_point_c** | FLOAT | Dew point temperature |
| **dew_point_spread** | FLOAT | T - Td (°C) |
| **wind_speed_ms** | FLOAT | Wind speed |
| **gust_factor** | FLOAT | Gust/wind ratio |
| **blade_tip_speed_ms** | FLOAT | Estimated (60-90 m/s) |
| **pressure_drop_3h** | FLOAT | hPa change (3h) |
| **predicted_ice** | BOOLEAN | Model prediction |

### Icing Risk Classification Query

```sql
CREATE OR REPLACE VIEW wind_icing_risk AS
SELECT 
    farm_name,
    timestamp,
    temperature_2m_c,
    temperature_2m_c - ((100 - relative_humidity_2m_pct) / 5) as dew_point_c,
    temperature_2m_c - (temperature_2m_c - ((100 - relative_humidity_2m_pct) / 5)) as dew_point_spread,
    wind_speed_100m_ms,
    wind_gusts_10m_ms / NULLIF(wind_speed_100m_ms, 0) as gust_factor,
    surface_pressure_hpa - LAG(surface_pressure_hpa) OVER (
        PARTITION BY farm_name ORDER BY timestamp
    ) as pressure_change_1h,
    CASE 
        WHEN temperature_2m_c BETWEEN -10 AND 2
         AND (temperature_2m_c - ((100 - relative_humidity_2m_pct) / 5)) <= 2
         AND wind_speed_100m_ms BETWEEN 6 AND 12
         AND (wind_gusts_10m_ms / NULLIF(wind_speed_100m_ms, 0)) > 1.3
        THEN 'HIGH'
        WHEN temperature_2m_c BETWEEN -5 AND 5
         AND (temperature_2m_c - ((100 - relative_humidity_2m_pct) / 5)) <= 5
        THEN 'MEDIUM'
        ELSE 'LOW'
    END AS icing_risk_level
FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_complete`
WHERE temperature_2m_c < 10  -- Only relevant in cold conditions
```

---

## 🌊 UPSTREAM WEATHER PROPAGATION SCHEMA

### Proposed Table: `upstream_weather_signals`

| Column | Type | Description |
|--------|------|-------------|
| **downstream_farm** | STRING | Target farm (east) |
| **upstream_farm** | STRING | Signal source (west) |
| **distance_km** | FLOAT | Farm separation |
| **signal_timestamp** | TIMESTAMP | Signal detection time |
| **signal_type** | STRING | 'PRESSURE_DROP', 'PRESSURE_RISE', 'TEMP_CHANGE' |
| **signal_magnitude** | FLOAT | Change magnitude |
| **propagation_time_hours** | FLOAT | Measured lead time |
| **actual_impact** | BOOLEAN | Did downstream farm see impact? |
| **impact_timestamp** | TIMESTAMP | When impact occurred |

### Upstream Tracking Query

```sql
-- Find upstream farms (50-150km west) and track pressure changes
WITH farm_pairs AS (
  SELECT 
    f1.name as downstream_farm,
    f2.name as upstream_farm,
    ST_DISTANCE(
      ST_GEOGPOINT(f1.longitude, f1.latitude),
      ST_GEOGPOINT(f2.longitude, f2.latitude)
    ) / 1000 as distance_km
  FROM `inner-cinema-476211-u9.uk_energy_prod.offshore_wind_farms` f1
  CROSS JOIN `inner-cinema-476211-u9.uk_energy_prod.offshore_wind_farms` f2
  WHERE f2.longitude < f1.longitude  -- Upstream (west)
    AND ST_DISTANCE(
      ST_GEOGPOINT(f1.longitude, f1.latitude),
      ST_GEOGPOINT(f2.longitude, f2.latitude)
    ) / 1000 BETWEEN 50 AND 150
),

pressure_changes AS (
  SELECT 
    farm_name,
    timestamp,
    surface_pressure_hpa,
    surface_pressure_hpa - LAG(surface_pressure_hpa, 3) OVER (
        PARTITION BY farm_name ORDER BY timestamp
    ) as pressure_change_3h
  FROM `inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_complete`
)

SELECT 
    p.upstream_farm,
    p.downstream_farm,
    p.distance_km,
    up.timestamp as upstream_time,
    up.pressure_change_3h as upstream_pressure_change,
    down.timestamp as downstream_time,
    down.pressure_change_3h as downstream_pressure_change,
    TIMESTAMP_DIFF(down.timestamp, up.timestamp, HOUR) as lead_time_hours
FROM farm_pairs p
JOIN pressure_changes up ON up.farm_name = p.upstream_farm
JOIN pressure_changes down ON down.farm_name = p.downstream_farm
WHERE ABS(up.pressure_change_3h) > 3  -- Significant pressure change
  AND ABS(down.pressure_change_3h) > 3
  AND TIMESTAMP_DIFF(down.timestamp, up.timestamp, HOUR) BETWEEN 1 AND 12
ORDER BY lead_time_hours
```

---

## 📋 TODO LIST IMPLEMENTATION

### Task 8: Add Icing Risk Analysis to Weather Data

**Implementation Steps**:

1. **Create Icing Risk View** (5 min)
   ```sql
   -- Run the CREATE OR REPLACE VIEW query above
   ```

2. **Validate High-Risk Periods** (10 min)
   ```python
   # Count high-risk events by farm
   query = """
   SELECT 
       farm_name,
       icing_risk_level,
       COUNT(*) as hours
   FROM wind_icing_risk
   GROUP BY farm_name, icing_risk_level
   ORDER BY farm_name, icing_risk_level
   """
   ```

3. **Correlate with Yield Drops** (20 min)
   - Join icing risk view with generation data
   - Identify yield drops during HIGH icing risk
   - Calculate accuracy (true positives, false positives)

4. **Update Documentation** (10 min)
   - Add icing risk section to WIND_YIELD_DROPS_UPSTREAM_ANALYSIS.md
   - Include sample queries and validation results

**Expected Output**:
- View: `wind_icing_risk` in BigQuery
- Report: Icing risk validation results
- Update: Documentation with icing analysis section

### Task 9: Add NESO Curtailment Data Integration

**Data Sources**:

1. **BOALF Acceptances** (already in BigQuery)
   - Table: `bmrs_boalf_complete` or `boalf_with_prices`
   - BID acceptances = turn-down instructions
   - Has acceptance prices + volumes

2. **REMIT Outages** (already collected)
   - Script: `update_unavailability.py`
   - Table: Manual updates to spreadsheet
   - Should create: `remit_outages` BigQuery table

3. **NESO Constraint Costs** (needs API integration)
   - Source: NESO Data Portal API
   - Endpoint: Constraint management data
   - Aggregate cost + volume by date

**Implementation Steps**:

1. **Create REMIT Outages Table** (15 min)
   ```python
   # Modify update_unavailability.py to also write to BigQuery
   # Schema: asset, start_time, end_time, capacity_mw, reason, message_type
   ```

2. **Add Constraint Cost Tracking** (30 min)
   ```python
   # New script: fetch_neso_constraint_costs.py
   # API: NESO Data Portal
   # Output: Table with daily constraint volumes + costs
   ```

3. **Join Curtailment Sources** (20 min)
   ```sql
   -- Unified curtailment view
   CREATE OR REPLACE VIEW wind_curtailment_unified AS
   SELECT ... FROM boalf_with_prices  -- BM instructions
   UNION ALL
   SELECT ... FROM remit_outages       -- Declared outages
   UNION ALL  
   SELECT ... FROM neso_constraints    -- System-wide constraints
   ```

4. **Update Spreadsheet Dashboard** (15 min)
   - Add curtailment section to Live Dashboard v2
   - Show: Daily curtailment MW, revenue lost, constraint costs
   - Cell range: Rows 70-75 (below wind forecast section)

**Expected Output**:
- Table: `remit_outages` in BigQuery
- Table: `neso_constraint_costs` in BigQuery
- View: `wind_curtailment_unified` in BigQuery
- Dashboard: Curtailment section in spreadsheet (rows 70-75)

---

## 🔗 RELATED DOCUMENTATION

- **Weather Pipeline**: `WEATHER_DATA_UPDATE_STRATEGY.md`
- **Cell Conflicts**: `SHEETS_CELL_CONFLICT_AUDIT.md`
- **Yield Analysis**: `WIND_YIELD_DROPS_UPSTREAM_ANALYSIS.md`
- **Project Config**: `PROJECT_CONFIGURATION.md`

---

**Last Updated**: January 2, 2026  
**Version**: 1.0
