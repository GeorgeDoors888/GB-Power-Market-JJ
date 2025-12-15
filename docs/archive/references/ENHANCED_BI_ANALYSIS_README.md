# 🚀 Enhanced BI Analysis Sheet

> **⚠️ BEFORE YOU START**: Read [`PROJECT_CONFIGURATION.md`](PROJECT_CONFIGURATION.md) for critical setup details (BigQuery project, region, table schemas, Python commands)

## Overview
This enhanced Analysis sheet implements the **Unified Data Architecture** (documented in `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`) that combines historical batch data with real-time IRIS streaming data in your **inner-cinema-476211-u9.uk_energy_prod** dataset.

## 🏗️ Architecture Foundation

This sheet is built on the **Two-Pipeline Architecture** developed October 30, 2025:

1. **Historical Pipeline** (Elexon API) - Batch ingestion of past data
2. **Real-Time Pipeline** (IRIS) - Streaming current data via Azure Service Bus

Both pipelines write to the same BigQuery project using **different table names** to keep them separate but queryable together via UNION queries.

## 📊 What's Different from the Original?

### Original Analysis Sheet
- ✅ Generation data only (bmrs_fuelinst_unified)
- ✅ Date range dropdown
- ✅ Simple metrics

### Enhanced BI Analysis Sheet (Based on Unified Architecture)
- ✅ **4 Data Sections**: Generation, Frequency, Prices, Balancing
- ✅ **Historical + Real-time**: Combines `bmrs_*` (historical) and `bmrs_*_iris` (IRIS) tables
- ✅ **Rich Metrics**: Renewable %, grid stability, price spreads
- ✅ **Source Mix**: Shows historical vs IRIS data counts
- ✅ **Advanced Calculations**: Wind curtailment, balancing stats, capacity factors, data quality
- ✅ **Multiple Views**: Summary, detailed tables

## 🗂️ Data Sources (Two-Pipeline Architecture)

| Section | Historical Table<br/>(Elexon API) | Real-Time Table<br/>(IRIS Stream) | Combined | Architecture |
|---------|-----------------|-----------------|----------|--------------|
| Generation Mix | `bmrs_fuelinst` | `bmrs_fuelinst_iris` | ✅ UNION | 5.7M + IRIS rows |
| System Frequency | `bmrs_freq` | `bmrs_freq_iris` | ✅ UNION | Per-minute streaming |
| Market Prices | `bmrs_mid` | `bmrs_mid_iris` | ✅ UNION | System Buy/Sell |
| Balancing Costs | `bmrs_netbsad` + `bmrs_bod` | N/A | ✅ Combined | Bid-Offer Data |

**Note:** The architecture separates historical (2020-2025 batch data) from real-time (last 24-48 hours streaming) using different table names, allowing seamless UNION queries for complete timelines.

## 🎯 Key Features

### 1. Control Panel
- **Quick Select Dropdown**: 24 Hours, 1 Week, 1 Month, 3 Months, 6 Months, 1 Year, Custom
- **Custom Date Range**: Specify exact from/to dates
- **View Type**: Summary, Generation Mix, System Frequency, etc.

### 2. Summary Metrics (Top Cards)
```
🔋 Total Generation    ⚖️ Avg System Frequency    💰 Avg System Price
🌱 Renewable %         📈 Peak Demand              ⚡ Grid Stability
```

### 3. Generation Mix Section
- **Fuel Type Breakdown**: Wind, CCGT, Nuclear, Solar, etc.
- **Metrics per Fuel**: Total MWh, Avg MW, % Share, Max/Min
- **Source Mix**: Shows Historical vs IRIS record counts

### 4. System Frequency Section
- **Real-time Monitoring**: Latest 20 frequency measurements
- **Deviation Tracking**: Shows mHz deviation from 50 Hz
- **Status Flags**: Normal (49.8-50.2 Hz) or Alert
- **Grid Stability**: Overall assessment

### 5. Market Prices Section
- **System Prices**: Buy Price (SBP) and Sell Price (SSP)
- **Price Spreads**: Calculated spread between buy/sell
- **Settlement Period**: 48 periods per day

### 6. Balancing Costs Section
- **NETBSAD + DISBSAD**: Combined balancing costs
- **Category Breakdown**: By cost category
- **Rate Calculation**: £/MWh rate for each action

## 📝 Usage

### Initial Setup
```bash
cd ~/GB\ Power\ Market\ JJ
python3 create_analysis_bi_enhanced.py
```

This creates a new sheet called **"Analysis BI Enhanced"** with:
- All section headers and formatting
- Dropdown controls
- Initial data population (default: 1 week)

### Refresh Data
```bash
python3 update_analysis_bi_enhanced.py
```

This:
1. Reads your dropdown selections (Quick Select, Custom dates, View Type)
2. Queries BigQuery with your date range
3. Updates all 4 sections with fresh data
4. Recalculates summary metrics

### Using the Sheet

1. **Open the sheet**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/

2. **Select date range**:
   - Use **Quick Select** dropdown (cell B5): Choose "1 Week", "1 Month", etc.
   - OR use **Custom** dates: Enter dates in cells D5 and F5 (format: DD/MM/YYYY)

3. **Refresh data**:
   ```bash
   python3 update_analysis_bi_enhanced.py
   ```

4. **Analyze**:
   - Scroll through the 4 sections
   - Check summary metrics at top
   - Look for patterns in frequency, prices, balancing costs

## 🔄 Unified Architecture Implementation

### Two-Pipeline Design (October 30, 2025)

This sheet implements the **Unified Data Architecture** that seamlessly combines:

**Historical Pipeline (Batch):**
```
Elexon BMRS API → Python Scripts → BigQuery (bmrs_* tables)
- Data: 2020-2025 (multi-year backfill)
- Update: On-demand/15-min cron
- Tables: bmrs_fuelinst, bmrs_freq, bmrs_mid, bmrs_bod, etc.
- Status: ✅ 174 tables populated
```

**Real-Time Pipeline (Streaming):**
```
Azure Service Bus (IRIS) → Python Client → JSON Files → Processor → BigQuery (bmrs_*_iris tables)
- Data: Last 24-48 hours
- Update: Continuous streaming (30s-2min latency)
- Tables: bmrs_fuelinst_iris, bmrs_freq_iris, bmrs_mid_iris, etc.
- Status: 🟢 Operational since Oct 30, 2025
```

### Query Pattern (UNION for Complete Timeline)
```sql
-- Example: Complete generation timeline (historical + real-time)
WITH combined AS (
  -- Historical data (older)
  SELECT 
    publishTime as timestamp,
    fuelType,
    generation,
    'historical' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
  WHERE publishTime >= '2025-10-01'
  
  UNION ALL
  
  -- Real-time data (most recent)
  SELECT 
    publishTime as timestamp,
    fuelType,
    generation,
    'real-time' as source
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
  WHERE publishTime >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL 2 HOUR)
)
SELECT 
  fuelType,
  SUM(generation) as total_generation,
  AVG(generation) as avg_generation,
  COUNTIF(source='historical') as hist_count,
  COUNTIF(source='real-time') as iris_count
FROM combined
GROUP BY fuelType;
```

**Key Design Decision:** Separate tables (`bmrs_*` vs `bmrs_*_iris`) instead of merged tables for:
- Clear separation and debugging
- Performance optimization (IRIS optimized for low-latency)
- Future flexibility (easy to merge or keep separate)

## 📊 Metrics Calculated

### Generation Metrics
- ✅ Total Generation (MWh)
- ✅ Renewable % (Wind, Solar, Hydro, Biomass, Nuclear)
- ✅ Peak Demand (Max MW across all fuels)
- ✅ Fuel Type % Share

### Frequency Metrics
- ✅ Average Frequency (Hz)
- ✅ Deviation from 50 Hz (mHz)
- ✅ Grid Stability Status (Normal/Warning/Critical)

### Price Metrics
- ✅ Average System Price (£/MWh)
- ✅ Price Spread (Buy - Sell)

### Balancing Metrics
- ✅ Total Balancing Costs (£)
- ✅ Balancing Volume (MWh)
- ✅ Rate (£/MWh)

## 🎨 Sheet Structure

```
Row 1:    HEADER (Enhanced BI Analysis Dashboard)
Row 3:    CONTROL PANEL
Row 5:    Dropdowns (Quick Select, Custom Dates, View Type)
Row 7:    KEY METRICS (6 summary cards)
Row 15:   GENERATION MIX Section
Row 17:   Generation table headers
Row 18-34: Generation data (up to 20 fuel types)
Row 35:   SYSTEM FREQUENCY Section
Row 37:   Frequency table headers
Row 38-59: Frequency data (20 records)
Row 60:   MARKET PRICES Section
Row 62:   Price table headers
Row 63-84: Price data (20 records)
Row 85:   BALANCING COSTS Section
Row 87:   BSAD table headers
Row 88-109: BSAD data (20 records)
Row 110:  Last Updated timestamp
```

## 🚀 Next Steps

### 1. Future Architecture: Unified Views (Phase 2)

As documented in `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`, the next phase could involve:

**Option A: Merge IRIS data into historical tables**
```sql
-- Periodically merge IRIS data into historical tables
INSERT INTO `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
WHERE measurementTime NOT IN (
    SELECT measurementTime 
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
)
```

**Option B: View layer (Recommended for now)**
```sql
-- Create unified views that combine both sources automatically
CREATE OR REPLACE VIEW `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_unified` AS
SELECT *, 'historical' as source 
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
UNION ALL
SELECT *, 'real-time' as source
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq_iris`
WHERE measurementTime > (
    SELECT MAX(measurementTime) 
    FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
)
```

**Current Status:** Sticking with **Phase 1 (separate tables)** until IRIS pipeline proven stable over multiple days.

### 2. Automate Refresh
Set up cron job:
```bash
# Refresh every 30 minutes
*/30 * * * * cd ~/GB\ Power\ Market\ JJ && python3 update_analysis_bi_enhanced.py >> analysis_bi_refresh.log 2>&1
```

### 3. Add Charts
- Generation pie chart (fuel mix %)
- Frequency timeline chart
- Price spread timeline
- Balancing cost trend

### 4. Add More Sections
- Interconnector flows (if you have bmrs_interconnector tables)
- Demand forecast accuracy
- Carbon intensity correlation

## 📚 Related Files & Architecture Documentation

### ⭐ Essential Reading
- **`PROJECT_CONFIGURATION.md`** - 🔧 **START HERE!** Single source of truth for:
  - BigQuery project ID, region, dataset names
  - Python commands (python3 not python!)
  - Table schemas (bmrs_bod, bmrs_freq column names)
  - Common pitfalls and solutions
  - Script templates and pre-flight checklist

### Core Scripts
- `create_analysis_bi_enhanced.py` - Initial setup script (creates 4-section sheet)
- `update_analysis_bi_enhanced.py` - Data refresh script (updates all sections)
- `update_analysis_with_calculations.py` - Advanced calculations (fixed Oct 31, 2025)
- `read_full_sheet.py` - Full sheet reader and validator

### Architecture Documentation (October 30-31, 2025)
- **`UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md`** - ⭐ **Core architecture document**
  - Two-pipeline design (Historical + IRIS)
  - Table naming conventions
  - Query patterns (UNION)
  - System status and components
  - Future roadmap (Phase 2: unified views)

- `SCHEMA_FIX_SUMMARY.md` - Schema troubleshooting (Oct 31, 2025)
  - bmrs_bod column mismatch resolution
  - bmrs_freq measurementTime fix
  - db-dtypes installation
  
- `ENHANCED_BI_STATUS.md` - Initial deployment status
- `SIMPLE_REFRESH_SOLUTIONS.md` - Menu workaround (parked)

### Historical Pipeline Scripts
- `ingest_elexon_fixed.py` - Batch download from Elexon API
- `fetch_fuelinst_today.py` - Today's generation data
- `update_graph_data.py` - Historical dashboard updater

### Real-Time Pipeline Components
- `iris-clients/python/client.py` - IRIS message downloader (PID 81929)
- `iris_to_bigquery_unified.py` - IRIS processor → BigQuery (PID 15141)
- `automated_iris_dashboard.py` - IRIS-specific dashboard updater

## 💡 Tips

1. **Date Range Selection**: Use shorter ranges (24 Hours, 1 Week) for faster queries
2. **Custom Dates**: Great for analyzing specific events (storms, market spikes)
3. **Source Mix Column**: Shows how much data comes from historical vs real-time
4. **Grid Stability**: Critical if frequency goes below 49.5 Hz or above 50.5 Hz
5. **Renewable %**: Track progress toward net-zero targets

## 🔍 Troubleshooting

### "No data returned"
- Check date range (might be too narrow)
- Verify tables exist: `bmrs_fuelinst`, `bmrs_freq`, `bmrs_qas`, `bmrs_netbsad`, `bmrs_disbsad`
- Check IRIS tables populated: `bmrs_fuelinst_iris`, `bmrs_freq_iris`

### "Query timeout"
- Reduce date range (try 1 Week instead of 1 Year)
- Reduce LIMIT in queries (change from 20 to 10)

### "Missing metrics"
- Some metrics require recent data
- Peak demand needs at least 1 day of data
- Renewable % needs multiple fuel types

## ✅ What You Have Now

| Feature | Original Sheet | Enhanced BI Sheet |
|---------|---------------|-------------------|
| Generation Data | ✅ | ✅ Enhanced with % share |
| System Frequency | ❌ | ✅ NEW |
| Market Prices | ❌ | ✅ NEW |
| Balancing Costs | ❌ | ✅ NEW |
| Historical Data | ✅ | ✅ |
| Real-Time Data | ✅ | ✅ |
| Date Dropdowns | ✅ | ✅ |
| Summary Metrics | ⚠️ Basic | ✅ Rich (6 cards) |
| Source Mix | ❌ | ✅ Shows Hist vs IRIS |
| Grid Stability | ❌ | ✅ Calculated |
| Renewable % | ❌ | ✅ Calculated |

---

## 🎯 Summary

**You have a hybrid dual-pipeline data system:**

1. **Historical Pipeline (Elexon API)** ✅
   - Operational since 2020
   - 174 tables with 391M+ rows (bmrs_bod alone)
   - Perfect for analysis, reporting, trends
   - Updated: On-demand or 15-min cron

2. **Real-Time Pipeline (IRIS)** 🟢
   - Operational since Oct 30, 2025
   - 8+ streaming tables (_iris suffix)
   - Perfect for monitoring, alerts, live dashboards
   - Updated: Continuous (30s-2min latency)

3. **This BI Sheet** 📊
   - Combines both via UNION queries
   - Shows source mix (Historical vs IRIS)
   - 4 sections: Generation, Frequency, Prices, Balancing
   - Advanced calculations: Wind curtailment, capacity factors, quality scores
   - Live Google Sheet dashboard with dropdown controls

**Architecture designed for future expansion:** Ready for Phase 2 unified views when IRIS pipeline proven stable.

---

**Created**: 31 October 2025  
**Updated**: 31 October 2025 (Added advanced calculations & schema fixes)  
**Dataset**: `inner-cinema-476211-u9.uk_energy_prod`  
**Architecture**: Two-Pipeline (Historical + Real-Time IRIS)  
**Documentation**: See `UNIFIED_ARCHITECTURE_HISTORICAL_AND_REALTIME.md` for complete system design  
**Repository**: https://github.com/GeorgeDoors888/jibber-jabber-24-august-2025-big-bop  
**Local Path**: ~/GB Power Market JJ
