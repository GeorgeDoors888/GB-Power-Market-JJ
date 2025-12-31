# ERA5 Downloads - Active Status

**Started**: 31 December 2025, 01:16 UTC  
**Strategy**: ONE FARM AT A TIME (sequential completion)  
**Status**: ✅ RUNNING

---

## 📊 What's Being Downloaded

### 1️⃣ Ocean/Wave Data
**Script**: `download_era5_ocean_waves.py`  
**Target**: 29 offshore wind farms  
**Variables**: 24 variables across 5 groups

#### Variable Groups:
1. **Air-Sea Interaction** (5 vars)
   - Air density over oceans (ρ for power = ρ·v³)
   - Coefficient of drag with waves
   - Ocean surface stress equivalent 10m wind speed/direction
   - Normalized energy flux into ocean

2. **Wave Basics** (6 vars)
   - Significant height (combined, wind waves, swell)
   - Peak wave period
   - Mean wave period/direction

3. **Wave Details** (6 vars)
   - Mean direction (wind waves, swell)
   - Mean period (wind waves, swell, zero-crossing)
   - Maximum individual wave height

4. **Spectral Properties** (6 vars)
   - Wave spectral peakedness/directional width
   - Mean square slope
   - Swell partitions (1st, 2nd, 3rd)

5. **Bathymetry** (1 var)
   - Model bathymetry (ocean depth)

**Timeline**: 360 requests per farm × 9 min = 54 hours = 2.2 days per farm

---

### 2️⃣ Weather Data
**Script**: `download_era5_icing_optimized.py`  
**Target**: 41 wind farms (offshore + onshore)  
**Variables**: 6 variables across 3 groups

#### Variable Groups:
1. **Temperature/Humidity** (2 vars)
   - 2m temperature
   - 2m dewpoint temperature

2. **Precipitation/Cloud** (2 vars)
   - Total precipitation
   - Total cloud cover

3. **Wind** (2 vars)
   - 10m u-component wind
   - 10m v-component wind

**Timeline**: 216 requests per farm × 9 min = 32.4 hours = 1.35 days per farm

---

## 🎯 Download Strategy

### Sequential Farm Completion

**OLD Approach** (scattered):
```
Month 2020-11: All 29 farms
Month 2020-12: All 29 farms
Month 2021-01: All 29 farms
...
❌ No complete farm until day 65
```

**NEW Approach** (sequential):
```
Farm 1 (Beatrice):
  ├─ All 72 months (2020-2025)
  ├─ All 5 variable groups (ocean/wave)
  └─ ✅ COMPLETE in 2.2 days

Farm 2 (Hornsea One):
  ├─ All 72 months
  ├─ All 5 variable groups
  └─ ✅ COMPLETE in 2.2 days
...
```

### Priority Order: Icing Season First
Within each farm, download months in this order:
1. **Nov-Mar** (icing season) - highest priority
2. **Apr-Oct** (non-icing) - lower priority

Years: 2020, 2021, 2022, 2023, 2024, 2025

---

## 📅 Completion Timeline

### Ocean/Wave (29 farms)
| Day | Farm Complete | Capacity | Cumulative |
|-----|---------------|----------|------------|
| 2.2 | Beatrice | 588 MW | 588 MW |
| 4.5 | Hornsea One | 1,218 MW | 1,806 MW |
| 6.7 | Hornsea Two | 1,386 MW | 3,192 MW |
| 8.9 | Dogger Bank A | 1,200 MW | 4,392 MW |
| 11.2 | Moray East | 950 MW | 5,342 MW |
| 13.4 | Triton Knoll | 857 MW | 6,199 MW |
| 15.6 | East Anglia One | 714 MW | 6,913 MW |
| 17.8 | Walney Extension | 659 MW | 7,572 MW |
| 20.1 | London Array | 630 MW | 8,202 MW |
| 22.3 | Race Bank | 573 MW | 8,775 MW |
| ... | ... | ... | ... |
| **65** | All 29 farms | **16,780 MW** | **100%** |

### Weather (41 farms)
First farm: 1.35 days  
All farms: ~55 days

---

## 💾 Data Storage

### Local Files (Permanent)
```
~/era5_downloads/
├── ocean_wave/
│   ├── Beatrice_2020_11_air_sea_interaction.nc (148 KB)
│   ├── Beatrice_2020_11_wave_basics.nc (162 KB)
│   ├── Beatrice_2020_11_wave_details.nc (178 KB)
│   ├── Beatrice_2020_11_spectral_properties.nc (148 KB)
│   ├── Beatrice_2020_11_bathymetry.nc (95 KB)
│   └── ... (10,440 files total, ~1.5 GB)
│
└── weather/
    ├── Beatrice_2020_11_temperature_humidity.nc
    ├── Beatrice_2020_11_precipitation_cloud.nc
    ├── Beatrice_2020_11_wind.nc
    └── ... (8,856 files total, ~1 GB)
```

### BigQuery Tables
```
inner-cinema-476211-u9.uk_energy_prod.era5_ocean_wave_data
  • Schema: 28 fields (farm_name, time_utc, lat, lon, 24 variables)
  • Expected: ~7.5 million rows (29 farms × 72 months × 24h × 30 days)
  • Size: ~440 MB compressed

inner-cinema-476211-u9.uk_energy_prod.era5_weather_data
  • Schema: 10 fields (farm_name, time_utc, lat, lon, 6 variables)
  • Expected: ~2.2 million rows (41 farms × 72 months × 24h × 30 days)
  • Size: ~130 MB compressed
```

---

## 📊 Monitoring Progress

### Check Download Status
```bash
# Monitor both downloads
./monitor_era5_downloads.sh

# View ocean/wave log
tail -f /tmp/era5_ocean_wave_download.log

# View weather log
tail -f /tmp/era5_weather_download.log

# Check processes
ps aux | grep download_era5
```

### Query BigQuery Data
```python
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')

# Check ocean/wave progress
query = '''
SELECT 
    farm_name,
    COUNT(*) as records,
    MIN(time_utc) as earliest,
    MAX(time_utc) as latest,
    COUNT(DISTINCT DATE(time_utc)) as days
FROM `inner-cinema-476211-u9.uk_energy_prod.era5_ocean_wave_data`
GROUP BY farm_name
ORDER BY records DESC
'''
df = client.query(query).to_dataframe()
print(df)
```

### Check Saved Files
```bash
# Count files
ls ~/era5_downloads/ocean_wave/ | wc -l
ls ~/era5_downloads/weather/ | wc -l

# Check disk usage
du -sh ~/era5_downloads/ocean_wave/
du -sh ~/era5_downloads/weather/

# List recent files
ls -lht ~/era5_downloads/ocean_wave/ | head -10
```

---

## 🎉 When Can I Start Analysis?

### Day 2-3: First Farm Complete
- ✅ Beatrice ocean/wave data: 259,200 records (72 months × 24h × 30 days)
- ✅ Beatrice weather data: 51,840 records (72 months × 24h × 30 days)
- **What you can analyze**:
  - Air density corrections for power forecasting
  - Wave-induced turbulence effects
  - Icing season validation (Nov-Mar data available)
  - Seasonal patterns and trends
  - Extreme event identification

### Week 2: Top 5 Farms Complete
- ✅ 5 major farms (28% of UK offshore capacity)
- **What you can analyze**:
  - Inter-farm correlations
  - Geographic variations (North Sea coverage)
  - Regional weather patterns
  - Portfolio-level statistics (preliminary)

### Week 3: Top 10 Farms Complete
- ✅ 10 major farms (64% of UK offshore capacity)
- **What you can analyze**:
  - Full portfolio analysis
  - Geographic diversity (North Sea → Irish Sea)
  - Technology comparison (fixed vs floating)
  - Production forecasting models

### Month 2-3: All Farms Complete
- ✅ Complete UK offshore wind dataset
- ✅ 7.5M ocean/wave records
- ✅ 2.2M weather records
- **What you can analyze**:
  - Everything!

---

## 🚨 Troubleshooting

### Downloads Stopped?
```bash
# Check if processes are running
ps aux | grep download_era5

# Restart ocean/wave
cd /home/george/GB-Power-Market-JJ
nohup python3 download_era5_ocean_waves.py > /tmp/era5_ocean_wave.out 2>&1 &

# Restart weather
nohup python3 download_era5_icing_optimized.py > /tmp/era5_weather.out 2>&1 &
```

### Check for Errors
```bash
# Ocean/wave errors
grep -i "error\|failed\|exception" /tmp/era5_ocean_wave_download.log | tail -20

# Weather errors
grep -i "error\|failed\|exception" /tmp/era5_weather_download.log | tail -20
```

### CDS API Issues
```bash
# Check CDS API credentials
cat ~/.cdsapirc

# Test CDS connection
python3 -c "import cdsapi; c = cdsapi.Client(); print('✅ Connected')"
```

---

## 📚 Related Documentation

- `ERA5_DOWNLOAD_STRATEGY.md` - Detailed strategy explanation
- `OCEAN_WAVE_FEATURES.md` - Variable definitions and use cases
- `PROJECT_CONFIGURATION.md` - BigQuery settings
- `monitor_era5_downloads.sh` - Progress monitoring script

---

**Last Updated**: 31 December 2025, 01:20 UTC  
**Status**: ✅ Both downloads running successfully  
**Next Milestone**: Beatrice complete (Day 2.2)
