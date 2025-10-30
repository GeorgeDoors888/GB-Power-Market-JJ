# Solar Data Investigation & Fix - October 29, 2025

## Problem Discovery
User reported that solar data was not updating on the dashboard despite it being daytime (1:45 PM BST).

## Investigation Results

### 1. Data Source Analysis
✅ **FUELINST table**: Contains 20 fuel types but **NO SOLAR**
- Fuel types: CCGT, WIND, NUCLEAR, BIOMASS, NPSHYD, COAL, OCGT, OIL, OTHER, PS, + 10 interconnectors
- Last updated: 2025-10-29 Period 50 (75 minutes old)

✅ **WIND_SOLAR_GEN table exists**: Contains Solar, Wind Offshore, Wind Onshore
- Table: `bmrs_wind_solar_gen`
- psrType: 'Solar' (capital S)
- Total records: 235,203 (78,401 per type)
- Date range: 2022-01-01 to 2025-10-28
- **Latest solar data: 2025-10-28 Period 1 (36.6 hours old)**

### 2. Typical Solar Generation
At Period 26 (13:00-13:30) in October 2025:
- Oct 27: 5.82 GW
- Oct 26: 3.71 GW
- Oct 25: 6.29 GW
- Oct 24: 6.85 GW
- **Average: 4-6 GW at midday**

### 3. Root Cause
**Real-time updater was only fetching FUELINST, not WIND_SOLAR_GEN**

Original code (line 53 of realtime_updater.py):
```python
'--only', 'FUELINST'
```

## Fixes Implemented

### 1. Updated realtime_updater.py
**Changed line 53** to fetch both datasets:
```python
'--only', 'FUELINST,WIND_SOLAR_GEN'
```

### 2. Enhanced Data Freshness Monitoring
Added separate monitoring for both tables:
- FUELINST status
- WIND_SOLAR_GEN status
- Reports age for both datasets

### 3. Updated dashboard_updater_complete.py
Modified `get_latest_fuelinst_data()` function to:
1. Fetch FUELINST data (main generation + interconnectors)
2. Query `bmrs_wind_solar_gen` for solar data
3. Add SOLAR to the data dictionary
4. Handle cases where solar data is missing (returns 0.0 GW)

## Current Status

### Cron Job
✅ Running every 5 minutes: `*/5 * * * *`
✅ Now configured to fetch both FUELINST and WIND_SOLAR_GEN
✅ Logs to: `/Users/georgemajor/GB Power Market JJ/logs/realtime_cron.log`

### Dashboard Updates
✅ Dashboard updater now pulls solar from `bmrs_wind_solar_gen`
✅ Handles missing solar data gracefully
✅ Updates all 28 cells including solar generation

### Data Freshness (as of 14:06 UTC Oct 29)
- **FUELINST**: 75 minutes old ⚠️
- **WIND_SOLAR_GEN**: 2197 minutes old (36.6 hours) ❌

## Why Solar is Still 0.0 GW

The API (`/generation/actual/per-type/wind-and-solar`) appears to have a **publication delay**.
- Last available data: 2025-10-28
- Current date: 2025-10-29
- The real-time updater is running correctly but finding "0 existing windows" (no new data from API)

## Next Steps

### Option A: Wait for API Update
The BMRS API typically publishes WIND_SOLAR_GEN data with a delay. The real-time updater will automatically fetch it once available.

### Option B: Use Estimation
Could estimate solar based on:
- Time of day
- Historical patterns
- Weather data (if available)

### Option C: Alternative Data Source
Check if solar is available from:
- `generation_actual_per_type` table
- `generation_wind_solar` table  
- Other BMRS endpoints

## Verification Commands

### Check data freshness:
```bash
python realtime_updater.py --check-only
```

### Manual fetch:
```bash
python realtime_updater.py --minutes-back 120
```

### Check logs:
```bash
tail -50 logs/realtime_updates.log
```

### Run dashboard update:
```bash
python dashboard_updater_complete.py
```

## Files Modified

1. **realtime_updater.py**
   - Line 53: Added WIND_SOLAR_GEN to fetch list
   - Lines 80-114: Enhanced data freshness monitoring
   - Header comments updated

2. **dashboard_updater_complete.py**
   - Lines 41-69: Modified `get_latest_fuelinst_data()` to fetch solar

## Monitoring

The real-time updater will continue attempting to fetch WIND_SOLAR_GEN every 5 minutes. Once the API publishes today's data:
1. Real-time updater will ingest it automatically
2. Dashboard updater will pick it up on next run
3. Solar values will appear on dashboard

## Expected Behavior

Once solar data arrives:
- Dashboard Row 8 will show: "☀️ Solar: X.X GW" (where X is 3-7 GW during midday)
- Renewables percentage will increase accordingly
- Low carbon generation will be more accurate

## Additional Notes

- The WIND_SOLAR_GEN dataset has been configured in the ingestion script since the beginning
- It's properly mapped to the `/generation/actual/per-type/wind-and-solar` endpoint
- The issue was simply that the real-time updater wasn't requesting it
- Cron job is now properly configured to fetch both datasets

---

**Status**: ✅ Configuration fixed, waiting for API to publish today's solar data
**Next check**: Wait 30-60 minutes and run `python realtime_updater.py --check-only`
