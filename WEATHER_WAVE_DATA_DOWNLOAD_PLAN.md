# Weather & Wave Data Download Plan - GB Power Market JJ

**Status**: Ready to execute  
**Date**: 31 December 2025  
**Expected Runtime**: 4-24 hours (depends on CDS/CMEMS queue times)

---

## 📊 Current Data Inventory

### ✅ What We Already Have

**BigQuery Tables** (`inner-cinema-476211-u9.uk_energy_prod`):
- **`metoffice_marine_stations`** - 106 UK marine observation stations
  - 18 ocean buoys (high-priority for upstream wind monitoring)
  - 83 coastal land stations
  - 5 light vessels
  - Full metadata: coordinates, station type, region, data source
  
- **`metoffice_stations_to_wind_farms`** (VIEW) - Spatial joins
  - Links each station → 5 nearest wind farms
  - Distance calculations (km)
  - Proximity categories (adjacent/near/regional/distant)
  - Estimated weather lag time (hours at 30 km/h wind speed)

- **`offshore_wind_farms`** - 41 operational/under-construction UK offshore wind farms
  - Total capacity: ~15 GW
  - Full coordinates (lat/lon)
  - Status, commissioned year, capacity, turbine counts

- **Historical Market Data** (2020-2025):
  - `bmrs_bod` - Bid-offer data (391M+ rows)
  - `bmrs_boalf_complete` - Balancing acceptances with prices (11M rows)
  - `bmrs_costs` - Imbalance prices (SSP/SBP)
  - `bmrs_fuelinst` - Fuel mix (5-min intervals)
  - `bmrs_freq` - Grid frequency
  - Plus 174+ other BMRS tables

- **Real-Time IRIS Pipeline** (AlmaLinux server):
  - `bmrs_*_iris` tables (last 24-48h)
  - Fuel mix, frequency, individual generation
  - 15-30 min update frequency

**Local Files**:
- `turbines.csv` - 41 wind farm locations (just created from BigQuery)
- `metoffice_marine_station_locations.csv` - 106 marine stations

---

## ❌ Outstanding Data (To Be Downloaded)

### 1. ERA5 Reanalysis (Hourly Point Data at Turbines)

**What**: Historical model-based weather reanalysis at 31 km resolution  
**Period**: 2020-01-01 to 2025-12-31 (6 years)  
**Locations**: 41 UK offshore wind farms (point data)  
**Frequency**: Hourly (8,760 hours/year × 6 years = 52,560 timesteps per location)

**Variables (Raw)**:
- `u100` - U-component wind at 100m hub height (m/s)
- `v100` - V-component wind at 100m hub height (m/s)
- `t2m` - 2-meter air temperature (Kelvin)
- `d2m` - 2-meter dewpoint temperature (Kelvin)

**Variables (Derived - Computed Locally)**:
- `wind_speed_100m` - Wind speed at hub height (m/s)  
  Formula: `√(u²+ v²)`
  
- `wind_dir_from_deg` - Wind direction (degrees, meteorological "from")  
  Formula: `(arctan2(-u, -v) × 180/π + 360) % 360`
  
- `rh_2m_pct` - Relative humidity at 2m (%)  
  Formula: Magnus equation using T and Td

**Total Data Volume**:
- 41 locations × 6 years = **246 year-location requests**
- Expected file size: ~50-100 MB per location-year = **12-25 GB total**
- Expected rows: 52,560 hours × 41 locations = **2.15M rows** in BigQuery

**Runtime Estimate**:
- With 3 concurrent workers: **1-12 hours**
- Bottleneck: CDS API queue processing (not bandwidth)
- Light queue: ~30-90 sec per request → 1-4 hours
- Busy queue: ~5-10 min per request → 4-12 hours

**Why Point Data (Not Grid)**:
- Full UK grid would be ~100 GB per year (unmanageable)
- Point data at turbines gives exact hub-height conditions
- Sufficient for power output correlation analysis

---

### 2. CMEMS Wave Data (UK Bounding Box Grid)

**What**: Global ocean wave reanalysis + analysis/forecast  
**Period**: 2020-01-01 to 2025-12-31 (6 years)  
**Coverage**: UK bounding box **49.5-61.5°N, -12.0-4.5°E** (gridded, not points)  
**Resolution**: ~0.2° (~20 km) spatial, **3-hourly temporal** (not hourly!)  
**Important**: Wave data is 3-hourly (16,080 timesteps over 6 years), not hourly

**Variables (Auto-Discovered - ALL Available)**:
Core variables (confirmed from product page):
- `VHM0` - Significant wave height (m)
- `VTPK` - Peak wave period (s)
- `VMDR` - Mean wave direction (degrees)
- `VPED` - Wave energy period (s)
- `VTM01` - Mean period Tm01 (s)
- `VTM02` - Mean period Tm02 (s)
- `VMDR_SW1` - Mean direction of primary swell partition
- `VMDR_SW2` - Mean direction of secondary swell partition
- `VMDR_WW` - Mean direction of wind-wave partition
- `VHM0_SW1` - Significant height of primary swell partition (m)
- `VHM0_SW2` - Significant height of secondary swell partition (m)
- `VHM0_WW` - Significant height of wind-wave partition (m)
- Plus other partitioned wave fields

**Download Strategy**:
- **Reanalysis** (1980-2025-10-31): `GLOBAL_MULTIYEAR_WAV_001_032`
- **Forecast Tail** (2025-11-01 to today): `GLOBAL_ANALYSISFORECAST_WAV_001_027`
- Year-chunked downloads (resumable if interrupted)
- Auto-variable discovery (script queries product metadata)

**Total Data Volume**:
- 6 year files (2020-2024 full + 2025 split into reanalysis+forecast)
- Expected file size: **50-500 MB per year** (depends on # of variables)
- Total: **~300 MB - 3 GB** (gridded NetCDF format)

**Runtime Estimate**:
- No rate limits on CMEMS Toolbox
- I/O bound: minutes to ~2 hours per year
- Total: **~30 min - 4 hours** for 6 years

**Use Cases**:
- Offshore access weather (crew transfer vessel planning)
- Turbine foundation loads (fatigue analysis)
- Maintenance window forecasting
- Correlation with unplanned outages (high seas → forced shutdown)

---

## 🚫 Data We Are NOT Getting (Yet)

### Met Office Station Observations (Actual Measurements)

**Why Not Included**:
- ERA5/CMEMS are **model/reanalysis** products (gridded interpolations)
- Met Office stations are **point observations** (real measurements)
- Different download pipelines:
  - ERA5 → Copernicus CDS API
  - CMEMS → Copernicus Marine Toolbox
  - Met Office → CEDA MIDAS Open (different auth/API)

**What We Have**:
- 106 marine station **locations** (scraped from Met Office website)
- Station metadata (coordinates, types, URLs)
- Spatial links to wind farms

**What We DON'T Have**:
- Historical hourly observations (wind, temp, pressure, etc.)
- Real-time observation data feeds
- Multi-year time-series from buoys

**How to Get It** (Future Work):
1. Register at CEDA (https://services.ceda.ac.uk)
2. Request access to MIDAS Open dataset
3. Download via FTP or API
4. Separate ingestion script: `download_metoffice_station_obs.py`

**Priority**: Medium (use for bias correction of ERA5 at coastal locations)

---

## 🔄 What Live Data We're Currently Ingesting

**IRIS Real-Time Pipeline** (AlmaLinux server `94.237.55.234`):

**Active Streams** (Azure Service Bus → BigQuery):
- `bmrs_fuelinst_iris` - Fuel mix (coal, gas, wind, solar, nuclear) - 5-min
- `bmrs_freq_iris` - Grid frequency (Hz) - real-time
- `bmrs_indgen_iris` - Individual unit generation (MW) - 5-min
- `bmrs_mid_iris` - Market index prices (£/MWh) - 30-min

**NOT Configured** (Available but not enabled):
- `bmrs_costs_iris` - Imbalance prices (SSP/SBP)
- `bmrs_boalf_iris` - Balancing acceptances
- `bmrs_bod_iris` - Bid-offer data

**Update Frequency**: 15-30 min lag from National Grid publication  
**Retention**: Last 24-48 hours (older data in historical tables)  
**Deployment**: `iris_to_bigquery_unified.py` + systemd service

---

## 📝 Download Instructions

### Prerequisites

**1. Install Python Packages**:
```bash
pip3 install --user cdsapi copernicusmarine pandas numpy xarray netcdf4 pyarrow google-cloud-bigquery
```

**2. Configure Copernicus CDS API (for ERA5)**:
```bash
# Register at: https://cds.climate.copernicus.eu
# Get your UID and API key from account page
# Create config file:
cat > ~/.cdsapirc << EOF
url: https://cds.climate.copernicus.eu/api/v2
key: {YOUR_UID}:{YOUR_API_KEY}
EOF
chmod 600 ~/.cdsapirc
```

**3. Configure Copernicus Marine (for CMEMS)**:
```bash
# Register at: https://data.marine.copernicus.eu
# Either set environment variables:
export CMEMS_USERNAME="your_username"
export CMEMS_PASSWORD="your_password"

# OR login interactively:
copernicusmarine login
```

---

### Execution Steps

#### Step 1: Download ERA5 Data (1-12 hours)

```bash
cd /home/george/GB-Power-Market-JJ

# Verify turbines.csv exists (already created)
head turbines.csv

# Run downloader (3 concurrent workers)
python3 download_era5_turbine_points.py

# Monitor progress (outputs to stdout)
# Expected: 246 year-location downloads
# Output: era5_points/*.nc (NetCDF) + era5_points/*.parquet (processed)
```

**What It Does**:
- Downloads hourly u100/v100/t2m/d2m from CDS
- Year-chunked requests (246 requests total)
- Auto-fallback to monthly chunks if year request fails
- Computes wind speed, direction, RH locally
- Saves both NetCDF (raw) + Parquet (analysis-ready)

**Troubleshooting**:
- Slow? CDS queue is busy (normal, just wait)
- API errors? Check `~/.cdsapirc` credentials
- Disk space? Need ~25 GB free

---

#### Step 2: Download CMEMS Wave Data (30 min - 4 hours)

```bash
cd /home/george/GB-Power-Market-JJ

# Run downloader
python3 download_cmems_waves_uk.py

# Monitor progress
# Expected: 6-7 NetCDF files (year-chunked)
# Output: cmems_waves_uk/*.nc
```

**What It Does**:
- Auto-discovers all wave variables from product metadata
- Downloads UK bbox grid (49.5-61.5°N, -12-4.5°E)
- Year-chunked (2020-2024 full, 2025 split reanalysis+forecast)
- No rate limits (CMEMS Toolbox is quota-free)

**Troubleshooting**:
- Login errors? Run `copernicusmarine login` first
- Slow? Large bbox + many variables (normal)
- Disk space? Need ~3 GB free

---

## 🗄️ BigQuery Ingestion Plan

### ERA5 Table Schema

**Table**: `uk_energy_prod.era5_turbine_hourly`

| Column | Type | Description |
|--------|------|-------------|
| `turbine_id` | STRING | Wind farm name (from offshore_wind_farms) |
| `time` | TIMESTAMP | Hourly timestamp (UTC) |
| `latitude` | FLOAT64 | Turbine location (from turbines.csv) |
| `longitude` | FLOAT64 | Turbine location (from turbines.csv) |
| `u100` | FLOAT64 | U-component wind at 100m (m/s) |
| `v100` | FLOAT64 | V-component wind at 100m (m/s) |
| `t2m_k` | FLOAT64 | 2m temperature (Kelvin) |
| `t2m_c` | FLOAT64 | 2m temperature (Celsius, computed) |
| `d2m_k` | FLOAT64 | 2m dewpoint (Kelvin) |
| `wind_speed_100m` | FLOAT64 | Wind speed at hub height (m/s) |
| `wind_dir_from_deg` | FLOAT64 | Wind direction (degrees, 0°=N) |
| `rh_2m_pct` | FLOAT64 | Relative humidity (%) |
| `ingested_at` | TIMESTAMP | When loaded to BigQuery |

**Expected Rows**: ~2.15M (52,560 hours × 41 turbines)

**Ingestion Script**: `ingest_era5_to_bigquery.py` (to be created)

---

### CMEMS Wave Table Schema

**Table**: `uk_energy_prod.cmems_waves_uk_grid`

| Column | Type | Description |
|--------|------|-------------|
| `time` | TIMESTAMP | 3-hourly timestamp (UTC) |
| `latitude` | FLOAT64 | Grid point latitude |
| `longitude` | FLOAT64 | Grid point longitude |
| `VHM0` | FLOAT64 | Significant wave height (m) |
| `VTPK` | FLOAT64 | Peak wave period (s) |
| `VMDR` | FLOAT64 | Mean wave direction (degrees) |
| `VPED` | FLOAT64 | Wave energy period (s) |
| ... | ... | (All other wave variables auto-included) |
| `VHM0_WW` | FLOAT64 | Wind-wave height (m) |
| `VHM0_SW1` | FLOAT64 | Primary swell height (m) |
| `ingested_at` | TIMESTAMP | When loaded to BigQuery |

**Expected Rows**: ~500k-2M (depends on grid resolution × 16,080 timesteps)

**Ingestion Script**: `ingest_cmems_waves_to_bigquery.py` (to be created)

---

### Spatial Analysis Views (To Be Created)

**1. `era5_to_wind_farms` (VIEW)**:
```sql
-- Each wind farm → its own ERA5 data (1:1 match since we downloaded at turbine points)
SELECT 
    e.turbine_id as wind_farm_name,
    e.time,
    e.wind_speed_100m,
    e.wind_dir_from_deg,
    e.t2m_c,
    e.rh_2m_pct,
    w.capacity_mw,
    w.latitude as farm_lat,
    w.longitude as farm_lon
FROM uk_energy_prod.era5_turbine_hourly e
JOIN uk_energy_prod.offshore_wind_farms w
  ON e.turbine_id = w.name
```

**2. `waves_to_wind_farms` (VIEW)**:
```sql
-- Each wind farm → nearest wave grid point (spatial join)
WITH farm_wave_distances AS (
  SELECT 
    w.name as wind_farm_name,
    wav.time,
    wav.VHM0,
    wav.VTPK,
    wav.VMDR,
    -- Distance calculation using ST_DISTANCE
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
  FROM uk_energy_prod.offshore_wind_farms w
  CROSS JOIN uk_energy_prod.cmems_waves_uk_grid wav
)
SELECT * FROM farm_wave_distances WHERE rank = 1
```

**3. `combined_weather_waves` (VIEW)**:
```sql
-- Unified hourly weather + wave conditions per farm
SELECT 
    e.wind_farm_name,
    e.time,
    e.wind_speed_100m,
    e.wind_dir_from_deg,
    e.t2m_c,
    e.rh_2m_pct,
    w.VHM0 as significant_wave_height_m,
    w.VTPK as peak_wave_period_s,
    w.VMDR as wave_direction_deg,
    e.capacity_mw
FROM uk_energy_prod.era5_to_wind_farms e
LEFT JOIN uk_energy_prod.waves_to_wind_farms w
  ON e.wind_farm_name = w.wind_farm_name
  AND TIMESTAMP_TRUNC(e.time, HOUR) = TIMESTAMP_TRUNC(w.time, HOUR)
```

---

## 📋 Next Actions Checklist

- [ ] **1. Set up CDS API credentials** (`~/.cdsapirc`)
- [ ] **2. Set up CMEMS credentials** (environment vars or `copernicusmarine login`)
- [ ] **3. Run ERA5 downloader** (`python3 download_era5_turbine_points.py`)
  - Monitor: expect 1-12 hours runtime
  - Output: `era5_points/` directory with 492 files (246 NC + 246 Parquet)
  
- [ ] **4. Run CMEMS downloader** (`python3 download_cmems_waves_uk.py`)
  - Monitor: expect 30 min - 4 hours runtime
  - Output: `cmems_waves_uk/` directory with 6-7 NC files
  
- [ ] **5. Create BigQuery ingestion scripts**:
  - `ingest_era5_to_bigquery.py`
  - `ingest_cmems_waves_to_bigquery.py`
  
- [ ] **6. Run BigQuery ingestion**
  - ERA5: ~2.15M rows → `uk_energy_prod.era5_turbine_hourly`
  - CMEMS: ~500k-2M rows → `uk_energy_prod.cmems_waves_uk_grid`
  
- [ ] **7. Create spatial analysis views**:
  - `era5_to_wind_farms`
  - `waves_to_wind_farms`
  - `combined_weather_waves`
  
- [ ] **8. Validate data quality**:
  - Check row counts match expectations
  - Verify date ranges complete (2020-2025)
  - Spot-check wind speeds reasonable (0-30 m/s)
  - Confirm wave heights realistic (0-15m typical, 20m extreme)
  
- [ ] **9. Document in project**:
  - Update `PROJECT_CONFIGURATION.md`
  - Create `WEATHER_DATA_SOURCES.md`
  - Update dashboard to include weather correlations

---

## 🎯 Use Cases After Ingestion

### Power Output Correlation
```sql
-- Wind speed vs generation at Hornsea One
SELECT 
    e.time,
    e.wind_speed_100m,
    g.generation_mw,
    e.capacity_mw,
    g.generation_mw / e.capacity_mw * 100 as capacity_factor_pct
FROM uk_energy_prod.era5_to_wind_farms e
JOIN uk_energy_prod.bmrs_indgen g
  ON g.bmUnitId = 'HORNSEA1'
  AND CAST(g.settlementDate AS TIMESTAMP) = e.time
WHERE e.wind_farm_name = 'Hornsea One'
  AND e.time >= '2024-01-01'
ORDER BY e.time
```

### Maintenance Window Analysis
```sql
-- Safe access periods (wave height < 2m, wind < 15 m/s)
SELECT 
    wind_farm_name,
    DATE(time) as date,
    COUNTIF(wind_speed_100m < 15 AND significant_wave_height_m < 2) as safe_hours,
    COUNTIF(wind_speed_100m >= 15 OR significant_wave_height_m >= 2) as unsafe_hours
FROM uk_energy_prod.combined_weather_waves
WHERE time >= '2025-01-01'
GROUP BY wind_farm_name, date
ORDER BY safe_hours DESC
```

### Storm Event Detection
```sql
-- Extreme weather events (potential forced outages)
SELECT 
    wind_farm_name,
    time,
    wind_speed_100m,
    significant_wave_height_m,
    CASE 
      WHEN wind_speed_100m > 25 THEN 'Curtailment Risk'
      WHEN significant_wave_height_m > 10 THEN 'High Seas'
      ELSE 'Normal'
    END as alert_type
FROM uk_energy_prod.combined_weather_waves
WHERE wind_speed_100m > 25 OR significant_wave_height_m > 10
ORDER BY time DESC
LIMIT 100
```

---

## 📞 Support & References

**Copernicus CDS (ERA5)**:
- Registration: https://cds.climate.copernicus.eu
- API docs: https://cds.climate.copernicus.eu/api-how-to
- Dataset page: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels-timeseries

**Copernicus Marine (CMEMS)**:
- Registration: https://data.marine.copernicus.eu
- Toolbox docs: https://help.marine.copernicus.eu/en/collections/4060068-copernicus-marine-toolbox
- Wave reanalysis: https://data.marine.copernicus.eu/product/GLOBAL_MULTIYEAR_WAV_001_032

**Project Documentation**:
- Configuration: `PROJECT_CONFIGURATION.md`
- Architecture: `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`
- Data reference: `STOP_DATA_ARCHITECTURE_REFERENCE.md`

---

**Document Version**: 1.0  
**Last Updated**: 31 December 2025  
**Next Update**: After successful ingestion (add actual row counts, file sizes, runtime benchmarks)
