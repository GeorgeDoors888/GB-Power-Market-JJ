# Next Steps Execution Summary

**Date**: 31 December 2025  
**Status**: ✅ ERA5 download IN PROGRESS

---

## ✅ Completed Actions

### 1. Package Installation
```bash
✅ pip3 install cdsapi copernicusmarine xarray pandas numpy h5netcdf
```
All required packages installed successfully.

### 2. Credentials Verification
- ✅ **CDS API**: Credentials found at `~/.cdsapirc` and tested successfully
- ⏳ **CMEMS**: Not yet configured (see step 2 below)

### 3. Scripts Created
- ✅ `download_era5_turbine_points.py` - ERA5 downloader (CURRENTLY RUNNING)
- ✅ `download_cmems_waves_uk.py` - CMEMS wave downloader (ready)
- ✅ `ingest_era5_to_bigquery.py` - ERA5 → BigQuery ingestion
- ✅ `ingest_cmems_waves_to_bigquery.py` - CMEMS → BigQuery ingestion
- ✅ `SETUP_CMEMS_CREDENTIALS.md` - Credential setup guide

### 4. ERA5 Download Started
**Process**: PID 3148930 (running in background)  
**Log**: `era5_download.log`  
**Status**: Just started (0/246 files completed)  
**Expected duration**: 1-12 hours depending on CDS queue

**What it's downloading**:
- 41 UK offshore wind farm locations
- 6 years of hourly data (2020-2025)
- Variables: u100, v100, t2m, d2m
- Auto-computed: wind speed, direction, relative humidity

---

## 📋 Remaining Steps (In Order)

### Step 1: Monitor ERA5 Download
**Duration**: 1-12 hours (automated, already running)

```bash
# Watch live progress
tail -f era5_download.log

# Check file count
ls era5_points/*.parquet 2>/dev/null | wc -l
# Target: 246 files

# Formatted progress report
bash monitor_downloads.sh
```

**When complete**: You'll see 246 parquet files in `era5_points/` directory

---

### Step 2: Configure CMEMS Credentials
**Duration**: 5 minutes (manual setup)

**Option A - Environment Variables** (recommended):
```bash
# Register first at: https://data.marine.copernicus.eu
export CMEMS_USERNAME="your_email@domain.com"
export CMEMS_PASSWORD="your_password"

# Make permanent (add to ~/.bashrc):
echo 'export CMEMS_USERNAME="your_email@domain.com"' >> ~/.bashrc
echo 'export CMEMS_PASSWORD="your_password"' >> ~/.bashrc
```

**Option B - Interactive Login**:
```bash
copernicusmarine login
# Enter credentials when prompted
```

**Test**:
```bash
copernicusmarine describe --product-id GLOBAL_MULTIYEAR_WAV_001_032
# Should show product metadata if credentials work
```

---

### Step 3: Run CMEMS Wave Download
**Duration**: 30 minutes - 4 hours

```bash
python3 download_cmems_waves_uk.py
```

**What it downloads**:
- UK bounding box: 49.5-61.5°N, -12.0-4.5°E
- Period: 2020-2025 (6 years, 3-hourly)
- All wave variables: VHM0, VTPK, VMDR, partitioned swell/wind-waves
- Expected output: 6-7 NetCDF files, 300 MB - 3 GB

**Monitor**:
```bash
ls cmems_waves_uk/*.nc 2>/dev/null | wc -l
# Target: 6-7 files
```

---

### Step 4: Ingest ERA5 to BigQuery
**Duration**: 10-30 minutes  
**Prerequisites**: ERA5 download complete (246 parquet files)

```bash
python3 ingest_era5_to_bigquery.py
```

**What it does**:
- Combines all 246 parquet files
- Adds derived columns (Celsius temp, coordinates)
- Uploads to `uk_energy_prod.era5_turbine_hourly`
- Expected: ~2.15M rows

**Verify**:
```sql
SELECT 
    COUNT(*) as rows,
    COUNT(DISTINCT turbine_id) as turbines,
    MIN(time) as earliest,
    MAX(time) as latest
FROM `inner-cinema-476211-u9.uk_energy_prod.era5_turbine_hourly`
-- Should show: 2.15M rows, 41 turbines, 2020-2025 date range
```

---

### Step 5: Ingest CMEMS Waves to BigQuery
**Duration**: 10-30 minutes  
**Prerequisites**: CMEMS download complete (6-7 NetCDF files)

```bash
python3 ingest_cmems_waves_to_bigquery.py
```

**What it does**:
- Loads all NetCDF files
- Flattens grid data (time × lat × lon)
- Uploads to `uk_energy_prod.cmems_waves_uk_grid`
- Expected: 500k-2M rows

**Verify**:
```sql
SELECT 
    COUNT(*) as rows,
    MIN(time) as earliest,
    MAX(time) as latest,
    ROUND(AVG(VHM0), 2) as avg_wave_height_m
FROM `inner-cinema-476211-u9.uk_energy_prod.cmems_waves_uk_grid`
```

---

### Step 6: Create Spatial Analysis Views
**Duration**: 5 minutes  
**Prerequisites**: Both datasets in BigQuery

Create these views to link weather/wave data to wind farms:

#### View 1: ERA5 to Wind Farms (1:1 mapping)
```sql
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.era5_to_wind_farms` AS
SELECT 
    e.turbine_id as wind_farm_name,
    e.time,
    e.wind_speed_100m,
    e.wind_dir_from_deg,
    e.t2m_c as temperature_c,
    e.rh_2m_pct as humidity_pct,
    w.capacity_mw,
    w.latitude as farm_lat,
    w.longitude as farm_lon
FROM `inner-cinema-476211-u9.uk_energy_prod.era5_turbine_hourly` e
JOIN `inner-cinema-476211-u9.uk_energy_prod.offshore_wind_farms` w
  ON e.turbine_id = w.name;
```

#### View 2: Waves to Wind Farms (nearest grid point)
```sql
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.waves_to_wind_farms` AS
WITH farm_wave_distances AS (
  SELECT 
    w.name as wind_farm_name,
    wav.time,
    wav.VHM0 as significant_wave_height_m,
    wav.VTPK as peak_wave_period_s,
    wav.VMDR as wave_direction_deg,
    ST_DISTANCE(
      ST_GEOGPOINT(w.longitude, w.latitude),
      ST_GEOGPOINT(wav.longitude, wav.latitude)
    ) / 1000 as distance_km,
    ROW_NUMBER() OVER (
      PARTITION BY w.name, wav.time 
      ORDER BY ST_DISTANCE(
        ST_GEOGPOINT(w.longitude, w.latitude),
        ST_GEOGPOINT(wav.longitude, wav.latitude)
      )
    ) as rank
  FROM `inner-cinema-476211-u9.uk_energy_prod.offshore_wind_farms` w
  CROSS JOIN `inner-cinema-476211-u9.uk_energy_prod.cmems_waves_uk_grid` wav
)
SELECT * FROM farm_wave_distances WHERE rank = 1;
```

#### View 3: Combined Weather + Waves
```sql
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.combined_weather_waves` AS
SELECT 
    e.wind_farm_name,
    e.time,
    e.wind_speed_100m,
    e.wind_dir_from_deg,
    e.temperature_c,
    e.humidity_pct,
    w.significant_wave_height_m,
    w.peak_wave_period_s,
    w.wave_direction_deg,
    e.capacity_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.era5_to_wind_farms` e
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.waves_to_wind_farms` w
  ON e.wind_farm_name = w.wind_farm_name
  AND TIMESTAMP_TRUNC(e.time, HOUR) = TIMESTAMP_TRUNC(w.time, HOUR);
```

---

## 🎯 Example Queries After Completion

### Power Output Correlation
```sql
-- Wind speed vs actual generation
SELECT 
    DATE(w.time) as date,
    AVG(w.wind_speed_100m) as avg_wind_speed,
    AVG(g.generation_mw) as avg_generation,
    AVG(g.generation_mw / w.capacity_mw * 100) as capacity_factor_pct
FROM `inner-cinema-476211-u9.uk_energy_prod.era5_to_wind_farms` w
JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_indgen` g
  ON g.bmUnitId = 'HORNSEA1'
  AND DATE(g.settlementDate) = DATE(w.time)
WHERE w.wind_farm_name = 'Hornsea One'
  AND w.time >= '2024-01-01'
GROUP BY date
ORDER BY date;
```

### Maintenance Windows
```sql
-- Safe access periods (low wind + low waves)
SELECT 
    wind_farm_name,
    DATE(time) as date,
    COUNTIF(wind_speed_100m < 12 AND significant_wave_height_m < 2) as safe_hours,
    COUNTIF(wind_speed_100m >= 20 OR significant_wave_height_m >= 4) as extreme_hours
FROM `inner-cinema-476211-u9.uk_energy_prod.combined_weather_waves`
WHERE time >= '2025-01-01'
GROUP BY wind_farm_name, date
HAVING safe_hours >= 6  -- At least 6-hour maintenance window
ORDER BY safe_hours DESC;
```

### Storm Events
```sql
-- Extreme weather events
SELECT 
    wind_farm_name,
    time,
    wind_speed_100m,
    significant_wave_height_m,
    CASE 
      WHEN wind_speed_100m > 25 THEN 'Hurricane Force'
      WHEN wind_speed_100m > 20 THEN 'Storm Force'
      WHEN significant_wave_height_m > 8 THEN 'Very High Seas'
      ELSE 'High Wind/Waves'
    END as alert_type
FROM `inner-cinema-476211-u9.uk_energy_prod.combined_weather_waves`
WHERE wind_speed_100m > 20 OR significant_wave_height_m > 6
ORDER BY time DESC
LIMIT 100;
```

---

## 📊 Expected Final Data Inventory

### BigQuery Tables
- ✅ `metoffice_marine_stations` (106 stations) - Already exists
- ✅ `offshore_wind_farms` (41 farms) - Already exists
- ⏳ `era5_turbine_hourly` (2.15M rows) - After step 4
- ⏳ `cmems_waves_uk_grid` (500k-2M rows) - After step 5

### BigQuery Views
- ⏳ `era5_to_wind_farms` - After step 6
- ⏳ `waves_to_wind_farms` - After step 6
- ⏳ `combined_weather_waves` - After step 6

### Local Files
- ✅ `turbines.csv` (41 locations)
- ✅ `metoffice_marine_station_locations.csv` (106 stations)
- ⏳ `era5_points/*.nc` (246 files, ~12-25 GB) - In progress
- ⏳ `era5_points/*.parquet` (246 files) - In progress
- ⏳ `cmems_waves_uk/*.nc` (6-7 files, ~300 MB-3 GB) - After step 3

---

## 🕐 Timeline Summary

| Step | Duration | Status |
|------|----------|--------|
| Package install | 2 min | ✅ Complete |
| ERA5 download | 1-12 hrs | 🔄 Running (0% complete) |
| CMEMS setup | 5 min | ⏳ Manual action needed |
| CMEMS download | 0.5-4 hrs | ⏳ Waiting for credentials |
| ERA5 ingestion | 10-30 min | ⏳ Waiting for download |
| CMEMS ingestion | 10-30 min | ⏳ Waiting for download |
| Create views | 5 min | ⏳ Waiting for ingestion |
| **Total** | **2-17 hrs** | **16% complete** |

---

## 🔧 Troubleshooting

### ERA5 download stuck/slow
- **Normal**: CDS queue can be very slow (hours per request)
- **Check**: `tail -f era5_download.log` to see if requests are progressing
- **CDS Status**: Check https://cds.climate.copernicus.eu for service status

### CMEMS credentials rejected
```bash
# Test login
copernicusmarine login

# Verify credentials work
copernicusmarine describe --product-id GLOBAL_MULTIYEAR_WAV_001_032
```

### BigQuery ingestion fails
- **Quota**: Check BigQuery quotas (free tier: 10 GB/day upload)
- **Credentials**: Verify `GOOGLE_APPLICATION_CREDENTIALS` set
- **Project**: Confirm using `inner-cinema-476211-u9` (not jibber-jabber-knowledge)

---

## 📞 Support & Documentation

- **Full plan**: `WEATHER_WAVE_DATA_DOWNLOAD_PLAN.md`
- **CMEMS setup**: `SETUP_CMEMS_CREDENTIALS.md`
- **Project config**: `PROJECT_CONFIGURATION.md`
- **Data architecture**: `STOP_DATA_ARCHITECTURE_REFERENCE.md`

---

**Last Updated**: 31 December 2025, 11:24 UTC  
**Next Action**: Monitor ERA5 download progress with `tail -f era5_download.log`
