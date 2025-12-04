# 💰 GB Power Market - Energy Costs & Levies Breakdown

## 📋 **Fixed National Levies (2025/26)**

All costs in **£/kWh** unless stated otherwise.

### **1. Climate Change Levy (CCL)**
- **Rate:** £0.00775/kWh (0.775 p/kWh)
- **Type:** Fixed national tax
- **Applied to:** All electricity consumption
- **Purpose:** Government environmental tax
- **Annual Review:** Budget announcement (March)

### **2. Renewables Obligation (RO)**
- **Rate:** £0.0619/kWh (6.19 p/kWh)
- **Type:** Fixed levy
- **Applied to:** All consumption
- **Purpose:** Support renewable energy generation
- **Note:** Highest single levy component

### **3. Feed-in Tariff (FiT)**
- **Rate:** £0.0115/kWh (1.15 p/kWh)
- **Type:** Fixed levy
- **Applied to:** All consumption
- **Purpose:** Support small-scale renewable generation
- **Status:** Closed to new generators (legacy scheme)

### **4. Balancing Services Use of System (BSUoS)**
- **Average Rate:** £0.0045/kWh (0.45 p/kWh)
- **Type:** Variable (changes daily)
- **Applied to:** All consumption
- **Purpose:** National Grid balancing costs
- **Volatility:** Can vary ±50% day-to-day

### **5. Transmission Network Use of System (TNUoS)**
- **HV Rate:** £0.0125/kWh (1.25 p/kWh)
- **Type:** Zone-dependent
- **Applied to:** Based on location & voltage
- **Purpose:** Transmission infrastructure costs
- **Variation:** Higher in remote areas

---

## 🏢 **Distribution Use of System (DUoS)**

**Variable by DNO, Voltage Level, and Time Band**

### **Rate Structure:**

| Time Band | Typical Range | **ACTUAL: EMID HV (From BESS Sheet)** |
|-----------|---------------|----------------------------------------|
| **RED** (Peak) | 3.5 - 8.0 p/kWh | **1.764 p/kWh (£0.01764)** |
| **AMBER** (Shoulder) | 1.2 - 3.5 p/kWh | **0.205 p/kWh (£0.00205)** |
| **GREEN** (Off-peak) | 0.3 - 1.2 p/kWh | **0.011 p/kWh (£0.00011)** |

### **Time Bands (ACTUAL - From BESS Sheet):**
- **RED:** **08:00-16:00 weekdays** (Daytime business hours)
- **AMBER:** **19:30-22:00 weekdays** (Evening)
- **GREEN:** **All other times** (Overnight 22:00-08:00 + 16:00-19:30 + weekends)

### **Time Bands (Standard Ofgem Reference):**
- **RED:** 16:00-19:00 weekdays (Nov-Feb)
- **AMBER:** 07:30-16:00, 19:00-23:00 weekdays
- **GREEN:** 23:00-07:30 weekdays + all weekend

### **Voltage Level Multipliers:**
- **EHV** (Extra High Voltage): Lowest rates (0.3x)
- **HV** (High Voltage): Medium rates (1.0x baseline)
- **LV** (Low Voltage): Highest rates (1.8x)

### **DNO Variations (14 regions):**

| DNO | Region | Typical HV Red Rate |
|-----|--------|---------------------|
| NGED-WM | West Midlands | 5.2 p/kWh |
| UKPN-EPN | East England | 4.8 p/kWh |
| **NGED-EM (EMID)** | **East Midlands** | **1.764 p/kWh** ⭐ **(YOUR BESS)** |
| NGED-SW | South West | 5.5 p/kWh |
| NGED-WA | Wales | 5.3 p/kWh |
| SSEN-SSES | Southern Scotland | 5.8 p/kWh |
| SPEN-SPM | Central Scotland | 6.1 p/kWh |
| NPEN-NE | North East | 5.6 p/kWh |
| NPEN-NW | North West | 5.4 p/kWh |
| UKPN-LPN | London | 4.5 p/kWh |
| UKPN-SPN | South East | 4.7 p/kWh |
| SSEN-SSES | South England | 5.0 p/kWh |
| SHET | North Scotland | 6.5 p/kWh |
| EMEB | Merseyside | 5.2 p/kWh |

---

## 💡 **Total Cost Example (20 MWh BESS)**

### **Scenario A: Generic Example (HV connection, NGED-WM, balanced load profile)**

**Daily Consumption: 20 MWh (20,000 kWh)**

| Cost Component | Rate | Daily Cost | Annual Cost |
|----------------|------|------------|-------------|
| **CCL** | £0.00775/kWh | £155 | £56,575 |
| **RO** | £0.0619/kWh | £1,238 | £451,870 |
| **FiT** | £0.0115/kWh | £230 | £83,950 |
| **BSUoS** (avg) | £0.0045/kWh | £90 | £32,850 |
| **TNUoS** (HV) | £0.0125/kWh | £250 | £91,250 |
| **DUoS** (weighted) | ~£0.025/kWh | £500 | £182,500 |
| **TOTAL LEVIES** | **£0.1281/kWh** | **£2,463** | **£899,000** |

### **Energy Cost (SSP):**
- System Sell Price: ~£50-100/MWh (£0.05-0.10/kWh)
- **Daily Energy:** £1,000 - £2,000
- **Annual Energy:** £365,000 - £730,000

### **TOTAL ALL-IN COST:**
- **Daily:** £3,463 - £4,463
- **Annual:** £1.26M - £1.63M
- **Per kWh:** **£0.173 - £0.223/kWh**

---

## 🔄 **BESS Optimization Strategy**

### **Time-Shift Arbitrage:**

**Charge during GREEN band (23:00-07:30):**
- Energy cost: £50/MWh
- DUoS: £0.007/kWh
- Total levies: £0.135/kWh
- **All-in:** £0.185/kWh

**Discharge during RED band (16:00-19:00):**
- Energy revenue: £100/MWh
- DUoS avoided: £0.052/kWh
- **Net revenue:** £0.100/kWh

**Spread per cycle: £0.100 - £0.185 = -£0.085/kWh**
*Note: Negative means arbitrage requires >100% spread to be profitable after levies*

### **Key Insight:**
Fixed levies (CCL, RO, FiT, BSUoS, TNUoS) = **£0.1081/kWh** apply regardless of time, making pure arbitrage difficult. Revenue must come from:
- **Frequency response** services (FFR, DCR)
- **Capacity market** payments
- **Balancing mechanism** (BM) bids
- **Demand side response** (DSR)

---

## 📊 **Rate Sources & Updates**

### **Ofgem Published Rates:**
- **DUoS:** Updated April 1st annually (each DNO publishes tariff schedule)
- **TNUoS:** Published by National Grid ESO (zone-specific)
- **BSUoS:** Daily rates published by National Grid ESO

### **Government Set Rates:**
- **CCL:** HM Treasury (Budget announcement)
- **RO:** BEIS/DESNZ (annual obligation level)
- **FiT:** Ofgem (legacy scheme, rates fixed)

### **System Access:**
- **BigQuery Tables:** 
  - `uk_energy_prod.duos_tariff_rates` (207 rows: 14 DNOs × 3 voltages × 3 bands)
  - `uk_energy_prod.dno_duos_rates` (time band definitions)
  - `uk_energy_prod.balancing_prices` (SSP/SBP)

---

## 🎯 **Key Takeaways**

1. **Fixed levies dominate:** 10.81 p/kWh before energy or DUoS
2. **RO is largest:** 6.19 p/kWh (57% of fixed levies)
3. **DUoS varies 10x:** RED vs GREEN (critical for optimization)
4. **Total all-in cost:** 17.3 - 22.3 p/kWh for typical HV BESS
5. **Arbitrage threshold:** Need >8.5 p/kWh spread minimum

**For BESS profitability, focus on:**
- Avoiding RED band charging
- Maximizing GREEN band charging
- Stacking revenue streams (FFR + CM + DSR)
- Minimizing cycling losses (round-trip efficiency)

---

**Last Updated:** November 30, 2025  
**Rates Valid:** 2025/26 financial year  
**Source:** Ofgem, National Grid ESO, BEIS/DESNZ

---

### **Scenario B: YOUR 2.5MW BESS (ACTUAL - From BESS Sheet)**

**Configuration:**
- **Location:** EMID (East Midlands)
- **Voltage:** HV (6.6-33kV)
- **Capacity:** 2.5 MW / 2.5 MWh (1-hour duration)
- **PPA Rate:** £150/MWh (£0.15/kWh)
- **DUoS Rates:** RED 1.764p | AMBER 0.205p | GREEN 0.011p
- **Time Bands:** RED 08:00-16:00 | AMBER 19:30-22:00 | GREEN Other

**Daily Operation (Example: 1 cycle/day, 2.5 MWh):**

| Cost Component | Rate | Daily Cost | Annual Cost |
|----------------|------|------------|-------------|
| **CCL** | £0.00775/kWh | £19.38 | £7,073 |
| **RO** | £0.0619/kWh | £154.75 | £56,484 |
| **FiT** | £0.0115/kWh | £28.75 | £10,494 |
| **BSUoS** (avg) | £0.0045/kWh | £11.25 | £4,106 |
| **TNUoS** (HV) | £0.0125/kWh | £31.25 | £11,406 |
| **DUoS** (GREEN charge) | £0.00011/kWh | £0.28 | £101 |
| **DUoS** (RED discharge avoid) | -£0.01764/kWh | -£44.10 | -£16,097 |
| **TOTAL LEVIES** | **£0.0900/kWh** | **£225** | **£82,125** |

**Energy Economics:**
- **PPA Revenue:** 2.5 MWh × £150/MWh = **£375/day** (£136,875/year)
- **Less Levies:** £225/day (£82,125/year)
- **Net Revenue:** **£150/day** (£54,750/year)

**With Round-Trip Efficiency (85%):**
- Actual discharge: 2.5 × 0.85 = 2.125 MWh
- PPA Revenue: £318.75/day
- Less Levies: £225/day
- **Net Revenue:** **£93.75/day** (£34,219/year)

**Key Insight:**
Your EMID HV rates are **exceptionally low** compared to typical UK rates:
- RED: 1.764p vs typical 5.2p (66% lower!)
- GREEN: 0.011p vs typical 0.7p (98% lower!)

This makes your BESS **highly profitable** for arbitrage at £150/MWh PPA rate.

---

## 🎯 **Analysis Required (From Your BESS Sheet)**

Based on your configuration, here's what needs analysis:

1. **Optimal Charge/Discharge Schedule**
   - Charge: GREEN band (22:00-08:00 + 16:00-19:30) at 0.011p DUoS
   - Discharge: RED band (08:00-16:00) at 1.764p DUoS saved
   - Spread: 1.753p DUoS + £150/MWh PPA

2. **Revenue Stacking Opportunities**
   - PPA: £150/MWh base
   - DUoS avoided: 1.753p/kWh
   - Frequency response: FFR/DCR on top
   - Capacity market: Additional revenue

3. **Cost Breakdown Required**
   - "BtM PPA Non BESS Element Costs" (Your sheet Row 26)
   - "BtM PPA BESS Costs" (Your sheet Row 27-37)
   - Need to populate kWh and Costs columns (B27-C37, E27-F37)

4. **Battery Efficiency Issue**
   - B19 shows "2500" (should be 0.85-0.95)
   - Need to correct this for accurate analysis

5. **Environmental Levies**
   - CCL, RO, FiT calculations for both scenarios
   - Showing how BESS reduces total levy burden

---

**Updated:** November 30, 2025 (with actual BESS sheet values)  
**Next Step:** Run analysis scripts to populate cost columns in BESS sheet
