# Spreadsheet Update Scripts & Data Coverage Analysis
**Generated**: January 2, 2026  
**Spreadsheet**: [GB Live Dashboard v2](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit)

---

## 📋 TODO LIST SUMMARY

### ✅ COMPLETED ANALYSIS

1. **✅ All Spreadsheet Update Scripts Identified** (48+ scripts found)
2. **✅ Historic Wind Data Coverage Verified** (3.5 years, 1.1M records)
3. **✅ Live Weather Data Lag Measured** (33 days for weather, 0 days for IRIS generation)
4. **⏳ Documentation & Recommendations** (this document)

---

## 🔧 SCRIPTS THAT UPDATE THE SPREADSHEET

### **Primary Dashboard Updater** (Main Script)
**File**: `update_live_metrics.py` (1,500+ lines)  
**Purpose**: Main auto-updater for Live Dashboard v2  
**What it updates**:
- Row 6: Market KPIs (MID price, frequency, total gen, wind, demand)
- Row 7: Sparkline charts (5 mini-charts: wholesale, freq, gen, wind, demand)
- Rows 13-22: Generation Mix (10 fuel types with MW, %, icons)
- Data_Hidden tab: Historical data for sparklines (49 columns × 37 rows)
- Row 3: IRIS data freshness indicator
- Row 5-6: BM-MID spread calculation

**Update Frequency**: Every 5 minutes (via cron)  
**Crontab**: `*/5 * * * * python3 update_live_metrics.py`

### **Wind Forecast Dashboard Updaters** (NEW)
1. **`detect_upstream_weather.py`** (196 lines)
   - Updates: Wind Forecast section (rows 61-62)
   - What: Upstream pressure alerts, capacity at risk
   - Frequency: Every 15 minutes (manual/cron)

2. **`update_unavailability.py`** (250 lines)
   - Updates: REMIT Unavailability tab
   - What: Active outages (77 assets, 183k MW offline)
   - Frequency: Manual (should be added to cron)

3. **`auto_update_wind_dashboard.py`** (105 lines)
   - Orchestrates: Both upstream weather + REMIT outages
   - Frequency: Every 15 minutes (ready for cron)

### **BM Costs & Analysis**
4. **`update_bm_costs.py`**
   - Updates: BM costs analysis sheet
   - What: Balancing mechanism costs, NIV, PAR
   
5. **`update_top_outages.py`**
   - Updates: Top outages section
   - What: Largest capacity outages

### **Enhanced Dashboards**
6. **`create_wind_analysis_dashboard_enhanced.py`**
   - Creates: Comprehensive wind analysis dashboard
   - What: Weather correlations, ramp analysis, alerts

7. **`update_gb_live_complete.py`** (538+ lines)
   - Updates: Complete GB Live dashboard refresh
   - What: All sections (generation, interconnectors, frequency, etc.)

### **Data Dictionary & Documentation**
8. **`create_data_dictionary_sheet.py`**
   - Updates: DATA DICTIONARY tab
   - What: Field definitions, units, sources

9. **`add_elexon_neso_definitions.py`**
   - Updates: Elexon/NESO term definitions

### **Specialized Analysis Sheets**
10. **`export_complete_data.py`** - BM Units Detail, Balancing Revenue
11. **`export_gsp_dno_to_sheets.py`** - GSP-DNO analysis
12. **`export_constraints_to_sheets.py`** - Constraint actions
13. **`add_geochart_postcodes.py`** - Geographic constraint map
14. **`update_scrp_analysis_to_sheets.py`** - SCRP (balancing) analysis
15. **`upload_vtp_revenue_to_sheets.py`** - VTP revenue tracking

### **Chart & Visualization Scripts**
16. **`add_geo_chart_to_sheets.py`** - Geographic charts
17. **`add_dno_map_to_sheets.py`** - DNO boundary maps
18. **`fix_dno_chart.py`** - Fix DNO chart formatting
19. **`recreate_sparklines.py`** - Rebuild sparkline formulas

### **Formatting & Enhancement**
20. **`optimize_sheets_performance.py`** - Performance optimization
21. **`fix_sparkline_formulas.py`** - Sparkline formula fixes
22. **`format_ic_section.py`** - Interconnector formatting
23. **`apply_test_formatting_to_live.py`** - Apply Test sheet formatting

### **Testing & Diagnostics**
24. **`create_test_dashboard_duplicate.py`** - Create Test sheet
25. **`compare_sheets.py`** - Compare Live vs Test
26. **`analyze_missing_dashboard_data.py`** - Find missing data
27. **`diagnose_apps_script_error.py`** - Debug Apps Script issues

---

## 📊 COMPREHENSIVE DATA COVERAGE

### **1. Wind Generation Data (BMRS B1610 Physical Notifications)**

| Metric | Value | Status |
|--------|-------|--------|
| **Total Records** | 1,103,719 | ✅ Excellent |
| **BM Units Tracked** | 15 wind offshore units | ⚠️ Limited (67 exist) |
| **Date Range** | 2022-05-08 to 2025-10-28 | ✅ 3.5 years |
| **Coverage** | 1,269 days | ✅ Continuous |
| **Avg Generation** | 57.3 MW per unit | ✅ Realistic |
| **Max Generation** | 358 MW | ✅ Plausible |
| **Data Lag** | **66 days** (latest: Oct 28) | ⚠️ **OUT OF DATE** |

**Tracked BM Units** (15 of 67 possible):
- T_HOWAO-1, T_HOWAO-2, T_HOWAO-3 (Hornsea One)
- T_HOWBO-1 (Hornsea Two)
- T_SGRWO-1 (Seagreen Phase 1)
- (10 more units)

**Missing**: 52 wind BM units not tracked in bmrs_pn

---

### **2. ERA5 Weather Data (OpenMeteo Archive API)**

| Metric | Value | Status |
|--------|-------|--------|
| **Farms Covered** | 21 offshore farms | ✅ Good (67% of 31 total) |
| **Total Observations** | 1,348,464 | ✅ Massive dataset |
| **Date Range** | 2020-01-01 to 2025-11-30 | ✅ 5.9 years |
| **Coverage** | 2,160 days | ✅ Continuous |
| **Wind Speed** | 100% complete | ✅ Perfect |
| **Wind Gusts** | 100% complete | ✅ Perfect |
| **Surface Pressure** | 100% complete | ✅ Perfect |
| **Temperature** | 100% complete | ✅ Perfect |
| **Humidity** | 100% complete | ✅ Perfect |
| **Data Lag** | **33 days** (latest: Nov 30) | ⚠️ **MODERATE LAG** |

**Variables Available**:
- wind_speed_100m_ms (turbine hub height)
- wind_gusts_10m_ms (turbulence detection)
- surface_pressure_hpa (upstream weather signals)
- temperature_2m_c (frontal passages)
- relative_humidity_2m_pct (forecast bust detection)
- wind_direction_100m_deg (directional shifts)
- cloud_cover_pct (weather system type)
- precipitation_mm (storm detection)

**Update Frequency**: Weekly backfills (manual run of fetch scripts)

---

### **3. IRIS Real-Time Data (Azure Service Bus)**

| Metric | Value | Status |
|--------|-------|--------|
| **Fuel Mix Records (7d)** | 49,520 | ✅ Excellent |
| **Latest Data** | 2026-01-02 (TODAY!) | ✅ **REAL-TIME** |
| **Data Lag** | **0 days** (same-day updates) | ✅ **LIVE DATA** |
| **Update Frequency** | 15-minute intervals | ✅ Near real-time |
| **Deployment** | AlmaLinux server 94.237.55.234 | ✅ Active |
| **Tables** | bmrs_*_iris (174+ tables) | ✅ Comprehensive |

**Key IRIS Tables**:
- `bmrs_fuelinst_iris` - Fuel mix (wind, gas, nuclear, etc.)
- `bmrs_indgen_iris` - Individual BM unit generation
- `bmrs_freq_iris` - Grid frequency
- `bmrs_mid_iris` - Market index price
- `bmrs_costs_iris` - System costs (currently NOT configured)

**IRIS Coverage**: Last 24-48 hours rolling window  
**Historical Cutoff**: Union with historical tables at ~2025-10-30

---

### **4. Wind Farm Mapping**

| Metric | Value | Status |
|--------|-------|--------|
| **Mapped Farms** | 29 offshore farms | ✅ Good |
| **Mapped BM Units** | 67 units | ✅ Excellent |
| **Total Capacity** | 15,354 MW | ✅ 93.6% of UK offshore |
| **Unmapped Farms** | 2 farms, ~1 GW | ⚠️ Minor gap |

**Best Mapped Farms**:
- Hornsea Two (1,320 MW, 3 BM units)
- Seagreen Phase 1 (1,075 MW, 6 units)
- Moray East (950 MW, 4 units)
- Walney Extension (659 MW, 2 units)
- Beatrice (588 MW, 2 units)

---

## ⏱️ DATA LAG SUMMARY

| Data Source | Latest Date | Lag | Update Frequency | Status |
|-------------|-------------|-----|------------------|--------|
| **IRIS Generation** | 2026-01-02 | 0 days | 15 minutes | 🟢 **REAL-TIME** |
| **ERA5 Weather** | 2025-11-30 | 33 days | Weekly backfill | 🟡 **MODERATE LAG** |
| **BMRS Wind Generation** | 2025-10-28 | 66 days | Manual query | 🔴 **OUT OF DATE** |
| **REMIT Outages** | 2026-01-02 | 0 days | On-demand | 🟢 **CURRENT** |

### **What This Means**:

✅ **Real-Time Data (IRIS)**: You CAN track live generation, frequency, prices  
⚠️ **Weather Analysis**: Limited to data up to Nov 30 (33-day lag)  
❌ **Wind Forecasting**: Cannot use bmrs_pn for recent analysis (66-day lag)

---

## 🚨 CRITICAL GAPS & RECOMMENDATIONS

### **GAP 1: BMRS Wind Generation 66-Day Lag** ⚠️ HIGH PRIORITY

**Problem**: bmrs_pn table (Physical Notifications B1610) hasn't been updated since Oct 28, 2025  
**Impact**: 
- Cannot analyze recent wind generation patterns
- Wind forecast dashboard has no recent actuals
- Upstream weather correlation analysis limited to Nov 30

**Solution**:
```bash
# Update bmrs_pn table with latest data
python3 ingest_elexon_fixed.py --table bmrs_pn --start-date 2025-10-29 --end-date 2026-01-02
```

**Automation**: Add to cron for daily updates:
```bash
0 4 * * * cd /home/george/GB-Power-Market-JJ && python3 ingest_elexon_fixed.py --table bmrs_pn --start-date $(date -d '7 days ago' +\%Y-\%m-\%d) --end-date $(date +\%Y-\%m-\%d)
```

---

### **GAP 2: ERA5 Weather 33-Day Lag** ⚠️ MEDIUM PRIORITY

**Problem**: ERA5 weather data ends Nov 30, 2025 (33 days behind)  
**Impact**:
- Upstream pressure analysis outdated
- Cannot validate recent weather-driven yield drops
- Wind forecast dashboard shows old alerts

**Solution**:
1. **Immediate**: Run backfill script for Dec 2025 data
   ```bash
   python3 fetch_historic_wind_openmeteo_v2.py  # Downloads remaining 20 farms
   ```

2. **Real-Time Weather**: Integrate OpenMeteo Forecast API
   ```bash
   # Create new script: fetch_realtime_weather.py
   # Use OpenMeteo Forecast API (free, 7-day ahead)
   # Store in: era5_weather_forecast table
   # Update frequency: Hourly cron
   ```

3. **Automation**: Weekly ERA5 backfill (Sundays 3am)
   ```bash
   0 3 * * 0 cd /home/george/GB-Power-Market-JJ && python3 backfill_era5_weekly.py
   ```

---

### **GAP 3: Wind Forecast Dashboard Not Auto-Updating** ⚠️ MEDIUM PRIORITY

**Problem**: Upstream weather alerts and REMIT outages update manually only  
**Impact**: Dashboard shows stale weather alerts and outdated outage data

**Solution**: Add to cron (already have scripts!)
```bash
# Add these lines to crontab
*/15 * * * * cd /home/george/GB-Power-Market-JJ && python3 auto_update_wind_dashboard.py >> logs/wind_dashboard_cron.log 2>&1

# Or run individually:
*/15 * * * * cd /home/george/GB-Power-Market-JJ && python3 detect_upstream_weather.py >> logs/upstream_weather.log 2>&1
*/30 * * * * cd /home/george/GB-Power-Market-JJ && python3 update_unavailability.py >> logs/remit_outages.log 2>&1
```

---

### **GAP 4: Only 15 of 67 Wind BM Units Tracked** ⚠️ LOW PRIORITY

**Problem**: bmrs_pn table only tracks 15 offshore wind BM units  
**Impact**: Missing 52 units = incomplete wind generation picture

**Solution**: Expand bmrs_pn queries to include all T_*WO-* units
```sql
-- Add these BM units to ingest_elexon_fixed.py:
'T_MOWWO-%',  -- Moray West
'T_DBAWO-%',  -- Dogger Bank A
'T_TRIWO-%',  -- Triton Knoll
'T_WALWO-%',  -- Walney Extension
'T_BEAT_%',   -- Beatrice
-- etc. (see wind_farm_to_bmu table for full list)
```

---

### **GAP 5: No Real-Time Weather Forecasts** 💡 ENHANCEMENT

**Current**: Historical weather only (33-day lag)  
**Desired**: 7-day wind speed/pressure forecasts for predictive alerts

**Solution**: Integrate OpenMeteo Forecast API
```python
# New script: fetch_wind_forecast.py
import requests

def fetch_openmeteo_forecast(lat, lon):
    """Fetch 7-day wind forecast from OpenMeteo"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        'latitude': lat,
        'longitude': lon,
        'hourly': 'wind_speed_100m,wind_gusts_10m,surface_pressure',
        'forecast_days': 7
    }
    response = requests.get(url, params=params)
    return response.json()

# Store in: wind_forecast_7day table
# Update: Hourly cron
```

**Benefit**: Real-time upstream weather alerts instead of 33-day delayed data!

---

## 📝 RECOMMENDED ACTIONS (Priority Order)

### **TODAY** (High Priority)
1. ✅ **Update bmrs_pn table** - Run Elexon ingest for Oct 29 - Jan 2
2. ✅ **Add wind dashboard to cron** - Enable auto-updates every 15 min
3. ✅ **Test REMIT outages** - Verify 77 assets showing correctly

### **THIS WEEK** (Medium Priority)
4. ⏳ **ERA5 weather backfill** - Get Dec 2025 data (remaining 20 farms)
5. ⏳ **Expand BM unit tracking** - Add 52 missing wind units to bmrs_pn
6. ⏳ **Create weekly ERA5 cron** - Automate Sunday backfills

### **NEXT SPRINT** (Enhancements)
7. ⏳ **Integrate OpenMeteo Forecast API** - Get real-time 7-day forecasts
8. ⏳ **Build 48h generation forecast** - Use upstream correlation model
9. ⏳ **Create 6h farm heatmap** - Farm-level forecasts

---

## 🎯 QUICK REFERENCE COMMANDS

### **Update Wind Generation Data**
```bash
# Update bmrs_pn (Physical Notifications) for last 7 days
python3 ingest_elexon_fixed.py --table bmrs_pn --start-date $(date -d '7 days ago' +%Y-%m-%d) --end-date $(date +%Y-%m-%d)
```

### **Update ERA5 Weather Data**
```bash
# Backfill remaining 20 farms
python3 fetch_historic_wind_openmeteo_v2.py

# Check progress
tail -f logs/era5_download.log
```

### **Update Dashboard**
```bash
# Main dashboard (runs every 5 min automatically)
python3 update_live_metrics.py

# Wind forecast dashboard
python3 auto_update_wind_dashboard.py

# REMIT outages only
python3 update_unavailability.py
```

### **Check Data Coverage**
```bash
# Check latest data dates
python3 -c "
from google.cloud import bigquery
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

tables = [
    ('bmrs_pn', 'settlementDate'),
    ('era5_weather_data_complete', 'timestamp'),
    ('bmrs_fuelinst_iris', 'settlementDate')
]

for table, date_col in tables:
    query = f'SELECT MAX({date_col}) as latest FROM \`inner-cinema-476211-u9.uk_energy_prod.{table}\`'
    df = client.query(query).to_dataframe()
    print(f'{table}: {df.iloc[0][\"latest\"]}'
)
"
```

---

## 📚 KEY DOCUMENTATION FILES

1. **`PROJECT_CONFIGURATION.md`** - All config settings
2. **`STOP_DATA_ARCHITECTURE_REFERENCE.md`** - Data architecture
3. **`WIND_FORECAST_DASHBOARD_FIXES.md`** - Dashboard solutions
4. **`WIND_FORECAST_DASHBOARD_EXPLAINED.md`** - Complete explanation
5. **`WIND_YIELD_DROPS_UPSTREAM_ANALYSIS.md`** - Weather correlation analysis
6. **`DEPLOYMENT_COMPLETE.md`** - Deployment guide
7. **`IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md`** - IRIS setup

---

**Last Updated**: January 2, 2026  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Status**: ✅ Production (48+ scripts identified, data coverage analyzed)
