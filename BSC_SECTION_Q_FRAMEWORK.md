# BSC Section Q Framework: Settlement Data Architecture

## Document Purpose

This guide explains the Balancing Settlement Code (BSC) Section Q framework that defines:
- What balancing data exists
- Who submits it
- How acceptances/instructions are represented
- Data flows from operational systems → BMRA/SAA → settlement outputs

**Critical for understanding**: How operational balancing actions (BM instructions) become settlement data (P114 outputs).

---

## Executive Summary

**Section Q** is the BSC section that governs Balancing Mechanism (BM) data submission and defines what counts as BM data for settlement purposes.

### The Data Journey

```
Operational Action (Grid Code)
    ↓
Section Q Definition (BSC)
    ↓
BMRA Publication (BOAL/BOALF)
    ↓
SAA Settlement Processing
    ↓
P114 Settlement Outputs
```

---

## Part 1: BSC Section Q Core Framework

### 1.1 What is Section Q?

**BSC Section Q** defines:
- Physical Notifications (PN/FPN) - generation/demand forecasts
- Bid-Offer Data (BOD) - prices at which units will change output
- Acceptance Data (BOAL/BOALF) - SO instructions to units
- BSAD (Balancing Services Adjustment Data) - non-BM balancing services
- Data submission requirements to BMRA (publication) and SAA (settlement)

**Key Reference Documents**:
- BSC Section Q (full legal text)
- Section Q Simple Guide (plain English companion)
- BMRA Service Description (publication layer)
- Balancing Mechanism Assurance Report (NESO/NETSO obligations)

### 1.2 Physical Notifications (PN/FPN)

**What they are**: BM Unit forecasts of energy production/consumption submitted by Lead Parties.

**Types**:
- **PN (Physical Notification)**: Initial forecast, submitted before gate closure
- **FPN (Final Physical Notification)**: Updated forecast, can be revised up to gate closure

**Why they matter**:
- Baseline for imbalance calculation (actual vs. FPN)
- Required for settlement processing
- Can be corrected post-event (e.g., after gas emergencies via BSCP18)

**Data location**:
- BMRS API: FPN endpoint
- P114 settlement: Used to calculate imbalance volumes

### 1.3 Bid-Offer Data (BOD)

**What it is**: Price-quantity pairs submitted by BM Units indicating:
- **Bids**: Price to decrease output (£/MWh)
- **Offers**: Price to increase output (£/MWh)

**Structure**:
- Pair ID (links bid to offer)
- Price (£/MWh)
- Volume (MW)
- Time period (settlement period)

**Data location**:
- `bmrs_bod`: Historical bid-offer submissions (439M+ records)
- Used to match acceptance prices in `bmrs_boalf_complete`

**Key concept**: Generators submit bids/offers; NESO accepts them to balance the grid.

### 1.4 Acceptance Data (BOAL/BOALF)

**Definition** (Elexon Glossary):
> "A Bid-Offer Acceptance is the formalised representation of the purchase/sale of bids/offers by the System Operator operating the BM, shown as MW at start and end time (and intermediate points if needed)."

**Types**:
- **BOAL (Bid-Offer Acceptance Level)**: Basic acceptance data (MW, time)
- **BOALF (Bid-Offer Acceptance Level Flagged)**: Enhanced with SO-Flag, prices, volumes

**Critical Field: SO-Flag**:
- Indicates acceptances taken for reasons **other than balancing short-term energy imbalance**
- Examples: System security, voltage control, gas emergency curtailment
- Used to identify special events (like NGSEA)

**Bid-Offer Acceptance Time** (Section Q):
> "For a Bid-Offer Acceptance or Emergency Instruction, the time the communication was issued by NETSO."

**Data location**:
- BMRS API: BOALF endpoint (operational data, published within minutes)
- `bmrs_boalf`: Raw acceptance data from BMRS
- `bmrs_boalf_complete`: Enhanced with prices matched from BOD
- `boalf_with_prices`: View of validated acceptances only (42.8% pass Elexon B1610 filters)

---

## Part 2: Section Q → Settlement Data Flow

### 2.1 NETSO (NESO) Obligations Under Section Q

**Requirements**:
1. Submit BM data to **BMRA** (for publication via BMRS/Insights)
2. Submit BM data to **SAA** (for settlement processing)
3. Include: FPN, BOD, BOAL, and special event flags

**What this means**: Every operational BM action must be captured and submitted to both systems.

### 2.2 BMRA (Balancing Mechanism Reporting Agent)

**Purpose**: Transparency layer - publishes operational BM data in near real-time.

**What it publishes**:
- BOALF (acceptances with flags)
- FPN (generation forecasts)
- BOD (bid-offer pairs)
- System prices (SBP/SSP, now unified as System Price)
- Imbalance volumes

**API Access**:
- Elexon BMRS API (legacy)
- Elexon Insights API (modern, used in this project)
- Data available: T+5 minutes to T+30 minutes after event

**Data in this project**:
- `bmrs_boalf`: BOALF acceptances
- `bmrs_bod`: Bid-offer data
- `bmrs_costs`: System prices (SBP/SSP unified since Nov 2015 P305)

### 2.3 SAA (Settlement Administration Agent)

**Purpose**: Settlement calculation engine - processes BM data to produce final settlement runs.

**What it does**:
- Calculates imbalance volumes (FPN vs. actual metered)
- Applies acceptance data to determine energy settled
- Calculates system prices (imbalance price calculation)
- Produces settlement outputs: II → R3 → RF runs

**Settlement Run Progression**:
- **II (Initial)**: T+1 day (preliminary)
- **R1 (1st Reconciliation)**: T+28 days
- **R2 (2nd Reconciliation)**: T+55 days
- **R3 (3rd Reconciliation)**: T+~14 months
- **RF (Final Reconciliation)**: T+~28 months (most accurate)

**Why runs change**: Meter data updates, FPN corrections (BSCP18), acceptance data corrections.

**Data in this project**:
- `elexon_p114_s0142_bpi`: SAA settlement outputs (59.69M records, 219 days)
- `p114_settlement_canonical`: Deduplication view (RF > R3 > II priority)
- `mart_vlp_revenue_p114`: VLP settlement revenue view

---

## Part 3: Data Object Definitions

### 3.1 Physical Notifications

| Field | Description | Source |
|-------|-------------|--------|
| bmUnitId | BM Unit identifier | Lead Party |
| settlementPeriod | Half-hour period (1-48) | System |
| levelFrom | FPN start level (MW) | Lead Party |
| levelTo | FPN end level (MW) | Lead Party |
| timeFrom | Start time | Lead Party |
| timeTo | End time | Lead Party |

**Correction mechanism**: BSCP18 (e.g., after gas emergencies)

### 3.2 Bid-Offer Data (BOD)

| Field | Description | Example |
|-------|-------------|---------|
| bmUnitId | BM Unit | T_DRAXX-1 |
| settlementDate | Date | 2024-10-17 |
| settlementPeriod | Period (1-48) | 36 |
| pairId | Bid-offer pair ID | 12345 |
| bid | Bid price (£/MWh) | -50.00 |
| offer | Offer price (£/MWh) | 85.00 |
| bidVolume | Bid volume (MW) | 100 |
| offerVolume | Offer volume (MW) | 150 |

**Key concept**: 
- Negative bid = paid to reduce output (curtailment)
- Positive offer = paid to increase output

### 3.3 Acceptance Data (BOAL/BOALF)

| Field | Description | Example |
|-------|-------------|---------|
| bmUnitId | BM Unit | T_KEAD-2 |
| acceptanceNumber | Unique ID | ACC_12345 |
| acceptanceTime | Time issued | 2024-10-17 17:28:00 |
| settlementPeriod | Period | 36 |
| levelFrom | Start MW | 350 |
| levelTo | End MW | 400 |
| acceptanceType | BID/OFFER | OFFER |
| soFlag | Special event flag | FALSE |

**SO-Flag Values** (BMRS Market View):
- FALSE: Normal balancing
- TRUE: Taken for reasons other than short-term energy imbalance (system security, voltage, **gas emergency**)

### 3.4 P114 Settlement Data (S0142 BPI)

| Field | Description | Example |
|-------|-------------|---------|
| bm_unit_id | BM Unit | FBPGM002 |
| settlement_date | Date | 2024-10-17 |
| settlement_period | Period (1-48) | 36 |
| settlement_run | II/R3/RF | RF |
| system_price | Settlement price (£/MWh) | 83.73 |
| value2 | Energy settled (MWh) | 1.36 |
| multiplier | Period multiplier | 0.5 |

**Revenue calculation**: `value2 × system_price × multiplier`

---

## Part 4: Operational → Settlement Data Journey

### Example: Gas Generator Accepted Offer

**Step 1: Generator submits BOD**
```
bmUnitId: T_KEAD-2
settlementPeriod: 36
offer: £85.00/MWh
offerVolume: 50 MW
```

**Step 2: NESO accepts offer (Grid Code)**
```
NESO issues instruction to T_KEAD-2:
"Increase output by 50 MW for period 36"
```

**Step 3: Section Q converts to BM data**
```
Acceptance created:
- acceptanceType: OFFER
- levelFrom: 350 MW → levelTo: 400 MW
- acceptanceTime: 17:28:00
- soFlag: FALSE (normal balancing)
```

**Step 4: BMRA publishes (BOALF)**
```
Published to BMRS/Insights API within 5-30 minutes
Visible in bmrs_boalf table
```

**Step 5: SAA processes for settlement**
```
Calculates energy settled:
- Delta MW: 50 MW
- Duration: 0.5 hours
- Energy: 25 MWh
- Price: £85.00/MWh (from BOD match)
- Settlement value: 25 × 85 × 0.5 = £1,062.50
```

**Step 6: P114 output**
```
elexon_p114_s0142_bpi record:
- bm_unit_id: T_KEAD-2
- settlement_period: 36
- value2: 25.0 (MWh)
- system_price: 83.73 (system-wide price, not acceptance price)
- settlement_run: II (initial), later updated to R3, then RF
```

---

## Part 5: Data Relationships

### 5.1 BOD → BOALF → P114 Lineage

```sql
-- Find acceptance with price
SELECT 
    boalf.bmUnitId,
    boalf.acceptanceNumber,
    boalf.acceptanceTime,
    boalf.acceptanceType,
    boalf.soFlag,
    bod.bid,
    bod.offer,
    p114.system_price,
    p114.value2 as energy_mwh
FROM bmrs_boalf boalf
LEFT JOIN bmrs_bod bod 
    ON boalf.bmUnitId = bod.bmUnitId 
    AND boalf.settlementDate = bod.settlementDate
    AND boalf.settlementPeriod = bod.settlementPeriod
LEFT JOIN elexon_p114_s0142_bpi p114
    ON boalf.bmUnitId = p114.bm_unit_id
    AND boalf.settlementDate = p114.settlement_date
    AND boalf.settlementPeriod = p114.settlement_period
WHERE boalf.settlementDate = '2024-10-17'
  AND boalf.settlementPeriod = 36
```

### 5.2 Why Prices Differ

**BOD Price** (acceptance price): What NESO paid for THIS SPECIFIC acceptance
- Example: £85.00/MWh for T_KEAD-2 offer

**System Price** (P114): Marginal price across ALL BM actions in the period
- Example: £83.73/MWh (system-wide imbalance price)

**Implication**: 
- Generators/demand see individual acceptance prices (BOD-derived)
- Settlement uses system price (P114)
- Difference can be profit/loss vs. offer/bid price

---

## Part 6: Key BSC Documents Reference

### 6.1 Section Q Documents

**BSC Section Q** (full legal text)
- Location: Elexon Digital BSC
- Covers: PN, FPN, BOD, BOAL, BSAD definitions
- Status: Legally binding under BSC

**Section Q Simple Guide**
- Purpose: Plain English companion
- Explains: What counts as "Acceptance", data requirements
- Useful for: Quick understanding without legal text

### 6.2 Related Documents

**BMRA Service Description**
- Explains BMRS service scope
- What data is published/hosted
- API endpoints and access

**Balancing Mechanism Assurance Report** (NESO)
- Ties BSC obligations to operational reality
- States Section Q requires NETSO (NESO) to submit data to BMRA/SAA
- Audit-grade understanding of required data feeds

**BSCP18** (Corrections to Bid-Offer Acceptance Related Data)
- Correction mechanism for FPN, BOD, BOAL
- Covers: Network Gas Supply Emergency Acceptances
- Generation Curtailment Validation Committee review
- How corrected data lands in subsequent settlement runs

---

## Part 7: Data Sources in This Project

### 7.1 BMRS Operational Data

| Table | Description | Records | Coverage |
|-------|-------------|---------|----------|
| `bmrs_boalf` | Acceptances | 3.3M | 2022-2025 |
| `bmrs_boalf_complete` | With matched prices | 11M | 2022-2025 |
| `boalf_with_prices` | Validated only (42.8%) | 4.7M | 2022-2025 |
| `bmrs_bod` | Bid-offer data | 439M | 2020-2025 |
| `bmrs_costs` | System prices | 191k | 2016-2025 |

### 7.2 P114 Settlement Data

| Table/View | Description | Records | Coverage |
|------------|-------------|---------|----------|
| `elexon_p114_s0142_bpi` | Raw settlement | 59.69M | Oct 2021 - Oct 2024 (219 days) |
| `p114_settlement_canonical` | Deduplication (RF>R3>II) | 0 (needs refresh) | Same |
| `mart_vlp_revenue_p114` | VLP revenue view | 0 (needs refresh) | Same |

**Note**: Canonical view empty = needs refresh after backfill completion.

---

## Part 8: Query Patterns

### 8.1 Find All Acceptances for a Unit/Period

```sql
-- BOALF (operational data)
SELECT 
    acceptanceNumber,
    acceptanceTime,
    acceptanceType,
    soFlag,
    levelFrom,
    levelTo
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
WHERE bmUnitId = 'T_KEAD-2'
  AND settlementDate = '2024-10-17'
  AND settlementPeriod = 36
ORDER BY acceptanceTime
```

### 8.2 Match Acceptance with BOD Prices

```sql
-- Use pre-matched table
SELECT 
    bm_unit_id,
    acceptance_number,
    acceptance_type,
    acceptance_price,  -- From BOD match
    acceptance_volume,
    revenue_estimate_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.boalf_with_prices`
WHERE bm_unit_id = 'T_KEAD-2'
  AND settlement_date = '2024-10-17'
  AND settlement_period = 36
  AND validation_flag = 'Valid'
```

### 8.3 Compare BOALF → P114 Settlement

```sql
-- Acceptance price vs. settlement price
WITH boalf_data AS (
    SELECT 
        bm_unit_id,
        settlement_date,
        settlement_period,
        SUM(acceptance_volume) as boalf_mwh,
        AVG(acceptance_price) as avg_acceptance_price
    FROM boalf_with_prices
    WHERE validation_flag = 'Valid'
    GROUP BY 1,2,3
),
p114_data AS (
    SELECT 
        bm_unit_id,
        settlement_date,
        settlement_period,
        SUM(value2) as p114_mwh,
        AVG(system_price) as system_price
    FROM elexon_p114_s0142_bpi
    WHERE settlement_run = 'RF'
    GROUP BY 1,2,3
)
SELECT 
    b.bm_unit_id,
    b.settlement_date,
    b.settlement_period,
    b.boalf_mwh,
    b.avg_acceptance_price,
    p.p114_mwh,
    p.system_price,
    b.boalf_mwh - p.p114_mwh as volume_difference,
    b.avg_acceptance_price - p.system_price as price_difference
FROM boalf_data b
LEFT JOIN p114_data p USING (bm_unit_id, settlement_date, settlement_period)
WHERE b.settlement_date = '2024-10-17'
  AND b.settlement_period = 36
ORDER BY ABS(b.boalf_mwh - p.p114_mwh) DESC
LIMIT 20
```

---

## Part 9: Summary & Key Takeaways

### 9.1 Critical Concepts

1. **Section Q defines BM data** - operational actions become structured data
2. **Dual submission** - BMRA (transparency) + SAA (settlement)
3. **Acceptance = formalised instruction** - Grid Code action → BSC data object
4. **SO-Flag identifies special events** - gas emergencies, voltage control, etc.
5. **Settlement runs mature** - II (T+1) → R3 (T+14mo) → RF (T+28mo)
6. **Prices differ** - acceptance price (BOD) ≠ system price (P114)

### 9.2 Data Quality Checks

When using P114 + BOALF together:
- ✅ Match by: `bm_unit_id`, `settlement_date`, `settlement_period`
- ✅ Use `settlement_run = 'RF'` for most accurate P114 data
- ✅ Filter `validation_flag = 'Valid'` in `boalf_with_prices` (42.8% pass Elexon B1610)
- ✅ Check `soFlag` for special events (gas emergencies, system security)
- ⚠️ Expect volume differences - P114 includes non-BM adjustments
- ⚠️ Expect price differences - acceptance price vs. system marginal price

### 9.3 When Data Changes

**BOALF**: Published T+5 to T+30 minutes, stable after publication

**P114**: Changes across settlement runs
- **II (T+1)**: Preliminary, ~85-90% accurate
- **R3 (T+14mo)**: High confidence, meter data reconciled
- **RF (T+28mo)**: Final, includes all corrections (BSCP18)

**Why changes occur**:
- Meter data updates
- FPN corrections (BSCP18)
- Acceptance data corrections
- Gas emergency acceptance reviews
- NGSEA validation committee findings

---

## Next Document

See: **`GAS_EMERGENCY_CURTAILMENT_NGSEA_GUIDE.md`** for:
- Network Gas Supply Emergency Acceptances (NGSEA)
- How gas generators are paid to turn down
- BSCP18 correction pathway
- Detection queries for NGSEA events in data
- Negative bids explained

---

*Created: 28 December 2025*  
*References: BSC Section Q, Section Q Simple Guide, BMRA Service Description, Elexon Glossary*  
*Data: inner-cinema-476211-u9.uk_energy_prod (59.69M P114 records, 219 days)*
