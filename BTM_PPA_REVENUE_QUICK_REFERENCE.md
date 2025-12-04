# BtM PPA Revenue Calculation - Quick Reference

## Updated Logic (December 2, 2025)

### Revenue Stream 1: Direct Import Arbitrage
**NO BATTERY NEEDED**

```
When: Grid import cost < £150/MWh
Action: Import and sell at £150/MWh PPA
Profit: (£150 - Total_Import_Cost) × Volume

Total_Import_Cost = System_Buy + DUoS + BSUoS + CCL + RO + FiT + TNUoS
```

**Example**:
- Green period: £40 (buy) + £1.10 (DUoS) + £98.15 (levies) = £139.25
- Sell at £150/MWh PPA
- **Profit: £10.75/MWh** ✅

---

### Revenue Stream 2: Battery Arbitrage + VLP
**REQUIRES BATTERY**

```
Charge: During cheap periods (Green/Amber)
Discharge: At £150/MWh PPA + VLP payments
KEY: Levies paid ONCE on charging, NOT on discharging!
BONUS: VLP revenue from National Grid balancing services

Charging Cost = System_Buy + DUoS + Levies (paid once)
Discharge Revenue = £150/MWh PPA + £15/MWh VLP (avg)
Total Revenue = PPA + VLP (NO additional levies!)
Profit = Total_Revenue - Charging_Cost
```

**VLP Revenue Streams**:
- BID acceptance: £25/MWh (reduce demand)
- Offer acceptance: £15/MWh (increase supply)
- Availability payments: £5/MWh
- **Average**: ~£15/MWh additional to PPA

**Example**:
- Charge at £99/MWh (System £40 + DUoS £1.10 + Levies £98.15, optimized avg)
- Discharge at £150/MWh PPA + £15/MWh VLP = £165/MWh total
- **Profit: £66/MWh** ✅ (vs £51/MWh without VLP)

---

## Decision Logic: Battery First, Direct Import Second

**TWO-STEP PRIORITY SYSTEM**:

### Step 1: Check Battery (Stream 2 - Priority)
```
FOR each_settlement_period:
    IF battery_charged AND available:
        → Use Stream 2 (discharge + VLP)
        → Revenue: £165/MWh (£150 PPA + £15 VLP)
        → Cost: £99/MWh (levies paid once)
        → Profit: £66/MWh ✅
        → Period USED by battery
```

### Step 2: All Other Periods (Stream 1 - Fallback)
```
FOR each_remaining_period (not using battery):
    → Use Stream 1 (direct import)
    → Revenue: £150/MWh (PPA contract)
    → Cost: Market + DUoS + Levies
    → Profit: £150 - Cost (can be + or -)
    → Contract obligation (must supply)
```

**Example 24-Hour Period**:

| Time | SP | Band | Battery? | Logic |
|------|----|----|----------|-------|
| 00:00-08:00 | 1-16 | 🟢 Green | Charge | Cost £139 → Profit £11 + Charge for later |
| 08:00-16:00 | 17-32 | 🟡 Amber | Maybe | Cost £170 → Loss £20. Use battery if available |
| 16:00-19:30 | 33-39 | 🔴 Red | **Discharge** | Cost £355 → Loss £205! **Battery saves £271/MWh** |
| 19:30-22:00 | 40-44 | 🟡 Amber | Maybe | Cost £170 → Loss £20. Use battery if available |
| 22:00-24:00 | 45-48 | 🟢 Green | Charge | Cost £139 → Profit £11 + Charge for later |

**Battery Value**:
- Converts RED losses (-£205/MWh) → Profits (+£66/MWh) = **£271/MWh swing!**
- Adds VLP revenue: +£15/MWh
- Reduces levy costs: Paid once vs every period
- Handles ~4,000 periods/year (battery discharge)
- Remaining ~13,500 periods/year (direct import)

**Streams are NOT additive**: Each period uses ONE method only.

---

## Sheet Structure

### Non-BESS Element (Columns A-C)
Shows direct import costs:
- Row 28-30: DUoS costs (Red/Amber/Green)
- Row 31-32: TNUoS, BSUoS
- Row 35-37: CCL, RO, FiT
- Row 40-42: System Buy Price
- **Total = Import costs when no battery available**

### BESS Element (Columns E-H)
Shows battery charging costs:
- Row 28-30: Charging MWh by DUoS band
- Row 32-37: Levies (paid ONCE on charging)
- **Total = Charging costs (levies included)**

### Revenue (Rows 43-48)
- Row 45: PPA price £150/MWh
- Row 45: Import volume + Discharge volume
- Row 48: Total PPA revenue

### Profit Analysis (Rows 50-62)
- Stream 1: Import profit (no battery)
- Stream 2: Battery profit (discharge - charging)
- Total: Combined annual profit

---

## Script: calculate_btm_ppa_revenue_complete.py

**What it does**:
1. Reads actual import volumes from sheet (Non-BESS columns B28-B37)
2. Reads actual costs from sheet (Non-BESS columns C28-C42)
3. Calculates Stream 1 profit: Revenue - Costs
4. Queries BigQuery for system prices
5. Calculates battery charging strategy (Green priority)
6. Calculates Stream 2 profit: Discharge revenue - Charging costs
7. Writes results to sheet rows 50-62

**Run**: `python3 calculate_btm_ppa_revenue_complete.py`

---

## Key Insights

✅ **Stream 1 is independent**: Makes profit without battery  
✅ **Stream 2 adds value**: Battery + VLP revenue  
✅ **Levies paid once**: Battery charges pay levies, discharge = £0 additional  
✅ **VLP bonus**: £15/MWh avg from National Grid on top of PPA  
⚠️ **Capacity constraint**: Same period = ONE stream only (must choose!)  
✅ **Optimization needed**: Allocate each period to most profitable stream  
✅ **Battery advantages over Stream 1**:
   - Lower cost (levies paid once)
   - Higher revenue (PPA + VLP)
   - Time-shift from cheap to expensive periods  

---

*Last Updated: December 2, 2025*
