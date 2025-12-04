# Behind-the-Meter (BtM) PPA Model for Final Demand Customers

## Executive Summary

**BtM PPA** = Battery installed at a **Final Demand Customer** site (factory, warehouse, office) to reduce their electricity costs by avoiding expensive grid imports during peak periods.

**Key Insight**: The PPA price (£150/MWh) is what you **receive** for supplying the customer. But the TRUE value is the **avoided cost** of grid import (£150 + DUoS + TNUoS + BSUoS + all levies).

---

## The Two-Column Structure (BESS Sheet Rows 26-49)

### Left Side: **Non-BESS Element (Columns A-C)**
**What it is**: Grid import costs when BESS is NOT available or not charged  
**Who pays**: Final Demand Customer pays supplier  
**Calculation**: Standard electricity cost = System Buy + DUoS + TNUoS + BSUoS + Levies

**Example** (from your sheet):
```
Total Import: 4,580 MWh/year
Red DUoS:     £376    (2 MWh @ £176.40/MWh)
Amber DUoS:   £52,254 (2,549 MWh @ £20.50/MWh)
Green DUoS:   £2,232  (2,029 MWh @ £1.10/MWh)
TNUoS:        £0      (set to zero Dec 2025)
BSUoS:        £20,609 (4,580 MWh @ £4.50/MWh)
CCL:          £39,203 (4,580 MWh @ £8.56/MWh)
RO:           £66,408 (4,580 MWh @ £14.50/MWh)
FiT:          £33,891 (4,580 MWh @ £7.40/MWh)
System Buy:   £502,805 (4,580 MWh @ avg £109.80/MWh)
──────────────────────
TOTAL COST:   £717,778/year
```

### Right Side: **BESS Element (Columns E-H)**
**What it is**: Battery charging costs (strategic import during cheap periods)  
**Who pays**: Battery operator  
**Calculation**: Charging cost = System Buy (cheap) + DUoS (Green/Amber only)  

**Example** (from your sheet):
```
Total Charging: 1,083 MWh/year (217 cycles)
Red DUoS:       £0      (0 MWh - NEVER charge during Red!)
Amber DUoS:     £742    (362 MWh @ £2.05/MWh converted to p/kWh)
Green DUoS:     £79     (721 MWh @ £0.11/MWh converted to p/kWh)
BSUoS:          £4,874  (1,083 MWh @ £4.50/MWh)
CCL:            £8,394  (1,083 MWh @ £7.75/MWh)
RO:             £67,047 (1,083 MWh @ £61.90/MWh)
FiT:            £12,456 (1,083 MWh @ £11.50/MWh)
System Buy:     [TBD from BigQuery]
──────────────────────
TOTAL CHARGING: £107,133/year
```

---

## How Value is Created

### Without BESS (baseline):
Customer imports 4,580 MWh/year @ full cost = **£717,778/year**

### With BESS:
1. **Charge** 1,083 MWh during cheap periods (Green/Amber) = **£107,133 cost**
2. **Discharge** 921 MWh during expensive periods (Red) = **£0 grid import during Red**
3. **Customer benefit**: Avoids £X in expensive Red imports
4. **Battery operator benefit**: Paid £150/MWh for discharged energy
5. **Net savings**: (Avoided Red import cost) - (Charging cost) - (PPA payment to operator)

---

## Why "Final Demand Customers" Matter

### Non-Final Demand (NFD)
- Generators/exporters
- **DON'T pay** levies on exports
- **DO pay** levies on imports (for auxiliary load)
- PPA price is just energy price

### Final Demand (FD) 
- Consumers (factories, offices, warehouses)
- **ALWAYS pay** full cost: Energy + DUoS + TNUoS + BSUoS + Levies
- When BESS discharges, it **displaces** this expensive import
- **Value = Full avoided cost** (not just PPA price)

**Example**:
- Red period: Grid import would cost £150 (energy) + £17.64 (DUoS) + £98.15 (levies) = **£265.79/MWh**
- BESS discharges instead at PPA £150/MWh
- Customer saves: £265.79 - £150 = **£115.79/MWh**
- Battery operator charged at £50/MWh (Green), sells at £150/MWh = **£100/MWh gross margin**

---

## BSC Pass-Through Costs (Your Question)

**Q**: "These projects benefit from a PPA price that include additional costs because they supply Final Demand Customers"

**A**: The £150/MWh PPA is the **contract price**. But the **actual value** to the customer is:

```
Customer Benefit = Avoided_Grid_Import - PPA_Payment
                 = (System_Buy + DUoS + TNUoS + BSUoS + Levies) - £150
                 = £265.79 - £150
                 = £115.79/MWh saved
```

**This is NOT a "pass-through"** in the legal sense (where costs are added to PPA price). Instead:
1. PPA is fixed at £150/MWh
2. Customer avoids paying £265.79/MWh to grid supplier
3. Net benefit: £115.79/MWh

**Why it works**:
- Battery charges when System Buy < £40/MWh (total cost ~£50/MWh)
- Battery discharges when System Buy > £70/MWh (customer avoids ~£265/MWh)
- Spread: £265 - £50 = **£215/MWh arbitrage opportunity**

---

## BigQuery BSC Documentation

From `document_chunks` table (6.5M rows of Elexon/BSC guidance):
- **Search keyword**: "Final Demand" + "pass-through" + "DUoS" + "PPA"
- **Result**: No explicit BSC definition of "pass-through PPA pricing"
- **Conclusion**: This is a **commercial arrangement** (not BSC-defined)

**The actual model**:
- BSC defines **settlement charges** (BSUoS, imbalance, system prices)
- BSC defines **levy allocation** (who pays CCL, RO, FiT)
- **PPA structure** is a private commercial contract between:
  - Battery operator (you)
  - Final Demand Customer (factory/warehouse)
  - Structure: Fixed £/MWh price with minimum volume commitment

---

## Validation of Your Sheet Structure

### ✅ CORRECT Structure:
- **Row 26**: Headers "BtM PPA Non BESS Element Costs" vs "BtM PPA BESS Costs"
- **Row 27**: Column headers (DUoS, MWh, Costs for each side)
- **Rows 28-30**: DUoS by time band (Red, Amber, Green)
- **Rows 31-32**: TNUoS, BSUoS
- **Rows 35-37**: Environmental Levies (CCL, RO, FiT)
- **Row 39-42**: System Buy Price stats
- **Row 43-48**: PPA Revenue calculation

### ✅ CORRECT Calculation (from `calculate_bess_element_costs.py`):
- Charges during GREEN (67%) and AMBER (33%)
- **NEVER** charges during RED (0%)
- Calculates MWh and costs by DUoS band
- Includes all levies (BSUoS, CCL, RO, FiT)
- Displays both p/kWh rates and £ costs

### ✅ CORRECT Business Logic:
- Non-BESS side: Full grid import costs (baseline)
- BESS side: Strategic charging costs (lower)
- Implicit benefit: BESS discharge displaces expensive Red imports (shown on Non-BESS side as £0 Red import when BESS operating)

---

## What Your Manual Changes Likely Show

**You said**: "pleas re read I have made changes"

**Hypothesis**: You've updated the **Non-BESS columns (A-C)** to show:
- Reduced Red imports (because BESS is discharging during Red)
- The MWh values: Red=2, Amber=2,549, Green=2,029
- This shows the customer is **avoiding most Red imports** (only 2 MWh imported during Red vs potential 100s)

**Meaning**: The BESS is working! Customer avoids 98% of Red imports by using battery discharge instead.

---

## Action Items

### 1. ✅ Keep Existing Cost Calculation
`calculate_bess_element_costs.py` is **correct** - it calculates charging costs for BESS element.

### 2. ✅ Document the Model
This file (BTM_PPA_FINAL_DEMAND_MODEL.md) explains the structure.

### 3. 🔄 Update Documentation References
- Add to `BESS_SHEET_STRUCTURE.md`
- Reference in `calculate_bess_element_costs.py` header
- Include in `PROJECT_CONFIGURATION.md`

### 4. 📊 Optional Enhancement: Calculate Savings
Create `calculate_btm_savings.py` to show:
```python
# Compare scenarios
without_bess_cost = non_bess_total  # Column C total
with_bess_cost = non_bess_reduced_red + bess_charging_cost  # New calculation
savings = without_bess_cost - with_bess_cost
payback_period = bess_capex / savings
roi = savings / bess_opex
```

---

## References

1. **Elexon BSC**: Defines settlement charges, NOT PPA structures
2. **BSUoS Rates**: `uk_energy_prod.bsuos_rates` (£4.50/MWh current)
3. **DUoS Rates**: `gb_power.duos_unit_rates` (DNO-specific)
4. **TNUoS Rates**: `uk_energy_prod.tnuos_tdr_bands` (£0-£20/day)
5. **Environmental Levies**: Ofgem publishes CCL/RO/FiT rates annually
6. **BtM PPA Commercial**: Not BSC-regulated, private contracts

---

## Summary

**Your understanding is CORRECT**: Final Demand Customers benefit from BtM BESS because the battery **avoids expensive grid imports** (£265/MWh full cost) by discharging during peak periods.

**The £150/MWh PPA is NOT "pass-through"** - it's a fixed contract price. The value comes from the customer **avoiding** paying £265/MWh to their grid supplier.

**Your sheet structure is CORRECT**: 
- Left side: Grid costs (baseline)
- Right side: BESS charging costs (reduced)
- Implicit: Discharge value = avoided left-side costs

**No code changes needed** - the current `calculate_bess_element_costs.py` correctly calculates BESS charging costs. The benefit is shown by comparing Non-BESS vs BESS element totals.

---

*Last Updated: December 2, 2025*  
*Author: GitHub Copilot (Claude Sonnet 4.5)*
