# Weather Data Guide - GB Power Market JJ

**Author**: AI Coding Agent  
**Date**: December 30, 2025  
**Purpose**: Comprehensive reference for all weather data sources in the wind forecasting system

---

## 📊 Data Sources Overview

### 1. Open-Meteo Historical Wind (`openmeteo_wind_historic`)

**Source**: https://archive-api.open-meteo.com/v1/archive  
**Coverage**: 48 UK offshore wind farms, 2021-2025  
**Update Frequency**: Manual/on-demand  
**Records**: ~10.5M hourly observations

**Schema**:
```sql
CREATE TABLE openmeteo_wind_historic (
    settlementDate TIMESTAMP,
    farm_name STRING,
    latitude FLOAT64,
    longitude FLOAT64,
    generation FLOAT64,           -- Actual generation (MW) from BMRS B1610
    wind_speed_100m FLOAT64,      -- Wind speed at 100m hub height (m/s)
    wind_speed_10m FLOAT64,       -- Wind speed at 10m (m/s)
    wind_direction_10m FLOAT64,   -- Wind direction (0-360°)
    wind_gusts_10m FLOAT64,       -- Wind gusts at 10m (m/s)
    temperature_2m FLOAT64,       -- Air temperature at 2m (°C)
    relative_humidity_2m FLOAT64, -- Relative humidity (%)
    pressure_msl FLOAT64,         -- Mean sea level pressure (hPa)
    cloud_cover FLOAT64,          -- Cloud cover (0-100%)
    precipitation FLOAT64         -- Precipitation (mm)
)
```

**Key Features**:
- Hourly temporal resolution
- Hub height wind speed (100m) for power curve modeling
- Historical generation matched to weather conditions
- Full atmospheric variables for icing detection

**Usage Example**:
```sql
SELECT
    farm_name,
    settlementDate,
    wind_speed_100m,
    generation
FROM `inner-cinema-476211-u9.uk_energy_prod.openmeteo_wind_historic`
WHERE farm_name = 'Hornsea 1'
  AND DATE(settlementDate) = '2025-12-01'
ORDER BY settlementDate
```

---

### 2. Open-Meteo Real-Time Wind (`openmeteo_wind_realtime`)

**Source**: https://api.open-meteo.com/v1/forecast  
**Coverage**: 48 UK offshore wind farms  
**Update Frequency**: Every 15 minutes (automated via cron)  
**Records**: Rolling 48-hour window

**Schema**: Same as `openmeteo_wind_historic`

**Purpose**:
- Real-time forecasting input
- Ramp detection (>50 MW/h WARNING, >150 MW/h CRITICAL)
- Dashboard live updates
- Trading signals

**Automation**:
```bash
# Cron job: */15 * * * *
python3 download_realtime_wind.py
```

---

### 3. ERA5 Weather for Icing Detection (`era5_weather_icing`)

**Source**: Open-Meteo Archive API (ERA5 reanalysis data)  
**Coverage**: 48 UK offshore wind farms, 2021-2025  
**Update Frequency**: Daily (T-5 days lag, ERA5 publication schedule)  
**Records**: ~10.5M hourly observations (target)

**Schema**:
```sql
CREATE TABLE era5_weather_icing (
    time_utc TIMESTAMP,
    farm_name STRING,
    latitude FLOAT64,
    longitude FLOAT64,
    temperature_2m FLOAT64,        -- Air temperature (°C)
    relative_humidity_2m FLOAT64,  -- Relative humidity (%)
    precipitation FLOAT64,         -- Precipitation (mm)
    cloud_cover FLOAT64,           -- Cloud cover (%)
    pressure_msl FLOAT64,          -- Mean sea level pressure (hPa)
    shortwave_radiation FLOAT64    -- Solar radiation (W/m²)
)
```

**Icing Detection Thresholds**:
```python
icing_conditions = (
    (temperature_2m >= -3) & (temperature_2m <= 2) &  # Near-freezing
    (relative_humidity_2m > 92) &                      # High moisture
    (precipitation > 0) &                               # Active precipitation
    (month IN (11, 12, 1, 2, 3))                       # Nov-Mar icing season
)
```

**Expected Icing Frequency**: 2-8% of hours (winter months only)

**Automation**:
```bash
# Cron job: 0 3 * * * (daily at 03:00 UTC)
python3 download_era5_weather_incremental.py
```

---

### 4. GFS Forecast Weather (`gfs_forecast_weather`)

**Source**: NOAA GFS via Open-Meteo https://api.open-meteo.com/v1/gfs  
**Coverage**: 48 UK offshore wind farms, 7-day ahead forecasts  
**Update Frequency**: Every 6 hours (00Z, 06Z, 12Z, 18Z cycles)  
**Records**: Rolling 7-day horizon × 48 farms = ~8,064 hourly forecasts

**Schema**:
```sql
CREATE TABLE gfs_forecast_weather (
    forecast_time TIMESTAMP,        -- When forecast was issued
    valid_time TIMESTAMP,           -- When forecast is valid for
    farm_name STRING,
    latitude FLOAT64,
    longitude FLOAT64,
    wind_speed_100m FLOAT64,        -- Forecast wind speed (m/s)
    wind_direction_10m FLOAT64,     -- Forecast wind direction (°)
    temperature_2m FLOAT64,         -- Forecast temperature (°C)
    relative_humidity_2m FLOAT64,   -- Forecast humidity (%)
    pressure_msl FLOAT64,           -- Forecast pressure (hPa)
    cloud_cover FLOAT64,            -- Forecast cloud cover (%)
    precipitation FLOAT64           -- Forecast precipitation (mm)
)
```

**Purpose**:
- Day-ahead wind forecasting (t+24h, t+72h)
- Trading desk decision support
- Multi-horizon model input features
- Weather pattern prediction

**Automation**:
```bash
# Cron job: 15 */6 * * * (every 6 hours at :15 past)
python3 download_gfs_forecasts.py
```

---

### 5. ERA5 3D Wind Components (`era5_3d_wind_components`)

**Source**: Open-Meteo Archive API (ERA5 pressure level data)  
**Coverage**: 48 UK offshore wind farms, 2021-2025  
**Update Frequency**: Daily (T-5 days lag)  
**Records**: ~10.5M hourly observations (target)

**Schema**:
```sql
CREATE TABLE era5_3d_wind_components (
    time_utc TIMESTAMP,
    farm_name STRING,
    latitude FLOAT64,
    longitude FLOAT64,
    u_component_100m FLOAT64,      -- Eastward wind (m/s)
    v_component_100m FLOAT64,      -- Northward wind (m/s)
    u_component_10m FLOAT64,       -- Eastward wind at 10m (m/s)
    v_component_10m FLOAT64,       -- Northward wind at 10m (m/s)
    wind_shear FLOAT64,            -- (speed_100m - speed_10m) turbulence
    pressure_gradient FLOAT64,     -- Pressure change rate (hPa/h)
    vertical_velocity FLOAT64      -- Updraft/downdraft (m/s)
)
```

**Derived Features**:
```python
# Wind shear (turbulence indicator)
wind_shear = wind_speed_100m - wind_speed_10m

# Pressure gradient (frontal systems)
pressure_gradient = pressure_msl.diff()

# Wind power density (air density × v³)
wind_power_density = air_density × (wind_speed_100m ** 3)
```

**Purpose**:
- Ramp prediction (sudden wind changes)
- Frontal system detection (pressure gradients)
- Turbulence assessment (wind shear)
- Atmospheric stability analysis

**Automation**:
```bash
# Cron job: 0 4 * * * (daily at 04:00 UTC, after ERA5 icing data)
python3 download_era5_3d_wind.py
```

---

### 6. REMIT Unavailability Messages (`remit_unavailability_messages`)

**Source**: Elexon REMIT API https://api.bmreports.com/BMRS/REMIT  
**Coverage**: All UK BM units (including wind farms)  
**Update Frequency**: Daily (captures yesterday's messages)  
**Records**: ~5k-10k messages per month

**Schema**:
```sql
CREATE TABLE remit_unavailability_messages (
    message_id STRING,
    event_start TIMESTAMP,
    event_end TIMESTAMP,
    bm_unit STRING,                -- BM unit code (e.g., T_HOWAO-1)
    message_type STRING,           -- Planned, Unplanned, Unavailability
    event_type STRING,             -- Outage, Derate
    fuel_type STRING,              -- Wind, CCGT, Nuclear, etc.
    unavailable_capacity_mw FLOAT64,
    available_capacity_mw FLOAT64,
    cause STRING,                  -- Free text (maintenance, weather, fault)
    remarks STRING,                -- Additional details
    published_time TIMESTAMP
)
```

**Key Use Cases**:

1. **Icing vs Maintenance**:
```sql
-- Find maintenance events that overlap with predicted icing
SELECT *
FROM remit_unavailability_messages
WHERE bm_unit IN (SELECT bm_unit FROM wind_farm_to_bmu WHERE farm_name = 'Hornsea 1')
  AND event_start <= '2025-01-15 12:00:00'
  AND event_end >= '2025-01-15 12:00:00'
  AND cause LIKE '%weather%' OR cause LIKE '%ice%'
```

2. **Curtailment Detection**:
```sql
-- Find grid constraint events
SELECT *
FROM remit_unavailability_messages
WHERE fuel_type = 'Wind'
  AND event_type = 'Derate'
  AND cause LIKE '%constraint%' OR cause LIKE '%curtailment%'
```

**Automation**:
```bash
# Cron job: 0 2 * * * (daily at 02:00 UTC)
python3 download_remit_messages_incremental.py
```

---

## 🔄 Data Pipeline Architecture

### Ingestion Flow

```
┌─────────────────────────────────────────────────────────────┐
│                     DATA SOURCES                            │
├─────────────────────────────────────────────────────────────┤
│  Open-Meteo API  │  NOAA GFS  │  Elexon REMIT  │  ERA5     │
└────────┬─────────┴──────┬─────┴───────┬────────┴───────┬───┘
         │                │             │                │
         ▼                ▼             ▼                ▼
┌─────────────────────────────────────────────────────────────┐
│              PYTHON DOWNLOAD SCRIPTS (Cron)                 │
├─────────────────────────────────────────────────────────────┤
│  download_realtime_wind.py        (every 15 min)           │
│  download_gfs_forecasts.py        (every 6 hours)          │
│  download_remit_messages.py       (daily 02:00)            │
│  download_era5_weather.py         (daily 03:00)            │
│  download_era5_3d_wind.py         (daily 04:00)            │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    BIGQUERY STORAGE                         │
├─────────────────────────────────────────────────────────────┤
│  Project: inner-cinema-476211-u9                            │
│  Dataset: uk_energy_prod                                    │
│  Location: US                                               │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│              WIND FORECASTING MODELS                        │
├─────────────────────────────────────────────────────────────┤
│  - Power curve models (48 farms)                            │
│  - Multi-horizon forecasting (t+1h/6h/24h/72h)              │
│  - Icing risk classifier                                    │
│  - Ramp prediction system                                   │
│  - Curtailment detection                                    │
└────────┬────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                  OUTPUT SYSTEMS                             │
├─────────────────────────────────────────────────────────────┤
│  - Google Sheets Dashboard (live updates)                  │
│  - Trading Signals (alerts)                                │
│  - Email/SMS Notifications (critical ramps)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 Data Quality Monitoring

### Freshness Checks

Script: `check_data_freshness.py` (runs hourly)

**Thresholds**:
```python
FRESHNESS_THRESHOLDS = {
    'era5_weather_icing': 24 * 6,        # 6 days (ERA5 T-5 lag)
    'gfs_forecast_weather': 8,           # 8 hours (6-hourly updates)
    'remit_unavailability_messages': 26, # 26 hours (daily updates)
    'openmeteo_wind_realtime': 1         # 1 hour (15-min updates)
}
```

**Status Codes**:
- ✅ **OK**: Data within threshold
- ⚠️ **WARNING**: Data 1.5x threshold (e.g., 12h for GFS)
- ❌ **STALE**: Data >2x threshold (e.g., 16h for GFS)
- 🔴 **EMPTY**: No data in table
- 💀 **ERROR**: Table doesn't exist

### Validation Queries

**Check for gaps**:
```sql
WITH hourly_sequence AS (
    SELECT TIMESTAMP_ADD('2025-01-01', INTERVAL n HOUR) as hour
    FROM UNNEST(GENERATE_ARRAY(0, 24*30)) as n  -- Last 30 days
),
actual_data AS (
    SELECT DISTINCT TIMESTAMP_TRUNC(settlementDate, HOUR) as hour
    FROM `inner-cinema-476211-u9.uk_energy_prod.openmeteo_wind_historic`
    WHERE farm_name = 'Hornsea 1'
      AND DATE(settlementDate) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
)
SELECT
    hs.hour,
    CASE WHEN ad.hour IS NULL THEN 'MISSING' ELSE 'OK' END as status
FROM hourly_sequence hs
LEFT JOIN actual_data ad ON hs.hour = ad.hour
WHERE ad.hour IS NULL
ORDER BY hs.hour
```

**Check for outliers**:
```sql
SELECT
    farm_name,
    settlementDate,
    wind_speed_100m,
    generation
FROM `inner-cinema-476211-u9.uk_energy_prod.openmeteo_wind_historic`
WHERE wind_speed_100m > 35  -- Extreme wind (>35 m/s = 126 km/h)
   OR wind_speed_100m < 0   -- Invalid negative
   OR temperature_2m > 40   -- Extreme temperature
   OR temperature_2m < -30
ORDER BY settlementDate DESC
LIMIT 100
```

---

## 🛠️ Maintenance & Operations

### Daily Tasks (Automated)

1. **02:00 UTC**: Download REMIT messages (yesterday)
2. **03:00 UTC**: Download ERA5 weather incremental (T-5 to T-1)
3. **04:00 UTC**: Download ERA5 3D wind incremental
4. **Every 6h**: Download GFS forecasts (00Z, 06Z, 12Z, 18Z)
5. **Every 15min**: Download real-time wind data
6. **Every 1h**: Check data freshness, alert if stale

### Weekly Tasks (Manual)

1. **Monday 08:00**: Run drift monitoring (PSI checks)
2. **Review alerts**: Critical ramps, icing events, curtailment
3. **Model retraining**: If drift detected (PSI > 0.2)

### Monthly Tasks (Manual)

1. **Validate forecasts**: Compare to NESO actuals
2. **Review business value**: Trading accuracy, revenue impact
3. **Check storage costs**: BigQuery table sizes
4. **Update documentation**: New farms, schema changes

---

## 📚 Reference

### API Rate Limits

- **Open-Meteo Free Tier**: 10,000 requests/day, 10 requests/min
- **Elexon REMIT**: No documented limit (reasonable use)
- **NOAA GFS**: Public data, no hard limits

### Data Retention

- **Historical wind**: Permanent (2021-present)
- **Real-time wind**: Rolling 48 hours (overwritten)
- **GFS forecasts**: Rolling 7 days (overwritten)
- **REMIT messages**: Permanent (regulatory requirement)

### Contact

- **Technical Issues**: george@upowerenergy.uk
- **Data Questions**: See CHATGPT_INSTRUCTIONS.md
- **API Issues**: Check individual provider status pages

---

**Last Updated**: December 30, 2025  
**Version**: 1.0
