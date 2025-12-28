# Annex X: Interpreting Curtailment, Acceptances, and Settlement Outputs (P114)

**Purpose**: Formal guidance on using P114 settlement data to analyze generator curtailment events, including NGSEA (Network Gas Supply Emergency Acceptances). Clarifies what P114 evidence shows and what it does not.

**Audience**: Energy analysts, traders, compliance teams, data scientists

**Last Updated**: 28 December 2025

---

## Executive Summary

**P114 settlement data is more than just volumes** - it reveals:
- Section T Trading Charges (pay-as-bid acceptance cashflows)
- Settlement-run versioning (data maturity: II → R3 → RF)
- BSAD transparency (Balancing Services Adjustment Data)
- Post-event corrections (BSCP18 changes via committee review)

**Critical Understanding**: P114 shows **settlement outcomes** (what was settled), not operational reality (what happened in real-time).

**Key Limitation**: Curtailment may not appear in operational BOALF data due to post-event construction (NGSEA P448 process).

---

## Section X.1: Key Datasets for Curtailment Analysis

### X.1.1 P114 Settlement Data (S0142 BPI Flow)

**Source**: Settlement Administration Agent (SAA)  
**Format**: BPI (Balancing Platform Imbalance)  
**BigQuery Table**: `elexon_p114_s0142_bpi`

**Key Fields**:
```
bm_unit_id       - BM Unit identifier (e.g., T_KEAD-2)
settlement_date  - Trading day
settlement_period - Half-hour period (1-48)
value2           - Energy settled (MWh) - negative = reduction
system_price     - Imbalance price (£/MWh) - SBP/SSP
multiplier       - Period duration (0.5 for half-hour)
settlement_run   - II/R3/RF (maturity indicator)
```

**What P114 Shows**:
- **Trading Charges** calculated by SAA per Section T
- Energy settled (positive = generation, negative = reduction)
- Settlement runs show data evolution (II → R3 → RF)
- BSAD components (bid-offer acceptance costs)

**What P114 Does NOT Show**:
- Real-time operational BOALF acceptance data
- Acceptance prices (shows system_price, not bid/offer price)
- Causal triggers (e.g., "this was NGSEA" flag)
- Commercial arrangements behind curtailment

### X.1.2 BOALF Operational Data

**Source**: BMRS (Balancing Mechanism Reporting Service)  
**Format**: Bid-Offer Acceptance Levels  
**BigQuery Table**: `bmrs_boalf`

**Key Fields**:
```
bmUnitId          - BM Unit identifier
settlementDate    - Trading day
settlementPeriod  - Half-hour period
acceptanceNumber  - Unique acceptance ID
acceptanceType    - BID or OFFER
levelFrom         - MW before acceptance
levelTo           - MW after acceptance
soFlag            - TRUE = SO-flagged (constructed/special)
timeFrom/timeTo   - Duration window
```

**What BOALF Shows**:
- Real-time operational acceptances (when issued)
- MW changes instructed by NESO
- SO-Flag indicates constructed/special acceptances
- Duration and timing of instructions

**What BOALF Does NOT Show**:
- Prices (must join to BOD for bid/offer prices)
- Settlement outcomes (use P114 for settled values)
- Post-event corrections (use P114 settlement runs)

### X.1.3 BOD Bid-Offer Data

**Source**: BMRS  
**Format**: Bid-Offer prices submitted by generators  
**BigQuery Table**: `bmrs_bod`

**Key Fields**:
```
bmUnitId       - BM Unit identifier
settlementDate - Trading day
settlementPeriod - Half-hour period
pairId         - Bid-offer pair ID (ladder identifier)
bid            - Bid price (£/MWh) - negative for reductions
offer          - Offer price (£/MWh) - positive for increases
```

**What BOD Shows**:
- Prices generators submitted for BM actions
- Negative bid prices = payment TO generator for reduction
- Multiple pairs = price ladder (stacking)

**What BOD Does NOT Show**:
- Which bids/offers were accepted (use BOALF)
- Settlement outcomes (use P114)

### X.1.4 FPN Final Physical Notification

**Source**: BMRS  
**Format**: Generator forecast submissions  
**Status**: Not currently ingested to BigQuery

**Key Fields** (when available):
```
bmUnitId        - BM Unit identifier
settlementDate  - Trading day
settlementPeriod - Half-hour period
levelFrom       - Expected generation (MW)
```

**What FPN Shows**:
- Generator's forecast of output
- Baseline for imbalance calculation
- Can reveal mismatch during curtailment

**Use for NGSEA**: Large FPN vs actual discrepancy indicates post-event correction (BSCP18).

---

## Section X.2: P114 as More Than Volumes

### X.2.1 Section T Trading Charges

**P114 `value2` field is NOT just metered energy** - it's the outcome of Section T Trading Charges calculation by SAA.

**Trading Charges Include**:
1. **Bid-Offer Acceptance Charges**: Pay-as-bid cashflows for accepted actions
2. **Delivery/Non-Delivery Adjustments**: Penalties for not delivering accepted actions
3. **Tagging**: Allocation of acceptances to responsible parties
4. **BSAD Components**: Balancing Services Adjustment Data

**Formula**:
```
Trading Charge (£) = Σ [Accepted Volume × Acceptance Price × Delivery Factor]
```

**In P114**:
```
revenue_gbp = value2 × system_price × multiplier
```

**Critical Distinction**:
- `value2` reflects **settled energy** (post-Section T calculation)
- `system_price` = imbalance price (NOT acceptance price from BOD)
- Result = settlement outcome, not operational estimate

### X.2.2 Settlement-Run Versioning

**P114 evolves through 3 settlement runs**:

| Run | Timing | Description | Data Maturity |
|-----|--------|-------------|---------------|
| **II** | T+1 day | Initial | ~85% accurate |
| **R3** | T+14 months | Reconciliation | ~95% accurate (includes BSCP18 corrections) |
| **RF** | T+28 months | Final | 100% (legally binding) |

**Why Multiple Runs?**:
- **II**: Fast availability, uses best available data at T+1
- **R3**: Incorporates late metering, BSCP18 corrections, validation
- **RF**: Final reconciliation, all disputes resolved

**For NGSEA Analysis**:
- **II**: First indication (may have errors)
- **R3**: Shows BSCP18 committee corrections
- **RF**: Authoritative (use for revenue/cost calculations)

**Query Pattern**:
```sql
-- Compare settlement runs to detect BSCP18 corrections
SELECT 
  settlement_date,
  settlement_period,
  bm_unit_id,
  MAX(CASE WHEN settlement_run = 'II' THEN value2 END) as ii_energy,
  MAX(CASE WHEN settlement_run = 'R3' THEN value2 END) as r3_energy,
  MAX(CASE WHEN settlement_run = 'RF' THEN value2 END) as rf_energy,
  MAX(CASE WHEN settlement_run = 'RF' THEN value2 END) - 
    MAX(CASE WHEN settlement_run = 'II' THEN value2 END) as correction_mwh
FROM elexon_p114_s0142_bpi
WHERE bm_unit_id = 'T_KEAD-2'
  AND settlement_date = '2024-03-15'
GROUP BY settlement_date, settlement_period, bm_unit_id
HAVING ABS(correction_mwh) > 10  -- Significant corrections only
```

### X.2.3 BSAD Transparency

**BSAD (Balancing Services Adjustment Data)** is embedded in P114:
- Costs of bid-offer acceptances
- Reconciliation adjustments
- System operator charges

**P114 `value2` includes BSAD effects**:
- Accepted actions tagged to responsible parties
- Costs allocated via Section T Trading Charges
- Shows up as energy imbalance adjustments

**Example**:
- Generator accepts 100 MW reduction (BID)
- P114 shows `-50 MWh` for period (100 MW × 0.5h)
- Negative energy = generator paid (BSAD cost to system)
- Settlement run RF = final BSAD allocation

---

## Section X.3: Why Curtailment May Not Appear in BOALF

### X.3.1 Post-Event Construction (NGSEA P448)

**Normal BM Flow**:
```
NESO accepts bid/offer → BOA instruction → BOALF published → P114 settled
```

**NGSEA P448 Flow**:
```
Gas emergency → LSI issued → Generator reduces → NESO constructs acceptance POST-EVENT → P114 settled
```

**Key Difference**: NGSEA acceptances are **constructed after the event**, not issued in real-time.

**P448 Ofgem Decision**:
> "Load Shedding instructions during Stage 2+ NGSE are treated for BSC purposes as electricity bids, and **Acceptance data is constructed by the ESO after the event and entered into Settlement**."

**Implications**:
- BOALF may not show real-time acceptance during event
- P114 will show constructed acceptance in II/R3/RF runs
- SO-Flag = TRUE in BOALF indicates constructed acceptance
- Timing may not align with actual curtailment moment

### X.3.2 Detection Strategy

**Operational BOALF may be incomplete for NGSEA** - use P114 patterns instead:

**P114 Detection Criteria**:
1. Negative `value2` (reduction) for gas units (T_*)
2. High `system_price` (>£80/MWh indicates supply stress)
3. Multiple units affected same period (3+ units)
4. Large reductions (>50 MWh per unit)
5. Settlement run corrections (R3/RF differs from II)

**BOALF Validation**:
- Check for SO-Flag = TRUE (constructed acceptance)
- Timing may lag actual curtailment event
- May be absent entirely (post-event construction)

**Cross-Validation**:
- NESO constraint cost publications (MBSS, Annual Report)
- Gas market data (pipeline flows, linepack levels)
- System operator announcements (emergency declarations)

---

## Section X.4: NGSEA and Post-Event Corrections (P448/BSCP18)

### X.4.1 The P448 Settlement Construct

**P448 creates special settlement treatment for NGSEA**:
1. ESO constructs acceptance data after gas emergency
2. NGSEA Settlement Validation Committee reviews
3. Committee can direct changes to FPN, BOD, Acceptance Data
4. Corrections applied via BSCP18 process

**BSCP18 Statement**:
> "Each NGSEA is entered using a similar process to Emergency Instructions and is reviewed after the event by the NGSEA Settlement Validation Committee which may direct changes to FPNs, Bid-Offer Data and/or Acceptance Data."

> "A Network Gas Supply Emergency Acceptance will always be a Bid."

### X.4.2 Committee Correction Process

**Step 1**: Event occurs (gas emergency, LSI issued)

**Step 2**: ESO constructs initial acceptance data (appears in II run)

**Step 3**: Committee convenes (weeks after event)

**Step 4**: Committee review:
- Were FPNs realistic?
- Were bid prices reasonable?
- Were volumes/timing correct?

**Step 5**: Committee directs corrections (if needed):
- FPN adjustments
- BOD price changes
- Acceptance volume/timing fixes

**Step 6**: BSCP18 corrections implemented (R3/RF runs)

### X.4.3 Detecting BSCP18 Corrections in P114

**Query Pattern**:
```sql
-- Find BSCP18 corrections by comparing settlement runs
WITH run_comparison AS (
  SELECT 
    settlement_date,
    settlement_period,
    bm_unit_id,
    settlement_run,
    value2,
    system_price,
    value2 * system_price * multiplier as revenue_gbp
  FROM elexon_p114_s0142_bpi
  WHERE bm_unit_id LIKE 'T_%'
    AND value2 < -50  -- Significant reductions
    AND system_price > 80  -- High prices
),
corrections AS (
  SELECT 
    r3.settlement_date,
    r3.settlement_period,
    r3.bm_unit_id,
    ii.value2 as ii_energy,
    r3.value2 as r3_energy,
    r3.value2 - ii.value2 as correction_mwh,
    ii.revenue_gbp as ii_revenue,
    r3.revenue_gbp as r3_revenue,
    r3.revenue_gbp - ii.revenue_gbp as correction_gbp
  FROM run_comparison r3
  INNER JOIN run_comparison ii
    ON r3.settlement_date = ii.settlement_date
    AND r3.settlement_period = ii.settlement_period
    AND r3.bm_unit_id = ii.bm_unit_id
  WHERE r3.settlement_run = 'R3'
    AND ii.settlement_run = 'II'
    AND ABS(r3.value2 - ii.value2) > 5  -- Material correction
)
SELECT * FROM corrections
ORDER BY ABS(correction_gbp) DESC
LIMIT 20;
```

**Interpretation**:
- Large `correction_mwh` = BSCP18 committee changed settled energy
- Large `correction_gbp` = Material financial impact of correction
- Positive correction = generator paid more in R3 vs II
- Negative correction = generator paid less (or owed more)

---

## Section X.5: Recommended Analytical Approach (Level 1 vs Level 2)

### X.5.1 Two-Level Framework

**Level 1: Operational Estimate (BOALF + BOD)**

**Use Case**: "What did NESO accept and at what price?"

**Data Sources**:
- BOALF (acceptances)
- BOD (bid/offer prices)

**Formula**:
```
Indicative Cashflow = delta_MW × duration_hours × bid_price
```

**Limitations**:
- NOT guaranteed to match settlement
- Delivery/non-delivery not accounted for
- NGSEA post-event construction not captured
- Section T adjustments not included

**When to Use**:
- Operational analysis (what was instructed?)
- Quick estimates (T+1 availability)
- Compliance checking (did units respond?)

**Level 2: Settlement-Consistent (P114/SAA)**

**Use Case**: "What was actually charged/credited in settlement?"

**Data Source**:
- P114 (settlement outputs from SAA)

**Formula**:
```
Settlement Revenue = value2 × system_price × multiplier
```

**Advantages**:
- Authoritative (Section T Trading Charges)
- Includes all adjustments (delivery, BSAD, corrections)
- Legally binding (RF run)
- Committee corrections applied (BSCP18)

**When to Use**:
- Revenue/cost calculations (financial analysis)
- Settlement verification (billing disputes)
- Historical analysis (post-RF availability)
- NGSEA detection (constructed acceptances included)

### X.5.2 Reconciliation Workflow

**Step 1**: Calculate Level 1 estimate (BOALF+BOD)
```sql
-- Level 1: Operational estimate
SELECT 
  boalf.settlement_date,
  boalf.settlement_period,
  boalf.bm_unit_id,
  (boalf.levelTo - boalf.levelFrom) as delta_mw,
  TIMESTAMP_DIFF(boalf.timeTo, boalf.timeFrom, MINUTE) / 60.0 as duration_hours,
  bod.bid as bid_price,
  ABS((boalf.levelTo - boalf.levelFrom)) * 
    (TIMESTAMP_DIFF(boalf.timeTo, boalf.timeFrom, MINUTE) / 60.0) * 
    ABS(bod.bid) as level1_cashflow_gbp
FROM bmrs_boalf boalf
LEFT JOIN bmrs_bod bod USING (bmUnitId, settlementDate, settlementPeriod)
WHERE boalf.acceptanceType = 'BID'
  AND boalf.levelTo < boalf.levelFrom  -- Turn-down
```

**Step 2**: Get Level 2 settlement outcome (P114)
```sql
-- Level 2: SAA-settled
SELECT 
  settlement_date,
  settlement_period,
  bm_unit_id,
  value2 as settled_mwh,
  system_price,
  value2 * system_price * multiplier as level2_cashflow_gbp
FROM elexon_p114_s0142_bpi
WHERE settlement_run = 'RF'  -- Final settlement
```

**Step 3**: Compare and quantify differences
```sql
-- Reconciliation
SELECT 
  l1.settlement_date,
  l1.settlement_period,
  l1.bm_unit_id,
  l1.level1_cashflow_gbp,
  l2.level2_cashflow_gbp,
  ABS(l1.level1_cashflow_gbp - ABS(l2.level2_cashflow_gbp)) as difference_gbp,
  ROUND(ABS(l1.level1_cashflow_gbp - ABS(l2.level2_cashflow_gbp)) / 
    NULLIF(ABS(l2.level2_cashflow_gbp), 0) * 100, 1) as difference_percent,
  CASE 
    WHEN ABS(difference_gbp) < 100 THEN 'Close match (<£100)'
    WHEN ABS(difference_gbp) < 1000 THEN 'Moderate difference (£100-1k)'
    ELSE 'Large difference (>£1k)'
  END as match_quality
FROM level1_estimates l1
INNER JOIN level2_settlement l2 USING (settlement_date, settlement_period, bm_unit_id)
ORDER BY ABS(difference_gbp) DESC
```

**Expected Outcomes**:
- **Close match** (<10% difference): Normal BM actions, minimal adjustments
- **Moderate difference** (10-30%): Delivery adjustments, price differences
- **Large difference** (>30%): NGSEA constructed acceptances, BSCP18 corrections, ladder pricing issues

### X.5.3 Analysis Decision Tree

```
START: Do you need curtailment analysis?
  ↓
Question 1: Is this for financial/settlement purposes?
  YES → Use Level 2 (P114 RF run)
  NO  → Continue
  ↓
Question 2: Do you need real-time operational view?
  YES → Use Level 1 (BOALF+BOD), but expect NGSEA gaps
  NO  → Continue
  ↓
Question 3: Is this for NGSEA detection?
  YES → Use Level 2 (P114) + NGSEA criteria (negative energy, high price, gas units)
  NO  → Continue
  ↓
Question 4: Do you need to validate BSCP18 corrections?
  YES → Compare II vs R3 vs RF settlement runs
  NO  → Use Level 2 (P114 RF run)
```

---

## Section X.6: Key Takeaways

### X.6.1 What P114 Evidence Shows

**✅ P114 CAN Evidence**:
1. Settlement outcomes (Section T Trading Charges)
2. Constructed acceptances entered per P448 (NGSEA)
3. Committee-driven corrections (BSCP18 changes visible in R3/RF)
4. Settlement run progression (data maturity: II → R3 → RF)
5. BSAD transparency (balancing costs allocation)
6. Negative revenue = generator received payment

### X.6.2 What P114 Cannot Show

**❌ P114 CANNOT Evidence**:
1. Real-world commercial arrangements (gas contracts, compensation deals)
2. Causal operational triggers (without external markers like NGSEA flags)
3. Acceptance prices (shows `system_price`, not `bid_price` from BOD)
4. Committee decision rationale (need BSCP18 minutes/change requests)
5. Real-time operational BOALF data (post-event construction for NGSEA)

### X.6.3 Critical Statements

**P114 Records Are Settlement Artefacts**:
> "P114 records are settlement artefacts, NOT gas commercial contracts. They show what was settled by SAA per Section T, not the underlying commercial makeup of compensation."

**NGSEA is Post-Event Construction**:
> "NGSEA acceptances are constructed after the event and entered into Settlement. They may not appear in real-time operational BOALF data." *(P448 Ofgem Decision)*

**Always a Bid**:
> "A Network Gas Supply Emergency Acceptance will always be a Bid." *(BSCP18)*

**Section T is Authoritative**:
> "Section T is where SAA determines the official Trading Charges and cashflows." *(BSC Section T)*

---

## Section X.7: Practical Examples

### Example 1: Detecting NGSEA Events

**Scenario**: Identify gas emergency curtailments in 2024

```sql
-- NGSEA Detection Query
WITH p114_curtailments AS (
  SELECT 
    settlement_date,
    settlement_period,
    COUNT(DISTINCT bm_unit_id) as units_affected,
    SUM(value2) as total_reduction_mwh,
    AVG(system_price) as avg_system_price,
    SUM(value2 * system_price * multiplier) as total_payment_gbp
  FROM elexon_p114_s0142_bpi
  WHERE settlement_run = 'RF'
    AND value2 < -50  -- Large reductions
    AND bm_unit_id LIKE 'T_%'  -- Gas CCGTs
    AND system_price > 80  -- High prices
    AND settlement_date BETWEEN '2024-01-01' AND '2024-12-31'
  GROUP BY settlement_date, settlement_period
  HAVING COUNT(DISTINCT bm_unit_id) >= 3  -- Multiple units = event
)
SELECT 
  settlement_date,
  settlement_period,
  units_affected,
  ROUND(total_reduction_mwh, 2) as reduction_mwh,
  ROUND(avg_system_price, 2) as price_gbp_per_mwh,
  ROUND(ABS(total_payment_gbp), 2) as payment_to_generators_gbp
FROM p114_curtailments
ORDER BY ABS(total_payment_gbp) DESC
LIMIT 20;
```

**Output Interpretation**:
- `units_affected ≥ 3` → Likely NGSEA event
- `price_gbp_per_mwh > 100` → Severe gas stress
- `payment_to_generators_gbp > £50k` → Material industry cost

### Example 2: Quantifying BSCP18 Corrections

**Scenario**: Find NGSEA events where committee made material corrections

```sql
-- BSCP18 Correction Analysis
WITH corrections AS (
  SELECT 
    rf.settlement_date,
    rf.settlement_period,
    rf.bm_unit_id,
    ii.value2 as ii_energy_mwh,
    rf.value2 as rf_energy_mwh,
    rf.value2 - ii.value2 as correction_mwh,
    ii.value2 * ii.system_price * ii.multiplier as ii_payment_gbp,
    rf.value2 * rf.system_price * rf.multiplier as rf_payment_gbp,
    (rf.value2 * rf.system_price * rf.multiplier) - 
      (ii.value2 * ii.system_price * ii.multiplier) as correction_payment_gbp
  FROM elexon_p114_s0142_bpi rf
  INNER JOIN elexon_p114_s0142_bpi ii
    ON rf.settlement_date = ii.settlement_date
    AND rf.settlement_period = ii.settlement_period
    AND rf.bm_unit_id = ii.bm_unit_id
  WHERE rf.settlement_run = 'RF'
    AND ii.settlement_run = 'II'
    AND rf.value2 < -50  -- Curtailments
    AND rf.bm_unit_id LIKE 'T_%'
    AND ABS(rf.value2 - ii.value2) > 10  -- Material correction
)
SELECT 
  settlement_date,
  settlement_period,
  bm_unit_id,
  ROUND(ii_energy_mwh, 2) as initial_settlement_mwh,
  ROUND(rf_energy_mwh, 2) as final_settlement_mwh,
  ROUND(correction_mwh, 2) as correction_mwh,
  ROUND(ABS(ii_payment_gbp), 2) as initial_payment_gbp,
  ROUND(ABS(rf_payment_gbp), 2) as final_payment_gbp,
  ROUND(correction_payment_gbp, 2) as correction_impact_gbp,
  CASE 
    WHEN correction_payment_gbp > 0 THEN 'Generator paid MORE in RF'
    WHEN correction_payment_gbp < 0 THEN 'Generator paid LESS in RF'
    ELSE 'No change'
  END as correction_direction
FROM corrections
ORDER BY ABS(correction_payment_gbp) DESC
LIMIT 20;
```

**Output Interpretation**:
- Large `correction_mwh` → Committee changed settled volumes
- `correction_impact_gbp > 0` → Generator benefited from correction
- `correction_impact_gbp < 0` → Generator received less than initially calculated

---

## References

**BSC Documents**:
- BSC Section Q: Bid-Offer Acceptance definitions
- BSC Section T: Trading Charges (SAA settlement calculations)
- BSC Section Q Simple Guide: Plain English companion

**Operational Procedures**:
- BSCP18: Corrections to Bid-Offer Acceptance Related Data

**Modification Proposals**:
- P448 Ofgem Decision: NGSEA settlement construct

**Elexon Guidance**:
- NGSEA Guidance Note: Two-stage process (construction + committee review)
- S0142 Data Specification: P114 settlement report format

**Project Documentation**:
- `GAS_EMERGENCY_CURTAILMENT_NGSEA_GUIDE.md`: NGSEA explanation
- `BSC_SECTION_Q_FRAMEWORK.md`: Core BSC concepts
- `P114_SETTLEMENT_VALUE_EXPLAINED.md`: Settlement calculation mechanics
- `BOALF_BOD_JOIN_EXAMPLE.sql`: Practical join examples
- `NESO_CONSTRAINT_COST_PUBLICATIONS.md`: Cross-validation datasets

---

*Created: 28 December 2025*  
*Author: GitHub Copilot (Claude Sonnet 4.5)*  
*Related: Todo 4 - Formal Annex X on interpreting curtailment data*  
*Status: Formal guidance document for energy analysts and compliance teams*  
*Next: Integrate into main NGSEA guide as referenced annex*
