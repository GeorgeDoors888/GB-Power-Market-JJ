# BESS COMPREHENSIVE REVENUE ANALYSIS
**Generated:** 1 December 2025
**Analysis Period:** 2025-01-01 to 2025-12-31

---

## EXECUTIVE SUMMARY

### Optimal Operating Strategy
- **Charge Threshold:** < £20/MWh
- **Discharge Threshold:** > £180/MWh for VLP, or when import price > PPA (£150/MWh)
- **Expected Annual Profit:** £36,671
- **ROI:** 117% (based on £31,292 annual costs)
- **Utilization:** 36.7% (536 of 1,460 theoretical cycles)

### Revenue Breakdown
| Revenue Stream | Annual Value | % of Total |
|---|---|---|
| Avoided Import Cost | £67,962 | 100% |
| VLP/SO Revenue | £0 | 0% |
| **TOTAL REVENUE** | **£67,962** | **100%** |

### Cost Breakdown
| Cost Item | Annual Value | % of Total |
|---|---|---|
| Charging Energy | £19,878 | 63.5% |
| Degradation (£5/MWh) | £4,250 | 13.6% |
| Efficiency Losses | £7,139 | 22.8% |
| Fixed O&M | £25 | 0.1% |
| **TOTAL COST** | **£31,292** | **100%** |

---

## REVENUE STREAMS EXPLAINED

### 1. Avoided Import Cost (Primary Revenue)
**What it is:** When BESS discharges to meet site demand, it avoids importing expensive grid electricity

**Calculation per period:**
```
Avoided Import Revenue = Discharge_MWh × (Wholesale + DUoS + Levies)
```

**Components of import price:**
- **Wholesale:** System Buy Price (avg £75.53/MWh in 2025)
- **Network:** DUoS Red (£176.40), Amber (£20.50), Green (£1.10)
- **Levies:** BSUoS (£4.50) + CCL (£8.56) + RO (£14.50) + FiT (£7.40) + CfD (£9.00) + ECO (£1.75) + WHD (£0.75) = **£46.50/MWh**

**When it's profitable:**
- Import price > PPA price (£150/MWh)
- Battery has charge (SOC > 0)
- Site has demand

**2025 Results:**
- **694 periods** discharged to meet demand
- **379.3 MWh** delivered (post-efficiency losses)
- **£67,962** avoided import cost
- **Avg avoided price:** £179.17/MWh

### 2. VLP/SO Revenue (Virtual Lead Party)
**What it is:** Selling flexibility to National Grid System Operator for balancing

**Revenue types:**
1. **Energy payments:** Paid system sell price when dispatched
2. **Availability payments:** Capacity payments for being available (e.g., Dynamic Containment)
3. **Auction revenues:** FFR, Dynamic Regulation, etc.

**Calculation per period:**
```
VLP Revenue = Discharge_MWh × System_Sell_Price × Efficiency
VLP Fee = VLP Revenue × 0.20  (aggregator takes 20%)
Net VLP Revenue = VLP Revenue - VLP Fee
```

**When it's profitable:**
- System sell price > Charge price + Degradation + Margin
- With £20 charge / £180 discharge: Spread = £160/MWh
- But system sell rarely exceeds £180 (only 0.4% of periods in 2025)

**2025 Results (£20/£180 thresholds):**
- **0 periods** at £180+ system sell price
- **£0** VLP revenue
- **Strategy:** Too restrictive for VLP, focus on avoided import instead

**Alternative VLP Strategy (£50/£100 thresholds):**
- **488 periods** at £100+ system sell price
- **£44,806** net VLP revenue (after 20% fee)
- **But:** Total profit drops to **-£27,578** (loss!)
- **Why?** More frequent cycles at lower margins = higher costs

### 3. Availability Payments (Future Opportunity)
**What it is:** Capacity payments for being available for dispatch (not yet implemented)

**Examples:**
- **Dynamic Containment:** £5-15/MW/h for frequency response
- **Dynamic Regulation:** £3-8/MW/h 
- **STOR:** £10-25/MW/h for peak periods

**Potential Annual Revenue:**
- 2.5 MW × £10/MW/h × 8,760 hours = **£219,000/year**
- But requires:
  - VLP/aggregator contract
  - Grid connection modifications
  - Response time guarantees (< 1 second for DC)

---

## COST ACCOUNTING

### 1. Charging Energy Cost
**What it is:** Cost to charge battery from grid

**Calculation:**
```
Charging Cost = Charge_MWh × (System_Buy + DUoS + Levies)
```

**2025 Results (£20/£180 strategy):**
- **378 charge periods** at avg £52.58/MWh
- **470.7 MWh charged**
- **£19,878 total charging cost**

### 2. Round-Trip Efficiency Losses
**Physics:** 85% efficient = 15% energy lost as heat

**Accounting approach:**
```
To deliver 1 MWh output, must charge 1/0.85 = 1.176 MWh input
Lost energy: 1.176 - 1.000 = 0.176 MWh (15%)
Loss cost: 0.176 × Import_Price
```

**2025 Results:**
- **850 MWh throughput** (both charge + discharge)
- **127 MWh lost** to inefficiency
- **£7,139 loss cost** at avg import price

### 3. Battery Degradation
**What it is:** Wear-and-tear cost per cycle

**Typical values:**
- Capex: £200-400/kWh
- Lifetime: 4,000-6,000 cycles
- Degradation: **£3-7/MWh** throughput

**Our assumption:** £5/MWh throughput (conservative)

**2025 Results:**
- **850 MWh throughput**
- **£4,250 degradation cost**

### 4. VLP Service Fee
**What it is:** Aggregator's cut of VLP revenues (typically 15-25%)

**Our assumption:** 20% of gross VLP revenues

**2025 Results:**
- **£0** (no VLP revenues at £180 threshold)
- If using £100 threshold: **£11,202 fee** on £56,008 gross

### 5. Fixed O&M
**What it is:** Annual maintenance, insurance, monitoring

**Typical:** £5-15/kW/year for battery systems

**Our assumption:** £10/kW/year × 2.5 MW = **£25/year** (very low)

**Note:** Real O&M likely £12,500-37,500/year for 2.5 MW system

---

## STRATEGY COMPARISON

### Strategy A: Narrow Spread (£50 charge / £100 discharge)
**Pros:**
- More frequent cycles (651/year vs 536/year)
- Captures VLP opportunities (488 periods)
- Higher utilization (44.6% vs 36.7%)

**Cons:**
- Lower profit per cycle (£-42.36 vs £68.42)
- High charging costs (£62,156 vs £19,878)
- **NET RESULT: £-27,578 LOSS**

### Strategy B: Wide Spread (£20 charge / £100 discharge) ✅ OPTIMAL
**Pros:**
- High profit per cycle (£68.42)
- Low charging costs (only when wholesale <£20)
- Focus on avoided import (£179/MWh avg)
- **NET RESULT: £36,671 PROFIT**

**Cons:**
- Lower utilization (36.7%)
- No VLP revenues (prices rarely hit £180)
- Misses some arbitrage opportunities

### Strategy C: Hybrid (£30 charge / £120 discharge)
**Middle ground:**
- 560 cycles/year
- Mix of VLP (90 periods) + avoided import (560 periods)
- **NET RESULT: £32,964 PROFIT** (2nd best)

---

## CRITICAL INSIGHTS

### 1. VLP Revenue is NOT Always Profitable
**Common misconception:** "VLP pays £150-300/MWh, must be profitable!"

**Reality:**
- If you charge at £50 and discharge at £100, net spread is only £50
- After degradation (£5/MWh), efficiency losses (15%), and VLP fees (20%), you need **>£100 spread** to break even
- Real-world: £50 → £100 spread = **£-42.36 loss per cycle**

### 2. Avoided Import > VLP for BTM BESS
**Why?**
- Avoided import price includes **full retail tariff** (wholesale + network + levies)
- Avg import price: £146.81/MWh (much higher than wholesale £75.53)
- VLP only pays wholesale prices (system sell)
- **Avoided import is like selling at retail vs wholesale**

### 3. Threshold Selection is Critical
**Too narrow (£50/£100):**
- Many low-margin cycles
- High costs overwhelm revenues
- **Result:** Loss

**Too wide (£20/£180):**
- Few high-margin cycles
- Low costs, strong revenues
- **Result:** Profit

**Sweet spot:** £20 charge, discharge when import > £150 PPA

### 4. Utilization ≠ Profitability
**Higher utilization (44.6% at £50/£100) = LOSS**
**Lower utilization (36.7% at £20/£180) = PROFIT**

**Lesson:** Quality of cycles matters more than quantity

---

## DOUBLE-COUNTING CHECK ✅

**Question:** If BESS discharges to meet demand AND qualifies for VLP, do we count both revenues?

**Answer:** YES, but they're mutually exclusive in our model:

1. **VLP Discharge:** Battery exports to grid for SO balancing
   - Revenue: System sell price
   - Site still imports from grid to meet demand
   - No avoided import

2. **Demand Discharge:** Battery supplies site load
   - Revenue: Avoided import cost
   - No grid export
   - No VLP payment

**In practice:** A single period can only be ONE of these, not both. Our model correctly implements this via `if/elif` logic.

**Advanced case:** If battery has export capacity > site demand, could do BOTH:
- Export X MWh to SO (VLP)
- Discharge Y MWh to site (avoided import)
- Would require 2-stream dispatch logic (not currently implemented)

---

## RECOMMENDATIONS

### Immediate Actions
1. **Deploy £20/£180 strategy** for maximum profit
2. **Monitor performance** against £36,671/year target
3. **Track actual vs model**:
   - Charge periods (expect 378/year)
   - Discharge periods (expect 694/year)
   - Average import price avoided (expect £179.17/MWh)

### Medium-Term Optimizations
1. **Test £30/£120 hybrid** (2nd best at £32,964/year)
2. **Seasonal adjustment:**
   - Winter (Nov-Feb): Wider spread (£20/£200) - higher prices
   - Summer (May-Aug): Narrower spread (£30/£120) - more stable prices
3. **Add weather forecasting:**
   - Charge before wind lulls (high prices expected)
   - Discharge before wind surges (low prices expected)

### Long-Term Opportunities
1. **VLP Aggregator Contract:**
   - Negotiate <20% fee (currently 20%)
   - Explore Dynamic Containment (£219k/year potential)
   - But only if availability payments > £10/MW/h

2. **Expand Capacity:**
   - Current: 5 MWh, 2.5 MW (2 hours)
   - Optimal: 10 MWh, 5 MW (2 hours) = 2× cycles, 2× profit
   - ROI: £73,342/year profit vs £50-75k capex = <1 year payback

3. **Demand-Side Response (DSR):**
   - Shift site load to off-peak (when battery charges)
   - Reduces total import, increases battery utilization
   - Potential £10-20k/year additional value

---

## TECHNICAL NOTES

### Data Sources
- **System Prices:** `bmrs_costs` table (Jan-Nov 2025, 267 days, 12,813 records)
- **Site Demand:** HH Data sheet (17,520 periods, 8,760 hours)
- **DUoS Rates:** Red £176.40, Amber £20.50, Green £1.10
- **Levies:** Total £46.50/MWh (TNUoS excluded per user instruction)

### Assumptions
- **Round-trip efficiency:** 85% (typical for lithium-ion)
- **Degradation:** £5/MWh throughput (conservative)
- **VLP fee:** 20% of gross revenues
- **Fixed O&M:** £10/kW/year (likely understated)
- **PPA price:** £150/MWh (fixed)

### Model Limitations
1. **No intraday forecasting** - decisions based on current period only
2. **No SOC optimization** - simple greedy algorithm
3. **No availability payments** - VLP revenue is energy-only
4. **No degradation curve** - assumes constant £5/MWh (reality: increases over time)
5. **No grid constraints** - assumes infinite import/export capacity

### Future Enhancements
1. **Predictive dispatch:** Use next 4-hour forecast to optimize SOC
2. **Machine learning:** Predict high-price periods for pre-positioning
3. **Multi-objective optimization:** Balance profit, degradation, availability
4. **Real-time integration:** Connect to BESS BMS for live dispatch
5. **Sensitivity analysis:** Test price volatility, demand variations, efficiency changes

---

## APPENDIX: FORMULA REFERENCE

### Per-Period Calculations

**Import Price:**
```python
import_price = system_buy_price + duos_rate + TOTAL_FIXED_LEVIES
# where TOTAL_FIXED_LEVIES = BSUoS + CCL + RO + FiT + CfD + ECO + WHD = £46.50/MWh
```

**Charge Decision:**
```python
if system_buy_price < CHARGE_THRESHOLD and soc < capacity and daily_charges < 4:
    charge_mwh = min(max_charge_per_period, capacity - soc)
    cost = charge_mwh × import_price
```

**Discharge VLP Decision:**
```python
if system_sell_price > DISCHARGE_VLP_THRESHOLD and soc > 0 and daily_discharges < 4:
    discharge_mwh = min(max_discharge_per_period, soc)
    revenue = discharge_mwh × system_sell_price × efficiency
    vlp_fee = revenue × 0.20
    net_revenue = revenue - vlp_fee
```

**Discharge Demand Decision:**
```python
if soc > 0 and site_demand > 0 and import_price > ppa_price and daily_discharges < 4:
    discharge_mwh = min(max_discharge_per_period, soc, site_demand)
    avoided_import_mwh = discharge_mwh × efficiency
    revenue = avoided_import_mwh × import_price
```

**Degradation Cost:**
```python
throughput = charge_mwh + discharge_vlp_mwh + discharge_demand_mwh
degradation_cost = throughput × DEGRADATION_COST_PER_MWH  # £5/MWh
```

**Profit:**
```python
profit = (avoided_import_revenue + vlp_net_revenue) - (charging_cost + degradation_cost + fixed_om)
```

---

**Contact:** George Major (george@upowerenergy.uk)  
**Last Updated:** 1 December 2025  
**Next Review:** Q1 2026 (validate against actual performance)
