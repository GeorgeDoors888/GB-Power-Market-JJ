# Account Setup & Priority Todos Status
**Date**: 28 December 2025, 16:00 UTC

## 🔑 GOOGLE ACCOUNT CONFIGURATION

### ⚠️ IMPORTANT: Service Account (NOT Personal Gmail Accounts)
**Email**: `all-jibber@inner-cinema-476211-u9.iam.gserviceaccount.com`  
**Project**: `inner-cinema-476211-u9`  
**Credentials**: `inner-cinema-credentials.json`

This is a **GCP Service Account** that handles:
- ✅ BigQuery: Both `uk_energy_prod` (US location) and `gb_power` (EU location) datasets
- ✅ Google Sheets API access for dashboard automation
- ✅ Google Maps JavaScript API (for DNO boundary maps)
- ✅ Real-time ingestion: IRIS pipeline (PID 46608, running since Dec 20)

**Current Usage**:
- BigQuery queries: ~100 queries/day
- IRIS ingestion: Active (COSTS, FREQ, MID tables)
- P114 backfill: 342.6M / 584M records (58.7%, started Oct 13, 2021)
- Sheets automation: Dashboard refresh every 5 min

---

### 📧 Human Accounts (for context)
- **george@upowerenergy.uk**: NESO Data Portal access, project maintainer
- **User-facing sheets**: Shared with relevant stakeholders via service account permissions

---

## 📊 INGESTION STATUS UPDATE

### ✅ Real-Time IRIS Ingestion (RUNNING)
**Status**: 🟢 ACTIVE (last cycle 15:45 UTC)
**Process**: `python3 iris_to_bigquery_unified.py --continuous` (PID 46608)
**Uptime**: 8 days (since Dec 20)

**Recent Activity** (15:45 cycle):
```
✅ COSTS: 30 records inserted
✅ FUELINST: No new records (up to date)
✅ FREQ: 57 records inserted
✅ MID: 64 records inserted
```

**Tables Updated**:
- `bmrs_costs_iris` - System imbalance prices
- `bmrs_fuelinst_iris` - Fuel mix generation
- `bmrs_freq_iris` - Grid frequency
- `bmrs_mid_iris` - Market Index Data

---

### 🔄 P114 Settlement Backfill (58.7% COMPLETE)
**Status**: 🟡 IN PROGRESS (SINCE OCT 2021!)
**Current**: 342,646,594 / 584,000,000 records
**Progress**: +60.8M records since last check (10.4% gain in ~6 hours)
**Remaining**: 241,353,406 records
**ETA**: 1-2 January 2026

**IMPORTANT CONTEXT**: This backfill started from **October 13, 2021** - it's processing **4+ years of historical settlement data** (1,148 days so far). The process has been running continuously for 8 days (since Dec 20, 2025) and is ingesting data for 9,195 BM units across 48 settlement periods per day.

**Rate**: ~10-15M records/hour (accelerated from previous rate)

---

## 🟡 HIGH PRIORITY TODOS (2)

### 1️⃣ Google My Maps Auto-Upload ⚠️ BLOCKED
**Status**: 🔴 MANUAL IMPORT REQUIRED
**Blocker**: Google My Maps has NO programmatic API
**Time**: 30 min OAuth setup (NOT worth effort for manual task)

**Current State**:
- ✅ Script created: `auto_update_google_my_maps.py`
- ✅ KML file ready: `dno_boundaries.kml` (14 DNO regions)
- ✅ Guide available: `GOOGLE_MY_MAPS_GUIDE.md`
- ❌ OAuth credentials not configured (need client_credentials.json)

**Solution Options**:
1. **RECOMMENDED**: Manual import (5 minutes)
   - Go to https://www.google.com/mymaps
   - Sign in with smart.grd@gmail.com
   - Import `dno_boundaries.kml`
   - Done!

2. **Alternative**: Google Drive upload + reference
   - Requires OAuth setup (30 min)
   - Still manual My Maps import required
   - NOT WORTH IT

**Decision Needed**: Accept manual import or invest 30 min in OAuth?

---

### 2️⃣ BESS Real-Time DUoS Lookup - Using Hardcoded Rates
**Status**: 🟡 PARTIALLY WORKING (postcode/MPAN/DNO lookup OK, rates hardcoded)
**Blocker**: Need to verify why BigQuery lookup failing

**Investigation Findings**:
- ✅ Table exists: `gb_power.duos_unit_rates` (verified in code)
- ✅ Schema defined: dno_key, voltage_level, red_rate, amber_rate, green_rate
- ✅ Used in: `dno_webapp_client.py` (line 133), `btm_dno_lookup.py` (line 242)
- ❌ Current behavior: Using hardcoded rates instead of BigQuery

**Files Affected**:
- `dno_webapp_client.py` - Main DNO lookup (uses duos_unit_rates)
- `btm_dno_lookup.py` - Alternative lookup (also queries duos_unit_rates)
- `bess_live_duos_tracker.py` - Real-time tracker (line 99: get_duos_rates_for_dno)
- `bess_cost_tracking.py` - Cost calculator (line 24 comment: "not from BigQuery")

**Next Steps** (1-2 hours):
1. Query `gb_power.duos_unit_rates` to verify data exists
2. Check row count and sample rates
3. Test BigQuery query from affected scripts
4. Fix schema mismatch if found
5. Replace hardcoded rates with live lookup
6. Test with BESS calculator sheet

**Expected Outcome**: Live DUoS rates from BigQuery instead of hardcoded values

---

## 🟢 MEDIUM PRIORITY TODOS (2)

### 3️⃣ BESS HH Profile Generator
**Status**: 🔴 NOT IMPLEMENTED
**Complexity**: 3-4 hours
**Blocker**: None (straightforward implementation)

**Requirements**:
- Generate half-hourly import/export profiles
- Factor in DUoS time bands (Red/Amber/Green)
- Calculate costs per settlement period
- Export to BESS sheet or CSV

**Menu Item Exists**: Google Sheets menu has entry, but no backend script

**Implementation Plan**:
1. Create `bess_hh_profile_generator.py` script
2. Query `bmrs_costs` for imbalance prices
3. Join with `duos_time_bands` for Red/Amber/Green periods
4. Calculate optimal charge/discharge schedule
5. Output: CSV or direct to BESS sheet

---

### 4️⃣ Dashboard V3 Design Reconciliation
**Status**: 🔴 CONFLICTING IMPLEMENTATIONS
**Time**: 2-3 hours
**Blocker**: Architectural decision required

**Two Versions Exist**:

**Version A - Apps Script** (dark slate theme):
- File: `dashboard/apps-script/dashboard_charts_v3_final.gs`
- KPIs: 6 metrics
- Theme: Dark slate background
- Charts: Stacked columns, line graphs

**Version B - Python** (orange theme):
- File: `python/dashboard_v3_auto_refresh_with_data.py`
- KPIs: 7 metrics
- Theme: Orange/warm colors
- Auto-refresh: Every 5 min

**Conflict**: Two dashboards pulling same data with different designs

**Decision Needed**:
1. Which version is canonical? (Apps Script or Python)
2. Keep both or merge?
3. If merge, which theme to use?

**Recommendation**: Keep Python version (auto-refresh working), update Apps Script to match

---

## 🔍 INTERCONNECTOR DATA DISCOVERY

**Finding**: Found actual interconnector flow data!
**Table**: `balancing_physical_mels` (837k rows)
**Units Found**: 
- I_EAD-IFA2 (IFA2 interconnector - UK ↔ France)
- I_EAG-IFA2
- I_IED-IFA2
- I_IEG-IFA2

**Data Type**: Physical Notification MELs (Maximum Export Limits)
**Use Case**: Track interconnector flows between UK and Europe

**Next Steps** (optional):
1. Query for all interconnector units (IFA, IFA2, BritNed, Nemo, NSL, Viking, ElecLink)
2. Create summary table: interconnector_flows_daily
3. Visualize import/export patterns
4. Correlate with wind generation and prices

---

## 📁 FILES READY FOR USE

### Data Dictionary
- ✅ `data_dictionary.json` (594KB) - All 308 tables documented
- ✅ `data_dictionary_summary.json` (1.2KB) - Quick reference
- ✅ Usage: `jq '.tables[] | select(.category == "BMRS Historical")' data_dictionary.json`

### Google My Maps
- ✅ `dno_boundaries.kml` - 14 DNO regions with cost data
- ✅ `dno_boundaries.geojson` (5.6MB) - Source GeoJSON
- ✅ `GOOGLE_MY_MAPS_GUIDE.md` - Import instructions
- ✅ `convert_geojson_to_kml.py` - Conversion utility

### Todo Status
- ✅ `TODO_STATUS_REPORT.md` - Comprehensive progress report
- ✅ This file: `ACCOUNT_SETUP_STATUS.md` - Account configuration

---

## 🎯 RECOMMENDED IMMEDIATE ACTIONS

### Priority 1: Fix BESS DUoS Lookup (1-2 hours)
**Why**: Currently using hardcoded rates (incorrect for different DNOs)
**Impact**: BESS calculator showing wrong costs
**Action**: Debug why BigQuery lookup failing, switch to live rates

### Priority 2: Manual Import DNO Map (5 minutes)
**Why**: Quickest visual win, no coding required
**Impact**: Shareable interactive map for stakeholders
**Action**: Import `dno_boundaries.kml` to Google My Maps (smart.grd@gmail.com)

### Priority 3: Dashboard V3 Decision (30 min discussion)
**Why**: Two implementations causing confusion
**Impact**: Clean up codebase, standardize design
**Action**: Decide canonical version, deprecate other

### Priority 4: BESS HH Profile Generator (3-4 hours, low urgency)
**Why**: Menu item exists but non-functional
**Impact**: Complete BESS feature set
**Action**: Implement after fixing DUoS lookup

---

## 💡 QUICK WINS AVAILABLE

1. **Verify P114 Data Quality** (10 min)
   ```sql
   SELECT bm_unit_id, COUNT(*) as records
   FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
   WHERE bm_unit_id IN ('FBPGM002', 'FFSEN005')
   GROUP BY bm_unit_id
   ```

2. **Check DUoS Rates Table** (5 min)
   ```sql
   SELECT COUNT(*) as total_rows,
          COUNT(DISTINCT dno_key) as dno_count,
          COUNT(DISTINCT voltage_level) as voltage_levels
   FROM `inner-cinema-476211-u9.gb_power.duos_unit_rates`
   ```

3. **Test Interconnector Query** (5 min)
   ```sql
   SELECT bmUnit, COUNT(*) as notification_count,
          MIN(settlementDate) as first_date,
          MAX(settlementDate) as last_date
   FROM `inner-cinema-476211-u9.uk_energy_prod.balancing_physical_mels`
   WHERE bmUnit LIKE '%INT%' OR bmUnit LIKE '%IFA%'
   GROUP BY bmUnit
   ```

---

**Last Updated**: 28 Dec 2025, 16:00 UTC  
**Maintainer**: george@upowerenergy.uk  
**Accounts**: smart.grd@gmail.com (infrastructure), upower@gmail.com (sheets)
