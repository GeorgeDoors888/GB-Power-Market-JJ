# BtM PPA Capacity Constraint - The Critical Rule

## The Revenue Stream Decision Logic

## How It Actually Works

The system uses **TWO-STEP PRIORITY LOGIC** for each settlement period:

### Step 1: Check Battery Availability (Stream 2 - Priority)
```
FOR each_settlement_period:
    IF battery_is_charged AND battery_available:
        → Use Stream 2 (Discharge battery + collect VLP)
        → Revenue: £150/MWh (PPA) + £15/MWh (VLP) = £165/MWh
        → Cost: £99/MWh (charged earlier with levies paid once)
        → PROFIT: £66/MWh ✅
        → Mark this period as "BATTERY USED"
```

### Step 2: All Remaining Periods (Stream 1 - Fallback)
```
FOR each_remaining_period (not using battery):
    → Use Stream 1 (Direct import from supplier)
    → Revenue: £150/MWh (PPA contract)
    → Cost: Market price + DUoS + All levies
    → PROFIT: £150 - Total_Cost (can be positive OR negative)
    → Contract obligation: Must supply regardless of profitability
```

### Example Scenario
**Settlement Period 35** (Red period, 17:00-17:30)  
**Site Demand**: 1 MWh  
**PPA Contract**: Supply at £150/MWh

---

## Option A: Stream 1 (Direct Import)

```
Grid Import → Meter → Customer
1 MWh        1 MWh    1 MWh

Cost:
- System Buy:   £80/MWh
- Red DUoS:     £176.40/MWh
- Levies:       £98.15/MWh
- TOTAL COST:   £354.55/MWh ❌

Revenue:        £150/MWh (PPA)
PROFIT:         £150 - £354.55 = -£204.55 LOSS ❌
```

**Result**: UNPROFITABLE - Don't use Stream 1 during Red!

---

## Option B: Stream 2 (Battery Discharge)

```
Battery → Meter → Customer
1 MWh     1 MWh    1 MWh

Cost (already paid during charging):
- Charged at Green: £99/MWh (avg, including all levies)
- Discharge cost:   £0 (levies already paid!)

Revenue:
- PPA:              £150/MWh
- VLP (Balancing):  £15/MWh (avg)
- TOTAL REVENUE:    £165/MWh ✅

PROFIT:             £165 - £99 = £66/MWh ✅
```

**Result**: PROFITABLE - Use Stream 2 during Red!

---

## The Constraint Visualized

### ❌ IMPOSSIBLE: Cannot do BOTH
```
Period SP35 (Red, 17:00-17:30)
Customer Demand: 1 MWh

                    ┌─────────────┐
Grid Import (1 MWh) │             │
─────────────────→  │   Meter     │ ───→ Customer (1 MWh)
                    │             │
Battery (1 MWh)     │             │
─────────────────→  └─────────────┘

TOTAL: 2 MWh supplied, but customer only needs 1 MWh!
This would be:
1. Paying for 2 MWh
2. Only getting paid for 1 MWh PPA
3. Wasting 1 MWh = HUGE LOSS
```

### ✅ CORRECT: Choose ONE option per period
```
Period SP35 (Red, 17:00-17:30)
Customer Demand: 1 MWh

Option A: Stream 1 Only
┌─────────┐
│  Grid   │ ───→ 1 MWh ───→ Customer
└─────────┘
Profit: -£204.55 LOSS ❌

Option B: Stream 2 Only
┌─────────┐
│ Battery │ ───→ 1 MWh ───→ Customer
└─────────┘
Profit: +£66/MWh PROFIT ✅

CHOOSE: Option B (battery discharge)
```

---

## Optimization Logic

For each settlement period:

```python
def optimize_supply_strategy(settlement_period, demand_mwh):
    """Determine best way to supply customer demand"""
    
    # Calculate cost for each option
    stream1_cost = get_import_cost(settlement_period)  # System + DUoS + Levies
    stream2_cost = battery_charge_cost / efficiency     # Cost already paid (£99/MWh avg)
    
    # Calculate revenue for each option
    stream1_revenue = PPA_PRICE  # £150/MWh only
    stream2_revenue = PPA_PRICE + vlp_payment(settlement_period)  # £150 + £15 avg
    
    # Calculate profit
    stream1_profit = (stream1_revenue - stream1_cost) * demand_mwh
    stream2_profit = (stream2_revenue - stream2_cost) * demand_mwh
    
    # Choose more profitable option (if battery available)
    if battery_soc >= demand_mwh and stream2_profit > stream1_profit:
        discharge_battery(demand_mwh)
        return {
            'method': 'battery',
            'profit': stream2_profit,
            'revenue': stream2_revenue * demand_mwh
        }
    elif stream1_cost < PPA_PRICE:  # Only import if profitable
        import_from_grid(demand_mwh)
        return {
            'method': 'grid',
            'profit': stream1_profit,
            'revenue': stream1_revenue * demand_mwh
        }
    else:
        # Neither option profitable - must still supply under PPA!
        # Choose battery if available (better than grid loss)
        if battery_soc >= demand_mwh:
            discharge_battery(demand_mwh)
            return {'method': 'battery', 'profit': stream2_profit}
        else:
            import_from_grid(demand_mwh)
            return {'method': 'grid', 'profit': stream1_profit}
```

---

## Typical Period Allocation

### Green Periods (SP 1-16, 45-48 weekdays + all weekend)
**Typical Strategy**: Stream 1 (Direct Import)
- Import cost: £40 + £1.10 + £98.15 = £139.25/MWh
- PPA: £150/MWh
- **Profit: £10.75/MWh** ✅
- Battery: Save for discharge during Red

### Amber Periods (SP 17-32, 40-44 weekdays)
**Typical Strategy**: Stream 1 OR Stream 2 (depends on exact price)
- Import cost: £50 + £20.50 + £98.15 = £168.65/MWh
- PPA: £150/MWh
- **Profit: -£18.65/MWh** ❌ (unprofitable to import!)
- **Better**: Discharge battery at £99 cost → £165 revenue = **+£66/MWh** ✅

### Red Periods (SP 33-39 weekdays, 16:00-19:30)
**Typical Strategy**: Stream 2 (Battery Discharge) ALWAYS
- Import cost: £80 + £176.40 + £98.15 = £354.55/MWh
- PPA: £150/MWh
- **Profit: -£204.55/MWh** ❌ (HUGE LOSS to import!)
- **Better**: Discharge battery at £99 cost → £165 revenue = **+£66/MWh** ✅

---

## Annual Strategy Summary

**Without Battery** (Stream 1 only):
- Green: Profitable (import & sell)
- Amber: Marginal or loss (avoid or minimal)
- Red: HUGE LOSS (cannot profitably supply!)
- **Result**: Limited to Green period profits, cannot service Red demand profitably

**With Battery** (Optimized Stream 1 + Stream 2):
- Green: Stream 1 = Direct import, charge battery simultaneously
- Amber: Stream 2 = Discharge battery (better than unprofitable import)
- Red: Stream 2 = Discharge battery (only profitable option)
- **Result**: Maximize Green arbitrage + profitable Red supply via battery

---

## Key Takeaways

1. ⚠️ **Same period = ONE stream only** - Cannot supply 1 MWh twice!
2. ✅ **Optimize per period** - Choose most profitable option
3. ✅ **Battery enables Red supply** - Without it, Red = unprofitable
4. ✅ **VLP adds value** - £15/MWh bonus on battery discharge
5. ✅ **Levies paid once** - Battery discharge cheaper than grid import
6. 📊 **Total profit ≠ Stream1 + Stream2** - Must account for period allocation

---

## Updated Profit Formula

```python
total_profit = 0

for period in all_settlement_periods:
    demand = site_demand[period]
    
    # Calculate both options
    option1_profit = calculate_stream1_profit(period, demand)
    option2_profit = calculate_stream2_profit(period, demand)
    
    # Choose best option (considering battery availability)
    if battery_available and option2_profit > option1_profit:
        use_battery(period, demand)
        total_profit += option2_profit
    elif option1_profit > 0:
        use_grid(period, demand)
        total_profit += option1_profit
    else:
        # Forced to supply under PPA even if unprofitable
        # Choose lesser loss
        if battery_available:
            use_battery(period, demand)
            total_profit += option2_profit  # Likely negative but less than option1
        else:
            use_grid(period, demand)
            total_profit += option1_profit  # Negative
```

---

*Last Updated: December 2, 2025*  
*Critical constraint identified and documented*
