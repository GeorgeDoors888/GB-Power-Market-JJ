# UK Energy Data Architecture Guide
# Complete Field Definitions, Data Grains, and Analysis Patterns

**Generated:** 2025-12-29
**Dataset:** inner-cinema-476211-u9.uk_energy_prod (308 tables, 1.38B rows, 470.5 GB)
**Purpose:** Authoritative reference for data structure, field semantics, and valid analysis patterns

---

## Table of Contents

1. [Field Type Taxonomy](#field-type-taxonomy)
2. [Data Grain Definitions](#data-grain-definitions)
3. [Dataset Families](#dataset-families)
4. [Valid Analysis Patterns](#valid-analysis-patterns)
5. [Common Traps & Solutions](#common-traps--solutions)
6. [BMU Reference Model](#bmu-reference-model)
7. [Settlement vs Operational Data](#settlement-vs-operational-data)
8. [Geographic & Network Data](#geographic--network-data)

---

## 1. Field Type Taxonomy

### A️⃣ Identity Fields (WHAT / WHO)

Used to identify the subject of the record.

| Field | Meaning | Join Key |
|-------|---------|----------|
| `bmUnitId` | Balancing Mechanism Unit ID | ✅ Primary |
| `partyId` | BSC Party / Lead Party | ✅ Secondary |
| `boundary` | Constraint or transmission boundary | ✅ Geographic |
| `gspGroup` | Grid Supply Point Group | ✅ Regional |
| `zone` | Geographic / market zone | ✅ Geographic |

**Critical:** These are join keys to reference data. Always validate against `dim_bmu`, `dim_party`, `neso_dno_reference`.

---

### B️⃣ Time Fields (WHEN)

Elexon/NESO always include explicit time, often more than one.

| Type | Format | Context |
|------|--------|---------|
| `timeFrom`, `timeTo` | ISO-8601 UTC | Operational time |
| `startTime`, `endTime` | ISO-8601 UTC | NESO constraints |
| `settlementDate` | YYYY-MM-DD | BSC settlement day |
| `settlementPeriod` | 1–48 | Half-hour index |
| `acceptanceTime` | ISO-8601 UTC | BM acceptance timestamp |

**Rule:**
- If `settlementDate`/`Period` exists → settlement-aligned data
- If only timestamps exist → you must derive SP yourself

**Settlement Period Conversion:**
```sql
-- UTC timestamp to Settlement Period
EXTRACT(HOUR FROM timestamp) * 2 +
CASE WHEN EXTRACT(MINUTE FROM timestamp) >= 30 THEN 2 ELSE 1 END
```

---

### C️⃣ Quantities (PHYSICAL VALUES)

Always numeric, always unit-specific.

| Field | Typical Units | Notes |
|-------|---------------|-------|
| `acceptedVolume` | MW | Instantaneous power |
| `energy` / `value2` | MWh | Energy delivered |
| `volumeMW` | MW | Power level |
| `generationCapacity` | MW | Max export capability |
| `demandCapacity` | MW | Max import capability |
| `constraintVolume` | MW | Network constraint magnitude |

**Critical:**
- MW ≠ MWh
- Settlement uses MWh = MW × 0.5 (half-hour periods)
- Negative values have meaning (bid/offer direction)

---

### D️⃣ Prices / Costs (FINANCIAL VALUES)

| Field | Units | Mechanism |
|-------|-------|-----------|
| `price` | £/MWh | Pay-as-bid (BOALF) |
| `systemPrice` | £/MWh | Imbalance settlement (SSP/SBP) |
| `costGBP` | £ | NESO constraint cost |
| `revenue` | £ | Derived |

**Never assume prices are settlement prices unless explicitly stated (e.g., P114).**

**SSP/SBP Note:**
- Since Nov 2015 (BSC Mod P305): SSP = SBP (single imbalance price)
- Both columns exist for backward compatibility
- Battery arbitrage is **temporal** (charge low, discharge high), not SSP/SBP spread

---

### E️⃣ Flags & Qualifiers (HOW / WHY)

Essential for correct interpretation.

| Field | Values | Meaning |
|-------|--------|---------|
| `bidOfferIndicator` | BID / OFFER | Direction of action |
| `soFlag` | TRUE / FALSE | System Operator initiated |
| `bmUnitType` | Primary / Secondary | BMU classification |
| `fuelType` | GAS / WIND / BATTERY / etc. | Generation technology |
| `fpnFlag` | TRUE / FALSE | Participates in BM |
| `reasonCode` | Various | NESO constraint cause |

---

## 2. Data Grain Definitions

### BOALF Grain (Balancing Acceptances)

**One row ≈ one acceptance event (or one acceptance slice)**

✅ **What you CAN analyze:**
- How many acceptances
- Volumes and prices accepted
- Events by unit, by time
- Pay-as-bid cashflows (needs acceptance MW + acceptance price + duration logic)

❌ **What you CANNOT treat as:**
- Settlement truth (that's P114)

**Example canonical record:**
```json
{
  "bmUnitId": "T_KEAD-2",
  "settlementDate": "2024-03-01",
  "settlementPeriod": 12,
  "acceptanceTime": "2024-03-01T11:37:00Z",
  "acceptedVolume": -150,  // MW (negative = toward demand)
  "price": -75,  // £/MWh (pay-as-bid)
  "bidOfferIndicator": "BID",
  "soFlag": true,
  "fuelType": "GAS"
}
```

**From this you CAN say:**
- A BID was accepted
- MW movement was toward demand
- Pay-as-bid compensation applies

**From this you CANNOT say:**
- Settlement revenue
- Generator profit
- Demand vs generation without GC/DC

---

### P114 Grain (Settlement)

**One row ≈ one settlement output record (BMU × SP × run × component)**

✅ **What you CAN analyze:**
- Settlement energy and charges
- Final vs initial settlement changes
- "Who got paid when" in settlement terms

❌ **What you CANNOT compute:**
- Pay-as-bid acceptance amounts directly (must join to BOALF)
- Operational why (that's BOALF/BOD context)

**Runs:**
- `II` = Initial (indicative, not binding)
- `SF` = Settlement Final (binding)
- `R1/R2/R3` = Reconciliation runs (adjustments)
- `RF` = Reconciliation Final (last word)

---

### Constraint Breakdown Grain (NESO)

**One row ≈ one boundary/time interval cost or volume**

✅ **What you CAN analyze:**
- Where/when the network was constrained
- Costs by boundary, region, season
- Correlation with price spikes

❌ **What you CANNOT attribute:**
- Directly to a single generator (needs flow attribution model)

---

## 3. Dataset Families

### 3.1 BMRS Operational (BOD / BOALF / PN / FPN etc.)

**Tables:** `bmrs_bod`, `bmrs_boalf`, `bmrs_pn`, `bmrs_qpn`, `bmrs_ebocf`, etc.

**What it represents:**
- What the System Operator and units did operationally
- The bid/offer stacks (BOD)
- The acceptances/instructions (BOALF)

**Valid Analysis:**
✅ Balancing intensity over time (acceptances per SP, per day)
✅ Volumes accepted by BMU, fuel, party
✅ Pay-as-bid cashflows (needs acceptance MW + acceptance price + duration logic)
✅ Event detection: "system stress" windows (SO-Flag spikes, extreme pricing, ramp events)
✅ Unit behaviour: response speed, typical offer curves, bid/offer spread
✅ VLP behaviour: frequency of actions, unusual acceptances

**Key Joins:**
- BOALF ↔ BOD by (bmUnitId, time/settlement keys, pairId/offerId where present)
- BMU ↔ reference (bmUnit attributes, fuel, lead party)

**Cannot Provide:**
❌ Final "who paid whom" settlement truth (that's P114)

---

### 3.2 P114 Settlement (SAA Outputs)

**Tables:** `elexon_p114_s0142_bpi`, `elexon_p114_s0155_sagd`, etc.

**What it represents:**
- Settlement outputs produced by the SAA
- Multiple settlement runs: II, SF, R1/R2/R3, RF
- Settlement components (energy, imbalance prices, charges)

**Valid Analysis:**
✅ Settlement revenue/cost by BMU, party, day, SP
✅ Volatility and re-runs (II vs RF differences)
✅ "Which units get paid in settlement and when?"
✅ VLP presence and settlement revenue
✅ Structural anomaly detection: negative energy patterns, outliers, missing units, run gaps

**Key Joins:**
- P114 ↔ BMU reference by `bmUnitId`
- P114 ↔ BOALF for comparison (but not equivalence)

**Cannot Prove:**
❌ The pay-as-bid acceptance payment amounts directly
❌ Why an event happened operationally
❌ A specific SO reason (unless encoded elsewhere)

---

### 3.3 GC/DC (Generation Capacity / Demand Capacity)

**Tables:** `bmu_registration_data`, `bmu_metadata`, `dim_bmu`

**What it represents:**
- Declared maximum expected export/import per BMU for the season

**Valid Analysis:**
✅ Identify violations: where P114 settled energy exceeds expected max envelope
✅ Validate BOALF acceptances: did acceptances imply export/import beyond GC/DC?
✅ Seasonal structural changes: who changes capability envelope each season
✅ Classify units better: bidirectional vs gen-only vs demand-only
✅ Detect mis-registered / incorrectly categorized BMUs

---

### 3.4 NESO Constraints + Boundaries

**Tables:** `neso_constraint_breakdown_*`, `neso_dno_boundaries`, `neso_dno_reference`

**What it represents:**
- Network boundaries under constraint
- Costs and volumes of constraint management
- GIS boundaries for DNO regions

**Valid Analysis:**
✅ Constraint costs by region/boundary over time
✅ Seasonal/diurnal constraint patterns
✅ Correlation with system price spikes, balancing acceptances spikes, fuel mix changes
✅ Geographic heatmaps: which DNO regions are systematically stressed

**Key Joins:**
- Constraint point (lat/long or boundary ID) ↔ Geo boundaries (ST_WITHIN joins)
- Boundary ↔ constraint costs summary

**Cannot Claim:**
❌ "Generator X caused this boundary constraint" (needs flow attribution)

---

### 3.5 IRIS Real-Time Data

**Tables:** `bmrs_*_iris` (e.g., `bmrs_fuelinst_iris`, `bmrs_freq_iris`)

**What it represents:**
- "Near live" / streaming view of BMRS signals
- Last 24-48 hours typically

**Valid Analysis:**
✅ Intraday system stress dashboards
✅ Near-live anomaly detection
✅ Operational event windows and rapid response indicators

**Limitations:**
- Not always complete historical depth
- Some fields differ from historical snapshots
- Use UNION with historical tables for complete time series

---

## 4. Valid Analysis Patterns

### Pattern 1: Complete Time Series (Historical + Real-Time)

```sql
-- Always UNION historical + real-time for full coverage
WITH combined AS (
  SELECT
    CAST(settlementDate AS DATE) as date,
    settlementPeriod,
    generation,
    fuelType
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst`
  WHERE settlementDate < CURRENT_DATE() - 2  -- Historical cutoff

  UNION ALL

  SELECT
    CAST(settlementDate AS DATE) as date,
    settlementPeriod,
    generation,
    fuelType
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_fuelinst_iris`
  WHERE settlementDate >= CURRENT_DATE() - 2  -- Real-time overlap
)
SELECT * FROM combined ORDER BY date, settlementPeriod
```

### Pattern 2: Pay-as-Bid Revenue (BOALF + Prices)

```sql
-- Use bmrs_boalf_complete for acceptance prices
SELECT
  bmUnitId,
  DATE(acceptanceTime) as date,
  SUM(acceptanceVolume * acceptancePrice * 0.5) as revenue_gbp,  -- MW * £/MWh * 0.5h
  COUNT(*) as acceptance_count
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_complete`
WHERE validation_flag = 'Valid'  -- Only validated records (42.8% pass rate)
  AND acceptanceTime >= '2025-10-01'
GROUP BY bmUnitId, date
ORDER BY revenue_gbp DESC
```

### Pattern 3: Settlement vs Operational Comparison

```sql
-- Join P114 settlement to BOALF acceptances
SELECT
  p.bm_unit_id,
  p.settlement_date,
  p.settlement_period,
  p.value2 as settlement_energy_mwh,  -- P114: settlement truth
  SUM(b.acceptanceVolume * 0.5) as accepted_energy_mwh,  -- BOALF: operational
  ABS(p.value2 - SUM(b.acceptanceVolume * 0.5)) as variance_mwh
FROM `inner-cinema-476211-u9.uk_energy_prod.elexon_p114_s0142_bpi` p
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` b
  ON p.bm_unit_id = b.bmUnitId
  AND p.settlement_date = b.settlementDate
  AND p.settlement_period = b.settlementPeriod
WHERE p.settlement_run = 'SF'  -- Settlement Final only
GROUP BY p.bm_unit_id, p.settlement_date, p.settlement_period, p.value2
HAVING variance_mwh > 10  -- Flag significant variances
```

### Pattern 4: Constraint Cost Geographic Aggregation

```sql
-- Aggregate constraint costs by DNO region
SELECT
  d.dno_name,
  d.region,
  EXTRACT(YEAR FROM c.startTime) as year,
  EXTRACT(MONTH FROM c.startTime) as month,
  COUNT(*) as constraint_events,
  SUM(CAST(c.totalCost AS FLOAT64)) as total_cost_gbp,
  AVG(CAST(c.volume AS FLOAT64)) as avg_volume_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_constraint_breakdown_2024` c
JOIN `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference` d
  ON c.boundary LIKE CONCAT('%', d.dno_id, '%')
GROUP BY d.dno_name, d.region, year, month
ORDER BY total_cost_gbp DESC
```

---

## 5. Common Traps & Solutions

### Trap 1: Confusing Pay-as-Bid with Settlement

❌ **Wrong:** Using BOALF prices as settlement revenue
✅ **Right:** BOALF = operational acceptance price, P114 = settlement outcome

**Solution:** Join both datasets for complete picture:
- BOALF → "what SO paid immediately"
- P114 → "what was settled later"
- Difference = reconciliation adjustments

### Trap 2: MW vs MWh Confusion

❌ **Wrong:** Treating `acceptedVolume` (MW) as energy
✅ **Right:** Energy = MW × Duration (0.5 hours for settlement periods)

**Formula:**
```sql
acceptedVolume * 0.5 AS energy_mwh  -- MW * 0.5h = MWh
```

### Trap 3: SSP = SBP Misinterpretation

❌ **Wrong:** "SSP = SBP means system is balanced"
✅ **Right:** Single-price period (P305 since Nov 2015), often indicates system stress

**Battery Strategy:** SSP=SBP periods collapse risk asymmetry → highest arbitrage value

### Trap 4: Ignoring SO-Flag

❌ **Wrong:** Counting all acceptances as "market signals"
✅ **Right:** `soFlag=TRUE` → System Operator initiated (reliability/constraint), not pure market

**Filter:**
```sql
WHERE soFlag = FALSE  -- Pure market-driven acceptances only
```

### Trap 5: Missing IRIS Data for Recent Periods

❌ **Wrong:** Querying only historical tables for today's data
✅ **Right:** UNION historical + `_iris` tables for complete coverage

**Solution:** See Pattern 1 above

---

## 6. BMU Reference Model

### Canonical BMU Reference Query

```sql
CREATE OR REPLACE TABLE mart.ref_bmu_canonical AS
WITH latest_reg AS (
  SELECT
    elexonbmunit AS bm_unit_id,
    ANY_VALUE(leadpartyid) AS lead_party_id,
    ANY_VALUE(leadpartyname) AS lead_party_name,
    ANY_VALUE(fueltype) AS fuel_type_reg,
    ANY_VALUE(CAST(generationcapacity AS FLOAT64)) AS generation_capacity_mw,
    ANY_VALUE(CAST(demandcapacity AS FLOAT64)) AS demand_capacity_mw,
    ANY_VALUE(fpnflag) AS fpn_flag,
    ANY_VALUE(gspgroupid) AS gsp_group_id
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmu_registration_data`
  GROUP BY bm_unit_id
)
SELECT
  b.bm_unit_id,
  COALESCE(b.lead_party_name, r.lead_party_name) AS lead_party_name,
  COALESCE(b.fuel_type, r.fuel_type_reg) AS fuel_type,
  COALESCE(b.generation_capacity_mw, r.generation_capacity_mw) AS generation_capacity_mw,
  COALESCE(b.demand_capacity_mw, r.demand_capacity_mw) AS demand_capacity_mw,

  -- Classification
  CASE
    WHEN b.is_vlp THEN 'VLP'
    WHEN b.is_vtp THEN 'VTP'
    WHEN b.is_interconnector_unit THEN 'Interconnector'
    WHEN COALESCE(b.generation_capacity_mw, 0) > 0
     AND COALESCE(b.demand_capacity_mw, 0) = 0 THEN 'Generator'
    WHEN COALESCE(b.demand_capacity_mw, 0) > 0
     AND COALESCE(b.generation_capacity_mw, 0) = 0 THEN 'Demand'
    WHEN COALESCE(b.generation_capacity_mw, 0) > 0
     AND COALESCE(b.demand_capacity_mw, 0) > 0 THEN 'Bidirectional (BESS/Hybrid)'
    ELSE 'Other'
  END AS party_capacity_type,

  b.is_battery_storage,
  b.gsp_group,
  b.fpn_flag,
  CURRENT_TIMESTAMP() AS loaded_at
FROM `inner-cinema-476211-u9.uk_energy_prod.dim_bmu` b
LEFT JOIN latest_reg r ON b.bm_unit_id = r.bm_unit_id;
```

---

## 7. Settlement vs Operational Data

### Key Differences

| Aspect | BOALF (Operational) | P114 (Settlement) |
|--------|---------------------|-------------------|
| **Purpose** | SO instructions | BSC settlement |
| **Price Type** | Pay-as-bid | Imbalance settlement |
| **Timing** | Real-time | Days/weeks later |
| **Authority** | Operational only | Legally binding |
| **Reconciliation** | No | Yes (II→SF→R1→RF) |

### When to Use Which

**Use BOALF for:**
- BM activity analysis
- Pay-as-bid revenue estimation
- Event detection (stress periods)
- Unit behavior patterns

**Use P114 for:**
- Settlement revenue truth
- Imbalance exposure analysis
- Reconciliation tracking
- Financial reporting

**Use Both (Joined) for:**
- Variance analysis
- Settlement vs operational comparison
- Revenue validation

---

## 8. Geographic & Network Data

### DNO Reference (14 Regions)

```sql
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`
```

**Contains:**
- DNO ID (01-29)
- DNO Name (e.g., "UKPN-EPN Eastern")
- Region boundaries (GeoJSON where available)
- DUoS rate references

### Creating Geographic Visualizations

**For Google Sheets Geo Chart:**
1. Aggregate data by DNO name/region
2. Export to Sheets with columns: [Region, Value]
3. Insert → Chart → Geo chart
4. Customize → Set region to "United Kingdom"
5. Color scale: min=green, max=red

**Example Data Structure:**
```
Region              | Total Cost (£)
--------------------|---------------
UKPN-EPN Eastern    | 1,234,567
NGED West Midlands  | 987,654
SPEN Manweb         | 765,432
```

---

## Appendix: P246 LLF Exclusions

Line Loss Factor (LLF) exclusions by GSP Group (P246 modification):
- 14 GSP Groups (_A through _P, excluding _I and _O)
- Last modified: 27/01/2012
- Reference: BSC Website → Settlement → Technical Specifications → P246

---

## Document Maintenance

**Last Updated:** 2025-12-29
**Maintained By:** George Major (george@upowerenergy.uk)
**Source Dataset:** inner-cinema-476211-u9.uk_energy_prod
**Version:** 1.0

**Change Log:**
- 2025-12-29: Initial comprehensive guide created from user specifications
