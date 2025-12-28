# NESO Data Portal: Unique Datasets vs Elexon BMRS

**Analysis Date**: 28 December 2025  
**NESO API**: https://api.neso.energy/api/3/action/  
**Total Datasets**: 124

---

## ✅ Already Downloading (Via API)

### 1. Constraint Breakdown Costs and Volume (2017-2026)
- **Status**: DOWNLOADING IN BACKGROUND (PID 2287625)
- **Tables**: `neso_constraint_breakdown_2017_2018` through `neso_constraint_breakdown_2025_2026`
- **Categories**: Thermal, Voltage, Inertia constraints (costs & volumes)
- **Update Frequency**: Annual files, updated within 2-3 months of year-end
- **Unique**: ✅ NOT in Elexon BMRS (NESO-specific constraint analysis)

---

## 🆕 NESO-EXCLUSIVE Datasets (NOT in Elexon)

### 2. **Historic Generation Mix & Carbon Intensity** ⭐
- **ID**: `historic-generation-mix`
- **Resource ID**: `f93d1835-75bc-43e5-84ad-12472b180a98`
- **Coverage**: 1 January 2009 - Present (updated DAILY)
- **Last Updated**: 28 December 2025
- **Content**: 
  - Generation by fuel type (CCGT, Nuclear, Wind, Solar, Coal, etc.)
  - Carbon intensity (gCO2/kWh)
  - Seasonal decomposition applied (cleaned data)
- **Why Unique**: Aggregated historic generation mix with carbon intensity
- **Elexon Equivalent**: BMRS has `FUELINST` (real-time) but not historic aggregated mix
- **Value**: Long-term carbon analysis, generation trends (2009-2025)

### 3. **Open Balancing Platform (OBP) - Non-BM Physical Notifications**
- **ID**: `open-balancing-platform-obp-non-bm-physical-notification`
- **Content**: Physical notifications for NON-BM units (distributed generators)
- **Update**: Real-time/near real-time
- **Why Unique**: 
  - Elexon BMRS only covers BM units
  - OBP covers distributed/embedded generators (non-BM)
  - Important for NGSEA detection (Feature C alternative!)
- **Status**: May solve FPN blocker (Todo #4)

### 4. **Open Balancing Platform (OBP) - Reserve Availability**
- **ID**: Similar to OBP Physical Notifications
- **Content**: Reserve capacity availability (MW) for non-BM units
- **Why Unique**: Non-BM reserve data not in BMRS

### 5. **Skip Rates** ⭐
- **ID**: `skip-rates`
- **Content**: Monthly dispatch efficiency metrics (skip rate = % of instructions skipped)
- **Update Frequency**: Monthly (2-4 weeks lag)
- **Why Unique**: NESO operational efficiency metric, not published by Elexon
- **Discovery**: Found 1 dataset (confirmed in earlier search)

### 6. **Operational Planning Margin Requirement (OPMR)**
- **Daily**: `daily-opmr` (updated daily)
- **Weekly**: `weekly-opmr` (updated weekly)
- **Content**: MW margin required for system security
- **Why Unique**: NESO planning metric, not in BMRS
- **Value**: Forecast constraint risk, tight margin = higher BM costs

### 7. **Carbon Intensity Forecasts**
- **National**: `national-carbon-intensity-forecast`
- **Regional**: `regional-carbon-intensity-forecast`
- **Country**: `country-carbon-intensity-forecast`
- **Update**: Real-time/near real-time
- **Why Unique**: NESO-specific carbon forecasting (not in BMRS)

### 8. **Wind Availability**
- **Daily**: `daily-wind-availability` (updated daily)
- **Weekly**: `weekly-wind-availability` (updated weekly)
- **Content**: MW wind capacity available vs installed
- **Why Unique**: Availability factors not published by Elexon at this granularity

### 9. **14 Days Ahead Wind & Demand Forecasts**
- **Wind**: `14-days-ahead-wind-forecast`
- **Demand**: `2-14-days-ahead-national-demand-forecast`
- **Update**: Daily
- **Why Unique**: Medium-term forecasts (Elexon has day-ahead only)

### 10. **Embedded Wind & Solar Forecasts**
- **ID**: `embedded-wind-and-solar-forecasts`
- **Content**: Distribution-level (non-transmission) generation forecasts
- **Why Unique**: Embedded generation not visible in BMRS
- **Value**: Full system generation picture (transmission + distribution)

### 11. **Non-BM ASDP (Ancillary Service Dispatch Platform)**
- **Instructions**: `non-bm-ancillary-service-dispatch-platform-asdp-instructions`
- **Window Prices**: `non-bm-ancillary-service-dispatch-platform-asdp-window-prices`
- **Content**: Ancillary service dispatch for non-BM providers
- **Why Unique**: Non-BM services not in BMRS

---

## ⚠️ POTENTIAL DUPLICATES (Also in Elexon BMRS)

### Datasets to SKIP (Already Have from BMRS)

1. **Balancing Mechanism Acceptances** - Have via BMRS `BOALF`
2. **Bid-Offer Data** - Have via BMRS `BOD`
3. **System Prices** - Have via BMRS `COSTS` (SSP/SBP)
4. **Frequency Data** - Have via BMRS `FREQ`
5. **Interconnector Flows** - Have via BMRS (IFA, BritNed, etc.)

---

## 📅 Publication Timing: NESO vs Elexon

### Real-Time Data (< 5 min lag)
- **NESO**: OBP instructions, Carbon intensity forecasts
- **Elexon**: BMRS real-time feeds (BOALF, FREQ, FUELINST)
- **Winner**: TIE (both real-time)

### Day-Ahead Data (published daily)
- **NESO**: Wind availability, OPMR, demand forecasts
- **Elexon**: Day-ahead prices (not published), unit data
- **Winner**: NESO (more forward-looking data)

### Historical Aggregated Data
- **NESO**: 
  - Constraint breakdown (annual, 2-3 month lag)
  - Skip rates (monthly, 2-4 week lag)
  - Historic generation mix (daily updates, full history since 2009)
- **Elexon**: 
  - Raw BM data (real-time, but not aggregated)
  - Settlement data P114 (2-3 day lag for II, 28 days for SF)
- **Winner**: MIXED
  - NESO: Better for aggregated analysis (constraint costs, skip rates)
  - Elexon: Better for granular BM unit-level data

### Settlement Data
- **NESO**: Not published (NESO doesn't run settlement)
- **Elexon**: P114 settlement flows (authoritative source)
- **Winner**: ELEXON (ONLY source for settlement)

---

## 🎯 Recommended NESO Datasets to Ingest

### HIGH PRIORITY (Unique & Valuable)

1. ✅ **Constraint Breakdown** (DOWNLOADING NOW)
   - Priority: HIGH
   - Status: In progress (9 years, 2017-2026)

2. ⭐ **Historic Generation Mix & Carbon Intensity**
   - Priority: HIGH
   - Coverage: 2009-2025 (17 years!)
   - Command: 
     ```bash
     python3 ingest_neso_api.py \
       --resource-id f93d1835-75bc-43e5-84ad-12472b180a98 \
       --table-name neso_generation_mix_historic
     ```
   - Value: Carbon analysis, generation trends

3. ⭐ **OBP Non-BM Physical Notifications**
   - Priority: HIGH (solves FPN blocker!)
   - May provide alternative for NGSEA Feature C
   - Command: Research dataset ID first
     ```bash
     python3 ingest_neso_api.py --search "OBP physical notification"
     ```

4. ⭐ **Skip Rates**
   - Priority: MEDIUM
   - Monthly dispatch efficiency
   - Command: 
     ```bash
     python3 ingest_neso_api.py --search "skip rate"
     ```

5. **OPMR (Daily & Weekly)**
   - Priority: MEDIUM
   - Operational margin forecasts
   - Useful for predicting high BM cost periods

6. **Wind Availability (Daily & Weekly)**
   - Priority: LOW-MEDIUM
   - Helps explain constraint costs (wind availability = transmission constraints)

### MEDIUM PRIORITY (Nice to Have)

7. **Embedded Wind & Solar Forecasts**
   - Full generation picture (transmission + distribution)

8. **14 Days Ahead Wind & Demand Forecasts**
   - Medium-term planning

9. **Non-BM ASDP Instructions**
   - Non-BM ancillary services

### LOW PRIORITY (Skip for Now)

- Carbon intensity forecasts (real-time, high volume, low analytical value)
- Regional data (unless doing regional analysis)

---

## 🔄 Update Frequency Comparison

| Dataset Type | NESO Update | Elexon Update | Lag Difference |
|--------------|-------------|---------------|----------------|
| **Real-time BM** | N/A (NESO doesn't run BM) | < 5 min | Elexon only |
| **Settlement** | N/A | II: 2-3 days, SF: 28 days | Elexon only |
| **Constraint costs** | Annual (2-3 month lag) | Not published | NESO only |
| **Generation mix** | Daily (1 day lag) | Real-time (FUELINST) | Elexon faster, but NESO has history |
| **Forecasts** | Daily | Day-ahead only | NESO has 2-14 day forecasts |
| **Skip rates** | Monthly (2-4 week lag) | Not published | NESO only |
| **Non-BM data** | Real-time/daily | Not published | NESO only |

---

## 💡 Key Insights

### What NESO Has That Elexon Doesn't:

1. **Aggregated constraint analysis** (breakdown by type: thermal/voltage/inertia)
2. **Historic generation mix** (2009-present, cleaned data)
3. **Non-BM unit data** (distributed generators via OBP)
4. **Operational metrics** (skip rates, OPMR)
5. **Medium-term forecasts** (2-14 days ahead)
6. **Embedded generation** (distribution-level)

### What Elexon Has That NESO Doesn't:

1. **Settlement data** (P114 - authoritative revenue source)
2. **Granular BM unit data** (bid-offer, acceptances, FPN)
3. **Real-time BM actions** (sub-5 minute)
4. **Individual generator instructions** (BM-level detail)

### Optimal Strategy:

- **Elexon BMRS**: Granular BM analysis, settlement, revenue
- **NESO Data Portal**: System-level analysis, constraints, forecasts, non-BM units

---

## 📊 Data Completeness Assessment

### Current Coverage (via Elexon BMRS):
- ✅ BM Units: BOD, BOALF, P114 settlement
- ✅ System prices: COSTS (SSP/SBP)
- ✅ Frequency: FREQ
- ✅ Generation: FUELINST (real-time)
- ✅ Demand: INDOD, MELIMBALNGC

### Missing (Available via NESO):
- ❌ Constraint breakdown by type
- ❌ Historic generation mix (cleaned, 2009-2025)
- ❌ Non-BM physical notifications (OBP)
- ❌ Skip rates (dispatch efficiency)
- ❌ Embedded generation forecasts
- ❌ Medium-term forecasts (2-14 days)

### After NESO Ingestion:
- ✅ Constraint costs (thermal/voltage/inertia) - 2017-2026
- ✅ Historic generation mix - 2009-2025
- ✅ OBP non-BM data (if ingested)
- ✅ Skip rates (if ingested)

**Coverage Improvement**: 22/46 sources (48%) → 26+/46 sources (57%+)

---

## 🚀 Next Actions

1. ✅ **Wait for constraint breakdown download** (~1 hour, in progress)

2. **Download Historic Generation Mix** (HIGH PRIORITY):
   ```bash
   python3 ingest_neso_api.py \
     --resource-id f93d1835-75bc-43e5-84ad-12472b180a98 \
     --table-name neso_generation_mix_historic
   ```

3. **Research OBP Physical Notifications** (solves FPN blocker):
   ```bash
   python3 ingest_neso_api.py --search "OBP physical"
   curl "https://api.neso.energy/api/3/action/package_show?id=open-balancing-platform-obp-non-bm-physical-notification"
   ```

4. **Download Skip Rates**:
   ```bash
   python3 ingest_neso_api.py --search "skip rate"
   # Get resource ID, then download
   ```

5. **Consider OPMR & Wind Availability** (lower priority)

---

**Estimated Time to Complete**:
- Constraint breakdown: ~1 hour (in progress)
- Historic generation mix: ~15 min (17 years, single file)
- OBP physical notifications: ~30 min (research + download)
- Skip rates: ~10 min (small dataset)
- **Total**: ~2 hours for all high-priority datasets

**Status**: Constraint breakdown downloading, 2021-2022 complete (1/9 years done)
