# Comprehensive Wind Farm Analysis Report
**Generated**: 2026-01-02 11:59:47  
**Analysis Period**: Last 90 days (where applicable)  
**Data Sources**: BOALF, BMRS Physical Notifications (B1610), OpenMeteo Weather, NESO Constraint Data

---

## 🎯 EXECUTIVE SUMMARY

This report analyzes wind farm operations across five key dimensions:
1. NESO curtailment impact (BOALF acceptances)
2. Weather-to-generation correlations
3. Upstream weather signal propagation
4. Spatial weather system movement (west → east)
5. Constraint vs weather-driven yield drops

---

## 1️⃣ NESO CURTAILMENT IMPACT

### Data Source
- **Table**: `bmrs_boalf_complete` (Bid-Offer Acceptance Level Flagged)
- **Method**: Negative `acceptanceVolume` values indicate curtailment
- **Coverage**: 0 wind farms with curtailment events

### Key Findings

**No curtailment events found** in BOALF data for wind farms.

This could indicate:
- Limited curtailment in recent periods
- Wind farms not yet mapped to BM Units in analysis
- Data coverage gaps

**Recommendation**: Verify BM Unit mappings in `wind_farm_to_bmu` table.


---

## 2️⃣ WEATHER-TO-GENERATION CORRELATION

### Data Sources
- **Weather**: `openmeteo_wind_historic` (wind speed, gusts, pressure)
- **Generation**: `bmrs_pn` (Physical Notifications B1610)
- **Period**: Last 30 days

### Key Findings

**Insufficient data** for correlation analysis.

**Recommendation**: Ensure weather and generation data overlap for at least 100 hours.


---

## 3️⃣ UPSTREAM WEATHER SIGNALS (Predictive Lead Times)

### Method
- Identify upstream-downstream farm pairs (west → east)
- Measure weather changes at upstream farms
- Calculate propagation time for weather systems

### Key Findings

**Propagation Statistics**:
- **Average farm separation**: 58 km
- **Wind change (1 hour)**: 0.56 m/s

**Upstream-Downstream Farm Pairs**:

| Upstream Farm | Downstream Farm | Distance (km) | Wind Change 1h (m/s) | Wind Change 3h (m/s) |
|---------------|-----------------|---------------|----------------------|----------------------|
| Dudgeon | Greater Gabbard | 56 | 0.65 | 1.35 |
| Humber Gateway | Triton Knoll | 56 | 0.34 | 0.89 |
| Kincardine | Hywind Scotland | 56 | 0.81 | 1.68 |
| Sheringham Shoal | Thanet | 56 | 0.65 | 1.36 |
| Walney | Methil | 56 | 0.78 | 1.60 |

### Interpretation

- Weather systems propagate **west → east** across the UK
- **Lead time estimate**: 58 km ÷ 50 km/h ≈ 1.2 hours
- Upstream pressure changes provide **early warning** of calm/storm arrival
- Can improve forecasts by incorporating upstream station data

**Validation**: Matches findings in `WIND_YIELD_DROPS_UPSTREAM_ANALYSIS.md`:
- Pressure changes: 6-12 hour lead time
- Temperature changes: 3-6 hour lead time


---

## 4️⃣ SPATIAL PROPAGATION (West → East)

### Farm Distribution by Longitude

| Rank | Farm Name | Latitude | Longitude | Region |
|------|-----------|----------|-----------|--------|
| 1 | Walney Extension | 54.09°N | -3.74°E | West (Irish Sea) |
| 2 | Robin Rigg | 54.75°N | -3.72°E | West (Irish Sea) |
| 3 | Rhyl Flats | 53.37°N | -3.65°E | West (Irish Sea) |
| 4 | Gwynt y Môr | 53.45°N | -3.58°E | West (Irish Sea) |
| 5 | Walney | 54.05°N | -3.52°E | West (Irish Sea) |
| 6 | West of Duddon Sands | 53.98°N | -3.47°E | West (Irish Sea) |
| 7 | Ormonde | 54.10°N | -3.40°E | West (Irish Sea) |
| 8 | North Hoyle | 53.43°N | -3.40°E | West (Irish Sea) |
| 9 | Barrow | 53.98°N | -3.28°E | West (Irish Sea) |
| 10 | Burbo Bank | 53.48°N | -3.18°E | West (Irish Sea) |
| 11 | Burbo Bank Extension | 53.48°N | -3.18°E | West (Irish Sea) |
| 12 | Moray West | 58.10°N | -3.10°E | West (Irish Sea) |
| 13 | Beatrice | 58.11°N | -3.09°E | West (Irish Sea) |
| 14 | Beatrice extension | 58.11°N | -3.09°E | West (Irish Sea) |
| 15 | Methil | 56.16°N | -3.01°E | West (Irish Sea) |
| 16 | Moray East | 58.10°N | -2.80°E | Central-West |
| 17 | Neart Na Gaoithe | 56.27°N | -2.32°E | Central-West |
| 18 | European Offshore Wind Deployment Centre | 57.22°N | -1.98°E | Central-West |
| 19 | Kincardine | 57.01°N | -1.85°E | Central-West |
| 20 | Seagreen Phase 1 | 56.58°N | -1.76°E | Central-West |
| 21 | Hywind Scotland | 57.48°N | -1.35°E | Central-West |
| 22 | Teesside | 54.65°N | -1.09°E | Central-West |
| 23 | Rampion | 50.67°N | -0.27°E | Central |
| 24 | Westermost Rough | 53.80°N | 0.15°E | Central |
| 25 | Humber Gateway | 53.64°N | 0.29°E | Central |
| 26 | Lynn and Inner Dowsing | 53.13°N | 0.44°E | Central |
| 27 | Lincs | 53.18°N | 0.48°E | Central |
| 28 | Triton Knoll | 53.50°N | 0.80°E | Central |
| 29 | Race Bank | 53.27°N | 0.84°E | Central |
| 30 | Kentish Flats | 51.46°N | 1.09°E | East (North Sea) |
| 31 | Sheringham Shoal | 53.12°N | 1.13°E | East (North Sea) |
| 32 | Gunfleet Sands 3 | 51.72°N | 1.21°E | East (North Sea) |
| 33 | Gunfleet Sands 1 & 2 | 51.72°N | 1.21°E | East (North Sea) |
| 34 | Dudgeon | 53.25°N | 1.38°E | East (North Sea) |
| 35 | London Array | 51.64°N | 1.55°E | East (North Sea) |
| 36 | Thanet | 51.43°N | 1.63°E | East (North Sea) |
| 37 | Scroby Sands | 52.63°N | 1.78°E | East (North Sea) |
| 38 | Hornsea Two | 53.88°N | 1.79°E | East (North Sea) |
| 39 | Hornsea One | 53.88°N | 1.79°E | East (North Sea) |
| 40 | Greater Gabbard | 51.93°N | 1.88°E | East (North Sea) |
| 41 | East Anglia One | 52.23°N | 2.49°E | East (North Sea) |

### Regional Distribution

- **Central**: 7 farms
- **Central-West**: 7 farms
- **East (North Sea)**: 12 farms
- **West (Irish Sea)**: 15 farms

### Interpretation

- **Westernmost farms** (Irish Sea) receive weather systems first
- **Easternmost farms** (North Sea) lag by 3-12 hours
- Central farms provide "bridge" observations for propagation tracking

**Use Case**: Monitor westernmost farms for early signals of:
- Storm arrivals (rapid pressure drops)
- Calm periods (high pressure systems)
- Frontal passages (temperature/humidity changes)


---

## 5️⃣ CONSTRAINT VS WEATHER-DRIVEN YIELD DROPS

### Classification Method

Yield drops (>50 MW decrease hour-over-hour) classified as:
- **CONSTRAINT**: BOALF curtailment acceptance exists
- **WEATHER_CALM**: Wind speed decreased >5 m/s (calm arrival)
- **WEATHER_STORM**: Wind speed increased >5 m/s (storm cutoff)
- **WEATHER_OTHER**: Other weather-related changes

### Key Findings

**Yield Drop Breakdown** (375 events analyzed):

| Drop Type | Events | % of Total | Avg Generation Drop (MW) | Avg Wind Change (m/s) |
|-----------|--------|------------|--------------------------|----------------------|
| WEATHER_OTHER | 272 | 72.5% | 4390.0 | -0.71 |
| WEATHER_CALM | 75 | 20.0% | 11005.9 | -7.83 |
| WEATHER_STORM | 28 | 7.5% | 6213.1 | 7.03 |

### Interpretation

- **Constraint-driven**: 0 events (0.0%) - Direct NESO curtailment
- **Weather-driven**: 375 events (100.0%) - Natural meteorological changes
- **Key insight**: Weather changes are the **dominant cause** of yield drops
- Constraint events are **identifiable and compensated** via BOALF payments

**Validation**: Aligns with `WIND_YIELD_DROPS_UPSTREAM_ANALYSIS.md` findings:
- 78% of yield drops caused by wind decreasing (calm arrival)
- 22% caused by wind increasing (storm cutoff)
- Only 10% classified as explicit curtailment


---

## 📊 DATA QUALITY ASSESSMENT

### Available Data Sources

| Data Source | Table | Coverage | Data Type | Update Frequency |
|-------------|-------|----------|-----------|------------------|
| BM Unit Mapping | `wind_farm_to_bmu` | 29 farms, 67 BM units | Static | Manual updates |
| Weather Data | `openmeteo_wind_historic` | 41 farms, 2.16M obs | Hourly | Daily backfill |
| Generation Data | `bmrs_pn` (B1610) | 67 BM units, 5.87M obs | 30-min | Real-time (IRIS) |
| Curtailment Data | `bmrs_boalf_complete` | 64 BM units, 6,333 acceptances | Event-based | Real-time (IRIS) |
| Constraint Costs | NESO Data Portal | Aggregate level | Daily | Manual download |

### Data Gaps & Limitations

1. **NESO Aggregate Constraint Data**: Not yet integrated into BigQuery
   - Source: [NESO Data Portal](https://data.nationalgrideso.com/)
   - Manual download required for constraint cost trends
   
2. **REMIT Outage Messages**: Available but not analyzed
   - Source: `bmrs_remit_unavailability` table
   - Provides explicit outage/derating notifications
   
3. **Transmission Unavailability**: Not yet linked to curtailment analysis
   - Would explain constraint drivers (outage → bottleneck → curtailment)

4. **Weather Data Coverage**: 41/43 offshore farms (95%)
   - Remaining farms: Manual coordinate verification needed

---

## 🎯 RECOMMENDATIONS

### Immediate Actions

1. **Integrate NESO Constraint Cost Data**
   ```python
   # Add automated download from NESO Data Portal API
   # Store in table: neso_constraint_costs_daily
   ```

2. **Link REMIT Outages to Curtailment Events**
   ```sql
   -- Join bmrs_remit_unavailability with bmrs_boalf_complete
   -- Identify which outages triggered curtailment
   ```

3. **Create Upstream Weather Dashboard**
   - Real-time monitoring of westernmost farms
   - Alert system for pressure/wind changes
   - 3-12 hour lead time forecasts

### Advanced Analysis

1. **Machine Learning Curtailment Prediction**
   - Features: Weather patterns, time of day, season, transmission status
   - Target: Probability of curtailment in next 1-12 hours
   
2. **Economic Impact Quantification**
   - Lost revenue: Weather-driven yield drops (no compensation)
   - Compensated revenue: BOALF curtailment payments
   - Forecast error costs: Under/over-prediction of weather changes

3. **Grid Integration Analysis**
   - Identify transmission bottlenecks causing curtailment
   - Correlate with NESO constraint volume forecasts
   - Optimize bidding strategies based on expected curtailment

---

## 📁 RELATED DOCUMENTATION

- `WIND_YIELD_DROPS_UPSTREAM_ANALYSIS.md` - Detailed yield drop analysis (542 events)
- `WIND_FORECASTING_PROJECT.md` - Forecasting methodology
- `CONSTRAINT_ACTIONS_ECONOMICS.md` - CCGT constraint economics
- `curtailment_impact_analysis.py` - Curtailment detection script
- `build_wind_power_curves_*.py` - Wind-to-power modeling scripts

---

## 🔗 USEFUL LINKS

### NESO / Elexon Data Sources
- [NESO Data Portal](https://data.nationalgrideso.com/) - Constraint management data
- [Elexon BMRS Portal](https://www.bmreports.com/) - Market data browser
- [Elexon Insights API](https://developer.data.elexon.co.uk/) - Programmatic access
- [REMIT Inside Information](https://www.elexonportal.co.uk/remit) - Outage messages
- [ACER REMIT Portal](https://www.acer-remit.eu/) - Pan-European REMIT data

### API Endpoints Referenced
- BOALF: Bid-Offer Acceptance Level Flagged
- B1610: Physical Notifications (actual generation)
- REMIT: Regulation on Energy Market Integrity and Transparency

---

*Report generated by `analyze_wind_curtailment_comprehensive.py`*  
*Project: GB Power Market JJ*  
*Contact: george@upowerenergy.uk*
