# GB Wind Forecast Accuracy Analysis

## Overview
This document describes the wind generation forecast accuracy tracking system for the GB power market. The system analyzes the difference between forecasted and actual wind generation to provide actionable insights for trading, balancing, and operational decisions.

## Data Sources

### Forecast Data (B1440 - Generation Forecasts)
**Source Tables**:
- `bmrs_windfor` - Historical wind forecasts (hourly granularity)
- `bmrs_windfor_iris` - Real-time wind forecasts (last 48 hours)

**Coverage**: October 2025 onwards (limited historical data)

**Granularity**: Hourly forecasts, mapped to settlement periods (2 SPs per hour)

**What it contains**: 
- Predicted wind generation in MW
- Publish time (when forecast was issued)
- Start time (forecast validity period)
- Forecast horizon (how far ahead the forecast was made)

### Actual Generation Data (B1630 - Actual/Estimated Generation)
**Source Tables**:
- `bmrs_fuelinst` - Historical actual wind generation
- `bmrs_fuelinst_iris` - Real-time actual wind generation

**Coverage**: 2020-present (extensive historical data)

**Granularity**: Settlement period (30 minutes)

**What it contains**:
- Actual wind generation in MW (aggregated onshore + offshore)
- Settlement date and period
- Updated near real-time via IRIS feed

### Important Data Characteristics
- **Forecast Source**: NESO (National Energy System Operator) generation forecasts, NOT raw weather forecasts
- **Forecast Type**: Generation output in MW, not wind speed or meteorological data
- **Forecast Horizon**: Typically day-ahead or within-day forecasts
- **Fuel Type Mapping**: `WIND` in bmrs_fuelinst = combined onshore + offshore wind

## BigQuery Views Architecture

### 1. `wind_forecast_sp`
Hourly wind forecasts aligned to settlement periods.

**Key Fields**:
- `settlement_date`, `settlement_period` - Time identifier
- `forecast_mw` - Predicted wind generation (MW)
- `publishTime` - When forecast was issued
- `forecast_horizon_hours` - Hours ahead forecast was made
- `forecast_rank` - Ranks forecasts by recency (1 = most recent)

**Logic**: Takes most recent forecast for each settlement period to avoid duplicate forecasts.

### 2. `wind_outturn_sp`
Actual wind generation by settlement period.

**Key Fields**:
- `settlement_date`, `settlement_period` - Time identifier
- `actual_mw_total` - Actual wind generation (MW)
- `actual_mw_onshore`, `actual_mw_offshore` - Split by type (placeholder: not available in bmrs_fuelinst)

**Logic**: Combines historical and IRIS real-time data with 2-day cutoff.

### 3. `wind_forecast_error_sp`
Joined forecast and actual data with error calculations.

**Key Fields**:
- All fields from forecast and actual tables
- `error_mw` = forecast_mw - actual_mw
- `abs_error_mw` = |error_mw|
- `abs_percentage_error` = |error_mw| / actual_mw * 100
- `actual_ramp_mw` = Change from previous SP
- `forecast_ramp_mw` = Forecast change from previous SP
- `ramp_miss_mw` = |forecast_ramp_mw - actual_ramp_mw|
- `large_ramp_miss_flag` = 1 if ramp_miss_mw > 500 MW
- `hour_of_day`, `day_of_week` - For pattern analysis

**Logic**: Inner join on settlement_date and settlement_period, filters out zero actual generation.

### 4. `wind_forecast_error_daily`
Daily rollups of forecast error metrics.

**Key Fields**:
- `settlement_date` - Date
- `num_periods` - Number of settlement periods with data
- `avg_actual_mw`, `avg_forecast_mw` - Average wind output
- `bias_mw` - Systematic forecast error (positive = over-forecast, negative = under-forecast)
- `mae_mw` - Mean Absolute Error
- `rmse_mw` - Root Mean Squared Error
- `wape_percent` - Weighted Absolute Percentage Error (preferred metric)
- `mape_percent` - Mean Absolute Percentage Error
- `avg_ramp_miss_mw` - Average ramp forecast error
- `max_ramp_miss_mw` - Maximum ramp miss in day
- `num_large_ramp_misses` - Count of large ramp misses (>500 MW)

## Error Metrics Explained

### WAPE (Weighted Absolute Percentage Error) ⭐ PREFERRED
**Formula**: `SUM(|error_mw|) / SUM(actual_mw) * 100`

**Why preferred**:
- Not distorted by low wind periods (denominator is sum, not individual values)
- Industry standard for power system forecasting
- Treats all errors proportionally to actual generation
- More stable than MAPE during wind lulls

**Interpretation**:
- <10%: Excellent forecast accuracy
- 10-20%: Good (typical for GB wind forecasting)
- 20-30%: Moderate accuracy
- >30%: Poor accuracy (indicates systematic issues)

**Current Performance**: ~19-34% WAPE (reasonable for short-term wind forecasting)

### MAPE (Mean Absolute Percentage Error)
**Formula**: `AVG(|error_mw| / actual_mw) * 100`

**Issues**:
- Highly sensitive to low wind periods (division by small numbers)
- Can be artificially inflated by a few bad periods
- Less reliable for power system applications

**When to use**: Comparing forecasts across different wind farms or technologies where denominator is never near zero.

### Bias (Systematic Error)
**Formula**: `AVG(forecast_mw - actual_mw)`

**Interpretation**:
- **Negative bias** (current: -1075 to -1847 MW): **Under-forecasting** - System expects less wind than actually generated
  - Trading impact: Miss opportunities to sell excess wind
  - Balancing impact: Need more upward balancing actions
- **Positive bias**: Over-forecasting - System expects more wind than generated
  - Trading impact: Risk of being short
  - Balancing impact: Need more downward balancing actions
- **Near-zero bias**: No systematic error (ideal)

**Current Observation**: Significant negative bias suggests NESO forecasts are consistently conservative.

### RMSE (Root Mean Squared Error)
**Formula**: `SQRT(AVG(error_mw²))`

**Purpose**: 
- Penalizes large errors more heavily than small errors
- Useful for identifying periods with extreme forecast misses
- Higher RMSE relative to MAE indicates "lumpy" errors (occasional large misses vs consistent small errors)

**Current Performance**: 2650-4762 MW (reasonable given GB has ~25-30 GW wind capacity)

### Ramp Miss
**Definition**: Failure to predict change in wind output between settlement periods.

**Formula**: `|forecast_ramp_mw - actual_ramp_mw|`

**Threshold**: Large ramp miss = >500 MW/30min error

**Why it matters**:
- Ramp events cause balancing challenges (need to change dispatch quickly)
- Missed ramps = unexpected imbalance prices
- Critical for battery/storage dispatch strategies

**Current Performance**: 9-25 large ramp misses per day (indicates difficulty predicting wind volatility)

## Hour-of-Day Patterns

Analysis of last 30 days shows:

**Midnight Hours (00:00-03:00)**:
- Highest forecast errors (~10-11 GW absolute error)
- Likely due to forecast publication timing (forecasts issued before midnight may be stale by 00:00-03:00)
- Strategy: Be cautious with midnight dispatch decisions, wait for updated forecasts

**Morning Hours (04:00-07:00)**:
- Errors drop to ~300-450 MW (better accuracy)
- Fresh day-ahead forecasts available

**Daytime Hours (08:00-19:00)**:
- Moderate errors (~300-950 MW)
- Forecast accuracy varies more (depends on weather system complexity)

**Evening Hours (20:00-23:00)**:
- Low-moderate errors (~200-800 MW)
- Within-day forecast updates help accuracy

**Trading Implication**: Avoid aggressive wind-dependent strategies around midnight. Most reliable forecasts in morning hours after fresh day-ahead updates.

## Dashboard Implementation

### Location
**Sheet**: Live Dashboard v2  
**Range**: A27:F34

### Layout
```
Row 27: 💨 WIND FORECAST ACCURACY (Section header)
Row 28: (Blank spacer)
Row 29: 📊 Forecast Error (WAPE)    | 18.70%      | [7-day sparkline]
Row 30: 📉 Forecast Bias            | -1075 MW    | [7-day sparkline]
Row 31: ⚡ Avg Actual Wind          | 7225 MW     | [7-day sparkline]
Row 32: 🔮 Avg Forecast Wind        | 6150 MW     | [7-day sparkline]
Row 33: ⚠️ Large Ramp Misses (>500MW/30min): 16
Row 34: 📅 Data: 2025-12-29
```

### Sparklines
- **WAPE** (red line): Shows forecast accuracy trend
- **Bias** (green/red symmetric column): Shows over/under forecasting trend
- **Actual Wind** (blue column): Shows wind output variability
- **Forecast Wind** (purple column): Shows forecast variability

### Auto-Refresh
- **Frequency**: Every 5 minutes (via cron)
- **Script**: `update_live_metrics.py`
- **Query Time**: ~6 seconds (parallel BigQuery execution)
- **Data Freshness**: D-1 complete settlement data (yesterday)

## Usage Guide

### For Traders
1. **Check WAPE**: <20% = reliable forecast, can trade aggressively
2. **Check Bias**: Negative = system under-forecasting, opportunity to sell excess wind
3. **Check Ramp Misses**: High count = volatile day, reduce position size
4. **Hour-of-day**: Avoid midnight trades, prioritize morning liquidity

### For Balancing Engineers
1. **Bias direction**: Indicates whether to lean towards more buy or sell actions
2. **RMSE vs MAE**: Large difference = expect occasional extreme events (need reserve headroom)
3. **Ramp miss count**: Indicates need for flexible balancing resources (batteries, fast gas)

### For Analysts
1. **WAPE trend**: Improving = forecasting getting better (less market volatility)
2. **Bias trend**: Persistent bias = systematic issue with NESO forecasting model
3. **Correlation with price**: High forecast error days = high imbalance prices (see optional analysis below)

## Limitations

### What This Analysis Does NOT Include
1. **Raw Weather Forecasts**: NESO forecasts are generation (MW), not meteorological data (wind speed, pressure, etc.)
2. **Met Office Data**: For actual weather forecasts, need separate Met Office / ECMWF integration
3. **Individual Wind Farm Data**: Aggregate GB wind only, not site-specific
4. **Offshore vs Onshore Split**: bmrs_fuelinst combines both (alternative table bmrs_wind_solar_gen has split but limited coverage)
5. **Curtailment**: Actual generation includes curtailed output, not potential output
6. **Forecast Uncertainty Bands**: NESO provides point forecasts, not probabilistic ranges

### Data Quality Notes
- Historical forecast data only from October 2025 onwards (recent IRIS deployment)
- Earlier forecasts may exist in other BMRS datasets (B1440 API endpoint) but not yet ingested
- Actual generation data very reliable (NESO operational data, verified)

## Optional: Market Impact Analysis

### Correlation with Imbalance Prices
**Hypothesis**: Large forecast errors → large imbalance prices (SSP/SBP spikes)

**Implementation** (future enhancement):
```sql
-- Join wind forecast errors with imbalance prices
SELECT 
    e.settlement_date,
    e.settlement_period,
    e.error_mw,
    e.abs_error_mw,
    c.systemSellPrice as ssp,
    c.systemBuyPrice as sbp,
    ABS(c.systemSellPrice - c.systemBuyPrice) as imbalance_spread
FROM wind_forecast_error_sp e
INNER JOIN bmrs_costs c
    ON e.settlement_date = CAST(c.settlementDate AS DATE)
    AND e.settlement_period = c.settlementPeriod
WHERE e.abs_error_mw > 1000  -- Large errors only
ORDER BY e.abs_error_mw DESC
```

**Expected Result**: Strong positive correlation between |error_mw| and imbalance price volatility.

### Correlation with BM Dispatch Intensity
**Hypothesis**: Large forecast errors → more balancing acceptances (BOALF)

**Implementation** (future enhancement):
```sql
-- Count acceptances during high forecast error periods
SELECT
    e.settlement_date,
    e.settlement_period,
    e.abs_error_mw,
    COUNT(DISTINCT b.acceptanceId) as num_acceptances,
    SUM(ABS(b.acceptanceVolume)) as total_accepted_mwh
FROM wind_forecast_error_sp e
INNER JOIN bmrs_boalf_complete b
    ON e.settlement_date = CAST(b.acceptanceTime AS DATE)
    -- Approximate: use hour match since acceptanceTime is continuous
WHERE e.abs_error_mw > 500
GROUP BY e.settlement_date, e.settlement_period, e.abs_error_mw
ORDER BY e.abs_error_mw DESC
```

**Expected Result**: More acceptances during large forecast errors (system scrambling to balance).

### Correlation with Constraint Periods
**Hypothesis**: Wind forecast errors exacerbate transmission constraints

**Implementation** (future enhancement): Compare high forecast error periods with constraint cost spikes from `bmrs_disbsad` or NESO constraint reports.

## Scripts Reference

### `analyze_wind_forecast_accuracy.py`
**Purpose**: Create BigQuery views and run sample analysis

**Usage**:
```bash
python3 analyze_wind_forecast_accuracy.py
```

**Outputs**:
- Creates 4 BigQuery views (wind_forecast_sp, wind_outturn_sp, wind_forecast_error_sp, wind_forecast_error_daily)
- Prints last 7 days forecast accuracy
- Prints hour-of-day error patterns

**Functions**:
- `create_wind_forecast_sp_view()` - Forecast data view
- `create_wind_outturn_sp_view()` - Actual data view
- `create_wind_forecast_error_sp_view()` - Joined error metrics
- `create_wind_forecast_error_daily_view()` - Daily rollups
- `get_latest_forecast_metrics(days)` - Fetch daily metrics DataFrame
- `get_intraday_forecast_comparison(date)` - Fetch SP-level comparison
- `get_hour_of_day_error_pattern()` - Analyze error patterns by hour

### `update_live_metrics.py`
**Purpose**: Auto-refresh dashboard with wind forecast metrics

**Usage**: Runs every 5 minutes via cron

**Relevant Function**: `get_wind_forecast_metrics(bq_client)`

**Returns**:
- `daily_metrics`: DataFrame with last 7 days
- `yesterday_sp`: DataFrame with 48 SPs actual vs forecast
- `latest_kpis`: dict with current WAPE, bias, ramp misses

**Dashboard Update**: Writes to A27:F34 with KPIs and sparklines

## Future Enhancements

### Proposed Improvements
1. **Longer Historical Data**: Backfill forecasts from Elexon B1440 API (2020+ available)
2. **Probabilistic Forecasts**: If NESO provides P10/P50/P90 ranges, add uncertainty analysis
3. **Offshore vs Onshore Split**: Use `bmrs_wind_solar_gen` for granular analysis (once data updated)
4. **Real-time Forecast Updates**: Track forecast updates throughout the day (multiple forecasts per SP)
5. **Seasonal Patterns**: Analyze error patterns by season (winter vs summer wind regimes)
6. **Weather Regime Classification**: Link forecast errors to weather patterns (low pressure systems, fronts)
7. **Rolling Skill Score**: Compare forecast performance vs persistence baseline
8. **Intraday Forecast Improvement**: Track how forecast accuracy improves as delivery approaches

### Proposed Charts (Todo #5)
1. **Time Series Chart**: 48 SP actual vs forecast (line chart, last 24h)
2. **Error Distribution**: Histogram of forecast errors (shows bias and spread)
3. **WAPE Trend**: Line chart over 90 days (trend direction)
4. **Ramp Miss Events**: Scatter plot (SP vs ramp miss magnitude)
5. **Hour-of-day Heatmap**: Color-coded error magnitude by hour and day-of-week

## Contact & Support

**Maintainer**: George Major (george@upowerenergy.uk)  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Documentation**: See `DOCUMENTATION_INDEX.md` for full project docs  
**Related Docs**: 
- `PROJECT_CONFIGURATION.md` - BigQuery setup
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Data pipeline details
- `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md` - IRIS real-time system

---

*Last Updated: December 29, 2025*  
*Document Version: 1.0*
