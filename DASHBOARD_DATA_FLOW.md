# Dashboard Data Flow & Architecture

**Last Updated**: December 17, 2025

## Overview

The GB Power Market dashboard (`update_gb_live_complete.py`) updates Google Sheets with real-time energy market data from BigQuery, including generation mix, interconnectors, outages, and wind forecasts.

---

## Data Sources

### BigQuery Tables (inner-cinema-476211-u9.uk_energy_prod)

| Table | Purpose | Update Frequency |
|-------|---------|------------------|
| `bmrs_fuelinst_iris` | Real-time fuel generation (WIND, CCGT, NUCLEAR, etc.) | Every 5 min (IRIS) |
| `bmrs_mid_iris` | Wholesale market prices | Every 5 min (IRIS) |
| `bmrs_freq_iris` | Grid frequency data | Every 5 min (IRIS) |
| `bmrs_remit_iris` | Active outages (REMIT messages) | Every 5 min (IRIS) |
| `bmrs_windfor` | Wind generation forecasts | Historical (batch) |
| `bmu_registration_data` | BMU asset name lookups | Static reference |

---

## Google Sheets Layout

**Sheet**: `Live Dashboard v2` (ID: 1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA)

### Main Dashboard (Visible)

| Rows | Content | Columns |
|------|---------|---------|
| 2 | Last Updated timestamp + Settlement Period | A |
| 3 | Data freshness warning (if IRIS >15 min old) | A |
| 4-6 | KPIs (Price, Demand, Frequency) | A-F |
| 7 | Sparklines (Wholesale Price, Frequency) | B, E-F |
| 13-22 | Generation Mix (fuel type + GW + sparkline) | A-C |
| 13-22 | Interconnectors (country + MW + sparkline) | D-E, H |
| 25-47 | **Active Outages** (header, columns, data) | G-Q |

### Data_Hidden Sheet

| Rows | Content | Format |
|------|---------|--------|
| 1-10 | Fuel generation timeseries (48 periods) | 10 rows × 48 cols (A-AV) |
| 11-20 | Interconnector flow timeseries (48 periods) | 10 rows × 48 cols (A-AV) |
| 25 | Wholesale price timeseries (48 periods) | 1 row × 48 cols (A-AV) |
| 26 | Frequency deviation timeseries (100 readings) | 1 row × 100 cols (A-CV) |
| **35-37** | **Wind Forecast vs Actual (NEW)** | 3 rows × 48 cols (A-AV) |

#### Wind Forecast Data Structure (Rows 35-37)
```
Row 35: Settlement Periods [1, 2, 3, ..., 48]
Row 36: Actual Wind (GW)    [14.2, 14.5, 14.8, ...]
Row 37: Forecast Wind (GW)  [14.0, 14.3, 14.6, ...]
```

---

## Active Outages Section (NEW)

### Location
- **Main Header**: Row 25, Column G
- **Column Headers**: Row 26, Columns G-Q
- **Data**: Rows 27+, Columns G-Q

### Format
```
G25: ⚠️ ACTIVE OUTAGES - Top 15 by Capacity | Total: X units | Offline: X,XXX MW | Normal Capacity: X,XXX MW

G26-Q26: Asset Name | Fuel Type | Unavail (MW) | Normal (MW) | Type | Category | Expected Return | Duration | Operator | Area | Zone

G27+: [Data rows with emojis, calculations, timestamps]
```

### Data Processing
1. Query `bmrs_remit_iris` for Active outages >50 MW
2. Join with `bmu_registration_data` to get asset names (e.g., "Ffestiniog 3" instead of "T_FFES-3")
3. Calculate duration from `eventEndTime` (e.g., "58d 5h")
4. Classify as Planned (📅) or Unplanned (⚡)
5. Add fuel type emojis (🏭 CCGT, ⚛️ Nuclear, 🌬️ Wind, etc.)

### Key Features
- **Top 15** by unavailable capacity (descending)
- **Latest revision only** (uses `MAX(revisionNumber)`)
- **Total calculations** in header (units, offline MW, normal MW)
- **Real-time updates** from IRIS pipeline

---

## Wind Forecast vs Actual Chart

### Chart Location
- **Position**: Row 32, Column A (A32)
- **Title**: "🌬️ Intraday Wind: Actual vs Forecast (GW)"

### Data Source
- **Hidden data**: Data_Hidden sheet, Column Z starting row 35 (white text)
- **Python updates**: Rows 35-37 (Settlement Periods, Actual, Forecast)

### Chart Configuration (Apps Script)
```javascript
// From clasp-gb-live-2/src/Charts.gs
const windChart = sheet.newChart()
  .setChartType(Charts.ChartType.COMBO)
  .addRange(windRange) // Data_Hidden Z35:AB82
  .setPosition(32, 1, 0, 0)
  .setOption('series', {
    0: {labelInLegend: 'Actual', color: '#2ecc71', type: 'area'},
    1: {labelInLegend: 'Forecast', color: '#3498db', type: 'line', lineDashStyle: [4, 4]}
  })
```

### Data Flow
1. **Python** (`get_wind_forecast_vs_actual()`):
   - Queries `bmrs_fuelinst_iris` for actual WIND generation
   - Queries `bmrs_windfor` for forecast generation
   - Converts MW → GW (`generation / 1000`)
   - Fills missing periods with 0

2. **Write to Sheets**:
   - Row 35: `[1, 2, 3, ..., 48]` (settlement periods)
   - Row 36: `[14.2, 14.5, ...]` (actual GW)
   - Row 37: `[14.0, 14.3, ...]` (forecast GW)

3. **Apps Script**:
   - Reads hidden data from Data_Hidden
   - Creates combo chart (area + dashed line)
   - Auto-updates when dashboard refreshes

---

## Update Schedule

### Automatic Updates
```bash
# Cron job (every 5 minutes)
*/5 * * * * cd /home/george/GB-Power-Market-JJ && /usr/bin/python3 realtime_dashboard_updater.py >> logs/dashboard_updater.log 2>&1
```

### Manual Update
```bash
cd ~/GB-Power-Market-JJ
python3 update_gb_live_complete.py
```

---

## Data Freshness Monitoring

### IRIS Pipeline Status
- **Check**: Row 3 shows warning if IRIS data >15 min old
- **Log**: `logs/dashboard_updater.log`
- **Recovery**: See `IRIS_PIPELINE_RECOVERY_DEC17_2025.md`

### Expected Latency
- **Normal**: 2-5 minutes behind real-time
- **Warning**: >15 minutes (indicates IRIS issue)
- **Critical**: >60 minutes (manual intervention needed)

---

## Key Functions

### Main Script: `update_gb_live_complete.py`

| Function | Purpose | Returns |
|----------|---------|---------|
| `get_generation_mix()` | Current fuel generation (GW) | DataFrame (10 fuels) |
| `get_interconnector_flow()` | IC flows (MW) | DataFrame (10 ICs) |
| `get_fuel_timeseries()` | 48-period fuel data | DataFrame (10×48) |
| `get_wholesale_price_timeseries()` | 48 prices from bmrs_mid_iris | Array (48) |
| `get_frequency_timeseries()` | 100 recent frequency readings | Array (100) |
| `get_interconnector_timeseries()` | 48-period IC flows | DataFrame (10×48) |
| `get_outages_data()` | **Active outages with asset names** | DataFrame (15 max) |
| `get_wind_forecast_vs_actual()` | **Wind actual vs forecast (NEW)** | DataFrame (48 periods) |

---

## Troubleshooting

### Chart Not Showing
1. Check Data_Hidden rows 35-37 have data:
   ```
   =Data_Hidden!A36:AV36  // Should show 48 values
   ```
2. Verify chart exists: Extensions → Apps Script → Run `createCharts()`
3. Redeploy: `cd clasp-gb-live-2 && clasp push`

### Outages Not Updating
- **Check query**: `bmrs_remit_iris` table has Active records
- **Verify join**: Asset names appear (not just BM Unit IDs)
- **Test query**: See `get_outages_data()` function

### Wind Forecast Empty
- **IRIS table**: `bmrs_windfor_iris` may be empty (not configured)
- **Historical table**: `bmrs_windfor` has data through Oct 2025
- **Fallback**: Shows zeros if no forecast available

---

## Recent Changes (Dec 17, 2025)

### ✅ IRIS Pipeline Recovery
- Fixed REMIT schema (6 new fields, FLOAT64 capacity, JSON arrays)
- Pipeline processing 23,683 file backlog
- See: `IRIS_PIPELINE_RECOVERY_DEC17_2025.md`

### ✅ Outages Section Added
- Location: G25-Q47 (was A40-K62)
- Asset name lookup via `bmu_registration_data`
- Duration calculations, emoji classifications
- Total summary in header row

### ✅ Wind Forecast vs Actual
- Data: Data_Hidden rows 35-37
- Chart: Apps Script combo chart at A32
- Updates: Every dashboard refresh

### ✅ Sparkline Positions Updated
- Wholesale: B7 (was G7)
- Frequency: E7-F7 (was F13-F22)
- Time labels: "00:00→" in row 6

---

## Dependencies

### Python Packages
```bash
pip3 install --user google-cloud-bigquery db-dtypes pyarrow pandas gspread oauth2client
```

### Credentials
- **BigQuery**: `inner-cinema-credentials.json`
- **Google Sheets**: OAuth via gspread
- **Project**: `inner-cinema-476211-u9` (NOT jibber-jabber-knowledge)

### Apps Script
- **Project**: clasp-gb-live-2
- **Files**: `src/Charts.gs`, `src/Code.gs`
- **Deploy**: `clasp push` to update

---

## Links

- **Dashboard**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit
- **BigQuery Console**: https://console.cloud.google.com/bigquery?project=inner-cinema-476211-u9
- **IRIS Pipeline Docs**: `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md`
- **Full Project Docs**: `DOCUMENTATION_INDEX.md`

---

**Maintainer**: George Major (george@upowerenergy.uk)  
**Status**: ✅ Production (Auto-updates every 5 min)
