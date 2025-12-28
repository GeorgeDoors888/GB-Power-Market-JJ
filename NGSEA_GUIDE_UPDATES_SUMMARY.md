# NGSEA Guide Updates - Critical Corrections Applied

**Date**: 28 December 2025  
**Files Updated**: 
- `GAS_EMERGENCY_CURTAILMENT_NGSEA_GUIDE.md` (major revisions)
- `BOALF_BOD_JOIN_EXAMPLE.sql` (new file)

---

## Summary of Changes

### 1. Separated Three Distinct Settlement Concepts (Part 2 Rewrite)

**Previous Issue**: Guide conflated pay-as-bid acceptances, imbalance settlement, and NGSEA P448 construct.

**Fixed**: Part 2 now clearly separates:

**A. Pay-as-bid acceptances (BM action cashflows)**
- Section T Trading Charges (SAA-calculated)
- BOA (Bid-Offer Acceptance) instructions
- Accept bid/offer → charge/credit at that price

**B. Imbalance settlement (SBP/SSP)**
- SEPARATE mechanism from acceptances
- Cash-out price applied to party's net energy imbalance
- Settles deviation from contracted position

**C. NGSEA P448 construct**
- Post-event CONSTRUCTED acceptances (not real-time)
- Committee review can change FPN, Bid Prices, Acceptance Data
- "A Network Gas Supply Emergency Acceptance will always be a Bid" *(BSCP18)*

**Citations Added**: P448 Ofgem Decision, BSCP18, BSC Section Q, BSC Section T, Elexon NGSEA Guidance

---

### 2. Added Part 12: Cashflow Calculation (Level 1 vs Level 2)

**Level 1 — Indicative/Operational Cashflow (BOALF + BOD)**
- Use case: "What did NESO accept and at what price?"
- Formula: `delta_mw × duration_hours × bid_price`
- **NOT guaranteed to match settlement** due to:
  * Delivery/non-delivery adjustments (Section T)
  * NGSEA post-event construction/committee changes (P448, BSCP18)
  * Settlement run corrections (II → R3 → RF)

**Level 2 — Settlement-Consistent Cashflow (P114/SAA)**
- Use case: "What was actually charged/credited in settlement?"
- Source: Section T Trading Charges (SAA outputs)
- Formula: `value2 × system_price × multiplier`
- **Authoritative** settlement outcome

**Key Insight**: Level 1 ≠ Level 2 (expect differences, use appropriate level for task)

---

### 3. Clarified What P114 Can/Cannot Evidence

**✅ P114 CAN evidence**:
1. Settlement outcomes (Section T Trading Charges)
2. Constructed acceptances entered per P448
3. Committee-driven changes to settlement inputs
4. Settlement run progression (II → R3 → RF maturity)
5. Negative revenue = generator paid

**❌ P114 CANNOT evidence**:
1. Real-world commercial arrangements (gas contracts, compensation deals)
2. Causal operational trigger without explicit NGSEA markers
3. Acceptance prices (P114 shows `system_price` = imbalance price, not acceptance price)
4. Committee decision rationale (minutes/change requests needed)

**Critical Statement**: "P114 records are settlement artefacts, NOT gas commercial contracts"

---

### 4. Created BOALF/BOD Join Example (SQL with BigQuery Field Names)

**File**: `BOALF_BOD_JOIN_EXAMPLE.sql`

**Part 1**: Basic join (one BOALF acceptance → BOD bid price)
```sql
JOIN bmrs_bod bod
  ON boalf.bmUnitId = bod.bmUnitId
  AND boalf.settlementDate = bod.settlementDate
  AND boalf.settlementPeriod = bod.settlementPeriod
WHERE boalf.acceptanceType = 'BID'
  AND bod.bid IS NOT NULL
```

**Part 2**: Handle multiple BOD pairs (ladder stacking)
- Uses `ARRAY_AGG()` to collect all price tiers
- Notes need for volume band matching logic (simplified approach shown)

**Part 3**: Compare Level 1 vs Level 2
- Joins BOALF+BOD (operational) to P114 (settled)
- Calculates `cashflow_difference_gbp` to quantify variance
- Classifies match quality: CLOSE/MODERATE/LARGE difference

**Field Names Documented**:
- BOALF: `bmUnitId`, `settlementDate`, `settlementPeriod`, `acceptanceNumber`, `acceptanceTime`, `acceptanceType`, `levelFrom`, `levelTo`, `timeFrom`, `timeTo`, `soFlag`
- BOD: `bmUnitId`, `settlementDate`, `settlementPeriod`, `pairId`, `bid`, `offer`
- P114: `bm_unit_id`, `settlement_date`, `settlement_period`, `value2`, `system_price`, `multiplier`, `settlement_run`

**NGSEA Detection Filters**:
```sql
WHERE acceptanceType = 'BID'
  AND levelTo < levelFrom  -- Turn-down
  AND soFlag = TRUE        -- SO-flagged (constructed)
  AND system_price > 80    -- High price (gas stress)
```

---

### 5. Updated P114 Coverage Statistics

**Previous (Stale)**:
- Records: 59.69M
- Days: 219
- Status: Unknown

**Current (Accurate)**:
- Records: **105.25M** (nearly doubled!)
- Days: **399 days** (Oct 2021 - Oct 2024)
- Coverage: **36%** (399/1108 calendar days)
- Gap: **709 days missing** (Oct 15, 2022 → Sep 24, 2024)
- Status: **Backfill batch 49/53 active**, processing 2023 data for 2022 settlement dates
- Expected final: ~1,096 days (2022-2025)

**Key Finding**: "219 days" was outdated - actual is 399 days, but massive gap being filled by active backfill.

---

### 6. Enhanced Executive Summary & Table of Contents

**Executive Summary** now includes:
- "NGSEA is post-event construction" (not real-time BOALF)
- Committee review process (P448)
- Critical distinction from normal BM actions

**Table of Contents** updated:
- Part 2 labeled **CRITICAL** (P448 construct explanation)
- Part 12 added and labeled **CRITICAL** (Level 1 vs Level 2)
- References updated with P448, BSCP18, Section T citations

---

## Key Takeaways for Users

### 1. Don't Conflate Acceptances, Imbalance, and NGSEA
- **Acceptances** = pay-as-bid (Section T Trading Charges)
- **Imbalance** = SBP/SSP cash-out (separate mechanism)
- **NGSEA** = P448 post-event construct with committee review

### 2. Use Appropriate Data Level for Task
- **Operational analysis** → Level 1 (BOALF+BOD)
- **Settlement verification** → Level 2 (P114/SAA)
- **Expect differences** between Level 1 and Level 2

### 3. P114 Shows Settlement Outcomes, Not Commercial Deals
- Can evidence: Constructed acceptances, settlement calculations, committee changes
- Cannot evidence: Underlying commercial arrangements, gas contracts, "why" decisions

### 4. NGSEA is NOT Real-Time BOALF Flow
- Acceptance data constructed AFTER event
- Committee can change FPN, Bid Prices, Acceptance Data
- May not appear in operational BOALF immediately
- Use `soFlag = TRUE` to identify constructed acceptances

### 5. Join BOALF to BOD Carefully
- Match on: `bmUnitId`, `settlementDate`, `settlementPeriod`
- Handle multiple BOD pairs (ladder stacking)
- Use `acceptanceType` to select bid vs offer price
- Expect differences vs P114 settled outcomes

---

## Testing Recommendations

### 1. Validate BOALF/BOD Join
```bash
# Run example query in BigQuery
bq query --use_legacy_sql=false < BOALF_BOD_JOIN_EXAMPLE.sql
```

### 2. Compare Level 1 vs Level 2 for Known NGSEA Event
- Pick date: Oct 17-23, 2024 (high prices)
- Run Part 3 of join example
- Quantify typical cashflow difference
- Document settlement adjustments causing variance

### 3. Test NGSEA Detection with soFlag
```python
python3 detect_ngsea_events.py
# Add soFlag filter to detection criteria
```

### 4. Verify P114 Coverage After Backfill Complete
- Wait for batch 53/53 completion
- Re-run coverage analysis query
- Expect ~584M total records (272k/day × 1,096 days)
- Verify 709-day gap filled

---

## Next Steps (Outstanding Todos)

1. **Todo 2**: Research NESO constraint cost publications
   - Constraint Breakdown dataset
   - 24-month forecast
   - MBSS reports

2. **Todo 3**: Develop statistical NGSEA detection algorithm
   - Scoring: 2×A (turn-down) + 2×B (no BOALF) + 1×C (FPN mismatch) + 1×D (constraint spike)
   - Integrate into `detect_ngsea_events.py`

3. **Todo 4**: Write Annex X: Interpreting Curtailment Data
   - P114 as more than volumes
   - Trading Charges + settlement-run versioning
   - BSAD transparency

4. **Todo 10**: Verify negative bid payment formula
   - Test against actual P114 settlement records
   - Quantify Level 1 vs Level 2 differences
   - Document typical settlement adjustments

---

## References

**BSC Documents**:
- BSC Section Q: Bid-Offer Acceptance definitions
- BSC Section T: Trading Charges (SAA settlement calculations)
- BSC Section Q Simple Guide: Plain English companion

**Operational Procedures**:
- BSCP18: Corrections to Bid-Offer Acceptance Related Data (NGSEA specific)

**Modification Proposals**:
- P448 Ofgem Decision: NGSEA settlement construct

**Elexon Guidance**:
- NGSEA Guidance Note: Two-stage process (construction + committee review)

**Project Documentation**:
- `BSC_SECTION_Q_FRAMEWORK.md`: Core BSC concepts
- `P114_SETTLEMENT_VALUE_EXPLAINED.md`: Settlement calculation mechanics
- `BOALF_BOD_JOIN_EXAMPLE.sql`: Practical join examples

---

*Created: 28 December 2025*  
*Author: GitHub Copilot (Claude Sonnet 4.5)*  
*Context: User provided BSC/BSCP18/P448 guidance revealing critical conceptual errors in NGSEA guide*  
*Impact: Guide now correctly separates pay-as-bid, imbalance, and P448 construct; clarifies Level 1 vs Level 2 cashflow*
