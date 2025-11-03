# 📏 Generator Size Analysis - GB Power Market

## 🎯 Quick Answer

**Minimum Generator Size:** **0.001 MW** (1 kW)  
**Maximum Generator Size:** **1,484.44 MW** (1.48 GW)  

**Size Range:** From tiny 1 kW solar panels to massive 1.5 GW solar farm - a **1,484,440x difference!**

---

## 📊 Summary Statistics

| Metric | Value |
|--------|-------|
| **Minimum Capacity** | 0.001 MW (1 kW) |
| **Maximum Capacity** | 1,484.44 MW (1.48 GW) |
| **Average Capacity** | 25.90 MW |
| **Median Capacity** | 10.53 MW |
| **Total Capacity** | 182,960 MW (183 GW) |
| **Generators Analyzed** | 7,065 (with capacity > 0) |

---

## 🔬 Smallest Generators (Bottom 10)

All the smallest generators are **0.001 MW (1 kW)**:

| Rank | Capacity | Type | Name |
|------|----------|------|------|
| 1-7 | 0.001 MW | Various | Multiple tiny installations |
| 8 | 0.001 MW | Solar | Steerway farm |
| 9 | 0.001 MW | Storage | (storage facility) |
| 10 | 0.001 MW | Other | DRYNOCH RAAS FACILITY |
| 11-18 | 0.001 MW | Solar/Storage | Various PV & Battery systems |
| 19 | 0.002 MW | Solar | Wigston phase 2b |
| 20 | 0.011 MW | Solar | ELGIN |

**Note:** These 1 kW entries are likely:
- Data placeholders for projects under development
- Minimum capacity registrations
- Data entry errors (should be 0.1 MW or 1.0 MW)
- Test/demonstration projects

---

## 🏭 Largest Generators (Top 20)

| Rank | Capacity (MW) | Type | Name | Notes |
|------|--------------|------|------|-------|
| **1** | **1,484.44** | **Solar** | **Harborough Fields Farm** | 🥇 **Largest by far!** |
| 2 | 456.00 | Storage | Upper College Farm | Huge battery storage |
| 3 | 425.00 | Gas | SHOREHAM POWER | Major CCGT |
| 4 | 420.00 | Gas | GT YARMOUTH POWER STATION | Major CCGT |
| 5 | 400.00 | Storage | Church Road Farm | Battery storage |
| 6 | 399.00 | Biomass | Lynemouth Power Station | Former coal converted |
| 7 | 350.00 | Gas | KINGS LYNN POWER STATION | CCGT |
| 8 | 337.50 | Gas | PETERBOROUGH POWER STATION | CCGT |
| 9 | 322.00 | Wind | SHERINGHAM SHOAL OFFSHORE | Major offshore wind |
| 10 | 320.00 | Solar | Creyke Beck Solar | Huge solar farm |
| 11 | 315.00 | Wind | THANET WINDFARM | Major offshore wind |
| 12 | 314.10 | Solar | Pollington Solar PV & BESS | Solar + storage |
| 13 | 300.00 | Storage | SOUTHFLEET HOOK GREEN | Battery storage |
| 14-15 | 300.00 | Solar/Other | DATA NOT AVAILABLE | Large projects |
| 16 | 299.70 | Solar | Little Becks Solar, Wind and Storage | Multi-tech |
| 17 | 280.00 | Storage | Home farm | Battery storage |
| 18 | 263.00 | Storage | LAND AT HOOKERS FARM | Battery storage |
| 19 | 254.00 | Storage | Joyce Green | Battery storage |
| 20 | 250.00 | Storage | Old Hill Farm | Battery storage |

### 🏆 Key Observations:
- **Largest single generator:** Harborough Fields Solar Farm at **1,484 MW** (likely aggregated project or data error)
- **Storage dominates top 20:** 9 of top 20 are battery storage (456 MW max)
- **Gas still significant:** 5 major CCGT stations (337-425 MW each)
- **Offshore wind:** 2 major projects (Sheringham Shoal, Thanet)

---

## 📈 Size Distribution

### By Capacity Range

| Size Range | Count | Total Capacity (MW) | % of Total Capacity |
|------------|-------|---------------------|---------------------|
| **< 100 kW** | 26 | 0.4 | 0.0% |
| **100 kW - 1 MW** | 70 | 44.0 | 0.0% |
| **1 - 5 MW** | 2,265 | 5,879.0 | 3.2% |
| **5 - 10 MW** | 1,014 | 6,860.1 | 3.7% |
| **10 - 50 MW** | 2,722 | 76,767.9 | **42.0%** 🥇 |
| **50 - 100 MW** | 732 | 52,032.7 | **28.4%** 🥈 |
| **100 - 500 MW** | 242 | 39,891.8 | **21.8%** 🥉 |
| **> 1 GW** | 1 | 1,484.4 | 0.8% |
| **TOTAL** | **7,065** | **182,960.3** | **100.0%** |

### 📊 Key Insights:

1. **"Sweet Spot" is 10-50 MW:**
   - 2,722 generators (38.5% of all)
   - 76,768 MW capacity (42.0% of total)
   - Typical for: Solar farms, onshore wind, small CCGT

2. **50-100 MW is Second:**
   - 732 generators (10.4% of all)
   - 52,033 MW capacity (28.4% of total)
   - Typical for: Large solar, offshore wind connections, medium CCGT

3. **100-500 MW is Third:**
   - Only 242 generators (3.4% of all)
   - But 39,892 MW capacity (21.8% of total)
   - Typical for: Major offshore wind, large CCGT, battery storage

4. **Small Generators (<5 MW):**
   - 2,361 generators (33.4% of all)
   - But only 5,923 MW capacity (3.2% of total)
   - Many small embedded generators

---

## ⚡ Size by Energy Type

| Type | Count | Min (MW) | Max (MW) | Avg (MW) | Notes |
|------|-------|----------|----------|----------|-------|
| **Solar** | 2,748 | 0.001 | **1,484.44** | 21.49 | Huge range! |
| **Storage** (combined) | 1,312 | 0.001 | 456.00 | 56.63 | Large projects |
| **Wind** | 855 | 0.50 | 322.00 | 20.39 | Offshore largest |
| **Gas** | 1,111 | 0.33 | 425.00 | 10.78 | Many small CHPs |
| **Biomass** | 77 | 0.50 | 399.00 | 19.20 | Lynemouth largest |
| **Waste** | 179 | 1.02 | 89.00 | 14.44 | EfW plants |
| **Hydro** | 77 | 1.00 | 27.55 | 4.73 | Small run-of-river |
| **Fossil Oil** | 246 | 0.80 | 68.60 | 7.80 | Backup diesels |
| **Other** | 460 | 0.001 | 300.00 | varies | Mixed tech |

### 📊 Type-Specific Insights:

#### **Solar (2,748 generators)**
- **Smallest:** 0.001 MW (likely rooftop)
- **Largest:** 1,484.44 MW (Harborough Fields - appears to be aggregated)
- **Average:** 21.49 MW (typical solar farm size)
- **Distribution:** Mostly 1-50 MW farms

#### **Storage (1,312 generators)**
- **Average:** 56.63 MW (larger than solar!)
- **Largest:** 456.00 MW (Upper College Farm)
- **Trend:** Battery storage projects getting larger
- **Purpose:** Grid balancing, arbitrage

#### **Wind (855 generators)**
- **Smallest:** 0.5 MW (small turbine)
- **Largest:** 322.00 MW (Sheringham Shoal offshore)
- **Average:** 20.39 MW
- **Split:** Onshore 2-10 MW, Offshore 50-300 MW

#### **Gas (1,111 generators)**
- **Huge range:** 0.33 MW (tiny CHP) to 425 MW (major CCGT)
- **Average:** 10.78 MW (skewed by many small CHPs)
- **Split:** 
  - Small CHP: 0.3-5 MW (industrial, hospital)
  - Medium OCGT: 20-100 MW (peaking)
  - Large CCGT: 200-425 MW (baseload)

#### **Hydro (77 generators)**
- **Smallest:** 1.00 MW (micro-hydro)
- **Largest:** 27.55 MW (large run-of-river)
- **Average:** 4.73 MW (very consistent)
- **Type:** Mostly Scottish Highland run-of-river

---

## 🎯 Notable Extremes

### 🔬 Tiniest (≤ 0.011 MW / 11 kW)
These are likely:
- Demonstration projects
- Data placeholders
- Rooftop solar systems
- Test installations

### 🏭 Largest Single Sites

1. **Harborough Fields Solar** - 1,484 MW
   - ⚠️ **Warning:** This seems unusually large for a single solar farm
   - Likely an **aggregated project** or **data error**
   - Typical large UK solar farms: 50-350 MW
   - May represent multiple phases/projects

2. **Upper College Farm Storage** - 456 MW
   - One of UK's largest battery storage facilities
   - Grid-scale energy storage

3. **Shoreham Power CCGT** - 425 MW
   - Major gas-fired power station
   - Combined Cycle Gas Turbine

---

## 📊 Capacity Concentration

### Where is the capacity?
- **92.2%** of total capacity is in generators **≥ 10 MW**
- **50.2%** of total capacity is in generators **≥ 50 MW**
- **22.6%** of total capacity is in generators **≥ 100 MW**

### Generator Count vs Capacity
- **66.6%** of generators are **< 10 MW** (small)
- But they only represent **7.7%** of total capacity
- The **242 largest generators** (3.4%) hold **21.8%** of capacity

---

## 🔍 Data Quality Notes

### Suspicious Entries:
1. **19 generators at exactly 0.001 MW** - Likely placeholders
2. **Harborough Fields at 1,484 MW** - Unusually large, may be aggregated
3. **Several "DATA NOT AVAILABLE" entries** - Incomplete records

### Realistic Ranges by Type:
- **Rooftop Solar:** 0.005 - 0.5 MW
- **Solar Farms:** 5 - 350 MW
- **Onshore Wind:** 2 - 50 MW
- **Offshore Wind:** 100 - 1,200 MW (project level)
- **Battery Storage:** 10 - 500 MW
- **Gas CCGT:** 200 - 2,000 MW
- **Hydro:** 1 - 100 MW

---

## 💡 Key Takeaways

1. **Massive Size Dispersion**
   - Range: 1 kW to 1,484 MW (1.5 million times!)
   - Median: 10.53 MW (typical project size)
   - Average: 25.90 MW (pulled up by large projects)

2. **Storage is Getting Large**
   - Average storage project: 56.63 MW
   - Largest: 456 MW
   - Trend: Grid-scale battery deployment

3. **Solar Dominates by Count**
   - 2,748 solar generators (38.9%)
   - But only 21.49 MW average
   - Many small-to-medium farms

4. **A Few Giants Dominate Capacity**
   - Top 242 generators (3.4%) = 21.8% of capacity
   - Top 974 generators (13.8%) = 50% of capacity

5. **Distributed vs Centralized**
   - 4,626 generators < 50 MW (65.5%) = 6.9% capacity (distributed)
   - 974 generators ≥ 50 MW (13.8%) = 50% capacity (centralized)

---

**Analysis Date:** November 1, 2025  
**Data Source:** NESO All_Generators.xlsx  
**Generators Analyzed:** 7,065 (with capacity > 0)  
**Total Capacity:** 182,960 MW (183 GW)
