# Dashboard Update Procedure - CORRECT METHOD

**Date**: November 21, 2025  
**Status**: ✅ WORKING

## ⚠️ CRITICAL: Dashboard Has Complex Layout

The Dashboard uses a **multi-column layout** where:
- Columns A-C contain BOTH fuel types AND interconnectors on same rows
- Row 5 contains system metrics summary
- Must use `update_dashboard_preserve_layout.py` (NOT `comprehensive_dashboard_update.py`)

## ✅ Correct Update Scripts

### 1. **Main Data Update** (Fuel + Interconnectors + Flags)
```bash
python3 update_dashboard_preserve_layout.py
```

**What it updates**:
- ✅ Fuel breakdown (rows 6-17, columns B-C)
- ✅ Interconnector flows (rows 7-16, columns D-E)
- ✅ Country flags (all 10 interconnectors: 🇫🇷🇮🇪🇧🇪🇳🇱🇳🇴🇩🇰)
- ✅ Timestamp (row 2)
- ❌ Does NOT update row 5 system metrics
- ❌ Does NOT update outages

### 2. **Outages Update** (Deduplicated)
```bash
python3 update_dashboard_with_dedup.py
```

**What it updates**:
- ✅ Power station outages (rows 23-32, deduplicated by affectedUnit)
- ✅ Timestamp (row 2)
- ❌ Does NOT update fuel/interconnector data

### 3. **Full Update** (All Sections)
```bash
# Run both scripts in sequence:
python3 update_dashboard_preserve_layout.py && python3 update_dashboard_with_dedup.py
```

## ❌ Scripts That DON'T Work

### `comprehensive_dashboard_update.py`
**Problem**: Assumes simple column layout (B=fuel, D=interconnector)  
**Reality**: Dashboard has complex multi-column layout with mixed data  
**Result**: Writes to wrong cells, breaks alignment  
**Status**: ❌ DO NOT USE

### `fix_flags_and_outages.py`
**Problem**: Only queries data, doesn't write system metrics to row 5  
**Status**: ⚠️ Incomplete

### `final_dashboard_update.py`
**Problem**: Only updates outages, doesn't handle deduplication  
**Status**: ⚠️ Use `update_dashboard_with_dedup.py` instead

## 🔧 Data Issues Fixed

### Issue 1: Generation Units Wrong (2695 GW → 35 GW)
**Root Cause**: `bmrs_fuelinst_iris.generation` is in **MW** (not MWh)  
**Fix**: `generation_gw = generation_mw / 1000` (NOT `/500`)  
**Status**: ✅ Fixed in `update_dashboard_preserve_layout.py`

### Issue 2: Duplicate Outages (13x IFA France)
**Root Cause**: Multiple REMIT records for same unit (different timestamps/capacities)  
**Fix**: `GROUP BY affectedUnit` with `MAX(unavailableCapacity)`  
**Result**: 26,556 MW → 9,156 MW (deduplicated)  
**Status**: ✅ Fixed in `update_dashboard_with_dedup.py`

### Issue 3: Row 5 System Metrics Not Updating
**Root Cause**: `update_dashboard_preserve_layout.py` doesn't write to row 5  
**Status**: ⚠️ NEEDS FIX (see below)

## 🎯 TO FIX: Row 5 System Metrics

**Current State**: Row 5 shows stale data:
```
Total Generation: 37.0 GW | Supply: 37.9 GW | Renewables: 35% | 💰 Market Price: £90.01/MWh (SP46)
```

**Should Show** (based on current data):
```
Total Generation: 35.2 GW | Supply: 36.1 GW | Renewables: 21% | 💰 Market Price: £121.64/MWh (SP22)
```

**Fix Required**: Modify `update_dashboard_preserve_layout.py` to write system metrics to row 5.

## 📋 Current Dashboard State

**Last Update**: 2025-11-21 11:27:35

**Fuel Breakdown** (Rows 6-17, Col B-C):
- 🔥 CCGT: 22.1 GW
- 💨 WIND: 4.1 GW
- ⚛️ NUCLEAR: 3.8 GW
- 🌱 BIOMASS: 3.3 GW
- 💧 NPSHYD: 0.5 GW
- ⚡ OTHER: 1.2 GW
- 🔥 OCGT: 0.3 GW
- ⛏️ COAL: 0.0 GW
- 🛢️ OIL: 0.0 GW
- 🔋 PS: -0.2 GW

**Interconnectors** (Rows 7-16, Col D-E):
- 🇫🇷 ElecLink (France): 0 MW Balanced
- 🇮🇪 East-West (Ireland): 0 MW Balanced
- 🇫🇷 IFA (France): 3 MW Export
- 🇮🇪 Greenlink (Ireland): 0 MW Balanced
- 🇫🇷 IFA2 (France): 3 MW Export
- 🇮🇪 Moyle (N.Ireland): 0 MW Balanced
- 🇳🇱 BritNed (Netherlands): 0 MW Balanced
- 🇧🇪 Nemo (Belgium): 0 MW Balanced
- 🇳🇴 NSL (Norway): 643 MW Export
- 🇩🇰 Viking Link (Denmark): 1090 MW Export

**Outages** (Rows 23-32, deduplicated):
- 10 unique outages
- Total: 9,156 MW unavailable
- Major: IFA2 France (1,014 MW), IFA France interconnectors (multiple 1,500 MW outages)

## 🔍 Verification Commands

### Check Current Data
```bash
# Fuel generation
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); df = client.query('SELECT fuelType, ROUND(SUM(generation)/1000,1) as gw FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris\` WHERE DATE(settlementDate) = CURRENT_DATE() GROUP BY fuelType ORDER BY gw DESC LIMIT 10').to_dataframe(); print(df)"

# Outages (deduplicated)
python3 -c "from google.cloud import bigquery; client = bigquery.Client(project='inner-cinema-476211-u9'); df = client.query('SELECT affectedUnit, MAX(unavailableCapacity) as mw FROM \`inner-cinema-476211-u9.uk_energy_prod.bmrs_remit_unavailability\` WHERE eventStatus=\"Active\" GROUP BY affectedUnit ORDER BY mw DESC LIMIT 10').to_dataframe(); print(df); print(f\"Total: {df[\\\"mw\\\"].sum()} MW\")"
```

### Check Dashboard State
```bash
python3 -c "import pickle, gspread; creds = pickle.load(open('token.pickle','rb')); gc = gspread.authorize(creds); sheet = gc.open_by_key('12jY0d4jzD6lXFOVoqZZNjPRN-hJE3VmWFAPcC_kPKF8').worksheet('Dashboard'); print('Row 2:', sheet.acell('B2').value); print('Row 5:', sheet.acell('B5').value)"
```

## 📚 Reference Documentation

- **STOP_DATA_ARCHITECTURE_REFERENCE.md** - MW units warning
- **DASHBOARD_FIX_NOV_21_2025.md** - Complete fix documentation
- **DASHBOARD_CURRENT_STATUS_NOV_20_2025.md** - Dashboard features

---

**Status**: ⚠️ Partially Working  
**Next Step**: Fix row 5 system metrics update in `update_dashboard_preserve_layout.py`
