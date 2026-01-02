# SUMMARY: Wind Yield Drop Analysis - Data Quality Issues Fixed

**Date**: January 1, 2026  
**Status**: ✅ All issues resolved, cron job active

---

## 🎯 YOUR QUESTIONS ANSWERED

### Q1: "Do we have gust data?"
**✅ YES** - Open-Meteo provides `wind_gusts_10m` (km/h)
- Added to new download script: `download_era5_with_gusts.py`
- Will be available for all farms once cron job completes
- Can analyze gust vs mean wind for turbulence detection

### Q2: "Set cron job to download in 24 hours"
**✅ DONE** - Scheduled for daily 3 AM UTC
```bash
0 3 * * * cd /home/george/GB-Power-Market-JJ && ./download_era5_remaining_farms_24h.sh
```
- **Next run**: Tomorrow (Jan 2, 2026) at 03:00 UTC
- **Downloads**: 5 farms/day (respects Open-Meteo rate limit)
- **Remaining**: 20 farms
- **ETA**: January 5, 2026

### Q3: "Wind speeds seem wrong (42 m/s, 100 m/s?!)"
**✅ FIXED** - You were absolutely right!
- Open-Meteo returns wind in **km/h**, not m/s
- We analyzed km/h values as if they were m/s → 3.6× overestimation
- **Corrected**: Max wind 29.4 m/s (realistic), not 105.8 m/s (hurricane!)

---

## 🔍 CORRECTED ANALYSIS RESULTS

### Wind Speed Reality Check

| Metric | WRONG (km/h as m/s) | CORRECT (m/s) | Status |
|--------|---------------------|---------------|--------|
| Average wind | 33.2 "m/s" | **9.2 m/s** | ✅ Realistic |
| Max wind | 105.8 "m/s" | **29.4 m/s** | ✅ Realistic storm |
| Mean before drop | 42.3 "m/s" | **11.7 m/s** | ✅ Typical offshore |
| Storm curtailment | 54 events (10%) | **2 events (0.4%)** | ✅ Rare, as expected |

### Root Causes (CORRECTED)

| Cause | Events | % | Wind Change | Interpretation |
|-------|--------|---|-------------|----------------|
| **Calm Arrival** | 164 | 30% | **-8.4 m/s** | High-pressure system arrival |
| **Other/Gradual** | 299 | 55% | -0.4 m/s | Mixed/gradual changes |
| **Turbulence** | 65 | 12% | -3.2 m/s | Frontal instability |
| **Direction Shift** | 12 | 2% | -0.2 m/s | Wake effects |
| **Storm Curtailment** | 2 | **0.4%** | +10.1 m/s | Wind >25 m/s (RARE) |

### The "78% wind decreased" Finding

**✅ TRUE** - 78% of drops had wind DECREASING  
**💡 INTERPRETATION**: This is **normal physics**, not a surprise:
- Lower wind speed → Lower power output
- This is NOT a "forecast bust" unless the wind drop was unpredicted

**To assess forecast accuracy, we need**:
- Actual NWP forecast wind speeds (not available yet)
- Compare: Predicted wind vs Actual wind
- Then categorize: Model correct vs Forecast error

---

## 📊 KEY STATISTICS (CORRECTED)

### Capacity Factor Drops (542 events)
- **Average drop**: -11.9% (from 21.2% to 9.3%)
- **Worst drop**: -40.4% (East Anglia One, April 2024)
- **Pattern**: 7 of top 10 are calm arrival events

### Weather Changes During Drops
- **Wind**: 11.7 → 8.6 m/s (**-3.1 m/s**)
- **Temperature**: 11.1 → 10.9°C (-0.2°C)
- **Humidity**: 80.6 → 80.1% (-0.5%)
- **Waves**: 1.35 → 1.17 m (-0.18 m, lags wind)

### Wind Regime Distribution
- **Calm (<4 m/s)**: 14% of hours
- **Light (4-8 m/s)**: 33%
- **Moderate (8-12 m/s)**: 31%
- **Fresh (12-17 m/s)**: 18%
- **Strong (17-25 m/s)**: 4%
- **Storm (>25 m/s)**: **0.1%** ← Turbine cut-out threshold

---

## 🚨 WHAT WAS WRONG WITH PREVIOUS ANALYSIS

### Headline Claims (from WIND_YIELD_DROPS_UPSTREAM_ANALYSIS.md)

| Claim | Status | Reality |
|-------|--------|---------|
| "Wind before: 42.3 m/s" | ❌ WRONG | 11.7 m/s (÷3.6) |
| "Final wind: 49.3 m/s (max: 100 m/s!)" | ❌ WRONG | 13.7 m/s (max: 29.4 m/s) |
| "Storm curtailment: 10% (54 events)" | ❌ WRONG | 0.4% (2 events) |
| "Wind INCREASED: 22% (storm curtailment)" | ⚠️ MISLEADING | 22% increased, but only 2 exceeded 25 m/s |
| "Wind DECREASED: 78% (calm arrival)" | ✅ CORRECT | But "calm arrival" is overstated (only 30% are <6 m/s final) |
| "Upstream stations show 1-12hr lead time" | ✅ CORRECT | Pressure/temp/humidity patterns valid |

### Why Units Matter

A turbine with 25 m/s cut-out threshold:
- **If we believed the wrong data**: 42.3 m/s = already cut out, CF should be 0%, but it was 21% → contradiction
- **With correct data**: 11.7 m/s = well within operating range, 21% CF makes sense

---

## 📁 FILES CREATED/UPDATED

### Data Quality Fix
1. **fix_wind_units_and_add_gusts.py** - Creates BigQuery view with km/h → m/s
2. **BigQuery view: `era5_weather_corrected`** - Properly labeled units

### Updated Scripts
3. **download_era5_with_gusts.py** - New download script with gusts + pressure
4. **download_era5_remaining_farms_24h.sh** - Cron job wrapper script
5. **analyze_wind_yield_drops_CORRECTED.py** - Corrected analysis

### Documentation
6. **WIND_YIELD_DROPS_DATA_QUALITY_FIXED.md** - Full corrected analysis
7. **SUMMARY_WIND_ANALYSIS_FIXED.md** - This document

### Data Output
8. **wind_yield_drops_corrected.csv** - 542 events with realistic wind speeds

---

## 🎯 WHAT TO DO NEXT

### Immediate Actions ✅ DONE
- [x] Fix wind speed units (km/h → m/s)
- [x] Create corrected analysis script
- [x] Set up cron job for remaining farms
- [x] Document data quality issues

### Tomorrow (Jan 2, 03:00 UTC) ⏳ AUTOMATED
- [ ] Cron job downloads next 5 farms with gust data
- [ ] Check log: `/home/george/GB-Power-Market-JJ/logs/era5_download_with_gusts_20260102.log`

### Next Week 🔜 MANUAL
- [ ] Once all 41 farms downloaded, re-run correlation analysis
- [ ] Add wind direction data for wake effect analysis
- [ ] Download actual NWP forecasts for true forecast error assessment

### Optional Enhancements 💡
- [ ] Build upstream station early warning dashboard
- [ ] Implement real-time monitoring with alerts
- [ ] Calculate Weibull distribution for wind resource
- [ ] Compare ERA5 vs CMEMS wind speeds (data quality check)

---

## 🌐 UPSTREAM WEATHER STATION RECOMMENDATIONS (Still Valid)

Even with corrected data, the upstream station concept is sound:

### Lead Times (Confirmed)
- **Pressure**: 6-12 hours (regime change indicator)
- **Temperature**: 3-6 hours (frontal passage)
- **Humidity**: 2-4 hours (air mass indicator)
- **Wind Direction**: 1-3 hours (direct mechanical signal)
- **Wind Speed**: 1-2 hours (immediate precursor)

### Installation Locations
- **50-150 km west** of offshore farms
- Weather moves **west → east** at 20-60 km/h
- Full instrumentation: pressure, wind (speed + direction), temp, humidity
- Cost: ~£50k per station vs £millions in forecast improvement

### What to Monitor
1. **Pressure rising +2-4 mb** → Calm arrival risk (30% of drops)
2. **Pressure falling <-5 mb/hr** → Storm approach (rare curtailment)
3. **Wind direction shift 45-90°** → Wake effect risk (2% of drops)
4. **Humidity >90% + weak pressure gradient** → Stagnant air (forecast bust risk)

---

## 💡 KEY TAKEAWAYS (REVISED)

### The Big Picture
1. **Storm curtailment is rare** (<1% of hours) - don't over-design for it
2. **Calm arrival is the real operational risk** - 30% of significant drops
3. **Most drops are normal physics** - lower wind = lower output (78% of drops)
4. **Forecast error requires actual NWP data** - can't assess without predicted winds
5. **Upstream stations provide actionable early warning** - 1-12 hour lead time

### What Changed Your Mind
Your skepticism about "42 m/s mean wind" was 100% correct. The data had a **units error** (km/h vs m/s). This is a textbook example of:
- **Sanity checking** - "Does this physically make sense?"
- **Domain knowledge** - "Turbines cut out at 25 m/s, so 42 m/s makes no sense"
- **Cross-validation** - "If wind = 42 m/s, CF should be 0%, but it's 21%"

After correction:
- ✅ Wind speeds realistic (9.2 m/s mean, 29.4 m/s max)
- ✅ Storm curtailment rare (0.4%, not 10%)
- ✅ Physics makes sense (lower wind → lower output)

---

## 📞 CRON JOB MONITORING

### Check Status
```bash
# View cron jobs
crontab -l | grep era5

# Check tomorrow's log (after 3 AM)
tail -f /home/george/GB-Power-Market-JJ/logs/era5_download_with_gusts_20260102.log

# Verify farms downloaded
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')
query = 'SELECT COUNT(DISTINCT farm_name) as farms FROM \`inner-cinema-476211-u9.uk_energy_prod.era5_weather_data_v2\`'
df = client.query(query).to_dataframe()
print(f'Farms in era5_weather_data_v2: {df[\"farms\"].values[0]}')
"
```

### Expected Progress
- **Jan 2**: 5 farms downloaded (total: 5)
- **Jan 3**: 5 farms downloaded (total: 10)
- **Jan 4**: 5 farms downloaded (total: 15)
- **Jan 5**: 5 farms downloaded (total: 20) ✅ COMPLETE

---

**Analysis By**: GitHub Copilot + George Major  
**Status**: ✅ Data quality issues resolved, analysis corrected, automation active  
**Next Review**: January 5, 2026 (when all farms downloaded)  
**Contact**: george@upowerenergy.uk
