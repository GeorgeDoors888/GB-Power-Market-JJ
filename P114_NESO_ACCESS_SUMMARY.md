# P114 & NESO Data Access Summary
**Generated**: 28 December 2025
**Status**: Scripts Created - Keys/URLs Pending

---

## ✅ Completed Actions

### 1. P114 Scripting Key Investigation
**Status**: Old key found but expired

**Found**: `ju89x1a0fl` in `download_bmu_data.py`
- Tested with `curl` to P114 list endpoint
- Result: `Scripting Error 001: Scripting key provided does not resolve to a valid user`
- **Conclusion**: Key expired, needs regeneration from Portal

**Account Status**:
- ✅ P114 license GRANTED (Non-BSC Party access)
- ✅ Portal account active (george@upowerenergy.uk)
- ✅ Authorized for c0421, s0142, c0291, c0301 files

**To regenerate key**:
1. Login: https://www.elexonportal.co.uk/
2. Navigate: Account Settings → Scripting
3. Generate new key
4. Update `SCRIPTING_KEY` in `ingest_p114_settlement.py`

---

### 2. P114 Access Testing
**Method**: Portal HTTPS (recommended over FTP)

**Test commands**:
```bash
# List available c0421 files
curl "https://downloads.elexonportal.co.uk/p114/list?key=KEY&date=2025-12-27&filter=c0421"

# Download specific file
curl -O "https://downloads.elexonportal.co.uk/p114/download?key=KEY&filename=FILENAME"
```

**Status**: Commands tested with old key (failed as expected)
- Once new key obtained, these commands will work
- Expected response: JSON array of filenames

---

### 3. P114 Ingestion Script Created
**File**: `ingest_p114_settlement.py` (371 lines)

**Features**:
- ✅ Key validation at startup
- ✅ Date range processing
- ✅ List + download workflow
- ✅ c0421 CSV parsing (~370 columns)
- ✅ BigQuery auto-schema detection
- ✅ Partitioning by settlement_date
- ✅ Clustering by bm_unit_id
- ✅ Verification queries

**Target table**: `elexon_p114_settlement`
- Expected size: 10-20M rows, 20-30GB
- Partition: Daily by settlement_date
- Cluster: bm_unit_id for VLP filtering

**Usage** (after key configured):
```bash
python3 ingest_p114_settlement.py 2024-01-01 2024-12-31
```

**Purpose**: Reconcile BMRS revenue (£2.79M) vs actual settlement for VLPs

---

### 4. NESO Data Portal Mapping
**Status**: CKAN API unavailable

**API tests**:
```bash
# All returned empty/zero results:
curl "https://data.nationalgrideso.com/api/3/action/package_list"
curl "https://data.nationalgrideso.com/api/3/action/package_search?q=constraint"
curl "https://data.nationalgrideso.com/api/3/action/package_search?q=interconnector"
```

**Possible causes**:
- API maintenance/downtime
- CKAN version upgrade changed endpoints
- Authentication now required
- Domain migration

**Existing NESO tables** (already in BigQuery):
- `neso_dno_reference` - DNO details
- `neso_dno_boundaries` - Geographic boundaries
- `neso_gsp_groups` - Grid Supply Point groups
- `neso_gsp_boundaries` - GSP boundaries

**Workaround**: Manual web browser access
1. Visit: https://data.nationalgrideso.com/
2. Search for datasets
3. Download CSV/JSON manually
4. Upload to BigQuery with Python script

---

### 5. NESO Ingestion Scripts Created

#### Script 1: Constraints (`ingest_neso_constraints.py`)
**Status**: Already exists (301 lines)
- Scrapes GB transmission constraint data
- Multiple constraint types supported
- 6-hour refresh cadence
- Target: `uk_constraints.constraint_flows_da`

**Datasets**:
- Day-ahead constraint flows & limits
- 24-month ahead constraint limits
- CMIS (Constraint Management Intertrip)
- CMZ (Constraint Management Zones)
- Flexibility trades

#### Script 2: Interconnectors (`ingest_neso_interconnectors.py`)
**Status**: Created (271 lines)

**Features**:
- ✅ Search mode to find datasets
- ✅ Parse interconnector flows (MW)
- ✅ 8 interconnectors supported
- ✅ Flow direction (import/export)
- ✅ Capacity and utilization tracking

**Interconnectors tracked**:
| Name | Country | Capacity |
|------|---------|----------|
| IFA | France | 2000 MW |
| IFA2 | France | 1000 MW |
| ElecLink | France | 1000 MW |
| BritNed | Netherlands | 1000 MW |
| Nemo Link | Belgium | 1000 MW |
| Moyle | N. Ireland | 500 MW |
| EWIC | Ireland | 500 MW |
| NSL | Norway | 1400 MW |

**Usage**:
```bash
# Search for dataset
python3 ingest_neso_interconnectors.py search

# After updating resource ID
python3 ingest_neso_interconnectors.py ingest
```

**Target table**: `neso_interconnector_flows`
- Partition: Daily by timestamp
- Cluster: interconnector_name, flow_direction
- Expected: 384 rows/day (8 ICs × 48 periods)

---

## 📋 Documentation Created

### 1. NESO Data Access Guide (`NESO_DATA_ACCESS_GUIDE.md`)
**Content**:
- API status and troubleshooting
- Alternative access methods (web browser, direct URLs)
- Existing BigQuery tables inventory
- Priority datasets for VLP analysis
- Manual ingestion workflow
- Resource ID documentation template
- Contact information for NESO support

### 2. This Summary (`P114_NESO_ACCESS_SUMMARY.md`)
**Purpose**: Quick reference for all P114/NESO work

---

## 🎯 Next Steps (Actionable)

### Immediate (Today)
1. **Regenerate P114 key**:
   - Login to Elexon Portal
   - Generate new scripting key
   - Update `ingest_p114_settlement.py`
   - Test with: `python3 ingest_p114_settlement.py 2025-12-27 2025-12-27`

2. **Manual NESO exploration**:
   - Visit https://data.nationalgrideso.com/
   - Search for "constraint" and "interconnector"
   - Document dataset URLs
   - Note resource IDs

### Short-term (Next 7 days)
3. **Test P114 ingestion**:
   - Start with 1-day test (verify parsing)
   - Expand to 1-month test (Dec 2024)
   - Full backfill 2024-2025 if successful

4. **NESO dataset identification**:
   - Find constraints dataset URL
   - Find interconnector flows URL
   - Update resource IDs in scripts
   - Test ingestion with sample data

5. **VLP reconciliation**:
   - Compare BMRS revenue vs P114 settlement
   - Calculate variance for FBPGM002, FFSEN005
   - Document discrepancies

### Medium-term (Next 30 days)
6. **Automated refresh**:
   - Add P114 ingestion to cron (daily at 2am)
   - Add NESO constraints to cron (6-hourly)
   - Add NESO interconnectors to cron (hourly)

7. **Analysis enhancement**:
   - Correlate VLP revenue with constraint events
   - Analyze interconnector flow impact on prices
   - Create dashboard showing arbitrage opportunities

---

## 📊 Expected Data Volumes

| Dataset | Table | Rows | Size | Refresh |
|---------|-------|------|------|---------|
| P114 c0421 | elexon_p114_settlement | 10-20M | 20-30GB | Daily |
| NESO Constraints | neso_system_constraints | ~50k | 100MB | 6-hourly |
| NESO Interconnectors | neso_interconnector_flows | ~140k/year | 10MB/year | Hourly |

**Total additional storage**: ~30GB for 2-3 years

---

## 🔑 Key Contacts

- **Elexon Portal**: support@elexon.co.uk
- **NESO Data Team**: data@nationalgrideso.com
- **API Issues**: Check https://data.nationalgrideso.com/support

---

## ✅ Verification Checklist

P114 Setup:
- [x] Found old scripting key
- [x] Tested P114 endpoints (key expired as expected)
- [x] Created ingestion script with validation
- [x] Documented key regeneration process
- [ ] **TODO**: Regenerate key from Portal
- [ ] **TODO**: Test with 1-day ingestion
- [ ] **TODO**: Full 2024-2025 backfill

NESO Setup:
- [x] Tested CKAN API (unavailable)
- [x] Documented alternative access methods
- [x] Created constraints ingestion script (exists)
- [x] Created interconnectors ingestion script
- [x] Listed existing NESO tables
- [ ] **TODO**: Manual dataset URL identification
- [ ] **TODO**: Update resource IDs
- [ ] **TODO**: Test ingestion with sample data

---

**Last Updated**: 28 December 2025
**Next Action**: Regenerate P114 key + Manual NESO dataset search
