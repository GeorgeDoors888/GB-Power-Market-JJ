# Data Architecture Update - December 29, 2025

**Status**: Current as of Dec 29, 2025 23:59
**Major Changes**: P114 backfill complete, daily automation deployed, constraint map implemented

---

## 📊 Dataset Summary (Post-P114 Backfill)

### BigQuery Dataset: `inner-cinema-476211-u9.uk_energy_prod`

| Metric | Value | Previous (Dec 23) | Change |
|--------|-------|------------------|---------|
| **Total Tables** | 308 | 174+ | +134 tables |
| **Total Rows** | 1,378,618,733 | ~500M | +878M rows |
| **Total Size** | 470.45 GB | ~50-100 GB | +370-420 GB |
| **Location** | US | US | (unchanged) |

**Key Growth Drivers**:
- P114 Settlement Data: 342,646,594 rows added (Dec 28, 2025)
- BMRS Historical: 440,116,814 rows in `bmrs_bod`
- Automated Daily Downloads: P114 (2am) + NESO (3am)

---

## 🆕 New Automated Data Pipelines (Dec 28, 2025)

### 1. P114 Settlement Automation

**Script**: `auto_download_p114_daily.py`
**Schedule**: Daily at 2:00 AM (AlmaLinux cron)
**Function**: Downloads Elexon P114 settlement files (II, SF, R1 runs)

**Configuration**:
```bash
0 2 * * * cd /home/george/GB-Power-Market-JJ && /usr/bin/python3 auto_download_p114_daily.py >> logs/p114_daily.log 2>&1
```

**Features**:
- 3-day rolling window (current day - 2 days)
- Multi-run support (II = Initial, SF = Settlement Final, R1 = Reconciliation Run 1)
- 1-hour timeout protection
- Comprehensive logging to `/logs/p114_daily.log`

**Tables Updated**:
- `elexon_p114_s0142_bpi` - BM Unit settlement data (342.6M rows)
- Additional P114 report tables as configured

### 2. NESO Constraint Data Automation

**Script**: `auto_download_neso_daily.py`
**Schedule**: Daily at 3:00 AM (AlmaLinux cron)
**Function**: Downloads NESO constraint costs via CKAN API

**Configuration**:
```bash
0 3 * * * cd /home/george/GB-Power-Market-JJ && /usr/bin/python3 auto_download_neso_daily.py >> logs/neso_daily.log 2>&1
```

**Datasets Downloaded**:
1. `constraint-breakdown` → `neso_constraint_breakdown_YYYY_YYYY`
2. `mbss` → `neso_mbss`
3. `constraint-forecast` → `neso_constraint_forecast`
4. `modelled-costs` → `neso_modelled_costs`
5. `skip-rates` → `neso_skip_rates`

**Data Coverage**:
- Constraint breakdown: 2017-2018 through 2025-2026 (8.5 years, 2,983 days)
- Total constraint cost tracked: £10,644.7M (14 DNO regions)

### 3. Installation & Monitoring

**One-Command Installer**: `install_daily_download_crons.sh`
**Verification Script**: `check_automated_downloads.py`
**Documentation**: `AUTOMATED_DAILY_DOWNLOADS.md`, `DEPLOYMENT_SUMMARY.md`

---

## 🗺️ Geographic Constraint Mapping (New - Dec 29, 2025)

### Implementation

**Script**: `create_dno_constraint_map.py`
**Status**: ✅ Operational
**Purpose**: Visualize DNO constraint costs geographically

**Data Source**:
- BigQuery table: `constraint_costs_by_dno` (1,470 rows, 105 months)
- Reference table: `neso_dno_reference` (14 DNO regions)

**Output**: Google Sheets tab "Constraint Map Data"

**Key Metrics**:
- 14 DNO regions mapped
- Total constraint costs: £10,644.7M (2017-2025)
- Data period: April 2017 - December 2025 (105 months)
- Breakdown: Voltage, Thermal, Inertia costs

**Top 3 Costliest Regions**:
1. Electricity North West: £760.3M
2. National Grid Electricity Distribution: £760.3M (multiple regions)

**User Instructions**: See CONSTRAINT_MAP_ANALYSIS.md for Geo Chart setup

---

## 📋 Updated Table Inventory

### Major Tables (>10GB or >100M rows)

| Table | Rows | Size (GB) | Category | Purpose |
|-------|------|-----------|----------|---------|
| `bmrs_bod` | 440,116,814 | 207.0 | BMRS Historical | Bid-offer data |
| `elexon_p114_s0142_bpi` | 342,646,594 | 29.1 | P114 Settlement | Settlement outcomes |
| `bmrs_boalf` | 12,308,713 | 8.5 | BMRS Historical | Balancing acceptances |
| `bmrs_ebocf` | 7,861,671 | 1.4 | BMRS Historical | Energy change forecasts |
| `bmrs_boav` | 9,541,720 | 1.8 | BMRS Historical | Accepted volumes |
| `bmrs_fuelinst` | 5,706,845 | 2.2 | BMRS Historical | Fuel mix data |
| `bmrs_boalf_complete` | 3,347,652 | 0.5 | Derived/Mart | Acceptances WITH prices |
| `bmrs_costs` | 194,223 | 0.1 | BMRS Historical | Imbalance prices (SSP/SBP) |

### IRIS Real-Time Tables (Recent Data Only)

| Table | Rows | Purpose | Update Frequency |
|-------|------|---------|------------------|
| `bmrs_fuelinst_iris` | 350,820 | Real-time fuel mix | 5 minutes |
| `bmrs_indgen_iris` | 2,516,130 | Individual generation | 5 minutes |
| `bmrs_remit_unavailability` | 4,133 | Outage notifications | Real-time |

### Constraint & Network Data

| Table | Rows | Size (MB) | Coverage |
|-------|------|-----------|----------|
| `neso_constraint_breakdown_*` | 2,983 | 0.0 | 2017-2026 (yearly tables) |
| `constraint_costs_by_dno` | 1,470 | 0.2 | 14 DNOs, 105 months |
| `neso_dno_reference` | 14 | 0.0 | DNO metadata |
| `neso_dno_boundaries` | 14 | 1.4 | GeoJSON boundaries |
| `neso_gsp_boundaries` | 333 | 8.6 | GSP boundaries |

---

## 🔄 Data Pipeline Architecture

### Historical Batch Pipeline

**Frequency**: 15-minute batch (on-demand)
**Script**: `ingest_elexon_fixed.py`
**Tables**: 174+ BMRS tables
**Date Range**: 2020-01-01 onwards
**Source**: Elexon BMRS REST API

### Real-Time Streaming Pipeline (IRIS)

**Frequency**: 5-minute streaming
**Deployment**: AlmaLinux server (94.237.55.234)
**Scripts**:
- `iris-clients/python/client.py` (download)
- `iris_to_bigquery_unified.py` (upload)
**Tables**: `bmrs_*_iris` suffix
**Coverage**: Last 24-48 hours

### Daily Automation Pipeline (NEW)

**P114 Settlement** (2am):
- Downloads: II/SF/R1 settlement runs
- Window: 3-day rolling
- Table: `elexon_p114_s0142_bpi`

**NESO Constraints** (3am):
- Downloads: 5 datasets via CKAN API
- Tables: `neso_constraint_breakdown_*`, `neso_mbss`, etc.

### Query Pattern for Complete Timeline

```sql
-- UNION pattern for historical + real-time
WITH combined AS (
  SELECT CAST(settlementDate AS DATE) as date, ...
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
  WHERE settlementDate < '2025-10-30'  -- Adjust cutoff

  UNION ALL

  SELECT CAST(settlementDate AS DATE) as date, ...
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
  WHERE settlementDate >= '2025-10-30'
)
SELECT * FROM combined
ORDER BY date
```

---

## ⚠️ Known Data Issues (Updated)

### 1. bmrs_costs Duplicates (Pre-Backfill)

**Issue**: ~55k duplicate settlement periods in data prior to Oct 27, 2025
**Cause**: Historical backfill method
**Status**: **RESOLVED** - Oct 29+ data has zero duplicates (automated backfill)
**Workaround**: Use `GROUP BY` or `DISTINCT` for pre-Oct 29 data

```sql
-- Duplicate-safe query
SELECT
    DATE(settlementDate) as date,
    settlementPeriod,
    AVG(systemSellPrice) as price_sell,  -- AVG handles duplicates
    AVG(systemBuyPrice) as price_buy
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_costs`
GROUP BY date, settlementPeriod
```

### 2. bmrs_mid Missing Days

**Issue**: 24 days missing in 6-day blocks (Apr/Jul/Sep/Oct 2024)
**Cause**: Genuine API outages, data never published by Elexon
**Status**: ❌ NOT RECOVERABLE
**Pattern**: Apr 16-21, Jul 16-21, Sep 10-15, Oct 08-13

### 3. BOALF Missing Price Fields

**Issue**: Elexon BOALF API lacks `acceptancePrice` field
**Solution**: Use `bmrs_boalf_complete` (derived via BOD matching)
**Match Rate**: 85-95% (varies by month)
**Coverage**: 2022-2025, ~4.7M valid records (42.8% of total)

---

## 📊 Dashboard & Visualization Updates

### Google Sheets: Live Dashboard v2

**Sheet ID**: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`

**New Tabs**:
- **Test**: Copy of "Live Dashboard v2" for safe testing (Dec 29, 2025)
- **Constraint Map Data**: DNO constraint cost data for Geo Chart (Dec 29, 2025)
- **DATA**: Updated with current BigQuery stats (Dec 29, 2025)

**Update Scripts**:
- `update_data_tab_latest_stats.py` - Refresh DATA tab with current BigQuery metadata
- `update_live_metrics.py` - 5-minute auto-refresh (existing)
- `create_test_sheet_fast.py` - Duplicate sheets for testing
- `create_dno_constraint_map.py` - Generate constraint map data

**Auto-Refresh**:
- Frequency: Every 5 minutes (cron)
- Script: `realtime_dashboard_updater.py`
- Log: `logs/dashboard_updater.log`

---

## 🔧 Configuration Reference

### BigQuery Project

**Project ID**: `inner-cinema-476211-u9` (⚠️ NOT `jibber-jabber-knowledge`)
**Dataset**: `uk_energy_prod`
**Location**: `US` (⚠️ NOT `europe-west2`)
**Credentials**: `inner-cinema-credentials.json`

### Google Sheets

**Spreadsheet ID**: `1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA`
**API**: gspread + service account
**Credentials**: `inner-cinema-credentials.json`

### Server Deployment

**Production Server**: AlmaLinux 9.5 (94.237.55.234)
**IRIS Pipeline**: 24/7 streaming ingestion
**Cron Jobs**: 18 total (16 pre-existing + 2 new daily downloads)

---

## 📚 Documentation Files (Updated Dec 29, 2025)

### Core Architecture
- `docs/STOP_DATA_ARCHITECTURE_REFERENCE.md` - Quick reference (needs update)
- `DATA_ARCHITECTURE_VERIFIED_DEC17_2025.md` - Verified state Dec 17 (needs update)
- `DATA_ARCHITECTURE_UPDATE_DEC29_2025.md` - **THIS FILE** (current)

### Automation
- `AUTOMATED_DAILY_DOWNLOADS.md` - P114/NESO automation guide
- `DEPLOYMENT_SUMMARY.md` - Full deployment log
- `quick_reference_downloads.sh` - Command reference

### Constraint Mapping
- `CONSTRAINT_MAP_ANALYSIS.md` - Why postcodes.io approach failed
- `create_dno_constraint_map.py` - Working DNO-based implementation

### Dashboard
- `ENHANCED_BI_ANALYSIS_README.md` - Dashboard KPIs
- `STATISTICAL_ANALYSIS_GUIDE.md` - Analysis methods

---

## 🎯 Action Items for Future Updates

### Immediate (Within 1 Week)
1. ✅ Update DATA tab - **COMPLETE** (Dec 29)
2. ✅ Create test sheet - **COMPLETE** (Dec 29)
3. ✅ Implement constraint map - **COMPLETE** (Dec 29)
4. ⏳ Update `STOP_DATA_ARCHITECTURE_REFERENCE.md` with new stats
5. ⏳ Update `DATA_ARCHITECTURE_VERIFIED_DEC17_2025.md` or deprecate

### Short-Term (Within 1 Month)
1. Add P114 R2/R3/RF run support to automation
2. Implement constraint time-series analysis
3. Create trader KPI dashboard (see extensive notes in Untitled-1.py)
4. Integrate DNO map into main dashboard

### Medium-Term (1-3 Months)
1. Backfill missing bmrs_mid days (if Elexon republishes)
2. Improve BOALF-BOD match rate (currently 85-95%)
3. Add settlement reconciliation reports
4. Implement automated data quality checks

---

## 📞 Support & Maintenance

**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ
**Maintainer**: George Major (george@upowerenergy.uk)
**Server Access**: root@94.237.55.234 (AlmaLinux)

**Key Commands**:
```bash
# Check automated downloads
python3 check_automated_downloads.py

# Refresh dashboard
python3 update_analysis_bi_enhanced.py

# Update constraint map
python3 create_dno_constraint_map.py

# Check IRIS pipeline
ssh root@94.237.55.234 'ps aux | grep iris'

# View cron jobs
crontab -l
```

---

**Status**: ✅ Current as of December 29, 2025 23:59
**Next Review**: January 2026 or after major schema changes
