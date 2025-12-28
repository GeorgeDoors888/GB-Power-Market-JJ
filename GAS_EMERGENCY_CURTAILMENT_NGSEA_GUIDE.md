# Network Gas Supply Emergency Acceptances (NGSEA) Guide

## Document Purpose

Explains how gas generators are **paid to turn down** during gas supply emergencies, and how this appears in BSC settlement data. **Critical clarification**: Distinguishes between pay-as-bid acceptances (Section T Trading Charges), imbalance settlement (SBP/SSP), and NGSEA P448 post-event construct.

**Key Question Answered**: When gas generators are curtailed (turned down/off) during a gas emergency, how do they get paid, and where does this show up in P114/BOALF data?

**Document Structure**:
- **Part 1**: Gas Emergency Mechanics (GSO, linepack, LSI)
- **Part 2**: BSC Settlement Mechanism - The P448 Construct ⚠️ **CRITICAL**
- **Part 3**: Data Trail (Gas Emergency → Settlement)
- **Part 4**: Negative Bids Explained (pricing mechanics)
- **Part 5**: Detecting NGSEA Events in Data
- **Part 6**: BSCP18 Correction Process
- **Part 7**: Real-World Example Analysis
- **Part 8**: Data Availability (P114 399 days, backfill in progress)
- **Part 9**: Practical Analysis Steps
- **Part 10**: Key Takeaways
- **Part 11**: Related Documents
- **Part 12**: Cashflow Calculation - Level 1 vs Level 2 ⚠️ **CRITICAL**

---

## Executive Summary

### The Scenario

**Gas System Emergency** → Gas System Operator (GSO) issues **Load Shedding Instruction** → Electricity generators using gas must reduce/stop → **They get PAID to turn down** → This appears as **constructed acceptance data** in settlement (P448 process).

### Critical Distinction: NGSEA is NOT Real-Time BOALF

**NGSEA (P448) is post-event construction**:
- Acceptance data **constructed after the event** by ESO
- Reviewed by NGSEA Settlement Validation Committee
- Committee can change FPNs, Bid Prices, Acceptance Data
- "A Network Gas Supply Emergency Acceptance will always be a Bid" *(BSCP18)*

**NOT** the real-time operational BOALF trail you'd expect from normal BM actions.

### How Payment Works

Generators submit **negative bids** = "Pay me £X/MWh and I'll reduce output by Y MW"

**Example**:
- Generator: T_KEAD-2 (gas-fired CCGT)
- Normal bid: £-50/MWh to reduce 100 MW
- Interpretation: "Pay me £50/MWh and I'll turn down 100 MW"
- During gas emergency: NESO constructs acceptance post-event
- Generator receives: 100 MW × 0.5 hours × £50/MWh = **£2,500 to turn down**

**Critical Concept**: Negative bid prices = payment TO generator for reduction, not FROM generator.

---

## Part 1: Gas Emergency Mechanics

### 1.1 What Triggers NGSEA?

**Gas System Operator (GSO)** declares emergency when:
- Gas supply shortage (pipeline issues, import constraints)
- Linepack critically low (gas storage in pipes via pressure)
- Demand exceeds supply + storage capacity
- System integrity at risk

### 1.2 Linepack Explained

**Linepack**: Gas stored in the transmission system by maintaining pressure.

**How it works**:
- High pressure = more gas molecules stored in pipes
- System can temporarily supply more than incoming gas by reducing pressure
- Emergency → pressure drops → must reduce offtake (curtail generators)

**Reference**: NESO - Introduction to energy system flexibility document explains linepack mechanism.

### 1.3 Load Shedding Instruction (LSI)

**Issued by**: Gas System Operator (GSO)
**Received by**: Gas-fired electricity generators
**Content**: "Reduce gas offtake by X mcm/hour immediately"

**Effect on electricity system**:
- Generators must reduce output proportionally
- Creates sudden generation shortfall
- NESO (electricity SO) must compensate with other generation
- Creates BM imbalance → acceptances issued

---

## Part 2: BSC Settlement Mechanism for NGSEA - The P448 Construct

### 2.1 Critical Distinction: Three Separate Mechanisms

**A. "Acceptance pay-as-bid" (BM action cashflows)**

Conceptually: NESO accepts a bid/offer → creates **BOA (Bid-Offer Acceptance)** instruction to change output.  
NESO describes BOAs as instructions issued once bid/offer accepted. *(NESO BOA documentation)*

In BSC terms: Section Q Simple Guide defines "Acceptance" as a communication; "Bid-Offer Acceptance Time" = when NETSO issued it. *(BSC Section Q Simple Guide)*

**Key point**: "Pay-as-bid" belongs to BM action side - you settle the accepted action at its bid/offer price (subject to delivery/non-delivery rules in **Section T**).  
**Section T is where SAA determines Trading Charges, volumes, and cashflows.** *(BSC Section T)*

**B. "Imbalance settlement / cash-out" (SBP/SSP)**

Imbalance settlement is **separate** from acceptances:  
- SBP/SSP are "cash-out" prices applied to party's energy imbalance  
- Acceptances → action-level cashflows (pay-as-bid mechanics inside Trading Charges)  
- Imbalance → settles party's net deviation vs contracted position *(Elexon imbalance pricing)*

**C. NGSEA (P448) construct - NOT normal BOA flow**

**P448 (Ofgem Decision)** creates specific settlement construct for gas load shedding:  
> "Load Shedding instructions during Stage 2+ NGSE are treated for BSC purposes as electricity bids, and **Acceptance data is constructed by the ESO after the event and entered into Settlement**." *(P448 Ofgem Decision)*

> "There is a post-event committee that can reduce FPNs, amend Bid Price and/or amend Acceptance Data." *(P448 Ofgem Decision)*

**BSCP18** operationalises this:  
> "Each NGSEA is entered using a similar process to Emergency Instructions and is reviewed after the event by the NGSEA Settlement Validation Committee which may direct changes to FPNs, Bid-Offer Data and/or Acceptance Data." *(BSCP18)*

> "A Network Gas Supply Emergency Acceptance will always be a Bid." *(BSCP18, explicit statement)*

**NGSEA Guidance Note** describes two-stage process:  
1. ESO constructs BOAs post-LSI and submits into Settlement  
2. Committee review may direct further settlement data changes *(Elexon NGSEA Guidance)*

### 2.2 Bottom Line: NGSEA is Post-Event Construction

**NGSEA is NOT real-time accepted actions**:  
- "Acceptance" record **constructed after the event** to reflect gas load shedding effect  
- NOT the real-time BMRS acceptance trail you'd expect in operational BOALF  
- This explains why NGSEA may not appear in operational BOALF data immediately  
- Settlement records are **settlement artefacts** (accepted/constructed data + SAA charge calculations)  

### 2.3 What This Means for Data Analysis

**In BOALF (operational data)**:  
- May show SO-Flag = TRUE for constructed acceptances  
- Timing may not align with real-time curtailment event  
- Acceptance created after event, not during

**In P114 (settlement data)**:  
- Shows **SAA-settled** outcome after committee review  
- Includes constructed acceptance data entered per P448  
- May differ from initial II run after BSCP18 corrections applied  
- **Section T Trading Charges** = final cashflows, not operational estimates

---

## Part 3: Data Trail - Gas Emergency → Settlement

### 3.1 End-to-End Pathway

```
Gas System Emergency (GSO)
    ↓
Load Shedding Instruction to generator
    ↓
NESO accepts generator's negative BID
    ↓
Appears in BOAL/BOALF (BMRS) as BID acceptance with SO-Flag
    ↓
Post-event validation committee review
    ↓
BSCP18 corrections to FPN/BOD/Acceptance data
    ↓
Corrections implemented in SAA next settlement run
    ↓
Final settlement in P114 (RF run after 28 months)
```

### 3.2 Step-by-Step Example

**Event**: Gas emergency on 2024-03-01, period 12 (11:30-12:00)

**Step 1: Generator has submitted negative bid**
```sql
-- bmrs_bod table
bmUnitId: T_KEAD-2
settlementDate: 2024-03-01
settlementPeriod: 12
pairId: 67890
bid: -75.00  -- Negative = paid to reduce
bidVolume: 150  -- MW reduction offered
```

**Step 2: GSO issues LSI**
```
Time: 11:35
Instruction: "Reduce gas offtake by 1,500 mcm/hour"
Affected units: T_KEAD-2, T_PEHE-1, T_GRAIN-1
```

**Step 3: NESO accepts negative bids (BM instruction)**
```
Time: 11:37
NESO issues acceptance:
  - acceptanceType: BID
  - bmUnitId: T_KEAD-2
  - levelFrom: 400 MW → levelTo: 250 MW
  - reduction: 150 MW
  - soFlag: TRUE  ← Indicates special event
```

**Step 4: Published to BMRS (BOALF)**
```sql
-- bmrs_boalf table
acceptanceNumber: ACC_2024030112001
bmUnitId: T_KEAD-2
acceptanceTime: 2024-03-01 11:37:00
acceptanceType: BID
soFlag: TRUE  -- Indicates non-normal balancing
levelFrom: 400
levelTo: 250
```

**Step 5: Initial Settlement (II run, T+1 day)**
```sql
-- elexon_p114_s0142_bpi table
bm_unit_id: T_KEAD-2
settlement_date: 2024-03-01
settlement_period: 12
settlement_run: II
value2: -75.0  -- Negative = generation reduced
system_price: 95.00  -- High (gas shortage drives prices up)
multiplier: 0.5
-- Revenue = -75.0 × 95.00 × 0.5 = -£3,562.50
-- Negative revenue = generator PAID to reduce
```

**Step 6: Validation Committee Review**
```
Post-event (within weeks):
- Generation Curtailment Validation Committee convened
- Reviews event circumstances
- May direct corrections to FPN/BOD/Acceptance data
- Corrections via BSCP18 process
```

**Step 7: BSCP18 Corrections Applied (R3 run, T+14 months)**
```sql
-- Corrected settlement
settlement_run: R3
value2: -75.0  -- Confirmed
system_price: 95.00  -- Validated
-- OR potentially adjusted if validation found errors
```

**Step 8: Final Settlement (RF run, T+28 months)**
```sql
settlement_run: RF
value2: -75.0
system_price: 95.00
-- Final, legally binding settlement value
-- Generator received £3,562.50 to reduce 75 MWh
```

---

## Part 4: Negative Bids Explained

### 4.1 What is a Negative Bid?

**Bid**: Offer to reduce output in exchange for payment

**Negative Bid Price**: Amount generator wants to be PAID per MWh of reduction

**Example Bid Ladder**:
```
Bid Price     Volume (MW)    Interpretation
-£100/MWh         50          "Pay me £100/MWh to reduce 50 MW"
-£75/MWh          100         "Pay me £75/MWh to reduce 100 MW"
-£50/MWh          150         "Pay me £50/MWh to reduce 150 MW"
-£25/MWh          200         "Pay me £25/MWh to reduce 200 MW"
```

**Why negative?**:
- Generator LOSES revenue by reducing output
- Needs compensation for: fuel costs already committed, start-up costs wasted, opportunity cost
- More negative = more expensive to turn down

### 4.2 Settlement Calculation with Negative Bids

**Formula**: `revenue_gbp = energy_mwh × system_price × multiplier`

**For negative energy (reduction)**:

Example:
- Energy: -75 MWh (reduction)
- System Price: £95/MWh
- Multiplier: 0.5
- Revenue: `-75 × 95 × 0.5 = -£3,562.50`

**Interpretation of negative revenue**:
- Negative revenue = **generator receives payment**
- Positive revenue = generator pays (or receives if selling)
- During NGSEA: Generator reduces output AND gets paid (double benefit)

### 4.3 Why Gas Generators Have Negative Bids

**Reason 1: Fuel Commitment**
- Gas purchased in advance (day-ahead/intraday)
- Can't easily resell gas on short notice
- Must pay for unused gas
- Compensation needed for wasted fuel cost

**Reason 2: Technical Constraints**
- CCGTs have minimum stable generation (MSG)
- Turning down below MSG requires shutdown
- Shutdown = restart costs (fuel, wear, time)
- Re-start takes 4-8 hours (hot start) or 24+ hours (cold start)

**Reason 3: Opportunity Cost**
- Lost electricity revenue while turned down
- Lost market share
- Contractual obligations (capacity market, PPAs)

**Typical negative bid range**: -£20/MWh to -£150/MWh

---

## Part 5: Detecting NGSEA Events in Data

### 5.1 Key Indicators

1. **SO-Flag = TRUE** in BOALF
2. **Negative energy** in P114 (reduction)
3. **High system prices** during event
4. **Gas units** (T_KEAD, T_GRAIN, T_PEHE, etc.)
5. **Clustered timing** (multiple units same period)

### 5.2 Query 1: Find NGSEA Candidates (BOALF)

```sql
-- Find acceptances with SO-Flag (special events)
SELECT 
    settlementDate,
    settlementPeriod,
    bmUnitId,
    acceptanceNumber,
    acceptanceType,
    acceptanceTime,
    soFlag,
    levelFrom,
    levelTo,
    levelTo - levelFrom as delta_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
WHERE soFlag = TRUE
  AND acceptanceType = 'BID'  -- Reductions
  AND bmUnitId LIKE 'T_%'  -- Large thermal generators
  AND settlementDate BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY settlementDate, settlementPeriod, acceptanceTime
```

**Expected Output**: Days with gas emergencies will show multiple gas units with SO-Flag=TRUE bids.

### 5.3 Query 2: Identify High-Value Curtailments (P114)

```sql
-- Find units paid to reduce output
SELECT 
    settlement_date,
    settlement_period,
    bm_unit_id,
    value2 as energy_mwh,  -- Negative = reduction
    system_price,
    value2 * system_price * multiplier as revenue_gbp,  -- Negative = paid
    settlement_run
FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
WHERE value2 < -50  -- Large reductions
  AND system_price > 80  -- High prices (typical of gas shortage)
  AND bm_unit_id LIKE 'T_%'
  AND settlement_date BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY revenue_gbp ASC  -- Most negative first (largest payments)
LIMIT 100
```

### 5.4 Query 3: Match BOALF → P114 for NGSEA

```sql
-- Comprehensive NGSEA detection
WITH ngsea_candidates AS (
    SELECT 
        settlementDate,
        settlementPeriod,
        bmUnitId,
        COUNT(*) as acceptances,
        SUM(levelTo - levelFrom) as total_mw_reduction
    FROM bmrs_boalf
    WHERE soFlag = TRUE
      AND acceptanceType = 'BID'
      AND bmUnitId LIKE 'T_%'
    GROUP BY 1,2,3
    HAVING total_mw_reduction < -100  -- Significant reduction
),
p114_data AS (
    SELECT 
        settlement_date,
        settlement_period,
        bm_unit_id,
        value2 as energy_mwh,
        system_price,
        value2 * system_price * multiplier as revenue_gbp
    FROM elexon_p114_s0142_bpi
    WHERE settlement_run = 'RF'  -- Final settlement
)
SELECT 
    n.settlementDate,
    n.settlementPeriod,
    n.bmUnitId,
    n.acceptances,
    n.total_mw_reduction,
    p.energy_mwh as p114_energy_mwh,
    p.system_price,
    p.revenue_gbp as p114_revenue_gbp,
    ROUND(n.total_mw_reduction * 0.5, 2) as expected_mwh,  -- MW × 0.5h
    ROUND(ABS(p.energy_mwh - n.total_mw_reduction * 0.5), 2) as mwh_difference
FROM ngsea_candidates n
LEFT JOIN p114_data p 
    ON n.settlementDate = p.settlement_date
    AND n.settlementPeriod = p.settlement_period
    AND n.bmUnitId = p.bm_unit_id
WHERE p.revenue_gbp < -1000  -- Significant payment
ORDER BY n.settlementDate, n.settlementPeriod, p.revenue_gbp ASC
```

---

## Part 6: BSCP18 Correction Process

### 6.1 What is BSCP18?

**BSC Procedure 18**: Corrections to Bid-Offer Acceptance Related Data

**Scope**: Covers corrections to:
- FPN (Final Physical Notifications)
- BOD (Bid-Offer Data)
- BOAL/BOALF (Acceptance Data)

**Specific NGSEA provisions** (explicit in BSCP18):
- References Network Gas Supply Emergency Acceptance
- Generation Curtailment Validation Committee
- Post-event review mechanism

### 6.2 BSCP18 Process for NGSEA

**Step 1: Event Occurs**
- Gas emergency
- LSI issued
- NGSEA acceptances processed (settled as bids)

**Step 2: Validation Committee Convened**
- Members: Elexon, NESO, industry representatives
- Timing: Within weeks of event
- Purpose: Review NGSEA circumstances and settlement treatment

**Step 3: Committee Findings**
- Review FPNs: Were forecasts appropriate?
- Review BOD: Were bid prices reasonable?
- Review Acceptances: Were volumes/timing correct?
- Determine: Should any data be corrected?

**Step 4: Directed Corrections**
- Committee MAY direct changes to:
  - FPN levels (if forecast was unrealistic)
  - BOD prices (if bids inappropriate for emergency)
  - Acceptance volumes/timing
- Corrections documented in BSCP18 Change Request

**Step 5: SAA Implementation**
- Corrections entered into SAA systems
- Applied in **next available settlement run**
- Typically R3 run (T+14 months after event)
- Can also appear in RF run (T+28 months)

**Step 6: Settlement Re-run**
- SAA recalculates affected periods
- Updated P114 outputs published
- Market participants notified of changes
- Financial adjustments made if settlement values change materially

### 6.3 Why Corrections Happen

**Common correction scenarios**:

1. **FPN was too high** (overstated generation capability)
   - Correction: Reduce FPN to realistic level
   - Effect: Reduces imbalance charged to generator

2. **Bid price was opportunistic** (exploited emergency)
   - Correction: Adjust bid price to reasonable level
   - Effect: Reduces payment to generator

3. **Acceptance volume wrong** (MW reduction miscalculated)
   - Correction: Adjust energy settled (value2)
   - Effect: Corrects revenue calculation

4. **Timing issue** (acceptance applied to wrong period)
   - Correction: Move acceptance to correct settlement period
   - Effect: Redistributes costs across periods

---

## Part 7: Real-World NGSEA Example Analysis

### 7.1 Hypothetical Scenario: March 2024 Gas Emergency

**Background**:
- Date: 2024-03-15
- Trigger: Norwegian pipeline reduced flow by 40%
- Duration: 3 hours (periods 10-12, 09:30-12:00)
- Affected: 15 gas-fired CCGTs
- Total reduction: 2,500 MW

**Market Impact**:
- System price: £120/MWh (normal: £40/MWh)
- Gas generators turned down: Lost revenue + received negative bid payment
- Other generators ramped up: Received high offer prices

### 7.2 Detection Query

```sql
-- Find the event
SELECT 
    settlement_date,
    settlement_period,
    COUNT(DISTINCT bm_unit_id) as units_affected,
    SUM(value2) as total_energy_reduction_mwh,
    AVG(system_price) as avg_system_price,
    SUM(value2 * system_price * multiplier) as total_payment_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi`
WHERE settlement_date = '2024-03-15'
  AND settlement_period BETWEEN 10 AND 12
  AND value2 < -10  -- Reductions only
  AND bm_unit_id LIKE 'T_%'  -- Thermal generators
  AND settlement_run = 'RF'  -- Final settlement
GROUP BY settlement_date, settlement_period
ORDER BY settlement_period
```

**Expected Output**:
```
Period  Units  Reduction (MWh)  Avg Price  Total Payment
10      12     -850            £118       -£50,150
11      15     -1,200          £122       -£73,200
12      13     -950            £115       -£54,625
```

### 7.3 Interpretation

**Units affected**: 15 gas generators forced to reduce

**Total reduction**: 3,000 MWh across 3 periods

**Total payment**: £178,000 paid to generators for turning down

**System price impact**: £120/MWh (3x normal) due to gas shortage

**Winners**:
- Non-gas generators: Received £120/MWh for additional output
- Gas generators with negative bids: Paid to reduce + avoided fuel costs

**Losers**:
- Demand side: Paid £120/MWh for electricity
- Suppliers: Higher cost to serve customers

---

## Part 8: Data Availability in This Project

### 8.1 BOALF Acceptance Data

**Available**:
- `bmrs_boalf`: 3.3M acceptances (2022-2025)
- `bmrs_boalf_complete`: 11M acceptances with matched prices
- `boalf_with_prices`: 4.7M validated acceptances

**SO-Flag coverage**: Available in BOALF data for detecting NGSEAs

**Limitation**: Historical BOALF may not have complete SO-Flag data (added in later years)

### 8.2 P114 Settlement Data

**Available**:
- `elexon_p114_s0142_bpi`: **105.25M records** (399 days, Oct 2021 - Oct 2024)
- Settlement runs: RF + II (actively being backfilled)
- Unique units: 6,526
- **Status**: Batch 49/53 running (2023 data loading), 709-day gap being filled

**Coverage for NGSEA detection**:
- Can identify negative energy (reductions)
- Can calculate payments (negative revenue using settlement values)
- Can correlate with high system prices
- **Important**: P114 shows **SAA-settled** outcomes (Section T Trading Charges), not just operational BOALF acceptances

**Coverage completeness**: 36% (399/1108 days between earliest-latest)
**Expected final**: ~1,096 days (2022-2025) after backfill completes

**Limitation**: 
- No direct "NGSEA flag" in P114 settlement records
- Must infer from patterns (negative energy + high prices + gas units)
- P114 shows **constructed acceptances** entered post-event for NGSEA (P448), not real-time operational flow

### 8.3 BOD Bid-Offer Data

**Available**:
- `bmrs_bod`: 439M records (2020-2025)
- Includes negative bid prices

**Use for NGSEA analysis**:
- Match acceptance prices (what generator was paid)
- Identify typical negative bid ranges
- Analyze bid behavior during stress periods

---

## Part 9: Practical Analysis Steps

### 9.1 How to Find Historical NGSEAs

**Step 1: Identify candidate days** (high system prices)
```sql
SELECT 
    settlementDate,
    AVG(systemSellPrice) as avg_price
FROM bmrs_costs
WHERE systemSellPrice > 80  -- Threshold for gas stress
GROUP BY settlementDate
HAVING AVG(systemSellPrice) > 80
ORDER BY settlementDate DESC
```

**Step 2: Check BOALF for SO-Flag acceptances**
```sql
SELECT 
    settlementDate,
    COUNT(*) as so_flag_acceptances
FROM bmrs_boalf
WHERE soFlag = TRUE
  AND settlementDate IN (/* candidate days from step 1 */)
GROUP BY settlementDate
ORDER BY so_flag_acceptances DESC
```

**Step 3: Analyze P114 for large curtailments**
```sql
SELECT 
    settlement_date,
    settlement_period,
    bm_unit_id,
    value2,
    system_price,
    value2 * system_price * multiplier as revenue_gbp
FROM elexon_p114_s0142_bpi
WHERE settlement_date IN (/* candidate days */)
  AND value2 < -50
  AND settlement_run = 'RF'
ORDER BY revenue_gbp ASC
```

### 9.2 Calculate Total NGSEA Costs

```sql
-- Estimate industry-wide NGSEA costs
SELECT 
    EXTRACT(YEAR FROM settlement_date) as year,
    EXTRACT(MONTH FROM settlement_date) as month,
    COUNT(DISTINCT settlement_date) as event_days,
    SUM(CASE WHEN value2 < 0 THEN value2 * system_price * multiplier ELSE 0 END) as curtailment_payments_gbp,
    SUM(CASE WHEN value2 < 0 THEN ABS(value2) ELSE 0 END) as total_reduction_mwh
FROM elexon_p114_s0142_bpi
WHERE system_price > 80  -- Gas stress indicator
  AND bm_unit_id LIKE 'T_%'
  AND settlement_run = 'RF'
GROUP BY year, month
ORDER BY year, month
```

---

## Part 10: Key Takeaways

### 10.1 Summary of NGSEA Mechanism

1. **Gas emergency** triggers Load Shedding Instruction (GSO → generators)
2. **Generators must reduce** gas offtake per LSI
3. **NESO accepts negative bids** to formalize reduction in BM
4. **Settled as bids** initially (Elexon guidance explicit)
5. **Generators paid** according to negative bid prices
6. **Appears in BOALF** with SO-Flag = TRUE
7. **Appears in P114** as negative energy (reduction)
8. **Post-event review** via Generation Curtailment Validation Committee
9. **BSCP18 corrections** applied in R3/RF settlement runs
10. **Final settlement** in RF run (T+28 months)

### 10.2 How Gas Generators Are Paid

**Mechanism**: Negative bid acceptance

**Payment formula**: `|reduction_mwh| × |bid_price| × 0.5`

**Example**:
- Reduction: 100 MW × 0.5 hours = 50 MWh
- Bid price: -£75/MWh
- Payment: 50 × 75 = **£3,750**

**Plus**: Generator saves fuel costs (gas not burned)

**Minus**: Generator loses electricity sales revenue

**Net effect**: Typically profitable (negative bid covers lost revenue + compensation)

### 10.3 Data Detection Checklist

To identify NGSEAs in your data:
- ✅ High system prices (>£80/MWh)
- ✅ BOALF SO-Flag = TRUE for BID acceptances
- ✅ P114 negative energy for gas units (T_*)
- ✅ Clustered timing (multiple units same period)
- ✅ P114 negative revenue (generators paid)
- ✅ BSCP18 corrections in R3/RF runs (check for value changes)

---

## Part 11: Related Documents & References

### 11.1 BSC Documents

- **BSC Section Q**: Defines BM data (PN, FPN, BOD, BOAL)
- **Section Q Simple Guide**: Plain English companion
- **BSCP18**: Corrections to Bid-Offer Acceptance Related Data (NGSEA specific)
- **Elexon NGSEA Guidance**: Network Gas Supply Emergency Acceptances explainer

### 11.2 NESO Documents

- **Balancing Mechanism Wider Access (BMWA)**: Routes into BM
- **Introduction to Energy System Flexibility**: Linepack mechanism explained
- **Balancing Mechanism Assurance Report**: NETSO obligations under Section Q

### 11.3 Project Documents

- **`BSC_SECTION_Q_FRAMEWORK.md`**: Section Q data flow and definitions
- **`P114_SETTLEMENT_VALUE_EXPLAINED.md`**: Settlement calculation mechanics
- **`S0142_GOVERNANCE_POLICY.md`**: Settlement run strategy (II/R3/RF)

### 11.4 Data Tables

- `bmrs_boalf`: Acceptance data with SO-Flag
- `bmrs_boalf_complete`: Acceptances with matched BOD prices
- `boalf_with_prices`: Validated acceptances (42.8%)
- `bmrs_bod`: Bid-offer data (negative bids)
- `elexon_p114_s0142_bpi`: Settlement outputs (59.69M records)
- `p114_settlement_canonical`: Deduplication view (RF>R3>II)

---

## Next Steps

1. **Run detection queries** to find historical NGSEAs in your 219-day P114 dataset
2. **Analyze patterns**: Which units curtailed most? What were typical payments?
3. **Calculate industry costs**: Total NGSEA payments across dataset
4. **Compare settlement runs**: How did values change from II → R3 → RF?
5. **Correlate with gas market**: Match to known gas shortage events
6. **Build dashboard**: NGSEA events, affected units, payments, system impacts

---

## Part 12: Cashflow Calculation - Level 1 vs Level 2

### 12.1 Two Different Calculation Levels

**Level 1 — Indicative / Operational Cashflow (BOALF + BOD)**

This is "what did NESO accept and at what price?" (good for operational analytics, **NOT guaranteed to match final settlement**)

**Required BOALF fields**:
- `settlementDate`, `settlementPeriod` (grouping)
- `bmUnitId` (unit key)
- `acceptanceNumber` (unique acceptance key)
- `acceptanceTime` (timestamp; aligns to "Bid-Offer Acceptance Time" concept) *(BSC Section Q)*
- `acceptanceType` (BID vs OFFER)
- `timeFrom`, `timeTo` (duration window)
- `levelFrom`, `levelTo` (MW before/after)
- `soFlag` (important to segment "special" acceptances / constructed flows - BSCP18 covers SO-Flag correction handling) *(BSCP18)*

**Required BOD fields**:
- `settlementDate`, `settlementPeriod`
- `bmUnitId`
- `bidOfferPairId` (or equivalent pair identifier)
- `bidPrice`, `offerPrice` (£/MWh prices)
- Ladder/stack fields if present (pair number / volume bands) to map acceptance to correct price step

**Indicative cashflow formula**:
```
delta_mw = levelTo - levelFrom
mwh ≈ delta_mw * duration_hours (from timeFrom→timeTo)
£ ≈ mwh * price (offerPrice or bidPrice depending on acceptanceType)
```

**⚠️ NOT GUARANTEED TO EQUAL SETTLED TRADING CHARGES** because:
- Settlement can adjust for delivery, non-delivery, tagging
- NGSEA post-event construction/committee changes *(P448, BSCP18)*
- Section T adjustments by SAA *(BSC Section T)*

**Level 2 — Settlement-Consistent Cashflow (P114/SAA)**

If you need "what was actually charged/credited in settlement," use **SAA outputs (P114 / S0142 etc.)**

Why: **Section T is where SAA determines the official Trading Charges and cashflows.** *(BSC Section T)*

P114 fields:
- `bm_unit_id`, `settlement_date`, `settlement_period`
- `value2` (energy settled in MWh)
- `system_price` (£/MWh imbalance price, NOT acceptance price)
- `multiplier` (typically 0.5 for half-hour periods)
- `settlement_run` (II/R3/RF - maturity indicator)

**Settlement formula**:
```
revenue_gbp = value2 × system_price × multiplier
```

**For negative energy (curtailment)**:
- Negative `value2` × positive `system_price` = **negative revenue**
- Negative revenue = **generator receives payment**
- Example: `-75 MWh × £95/MWh × 0.5 = -£3,562.50` (generator paid £3,562.50)

### 12.2 Join Keys for BOALF + BOD (BigQuery Field Names)

**Joining BOALF to BOD**:
```sql
FROM bmrs_boalf boalf
LEFT JOIN bmrs_bod bod
  ON boalf.bmUnitId = bod.bmUnitId
  AND boalf.settlementDate = bod.settlementDate
  AND boalf.settlementPeriod = bod.settlementPeriod
  -- AND boalf.bidOfferPairId = bod.pairId  -- If pair tracking available
WHERE boalf.acceptanceType = 'BID'
  AND bod.bid IS NOT NULL  -- Get bid price for BID acceptances
```

**Note**: BigQuery table field names may differ from Elexon API:  
- API: `bmUnitID` → BigQuery: `bmUnitId`  
- API: `settlementPeriod` → BigQuery: `settlementPeriod` (consistent)  
- BOD pair matching may require additional logic if multiple pairs exist

### 12.3 What P114 Can and Cannot Evidence

**✅ P114 CAN evidence**:

1. **What was entered into Settlement** for acceptances (including NGSEA constructed acceptances) and resulting settlement outputs/cashflows as calculated by SAA (Section T) *(BSC Section T)*

2. **NGSEA acceptances treated as bids** in settlement mechanics:  
   > "A Network Gas Supply Emergency Acceptance will always be a Bid." *(BSCP18)*

3. **Post-event committee drove changes** to settlement inputs (FPN/Bid Prices/Acceptance Data):  
   > "Committee may direct changes to FPNs, Bid-Offer Data and/or Acceptance Data." *(BSCP18)*

4. **Settlement run progression** (II → R3 → RF) shows data maturity and corrections

5. **Negative revenue = generator paid** (settlement accounting convention)

**❌ P114 CANNOT evidence**:

1. **Real-world commercial arrangements**:  
   - Does NOT prove underlying "deal" interpretation (e.g., "they keep the gas and can sell it")  
   - Settlement records are settlement artefacts, NOT gas commercial contracts  
   - Cannot show contractual makeup of compensation

2. **Causal operational trigger** without joining to explicit NGSEA markers:  
   - P114 line item doesn't carry "this happened because of gas LSI" flag  
   - NGSEA process = constructed acceptances + committee governance (procedural, not flagged in every settlement record) *(P448)*

3. **Acceptance prices vs settlement prices**:  
   - P114 `system_price` = imbalance price (SBP/SSP, system-wide marginal)  
   - Acceptance price (from BOD matching) may differ  
   - P114 shows **settlement outcome**, not operational acceptance price

4. **Why specific bid price was chosen** during NGSEA construction:  
   - Committee decision-making not visible in P114 data  
   - May require BSCP18 change requests or committee minutes

### 12.4 Recommended Analysis Approach

**For operational understanding**:  
→ Use BOALF + BOD (Level 1) to see accepted actions and indicative prices

**For settlement verification**:  
→ Use P114 (Level 2) as authoritative source for settled outcomes

**For NGSEA detection**:  
→ Combine both: BOALF SO-Flag + P114 negative energy + NESO constraint cost datasets

**For cashflow reconciliation**:  
→ Expect differences between Level 1 (operational estimate) and Level 2 (SAA-settled)

---

*Created: 28 December 2025*  
*Updated: 28 December 2025 - Added P448/BSCP18 clarifications, Level 1/2 cashflow distinction*  
*References: P448 Ofgem Decision, BSCP18, BSC Section Q, BSC Section T, Elexon NGSEA Guidance*  
*Data: 105.25M P114 records (399 days, backfill in progress to 1,096 days), 3.3M BOALF acceptances*  
*Key Finding: NGSEA = post-event constructed acceptances (P448), NOT real-time BOALF flow*  
*Critical: Section T Trading Charges (SAA-settled) ≠ operational BOALF estimates*
