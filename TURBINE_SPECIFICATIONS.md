# Turbine Specifications Database

**Author**: AI Coding Agent  
**Date**: December 30, 2025  
**Purpose**: Reference guide for UK offshore wind farm turbine specifications

---

## 📊 Database Overview

**Table**: `turbine_specifications`  
**Project**: `inner-cinema-476211-u9`  
**Dataset**: `uk_energy_prod`  
**Records**: 2,375 turbines across 29 wind farms

---

## 🗃️ Schema

```sql
CREATE TABLE turbine_specifications (
    farm_name STRING,
    turbine_id STRING,             -- Unique identifier per turbine
    manufacturer STRING,           -- Siemens Gamesa, Vestas, MHI Vestas, GE, etc.
    model STRING,                  -- SWT-8.0-154, V164-9.5, etc.
    rated_power_mw FLOAT64,        -- Nameplate capacity (MW)
    rotor_diameter_m FLOAT64,      -- Rotor diameter (meters)
    hub_height_m FLOAT64,          -- Hub height above sea level (meters)
    cut_in_speed_ms FLOAT64,       -- Minimum wind speed for generation (m/s)
    rated_speed_ms FLOAT64,        -- Wind speed at rated power (m/s)
    cut_out_speed_ms FLOAT64,      -- Maximum wind speed before shutdown (m/s)
    commissioning_date DATE,       -- When turbine became operational
    latitude FLOAT64,              -- Turbine location
    longitude FLOAT64,
    offshore_distance_km FLOAT64,  -- Distance from shore
    water_depth_m FLOAT64          -- Seabed depth
)
```

---

## 🏭 Wind Farm Summary

### Large Farms (>800 MW)

**Hornsea Two** (1,386 MW)
- Turbines: 165 × Siemens Gamesa SG 8.0-167 DD
- Rated Power: 8.4 MW per turbine
- Hub Height: 112m
- Rotor Diameter: 167m
- Location: 89 km off Yorkshire coast
- Water Depth: ~30-40m
- Commissioned: 2022

**Hornsea One** (1,218 MW)
- Turbines: 174 × Siemens Gamesa SWT-7.0-154
- Rated Power: 7.0 MW per turbine
- Hub Height: 100m
- Rotor Diameter: 154m
- Location: 120 km off Yorkshire coast
- Water Depth: ~30-40m
- Commissioned: 2020

**Dogger Bank A** (1,200 MW planned)
- Turbines: 100 × GE Haliade-X 12 MW
- Rated Power: 12.0 MW per turbine
- Hub Height: 150m
- Rotor Diameter: 220m
- Location: 130 km off Yorkshire coast
- Water Depth: ~30m
- Commissioning: 2023-2024

### Medium Farms (300-800 MW)

**Moray East** (950 MW)
- Turbines: 100 × MHI Vestas V164-9.5
- Rated Power: 9.5 MW per turbine
- Hub Height: 107m
- Rotor Diameter: 164m
- Location: 22 km off Scotland coast
- Commissioned: 2022

**Triton Knoll** (857 MW)
- Turbines: 90 × Vestas V164-9.5
- Rated Power: 9.5 MW per turbine
- Hub Height: 115m
- Rotor Diameter: 164m
- Location: 32 km off Lincolnshire coast
- Commissioned: 2022

**Walney Extension** (659 MW)
- Turbines: 87 × mixed (Vestas V164-8.25 + Siemens SWT-7.0)
- Rated Power: 7.0-8.25 MW per turbine
- Hub Height: 100-105m
- Location: 19 km off Cumbria coast
- Commissioned: 2018

### Smaller Farms (<300 MW)

**Seagreen Phase 1** (1,075 MW - under construction)
- Turbines: 114 × Vestas V164-10.0
- Rated Power: 10.0 MW per turbine
- Hub Height: 107m
- Rotor Diameter: 164m
- Location: 27 km off Scotland coast
- Commissioning: 2022-2023

---

## 🔧 Turbine Model Specifications

### Siemens Gamesa Models

**SG 8.0-167 DD** (Hornsea Two)
- Rated Power: 8.4 MW
- Rotor Diameter: 167m
- Hub Height: 112m
- Cut-in Speed: 3 m/s
- Rated Speed: 13 m/s
- Cut-out Speed: 25 m/s
- Generator: Direct Drive (DD)
- Weight: ~500 tonnes (nacelle + rotor)

**SWT-7.0-154** (Hornsea One, Walney)
- Rated Power: 7.0 MW
- Rotor Diameter: 154m
- Hub Height: 100m
- Cut-in Speed: 3-4 m/s
- Rated Speed: 13 m/s
- Cut-out Speed: 25 m/s
- Generator: Direct Drive
- Swept Area: 18,600 m²

### Vestas Models

**V164-10.0** (Seagreen)
- Rated Power: 10.0 MW
- Rotor Diameter: 164m
- Hub Height: 107m
- Cut-in Speed: 3 m/s
- Rated Speed: 11.5 m/s
- Cut-out Speed: 25 m/s
- Generator: Medium Speed
- Swept Area: 21,124 m²

**V164-9.5** (Triton Knoll, Moray East)
- Rated Power: 9.5 MW
- Rotor Diameter: 164m
- Hub Height: 105-115m
- Cut-in Speed: 3 m/s
- Rated Speed: 13 m/s
- Cut-out Speed: 25 m/s
- Swept Area: 21,124 m²

### GE Renewable Energy

**Haliade-X 12 MW** (Dogger Bank)
- Rated Power: 12-14 MW (uprated)
- Rotor Diameter: 220m
- Hub Height: 150m
- Cut-in Speed: 3 m/s
- Rated Speed: 10.9 m/s
- Cut-out Speed: 25 m/s
- Swept Area: 38,000 m² (largest in UK)
- Blade Length: 107m

---

## 📐 Power Curve Characteristics

### Typical Offshore Wind Power Curve

```
Power (MW)
  │
14│                      ┌─────────────────── Rated Power
  │                     ╱
12│                   ╱
  │                 ╱
10│               ╱
  │             ╱
 8│           ╱
  │         ╱
 6│       ╱
  │     ╱
 4│   ╱
  │ ╱
 2│╱
  └───────────────────────────────────────────► Wind Speed (m/s)
  0  3  6  9  12 15 18 21 24 27 30
     ▲     ▲        ▲           ▲
  Cut-in Optimal Rated      Cut-out
   (3m/s) (9-11) (13m/s)    (25m/s)
```

### Power Calculation

**Theoretical Maximum** (Betz Limit):
```python
P_max = 0.593 × 0.5 × ρ × A × v³
```

Where:
- ρ = air density (1.225 kg/m³ at sea level, 15°C)
- A = rotor swept area (π × (D/2)²)
- v = wind speed (m/s)
- 0.593 = Betz limit (59.3% max efficiency)

**Actual Power** (with Cp):
```python
P = Cp × 0.5 × ρ × A × v³
```

Where:
- Cp = power coefficient (0.35-0.45 typical for offshore turbines)

**Example**: Siemens SG 8.0-167 at 12 m/s
```python
A = π × (167/2)² = 21,903 m²
P = 0.40 × 0.5 × 1.225 × 21,903 × 12³ = 9.2 MW
```
Exceeds rated 8.4 MW → capped at nameplate capacity

---

## 🌊 Environmental Factors

### Water Depth Impact

**Shallow (<25m)**:
- Foundation: Monopile
- Installation: Jack-up vessels
- Examples: Walney Extension, Triton Knoll

**Medium (25-50m)**:
- Foundation: Jacket or Monopile
- Installation: Heavy-lift vessels
- Examples: Hornsea One/Two, Dogger Bank

**Deep (>50m)**:
- Foundation: Floating (future)
- Installation: Specialized vessels
- Examples: Celtic Sea projects (planned)

### Distance from Shore

**Near-shore (<30 km)**:
- Lower transmission losses
- Easier maintenance access
- Examples: Moray East (22 km), Walney (19 km)

**Far-shore (>50 km)**:
- Higher wind resource (less turbulence)
- More expensive O&M
- Examples: Hornsea One (120 km), Dogger Bank (130 km)

---

## 🔍 Usage Examples

### Query All Turbines for a Farm

```sql
SELECT
    turbine_id,
    manufacturer,
    model,
    rated_power_mw,
    hub_height_m,
    commissioning_date
FROM `inner-cinema-476211-u9.uk_energy_prod.turbine_specifications`
WHERE farm_name = 'Hornsea One'
ORDER BY turbine_id
```

### Calculate Farm Theoretical Maximum Power

```sql
SELECT
    farm_name,
    COUNT(*) as turbine_count,
    AVG(rated_power_mw) as avg_turbine_mw,
    SUM(rated_power_mw) as total_capacity_mw,
    AVG(rotor_diameter_m) as avg_rotor_diameter,
    AVG(hub_height_m) as avg_hub_height
FROM `inner-cinema-476211-u9.uk_energy_prod.turbine_specifications`
GROUP BY farm_name
ORDER BY total_capacity_mw DESC
```

### Find Turbines by Manufacturer

```sql
SELECT
    manufacturer,
    COUNT(DISTINCT farm_name) as farms,
    COUNT(*) as turbines,
    SUM(rated_power_mw) as total_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.turbine_specifications`
GROUP BY manufacturer
ORDER BY total_mw DESC
```

### Power Curve Validation Query

```sql
WITH turbine_specs AS (
    SELECT
        farm_name,
        AVG(rated_power_mw) as rated_mw,
        AVG(cut_in_speed_ms) as cut_in,
        AVG(rated_speed_ms) as rated_speed,
        AVG(cut_out_speed_ms) as cut_out
    FROM `inner-cinema-476211-u9.uk_energy_prod.turbine_specifications`
    WHERE farm_name = 'Hornsea One'
    GROUP BY farm_name
),
wind_gen AS (
    SELECT
        farm_name,
        wind_speed_100m,
        AVG(generation) as avg_generation
    FROM `inner-cinema-476211-u9.uk_energy_prod.openmeteo_wind_historic`
    WHERE farm_name = 'Hornsea One'
      AND DATE(settlementDate) >= '2025-01-01'
    GROUP BY farm_name, wind_speed_100m
)
SELECT
    wg.wind_speed_100m,
    wg.avg_generation,
    ts.rated_mw * (SELECT COUNT(*) FROM turbine_specifications WHERE farm_name = 'Hornsea One') as max_capacity,
    wg.avg_generation / (ts.rated_mw * 174) * 100 as capacity_factor_pct,
    CASE
        WHEN wg.wind_speed_100m < ts.cut_in THEN 'Below Cut-in'
        WHEN wg.wind_speed_100m >= ts.rated_speed THEN 'At Rated'
        WHEN wg.wind_speed_100m > ts.cut_out THEN 'Above Cut-out'
        ELSE 'Ramping'
    END as power_curve_region
FROM wind_gen wg
CROSS JOIN turbine_specs ts
ORDER BY wg.wind_speed_100m
```

---

## 🚧 Maintenance & Operations

### Typical Maintenance Schedule

**Daily** (Automated):
- SCADA monitoring (if available)
- Performance metrics
- Fault detection

**Monthly**:
- Vibration analysis
- Oil sampling
- Visual inspections

**Annual**:
- Major component inspection
- Gearbox (if not direct drive)
- Electrical systems
- Safety systems

**5-Year**:
- Blade inspection/repair
- Torque checks
- Generator overhaul

### Common Failure Modes

1. **Blade damage** (5-10 years): Lightning, erosion, ice
2. **Gearbox failure** (8-12 years): Wear, lubrication
3. **Generator issues** (10-15 years): Bearing wear
4. **Yaw system** (5-10 years): Mechanical wear
5. **Pitch system** (5-10 years): Hydraulic/electric faults

---

## 📊 Performance Metrics

### Capacity Factor by Farm Size

| Farm Size | Typical Capacity Factor | UK Offshore Average |
|-----------|------------------------|---------------------|
| <300 MW | 35-40% | - |
| 300-800 MW | 40-45% | 42% |
| >800 MW | 45-50% | 47% |

**UK Offshore Average**: ~43% (2022-2023)

### Availability Targets

- **Target**: >95% availability
- **Actual**: 93-97% (varies by farm age)
- **Downtime causes**:
  - Maintenance: 40%
  - Weather: 30%
  - Grid constraints: 20%
  - Faults: 10%

---

## 📚 References

### Data Sources

1. **The Crown Estate** - Wind farm database
2. **4C Offshore** - Turbine specifications
3. **Manufacturers** - Technical datasheets
   - Siemens Gamesa: https://www.siemensgamesa.com
   - Vestas: https://www.vestas.com
   - GE Renewable Energy: https://www.ge.com/renewableenergy

### Related Documentation

- `WEATHER_DATA_GUIDE.md` - Weather data schemas
- `WIND_FORECASTING_COMPLETE_IMPLEMENTATION.md` - Forecasting system
- `PROJECT_CONFIGURATION.md` - BigQuery setup

---

## 🔄 Update History

- **Dec 30, 2025**: Initial version (29 farms, 2,375 turbines)
- **Future**: Add SCADA integration, real-time status

---

**Last Updated**: December 30, 2025  
**Version**: 1.0  
**Maintainer**: george@upowerenergy.uk
