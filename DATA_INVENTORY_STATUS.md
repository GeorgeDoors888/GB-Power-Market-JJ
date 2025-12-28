# GB Power Market - Comprehensive Data Inventory Status
**Generated:** 27 December 2025
**Project:** inner-cinema-476211-u9.uk_energy_prod
**Total Tables:** 287 (73 with data)

---

## Executive Summary

### ✅ What We HAVE

#### **Balancing Mechanism (BMRS) - Core Data** ✅
| Dataset | Table | Coverage | Rows | Per-Unit | Status |
|---------|-------|----------|------|----------|--------|
| BOD (Bid-Offer) | `bmrs_bod` | 2022-2025 | 407M | ✅ YES (bmUnit) | Complete |
| BOD (IRIS) | `bmrs_bod_iris` | Last 48h | 8M | ✅ YES | Real-time |
| BOALF (Acceptances) | `bmrs_boalf` | 2022-2025 | 12.3M | ✅ YES (bmUnit) | Complete |
| BOALF (Enhanced) | `bmrs_boalf_complete` | 2022-2025 | 3.3M | ✅ YES + Prices | 42.8% Valid |
| PN (Physical Notifications) | `bmrs_pn` | 2022-2025 | 173M | ✅ YES | Complete |
| QPN (Quiescent) | `bmrs_qpn` | 2022-2025 | 152M | ✅ YES | Complete |
| COSTS (Imbalance Prices) | `bmrs_costs` | **2016-2025** | 191k | System-level | ✅ Backfilled |
| MID (Market Index) | `bmrs_mid` | 2022-2025 | 197k | Market | Partial |
| DISBSAD (Settlement) | `bmrs_disbsad` | 2022-2025 | 512k | Volume-weighted | Partial |

#### **Generation & Demand** ✅
| Dataset | Table | Coverage | Rows | Status |
|---------|-------|----------|------|--------|
| FUELINST (Fuel Mix) | `bmrs_fuelinst` | 2020-2025 | 5.7M | Complete |
| INDGEN (Per-Unit Gen) | `bmrs_indgen` | 2022-2025 | 2.7M | Complete |
| INDDEM (Per-Unit Demand) | `bmrs_inddem` | 2022-2025 | 2.7M | Complete |
| FREQ (System Frequency) | `bmrs_freq` | 2022-2025 | 1.2M | Complete |

#### **Physical Positions (UOU)** ✅
| Dataset | Table | Coverage | Rows | Status |
|---------|-------|----------|------|--------|
| UOU2T3YW (3.5yr ahead) | `bmrs_uou2t3yw` | 2022-2025 | 127M | Complete |
| UOU2T14D (14d ahead) | `bmrs_uou2t14d` | 2022-2025 | 10.4M | Complete |

#### **NESO Reference Data** ✅
| Dataset | Table | Coverage | Rows | Purpose |
|---------|-------|----------|------|---------|
| DNO Reference | `neso_dno_reference` | Static | 14 | DUoS rates |
| DNO Boundaries | `neso_dno_boundaries` | Static | 14 | Geographic |
| GSP Boundaries | `neso_gsp_boundaries` | Static | 333 | Grid points |
| GSP Groups | `neso_gsp_groups` | Static | 14 | Regions |

#### **Generation Unit Outages** ⚠️
| Dataset | Table | Coverage | Rows | Status |
|---------|-------|----------|------|--------|
| REMIT Unavailability | `bmrs_remit_unavailability` | 2025 | 4,133 | IRIS only (last 48h) |

---

## ❌ What We DON'T HAVE (Critical Gaps)

### 🚨 **Priority 1: Settlement & Revenue Reconciliation**

#### **P114 Settlement Data** (MISSING)
- **Source:** Elexon Settlement Admin Agent (SAA)
- **Access:** ✅ GRANTED (scripting key available)
- **Data:** Per-unit settlement invoices (~370 columns)
  - `bmUnitId`, `settlementDate`, `meteredVolume`
  - `imbalanceCharge`, `transmissionLoss`, `bsuosCharge`
  - `rcrcAllocation`, `cashflowAmount`, `totalCharge`
- **Use Case:** Reconcile £2.79M VLP revenue (BMRS) vs actual settlement
- **Expected:** ~10-20M rows (2016-2025), ~20-30 GB
- **Impact:** 🔴 HIGH - Cannot validate BM revenue accuracy without this

#### **B1630 Contract Volume Allocation** (MISSING)
- **Source:** Elexon P114 c0421 report
- **Data:** Per-BM-unit contract vs non-contract volumes
- **Use Case:** VLP contract vs spot revenue split
- **Impact:** 🔶 MEDIUM - Affects revenue attribution

---

### 🚨 **Priority 2: NESO Data Portal (Constraints & Interconnectors)**

#### **Constraint Management** (MISSING)
- **Day-Ahead Constraint Flows & Limits**
  - Per-transmission-constraint forecast flows
  - Thermal limits, congestion indicators
  - Use case: Predict constraint-driven high prices

- **24-Month Ahead Constraint Cost Forecast**
  - Long-term constraint cost projections
  - Regional congestion trends
  - Use case: VLP siting strategy

- **Thermal Constraint Costs**
  - Actual historical constraint payments
  - Per-constraint cost breakdown
  - Use case: Correlate Oct 17-23 £80/MWh event with constraint costs

#### **Interconnector Flows** (MISSING)
- **Per-Interconnector Real-Time Flows**
  - IFA (2 GW), IFA2 (1 GW), BritNed (1 GW)
  - NemoLink (1 GW), NSL (1.4 GW), Viking (1.4 GW)
  - 5-minute resolution, actual vs scheduled
  - Use case: Cross-border arbitrage, import dependency tracking

#### **Long-Term Forecasts** (MISSING)
- **7-52 Week Demand Forecasts**
  - NESO long-term demand projections
  - Seasonal peaks, weather scenarios

- **7-52 Week Wind Forecasts**
  - Long-term wind generation outlook
  - Use case: Battery revenue seasonality modeling

---

### 🔶 **Priority 3: ENTSO-E Transparency (Outage Details)**

#### **B1510: Generation Unit Availability** (PARTIAL)
- **Current:** Only REMIT unavailability (4,133 rows, IRIS last 48h)
- **Missing:** Historical outage data (2016-2022)
- **Need:** Scheduled vs unplanned outages, per-unit capacity
- **Use case:** Correlate outages with high price events

#### **B1520: Aggregated Generation Availability** (MISSING)
- **Data:** Per-fuel-type total available capacity
- **Use case:** National capacity margins, scarcity pricing drivers

#### **B1530: Installed Capacity** (MISSING)
- **Data:** Per-unit nameplate capacity, technology type
- **Use case:** Unit size classification, market concentration analysis

---

### 🔷 **Priority 4: Market Depth & Liquidity**

#### **B1420: Day-Ahead Prices** (MISSING)
- **Source:** N2EX/EPEX auction results
- **Data:** Hourly DA prices, traded volumes
- **Use case:** Day-ahead vs balancing price spread

#### **B1430: Intraday Prices** (MISSING)
- **Source:** Continuous intraday trading
- **Data:** 15-minute prices, bid-offer spreads
- **Use case:** Intraday arbitrage opportunities

#### **B1770: Actual Load** (PARTIAL)
- **Current:** Have demand from FUELINST
- **Missing:** ENTSO-E official transmission system demand
- **Use case:** Cross-validate internal demand calculations

---

## 📊 Data Coverage Timeline

```
Dataset           2016 2017 2018 2019 2020 2021 2022 2023 2024 2025
─────────────────────────────────────────────────────────────────────
COSTS (Prices)     ✅   ✅   ✅   ✅   ✅   ✅   ✅   ✅   ✅   ✅
BOD (Bid-Offer)    ❌   ❌   ❌   ❌   🟡   🟡   ✅   ✅   ✅   ✅
MID (Index)        ❌   ❌   ❌   ❌   ❌   ❌   ✅   ✅   ✅   ✅
DISBSAD            ❌   ❌   ❌   ❌   ❌   ❌   ✅   ✅   ✅   ✅
FUELINST           ❌   ❌   ❌   ❌   ✅   ✅   ✅   ✅   ✅   ✅
P114 Settlement    ❌   ❌   ❌   ❌   ❌   ❌   ❌   ❌   ❌   ❌
NESO Constraints   ❌   ❌   ❌   ❌   ❌   ❌   ❌   ❌   ❌   ❌
Interconnectors    ❌   ❌   ❌   ❌   ❌   ❌   ❌   ❌   ❌   ❌

Legend: ✅ Complete | 🟡 Backfill needed | ❌ Missing
```

---

## 🔍 Critical Discovery: Per-Unit BOD Already Exists!

### ❌ FALSE ALARM: "Missing Per-Unit BOD"

**Assumption (WRONG):** bmrs_bod was aggregated market-level data, needed separate per-unit table

**Reality (CORRECT):**
- `bmrs_bod` table **ALREADY has `bmUnit` column** (column 12 of 20)
- 407M rows of **per-BM-unit bid-offer data** (2022-2025)
- 1,657 unique BM Units in Q4 2025
- Sample verified: FBPGM002 offers £129.08-£140.49/MWh on Oct 17 SP37

**Code Verification:**
```python
# derive_boalf_prices.py line 195 - USES bmUnit for JOIN
LEFT JOIN bod_data bod
  ON boalf.bmUnit = bod.bmUnit
  AND DATE(boalf.settlementDate) = DATE(bod.settlementDate)
  AND boalf.settlementPeriod = bod.settlementPeriod
```

**Conclusion:** £2.79M VLP revenue calculation **ALREADY uses per-unit pricing** ✅

---

## 🚀 Immediate Actions (Priority Order)

### ✅ COMPLETED
1. ✅ Fixed £0 BM revenue display (v_btm_bess_inputs view)
2. ✅ Extended VLP revenue to 2022-2025 (277 days, £2.79M)
3. ✅ Backfilled COSTS 2016-2021 (105,206 records)
4. ✅ Discovered BOD is per-unit (bmUnit column exists)
5. ✅ Verified VLP calculations use per-unit BOD (derive_boalf_prices.py)

### 🚀 NEXT (In Order)
6. **Backfill BOD 2020-2021** (NOT 2016-2019, data doesn't exist)
   - Update script: `years = [2020, 2021]`
   - Expected: ~7-10M additional rows
   - Runtime: ~1-2 hours

7. **Backfill MID 2016-2021** (Market Index prices)
   - Expected: ~105k rows (48 SP/day × 6 years)
   - Runtime: ~20 minutes

8. **Backfill DISBSAD 2016-2021** (Settlement proxy)
   - Expected: Variable, ~5 GB
   - Runtime: ~1 hour

9. **Ingest P114 Settlement** 🚨 HIGH PRIORITY
   - Verify scripting key access
   - Create `ingest_p114_c0421.py`
   - START WITH: 2024-2025 test period
   - Reconcile: £2.79M BMRS vs P114 actual

10. **Ingest NESO Constraints** 🚨 HIGH PRIORITY
    - Map NESO Data Portal resource IDs
    - Create `ingest_neso_constraints.py`
    - Use case: Predict constraint-driven high prices

11. **Ingest NESO Interconnectors** 🔶 MEDIUM
    - Per-interconnector flow data
    - Create `ingest_neso_interconnectors.py`
    - Use case: Cross-border arbitrage

12. **Update Documentation** 📝
    - Remove "missing per-unit BOD" from gap analyses
    - Update storage estimates (no +20GB for per-unit table)
    - Document BOD API limitation (2020+ only)

---

## 📈 Storage Impact

### Current
- Total dataset: ~370 GB
- Largest table: bmrs_bod (204 GB, 407M rows)

### After Backfills
- BOD 2020-2021: +5-7 GB (~7-10M rows)
- MID 2016-2021: +0.5 GB (~105k rows)
- DISBSAD 2016-2021: +5 GB (variable)
- **Subtotal:** ~380-390 GB

### After P114 & NESO
- P114 2016-2025: +20-30 GB (~10-20M rows)
- NESO Constraints: +10-15 GB (varies by dataset)
- NESO Interconnectors: +5-10 GB (5-min resolution)
- **Total estimated:** ~420-450 GB

---

## 🔬 Data Quality Notes

### BOD API Limitation Discovery
**Testing Results:**
```bash
# 2016: API returns empty (not 400 error!)
curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/BOD?from=2016-01-01T00:00:00Z&to=2016-01-01T01:00:00Z"
# {"data":[]}

# 2020: Data exists
curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/BOD?from=2020-01-01T00:00:00Z&to=2020-01-01T01:00:00Z" | jq '.data | length'
# 6502 records

# 2022: Data exists
curl "https://data.elexon.co.uk/bmrs/api/v1/datasets/BOD?from=2022-01-01T00:00:00Z&to=2022-01-01T01:00:00Z" | jq '.data | length'
# 7614 records
```

**Conclusion:** BOD only available from 2020 onwards (not 2016 as assumed)

### bmrs_costs Duplicates (2022-Oct 27)
- Pre-existing data has ~55k duplicate settlement periods
- Use `GROUP BY` or `DISTINCT` for queries covering 2022-Oct 27
- Post-Oct 29 data has zero duplicates (automated backfill)

### BOALF Price Matching Rate
- `bmrs_boalf_complete`: 11M acceptances
- Elexon B1610 filters: 42.8% pass as "Valid"
- BOD match rate: 85-95% (varies by month)
- Unmatched reasons: SO tests, low volume, timing mismatches

---

## 📚 References

**Configuration:**
- `PROJECT_CONFIGURATION.md` - All GCP/BigQuery settings
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Schema reference

**Analysis:**
- `ROOT_CAUSE_MISSING_DATASETS.md` - Why gaps occurred
- `ELEXON_NESO_DATASET_GAP_ANALYSIS.md` - Comprehensive inventory
- `COMPREHENSIVE_DATA_INGESTION_PLAN.md` - 4-phase roadmap

**Deployment:**
- `DEPLOYMENT_COMPLETE.md` - Live services
- `IRIS_DEPLOYMENT_GUIDE_ALMALINUX.md` - Real-time pipeline

---

**Last Updated:** 27 December 2025
**Next Review:** After P114 ingestion (Q1 2026)
