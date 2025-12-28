# Elexon & NESO Dataset Gap Analysis

**Date**: 27 December 2025
**Status**: 🚨 **CRITICAL GAPS IDENTIFIED** - We're ingesting <20% of available datasets

## Executive Summary

We have **174+ Elexon datasets** ingesting via `ingest_elexon_fixed.py`, but the comprehensive inventory shows **100+ critical datasets** we're **NOT** ingesting, particularly:

1. **Individual BM Unit Bid-Offer Data** (per-unit BOD) - Currently aggregated only
2. **Generation Unit Availability/Outages** (B1510/B1520) - ENTSO-E Transparency
3. **NESO Constraint Management** (constraint costs, flows, limits)
4. **Interconnector Flows** (per-interconnector detail)
5. **NESO Forecasts** (7-52 week demand, wind availability)
6. **Capacity Market & CfD Registers** (EMR datasets)
7. **Balancing Services Auctions** (FFR, STOR, Dynamic services)
8. **TNUoS Tariffs** (transmission charges)
9. **Settlement Data** (P114/SAA-I014 per-unit settlement)
10. **Market Domain Data** (MDD - master reference data)

---

## What We HAVE (Currently Ingesting)

### Elexon BMRS API (Historical Batch - 15min cron)
**Script**: `ingest_elexon_fixed.py`
**Coverage**: 2022-2025 (now backfilling 2016-2021)

| Dataset | Table | What It Is | Frequency | Status |
|---------|-------|------------|-----------|--------|
| **BOD** | `bmrs_bod` | Bid-Offer Data (407M rows, **PER-UNIT**) | Every 15min | ✅ **Has bmUnit column** |
| **BOALF** | `bmrs_boalf` | Balancing acceptances (40M rows) | Every 15min | ✅ Volumes, NO prices |
| **COSTS** | `bmrs_costs` | System prices (SSP/SBP) | Every 15min | ✅ Now backfilling 2016 |
| **DISBSAD** | `bmrs_disbsad` | Disaggregated BSAD | Every 15min | ✅ Partial |
| **NETBSAD** | `bmrs_netbsad` | Net BSAD | Every 15min | ✅ Partial |
| **FREQ** | `bmrs_freq` | System frequency | Every 15min | ✅ Good |
| **FUELINST** | `bmrs_fuelinst` | Fuel mix instant | Every 15min | ✅ Good |
| **FUELHH** | `bmrs_fuelhh` | Fuel mix half-hourly | Every 15min | ✅ Good |
| **MID** | `bmrs_mid` | Market Index Data | Every 15min | ✅ Good |
| **INDGEN** | `bmrs_indgen` | Individual generation | Every 15min | ✅ Good |
| **WINDFOR** | `bmrs_windfor` | Wind forecast | Every 15min | ✅ Good |
| **PN/QPN** | `bmrs_pn`, `bmrs_qpn` | Physical notifications | Every 15min | ✅ Good |
| **TEMP** | `bmrs_temp` | Temperature | Every 15min | ✅ Good |
| **~170 more** | Various | Other BMRS datasets | Every 15min | ✅ Partial |

### IRIS Real-Time (Last 24-48h)
**Script**: `iris_to_bigquery_unified.py` on AlmaLinux
**Coverage**: Last 48 hours only

| Dataset | Table | Status |
|---------|-------|--------|
| FUELINST | `bmrs_fuelinst_iris` | ✅ Real-time |
| FREQ | `bmrs_freq_iris` | ✅ Real-time |
| BOALF | `bmrs_boalf_iris` | ✅ Real-time |
| INDGEN | `bmrs_indgen_iris` | ✅ Real-time |
| 10+ more | `*_iris` tables | ✅ Real-time |

### Derived Tables (Internal)
| Table | What It Is | Status |
|-------|------------|--------|
| `bmrs_boalf_complete` | BOALF + BOD matched prices | ✅ 11M rows, 42.8% valid |
| `mart_bm_value_by_vlp_sp` | VLP revenue by SP | ✅ £2.79M (2024-2025) |
| `v_btm_bess_inputs` | Stacked revenue view | ✅ Recently fixed |

---

## What We DON'T HAVE (Critical Gaps)

### 1. **Individual BM Unit Bid-Offer Data** 🚨 **HIGH PRIORITY**

**Problem**: We have aggregated BOD (391M rows), but **NOT per-BM-unit bid-offer details**

**What's Missing**:
- Individual bid/offer price curves per BM Unit
- Full bid stack (not just accepted bids)
- Generator-level pricing behavior analysis
- Skip rate calculation (cheaper bids passed over)

**Elexon Source**:
- **Dataset**: BOD (B1770) - "Bid-Offer Level Data"
- **API**: `/bmrs/api/v1/balancing/bid-offer` or similar
- **Format**: JSON/XML per BM Unit per Settlement Period
- **Volume**: ~200k rows/day × 365 days × years = **billions of rows**

**Use Cases**:
- VLP revenue deep-dive (why was FBPGM002 accepted vs others?)
- Generator pricing strategy analysis
- Market manipulation detection
- Skip rate validation

**Implementation**:
```python
# New script: ingest_bm_unit_bod.py
# Fetch BOD per BM Unit, store in bmrs_bod_per_unit table
# Partition by settlementDate for efficient queries
```

---

### 2. **Generation Unit Availability/Outages** 🚨 **HIGH PRIORITY**

**Problem**: No generation unit outage data (planned/unplanned unavailability)

**What's Missing**:
- Generator outages (why was unit offline?)
- Available vs installed capacity
- Maintenance schedules
- Forced outage tracking

**Elexon Source** (ENTSO-E Transparency):
- **B1510**: Installed Generation Capacity Aggregated
- **B1520**: Installed Generation Capacity per Unit
- **B1530**: Actual Generation Output per Generation Unit
- **B1610**: Actual Generation Output per Production Type
- **B1620**: Day-Ahead Aggregated Generation
- **B1630**: Actual Aggregated Generation per Type

**API**: `/bmrs/api/v1/generation/availability` (check docs)

**Use Cases**:
- Capacity margin analysis
- Outage impact on prices
- System adequacy forecasting

---

### 3. **NESO Constraint Management** 🚨 **HIGH PRIORITY**

**Problem**: No transmission constraint data (congestion, redispatch costs)

**What's Missing**:
- Constraint forecast flows & limits
- 24-month ahead constraint cost forecast
- Thermal constraint costs (actual)
- Intertrip constraint info

**NESO Data Portal Source**:
- Dataset: "Day-Ahead Constraint Flows & Limits"
- Dataset: "24-Month Ahead Constraint Cost Forecast"
- Dataset: "Thermal Constraint Costs"
- **API**: NESO CKAN API (https://data.nationalgrideso.com/api/3/action/datastore_search)

**Use Cases**:
- Predict high-price events (constraint-driven)
- Regional price analysis
- Network congestion arbitrage

**Implementation**:
```python
# New script: ingest_neso_constraints.py (extend existing)
# Fetch from NESO Data Portal API
# Store in neso_constraint_costs, neso_constraint_flows tables
```

---

### 4. **Interconnector Flows (Per-Interconnector)** 🔶 **MEDIUM PRIORITY**

**Problem**: No detailed interconnector flow data

**What's Missing**:
- IFA, IFA2, BritNed, NemoLink, NSL, Viking flows
- Import/export volumes per hour
- Interconnector outages/capacity limits

**NESO Data Portal Source**:
- Datasets: "BritNed", "IFA", "IFA2", "NemoLink", "NSL", "Viking"
- **Format**: CSV per interconnector
- **API**: NESO CKAN API

**Use Cases**:
- Cross-border arbitrage analysis
- Import dependency tracking
- Price impact of interconnector flows

---

### 5. **NESO Long-Term Forecasts** 🔶 **MEDIUM PRIORITY**

**What's Missing**:
- 7-52 week demand forecasts
- Weekly wind availability forecasts
- 14-day ahead operational wind forecasts

**NESO Data Portal Source**:
- "7-day ahead demand forecast"
- "Long-term 2–52 weeks demand forecast"
- "Weekly Wind Availability"
- "14 Days Ahead Operational Metered Wind Forecasts"

**Use Cases**:
- Long-term capacity planning
- Renewable integration forecasting
- Maintenance scheduling optimization

---

### 6. **Capacity Market & CfD Registers** 🔷 **LOW PRIORITY (Static)**

**What's Missing**:
- Capacity Market Register (generators with CM agreements)
- Contract for Difference (CfD) allocation data
- New capacity coming online

**NESO Data Portal Source**:
- "Capacity Market Register" (XLS/CSV)
- "CfD contract datasets"
- Updated after each auction

**Use Cases**:
- Future capacity tracking
- Policy analysis
- Market entry/exit monitoring

---

### 7. **Balancing Services Auctions** 🔷 **LOW PRIORITY**

**What's Missing**:
- FFR (Firm Frequency Response) auction results
- STOR (Short-Term Operating Reserve) results
- Dynamic Containment/Moderation/Regulation
- Stability Pathfinder utilizations

**NESO Data Portal Source**:
- "Phase 2 FFR Auction Results"
- "STOR Day Ahead Auction Results"
- "Stability mid-term utilisation"

**Use Cases**:
- Ancillary service revenue tracking
- Frequency response market analysis
- Battery storage revenue optimization

---

### 8. **TNUoS Tariffs** 🔷 **LOW PRIORITY (Annual)**

**What's Missing**:
- Transmission Network Use of System charges
- Generator and supplier tariffs
- Transmission loss factors

**NESO Data Portal Source**:
- "TNUoS tariffs and revenue" (PDF/CSV)
- Updated annually

**Use Cases**:
- Transmission cost forecasting
- Generator location optimization

---

### 9. **Settlement Data (P114/SAA-I014)** 🚨 **HIGH PRIORITY (Restricted)**

**Problem**: No detailed settlement data at BM Unit level

**What's Missing**:
- Per-BM-unit settlement charges
- ~370 data items per unit per period
- Metered volumes, imbalance charges, losses
- Trading Unit breakdown

**Elexon Portal Source**:
- SAA-I014 Settlement Reports (CSV)
- **Restriction**: BSC Parties only (own data free)
- **P114 License**: Full dataset available to non-parties (fee)

**Use Cases**:
- Detailed imbalance analysis
- Settlement reconciliation
- Trading Unit performance

**Implementation**: Requires P114 license or BSC Party access

---

### 10. **Market Domain Data (MDD)** 🔶 **MEDIUM PRIORITY (Reference)**

**What's Missing**:
- Master reference data (Suppliers, DNOs, GSPs)
- Grid Supply Point identifiers
- LLF classes, profile classes
- Essential for interpreting other datasets

**Elexon Portal Source**:
- MDD releases (MDB/CSV, monthly updates)
- Publicly available (free portal account)

**Use Cases**:
- Data validation
- Reference lookups
- Market structure analysis

**Implementation**:
```python
# New script: ingest_mdd.py
# Download monthly MDD release
# Parse CSV, upload to BigQuery reference tables
```

---

## Priority Action Plan

### Phase 1: Critical Gaps (Q1 2025)
1. ✅ **Backfill 2016-2021 COSTS** (in progress)
2. 🚀 **Backfill 2016-2021 BOD** (billions of rows - plan carefully)
3. 🚀 **Backfill 2016-2021 MID, DISBSAD**
4. 🚀 **Ingest Per-BM-Unit BOD** (new table: `bmrs_bod_per_unit`)
5. 🚀 **Ingest Generation Outages** (B1510/B1520/B1530)

### Phase 2: High-Value Additions (Q2 2025)
6. **NESO Constraint Management** (extend `ingest_neso_constraints.py`)
7. **Interconnector Flows** (per-interconnector detail)
8. **Market Domain Data** (MDD reference tables)

### Phase 3: Forecasting & Services (Q3 2025)
9. **NESO Long-Term Forecasts** (7-52 weeks)
10. **Balancing Services Auctions** (FFR, STOR, DC/DM/DR)

### Phase 4: Settlement & Advanced (Q4 2025)
11. **P114 Settlement Data** (if license obtained)
12. **Capacity Market & CfD** (quarterly updates)
13. **TNUoS Tariffs** (annual updates)

---

## Technical Considerations

### Storage Requirements
- **Current**: ~50 GB (2022-2025, 174 tables)
- **After 2016-2021 backfill**: ~150 GB (+6 years historical)
- **With per-unit BOD**: ~500 GB (+billions of rows)
- **Full implementation**: ~1-2 TB (all datasets, full history)

### API Rate Limits
- **Elexon BMRS API**: No documented limit, but use 0.05s delay
- **NESO Data Portal API**: CKAN API, no strict limit
- **Recommendation**: 20-50 requests/second max

### Ingestion Architecture
```
Elexon BMRS API v1 (174+ datasets)
    ↓ ingest_elexon_fixed.py (every 15 min)
    ↓ Backfill scripts (2016-2021)
    ↓ BigQuery (inner-cinema-476211-u9.uk_energy_prod)
    ↓ Google Sheets Dashboard

NESO Data Portal (50+ datasets)
    ↓ ingest_neso_*.py (new scripts)
    ↓ CKAN API → BigQuery
    ↓ Separate dataset: uk_energy_prod.neso_*

IRIS Real-Time (Last 48h)
    ↓ iris_to_bigquery_unified.py
    ↓ BigQuery (*_iris tables)
```

---

## Immediate Next Steps (Today)

1. **Monitor 2016-2021 backfill** (bmrs_costs currently running)
2. **Create backfill scripts** for BOD, MID, DISBSAD (2016-2021)
3. **Design per-unit BOD schema** (partition strategy for billions of rows)
4. **Audit ingest_elexon_fixed.py** - verify which 174 datasets we're actually getting
5. **Map NESO datasets** - create ingestion plan for NESO Data Portal

---

## Questions to Answer

1. **BOD**: Are we getting per-unit BOD or just aggregated? (Check table schema)
2. **B1510/B1520**: Does `ingest_elexon_fixed.py` fetch ENTSO-E Transparency data?
3. **IRIS**: Can we expand IRIS to include BOD real-time? (currently only 10-15 datasets)
4. **P114**: Do we need settlement data? (Requires BSC Party or license)
5. **Storage**: Is 1-2 TB BigQuery storage acceptable? (Cost ~£20-40/month)

---

## Conclusion

We're ingesting a **solid foundation** (174 Elexon datasets), but missing **critical per-unit detail** and **NESO datasets**. The comprehensive inventory shows we need:

1. **Per-BM-Unit granularity** (not just aggregates)
2. **NESO Data Portal integration** (constraints, forecasts, services)
3. **Historical backfill** (2016-2021 for all tables, not just COSTS)
4. **Reference data** (MDD, capacity registers)

**Recommendation**: Start with **Phase 1** (per-unit BOD + outages + constraint management) for immediate VLP analysis improvements.

---

**Last Updated**: 27 Dec 2025 17:45 GMT
**Next Review**: After 2016-2021 backfill completes
