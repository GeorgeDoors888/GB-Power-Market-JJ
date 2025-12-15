# GB Live Dashboard - Complete Data Sources Reference

⚠️ **CRITICAL: THIS DOCUMENTATION IS FOR THE LEGACY SPREADSHEET**  
**Sheet:** GB Live (in spreadsheet 1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I) - **LEGACY/OLD**  
**Last Updated:** December 9, 2025  
**Update Script:** `update_gb_live_executive.py` - **NOT ACTIVELY MAINTAINED**

---

## ⚠️ IMPORTANT: Active Dashboard Information

**If you are looking for the CURRENT/ACTIVE Live Dashboard v2**, see instead:
- **Spreadsheet ID:** `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA` ✅ CORRECT
- **Documentation:** `GB_LIVE_DASHBOARD_V2_DOCUMENTATION.md`
- **Update Scripts:** 
  - `update_live_dashboard_v2.py` (basic updater)
  - `update_gb_live_complete.py` (with sparklines)
- **Recent Fix:** See `LIVE_DASHBOARD_V2_FIX_SUMMARY.md` for IRIS duplicate data fix (Dec 11, 2025)

**This document below refers to the OLD/LEGACY spreadsheet and may contain outdated information.**

---

## 💷 PRICE DATA SOURCES

### 1. System Imbalance Prices (£/MWh)
**Table:** `bmrs_costs` + `bmrs_costs_iris`  
**Columns Available:**
- `systemSellPrice` (£/MWh) - Energy Imbalance Price (SSP)
- `systemBuyPrice` (£/MWh) - Energy Imbalance Price (SBP)
- `settlementDate` (DATETIME)
- `settlementPeriod` (INTEGER 1-50)

**Note:** SSP = SBP since Nov 2015 (BSC Mod P305 single imbalance price)

**Historical Coverage:**
- `bmrs_costs`: 2020-01-01 to ~yesterday
- `bmrs_costs_iris`: Last 24-48 hours (real-time)

**Usage in GB Live:**
- A7: VLP Revenue (7-day avg × 1000)
- B6: Wholesale Price £/MWh (7-day avg)
- Row 41-42: 48-period price history sparkline

**Query Example:**
```sql
SELECT 
  settlementDate,
  settlementPeriod,
  systemSellPrice as imbalance_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
ORDER BY settlementDate DESC, settlementPeriod DESC
```

---

### 2. Market Index Data (Wholesale Prices)
**Table:** `bmrs_mid` + `bmrs_mid_iris`  
**Columns Available:**
- `price` (£/MWh) - Day-ahead/within-day wholesale price
- `volume` (MWh) - Trading volume
- `settlementDate` (DATETIME)
- `settlementPeriod` (INTEGER)

**Status:** ⚠️ Currently NO recent data (last entry ~2024)  
**Fallback:** Uses `bmrs_costs.systemSellPrice` instead

**Historical Coverage:**
- `bmrs_mid`: 2020-01-01 to ~2024 (stale)
- `bmrs_mid_iris`: Not currently configured in IRIS

**Usage in GB Live:**
- Intended for wholesale price (currently using bmrs_costs fallback)

---

### 3. Balancing Mechanism Bid-Offer Data
**Table:** `bmrs_bod`  
**Columns Available:**
- `bmUnitId` (STRING) - BM Unit identifier
- `pairId` (INTEGER) - Bid-offer pair ID
- `offer` (FLOAT64) - Offer price (£/MWh)
- `bid` (FLOAT64) - Bid price (£/MWh)
- `offerVolume` (FLOAT64) - Offered volume (MWh)
- `bidVolume` (FLOAT64) - Bid volume (MWh)
- `settlementDate` (DATETIME)
- `settlementPeriod` (INTEGER)

**Historical Coverage:** 391M+ rows (2020-present)  
**Note:** This is bid-offer DATA, NOT acceptances!

**Usage in GB Live:** Not currently used (available for future VLP analysis)

---

### 4. Balancing Mechanism Acceptances
**Table:** `bmrs_boalf` + `bmrs_boalf_iris`  
**Columns Available:**
- `acceptanceNumber` (STRING)
- `acceptanceTime` (DATETIME)
- `bmUnit` (STRING)
- `soFlag` (BOOLEAN) - SO-flagged constraint action
- `storFlag` (BOOLEAN) - STOR action
- `rrFlag` (BOOLEAN) - Replacement Reserve
- `settlementDate` (DATETIME)
- `settlementPeriod` (INTEGER)

**⚠️ CRITICAL:** NO price/volume columns! Only acceptance metadata.

**Historical Coverage:**
- `bmrs_boalf`: 2020-present
- `bmrs_boalf_iris`: Last 24-48 hours

**Usage in GB Live:**
- Geographic constraints analysis (joins with bmu_registration_data)
- Scotland wind curtailment counting

---

### 5. Disaggregated Balancing Services Adjustment Data
**Table:** `bmrs_disbsad`  
**Columns Available:**
- `assetId` (STRING) - Asset identifier (e.g., 'OFR-GH-001')
- `cost` (FLOAT64) - £ cost of action
- `volume` (FLOAT64) - MWh volume
- `so_flag` (BOOLEAN) - SO constraint action
- `settlementDate` (DATETIME)
- `settlementPeriod` (INTEGER)

**Historical Coverage:** 2020-present  

**Usage in GB Live:**
- Geographic constraints analysis (OFR pricing)
- Balancing cost breakdown

---

## 💨 WIND DATA SOURCES

### 1. Wind Generation (Actual)
**Table:** `bmrs_fuelinst` + `bmrs_fuelinst_iris`  
**Column:** `generation` (MW) where `fuelType = 'WIND'`

**Other Columns:**
- `fuelType` (STRING) - 'WIND', 'CCGT', 'NUCLEAR', etc.
- `generation` (FLOAT64) - MW generation
- `settlementDate` (DATETIME)
- `settlementPeriod` (INTEGER)

**Historical Coverage:**
- `bmrs_fuelinst`: 2020-01-01 to ~yesterday
- `bmrs_fuelinst_iris`: Last 24-48 hours (real-time)

**Usage in GB Live:**
- A10: 💨 Wind: XX.XX GW (XX.X%)
- Row 25: Intraday wind sparkline (48 periods)
- Row 41-48: Wind forecast vs actual analysis

**Query Example:**
```sql
SELECT 
  settlementDate,
  settlementPeriod,
  SUM(generation) / 1000 as wind_gw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE fuelType = 'WIND'
  AND CAST(settlementDate AS DATE) = CURRENT_DATE()
GROUP BY settlementDate, settlementPeriod
ORDER BY settlementPeriod
```

---

### 2. Wind Forecast Data
**Table:** `bmrs_windfor_iris`  
**Columns Available:**
- `generationMw` (FLOAT64) - Forecasted wind generation (MW)
- `publishTime` (DATETIME) - When forecast was published
- `targetTime` (DATETIME) - Target time for forecast
- `quantity` (STRING) - Forecast type identifier

**Historical Coverage:** Last ~7 days (IRIS real-time)

**Usage in GB Live:**
- Row 36: Wind forecast (actual)
- Row 37: Forecast error (%)
- Row 38: 24h trend (%)
- Row 39: 48-period avg error

**Query Example:**
```sql
SELECT 
  targetTime,
  AVG(generationMw) / 1000 as forecast_gw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_windfor_iris`
WHERE CAST(targetTime AS DATE) = CURRENT_DATE()
GROUP BY targetTime
ORDER BY targetTime
```

---

### 3. Wind Forecast Accuracy Metrics
**Derived Data** (calculated in `get_wind_forecast_vs_actual()` function)

**Metrics Available:**
- Actual generation (GW)
- Forecast generation (GW)
- Absolute error (GW)
- Percentage error (%)
- Bias direction (over/under forecasting)

**Time Ranges:**
- Last 48 settlement periods (~24 hours)
- Real-time comparison (latest period)
- 24-hour rolling trend

**Usage in GB Live:**
- F36: Wind Actual (current)
- F37: Wind Forecast (current)
- F38: Forecast error %
- F39: 24h trend %
- F40: 48-period avg error %
- F41: Forecast bias (OVER-FORECASTING/UNDER-FORECASTING)

---

## 📊 OTHER GENERATION DATA

### All Fuel Types Available in `bmrs_fuelinst`
1. **WIND** - Onshore + offshore wind
2. **CCGT** - Combined cycle gas turbines
3. **NUCLEAR** - Nuclear power stations
4. **BIOMASS** - Biomass generators
5. **NPSHYD** - Non-pumped storage hydro
6. **PS** - Pumped storage
7. **OTHER** - Other generation types
8. **OCGT** - Open cycle gas turbines
9. **COAL** - Coal power stations (currently 0 GW)
10. **OIL** - Oil-fired generation (currently 0 GW)

### Interconnectors (fuelType LIKE 'INT%')
11. **INTFR** - France interconnector
12. **INTELEC** - ElecLink
13. **INTIFA2** - IFA2 (France)
14. **INTNSL** - NSL (Norway)
15. **INTNEM** - Nemolink (Belgium)
16. **INTNED** - BritNed (Netherlands)
17. **INTIRL** - Moyle (Ireland)
18. **INTEW** - East-West (GB-Ireland)
19. **INTGRNL** - Greenlink (Ireland)
20. **INTVKL** - Viking Link (Denmark)

---

## 🔌 FREQUENCY DATA

**Table:** `bmrs_freq`  
**Columns Available:**
- `frequency` (FLOAT64) - Grid frequency (Hz)
- `measurementTime` (DATETIME) - Measurement timestamp

**Note:** Column is `measurementTime` NOT `recordTime`!

**Historical Coverage:** Real-time, high-frequency data

**Usage in GB Live:**
- D6: Grid Frequency XX.X Hz (latest from last hour)

**Query Example:**
```sql
SELECT 
  measurementTime,
  frequency
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_freq`
WHERE measurementTime >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
ORDER BY measurementTime DESC
LIMIT 1
```

---

## 📈 DEMAND DATA

**Source:** Calculated from `bmrs_fuelinst` + `bmrs_fuelinst_iris`

**Formula:**
```
Total Demand = Σ(domestic generation) + Σ(interconnector imports) - Σ(interconnector exports)
```

**Components:**
- Domestic generation: SUM(generation) WHERE fuelType NOT LIKE 'INT%'
- Interconnector flows: SUM(generation) WHERE fuelType LIKE 'INT%'
  - Positive = import (adds to demand)
  - Negative = export (subtracts from demand)

**Usage in GB Live:**
- B7: Total Demand: XX.XX GW
- Row 26: Intraday demand sparkline (48 periods)

---

## 🗺️ GEOGRAPHIC CONSTRAINT DATA

### BMU Registration Data
**Table:** `bmu_registration_data`  
**Columns Available:**
- `bmUnitId` (STRING)
- `fueltype` (STRING)
- `gspGroup` (STRING) - Grid Supply Point group
- `latitude` (FLOAT64)
- `longitude` (FLOAT64)
- `ngc_bmUnit` (STRING)
- `registered_capacity_mw` (FLOAT64)

**Usage in GB Live:**
- Joins with `bmrs_boalf` for geographic constraints
- Scotland wind curtailment analysis
- Region-specific constraint mapping

---

## 📝 DATA UPDATE FREQUENCIES

| Data Type | Table | Update Frequency | Coverage |
|-----------|-------|------------------|----------|
| Imbalance Prices | `bmrs_costs_iris` | ~5 minutes | Last 24-48h |
| Generation Mix | `bmrs_fuelinst_iris` | ~5 minutes | Last 24-48h |
| Wind Forecast | `bmrs_windfor_iris` | ~30 minutes | Last 7 days |
| Frequency | `bmrs_freq` | Real-time | Continuous |
| Acceptances | `bmrs_boalf_iris` | ~5 minutes | Last 24-48h |
| Historical Prices | `bmrs_costs` | Daily (4 AM cron) | 2020-present |
| Historical Gen | `bmrs_fuelinst` | Daily (4 AM cron) | 2020-present |
| Market Index | `bmrs_mid` | ❌ Stale (2024) | Not updating |

---

## 🚨 KNOWN DATA GAPS & LIMITATIONS

### 1. No Volume/Price in BOALF
- `bmrs_boalf` only has acceptance NUMBER and TIME
- NO `acceptanceVolume` or `acceptancePrice` columns
- Must join with `bmrs_disbsad` or `bmrs_bod` for financial data

### 2. Market Index Data Stale
- `bmrs_mid` last updated ~2024
- `bmrs_mid_iris` not configured in IRIS pipeline
- **Workaround:** Use `bmrs_costs.systemSellPrice` as proxy

### 3. Single Imbalance Price
- SSP = SBP since Nov 2015 (P305 modification)
- Both columns exist for backward compatibility
- Battery arbitrage based on TEMPORAL price variation, not SSP/SBP spread

### 4. Duplicate Settlement Periods in bmrs_costs
- Pre-existing data (2022-Oct 27) has ~55k duplicate periods
- **Mitigation:** Use `AVG()` or `GROUP BY` in queries
- New data (Oct 29+) has zero duplicates

### 5. Wind Forecast Matching
- Forecast `targetTime` may not align exactly with settlement periods
- Join logic rounds to nearest 30-minute period
- Some forecast periods may be missing

---

## 💡 QUICK REFERENCE: Common Queries

### Get Latest Wind Generation
```sql
SELECT SUM(generation)/1000 as wind_gw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE fuelType = 'WIND'
  AND CAST(settlementDate AS DATE) = CURRENT_DATE()
  AND settlementPeriod = (SELECT MAX(settlementPeriod) 
                          FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
                          WHERE CAST(settlementDate AS DATE) = CURRENT_DATE())
```

### Get 7-Day Average Price
```sql
SELECT AVG(systemSellPrice) as avg_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
```

### Get All Generation Mix (Current)
```sql
SELECT 
  fuelType,
  SUM(generation)/1000 as gw,
  SUM(generation)/(SELECT SUM(generation) 
                   FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
                   WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
                     AND fuelType NOT LIKE 'INT%'
                     AND settlementPeriod = (SELECT MAX(settlementPeriod)...)) * 100 as pct
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
WHERE CAST(settlementDate AS DATE) = CURRENT_DATE()
  AND fuelType NOT LIKE 'INT%'
  AND settlementPeriod = (SELECT MAX(settlementPeriod)...)
GROUP BY fuelType
ORDER BY gw DESC
```

### Get Scotland Wind Curtailment (Last 7 Days)
```sql
SELECT 
  COUNT(*) as actions,
  COUNT(DISTINCT boalf.bmUnit) as units,
  SUM(ABS(disbsad.volume)) as mw_curtailed,
  SUM(ABS(disbsad.cost)) as cost_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` boalf
JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_disbsad` disbsad
  ON boalf.acceptanceNumber = disbsad.acceptanceNumber
JOIN `inner-cinema-476211-u9.uk_energy_prod.bmu_registration_data` bmu
  ON boalf.bmUnit = bmu.bmUnitId
WHERE boalf.settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  AND bmu.fueltype = 'WIND'
  AND (bmu.gspGroup LIKE '_A%' OR bmu.gspGroup LIKE '_B%')
  AND boalf.soFlag = TRUE
```

---

## 📞 Support & Documentation

- **Main README:** `BG_LIVE_UPDATER_README.md`
- **Python Script:** `update_gb_live_executive.py`
- **BigQuery Project:** `inner-cinema-476211-u9`
- **Dataset:** `uk_energy_prod`
- **Sheet ID:** `1MSl8fJ0to6Y08enXA2oysd8wvNUVm3AtfJ1bVqRH8_I`

For data architecture questions, see: `STOP_DATA_ARCHITECTURE_REFERENCE.md`
