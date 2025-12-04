# BESS Revenue Model: Conjunctive vs Mutually Exclusive

## Critical Business Model Question

**When a BESS discharges, does it earn:**

### Option A: Mutually Exclusive (Original Model)
**One revenue stream per discharge action:**
- Discharge FOR arbitrage → Earn wholesale price only
- Discharge FOR PPA → Earn PPA price only  
- Discharge FOR Red DUoS → Earn avoided cost only
- Discharge FOR VLP → Earn balancing payment only

**Result:** £173,328/year (conservative, upper-conservative range)

### Option B: Conjunctive (New Model)  
**Multiple revenue streams per discharge action:**
- Discharge earns → SSP (balancing) + PPA (end-user) + DUoS savings (avoided network)
- All three payments received simultaneously
- Physical energy serves multiple purposes

**Result:** £512,197/year (aggressive range £450-650k)

## The Physical Reality

**What Actually Happens:**

1. **System Operator Perspective:**
   - Sees battery exporting to grid
   - Pays System Sell Price (SSP) for balancing service
   - This helps balance supply/demand on the grid

2. **End-User Perspective:**
   - Consumes energy from battery (if on-site demand exists)
   - Pays PPA price for that consumption
   - Avoids importing from grid

3. **DNO Perspective:**
   - Sees reduced import from grid
   - Customer avoids DUoS charges on that import
   - Network stress reduced

## The Key Question: Can You Stack These?

### Arguments FOR Conjunctive (£512k model):

**✅ Industry Practice:**
- VLP contracts typically include:
  - SSP payment from System Operator
  - Plus PPA revenue if supplying end-user
  - Plus capacity payments
  - Example: Flexitricity VLP batteries earn multiple streams

**✅ Physical Reality:**
- One MWh discharge CAN serve multiple purposes:
  - Helps grid (SO pays SSP)
  - Supplies site (end-user pays PPA)
  - Avoids import (DNO charges not incurred)

**✅ Contract Structure:**
- SO contract: Payment for balancing service (SSP)
- PPA contract: Payment for energy supply (separate agreement)
- DUoS: Avoided charges (tariff savings, not a payment)

**✅ Your Insight:**
- "the revenue from the PPA and other arbitrage e.g. VLP or SO is obtained in conjunction"
- "Vischarge is the virtual lead party"
- Suggests you've seen this in actual VLP data/PDFs

### Arguments AGAINST Conjunctive (£173k model):

**❌ Energy Can't Be in Two Places:**
- If energy goes to end-user, it's not exported to grid
- If exported to grid, end-user doesn't consume it
- Physical impossibility

**❌ Metering Reality:**
- Export meter: Battery → Grid (earns SSP)
- Import meter: Grid → Site (pays DUoS)
- Can't avoid import if you're exporting
- Meters would show this conflict

**❌ Conservative Accounting:**
- Better to underestimate than overestimate
- £173k model is defensible
- £512k model may be optimistic

## Reconciliation: The Hybrid Answer?

**Most Likely Reality:**

### Behind-The-Meter (BTM) BESS Has Unique Advantage:

```
Grid ←→ Battery ←→ Site Load
```

**Scenario 1: Site Has Demand + High SSP**
```
Grid pays SSP (£75/MWh) ← Battery (1 MWh discharge)
                           ↓
                         Site consumes (pays PPA £150/MWh)
                         Avoids import (saves DUoS £176/MWh Red)
```

**In this case, YES - all three revenues apply:**
- SO sees export, pays SSP
- End-user consumes, pays PPA
- No import occurs, DUoS avoided

**Result:** £75 (SSP) + £150 (PPA) + £176 (DUoS) = £401/MWh discharge!

**Scenario 2: No Site Demand + High SSP**
```
Grid pays SSP (£75/MWh) ← Battery (1 MWh export)
Site idle (no consumption)
```

**In this case, only SSP applies:**
- SO sees export, pays SSP
- No end-user consumption (no PPA)
- No import avoided (no DUoS savings)

**Result:** £75/MWh discharge only

### The Correct Model: Conditional Stacking

**Revenue Per Discharge = SSP (always if high) + PPA (if site has demand) + DUoS (if avoids import)**

```python
discharge_revenue = 0

# Always earn SSP when discharging during high price
discharge_revenue += ssp * discharge_mwh * efficiency

# Earn PPA if end-user consumes the energy
if site_demand_mwh > 0:
    ppa_supplied = min(discharge_mwh * efficiency, site_demand_mwh)
    discharge_revenue += ppa_supplied * ppa_price

# Earn DUoS savings if avoided import
if site_demand_mwh > 0:
    avoided_import = min(discharge_mwh * efficiency, site_demand_mwh)
    discharge_revenue += avoided_import * (duos_rate + levies)
```

## Validation Required

**To confirm which model is correct, check:**

1. **VLP Contract Terms:**
   - Does Flexitricity/aggregator contract show SSP + PPA stacking?
   - Or is it SSP OR PPA (mutually exclusive)?

2. **Metering Setup:**
   - Does site have separate battery export/import meters?
   - Can battery export to grid while site imports separately?
   - Or is it net metering (export XOR import)?

3. **Industry Examples:**
   - Find published case studies of BTM BESS with VLP
   - What revenue ranges are typical?
   - £173k (model 1) vs £512k (model 2) - which aligns with real projects?

4. **PDF Data Reference:**
   - You mentioned "bigquery data saved from pdf"
   - Check this source for actual VLP revenue structure
   - Does it show conjunctive revenues?

## Recommendation

**Most Conservative:** Use £173k model (mutually exclusive)
- Defensible
- No risk of over-promising
- 113% profit comes from DC alone

**Most Realistic:** Use £300-400k hybrid model
- Partial stacking during high-demand periods
- DC (£195k) + Arbitrage (£80k) + Network (£40k) + PPA (£20k)
- Conditional logic: PPA only when site has demand AND SSP is high

**Most Aggressive:** Use £512k model (full conjunctive)
- Only if VLP contract explicitly allows this
- Requires validation from aggregator
- High risk if incorrect

## Next Steps

1. **Find VLP contract example** - Does it show SSP + PPA stacking?
2. **Check BigQuery VLP data** - What revenue structure does PDF show?
3. **Model hybrid approach** - Conditional stacking based on site demand
4. **Validate with aggregator** - Ask Flexitricity/Limejump directly

---

**Current Status:** 
- Original model: £173k (conservative, mutually exclusive)
- Conjunctive model: £512k (aggressive, full stacking)
- Reality likely: £300-400k (conditional stacking)

**Your Input Needed:** Check the PDF/BigQuery VLP data you mentioned - does it confirm conjunctive revenues?
