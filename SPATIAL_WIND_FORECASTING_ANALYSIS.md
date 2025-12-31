# Spatial Wind Forecasting Analysis - Upstream Wind Speed Prediction

**Date**: December 30, 2025  
**Concept**: Use wind measurements from upstream locations to predict wind arriving at turbines  
**Method**: Spatial-temporal correlation analysis with wind direction and travel time

---

## Concept Overview

### The Physics

Wind systems move across the UK following prevailing weather patterns:
- **Prevailing Direction**: Southwest → Northeast (60% of time)
- **Typical Speed**: 10-20 m/s at 100m altitude
- **Travel Time**: 50 km distance ≈ 1-2 hours advance warning
- **Persistence**: Wind speed changes gradually (not instantaneous)

### The Hypothesis

If we measure wind at **Location A** (upstream) at time **T**, we can predict wind at **Location B** (turbine) at time **T + Δt** where:
- Δt = distance / wind_speed
- Accuracy depends on: wind direction consistency, atmospheric stability, terrain effects

---

## UK Offshore Wind Farm Geography

### Spatial Clusters

**North Sea Cluster** (East Coast):
- Hornsea One/Two (54.0°N, 1.8°E) - 70 km offshore
- Dogger Bank (54.7°N, 1.8°E) - 130 km offshore
- Triton Knoll (53.3°N, 0.5°E) - 32 km offshore
- Race Bank (53.2°N, 0.4°E) - 27 km offshore

**Irish Sea Cluster** (West Coast):
- Walney Extension (54.1°N, -3.4°W)
- West of Duddon Sands (54.1°N, -3.5°W)
- Burbo Bank Extension (53.5°N, -3.3°W)

**Scottish Cluster** (North):
- Seagreen Phase 1 (56.5°N, -2.1°W) - 27 km offshore
- Moray East/West (57.7°N, -2.3°W) - 22 km offshore
- Beatrice (58.1°N, -3.0°W) - 13 km offshore

### Prevailing Wind Patterns

**Southwest Winds** (most common):
```
Atlantic Ocean → Irish Sea → North England → North Sea
                     ↓
              Walney, Burbo Bank (hit first)
                     ↓
              Hornsea, Triton Knoll (30-60 min later)
```

**Northwest Winds** (winter storms):
```
Scotland → North Sea
    ↓
Moray East/West (hit first)
    ↓
Hornsea, Dogger Bank (2-3 hours later)
```

---

## Data Analysis Approach

### Step 1: Identify Upstream/Downstream Pairs

For each wind direction sector, identify which farms are upstream/downstream:

**Example - Southwest Wind (225°)**:
- **Upstream**: Walney Extension (Irish Sea)
- **Downstream**: Hornsea One (North Sea)
- **Distance**: ~150 km
- **Travel Time**: 150 km / 15 m/s = 2.8 hours

### Step 2: Calculate Spatial Correlation

```python
# Pseudo-code
for direction in [0, 45, 90, 135, 180, 225, 270, 315]:
    upstream_farms = find_upstream_farms(direction)
    downstream_farms = find_downstream_farms(direction)
    
    for lag in [30min, 1h, 2h, 3h, 4h]:
        correlation = correlate(
            upstream_wind_speed(t),
            downstream_wind_speed(t + lag)
        )
```

### Step 3: Build Spatial Features

New ML features:
1. `upstream_wind_speed` - Wind at farm 150 km upstream
2. `upstream_wind_direction` - Direction of upstream wind
3. `travel_time_estimate` - Distance / wind_speed
4. `spatial_lag` - Time delay for optimal correlation
5. `upstream_wind_trend` - Is upstream wind increasing/decreasing?

---

## Expected Correlations

### Strong Correlation Scenarios

**1. Same Weather System** (0.7-0.9 correlation)
- Large-scale fronts (low pressure systems)
- Consistent wind direction (±15°)
- Short distance (<100 km)
- Short time lag (<2 hours)

**2. Prevailing Southwesterly** (0.6-0.8 correlation)
- Atlantic weather moving northeast
- Walney → Hornsea pathway
- 2-3 hour advance warning

### Weak Correlation Scenarios

**1. Local Sea Breeze** (0.2-0.4 correlation)
- Thermal circulation (day/night)
- Different for each farm
- Not spatially coherent

**2. Frontal Boundaries** (0.3-0.5 correlation)
- Sudden wind shifts
- Non-linear propagation
- Difficult to predict lag time

---

## Implementation Plan

### Phase 1: Data Preparation (1 hour)

Query to get wind speed at all farms with timestamps:

```sql
WITH farm_locations AS (
    SELECT 
        'Hornsea One' as farm_name, 54.0 as lat, 1.8 as lon
    UNION ALL
    SELECT 'Walney Extension', 54.1, -3.4
    UNION ALL
    SELECT 'Seagreen Phase 1', 56.5, -2.1
    -- ... all 29 farms
),
wind_data AS (
    SELECT 
        farm_name,
        time_utc,
        wind_speed_100m,
        wind_direction_10m
    FROM openmeteo_wind_historic
    WHERE time_utc >= '2024-01-01'
)
SELECT 
    w1.farm_name as farm1,
    w2.farm_name as farm2,
    w1.time_utc as time1,
    w2.time_utc as time2,
    w1.wind_speed_100m as wind1,
    w2.wind_speed_100m as wind2,
    w1.wind_direction_10m as direction1,
    -- Calculate distance and bearing between farms
    ST_DISTANCE(
        ST_GEOGPOINT(l1.lon, l1.lat),
        ST_GEOGPOINT(l2.lon, l2.lat)
    ) / 1000 as distance_km,
    ST_AZIMUTH(
        ST_GEOGPOINT(l1.lon, l1.lat),
        ST_GEOGPOINT(l2.lon, l2.lat)
    ) as bearing_degrees
FROM wind_data w1
JOIN wind_data w2 
    ON w2.time_utc BETWEEN w1.time_utc AND TIMESTAMP_ADD(w1.time_utc, INTERVAL 4 HOUR)
JOIN farm_locations l1 ON w1.farm_name = l1.farm_name
JOIN farm_locations l2 ON w2.farm_name = l2.farm_name
WHERE w1.farm_name != w2.farm_name
```

### Phase 2: Correlation Analysis (2 hours)

Calculate cross-correlations for all farm pairs:

```python
import pandas as pd
import numpy as np
from scipy.stats import pearsonr

def analyze_spatial_correlation(df):
    results = []
    
    for farm1 in df['farm1'].unique():
        for farm2 in df['farm2'].unique():
            if farm1 == farm2:
                continue
            
            pair_data = df[(df['farm1'] == farm1) & (df['farm2'] == farm2)]
            
            # Only consider when wind direction aligns with farm bearing
            wind_aligned = pair_data[
                abs(pair_data['direction1'] - pair_data['bearing_degrees']) < 30
            ]
            
            if len(wind_aligned) < 100:
                continue
            
            # Test different time lags
            for lag_hours in [0.5, 1, 2, 3, 4]:
                lag_data = wind_aligned[
                    abs(wind_aligned['time2'] - wind_aligned['time1'] - pd.Timedelta(hours=lag_hours)) < pd.Timedelta(minutes=30)
                ]
                
                if len(lag_data) > 50:
                    correlation, p_value = pearsonr(
                        lag_data['wind1'],
                        lag_data['wind2']
                    )
                    
                    results.append({
                        'farm1': farm1,
                        'farm2': farm2,
                        'distance_km': lag_data['distance_km'].mean(),
                        'lag_hours': lag_hours,
                        'correlation': correlation,
                        'p_value': p_value,
                        'n_samples': len(lag_data)
                    })
    
    return pd.DataFrame(results)
```

### Phase 3: Enhanced ML Model (3 hours)

Update training to include spatial features:

```python
def create_spatial_features(df, farm_name, upstream_farms):
    """
    Add features from upstream farms based on wind direction
    """
    spatial_features = []
    
    for idx, row in df.iterrows():
        wind_dir = row['wind_direction_10m']
        
        # Find best upstream farm for this wind direction
        best_upstream = find_best_upstream_farm(
            farm_name, 
            wind_dir, 
            upstream_farms
        )
        
        if best_upstream:
            # Get upstream wind from 1-3 hours ago
            optimal_lag = calculate_optimal_lag(
                farm_name, 
                best_upstream, 
                row['wind_speed_100m']
            )
            
            upstream_time = row['time_utc'] - pd.Timedelta(hours=optimal_lag)
            upstream_wind = get_wind_at_time(
                best_upstream, 
                upstream_time
            )
            
            spatial_features.append({
                'upstream_wind_speed': upstream_wind,
                'upstream_farm': best_upstream,
                'spatial_lag_hours': optimal_lag
            })
        else:
            spatial_features.append({
                'upstream_wind_speed': np.nan,
                'upstream_farm': None,
                'spatial_lag_hours': np.nan
            })
    
    return pd.DataFrame(spatial_features)

# Enhanced model with spatial features
features = [
    'wind_speed_100m',          # Current location
    'wind_direction_10m',
    'upstream_wind_speed',      # NEW: Upstream measurement
    'spatial_lag_hours',        # NEW: Travel time
    'hour_of_day',
    'month',
    'day_of_week',
    'wind_gusts_10m'
]

model = GradientBoostingRegressor(...)
model.fit(X_train[features], y_train)
```

---

## Expected Results

### Scenario 1: Strong Spatial Correlation (Best Case)

**Example**: Southwest wind, Walney → Hornsea
- **Correlation**: 0.75 at 2.5-hour lag
- **Current Model MAE**: 211 MW (Hornsea One)
- **Spatial Model MAE**: ~160 MW (25% improvement)
- **Use Case**: 2-3 hour advance warning of wind changes

### Scenario 2: Moderate Spatial Correlation

**Example**: Northwest wind, Moray → Hornsea
- **Correlation**: 0.55 at 3-hour lag
- **Current Model MAE**: 211 MW
- **Spatial Model MAE**: ~190 MW (10% improvement)
- **Use Case**: Long-range (3-4 hour) predictions

### Scenario 3: Weak Spatial Correlation

**Example**: Easterly wind (rare), local sea breeze
- **Correlation**: 0.30
- **Improvement**: Minimal (model should ignore these features)
- **Fallback**: Use only local wind speed features

---

## Advantages of Spatial Forecasting

### 1. Lead Time

**Current Model**: 0-1 hour forecast (based on current conditions)

**Spatial Model**: 2-4 hour forecast (based on upstream conditions)

**Trading Benefit**: 
- More time to position for wind drops/surges
- Better intraday market timing
- Reduced forecast uncertainty

### 2. Wind Front Detection

**Current**: Cannot predict sudden wind changes

**Spatial**: Detect approaching fronts
```
Time T: Walney sees wind drop from 15 m/s to 8 m/s
Time T+2h: Predict Hornsea will drop from 15 m/s to ~9 m/s
Action: Pre-position battery discharge for price spike
```

### 3. Directional Patterns

**Current**: Treats all wind directions equally

**Spatial**: Learns that SW wind is more predictable than E wind
- Higher confidence in SW wind forecasts
- Lower position sizing for E wind forecasts

---

## Challenges & Limitations

### 1. Data Requirements

**Need**: Wind measurements at multiple locations simultaneously
- ✅ Have: 41 offshore farms with hourly data
- ⚠️ Gap: Some farms only have 2020-2025 data
- ⚠️ Gap: No onshore weather stations in current dataset

**Solution**: Current 41-farm network provides sufficient spatial coverage

### 2. Wind Direction Accuracy

**Challenge**: 10m wind direction may differ from 100m direction
- Surface wind affected by sea surface
- Upper wind (100m) follows gradient wind

**Solution**: Use only cases where wind direction is consistent (±15°)

### 3. Complex Terrain Effects

**Challenge**: Land interaction, coastal effects
- Offshore wind slows near coast
- Channeling through valleys
- Wake effects from other farms

**Solution**: Include only offshore-to-offshore predictions (avoid coastal farms)

### 4. Frontal Boundaries

**Challenge**: Wind speed can change abruptly at fronts
- Cold front: sudden wind shift and acceleration
- Warm front: gradual wind increase

**Solution**: Detect fronts using rapid wind speed changes, use different model

---

## Implementation Script

```python
#!/usr/bin/env python3
"""
Spatial wind forecasting analysis
Analyze upstream/downstream correlations for advance warning
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from scipy.stats import pearsonr
import matplotlib.pyplot as plt

PROJECT_ID = "inner-cinema-476211-u9"
DATASET = "uk_energy_prod"

# Farm coordinates (approximate offshore locations)
FARM_COORDS = {
    'Hornsea One': (54.0, 1.8),
    'Hornsea Two': (53.9, 1.7),
    'Walney Extension': (54.1, -3.4),
    'Seagreen Phase 1': (56.5, -2.1),
    'Moray East': (57.7, -2.3),
    'Triton Knoll': (53.3, 0.5),
    'East Anglia One': (52.0, 2.0),
    'London Array': (51.7, 1.5),
    # ... add all 41 farms
}

def calculate_bearing(lat1, lon1, lat2, lon2):
    """Calculate bearing from point 1 to point 2 (degrees)"""
    import math
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = math.atan2(x, y)
    return (math.degrees(bearing) + 360) % 360

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km using Haversine formula"""
    import math
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def analyze_spatial_correlations():
    """
    Analyze spatial correlations between all farm pairs
    """
    client = bigquery.Client(project=PROJECT_ID, location="US")
    
    print("="*70)
    print("Spatial Wind Correlation Analysis")
    print("="*70)
    
    # Get wind data for all farms
    query = f"""
    SELECT 
        farm_name,
        time_utc,
        wind_speed_100m,
        wind_direction_10m
    FROM `{PROJECT_ID}.{DATASET}.openmeteo_wind_historic`
    WHERE time_utc >= '2024-01-01'
      AND time_utc < '2025-01-01'
      AND wind_speed_100m IS NOT NULL
    """
    
    print("\n📊 Loading wind data for 2024...")
    df = client.query(query).to_dataframe()
    print(f"✅ Loaded {len(df):,} observations")
    
    # Pivot to wide format (one column per farm)
    df_pivot = df.pivot(index='time_utc', columns='farm_name', values='wind_speed_100m')
    df_dir_pivot = df.pivot(index='time_utc', columns='farm_name', values='wind_direction_10m')
    
    # Analyze all pairs
    results = []
    
    farms = list(FARM_COORDS.keys())
    print(f"\n🔍 Analyzing {len(farms)} farms...")
    
    for farm1 in farms:
        if farm1 not in df_pivot.columns:
            continue
            
        lat1, lon1 = FARM_COORDS[farm1]
        
        for farm2 in farms:
            if farm1 == farm2 or farm2 not in df_pivot.columns:
                continue
            
            lat2, lon2 = FARM_COORDS[farm2]
            distance = calculate_distance(lat1, lon1, lat2, lon2)
            bearing = calculate_bearing(lat1, lon1, lat2, lon2)
            
            # Only consider pairs >30 km apart
            if distance < 30:
                continue
            
            # Test different time lags
            for lag_hours in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]:
                # Shift farm2 data by lag
                wind1 = df_pivot[farm1]
                wind2 = df_pivot[farm2].shift(-int(lag_hours * 2))  # 30-min resolution
                
                # Get wind direction for farm1
                wind_dir1 = df_dir_pivot[farm1]
                
                # Only consider times when wind direction aligns with bearing (±30°)
                aligned_mask = (
                    ((wind_dir1 - bearing).abs() < 30) |
                    ((wind_dir1 - bearing).abs() > 330)  # Handle 0/360 wraparound
                )
                
                wind1_aligned = wind1[aligned_mask]
                wind2_aligned = wind2[aligned_mask]
                
                # Remove NaN values
                valid_mask = wind1_aligned.notna() & wind2_aligned.notna()
                wind1_valid = wind1_aligned[valid_mask]
                wind2_valid = wind2_aligned[valid_mask]
                
                if len(wind1_valid) < 50:
                    continue
                
                # Calculate correlation
                correlation, p_value = pearsonr(wind1_valid, wind2_valid)
                
                # Calculate expected travel time
                avg_wind_speed = wind1_valid.mean()
                expected_travel_time = distance / (avg_wind_speed / 3.6) / 3600  # Convert m/s to hours
                
                results.append({
                    'upstream_farm': farm1,
                    'downstream_farm': farm2,
                    'distance_km': distance,
                    'bearing_degrees': bearing,
                    'lag_hours': lag_hours,
                    'correlation': correlation,
                    'p_value': p_value,
                    'n_samples': len(wind1_valid),
                    'avg_wind_speed_ms': avg_wind_speed,
                    'expected_travel_hours': expected_travel_time
                })
    
    results_df = pd.DataFrame(results)
    
    # Find best correlations
    print(f"\n✅ Analyzed {len(results_df):,} upstream/downstream pairs")
    
    # Filter to significant correlations
    significant = results_df[
        (results_df['p_value'] < 0.01) &
        (results_df['correlation'] > 0.5) &
        (results_df['n_samples'] > 100)
    ].sort_values('correlation', ascending=False)
    
    print(f"\n🎯 Top 10 Spatial Correlations:")
    print(f"{'Upstream Farm':<25} {'→ Downstream Farm':<25} {'Distance':>10} {'Lag':>8} {'Corr':>8} {'Samples':>10}")
    print("-"*100)
    
    for idx, row in significant.head(10).iterrows():
        print(f"{row['upstream_farm']:<25} → {row['downstream_farm']:<25} "
              f"{row['distance_km']:>8.0f} km {row['lag_hours']:>6.1f} h "
              f"{row['correlation']:>7.3f} {row['n_samples']:>10,.0f}")
    
    # Save results
    results_df.to_csv('spatial_wind_correlations.csv', index=False)
    print(f"\n✅ Full results saved to spatial_wind_correlations.csv")
    
    return results_df

if __name__ == "__main__":
    results = analyze_spatial_correlations()
```

---

## Expected Top Correlations

Based on UK geography and prevailing winds:

| Upstream Farm | Downstream Farm | Distance (km) | Optimal Lag | Expected Corr | Wind Pattern |
|---------------|-----------------|---------------|-------------|---------------|--------------|
| Walney Extension | Hornsea One | 150 | 2.5 hours | 0.70-0.80 | SW Prevailing |
| Burbo Bank | Triton Knoll | 120 | 2.0 hours | 0.65-0.75 | SW Prevailing |
| Moray East | Seagreen | 140 | 2.5 hours | 0.60-0.70 | NW Storms |
| Seagreen | Hornsea Two | 280 | 4.0 hours | 0.50-0.60 | N Wind |
| Rampion | London Array | 100 | 1.5 hours | 0.55-0.65 | S Wind |

---

## Business Value

### 1. Extended Forecast Horizon

**Current**: 1-hour ahead using local conditions

**Spatial**: 2-4 hour ahead using upstream measurements

**Value**: Early positioning for wind drops = higher arbitrage profit

### 2. Improved Forecast Accuracy

**Current**: 15-20% error with local features only

**Spatial**: 10-15% error with upstream features (25% improvement)

**Value**: Better confidence in trading signals, larger position sizing

### 3. Wind Drop Early Warning

**Scenario**: Large southwest wind system approaching UK
- T-4h: Detect wind drop at Walney (-30%)
- T-2h: Predict Hornsea drop (-25%)
- T-0h: Position batteries for discharge at price spike

**Revenue Impact**: +£10-20k per event (20-30 events/year = £200-600k annual)

---

## Next Steps

1. **Run Correlation Analysis** (2 hours)
   - Execute spatial_wind_correlation.py
   - Identify top 20 farm pairs with strong correlations
   - Validate against weather patterns

2. **Build Spatial Feature Dataset** (3 hours)
   - Add upstream wind features to training data
   - Handle missing data (when wind direction doesn't align)
   - Create lag features (30min, 1h, 2h, 3h, 4h)

3. **Retrain Models with Spatial Features** (2 hours)
   - Add 3-5 new features per farm
   - Compare performance vs. baseline
   - Target: 25% error reduction for well-correlated pairs

4. **Deploy to Production** (1 hour)
   - Update realtime_wind_forecasting_simple.py
   - Add upstream farm lookup logic
   - Generate 2-4 hour ahead forecasts

**Total Effort**: 1 day development + testing

---

## Conclusion

Spatial wind forecasting using upstream measurements is a **proven meteorological technique** that should significantly improve forecast accuracy, especially for:

1. **Southwest prevailing winds** (60% of time) - Irish Sea → North Sea pathway
2. **Large-scale weather systems** (fronts, low pressure) - coherent across 100-200 km
3. **2-4 hour forecast horizon** - optimal for intraday trading

The UK offshore wind network provides **natural spatial sensors** covering 500+ km north-south and 200+ km east-west, creating excellent upstream/downstream measurement opportunities.

**Expected Improvement**: 25-40% error reduction for spatially-correlated scenarios, translating to better trading signals and higher battery arbitrage revenue.

---

*Analysis Date: December 30, 2025*  
*Next Action: Run spatial_wind_correlation.py to quantify actual correlations*
