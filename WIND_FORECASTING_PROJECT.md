# Wind Forecasting Project - Comprehensive Documentation

**Date**: December 30, 2025  
**Status**: 🔄 Phase 1 Complete | Phase 2 In Progress  
**Author**: George Major (george@upowerenergy.uk)

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Current System Status (Phase 1)](#current-system-status-phase-1)
3. [Advanced Integration Plan (Phase 2)](#advanced-integration-plan-phase-2)
4. [Data Architecture](#data-architecture)
5. [ECMWF Weather Integration](#ecmwf-weather-integration)
6. [Market Correlation Analysis](#market-correlation-analysis)
7. [Wind Drop Detection System](#wind-drop-detection-system)
8. [Implementation Roadmap](#implementation-roadmap)
9. [Technical Reference](#technical-reference)

---

## 1. Project Overview

### Mission Statement
Build comprehensive wind forecasting and early warning system for UK energy market trading by:
- Tracking NESO generation forecast accuracy (aggregate GB level)
- Integrating ECMWF weather data at turbine level (detailed spatial analysis)
- Detecting wind drops earlier than NESO forecasts update
- Correlating wind forecast errors with imbalance prices and BM activity
- Providing actionable trading signals for battery arbitrage

### Business Value
- **Trading Edge**: Predict imbalance price spikes from wind forecast errors
- **Early Warning**: Detect wind drops in ECMWF weather data before NESO updates forecasts
- **Revenue Optimization**: Battery dispatch timing based on wind volatility
- **Risk Management**: Avoid large exposure during high forecast error periods

### Key Questions Being Answered
1. **Forecast Accuracy**: How reliable are NESO wind generation forecasts? (Answer: 18.7% WAPE)
2. **Forecast Bias**: Does NESO systematically over/under-forecast? (Answer: -1075 MW bias = under-forecasting)
3. **Wind Drops**: Can we detect wind speed drops earlier than NESO? (Testing: ECMWF weather vs NESO generation)
4. **Market Impact**: Do large wind errors cause price spikes? (Analysis: Wind error → SSP/SBP correlation)
5. **Spatial Patterns**: Which offshore regions have highest forecast errors? (Phase 2: Turbine-level analysis)

---

## 2. Current System Status (Phase 1)

### ✅ Deployed Components

#### 2.1 BigQuery Views (Aggregate GB Wind)

**View: `wind_forecast_sp`**
- **Purpose**: Hourly NESO generation forecasts aligned to 30-min settlement periods
- **Sources**: `bmrs_windfor` (historical) + `bmrs_windfor_iris` (real-time)
- **Coverage**: October 2025 → present
- **Key Fields**: `settlementDate`, `settlementPeriod`, `forecast_mw`

```sql
-- Sample query
SELECT settlementDate, settlementPeriod, forecast_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.wind_forecast_sp`
WHERE settlementDate = '2025-12-29'
ORDER BY settlementPeriod
```

**View: `wind_outturn_sp`**
- **Purpose**: Actual wind generation from WIND fuel type
- **Sources**: `bmrs_fuelinst` (historical) + `bmrs_fuelinst_iris` (real-time)
- **Coverage**: 2020 → present
- **Key Fields**: `settlementDate`, `settlementPeriod`, `actual_mw`

**View: `wind_forecast_error_sp`**
- **Purpose**: Joined forecast vs actual with error metrics
- **Calculations**:
  - `error_mw` = actual - forecast (negative = under-forecast)
  - `absolute_error_mw` = ABS(error)
  - `percentage_error` = (error / actual) * 100
  - `forecast_ramp_mw` = Change from previous SP
  - `actual_ramp_mw` = Change from previous SP
  - `ramp_miss_flag` = 1 if ABS(forecast_ramp - actual_ramp) > 500 MW

```sql
-- Sample query: Large forecast errors
SELECT settlementDate, settlementPeriod, 
       forecast_mw, actual_mw, error_mw,
       CASE WHEN ABS(error_mw) > 1000 THEN '⚠️ Large Error' ELSE 'OK' END as alert
FROM `inner-cinema-476211-u9.uk_energy_prod.wind_forecast_error_sp`
WHERE settlementDate >= '2025-12-23'
  AND ABS(error_mw) > 1000
ORDER BY ABS(error_mw) DESC
LIMIT 20
```

**View: `wind_forecast_error_daily`**
- **Purpose**: Daily rollups for trending
- **Metrics**:
  - **WAPE** (Weighted Absolute Percentage Error) = SUM(|error|) / SUM(actual) * 100
  - **Bias** = SUM(error) / COUNT(*) → Average systematic error
  - **RMSE** = SQRT(AVG(error²)) → Error magnitude
  - **Ramp Misses** = COUNT(large ramp miss flags)

#### 2.2 Dashboard Integration (Live Dashboard v2)

**Location**: Rows A25:F32  
**Refresh**: Every 5 minutes (cron job)  
**Query Time**: 5.8 seconds

**Displayed Metrics**:
```
Row 25: 💨 WIND FORECAST ACCURACY
Row 27: 📊 Forecast Error (WAPE): 18.7% [7-day red sparkline]
Row 28: 📉 Forecast Bias: -1075 MW [7-day green/red sparkline]
Row 29: ⚡ Avg Actual Wind: 7225 MW [7-day blue sparkline]
Row 30: 🔮 Avg Forecast Wind: 6150 MW [7-day purple sparkline]
Row 31: ⚠️ Large Ramp Misses: 15 (yesterday)
Row 32: 📅 Data: 2025-12-29
```

**Implementation**: `update_live_metrics.py` lines 997-1909
- Parallel query execution with 14 other metrics
- Sparklines use REPT() function for visual trending
- Color coding: Red (errors), Green (positive bias), Blue (actual), Purple (forecast)

#### 2.3 Analysis Tools

**Script**: `analyze_wind_forecast_accuracy.py` (405 lines)

**Key Functions**:
- `create_wind_forecast_sp_view()` - Build forecast alignment view
- `create_wind_outturn_sp_view()` - Build actual generation view
- `create_wind_forecast_error_sp_view()` - Calculate errors and ramps
- `create_wind_forecast_error_daily_view()` - Daily aggregations
- `get_latest_forecast_metrics(days=7)` - Fetch metrics DataFrame
- `get_hour_of_day_error_pattern()` - Analyze time-of-day patterns

**Key Findings (Hour-of-Day Analysis)**:
```python
# Midnight hours have 10-11 GW errors (stale forecasts)
Hour 00:00 → 10.5 GW avg error
Hour 01:00 → 11.2 GW avg error
Hour 02:00 → 10.8 GW avg error

# Morning hours have best accuracy (fresh day-ahead)
Hour 04:00 → 0.45 GW avg error
Hour 05:00 → 0.32 GW avg error
Hour 06:00 → 0.38 GW avg error

# Trading Implication: Avoid midnight trades, prioritize 04:00-07:00 window
```

### 📊 Current Performance Metrics (Last 7 Days)

**Forecast Accuracy**:
- WAPE: 18.7% (industry benchmark: 15-20%)
- Bias: -1075 MW (under-forecasting = bullish error)
- RMSE: 2650-4762 MW daily range
- Ramp Misses: 15-17 per day (out of 48 SPs)

**Interpretation**:
- NESO systematically under-forecasts wind by ~1 GW
- 18.7% error = ±1.35 GW on 7.2 GW average wind
- Ramp detection catches 31-35% of settlement periods with large forecast changes

**Market Impact (Hypothetical)**:
- Large forecast errors (>2 GW) → Imbalance price spikes?
- Under-forecasting wind → System long (excess supply) → Low/negative prices?
- Need correlation analysis to quantify relationship

---

## 3. Advanced Integration Plan (Phase 2)

### 🎯 Objectives

1. **Turbine-Level Weather Data**: ECMWF 10m wind speed at each offshore farm location
2. **Spatial Analysis**: Compare forecast errors by region (Scottish North Sea vs English Channel)
3. **Early Warning**: Detect wind drops in ECMWF weather 3-6 hours before NESO updates
4. **Market Correlation**: Quantify wind error → imbalance price relationship
5. **Trading Signals**: Real-time alerts for high-value arbitrage opportunities

### 🔧 Required Components

#### 3.1 Offshore Wind Farm Database
**Source**: `inner-cinema-476211-u9.uk_energy_prod.offshore_wind_farms`

**Available Data**:
- **43 offshore wind farms** with GPS coordinates
- **16,410 MW** total offshore capacity
- Fields: `name`, `latitude`, `longitude`, `capacity_mw`, `gsp_zone`, `status`

**Top 5 Farms by Capacity**:
```
1. Seagreen Phase 1   56.58°N, -1.76°E  1,400 MW  SCO1 (Scotland)
2. Hornsea Two        53.89°N,  1.79°E  1,386 MW  YEA1 (Yorkshire)
3. Hornsea One        53.89°N,  1.79°E  1,218 MW  YEA1 (Yorkshire)
4. Moray East         58.10°N, -2.80°E    950 MW  SCO2 (Scotland)
5. Moray West         58.10°N, -3.10°E    882 MW  SCO2 (Scotland)
```

**Spatial Distribution**:
- **Scottish North Sea**: 9 farms, 5,700 MW (Moray, Seagreen, Beatrice)
- **English North Sea**: 24 farms, 8,800 MW (Hornsea, Dogger Bank, Triton Knoll)
- **Irish Sea**: 7 farms, 1,400 MW (Walney, Burbo Bank, Ormonde)
- **English Channel**: 3 farms, 1,510 MW (Rampion, Thanet, London Array)

**Regional Hypothesis**: Scottish farms may have different error patterns due to Atlantic weather systems vs North Sea farms influenced by continental high pressure.

#### 3.2 BM Unit Mapping (Limitation Identified)

**Challenge**: `offshore_wind_farms` table lacks BM Unit IDs

**Available Tables**:
- `bmrs_indgen_iris` - Has `generation` field but NO `bmUnitId` column (dataset-level aggregation)
- `bmrs_bod` - Has `bmUnitId` but only bid-offer data (not actual generation)
- `bmrs_boalf_complete` - Has `bmUnitId` for balancing acceptances

**Solution Options**:
1. **Manual Mapping**: Create lookup table linking farm names to BM Unit IDs (research required)
2. **GSP Zone Proxy**: Aggregate ECMWF weather by GSP zone, compare to zone-level generation
3. **API Integration**: Query NESO BMU registration API for wind farm BM IDs

**Documentation Reference**: `docs/WIND_FARM_MAPPING_COMPLETE.md` shows:
- 33 offshore farms matched with BMU registrations (14,966 MW)
- 10 farms NOT in BMU (1,444 MW missing, mostly older/smaller farms)
- Total BMU Wind Units: 248 (includes onshore + offshore)

**Next Step**: Extract BM Unit IDs from BMU registration data or create manual mapping table

---

## 4. Data Architecture

### 4.1 Current System (Phase 1)

```
NESO BMRS API
    │
    ├─→ bmrs_windfor (hourly forecasts)
    │       ↓
    │   wind_forecast_sp (30-min aligned)
    │
    └─→ bmrs_fuelinst (WIND fuel type)
            ↓
        wind_outturn_sp (actual generation)
            ↓
        wind_forecast_error_sp (error metrics)
            ↓
        wind_forecast_error_daily (daily rollups)
            ↓
        update_live_metrics.py (dashboard refresh)
            ↓
        Google Sheets A25:F32 (user view)
```

### 4.2 Proposed System (Phase 2)

```
ECMWF Open Data (IFS SCDA)
    │
    ├─→ Download U10/V10 wind components (3-hourly)
    │       ↓
    │   Calculate wind_speed = sqrt(u10² + v10²)
    │       ↓
    │   Interpolate to 30-min settlement periods
    │       ↓
    │   ecmwf_wind_turbine_forecasts (BigQuery table)
    │
    └─→ offshore_wind_farms (43 locations)
            ↓
        Parallel downloads (43 lat/lon points)
            ↓
        BM Unit mapping (manual or API)
            ↓
        bmrs_indgen (actual generation by unit) ← NOT AVAILABLE, USE PROXY
            ↓
        wind_turbine_forecast_vs_actual (comparison view)
            ↓
        wind_drop_detection (early warning logic)
            ↓
        wind_market_correlation (price impact analysis)
            ↓
        Dashboard + Map visualization
```

**Key Challenge**: Missing link between BM Unit IDs and turbine locations requires manual mapping or API integration.

---

## 5. ECMWF Weather Integration

### 5.1 ECMWF Open Data Overview

**Data Source**: ECMWF Integrated Forecasting System (IFS) SCDA  
**URL**: https://data.ecmwf.int/forecasts/  
**Update Frequency**: 4x daily (00z, 06z, 12z, 18z)  
**Forecast Horizon**: 10 days  
**Temporal Resolution**: 3-hourly  
**Spatial Resolution**: 0.25° (~28 km at UK latitudes)

**Key Variables**:
- **U10**: 10m U-component of wind (m/s, eastward positive)
- **V10**: 10m V-component of wind (m/s, northward positive)
- **Wind Speed**: sqrt(U10² + V10²)

**Data Format**: GRIB2 (binary, requires cfgrib/eccodes libraries)

### 5.2 User-Provided Script Analysis

**Script**: `ecmwf_scda_wind_to_settlement_periods.py` (250+ lines)

**Current Capabilities**:
```python
# Single-point download
def main():
    lat = 51.5  # Single location (hardcoded)
    lon = -0.1
    
    # Pick latest forecast run (06z or 18z preferred)
    run = _pick_latest_run(now_utc, candidate_cycles=["06", "18"])
    
    # Download GRIB file (~50 MB)
    grib_url = f"{base_url}/{best_grib_name}"
    _download_grib(grib_url, out_grib)
    
    # Extract U10/V10 time series at point
    u10 = _open_grib_point_timeseries(out_grib, lat, lon, "u10")
    v10 = _open_grib_point_timeseries(out_grib, lat, lon, "v10")
    
    # Calculate wind speed
    wind = np.sqrt(u10**2 + v10**2)
    
    # Interpolate to 30-min settlement periods
    wind_30min = _to_30min_settlement_periods(wind_3hourly)
    
    # Output CSV with volatility and ramp flags
    output_csv(wind_30min, "ecmwf_wind_forecast.csv")
```

**Strengths**:
- ✅ Robust forecast run selection (handles missing data)
- ✅ Settlement period alignment (critical for GB market)
- ✅ Ramp detection logic (>2 m/s change = high volatility)
- ✅ CSV output format (easy to ingest to BigQuery)

**Limitations**:
- ❌ Single location only (needs multi-turbine support)
- ❌ No BigQuery integration (manual CSV upload)
- ❌ No deduplication (can download same forecast multiple times)
- ❌ No error handling for network failures

### 5.3 Required Modifications

#### A. Multi-Location Download
```python
# Modified script structure
def download_ecmwf_for_all_turbines():
    """
    Download ECMWF wind data for all 43 offshore wind farms
    """
    from google.cloud import bigquery
    
    # Fetch turbine locations from BigQuery
    client = bigquery.Client(project="inner-cinema-476211-u9")
    query = """
    SELECT name, latitude, longitude, capacity_mw, gsp_zone
    FROM `inner-cinema-476211-u9.uk_energy_prod.offshore_wind_farms`
    WHERE status = 'Operational'
      AND latitude IS NOT NULL
    ORDER BY capacity_mw DESC
    """
    farms_df = client.query(query).to_dataframe()
    
    # Download in parallel (ThreadPoolExecutor)
    from concurrent.futures import ThreadPoolExecutor
    
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {}
        for idx, row in farms_df.iterrows():
            future = executor.submit(
                download_single_turbine,
                row['name'],
                row['latitude'],
                row['longitude'],
                forecast_run_time
            )
            futures[future] = row['name']
        
        for future in futures:
            farm_name = futures[future]
            try:
                wind_data = future.result(timeout=120)
                results.append({
                    'farm_name': farm_name,
                    'wind_forecast': wind_data
                })
                print(f"✅ {farm_name}")
            except Exception as e:
                print(f"❌ {farm_name}: {e}")
    
    return results
```

#### B. BigQuery Upload Integration
```python
def upload_to_bigquery(results, forecast_run_time):
    """
    Upload ECMWF wind forecasts to BigQuery
    
    Table: ecmwf_wind_turbine_forecasts
    Schema:
        - farm_name: STRING
        - forecast_run_utc: TIMESTAMP
        - settlement_date: DATE
        - settlement_period: INTEGER
        - wind_speed_ms: FLOAT
        - u10_ms: FLOAT
        - v10_ms: FLOAT
        - ramp_flag: INTEGER (1 if >2 m/s change)
        - volatility_ms: FLOAT
        - ingested_utc: TIMESTAMP
    """
    from google.cloud import bigquery
    import pandas as pd
    
    client = bigquery.Client(project="inner-cinema-476211-u9")
    table_id = "inner-cinema-476211-u9.uk_energy_prod.ecmwf_wind_turbine_forecasts"
    
    # Flatten results into DataFrame
    rows = []
    for result in results:
        farm = result['farm_name']
        for sp_data in result['wind_forecast']:
            rows.append({
                'farm_name': farm,
                'forecast_run_utc': forecast_run_time,
                'settlement_date': sp_data['date'],
                'settlement_period': sp_data['sp'],
                'wind_speed_ms': sp_data['wind_ms'],
                'u10_ms': sp_data['u10'],
                'v10_ms': sp_data['v10'],
                'ramp_flag': sp_data['ramp_flag'],
                'volatility_ms': sp_data['volatility'],
                'ingested_utc': pd.Timestamp.now(tz='UTC')
            })
    
    df = pd.DataFrame(rows)
    
    # Upload with WRITE_APPEND (deduplication needed)
    job_config = bigquery.LoadJobConfig(
        write_disposition="WRITE_APPEND",
        schema_update_options=["ALLOW_FIELD_ADDITION"]
    )
    
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()
    
    print(f"✅ Uploaded {len(df)} rows to {table_id}")
```

#### C. Deduplication Logic
```sql
-- Create deduplicated view
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.ecmwf_wind_latest` AS
SELECT
    farm_name,
    settlement_date,
    settlement_period,
    wind_speed_ms,
    u10_ms,
    v10_ms,
    ramp_flag,
    volatility_ms,
    forecast_run_utc,
    ingested_utc
FROM (
    SELECT *,
        ROW_NUMBER() OVER(
            PARTITION BY farm_name, settlement_date, settlement_period
            ORDER BY forecast_run_utc DESC, ingested_utc DESC
        ) as rn
    FROM `inner-cinema-476211-u9.uk_energy_prod.ecmwf_wind_turbine_forecasts`
)
WHERE rn = 1  -- Keep only latest forecast for each SP
```

---

## 6. Market Correlation Analysis

### 6.1 Hypothesis

**Wind Forecast Error → Imbalance Price Impact**

**Mechanism**:
1. NESO under-forecasts wind by 1 GW
2. System has 1 GW excess supply (long imbalance)
3. National Grid must pay generators to reduce output (System Buy Price falls)
4. Or wind over-forecasted → System short → Prices spike

**Expected Correlations**:
```
Large Positive Error (actual > forecast):
  → System LONG (excess supply)
  → SBP/SSP FALL (negative prices possible)
  → More SELL actions in BM (wind curtailment)
  
Large Negative Error (actual < forecast):
  → System SHORT (supply deficit)
  → SBP/SSP SPIKE (high prices)
  → More BUY actions in BM (gas/CCGT dispatch)
  → Constraint costs increase
```

### 6.2 Analysis Queries

#### A. Wind Error vs Imbalance Price
```sql
-- Calculate correlation between wind error and SSP
WITH wind_error AS (
    SELECT
        settlementDate,
        settlementPeriod,
        error_mw,
        ABS(error_mw) as abs_error_mw,
        CASE 
            WHEN error_mw > 1000 THEN 'Large Positive'
            WHEN error_mw < -1000 THEN 'Large Negative'
            ELSE 'Normal'
        END as error_category
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_forecast_error_sp`
    WHERE settlementDate >= '2025-10-01'
),
prices AS (
    SELECT
        DATE(settlementDate) as settlementDate,
        settlementPeriod,
        systemSellPrice as ssp,
        systemBuyPrice as sbp
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
    WHERE settlementDate >= '2025-10-01'
    GROUP BY settlementDate, settlementPeriod, ssp, sbp  -- Handle duplicates
)
SELECT
    w.error_category,
    COUNT(*) as num_periods,
    AVG(w.error_mw) as avg_error_mw,
    AVG(p.ssp) as avg_ssp,
    AVG(p.sbp) as avg_sbp,
    STDDEV(p.ssp) as stddev_ssp,
    MIN(p.ssp) as min_ssp,
    MAX(p.ssp) as max_ssp
FROM wind_error w
JOIN prices p ON w.settlementDate = p.settlementDate 
             AND w.settlementPeriod = p.settlementPeriod
GROUP BY w.error_category
ORDER BY w.error_category
```

**Expected Output**:
```
error_category    | num_periods | avg_error_mw | avg_ssp   | min_ssp | max_ssp
Large Positive    | 245         | +2150        | £45.20    | -£5.00  | £120.00
Normal            | 2890        | +50          | £67.80    | £15.00  | £180.00
Large Negative    | 182         | -1950        | £95.40    | £30.00  | £350.00
```

**Interpretation**: Large negative errors (wind shortfall) → Higher prices

#### B. Wind Error vs BM Intensity
```sql
-- Count balancing actions during wind forecast errors
WITH wind_error AS (
    SELECT
        settlementDate,
        settlementPeriod,
        error_mw,
        CASE 
            WHEN error_mw > 1000 THEN 'Over-Forecasted Wind'
            WHEN error_mw < -1000 THEN 'Under-Forecasted Wind'
            ELSE 'Normal'
        END as category
    FROM `inner-cinema-476211-u9.uk_energy_prod.wind_forecast_error_sp`
    WHERE settlementDate >= '2025-10-01'
),
bm_actions AS (
    SELECT
        DATE(acceptanceTime) as settlementDate,
        settlementPeriod,
        COUNT(*) as num_acceptances,
        SUM(ABS(acceptanceVolume)) as total_volume_mw,
        SUM(CASE WHEN so_flag THEN 1 ELSE 0 END) as num_so_flags
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
    WHERE validation_flag = 'Valid'
      AND acceptanceTime >= '2025-10-01'
    GROUP BY settlementDate, settlementPeriod
)
SELECT
    w.category,
    COUNT(*) as num_periods,
    AVG(b.num_acceptances) as avg_acceptances,
    AVG(b.total_volume_mw) as avg_volume_mw,
    AVG(b.num_so_flags) as avg_so_flags
FROM wind_error w
LEFT JOIN bm_actions b ON w.settlementDate = b.settlementDate 
                      AND w.settlementPeriod = b.settlementPeriod
GROUP BY w.category
ORDER BY w.category
```

**Expected Output**:
```
category               | num_periods | avg_acceptances | avg_volume_mw | avg_so_flags
Over-Forecasted Wind   | 245         | 45              | 850           | 15
Normal                 | 2890        | 32              | 520           | 8
Under-Forecasted Wind  | 182         | 58              | 1200          | 22
```

**Interpretation**: Wind shortfalls trigger more BM actions and SO flags (system stress)

#### C. Statistical Correlation Coefficient
```python
# Calculate Pearson correlation in Python
import pandas as pd
from scipy.stats import pearsonr
from google.cloud import bigquery

client = bigquery.Client(project="inner-cinema-476211-u9")

query = """
SELECT
    w.error_mw,
    c.systemSellPrice as ssp
FROM `inner-cinema-476211-u9.uk_energy_prod.wind_forecast_error_sp` w
JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs` c
    ON w.settlementDate = DATE(c.settlementDate)
    AND w.settlementPeriod = c.settlementPeriod
WHERE w.settlementDate >= '2025-10-01'
"""

df = client.query(query).to_dataframe()

# Calculate correlation
corr, p_value = pearsonr(df['error_mw'], df['ssp'])

print(f"Correlation between wind error and SSP: {corr:.3f}")
print(f"P-value: {p_value:.4f}")
print(f"Interpretation: {'Significant' if p_value < 0.05 else 'Not significant'}")

# Expected: Negative correlation (under-forecast wind → higher prices)
# corr ~ -0.25 to -0.45 (moderate negative correlation)
```

### 6.3 Trading Signal Logic

```python
def generate_trading_signal(wind_error_mw, current_ssp, forecast_horizon_hours):
    """
    Generate battery trading signal based on wind forecast error
    
    Args:
        wind_error_mw: Current wind forecast error (positive = over-forecast)
        current_ssp: Current imbalance price (£/MWh)
        forecast_horizon_hours: Hours until next forecast update
    
    Returns:
        dict with action ('CHARGE', 'DISCHARGE', 'HOLD') and confidence
    """
    
    # Thresholds (to be calibrated from correlation analysis)
    LARGE_ERROR_THRESHOLD = 1000  # MW
    HIGH_PRICE_THRESHOLD = 80     # £/MWh
    LOW_PRICE_THRESHOLD = 30      # £/MWh
    
    # Scenario 1: Large under-forecast (wind shortfall expected)
    if wind_error_mw < -LARGE_ERROR_THRESHOLD and forecast_horizon_hours < 6:
        # Wind lower than forecast → System short → Prices likely to spike
        return {
            'action': 'CHARGE_NOW_DISCHARGE_LATER',
            'reason': f'Wind shortfall {abs(wind_error_mw):.0f} MW detected',
            'confidence': 'HIGH',
            'expected_price_move': 'UP',
            'target_discharge_time': 'Next 2-6 hours'
        }
    
    # Scenario 2: Large over-forecast (wind surplus expected)
    elif wind_error_mw > LARGE_ERROR_THRESHOLD:
        # Wind higher than forecast → System long → Prices likely to fall
        return {
            'action': 'DISCHARGE_NOW' if current_ssp > HIGH_PRICE_THRESHOLD else 'HOLD',
            'reason': f'Wind surplus {wind_error_mw:.0f} MW detected',
            'confidence': 'MEDIUM',
            'expected_price_move': 'DOWN',
            'target_charge_time': 'Next 1-3 hours (wait for price drop)'
        }
    
    # Scenario 3: Normal error range
    else:
        return {
            'action': 'HOLD',
            'reason': 'Wind forecast error within normal range',
            'confidence': 'LOW',
            'expected_price_move': 'STABLE'
        }
```

---

## 7. Wind Drop Detection System

### 7.1 Comparison: NESO vs ECMWF Data

**Question**: Does NESO data show wind speed drops?

**Answer**: NESO provides **generation output** (MW), NOT raw wind speed (m/s)

**Key Distinctions**:

| Data Source | Variable | Unit | Update Frequency | Spatial Resolution |
|-------------|----------|------|------------------|-------------------|
| **NESO BMRS** | Wind generation forecast | MW | Hourly (updated every 30 min) | Aggregate GB |
| **NESO BMRS** | Actual wind generation | MW | 30-min settlement periods | Aggregate GB (WIND fuel type) |
| **ECMWF IFS** | 10m wind speed (U10/V10) | m/s | 4x daily (00z/06z/12z/18z) | 0.25° grid (~28 km) |
| **ECMWF IFS** | Forecast horizon | 10 days | - | - |

**Wind Speed → Generation Relationship**:
```
Wind Speed (m/s)  | Turbine Output  | Comments
0 - 3             | 0%              | Below cut-in
3 - 12            | 10-100%         | Linear ramp (varies by turbine model)
12 - 25           | 100%            | Rated capacity
> 25              | 0%              | Cut-out (safety shutdown)
```

**Key Insight**: ECMWF weather data shows **physical wind conditions**, while NESO shows **electrical output**. ECMWF may detect weather-driven wind drops earlier than NESO updates its generation forecasts.

### 7.2 Lead Time Analysis

**Hypothesis**: ECMWF weather forecasts update 4x daily, while NESO generation forecasts update every 30 minutes but are based on weather models run hours earlier.

**Test Scenario**: Atlantic weather front approaching Scotland
1. **T-12 hours**: ECMWF 06z forecast shows wind speed drop at Scottish offshore farms
2. **T-6 hours**: NESO generation forecast still shows high wind output (stale weather input)
3. **T-2 hours**: NESO updates generation forecast (wind drop now reflected)
4. **T-0 hours**: Actual wind generation drops (market reacts, prices spike)

**Early Warning Value**: 6-10 hour lead time for battery dispatch planning

**Implementation**:
```python
def detect_wind_drop_early(ecmwf_data, neso_data):
    """
    Compare ECMWF weather forecast to NESO generation forecast
    Alert if ECMWF shows wind drop but NESO forecast still high
    
    Args:
        ecmwf_data: DataFrame with wind_speed_ms by farm and SP
        neso_data: DataFrame with forecast_mw by SP (aggregate GB)
    
    Returns:
        dict with alert status and lead time
    """
    
    # Aggregate ECMWF farm-level data to GB total
    # (Requires capacity factor conversion: m/s → MW)
    ecmwf_gb_total = calculate_gb_wind_from_weather(ecmwf_data)
    
    # Compare ECMWF weather-implied generation to NESO forecast
    for sp in settlement_periods:
        ecmwf_implied_mw = ecmwf_gb_total[sp]
        neso_forecast_mw = neso_data[sp]
        
        difference = ecmwf_implied_mw - neso_forecast_mw
        
        # Alert if ECMWF shows significant drop not in NESO forecast
        if difference < -1500:  # 1.5 GW discrepancy
            lead_time_hours = (sp_timestamp - current_time).total_seconds() / 3600
            
            return {
                'alert': 'WIND_DROP_DETECTED',
                'ecmwf_implied_mw': ecmwf_implied_mw,
                'neso_forecast_mw': neso_forecast_mw,
                'difference_mw': difference,
                'lead_time_hours': lead_time_hours,
                'settlement_period': sp,
                'action': 'PREPARE_DISCHARGE' if lead_time_hours > 4 else 'DISCHARGE_NOW'
            }
    
    return {'alert': 'NORMAL'}
```

**Challenges**:
1. **Power Curve Mapping**: Need turbine model-specific power curves to convert m/s → MW
2. **Curtailment**: NESO may curtail wind even if weather good (grid constraints)
3. **Offshore vs Onshore**: ECMWF offshore data only covers 60% of GB wind (need onshore too)

### 7.3 Validation Strategy

**Step 1**: Historical Backtest
- Download ECMWF archive data for October 2025 (high wind period)
- Compare ECMWF 06z forecast to NESO 06:00 generation forecast
- Measure lead time for wind drop detection
- Calculate precision/recall for alerts

**Step 2**: Real-Time Monitoring (30 days)
- Run ECMWF download every 6 hours (06z, 18z)
- Compare to NESO forecast updates
- Log discrepancies > 1 GW
- Track market price response

**Step 3**: Refinement
- Calibrate alert threshold (1.5 GW vs 2.0 GW)
- Add regional filters (Scottish drops more impactful than English Channel)
- Integrate with battery SOC and trading position

---

## 8. Implementation Roadmap

### Phase 2A: Data Integration (Weeks 1-2)

**Tasks**:
1. ✅ **Extract offshore wind farm data** (COMPLETE)
   - 43 farms with lat/lon from BigQuery
   - Schema verified: `offshore_wind_farms` table

2. 🔄 **BM Unit mapping** (IN PROGRESS)
   - Research NESO BMU registration API
   - Create `wind_farm_to_bmu` lookup table
   - Fields: `farm_name`, `bmUnitId`, `capacity_mw`, `latitude`, `longitude`

3. 📋 **Modify ECMWF script for multi-turbine** (PENDING)
   - Adapt `ecmwf_scda_wind_to_settlement_periods.py`
   - Add parallel download logic (ThreadPoolExecutor)
   - Implement BigQuery upload function
   - Test with 5 farms before full rollout

4. 📋 **Create BigQuery table** (PENDING)
   - Table: `ecmwf_wind_turbine_forecasts`
   - Schema: farm_name, forecast_run_utc, settlement_date/period, wind_speed_ms, ramp_flag
   - View: `ecmwf_wind_latest` (deduplicated)

**Deliverables**:
- Modified Python script: `ecmwf_multi_turbine_downloader.py`
- Cron job: Run every 6 hours (after 06z/18z forecast release)
- BigQuery table populated with 72-hour forecasts for 43 farms

### Phase 2B: Analysis & Validation (Weeks 3-4)

**Tasks**:
5. 📋 **Turbine-level forecast vs actual** (PENDING)
   - Query: Compare ECMWF weather to BM unit output
   - Metrics: Forecast accuracy by farm, region, time-of-day
   - Output: `wind_turbine_forecast_accuracy` view

6. 📋 **Wind drop detection analysis** (PENDING)
   - Historical backtest: Oct 2025 wind events
   - Measure ECMWF lead time vs NESO forecast updates
   - Precision/recall for >1 GW wind drops

7. 📋 **Market correlation analysis** (PENDING)
   - Run wind error vs SSP correlation query
   - Calculate Pearson coefficient
   - Identify high-value trading periods (error >2 GW → price spike >£100/MWh)

**Deliverables**:
- Python script: `analyze_wind_turbine_accuracy.py`
- Report: `WIND_DROP_DETECTION_VALIDATION.md`
- Dashboard section: Correlation metrics (A35:F40)

### Phase 2C: Dashboard & Visualization (Weeks 5-6)

**Tasks**:
8. 📋 **Design graphical presentation** (PENDING)
   - UK map with offshore wind farms (colored by forecast error)
   - Time series chart: ECMWF vs NESO vs Actual (overlaid)
   - Heatmap: Error by hour-of-day and region
   - Alert panel: Wind drop warnings with lead time

9. 📋 **Integrate into Google Sheets** (PENDING)
   - New sheet: "Wind Turbine Analysis"
   - Sections:
     - A1: Regional forecast accuracy (Scottish vs English farms)
     - A10: Top 10 farms by capacity with error metrics
     - A20: ECMWF vs NESO comparison chart
     - A30: Wind drop alerts (last 7 days)

10. 📋 **Deploy automated pipeline** (PENDING)
    - Cron job: ECMWF download every 6 hours
    - Cron job: Dashboard refresh every 30 minutes
    - Logging: Track download failures and alert skipped runs

**Deliverables**:
- Python script: `update_wind_turbine_dashboard.py`
- Google Sheets: "Wind Turbine Analysis" sheet
- Apps Script: Interactive map with farm selection
- Deployment guide: `WIND_TURBINE_DEPLOYMENT.md`

### Phase 2D: Trading Integration (Weeks 7-8)

**Tasks**:
11. 📋 **Build early warning system** (PENDING)
    - Real-time alerts: Wind drop detected (>1.5 GW, >4 hour lead time)
    - SMS/email notifications to trading desk
    - Integration with battery dispatch system

12. 📋 **Backtesting trading strategy** (PENDING)
    - Simulate battery trades using wind drop signals
    - Metrics: Revenue uplift vs baseline, win rate, avg profit per trade
    - Risk analysis: False positive cost, missed opportunity cost

**Deliverables**:
- Python script: `wind_drop_trading_alerts.py`
- Report: `WIND_TRADING_BACKTEST_RESULTS.md`
- Integration: Webhook to battery dispatch API

---

## 9. Technical Reference

### 9.1 Key Files

**Current System (Phase 1)**:
- `update_live_metrics.py` - Dashboard refresh with wind metrics (lines 997-1909)
- `analyze_wind_forecast_accuracy.py` - Analysis tools and view creation (405 lines)
- `WIND_FORECAST_ANALYSIS.md` - Phase 1 documentation (500+ lines)

**Phase 2 Development**:
- `ecmwf_scda_wind_to_settlement_periods.py` - User-provided ECMWF script (250+ lines)
- `ecmwf_multi_turbine_downloader.py` - TO BE CREATED (multi-location download)
- `analyze_wind_turbine_accuracy.py` - TO BE CREATED (turbine-level analysis)
- `update_wind_turbine_dashboard.py` - TO BE CREATED (dashboard integration)
- `wind_drop_trading_alerts.py` - TO BE CREATED (trading signals)

**Documentation**:
- `WIND_FORECASTING_PROJECT.md` - This file (comprehensive overview)
- `docs/WIND_FARM_MAPPING_COMPLETE.md` - Offshore farm data summary (575 lines)
- `PROJECT_CONFIGURATION.md` - BigQuery settings and credentials
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Schema reference

### 9.2 BigQuery Tables & Views

**Phase 1 (Aggregate GB)**:
- `bmrs_windfor` / `bmrs_windfor_iris` - NESO generation forecasts
- `bmrs_fuelinst` / `bmrs_fuelinst_iris` - Actual wind generation
- `wind_forecast_sp` - Hourly forecasts aligned to 30-min SPs (VIEW)
- `wind_outturn_sp` - Actual wind generation (VIEW)
- `wind_forecast_error_sp` - Error metrics with ramp detection (VIEW)
- `wind_forecast_error_daily` - Daily rollups (VIEW)

**Phase 2 (Turbine-Level)**:
- `offshore_wind_farms` - 43 farms with GPS coordinates (TABLE)
- `ecmwf_wind_turbine_forecasts` - ECMWF weather data by farm (TO BE CREATED)
- `ecmwf_wind_latest` - Deduplicated latest forecasts (TO BE CREATED)
- `wind_farm_to_bmu` - Farm name to BM Unit ID mapping (TO BE CREATED)
- `wind_turbine_forecast_accuracy` - Farm-level error analysis (TO BE CREATED)
- `wind_drop_detection` - Early warning logic (TO BE CREATED)
- `wind_market_correlation` - Error vs price analysis (TO BE CREATED)

**Market Data**:
- `bmrs_costs` - Imbalance prices (SSP/SBP)
- `bmrs_boalf_complete` - Balancing acceptances with prices
- `bmrs_disbsad` - Volume-weighted settlement proxy

### 9.3 Performance Benchmarks

**Current System**:
- Dashboard refresh: 17.9 seconds total
  - BigQuery queries: 8.3s (15 parallel queries)
  - Wind metrics query: 5.8s
  - Sheets API flush: 1.3s
  - Connection time: 3.1s (Tailscale VPN overhead)

**Phase 2 Targets**:
- ECMWF download (43 farms): <120 seconds (parallel)
- BigQuery upload: <30 seconds
- Turbine-level dashboard refresh: <45 seconds (combined with main dashboard)

### 9.4 Data Quality & Coverage

**Phase 1 Metrics**:
- NESO forecast coverage: Oct 2025 → present (2+ months)
- Actual wind coverage: 2020 → present (5+ years)
- Data freshness: D-1 complete settlement (yesterday's data available by 06:00)
- Missing data: <0.1% (occasional IRIS pipeline gaps)

**Phase 2 Expected**:
- Offshore farm coverage: 43 farms, 16,410 MW (100% operational farms)
- ECMWF coverage: 10-day forecast horizon, 3-hourly resolution
- BM Unit mapping: 33 farms with known BM IDs, 10 farms need manual research
- Spatial coverage: Scottish + English North Sea + Irish Sea + English Channel

### 9.5 Dependencies

**Python Packages**:
```bash
pip3 install google-cloud-bigquery db-dtypes pyarrow pandas gspread
pip3 install cfgrib eccodes numpy scipy  # For ECMWF GRIB processing
```

**External Services**:
- ECMWF Open Data: https://data.ecmwf.int/forecasts/ (free, no API key)
- NESO BMRS API: https://api.bmreports.com/BMRS/ (free, no key for most streams)
- Google BigQuery: `inner-cinema-476211-u9` project (US location)
- Google Sheets API v4: Credentials in `inner-cinema-credentials.json`

**Infrastructure**:
- AlmaLinux server (94.237.55.234): IRIS real-time pipeline
- Cron jobs: Dashboard refresh (5 min), ECMWF download (6 hours)
- Tailscale VPN: Secure access to deployment server

---

## 10. Next Steps

### Immediate Actions (This Week)

1. **Performance Investigation** (if user continues experiencing slowness):
   - Test Tailscale connection latency: `ping -c 100 94.237.55.234`
   - Test BigQuery API response time: `time bq query --project_id=inner-cinema-476211-u9 'SELECT 1'`
   - Test Sheets API response time: Measure gspread.authorize() duration
   - Compare performance with/without Tailscale VPN

2. **BM Unit Mapping Research**:
   - Check NESO API documentation for BMU registration endpoint
   - Search existing data for wind farm → BM Unit lookup
   - Manual mapping for top 10 farms (covers 80% of capacity)

3. **ECMWF Script Modification**:
   - Create `ecmwf_multi_turbine_downloader.py` with parallel logic
   - Test download for 5 farms (Hornsea Two, Seagreen, Moray East, Triton Knoll, Walney)
   - Verify CSV output aligns to settlement periods correctly

### Mid-Term Goals (Next 2-4 Weeks)

4. **BigQuery Table Setup**:
   - Create `ecmwf_wind_turbine_forecasts` table with proper schema
   - Test upload from modified Python script
   - Create deduplicated view `ecmwf_wind_latest`

5. **Validation Analysis**:
   - Historical backtest: Oct 17-23, 2025 (high wind event)
   - Compare ECMWF weather to NESO forecast lead times
   - Calculate correlation: Wind error → Imbalance prices

6. **Dashboard Prototype**:
   - Create "Wind Turbine Analysis" sheet in Google Sheets
   - Add regional forecast accuracy table
   - Add ECMWF vs NESO comparison chart

### Long-Term Vision (Next 2-3 Months)

7. **Full Production Deployment**:
   - Automated ECMWF download pipeline (cron job every 6 hours)
   - Real-time wind drop alerts via SMS/email
   - Integration with battery dispatch system

8. **Advanced Features**:
   - Machine learning: Predict imbalance prices from wind + demand + interconnector flows
   - Offshore vs onshore split analysis
   - Regional constraint analysis (Scottish export limitations)

9. **Expansion to Other Renewables**:
   - Solar forecast accuracy (BMRS B1440)
   - Interconnector flow forecasts (BMRS B1620)
   - Demand forecast accuracy (BMRS INDOD vs actual)

---

## 11. FAQ

**Q: Why use ECMWF instead of just NESO forecasts?**  
A: ECMWF provides raw weather data (wind speed m/s) at turbine locations, potentially showing wind drops earlier than NESO's aggregate generation forecasts. This could provide 4-10 hour lead time for trading decisions.

**Q: How accurate are NESO wind forecasts?**  
A: Current analysis shows 18.7% WAPE with -1075 MW bias (under-forecasting). This is within industry norms (15-20%) but represents significant market impact (~£2M/day at £80/MWh).

**Q: Can we predict imbalance prices from wind errors?**  
A: Initial hypothesis suggests moderate negative correlation (-0.25 to -0.45). Large wind forecast errors likely contribute to price volatility but are not the only factor (demand errors, generator outages, interconnector flows also matter).

**Q: Why do midnight hours have 10 GW errors?**  
A: NESO forecasts are updated during day-ahead market (typically 10:00-14:00). By midnight, forecasts are 10-14 hours stale, leading to large deviations. Fresh forecasts at 04:00-06:00 show much better accuracy (<500 MW error).

**Q: What's the trading signal confidence level?**  
A: To be calibrated after backtesting. Initial target: 60-70% precision (60% of alerts lead to profitable trades) with 40-50% recall (catch 40% of high-value opportunities).

**Q: How much additional data will ECMWF integration generate?**  
A: ~43 farms × 48 SPs/day × 10 days forecast horizon = 20,640 rows/day (~600 KB/day). Annual storage: ~220 MB (negligible cost).

**Q: Is the system real-time?**  
A: Phase 1 (NESO) is real-time (5-minute dashboard refresh). Phase 2 (ECMWF) will be near-real-time (6-hour forecast updates, 30-minute dashboard refresh).

---

## 12. Glossary

**BM (Balancing Mechanism)**: Market where National Grid balances supply/demand in real-time  
**BMRS**: Balancing Mechanism Reporting Service (NESO data platform)  
**BOALF**: Balancing Offer Acceptance Level Flag (individual acceptance records)  
**ECMWF**: European Centre for Medium-Range Weather Forecasts  
**IFS SCDA**: Integrated Forecasting System Short Cut-off (ECMWF data stream)  
**NESO**: National Energy System Operator (formerly National Grid ESO)  
**SP**: Settlement Period (30-minute trading unit, 1-48 per day)  
**SSP/SBP**: System Sell Price / System Buy Price (imbalance prices, merged since Nov 2015)  
**WAPE**: Weighted Absolute Percentage Error (preferred over MAPE for zero-valued actuals)  
**Ramp Miss**: Large difference between forecast and actual generation change (>500 MW/30min)  
**Bias**: Systematic forecast error (negative = under-forecasting, positive = over-forecasting)  
**GRIB2**: Gridded Binary format for weather data  
**U10/V10**: 10-meter wind components (eastward/northward, m/s)

---

**Document Status**: ✅ Complete - Ready for Phase 2A implementation  
**Last Updated**: December 30, 2025  
**Next Review**: After BM Unit mapping complete (Target: Week of Jan 6, 2026)

---

*For questions or updates, contact: george@upowerenergy.uk*
