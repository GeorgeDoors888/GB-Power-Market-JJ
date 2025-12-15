# SO Flag Analysis Summary - Energy vs System Actions

**Analysis Date:** December 15, 2025  
**Data Source:** Combined BOALF (historical + IRIS streaming)  
**Coverage:** January 2022 - December 14, 2025 (12.35M acceptances)

---

## 📊 Executive Summary

**KEY FINDING:** **80-84% of all Balancing Mechanism actions are for system/constraint management, NOT energy shortfall**

### Multi-Period Comparison

| Period | Total Acceptances | Energy (True) | System (False) | Trend |
|--------|------------------|---------------|----------------|-------|
| **Last 30 days** | 690,860 | 16.5% | **83.5%** | Recent |
| **Last 90 days** | 1,835,813 | 16.4% | **83.6%** | Quarterly |
| **Last 6 months** | 3,410,960 | 15.4% | **84.6%** | Semi-annual |
| **Last 1 year** | 6,196,067 | 15.9% | **84.1%** | Annual |
| **Last 2 years** | 9,443,918 | 18.5% | **81.5%** | Long-term |
| **All data (2022+)** | 12,350,141 | 20.5% | **79.5%** | Baseline |

---

## 🔍 What the SO Flags Mean

### SO Flag = **True** (Energy Balancing)
- **System is short of energy**
- Generators instructed to **increase output** (offers accepted)
- Demand exceeds available supply
- **Example:** Wind drops unexpectedly, gas plants ramped up

### SO Flag = **False** (System/Constraint Action)
- **Grid constraint management**
- Could be:
  - Generators instructed to **reduce output** (bids accepted) - e.g., wind curtailment
  - Local transmission constraints requiring regional balancing
  - System security/stability actions
  - Frequency response
- **Example:** Too much wind in Scotland, congestion on transmission lines

---

## 📈 Key Insights

### 1. System Actions Dominate (79-85%)
- **Most BM activity is NOT about energy shortage**
- Grid operates with excess capacity but faces **transmission constraints**
- Wind curtailment is a major driver (see revenue analysis)

### 2. Trend Over Time
- **2022-2023:** 20.5% energy actions (higher)
- **2024-2025:** 15-17% energy actions (lower)
- **Interpretation:** More renewable capacity = more constraint management

### 3. MWh-Weighted Analysis
- Energy actions: **18.9%** of total MWh (smaller individual actions)
- System actions: **81.1%** of total MWh (larger constraint actions)
- **Wind curtailment produces very large MWh volumes**

---

## 💰 Revenue Implications (Last 30 Days)

From `analyze_accepted_revenue_so_flags_v2.py` analysis:

### Total Accepted Revenue: **£80.4M**
- **WIND bid revenue:** £172M (paid to turn DOWN - constraint management)
- **CCGT bid revenue:** -£56M (paying to turn down)
- **Overall VWAP:** £23.54/MWh

### SO Flag Split (690k acceptances):
- **False (83.5%):** System actions = £67M+ (estimated, mostly wind curtailment)
- **True (16.5%):** Energy balancing = £13M+ (estimated, gas/hydro ramping)

---

## 🎯 Business Applications

### 1. Battery Storage Strategy
- **83% of BM revenue is constraint-driven**, not energy-driven
- **Location matters:** Sites near transmission bottlenecks earn more
- **Wind-heavy regions:** More curtailment = more bid opportunities

### 2. VLP Revenue Forecasting
- Don't assume "system short of energy"
- **Model constraint patterns:**
  - Scotland-England interconnector limits
  - Local wind/solar saturation
  - Time-of-day transmission loading

### 3. Policy Analysis
- **Transmission upgrades reduce False-flag actions**
- Energy storage reduces need for wind curtailment
- **Grid flexibility > generation capacity** for revenue

---

## 📊 Data Quality & Methodology

### BOALF Data Sources
1. **Historical REST API** (`bmrs_boalf`): Jan 1, 2022 → Nov 4, 2025
   - 11.5M records
   - API now deprecated (404 error)
   
2. **IRIS Real-time Streaming** (`bmrs_boalf_iris`): Oct 30, 2025 → Dec 14, 2025
   - 870k records
   - Active and updating

**Combined Coverage:** Fully continuous from Jan 2022 to present

### MWh Proxy Calculation
```sql
MWh = ABS(AVG(levelFrom, levelTo)) × duration_hours
```
- Estimates energy volume per acceptance
- Uses MW level changes and time windows
- Not exact (BOALF lacks explicit MWh), but proportionally accurate

### Corrections Applied
1. ✅ Proper VWAP: `SUM(cashflow) / SUM(mwh)` (not `AVG(cashflow/mwh)`)
2. ✅ BOAV labeled as BMU×SP×direction aggregates (not acceptance counts)
3. ✅ Combined BOALF historical + IRIS for full coverage
4. ✅ EBOCF labeled as "indicative" cashflows

---

## 🔗 Related Analyses

- **`analyze_accepted_revenue_so_flags_v2.py`** - Revenue analysis with SO flags (supports 30/90/365/all days)
- **`analyze_so_flags_trend.py`** - Multi-period trend comparison (this analysis)
- **Google Sheets:** [SO Flag Trend Analysis](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA)

---

## 📝 Usage Examples

### Analyze Different Time Periods
```bash
# Last 30 days (default)
python3 analyze_accepted_revenue_so_flags_v2.py 30

# Last 90 days
python3 analyze_accepted_revenue_so_flags_v2.py 90

# Last year
python3 analyze_accepted_revenue_so_flags_v2.py 365

# All available data (Jan 2022 - present)
python3 analyze_accepted_revenue_so_flags_v2.py 0
```

### Multi-Period Trend Analysis
```bash
# Compare 6 different time periods
python3 analyze_so_flags_trend.py
```

---

## ⚠️ Important Notes

1. **SO Flag is operational classification**, not a perfect constraint marker
2. **"System" actions include multiple subcategories** (constraints, security, frequency)
3. **BOALF = acceptance-level data**, BOAV = settlement-aggregated volumes
4. **Revenue analysis uses EBOCF** (indicative, not final settled cashflows)
5. **Historical trend:** Energy % decreasing as renewable capacity increases

---

**Last Updated:** December 15, 2025  
**Maintainer:** George Major (george@upowerenergy.uk)  
**Repository:** https://github.com/GeorgeDoors888/GB-Power-Market-JJ
