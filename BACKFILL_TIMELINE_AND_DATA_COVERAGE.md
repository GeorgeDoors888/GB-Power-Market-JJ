# P114 Backfill Timeline & Data Source Coverage Analysis

**Created**: 28 December 2025  
**Status**: P114 backfill in progress, 113.32M records ingested  

---

## Part 1: P114 Backfill Completion Timeline

### Current Status (28 Dec 2025, 12:30 UTC)

**Active Backfill**:
- Master PID: `2243569` (execute_full_p114_backfill.sh)
- Coordinator PID: `2266755` (2024-01-01 to 2024-12-31 R3)
- Worker PID: `2272015` (2024-03-25 to 2024-03-31 R3, 79.8% CPU)

**Progress**:
- **Current**: 113.32M records (399 days coverage)
- **Target**: ~584M records (1,096 days coverage)
- **Gap remaining**: 709 days (Oct 2022 - Sep 2024)

### Completion Estimate

**Processing Rate Analysis**:
```
Current coverage: 399 days
Current records: 113.32M records
Average: 113.32M ÷ 399 = ~284k records/day

Target: 1,096 days × 284k records/day = ~311M records
Actual target: 584M records (indicates ~532k records/day at full BM participation)
```

**Batch Processing Speed**:
- Current batch: 2024-03-25 to 2024-03-31 (7 days)
- Batch started: 28 Dec 2025, 12:23 UTC
- Typical batch duration: 15-45 minutes (depends on data density)

**Estimated Timeline**:

| Milestone | Date Range | Records to Add | Est. Completion |
|-----------|------------|----------------|-----------------|
| **Current** | Oct 2021 - Oct 2024 | 113.32M | ✅ DONE |
| **2024 R3 (remaining)** | Apr-Sep 2024 | ~95M | 3-5 Jan 2026 |
| **2023 RF/R3** | Jan-Dec 2023 | ~195M | 15-20 Jan 2026 |
| **2022 RF/R3** | Oct-Dec 2022 | ~49M | 25-28 Jan 2026 |
| **Gap filling complete** | All 1,096 days | ~471M additional | **~28 Jan 2026** |

**Key Factors Affecting Timeline**:
1. **Settlement run availability**: R3 runs available after 14 months, RF after 28 months
2. **API rate limits**: Elexon API throttling may slow batch processing
3. **Data density**: Later years have more BM Units (increased participation)
4. **Server load**: AlmaLinux server running other pipelines (IRIS, BMRS)
5. **Network stability**: BigQuery upload speeds

### When Will We Hit 584M Records?

**Best Case**: 25 January 2026 (continuous processing, no errors)  
**Realistic Case**: **28-31 January 2026** (accounting for batch delays, retries)  
**Worst Case**: 10 February 2026 (if significant API issues or server downtime)

**Confidence**: 85% we'll reach 584M by end of January 2026

---

## Part 2: Data Source Coverage Analysis

### Summary: Current vs Required Data

| Category | Total Sources | Already Have | Missing | Coverage % |
|----------|--------------|--------------|---------|------------|
| **Demand & Load** | 5 | 4 | 1 | 80% |
| **Generation & Fuel Mix** | 7 | 5 | 2 | 71% |
| **Balancing Mechanism** | 4 | 3 | 1 | 75% |
| **System Frequency & Stability** | 4 | 2 | 2 | 50% |
| **Interconnectors** | 1 | 0 | 1 | 0% |
| **Constraint Management** | 1 | 0 | 1 | 0% |
| **Imbalance & Pricing** | 5 | 4 | 1 | 80% |
| **Settlement Data** | 7 | 2 | 5 | 29% |
| **Balancing Services** | 3 | 1 | 2 | 33% |
| **Network Charges** | 2 | 0 | 2 | 0% |
| **Market Monitoring** | 3 | 0 | 3 | 0% |
| **Reference Data** | 4 | 1 | 3 | 25% |
| **TOTAL** | **46** | **22** | **24** | **48%** |

---

## Part 3: Detailed Data Source Inventory

### ✅ HAVE (22 Sources)

#### Demand & Load (4/5)
1. ✅ **Actual Total Load (B0610)** - `bmrs_b0610` (historical, real-time via IRIS)
2. ✅ **Day-Ahead Demand Forecast** - `bmrs_fordaydem` (incomplete, needs backfill)
3. ✅ **2-14 Days Ahead Forecasts** - `bmrs_fordaydem` (partial)
4. ✅ **Historic Demand Data** - `bmrs_sysdem` (via IRIS)

#### Generation & Fuel Mix (5/7)
5. ✅ **Half-Hourly Generation by Fuel Type** - `bmrs_fuelinst` + `bmrs_fuelinst_iris`
6. ✅ **Wind and Solar Forecast vs Outturn** - `bmrs_windfor` (partial coverage)
7. ✅ **Generation Capacity (Installed)** - `bmrs_b1410`, `bmrs_b1420`
8. ✅ **Generation Unit Availability** - `bmrs_b1510`, `bmrs_b1520` (outages)
9. ✅ **Individual Generation by Unit** - `bmrs_indgen_iris` (real-time)

#### Balancing Mechanism (3/4)
10. ✅ **Bid-Offer Data (BOD)** - `bmrs_bod` (439M records, 2020-2025)
11. ✅ **Balancing Acceptances (BOALF)** - `bmrs_boalf` (3.3M acceptances)
12. ✅ **Acceptance Prices** - `bmrs_boalf_complete` (11M), `boalf_with_prices` (4.7M validated)

#### System Frequency & Stability (2/4)
13. ✅ **Rolling System Frequency (FREQ)** - `bmrs_freq` (every 2 minutes)
14. ✅ **System Frequency Data** - `bmrs_freq` (same as above, historical archive)

#### Imbalance & Pricing (4/5)
15. ✅ **Imbalance Prices (SSP/SBP)** - `bmrs_costs` (duplicate-safe via AVG/GROUP BY)
16. ✅ **Market Index Data (MID)** - `bmrs_mid` (2018-2025 backfilled)
17. ✅ **BSAD (Disaggregated)** - `bmrs_disbsad` (volume-weighted settlement proxy)
18. ✅ **Net BSAD** - `bmrs_netbsad` (net adjustments)

#### Settlement Data (2/7)
19. ✅ **P114 Settlement Data** - `elexon_p114_s0142_bpi` (113.32M → 584M target)
20. ✅ **Market Index Data (Settlement)** - `bmrs_mid` (also used in settlement)

#### Balancing Services (1/3)
21. ✅ **Generation Unit Outages** - `bmrs_b1510`, `bmrs_b1520` (availability data)

#### Reference Data (1/4)
22. ✅ **BM Unit Reference** - Embedded in P114, BOD, BOALF (unit IDs, names)

---

### ❌ MISSING (24 Sources)

#### Demand & Load (1/5)
1. ❌ **Long-Term Demand Forecasts (7-52 weeks)** - NESO Data Portal
   - **Impact**: Cannot validate long-term adequacy models
   - **Workaround**: Use FORDAYDEM for 2-14 days, extrapolate trends

#### Generation & Fuel Mix (2/7)
2. ❌ **Historic Generation Mix** - NESO Data Portal
   - **Impact**: Missing percentage breakdowns by fuel type over time
   - **Workaround**: Calculate from `bmrs_fuelinst` (have MWh, can derive %)
3. ❌ **14 Days Ahead Wind Forecasts** - NESO Data Portal
   - **Impact**: Cannot validate medium-term wind forecast accuracy
   - **Workaround**: Use `bmrs_windfor` (day-ahead only)

#### Balancing Mechanism (1/4)
4. ❌ **Physical Notifications (PN/FPN)** - BMRS (not currently ingested)
   - **Impact**: Cannot detect FPN mismatches (Feature C in NGSEA detection)
   - **Workaround**: Use P114 settlement outcomes as proxy

#### System Frequency & Stability (2/4)
5. ❌ **System Inertia** - NESO Data Portal
   - **Impact**: Cannot analyze inertia-driven frequency stability
   - **Workaround**: Use frequency data to infer stability issues
6. ❌ **System Inertia Cost** - NESO Data Portal
   - **Impact**: Missing cost of procuring inertia services
   - **Workaround**: None (specific dataset required)

#### Interconnectors (1/1)
7. ❌ **Interconnector Flows and Capacity** - NESO Data Portal
   - **Impact**: Cannot analyze cross-border flows, missing major market component
   - **Priority**: HIGH (interconnectors = 5-15% of GB supply/demand)
   - **Datasets needed**: IFA, IFA2, BritNed, NemoLink, NSL, Viking, ElecLink

#### Constraint Management (1/1)
8. ❌ **NESO Constraint Cost Publications** - NESO Data Portal
   - **Impact**: Cannot validate NGSEA detections against official NESO reports
   - **Priority**: HIGH (documented in NESO_CONSTRAINT_COST_PUBLICATIONS.md)
   - **Datasets needed**:
     - Constraint Breakdown (monthly Emergency Instructions costs)
     - MBSS (day-by-day emergency services)
     - Annual Balancing Costs Report
     - 24-Month Constraint Cost Forecast
     - Modelled Constraint Costs
     - Skip Rate Methodology

#### Imbalance & Pricing (1/5)
9. ❌ **Aggregated Imbalance Volume (NIV)** - BMRS B1780
   - **Impact**: Cannot see system-wide long/short position
   - **Workaround**: Can calculate from P114 sum of value2 across all units

#### Settlement Data (5/7)
10. ❌ **Settlement Period Summary Data** - Elexon Open Settlement Data
    - **Impact**: Missing verification data for cash-out calculations
    - **Priority**: MEDIUM (have P114 unit-level, missing system-level)
11. ❌ **Trading Charges - Aggregate Party Day** - Elexon Open Settlement Data
    - **Impact**: Cannot see daily charges per BSC Party
    - **Priority**: LOW (commercial data, not essential for generation analysis)
12. ❌ **Trading Unit & System Period Data** - Elexon Open Settlement Data
    - **Impact**: Missing system-wide settlement totals
    - **Priority**: MEDIUM (useful for validation)
13. ❌ **Line Loss Factors (LLF)** - Elexon Portal
    - **Impact**: Cannot adjust for distribution losses
    - **Priority**: LOW (P114 already loss-adjusted)
14. ❌ **Transmission Loss Multipliers (TLM)** - Elexon Portal
    - **Impact**: Cannot allocate transmission losses
    - **Priority**: LOW (P114 includes losses)

#### Balancing Services (2/3)
15. ❌ **Balancing Services Auctions** - NESO Data Portal
    - **Impact**: Missing FFR, STOR, Dynamic Containment procurement data
    - **Priority**: MEDIUM (useful for reserve cost analysis)
16. ❌ **Capacity Market Registers** - NESO Data Portal
    - **Impact**: Cannot track capacity market contracts
    - **Priority**: MEDIUM (useful for future capacity planning)

#### Network Charges (2/2)
17. ❌ **TNUoS Tariffs** - NESO Data Portal
    - **Impact**: Missing transmission charge data
    - **Priority**: LOW (not essential for NGSEA analysis)
18. ❌ **Transmission Losses Data** - NESO Data Portal
    - **Impact**: Missing annual loss factors
    - **Priority**: LOW (P114 includes losses)

#### Market Monitoring (3/3)
19. ❌ **NESO Forward Trades** - NESO Data Portal
    - **Impact**: Missing out-of-market trades
    - **Priority**: LOW (BM data covers most balancing)
20. ❌ **Historic GTMA Trades** - NESO Data Portal
    - **Impact**: Missing historical forward trades
    - **Priority**: LOW (historical interest only)
21. ❌ **Skip Rates** - NESO Data Portal
    - **Impact**: Cannot analyze BM inefficiency (cheaper bids skipped)
    - **Priority**: HIGH (documented in NESO publications guide)

#### Reference Data (3/4)
22. ❌ **Market Domain Data (MDD)** - Elexon Portal
    - **Impact**: Missing master reference data (GSPs, DNOs, Suppliers)
    - **Priority**: MEDIUM (useful for DNO lookup, currently using BigQuery tables)
23. ❌ **Credit Cover & Default Notices** - Elexon Portal
    - **Impact**: Cannot track BSC Party credit issues
    - **Priority**: LOW (commercial/operational data)
24. ❌ **GIS Data (Network Boundaries)** - NESO Data Portal
    - **Impact**: Cannot map regional generation/demand
    - **Priority**: LOW (nice to have for visualization)

---

## Part 4: Priority Data Gaps to Fill

### Critical Priority (Block NGSEA Analysis)

1. **NESO Constraint Cost Publications** (8 datasets)
   - **Why**: Cross-validate NGSEA detections with official NESO reports
   - **Action**: Manual download from NESO Data Portal → ingest to BigQuery
   - **Timeline**: 1-2 days manual effort
   - **Documented**: NESO_CONSTRAINT_COST_PUBLICATIONS.md

2. **Interconnector Flows** (7 interconnectors)
   - **Why**: Major market component (5-15% of supply/demand)
   - **Action**: Automate NESO Data Portal API ingestion
   - **Timeline**: 2-3 days development
   - **Impact**: Complete market picture

3. **Physical Notifications (FPN)** - BMRS API
   - **Why**: Required for Feature C (NGSEA detection algorithm)
   - **Action**: Add FPN ingestion to BMRS pipeline
   - **Timeline**: 1 day development
   - **Impact**: Enables full statistical detection

### High Priority (Improve Analysis Quality)

4. **Skip Rates** - NESO Data Portal
   - **Why**: Validate NGSEA inefficiency claims
   - **Action**: Monthly download, ingest to `neso_skip_rates` table
   - **Timeline**: 0.5 days setup

5. **14-Day Wind Forecasts** - NESO Data Portal
   - **Why**: Improve medium-term wind analysis
   - **Action**: Automate API ingestion
   - **Timeline**: 1 day development

6. **System Inertia** - NESO Data Portal
   - **Why**: Frequency stability analysis
   - **Action**: API ingestion to `neso_inertia` table
   - **Timeline**: 0.5 days development

### Medium Priority (Nice to Have)

7. **Settlement Period Summary** - Elexon Open Settlement
   - **Why**: Validate P114 system-level totals
   - **Action**: Download CSV files, ingest monthly
   - **Timeline**: 1 day development

8. **Capacity Market Register** - NESO Data Portal
   - **Why**: Track future capacity pipeline
   - **Action**: Quarterly download, ingest to BigQuery
   - **Timeline**: 0.5 days setup

9. **Balancing Services Auctions** - NESO Data Portal
   - **Why**: Analyze reserve procurement costs
   - **Action**: Monthly download, ingest per service
   - **Timeline**: 1-2 days development

---

## Part 5: Data Sufficiency for Current Projects

### NGSEA Detection & Analysis: 75% Complete ✅

**Have**:
- ✅ P114 settlement data (113.32M → 584M target)
- ✅ BOALF acceptances (3.3M)
- ✅ BOD bid prices (439M)
- ✅ System frequency (bmrs_freq)
- ✅ Imbalance prices (bmrs_costs)

**Missing**:
- ❌ FPN data (Feature C placeholder)
- ❌ NESO constraint costs (Feature D proxy only)
- ❌ Official NGSEA event counts (for validation)

**Can We Proceed?** YES
- Statistical detection works with Features A & B (98% match with P114)
- Annex X completed (formal interpretation guide)
- Formula validated (98% post-event construction proven)
- **Next**: Ingest NESO publications for cross-validation

### VLP Battery Arbitrage: 95% Complete ✅

**Have**:
- ✅ P114 settlement (FBPGM002, FFSEN005)
- ✅ BOALF acceptances with prices
- ✅ Imbalance prices (bmrs_costs)
- ✅ Market Index prices (bmrs_mid)
- ✅ System frequency (bmrs_freq)

**Missing**:
- ❌ Interconnector flows (minor impact)

**Can We Proceed?** YES
- All core datasets available
- Revenue calculations working
- Dashboard ready (need to refresh)
- **Next**: Update dashboard with Oct 17-23 high-price analysis

### Grid Frequency Monitoring: 90% Complete ✅

**Have**:
- ✅ System frequency (bmrs_freq, 2-min resolution)
- ✅ Generation by fuel type (bmrs_fuelinst)
- ✅ Individual unit output (bmrs_indgen_iris)

**Missing**:
- ❌ System inertia (cannot quantify GVA·s)

**Can We Proceed?** YES
- Frequency data sufficient for stability analysis
- Can infer inertia issues from frequency deviations
- **Next**: Inertia ingestion would enhance but not block

---

## Part 6: Recommended Data Ingestion Roadmap

### Phase 1: Complete NGSEA Framework (1-2 weeks)

1. **Download NESO Constraint Costs** (1-2 days)
   - Constraint Breakdown (monthly CSV)
   - MBSS (daily emergency services)
   - Annual Report (yearly event counts)
   - Modelled Constraint Costs (historical)
   - Upload to `neso_constraint_breakdown`, `neso_mbss`

2. **Ingest FPN Data** (1 day)
   - Add `bmrs_pn` and `bmrs_fpn` ingestion
   - Backfill last 12 months
   - Enable Feature C in detect_ngsea_statistical.py

3. **Test Full Statistical Detection** (1 day)
   - Run with all 4 features (A, B, C, D)
   - Compare with NESO official event counts
   - Tune scoring thresholds

### Phase 2: Market Completeness (1-2 weeks)

4. **Ingest Interconnector Flows** (2-3 days)
   - IFA, IFA2, BritNed, NemoLink, NSL, Viking, ElecLink
   - Historical backfill (2020-2025)
   - Real-time pipeline (if available)

5. **Add Skip Rates** (0.5 days)
   - Monthly CSV download from NESO
   - Ingest to `neso_skip_rates`
   - Validate NGSEA inefficiency claims

6. **System Inertia Ingestion** (0.5 days)
   - API connection to NESO Data Portal
   - Historical + real-time
   - Table: `neso_system_inertia`

### Phase 3: Settlement Validation (1 week)

7. **Settlement Period Summary** (1 day)
   - Download Elexon Open Settlement Data
   - Parse CSV monthly files
   - Ingest to `elexon_settlement_period_summary`

8. **Trading Unit & System Period Data** (1 day)
   - Same source as #7
   - Cross-validate P114 system totals

9. **Balancing Services Auctions** (2 days)
   - FFR, STOR, Dynamic Containment/Moderation/Regulation
   - Historical procurement data
   - Monthly updates

### Phase 4: Reference Data (Optional, 2-3 days)

10. **Market Domain Data (MDD)** (1 day)
    - Download latest MDD release
    - Parse MDB/CSV to BigQuery
    - Table: `elexon_market_domain_data`

11. **GIS Network Boundaries** (1 day)
    - Download DNO license area shapefiles
    - Convert to GeoJSON
    - Enable regional analysis

---

## Part 7: Storage & Cost Implications

### Current BigQuery Storage

**P114 Data**:
- Current: 113.32M records × ~500 bytes/record = **~57 GB**
- Target: 584M records × 500 bytes = **~292 GB**
- Additional: 471M records = **~235 GB to add**

**All BMRS Tables** (estimated):
- bmrs_bod: 439M records × 300 bytes = 132 GB
- bmrs_boalf: 3.3M records × 400 bytes = 1.3 GB
- bmrs_fuelinst: ~50M records × 200 bytes = 10 GB
- Other tables: ~100 GB
- **Total current**: ~300 GB

**After Full Ingestion** (all missing datasets):
- P114 complete: 292 GB
- Interconnector flows (5 years, 7 units): 3 GB
- NESO publications: 5 GB
- FPN data (12 months): 20 GB
- Settlement summaries: 10 GB
- Reference data: 5 GB
- **Total projected**: ~635 GB

### BigQuery Costs (US region)

**Storage**: $0.02 per GB/month (active), $0.01 per GB/month (long-term)
- Current: 300 GB × $0.02 = **$6/month**
- Projected: 635 GB × $0.015 (mixed) = **~$10/month**

**Query Processing**: $6.25 per TB scanned
- Typical monthly queries: ~2 TB scanned = **$12.50/month**
- With partitioning/clustering: ~1 TB = **$6.25/month**

**Total Monthly Cost**:
- Current: ~$18/month
- Projected: ~$16-20/month (more data but better optimized)

**Within Free Tier?** YES
- BigQuery free tier: 1 TB queries/month, 10 GB storage/month free
- Additional costs: ~$10-15/month (very affordable)

---

## Part 8: Key Takeaways

### Timeline Summary

| Milestone | Date | Days from Now |
|-----------|------|---------------|
| **P114 backfill complete** | 28-31 Jan 2026 | 30-33 days |
| **584M records achieved** | ~31 Jan 2026 | 33 days |
| **NGSEA framework complete** | 10-15 Jan 2026 | 12-17 days |
| **Market data complete** | 20-25 Jan 2026 | 22-27 days |

### Data Coverage Summary

- **Have**: 22/46 sources (48%)
- **Critical gaps**: 3 (NESO publications, interconnectors, FPN)
- **Can proceed with NGSEA**: YES (75% complete)
- **Can proceed with VLP**: YES (95% complete)
- **Storage impact**: ~335 GB additional (~$4-5/month)
- **Cost**: ~$16-20/month total (well within budget)

### Confidence Levels

- **P114 backfill by end Jan 2026**: 85% confidence
- **NGSEA detection operational**: 90% confidence (Features A & B work)
- **Full statistical algorithm**: 70% confidence (needs FPN + NESO data)
- **Market analysis completeness**: 75% confidence (interconnectors needed)

### Immediate Actions

1. ✅ **Continue P114 backfill** (autonomous, 30 days remaining)
2. 🔄 **Download NESO Constraint Costs** (manual, 1-2 days)
3. 🔄 **Ingest FPN data** (development, 1 day)
4. 🔄 **Add Interconnector flows** (development, 2-3 days)
5. 📋 **Test full NGSEA algorithm** (after #2 & #3 complete)

---

*Analysis Completed: 28 December 2025, 12:35 UTC*  
*P114 Status: 113.32M / 584M records (19.4% complete)*  
*Data Coverage: 22/46 sources (47.8% complete)*  
*ETA to 584M: ~31 January 2026 (33 days)*  
*Cost Projection: $16-20/month (within budget)*
