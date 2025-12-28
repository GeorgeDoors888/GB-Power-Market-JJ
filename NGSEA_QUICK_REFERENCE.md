# NGSEA Quick Reference Card

**Last Updated**: 28 December 2025  
**Source**: GAS_EMERGENCY_CURTAILMENT_NGSEA_GUIDE.md (882 lines)

---

## The Three Settlement Concepts (DON'T CONFUSE!)

### 1. Pay-as-Bid Acceptances
- **What**: NESO accepts bid/offer → Section T Trading Charges
- **Where**: BOALF (operational), P114 (settled)
- **Price**: Bid/offer price from BOD
- **Formula**: `delta_mw × duration_hours × bid_price`
- **Settlement**: Section T (SAA calculates Trading Charges)

### 2. Imbalance Settlement
- **What**: Cash-out for net energy deviation
- **Where**: bmrs_costs (SBP/SSP), P114 (applied to imbalance)
- **Price**: System-wide marginal price (SBP/SSP)
- **Formula**: `imbalance_mwh × cash_out_price`
- **Settlement**: SEPARATE from acceptances!

### 3. NGSEA (P448 Construct)
- **What**: Post-event CONSTRUCTED acceptances for gas LSI
- **Where**: P114 (settlement artefact), may not appear in operational BOALF
- **Process**: 
  1. Gas emergency → LSI issued
  2. ESO constructs acceptance data after event
  3. Committee reviews → can change FPN/Bid Prices/Acceptance Data
- **Key Rule**: "A Network Gas Supply Emergency Acceptance will always be a Bid" *(BSCP18)*

---

## Level 1 vs Level 2 Cashflow

| Aspect | Level 1 (BOALF+BOD) | Level 2 (P114/SAA) |
|--------|---------------------|---------------------|
| **Purpose** | Operational estimate | Settlement outcome |
| **Data Sources** | BOALF + BOD | P114/S0142 |
| **Formula** | delta_mw × duration × bid_price | value2 × system_price × multiplier |
| **Accuracy** | Indicative (NOT guaranteed) | Authoritative |
| **Use Case** | "What did NESO accept?" | "What was settled?" |
| **Match?** | NO - expect differences | YES - official settlement |

**Why differences?**
- Delivery/non-delivery adjustments (Section T)
- NGSEA post-event construction/committee changes (P448, BSCP18)
- Settlement run corrections (II → R3 → RF)

---

## BOALF/BOD Join Keys (BigQuery)

```sql
FROM bmrs_boalf boalf
LEFT JOIN bmrs_bod bod
  ON boalf.bmUnitId = bod.bmUnitId
  AND boalf.settlementDate = bod.settlementDate
  AND boalf.settlementPeriod = bod.settlementPeriod
WHERE boalf.acceptanceType = 'BID'  -- For negative bids
  AND bod.bid IS NOT NULL
```

**Critical Fields**:
- BOALF: `bmUnitId`, `acceptanceNumber`, `acceptanceType`, `levelFrom`, `levelTo`, `timeFrom`, `timeTo`, `soFlag`
- BOD: `bmUnitId`, `pairId`, `bid`, `offer`
- P114: `bm_unit_id`, `settlement_date`, `value2`, `system_price`, `multiplier`, `settlement_run`

---

## NGSEA Detection Filters

```sql
-- Detect potential NGSEA events
WHERE acceptanceType = 'BID'        -- Always bids per BSCP18
  AND levelTo < levelFrom           -- Turn-down signature
  AND soFlag = TRUE                 -- SO-flagged/constructed
  AND system_price > 80             -- High price = gas stress
  AND bmUnitId LIKE 'T_%'           -- Gas CCGTs
  AND ABS(levelTo - levelFrom) > 50 -- Material reduction (>50 MW)
```

**Statistical Scoring** (Todo 3):
- A: Turn-down signature (2 points)
- B: No BOALF or soFlag=TRUE (2 points)
- C: FPN mismatch/correction (1 point)
- D: Constraint cost spike (1 point)
- **Flag if score ≥5**

---

## What P114 CAN/CANNOT Evidence

### ✅ CAN Evidence
1. Settlement outcomes (Section T Trading Charges)
2. Constructed acceptances entered per P448
3. Committee-driven changes to settlement inputs
4. Settlement run progression (II → R3 → RF)
5. Negative revenue = generator paid

### ❌ CANNOT Evidence
1. Real-world commercial arrangements (gas contracts)
2. Causal operational trigger (without NGSEA markers)
3. Acceptance prices (shows system_price, not bid_price)
4. Committee decision rationale (need minutes/change requests)

**Key Insight**: "P114 records are settlement artefacts, NOT gas commercial contracts"

---

## Negative Bid Payment Example

**Generator**: T_KEAD-2 (gas CCGT)  
**Bid**: £-50/MWh to reduce 100 MW  
**Interpretation**: "Pay me £50/MWh and I'll turn down 100 MW"

**During NGSEA**:
- Gas emergency declared
- LSI issued to generator
- ESO constructs acceptance post-event
- Payment: `100 MW × 0.5 hours × £50/MWh = £2,500`

**In P114**:
- `value2 = -50 MWh` (negative energy)
- `system_price = £95/MWh` (high imbalance price)
- `multiplier = 0.5` (half-hour period)
- `revenue = -50 × 95 × 0.5 = -£2,375` (negative = payment TO generator)

**Note**: Level 1 (£2,500) ≠ Level 2 (£2,375) due to system_price vs bid_price difference!

---

## Data Availability (As of 28 Dec 2025)

**P114 (elexon_p114_s0142_bpi)**:
- Records: **113.32M** (growing rapidly)
- Days: **399 days** (Oct 2021 - Oct 2024)
- Coverage: **36%** (399/1108 calendar days)
- Gap: **709 days** (Oct 15, 2022 → Sep 24, 2024) - **BEING FILLED**
- Status: **Backfill active** (currently processing 2024 R3 runs)
- Expected final: ~1,096 days (2022-2025), ~584M records

**BOALF (bmrs_boalf)**:
- Records: **3.3M acceptances**
- Coverage: More complete for recent periods
- SO-Flag available for constructed acceptances

**BOD (bmrs_bod)**:
- Records: **391M+ rows**
- Price ladder data (may have multiple pairs per unit/period)

---

## Common Pitfalls

### ❌ WRONG: "NGSEA is real-time BOALF"
✅ **CORRECT**: NGSEA = post-event constructed acceptances (P448)

### ❌ WRONG: "Use system_price for acceptance cashflow"
✅ **CORRECT**: system_price = imbalance, use bid_price from BOD for acceptance cashflow

### ❌ WRONG: "Level 1 should match P114"
✅ **CORRECT**: Level 1 (operational) ≠ Level 2 (settled) - expect differences

### ❌ WRONG: "P114 shows commercial deals"
✅ **CORRECT**: P114 shows settlement artefacts, NOT underlying contracts

### ❌ WRONG: "P114 has only 219 days"
✅ **CORRECT**: 399 days currently, growing to ~1,096 (backfill active)

---

## Quick Analysis Workflow

### For Operational Understanding:
1. Query BOALF for acceptances (soFlag=TRUE for NGSEA)
2. Join to BOD for bid prices
3. Calculate Level 1 indicative cashflow
4. Identify curtailment events (levelTo < levelFrom)

### For Settlement Verification:
1. Query P114 for settlement outcomes (RF run preferred)
2. Filter negative value2 (generator paid)
3. Calculate Level 2 settled cashflow
4. Check settlement_run progression (II → R3 → RF)

### For NGSEA Detection:
1. Combine BOALF (soFlag=TRUE) + P114 (negative energy)
2. Filter high system_price (>£80/MWh)
3. Check gas units (T_* prefix)
4. Correlate with NESO constraint cost data
5. Score using statistical algorithm (Todo 3)

---

## Files & Scripts

**Documentation**:
- `GAS_EMERGENCY_CURTAILMENT_NGSEA_GUIDE.md` (full guide, 882 lines)
- `BSC_SECTION_Q_FRAMEWORK.md` (BSC concepts, 1,200+ lines)
- `BOALF_BOD_JOIN_EXAMPLE.sql` (SQL examples)

**Scripts**:
- `detect_ngsea_events.py` (automated detection)
- `ingest_p114_s0142.py` (backfill worker)

**Summaries**:
- `NGSEA_GUIDE_UPDATES_SUMMARY.md` (changelog)
- `SESSION_SUMMARY_NGSEA_CORRECTIONS.md` (session notes)

---

## Key Citations

**P448 Ofgem Decision**:
> "Acceptance data is constructed by the ESO after the event and entered into Settlement."

**BSCP18**:
> "A Network Gas Supply Emergency Acceptance will always be a Bid."

**BSC Section T**:
> "SAA determines the official Trading Charges and cashflows."

---

## Support

**Questions?** Check:
1. GAS_EMERGENCY_CURTAILMENT_NGSEA_GUIDE.md (comprehensive)
2. BOALF_BOD_JOIN_EXAMPLE.sql (SQL patterns)
3. BSC_SECTION_Q_FRAMEWORK.md (BSC fundamentals)

**Data Issues?** Check:
1. PROJECT_CONFIGURATION.md (all settings)
2. STOP_DATA_ARCHITECTURE_REFERENCE.md (architecture)

**Contact**: george@upowerenergy.uk

---

*Quick Reference Version 1.0*  
*Last Updated: 28 December 2025*  
*Reflects P448/BSCP18/BSC Section Q/T guidance*
