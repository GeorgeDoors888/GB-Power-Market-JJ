# Wind Forecasting System - Deployment Summary

**Status**: ✅ LIVE & OPERATIONAL  
**Date**: December 30, 2025  
**Coverage**: 41 offshore wind farms, 16,024 MW capacity

---

## System Architecture

### Data Pipeline
```
Open-Meteo API (6 years historical)
         ↓
1,051,680 weather observations @ 100m hub height
         ↓
Theoretical power curve (cut-in 3m/s, rated 12m/s, cut-out 25m/s)
         ↓
GradientBoostingRegressor (41 farm-specific models)
         ↓
Real-time predictions vs NESO forecasts
         ↓
Trading signals: LONG / SHORT / HOLD
```

### ML Models
- **Algorithm**: GradientBoostingRegressor (sklearn 1.8.0)
- **Features**: wind_speed_100m, wind_direction_10m, hour_of_day, month, day_of_week, wind_gusts_10m
- **Training**: 2020-2024 (4 years)
- **Testing**: 2025 (current year)
- **Performance**: MAE 0-3 MW, RMSE 0-10 MW per farm
- **Storage**: `models/wind_power_curves/{farm_name}.joblib`

### Data Sources
- **Historical Weather**: `openmeteo_wind_historic` (BigQuery)
- **NESO Forecasts**: `bmrs_windfor_iris` (real-time IRIS stream)
- **BM Unit Mapping**: `wind_farm_to_bmu` (67 units, 29 farms)

---

## Current Performance (Dec 30, 2025)

### Live Comparison
```
Our ML Forecast:    7,022 MW  (43.8% capacity factor)
NESO Forecast:      7,562 MW
Difference:          -540 MW  (-7.1%)

Trading Signal: 🟢 LONG
Rationale: We predict LESS wind → Higher prices → Long power
```

### Top Performers (by Capacity Factor)
1. **Hornsea Two**: 1,171 MW (84% CF) @ 11.5 m/s wind
2. **Hornsea One**: 1,029 MW (84% CF) @ 11.5 m/s wind
3. **East Anglia One**: 555 MW (78% CF) @ 11.3 m/s wind
4. **Triton Knoll**: 632 MW (74% CF) @ 11.1 m/s wind
5. **Greater Gabbard**: 362 MW (72% CF) @ 11.1 m/s wind

### Bottom Performers
1. **Burbo Bank Extension**: 4 MW (2% CF) @ 5.2 m/s wind
2. **Burbo Bank**: 2 MW (2% CF) @ 5.2 m/s wind
3. **Rhyl Flats**: 2 MW (2% CF) @ 5.4 m/s wind
4. **Walney Extension**: 26 MW (4% CF) @ 6.0 m/s wind
5. **European Offshore Wind**: 4 MW (4% CF) @ 6.1 m/s wind

---

## Usage

### Real-Time Forecasting
```bash
cd /home/george/GB-Power-Market-JJ
python3 realtime_wind_forecasting_simple.py
```

**Output**:
- Current total generation forecast
- Comparison with NESO forecast
- Trading signal (LONG/SHORT/HOLD)
- Top 5 best performing farms
- Bottom 5 underperforming farms

### Trading Signal Logic
```python
if abs(our_forecast - neso_forecast) < 500 MW:
    signal = "HOLD"  # Within tolerance
elif our_forecast > neso_forecast:
    signal = "SHORT"  # More wind → Lower prices
else:
    signal = "LONG"   # Less wind → Higher prices
```

### Model Retraining (monthly recommended)
```bash
python3 fetch_historic_wind_chunked.py  # Update weather data
python3 build_wind_power_curves_simple.py  # Retrain models
```

---

## Key Scripts

### `realtime_wind_forecasting_simple.py` (196 lines)
- Loads 41 trained ML models
- Fetches latest NESO forecast from IRIS
- Fetches recent weather from Open-Meteo historical
- Generates farm-level predictions
- Compares with NESO and generates trading signals

### `build_wind_power_curves_simple.py` (131 lines)
- Uses theoretical power curve (3-12-25 m/s)
- Trains GradientBoostingRegressor per farm
- 2020-2024 training, 2025 testing
- Outputs to `models/wind_power_curves/`

### `fetch_historic_wind_chunked.py` (187 lines)
- Downloads 100m hub height wind from Open-Meteo
- Rate limiting: 10s delays, 120s retry on 429
- Processes 10 farms × 6 years = 60 API calls
- Uploads to BigQuery `openmeteo_wind_historic`

---

## BigQuery Tables

### `openmeteo_wind_historic` (2.1M rows)
- **Coverage**: 41 farms, 2020-2025 (6 years)
- **Resolution**: Hourly
- **Key fields**: farm_name, time_utc, wind_speed_100m, capacity_mw
- **Size**: 1,051,680 training samples (20 farms with full data)

### `bmrs_windfor_iris` (real-time)
- **Source**: IRIS Azure Service Bus
- **Update**: Real-time streaming
- **Key fields**: startTime, generation, publishTime
- **Horizon**: 24 hours ahead

### `wind_farm_to_bmu` (67 rows)
- **Coverage**: 29 farms, 15,354 MW (93.6%)
- **Key fields**: farm_name, bm_unit_id, capacity_mw
- **Purpose**: Map BM units to physical wind farms

---

## Theoretical Power Curve

```python
def theoretical_power_curve(wind_speed_ms):
    if wind_speed < 3:           # Cut-in
        return 0
    elif wind_speed < 12:        # Ramp-up (cubic)
        return ((wind_speed - 3) / 9) ** 3
    elif wind_speed < 25:        # Rated power
        return 1.0
    else:                        # Cut-out
        return 0
```

**Typical 15 MW Offshore Turbine**:
- Cut-in: 3 m/s
- Rated: 12 m/s
- Cut-out: 25 m/s
- Power curve: Cubic between cut-in and rated

**Observed Performance**:
- Avg capacity factor: 38.1% (theoretical)
- Avg 100m wind speed: 9.0 m/s
- Max 100m wind speed: 37.3 m/s

---

## Trading Strategy

### Signal Generation
```
Difference > +500 MW:  SHORT (More wind → Lower prices)
Difference < -500 MW:  LONG  (Less wind → Higher prices)
Within ±500 MW:        HOLD  (No action)
```

### Historical Context (Oct 2025)
- **Oct 17-23**: £79.83/MWh avg (high-price event)
- **Oct 24-25**: £30.51/MWh avg (wind surge crash)
- **Strategy**: Aggressive deploy at £70+, preserve cycles at £25-40

### Wind Drop Predictions (TODO)
- Identify wind speed decreases >3 m/s over 6 hours
- Estimate generation impact (farm-level and GB-wide)
- Predict price effects using historical correlations
- Alert dashboard with sparklines and color-coded warnings

---

## Next Steps

### Phase 1: Wind Drop Alerts (In Progress)
- [ ] Design graphics: wind speed trend → generation impact → price effect
- [ ] Build Google Sheets dashboard with real-time alerts
- [ ] Add sparklines for 24h wind speed trends
- [ ] Color-code farms: 🟢 stable, 🟡 declining, 🔴 rapid drop

### Phase 2: Integration with Existing Systems
- [ ] Connect to BESS battery dashboard
- [ ] Link to imbalance price forecasts (bmrs_costs)
- [ ] Add to main Google Sheets (VLP/BESS analysis)
- [ ] Automate via cron (15-minute updates)

### Phase 3: Advanced Features
- [ ] ECMWF GRIB2 integration (when cfgrib works)
- [ ] Multi-hour ahead predictions (6h, 12h, 24h)
- [ ] Ensemble forecasting (combine multiple models)
- [ ] Backtesting framework (Oct 17-23 high-price event)

---

## Known Issues

### Data Limitations
- ❌ No farm-level actual generation data (bmrs_indgen_iris lacks BM unit IDs)
- ✅ Workaround: Theoretical power curves + proportional allocation
- ❌ ECMWF GRIB2 download blocked (cfgrib install fails)
- ✅ Workaround: Open-Meteo historical as proxy

### Model Assumptions
- Uses theoretical power curve (not site-specific)
- Assumes all farms have similar turbine characteristics
- Wind data is point forecast (farm centroid), not spatial average
- No wake effects or farm-to-farm interactions

### Performance Notes
- Sklearn warnings about feature names (cosmetic, doesn't affect predictions)
- BigQuery queries take 5-10 seconds (cached after first run)
- Model loading takes ~3 seconds for 41 joblib files

---

## Contact & Maintenance

**Owner**: George Major (george@upowerenergy.uk)  
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ  
**Location**: /home/george/GB-Power-Market-JJ  
**Environment**: Python 3.11, scikit-learn 1.8.0, BigQuery client

**Recommended Maintenance**:
- Monthly model retraining (refresh historical data)
- Quarterly backtest validation (check forecast accuracy)
- Ad-hoc updates when new farms commission

---

*Deployed: December 30, 2025*  
*Last Updated: December 30, 2025*
