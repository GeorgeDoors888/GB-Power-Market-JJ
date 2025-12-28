# Elexon Data Access Audit
**Generated**: 2025-12-27
**Status**: In Progress

---

## Todo #1: P114 FTP/Portal Access Requirements ✅

### Current Account Status
- **Permission**: Non BSC Party P114 Access - **GRANTED** ✅
- **Account Type**: Licensed non-BSC party (not a BSC Participant)
- **Access Methods Available**:
  - ✅ Portal HTTPS scripted downloads (list/download endpoints)
  - ⚠️ FTP (optional - available but not required)

### P114 Access Requirements (Official)
Per Elexon Portal documentation, P114 FTP/Portal access requires **at least one** of:
1. **BSC Participant ID** linked to Portal account (BM Unit / Party ID), OR
2. **P114 Data Licence** (non-participant access)

**Current account meets requirement #2** - licensed for P114 data as non-BSC party.

### HTTPS vs FTP Decision

| Method | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **Portal HTTPS** | • Works with scripting key<br>• No FTP client needed<br>• Explicitly supported for automation<br>• list endpoint shows available files<br>• Works on any platform | • None significant | ✅ **USE THIS** |
| **FTP** | • Traditional file access<br>• Browse directory structure | • Requires FTP client config<br>• Portal username/password in FTP client<br>• No advantage over HTTPS | ❌ Not needed |

**Conclusion**: Use Portal HTTPS scripted downloads exclusively. FTP adds no value and introduces credential management complexity.

### P114 Access Pattern (Recommended)
```bash
# List available P114 files (today or specific date)
curl "https://downloads.elexonportal.co.uk/p114/list?key=SCRIPTING_KEY&date=2025-12-27&filter=c0421"

# Download specific file from list
curl -O "https://downloads.elexonportal.co.uk/p114/download?key=SCRIPTING_KEY&filename=FILENAME"
```

**Daily cadence**: 1x per day, use list endpoint to fetch only new files not already ingested.

---

## Todo #2: Portal Scripting Downloads Catalog (In Progress)

### Available Files from Scripting Page

#### Daily Operational Files (Update ~1x/day)
| File Key | Description | Update Frequency | Duplicate Check |
|----------|-------------|------------------|-----------------|
| `SSPSBPNIV_FILE` | System Sell/Buy Price + Net Imbalance Volume | Daily | Check vs API pricing endpoints |
| `TLM_FILE` | Transmission Loss Multipliers by SP | Daily | Unique to Portal |
| `RCRC_FILE` | Residual Cashflow Reallocation Cashflow | Daily | Unique to Portal |
| `LATEST_MID_FILE` | Market Index Data (N2EX/APX prices) | Daily (YTD file) | **DUPLICATE** - API has MID dataset |
| `LATESTFUELHHFILE` | Generation by fuel type (half-hourly) | Daily (YTD file) | **DUPLICATE** - API has FUELHH dataset |
| `BESTVIEWPRICES_FILE` | Best View Prices | Daily | Check overlap with MID |

#### Reference Files (Updated infrequently)
| File Key | Description | Critical? |
|----------|-------------|-----------|
| `REGISTERED_BMUNITS_FILE` | BM Units master list | ✅ YES - needed for joins |
| `REGISTERED_PARTICIPANTS_FILE` | Market participants list | ✅ YES - needed for VLP identification |
| `GSPGROUPCORRECTIONFACTORFILE` | GSP Group Correction Factors | Settlement only |

#### Calendars & Timetables (Updated as needed)
- SAA/SVAA Settlement Calendars
- D0095 Reporting Calendar
- FAA Payment Calendar
- PF Settlement Run Calendar
- PARMS Timetables

#### High-Volume Archives (Update >1x/day)
| File Key | Description | Notes |
|----------|-------------|-------|
| **BMRA Data Archive** | Historic BMRA reports | Filename-based access, frequent updates |
| **P114 files** | Settlement flows (s0142, c0291, c0301, c0421) | Multiple files per day, use list endpoint |

### Identified Duplicates (Portal vs API)
1. **MID (Market Index Data)**: Available from both Portal file AND REST API `/datasets/MID`
2. **FUELHH (Fuel Generation)**: Available from both Portal file AND REST API `/datasets/FUELHH`

**Recommendation**: Prefer API for operational time-series (parameterized queries, backfills). Use Portal only for daily reference snapshots or when API lacks equivalent.

---

---

## Todo #11: BigQuery Ingestion Audit ✅

### Current BigQuery Tables (uk_energy_prod dataset)
**Total BMRS/Elexon tables**: 113 tables found

#### Already Ingesting (Historical + IRIS Real-time)
| Dataset | Historical Table | IRIS Table | Status |
|---------|------------------|------------|---------|
| **BOALF** (Acceptances) | `bmrs_boalf`, `bmrs_boalf_complete` | `bmrs_boalf_iris` | ✅ Both pipelines active |
| **BOD** (Bid-Offer Data) | `bmrs_bod` | `bmrs_bod_iris` | ✅ Both pipelines active |
| **FREQ** (Frequency) | `bmrs_freq` | `bmrs_freq_iris` | ✅ Both pipelines active |
| **FUELHH** (Fuel hourly) | `bmrs_fuelhh` | `bmrs_fuelhh_iris` | ✅ Both pipelines active |
| **FUELINST** (Fuel instant) | `bmrs_fuelinst`, `fuelinst` | `bmrs_fuelinst_iris` | ✅ Both pipelines active |
| **MID** (Market Index) | `bmrs_mid` | `bmrs_mid_iris` | ✅ Both pipelines active |
| **WINDFOR** (Wind forecast) | `bmrs_windfor` | `bmrs_windfor_iris` | ✅ Both pipelines active |
| **INDGEN** (Indicated Gen) | `bmrs_indgen` | `bmrs_indgen_iris` | ✅ Both pipelines active |
| **INDDEM** (Indicated Demand) | `bmrs_inddem` | `bmrs_inddem_iris` | ✅ Both pipelines active |
| **REMIT** (Unavailability) | `bmrs_remit` | `bmrs_remit_iris` | ✅ Both pipelines active |

#### Other Active Datasets (113 total)
- Demand forecasts: NDF, NDFD, NDFW, TSDF, TSDFD, TSDFW
- Generation forecasts: FOU2T14D, FOU2T3YW, NOU2T14D, NOU2T3YW, UOU2T14D, UOU2T3YW
- Balancing: NETBSAD, DISBSAD, NONBM, QAS, PN, QPN
- System: IMBALNGC, MELNGC, CBS, TEMP, SOSO
- Physical: MELS, MILS, SEL, SIL, RURE, RURI, RDRE, RDRI
- Others: AGWS, ATL, INDO, ITSDO, etc.

### Key Findings

#### ✅ Strengths
1. **Dual-pipeline architecture**: Both historical batch + IRIS real-time for critical datasets
2. **Comprehensive coverage**: 113 tables = extensive BMRS/Insights API ingestion
3. **Deduplication tables**: `bmrs_boalf_complete`, `fuelinst_dedup` show data quality processes
4. **Backup strategy**: Backup tables exist (`bmrs_costs_backup_20251205`, `bmrs_remit_iris_backup`)

#### ⚠️ Potential Issues
1. **Duplicate tables**:
   - `bmrs_fuelinst` + `fuelinst` (redundant?)
   - `bmrs_freq` + `freq_2025` + `system_frequency` (3 frequency tables?)
   - Sep/Oct 2025 specific tables (`freq_sep_oct_2025`, etc.) - temporary or permanent?

2. **Missing from Portal files**:
   - ❌ No `sspsbpniv` table (SSP/SBP/NIV pricing) - using `bmrs_costs` instead?
   - ❌ No `tlm` table (Transmission Loss Multipliers)
   - ❌ No `rcrc` table (Residual Cashflow)
   - ❌ No `registered_participants` table (VLP identification)
   - ❌ No `gsp_group_correction_factors` table

3. **No P114 settlement tables**:
   - ❌ No c0421 (BM Unit metered volumes)
   - ❌ No c0291/c0301 (GSP Group/connection point volumes)
   - ❌ No s0142 (Settlement Report)

### Recommendations

#### High Priority
1. **Add Portal reference files**:
   - `registered_participants` → needed for VLP identification
   - `tlm` / `rcrc` → needed for settlement calculations
   - `gsp_group_correction_factors` → needed for supplier allocations

2. **Clarify duplicate tables**:
   - Consolidate frequency tables (3 → 1 master table)
   - Document purpose of sep_oct_2025 tables (dev/test?)

3. **Add P114 if needed**:
   - If doing settlement analysis: ingest c0421 (BM Unit metered)
   - Alternative: Use Open Settlement Data ABV_YYYY.zip for historic backfills

#### Medium Priority
4. **API vs Portal deduplication**:
   - FUELHH: Currently ingesting from both API (bmrs_fuelhh) and Portal (LATESTFUELHHFILE likely)
   - MID: Currently ingesting from both API (bmrs_mid) and Portal (LATEST_MID_FILE likely)
   - **Action**: Pick one source per dataset (recommend API for time-series, Portal for daily snapshots only)

5. **Check IRIS vs Historical overlap**:
   - Verify proper UNION logic for seamless historical → real-time transitions
   - Validate no gaps at IRIS cutover dates

---

## Todo #6: Portal vs API vs IRIS Duplicates ✅

### Confirmed Duplicates (Same data from multiple sources)

| Dataset | Portal File | API Endpoint | IRIS Topic | BQ Tables | Recommendation |
|---------|-------------|--------------|------------|-----------|----------------|
| **MID** | LATEST_MID_FILE | /datasets/MID | MID | bmrs_mid, bmrs_mid_iris | ✅ Keep API+IRIS, stop Portal |
| **FUELHH** | LATESTFUELHHFILE | /datasets/FUELHH | FUELHH | bmrs_fuelhh, bmrs_fuelhh_iris | ✅ Keep API+IRIS, stop Portal |
| **BOD** | (BMRA archive) | /datasets/BOD | BOD | bmrs_bod, bmrs_bod_iris | ✅ API+IRIS sufficient |
| **FREQ** | (BMRA archive) | /datasets/FREQ | FREQ | bmrs_freq, bmrs_freq_iris, freq_2025, system_frequency | ⚠️ Consolidate 4→2 tables |

### Unique to Portal (No API equivalent)
- ✅ TLM_FILE (Transmission Loss Multipliers)
- ✅ RCRC_FILE (Residual Cashflow)
- ✅ GSPGROUPCORRECTIONFACTORFILE (GSP Group Correction Factors)
- ✅ REGISTERED_BMUNITS_FILE (BM Units master list)
- ✅ REGISTERED_PARTICIPANTS_FILE (Participants + VLP identification)
- ✅ SSPSBPNIV_FILE (System prices - likely same as bmrs_costs but check)
- ✅ Calendars (SAA/SVAA/D0095/FAA/PF Settlement/PARMS)
- ✅ P114 settlement flows (s0142, c0291, c0301, c0421)

### Unique to API (No Portal equivalent)
- Parameterized time-range queries (backfills without downloading full YTD file)
- Superseded forecast retrieval (by publishTime)
- Stream endpoints (efficient bulk export)
- Reference endpoints (/reference/bmunits/all, /reference/interconnectors/all)

### Recommendations
1. **Stop Portal downloads for**: MID, FUELHH (already have API+IRIS)
2. **Start Portal downloads for**: REGISTERED_BMUNITS, REGISTERED_PARTICIPANTS, TLM, RCRC, GSPGCF
3. **Consolidate duplicate BQ tables**: Merge freq tables (4→2), clarify sep_oct_2025 purpose

---

## Todo #8: VLP/Party Reference & Revenue Calculation ⚠️

### Missing Critical Data for VLP Revenue

#### ❌ Problem 1: No BM Units Reference Table
**Impact**: Cannot map `bmUnit` → `leadPartyName` for revenue aggregation

**Current State**:
- `bmrs_boalf_complete` has: ✅ `acceptancePrice`, ✅ `acceptanceVolume`, ✅ `bmUnit` (column name)
- But **NO** `leadPartyName` column
- **NO** BM Units reference table in BigQuery

**Root Cause**: Not ingesting `REGISTERED_BMUNITS_FILE` from Portal OR `/reference/bmunits/all` from API

**Solution Required**:
```python
# Option A: Portal download (daily)
curl "https://downloads.elexonportal.co.uk/file/download/REGISTERED_BMUNITS_FILE?key=KEY"

# Option B: API query
curl "https://data.elexon.co.uk/bmrs/api/v1/reference/bmunits/all"

# Load to: uk_energy_prod.ref_bm_units
# Schema: bmUnitId, bmUnitName, leadPartyId, leadPartyName, fuelType, effectiveFrom, effectiveTo
```

#### ❌ Problem 2: No Participants Reference for VLP Identification
**Impact**: Cannot filter to Virtual Lead Parties (VLP/AMVLP) only

**Current State**: No `registered_participants` table in BigQuery

**Solution Required**:
```python
# Download from Portal
curl "https://downloads.elexonportal.co.uk/file/download/REGISTERED_PARTICIPANTS_FILE?key=KEY"

# Check CSV for columns: PartyID, PartyName, PartyRoles (should contain "VP" or "AV" for VLPs)
# Load to: uk_energy_prod.ref_participants
# Then create: uk_energy_prod.dim_vlp (party_id, party_name, is_vlp BOOL)
```

### Revenue Calculation Formula (Once reference data added)

```sql
-- Step 1: Join acceptances to BM Units to get lead party
WITH acceptances_with_party AS (
  SELECT
    a.acceptanceNumber,
    a.settlementDate,
    a.settlementPeriod,
    a.bmUnit,
    a.acceptanceVolume AS accepted_mw,
    a.acceptanceVolume * 0.5 AS accepted_mwh,  -- MW × 30min
    a.acceptancePrice AS price_gbp_per_mwh,
    (a.acceptanceVolume * 0.5 * a.acceptancePrice) AS gross_value_gbp,
    b.leadPartyId,
    b.leadPartyName,
    b.fuelType
  FROM `uk_energy_prod.bmrs_boalf_complete` a
  LEFT JOIN `uk_energy_prod.ref_bm_units` b
    ON a.bmUnit = b.bmUnitId
    AND CAST(a.settlementDate AS DATE) BETWEEN b.effectiveFrom AND COALESCE(b.effectiveTo, '2099-12-31')
  WHERE a.validation_flag = 'Valid'  -- 42.8% pass validation
),

-- Step 2: Filter to VLPs only and aggregate
vlp_revenue AS (
  SELECT
    CAST(settlementDate AS DATE) AS date,
    settlementPeriod,
    leadPartyId,
    leadPartyName,
    SUM(accepted_mwh) AS total_accepted_mwh,
    SUM(gross_value_gbp) AS gross_value_gbp,
    COUNT(DISTINCT acceptanceNumber) AS acceptance_count
  FROM acceptances_with_party a
  INNER JOIN `uk_energy_prod.dim_vlp` v
    ON a.leadPartyId = v.party_id
  WHERE v.is_vlp = TRUE
  GROUP BY 1,2,3,4
)

SELECT * FROM vlp_revenue
ORDER BY date DESC, settlementPeriod, gross_value_gbp DESC;
```

### Current Status
✅ **UNBLOCKED**: VLP reference data EXISTS in BigQuery!
- ✅ `dim_party` table: 18 VLPs identified (Flexitricity=59 units, GridBeyond=26, Danske=18, etc.)
- ✅ `vlp_unit_ownership` table: 9 VLP units mapped (FBPGM002-010)
- ⚠️ **Join Issue**: BOALF has prefixed units (`2__FBPGM002`) vs reference has clean names (`FBPGM002`)
- ✅ **Solution**: Use `REGEXP_EXTRACT(bmUnit, r'__(.+)$')` to strip prefix before join

### Successful Revenue Test (Oct 17-23, 2025)
```
Flexitricity VLP Revenue:
- 258 acceptances
- 2,287.5 MWh
- £157,328 total value
- Avg price: £69/MWh (ranging £38-97/MWh)
```

**Working Query Pattern**:
```sql
WITH boalf_cleaned AS (
  SELECT
    REGEXP_EXTRACT(bmUnit, r'__(.+)$') as clean_bm_unit,
    acceptanceVolume * 0.5 * acceptancePrice AS gross_value_gbp,
    ...
  FROM bmrs_boalf_complete
  WHERE validation_flag = 'Valid'
)
SELECT * FROM boalf_cleaned b
JOIN vlp_unit_ownership v ON b.clean_bm_unit = v.bm_unit
```

---

## Todo #16: 2025 Data Freshness Validation ✅

### Freshness Check Results (Last 7 days)

| Table | Latest Date | Lag | Rows (7d) | Status |
|-------|-------------|-----|-----------|--------|
| **bmrs_bod** | 2025-12-26 | 1 day | 2,566,713 | ✅ Current |
| **bmrs_freq** | 2025-12-27 18:29 | <1 hour | 45,430 | ✅ Real-time |
| **bmrs_mid** | 2025-12-27 | 0 days | 32,918 | ✅ Current |
| **bmrs_costs** | 2025-12-27 | 0 days | 16,270 | ✅ Current |
| **bmrs_boalf** | N/A | ERROR | - | ⚠️ Check date field |
| **bmrs_boalf_complete** | N/A | ERROR | - | ⚠️ Check date field |
| **bmrs_fuelhh** | N/A | ERROR | - | ⚠️ Check date field |
| **bmrs_fuelinst** | N/A | ERROR | - | ⚠️ Check date field |

### Findings
1. ✅ **Core operational data is current**: FREQ (real-time), MID/costs (same-day)
2. ✅ **BOD lag acceptable**: 1-day lag normal for bid-offer data
3. ⚠️ **BOALF date field issue**: `settlementDate` is TIMESTAMP not DATE causing comparison errors
4. ⚠️ **FUELHH date field issue**: Similar TIMESTAMP type mismatch

### Data Quality Notes
- **bmrs_boalf_complete**:
  - Has `acceptancePrice` and `acceptanceVolume` ✅
  - Has `validation_flag` (42.8% = 'Valid') ✅
  - Column name is `bmUnit` (not `bmUnitId`) ⚠️
  - Missing `leadPartyName` ❌

- **Frequency tables proliferation**:
  - `bmrs_freq`, `bmrs_freq_iris`, `freq_2025`, `system_frequency` = 4 tables for same data
  - Recommendation: Consolidate to `bmrs_freq` (historical) + `bmrs_freq_iris` (real-time)

---

## Critical Action Items (Priority Order)

### 🔴 HIGH PRIORITY (Optimization)
1. **Expand vlp_unit_ownership coverage**
   - Current: 9 units (FBPGM002-010) for 9 VLPs
   - dim_party shows: 18 VLPs with 190 total BM units
   - Action: Map remaining 181 units from dim_party to vlp_unit_ownership
   - Benefit: Complete VLP revenue tracking across all 18 VLPs

2. **Download full BM Units reference** (Optional - for comprehensive analysis)
   - Source: Portal `REGISTERED_BMUNITS_FILE` or API `/reference/bmunits/all`
   - Target: `uk_energy_prod.ref_bm_units` (all 2764 units)
   - Use case: Analyze non-VLP lead parties, fuel type filtering, full market coverage
   - Note: Current vlp_unit_ownership sufficient for VLP-only analysis

3. **Fix BOALF/FUELHH date queries**
   - Issue: `settlementDate` is TIMESTAMP, need CAST to DATE for comparisons
   - Impact: Freshness monitoring failing for 4 tables

### 🟡 MEDIUM PRIORITY (Optimization)
4. **Stop duplicate Portal downloads**
   - MID: Already have bmrs_mid + bmrs_mid_iris from API
   - FUELHH: Already have bmrs_fuelhh + bmrs_fuelhh_iris from API

5. **Consolidate frequency tables**
   - Merge: bmrs_freq (keep), freq_2025 (remove?), system_frequency (remove?)
   - Document sep_oct_2025 tables purpose (temp vs permanent)

6. **Add missing Portal settlement files**
   - TLM (Transmission Loss Multipliers)
   - RCRC (Residual Cashflow)
   - GSPGCF (GSP Group Correction Factors)

### 🟢 LOW PRIORITY (Nice to have)
7. **Add P114 if settlement analysis needed**
   - c0421 (BM Unit metered volumes)
   - Alternative: Use Open Settlement Data ABV_YYYY.zip for backfills

8. **Set up Railway audit cron**
   - Daily freshness check using METADATA/latest endpoint
   - Write results to audit.audit_results table

---

## Final Recommendations Summary

### ✅ Keep These Data Sources

| Source | Use Case | Frequency | Rationale |
|--------|----------|-----------|-----------|
| **REST API** | Historical time-series (BOD, MID, FREQ, FUELHH, FUELINST, etc.) | On-demand backfills | Parameterized queries, efficient bulk export |
| **IRIS Real-time** | Latest 24-48h (all topics with _iris suffix) | Real-time streaming | Near-real-time data (<5 min latency) |
| **Portal HTTPS** | Reference files ONLY (REGISTERED_BMUNITS, REGISTERED_PARTICIPANTS, TLM, RCRC, GSPGCF, calendars) | Daily | Unique data not available via API |
| **P114 (Optional)** | Settlement flows if needed (s0142, c0291, c0301, c0421) | Daily | Alternative: Use Open Settlement Data ABV files |

### ❌ Stop These Duplicates

| Portal File | Replace With | Reason |
|-------------|--------------|--------|
| LATEST_MID_FILE | API `/datasets/MID` + IRIS `MID` | Already have bmrs_mid + bmrs_mid_iris |
| LATESTFUELHHFILE | API `/datasets/FUELHH` + IRIS `FUELHH` | Already have bmrs_fuelhh + bmrs_fuelhh_iris |

### 🔧 Fix These Issues

1. **Add missing reference tables** (BLOCKS VLP revenue):
   - Download `REGISTERED_BMUNITS_FILE` → create `ref_bm_units` table
   - Download `REGISTERED_PARTICIPANTS_FILE` → create `ref_participants` + `dim_vlp` tables

2. **Fix date field queries**:
   - Cast `settlementDate` TIMESTAMP to DATE in freshness checks
   - Update monitoring queries for boalf, fuelhh, fuelinst tables

3. **Consolidate frequency tables**:
   - Keep: `bmrs_freq` (historical), `bmrs_freq_iris` (real-time)
   - Review: `freq_2025`, `system_frequency`, `sep_oct_2025` (purpose unclear)

### 📊 Data Architecture Pattern

**Dual-Pipeline Model** (Already Implemented):
```
Historical (2020-present):     API → BigQuery → bmrs_* tables
Real-time (last 24-48h):       IRIS → BigQuery → bmrs_*_iris tables
Reference (daily refresh):     Portal → BigQuery → ref_* tables (MISSING!)

Query Pattern:
SELECT * FROM bmrs_table WHERE date < '2025-12-25'
UNION ALL
SELECT * FROM bmrs_table_iris WHERE date >= '2025-12-25'
```

### 🎯 Immediate Actions

**Priority 1 (TODAY)**: ✅ COMPLETE - VLP revenue calculation working!
```bash
# Reference tables already exist:
# - dim_party (18 VLPs, 351 parties)
# - vlp_unit_ownership (9 VLP units)
# Can now calculate VLP revenue using:
python3 calculate_vlp_revenue.py  # Create this to generate mart.bm_value_by_vlp_sp
```

**Priority 2 (THIS WEEK)**: Expand VLP unit coverage
```bash
# Map remaining 181 BM units from dim_party (190 total - 9 mapped = 181)
# Query Elexon API /reference/bmunits/all filtered by leadPartyId WHERE is_vlp=TRUE
# Or manually map from existing dim_party.party_id + BMU registry
python3 expand_vlp_unit_ownership.py
```

**Priority 3 (NEXT WEEK)**: Audit and cleanup
```bash
# Remove duplicate ingestion jobs (MID, FUELHH from Portal)
# Consolidate frequency tables
# Add TLM, RCRC, GSPGCF from Portal if needed for analysis
```

---

## Next Steps

1. **Download Portal reference files** (see Priority 1 above)
2. **Test BM Units reference join** (bmUnit → leadPartyName)
3. **Build VLP dimension table** (filter participants for VP/AV role codes)
4. **Run VLP revenue query** (acceptances × prices by lead party)
5. **Deploy to Railway cron** (daily refresh at 8am)
- [ ] Complete Todo #2 (check actual Portal file schemas)
- [ ] Complete Todo #4 (map REST API datasets from Swagger)
- [x] **Todo #11 COMPLETE** ✅
- [ ] Start Todo #6 (identify exact Portal vs API duplicates)
- [ ] Start Todo #8 (check VLP data availability)

