# BtM PPA Revenue Decision Logic

## Executive Summary

The Behind-the-Meter (BtM) PPA system operates with **TWO-STEP PRIORITY LOGIC**:

1. **FIRST**: Check if battery discharge (Stream 2) is available → Use it
2. **SECOND**: For all remaining periods → Use direct import (Stream 1)

**Key Principle**: Each settlement period can only use ONE method. Battery periods are EXCLUDED from Stream 1.

---

## The Two Revenue Streams

### Stream 2: Battery Discharge + VLP (PRIORITY)

**Requirements**: Battery must be charged and available

**Revenue Breakdown**:
- PPA Contract: £150/MWh (fixed)
- VLP Payments: ~£15/MWh average (National Grid balancing)
- **Total Revenue**: £165/MWh

**Cost Breakdown**:
- Charging cost: ~£40/MWh (system buy price during Green periods)
- DUoS: ~£0.11/MWh (Green rate)
- TNUoS: £12.50/MWh (transmission)
- BSUoS: £4.50/MWh (balancing)
- CCL: £7.75/MWh (climate levy)
- RO: £61.90/MWh (renewables)
- FiT: £11.50/MWh (feed-in tariff)
- **Total Cost**: ~£99/MWh

**Profit**: £165 - £99 = **£66/MWh**

**Key Advantage**: Levies paid ONCE (on charging), not on discharge!

---

### Stream 1: Direct Import (FALLBACK)

**Requirements**: Used for ALL periods where battery is NOT discharging

**Revenue Breakdown**:
- PPA Contract: £150/MWh (fixed)
- **Total Revenue**: £150/MWh

**Cost Breakdown** (varies by DUoS period):

**🟢 Green Periods (00:00-08:00, 22:00-24:00)**:
- System Buy: ~£40/MWh
- DUoS: £0.11/MWh
- Fixed Levies: £98.15/MWh
- **Total Cost**: ~£139/MWh
- **Profit**: £150 - £139 = **+£11/MWh** ✅

**🟡 Amber Periods (08:00-16:00, 19:30-22:00)**:
- System Buy: ~£50/MWh
- DUoS: £2.05/MWh
- Fixed Levies: £98.15/MWh
- **Total Cost**: ~£170/MWh
- **Profit**: £150 - £170 = **-£20/MWh** ❌

**🔴 Red Periods (16:00-19:30)**:
- System Buy: ~£80/MWh
- DUoS: £17.64/MWh
- Fixed Levies: £98.15/MWh
- **Total Cost**: ~£355/MWh
- **Profit**: £150 - £355 = **-£205/MWh** ❌❌

**Reality**: Stream 1 includes BOTH profitable AND unprofitable periods because of PPA contract obligation to supply customer demand.

---

## Decision Flow (For Each Settlement Period)

```
START: Customer needs X MWh at settlement period SP

┌─────────────────────────────────────────┐
│ Step 1: Check Battery Availability     │
└─────────────────────────────────────────┘
                  │
                  ├─→ YES: Battery charged ≥ X MWh
                  │        └─→ USE STREAM 2
                  │             • Discharge X MWh from battery
                  │             • Revenue: £165/MWh (PPA + VLP)
                  │             • Cost: £99/MWh (charged earlier)
                  │             • Profit: £66/MWh
                  │             • Mark period as "BATTERY USED"
                  │             └─→ END (Stream 1 NOT used this period)
                  │
                  └─→ NO: Battery empty or unavailable
                       └─→ USE STREAM 1
                            • Import X MWh from supplier
                            • Revenue: £150/MWh (PPA)
                            • Cost: Market + DUoS + Levies
                            • Profit: £150 - Cost (varies)
                            • Contract obligation (must supply)
                            └─→ END
```

---

## Annual Strategy Example

**Assumptions**:
- Site: 2.5 MW continuous load
- Battery: 5 MWh capacity, 2.5 MW power
- Annual demand: ~22,000 MWh
- Analysis: 17,520 settlement periods/year (48 per day × 365 days)

### Battery Allocation (Stream 2)

**Target Periods**: 🔴 RED first (highest value), then 🟡 AMBER if capacity available

**RED Periods**:
- Occurrence: 7 periods/day × 365 days = 2,555 periods/year
- Battery can serve: ~2,000 periods (limited by charging availability)
- Volume: 2,000 periods × 1.25 MWh = 2,500 MWh
- Profit: 2,500 MWh × £66/MWh = **£165,000/year**
- Value vs import: Saves £205/MWh loss → **£512,500 avoided losses!**

**AMBER Periods** (when battery available):
- Occurrence: 13 periods/day × 365 days = 4,745 periods/year
- Battery can serve: ~1,500 periods (remaining capacity)
- Volume: 1,500 periods × 1.25 MWh = 1,875 MWh
- Profit: 1,875 MWh × £66/MWh = **£123,750/year**
- Value vs import: Saves £20/MWh loss → **£37,500 avoided losses!**

**Total Stream 2**:
- Volume: 4,375 MWh/year
- Profit: **£288,750/year**
- Battery cycles: 4,375 MWh ÷ 5 MWh = **875 cycles/year** (good utilization)

### Direct Import Allocation (Stream 1)

**Remaining Periods**: All periods NOT using battery

**GREEN Periods** (all used for Stream 1 + charging):
- Occurrence: 28 periods/day × 365 days = 10,220 periods/year
- Volume: 10,220 periods × 1.25 MWh = 12,775 MWh
- Profit: 12,775 MWh × £11/MWh = **£140,525/year**
- Plus: Charges battery for Stream 2 use

**AMBER Periods** (remaining after battery discharge):
- Occurrence: 4,745 total - 1,500 battery = 3,245 periods
- Volume: 3,245 periods × 1.25 MWh = 4,056 MWh
- Profit: 4,056 MWh × (-£20/MWh) = **-£81,120/year** (loss)
- Unavoidable: Contract obligation

**RED Periods** (remaining after battery discharge):
- Occurrence: 2,555 total - 2,000 battery = 555 periods
- Volume: 555 periods × 1.25 MWh = 694 MWh
- Profit: 694 MWh × (-£205/MWh) = **-£142,270/year** (loss)
- Unavoidable: Contract obligation, battery capacity exhausted

**Total Stream 1**:
- Volume: 16,525 MWh/year
- Profit: £140,525 - £81,120 - £142,270 = **-£82,865/year** (NET LOSS)

### Combined Annual Result

- **Stream 2 (Battery)**: +£288,750
- **Stream 1 (Direct Import)**: -£82,865
- **TOTAL PROFIT**: **£205,885/year**

**Key Insight**: Without battery, total profit would be:
- All periods via Stream 1: -£82,865 (GREEN) + (-£341,250 RED) + (-£94,900 AMBER)
- **= -£518,115/year TOTAL LOSS**

**Battery saves**: £205,885 - (-£518,115) = **£724,000/year!**

---

## Why This Logic Matters

### ❌ Wrong Approach: "Streams are additive"
```
WRONG: Total_Profit = Stream1_Profit + Stream2_Profit
       = Calculate all imports as Stream 1
       = Calculate all battery as Stream 2
       = Add them together
```

**Problem**: This counts the same periods twice! If you import 1 MWh AND discharge 1 MWh for 1 MWh demand, you've supplied 2 MWh (excess generation, no revenue).

### ✅ Correct Approach: "Battery first, import second"
```
CORRECT: For each period:
           IF battery_available THEN use_battery (Stream 2)
           ELSE use_import (Stream 1)
         Total_Profit = Σ(period_profit)
```

**Result**: Each MWh of demand supplied exactly once, by most profitable method available.

---

## Script Implementation

**File**: `calculate_btm_ppa_revenue_complete.py`

**Logic Flow**:

1. **Read Configuration**
   - Battery capacity, power rating, efficiency
   - DUoS rates by band
   - Fixed levy rates
   - PPA price

2. **Query BigQuery**
   - Last 6 months system buy prices
   - Calculate total import costs by band
   - Identify charging opportunities

3. **Calculate Stream 2 (Battery First)**
   - Find Green/Amber periods with cost < £120/MWh
   - Calculate charging volume (respecting battery limits)
   - Calculate discharge volume (× 0.85 efficiency)
   - Calculate discharge revenue: PPA + VLP
   - Calculate profit: Revenue - Charging costs
   - **Record battery usage periods**

4. **Calculate Stream 1 (Remaining Periods)**
   - Read actual import volumes from sheet (Non-BESS columns)
   - Read actual import costs from sheet
   - Calculate revenue: Volume × £150/MWh
   - Calculate profit: Revenue - Costs
   - **Excludes battery discharge periods**

5. **Update Sheet**
   - Battery charging MWh by band (Column E)
   - Battery costs including levies (Column H)
   - Discharge revenue split: PPA + VLP
   - Profit analysis (Rows 50-62) with logic explanation

6. **Output Summary**
   - Stream 2: Battery profit with VLP
   - Stream 1: Direct import profit (including losses)
   - Period allocation breakdown
   - Battery utilization (cycles/year)
   - Total annual profit

**Run**: `python3 calculate_btm_ppa_revenue_complete.py`

---

## Key Metrics

| Metric | Value | Notes |
|--------|-------|-------|
| **Battery Utilization** | 875 cycles/year | Excellent (within limits) |
| **Stream 2 Periods** | ~4,000/year | Priority usage |
| **Stream 1 Periods** | ~13,500/year | Remaining demand |
| **Battery Profit Margin** | 66.7% | £66 profit on £99 cost |
| **Stream 1 Margin** | Variable | +7% (Green) to -136% (Red) |
| **VLP Contribution** | £15/MWh | +10% revenue boost |
| **Battery Annual Value** | £724,000/year | vs no-battery scenario |

---

## Decision Criteria Summary

**When to use Stream 2 (Battery)**:
- ✅ Battery is charged (≥ demand MWh)
- ✅ Battery available (not already discharging)
- ✅ Higher profit than Stream 1 (usually £66/MWh vs -£205 to +£11/MWh)

**When to use Stream 1 (Direct Import)**:
- Battery empty or unavailable
- All periods not covered by battery
- Contract obligation (must supply regardless of profitability)

**Charging Strategy**:
- Charge during GREEN periods (£99/MWh all-in cost)
- Charge during AMBER if needed (£101/MWh cost)
- NEVER charge during RED (£117/MWh cost, not economic)

**Discharge Priority**:
1. RED periods (saves £205 loss → £66 profit = £271/MWh value)
2. AMBER periods (saves £20 loss → £66 profit = £86/MWh value)  
3. GREEN periods (£66 profit vs £11 profit = £55/MWh premium, but better to import + charge)

---

*Last Updated: 2 December 2025*  
*For detailed constraint examples, see: `BTM_PPA_CAPACITY_CONSTRAINT.md`*  
*For quick reference, see: `BTM_PPA_REVENUE_QUICK_REFERENCE.md`*
