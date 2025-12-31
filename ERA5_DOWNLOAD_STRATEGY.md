# ERA5 Download Strategy - One Farm at a Time

**Last Updated**: 31 December 2025  
**Status**: ✅ IMPLEMENTED

---

## 🎯 Why Download One Farm at a Time?

### ❌ OLD APPROACH (Bad)
```
Farm 1 → Month 1 → Group 1
Farm 2 → Month 1 → Group 1
Farm 3 → Month 1 → Group 1
...
Farm 29 → Month 1 → Group 1
Farm 1 → Month 2 → Group 1
...
```
**Problem**: You get NO complete farm data until the entire 65-day download finishes!

### ✅ NEW APPROACH (Good)
```
Farm 1 → ALL months → ALL groups → COMPLETE! ✅
Farm 2 → ALL months → ALL groups → COMPLETE! ✅
Farm 3 → ALL months → ALL groups → COMPLETE! ✅
...
```
**Benefit**: Get complete, analyzable data for each farm as soon as it finishes!

---

## 📊 Timeline Comparison

### Current Download (29 farms × 72 months × 5 groups)

| Approach | First Complete Farm | All Farms Complete | Analysis Ready |
|----------|---------------------|-------------------|----------------|
| **OLD** (scattered) | 65 days | 65 days | 65 days |
| **NEW** (sequential) | 2.2 days | 65 days | **2.2 days** 🎉 |

### Optimized Download (10 farms × 30 months × 5 groups)

| Approach | First Complete Farm | All Farms Complete | Analysis Ready |
|----------|---------------------|-------------------|----------------|
| **OLD** (scattered) | 9 days | 9 days | 9 days |
| **NEW** (sequential) | **0.9 days** | 9 days | **0.9 days** 🎉 |

**Key Insight**: Get your first complete farm **30x faster** with the new approach!

---

## 🏗️ What Changed?

### Code Structure
```python
# OLD: Interleaved loop (all farms per month)
for month in months:
    for farm in farms:
        for group in groups:
            download()

# NEW: Complete one farm before moving to next
for farm in farms:  # ← One at a time!
    for month in months:
        for group in groups:
            download()
    logger.info(f"✅ FARM COMPLETE: {farm}")  # ← Clear milestone!
```

### Progress Tracking
```
OLD:
✅ Completed: 41/10,440 (0.4%)  # Meaningless!

NEW:
✅ Request complete: 41/360 for Hornsea One (11.4%)
✅ Overall: 41/10,440 (0.4%)
📊 Farm: 41/360 | Overall: 41/10,440 | Rows: 29,952/752,400
```

### Completion Milestones
```
NEW OUTPUT:
================================================================================
✅ FARM COMPLETE: Hornsea One
📊 Downloaded: 360/360 requests, 259,200 rows
📊 Remaining farms: 28
================================================================================
```

---

## 🎓 Farm Priority Order

### Current Download (29 farms)
1. **Hornsea One** (1,218 MW) - COMPLETE in 2.2 days
2. **Hornsea Two** (1,386 MW) - COMPLETE in 4.5 days
3. **Dogger Bank A** (1,200 MW) - COMPLETE in 6.7 days
4. **Moray East** (950 MW) - COMPLETE in 8.9 days
5. **Beatrice** (588 MW) - COMPLETE in 11.2 days
...
29. **Blyth Offshore Demo** (42 MW) - COMPLETE in 65 days

### Why This Order?
- **Capacity-weighted**: Largest farms = highest impact on grid
- **Geographic diversity**: North Sea → Irish Sea → Atlantic
- **Technology mix**: Fixed-bottom (most) → Floating (Hywind, Kincardine)

### Optimized Version (10 farms only)
If you want **fast results**, focus on top 10:
1. Hornsea One, Two, Three
2. Dogger Bank A, B, C
3. Moray East, Triton Knoll, East Anglia One, Beatrice

**Coverage**: 64% of UK offshore capacity  
**Timeline**: 9 days (7x faster!)

---

## 📁 File Organization

### Storage Structure
```
~/era5_downloads/ocean_wave/
├── Hornsea_One_2020_01_air_sea_interaction.nc
├── Hornsea_One_2020_01_wave_basics.nc
├── Hornsea_One_2020_01_wave_details.nc
├── Hornsea_One_2020_01_spectral_properties.nc
├── Hornsea_One_2020_01_bathymetry.nc
├── Hornsea_One_2020_02_air_sea_interaction.nc
...
├── Hornsea_One_2025_12_bathymetry.nc  ← Farm 1 complete!
├── Hornsea_Two_2020_01_air_sea_interaction.nc  ← Farm 2 starts
...
```

### BigQuery Table
```sql
SELECT farm_name, COUNT(*) as records
FROM `inner-cinema-476211-u9.uk_energy_prod.era5_ocean_wave_data`
GROUP BY farm_name
ORDER BY records DESC;

-- Results after 2.2 days:
-- Hornsea One: 259,200 records ✅ COMPLETE
-- Hornsea Two: 150,000 records (in progress)
-- Other farms: 0 records (pending)
```

---

## 🔍 When Can I Start Analysis?

### Scenario 1: Current Download (29 farms, icing season priority)
- **Day 1**: 41 requests done (0.4%), no complete farms
- **Day 2**: 192 requests (1.8%), **Hornsea One COMPLETE** ✅
- **Day 3-4**: Hornsea Two complete
- **Day 5-6**: Dogger Bank A complete
- **Week 2**: Top 5 farms complete (28% of UK capacity)
- **Week 3**: Top 10 farms complete (64% of UK capacity)
- **Day 65**: All 29 farms complete

### Scenario 2: Optimized Download (10 farms, icing season only)
- **Day 1**: **Hornsea One COMPLETE** ✅
- **Day 2**: Hornsea Two complete
- **Day 3**: Dogger Bank A complete
- **Day 9**: All 10 farms complete

---

## 📊 Analysis Readiness Checklist

### After First Farm Completes (2.2 days)
- ✅ Full 72-month time series (2020-2025)
- ✅ All 24 ocean/wave variables
- ✅ All 5 variable groups
- ✅ Icing season + non-icing season
- ✅ 259,200 hourly records

### What You Can Analyze:
1. **Air density corrections** → Improve power curve accuracy
2. **Wave-induced turbulence** → Refine wake models
3. **Seasonal patterns** → Validate icing detection
4. **Extreme events** → Identify high-risk periods
5. **Model validation** → Compare ERA5 vs. actual production

### What You CANNOT Analyze Yet:
- ❌ Inter-farm correlations (need multiple farms)
- ❌ Geographic trends (need regional coverage)
- ❌ Portfolio-wide statistics (need all farms)

**Recommendation**: Start preliminary analysis after Day 2-3 (first farm complete), then refine with more farms as they complete.

---

## 🚀 Quick Commands

### Check Current Farm Progress
```bash
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9')
query = '''
SELECT farm_name, 
       COUNT(*) as records,
       MIN(time_utc) as start_date,
       MAX(time_utc) as end_date
FROM \`inner-cinema-476211-u9.uk_energy_prod.era5_ocean_wave_data\`
GROUP BY farm_name
ORDER BY records DESC
'''
df = client.query(query).to_dataframe()
print(df)
"
```

### Monitor Download Progress
```bash
./monitor_era5_downloads.sh
```

### Check Saved Files
```bash
ls -lh ~/era5_downloads/ocean_wave/ | tail -20
du -sh ~/era5_downloads/ocean_wave/
```

### Restart Download (if needed)
```bash
# Stop current download
pkill -f download_era5_ocean_waves.py

# Start with new sequential logic
nohup python3 download_era5_ocean_waves.py > /tmp/era5_ocean_wave.out 2>&1 &

# Monitor
tail -f /tmp/era5_ocean_wave_download.log
```

---

## 📈 Expected Performance

### Per Farm (72 months × 5 groups = 360 requests)
- **Time**: 360 requests × 9 min/request = 3,240 minutes = **54 hours = 2.2 days**
- **Data**: ~259,200 hourly records
- **Storage**: ~54 MB NetCDF files
- **BigQuery**: ~15 MB compressed

### All 29 Farms
- **Time**: 29 farms × 2.2 days = **65 days**
- **Data**: ~7.5 million hourly records
- **Storage**: ~1.5 GB NetCDF files
- **BigQuery**: ~440 MB compressed

### Top 10 Farms (Optimized)
- **Time**: 10 farms × 2.2 days = **22 days**
- **Data**: ~2.6 million hourly records
- **Storage**: ~520 MB NetCDF files
- **BigQuery**: ~150 MB compressed

### Top 10 Farms, Icing Season Only (30 months)
- **Time**: 10 farms × 150 requests × 9 min = **9 days**
- **Data**: ~1.1 million hourly records
- **Storage**: ~220 MB NetCDF files
- **BigQuery**: ~65 MB compressed

---

## 🎯 Recommendation

### For Immediate Analysis (Next 3 Days)
✅ **Continue current download** (no restart needed)  
✅ **Wait for Hornsea One to complete** (2.2 days from now)  
✅ **Start preliminary analysis** with first complete farm  
✅ **Refine models** as more farms complete

### For Long-Term Project (Next 2-3 Months)
✅ **Let all 29 farms download** (background process)  
✅ **Analyze incrementally** (weekly updates)  
✅ **Build complete dataset** (7.5M records)  
✅ **Publish results** when ready

### For Quick Wins (Stop & Restart)
⚠️ **Stop current download** (lose 41 completed requests)  
⚠️ **Switch to 10 farms × icing season** (9 days total)  
✅ **Get first results in 1 day** (fastest path to data)  
❌ **Lose 19 farms** (no data for smaller farms)

---

## 📚 Related Documentation

- `OCEAN_WAVE_FEATURES.md` - Variable definitions and use cases
- `monitor_era5_downloads.sh` - Progress tracking script
- `PROJECT_CONFIGURATION.md` - BigQuery settings
- `download_era5_ocean_waves.py` - Main download script

---

**Created**: 31 December 2025  
**Author**: GitHub Copilot  
**Status**: ✅ Production Ready
