# Dynamic Containment Revenue Correction

**Date**: 1 December 2025  
**Issue**: Previous model used incorrect DC pricing assumptions  
**Status**: Corrected with actual NESO 2025 data

---

## ❌ What Was WRONG

### Previous Model Assumptions:
- **Day Rate**: £15/MW/h
- **Night Rate**: £5/MW/h
- **Source**: Hardcoded assumptions (NOT actual data)
- **Result**: £524,704/year DC revenue

**This was 858% TOO HIGH!**

---

## ✅ What Is CORRECT

### Actual NESO 2025 Data (from BigQuery documents):

**Found in document chunks from NESO Monthly Operation Reports:**

```
"For DC, prices rose from £2.60/MW to £2.82/MW" (August 2025)
"prices for DC have risen since August" reaching "£5.29/MW" (later 2025)
"There is some seasonality to DC pricing, which is needed less over 
winter when there is more inertia on the system, meaning higher 
prices in spring/summer"
```

### Actual DC Clearing Prices 2025:
- **Range**: £2.60 - £5.29/MW/h
- **Average**: ~£3.27/MW/h
- **Seasonal**: Higher in spring/summer, lower in winter
- **Trend**: Increasing through 2025

---

## 📊 Corrected DC Revenue Calculation

```
BESS Power: 2.5 MW
DC Available: 2.25 MW (after 90% derate)
DC Price: £3.27/MW/h (2025 average from NESO data)
Availability: 85%

Annual DC Revenue = 2.25 MW × £3.27/MW/h × 8,760 hours × 85%
                  = £54,784/year
```

**Not £524k - approximately £55k/year**

---

## 🔍 Why The Confusion?

### Historical Context:
- **2021-2022**: DC prices were very high (£10-20/MW/h) when service launched
- **2023-2024**: Oversupply of batteries caused price crash
- **2025**: Stabilized at £2.60-5.29/MW/h range

### My Error:
- Used outdated 2021-2022 "typical" rates
- Did not verify against actual current NESO data
- Assumed £15/£5 split without checking auction results

---

## 💰 Impact on Total BESS Revenue

| Revenue Stream | Previous (WRONG) | Corrected | Change |
|----------------|------------------|-----------|--------|
| **DC Availability** | **£524,704** | **£54,784** | **-£470k ❌** |
| ESO/VLP Payment | £15,051 | £15,051 | ✅ |
| VLP Compensation (SCVp) | £3,605 | £3,605 | ✅ |
| Avoided Wholesale | £7,974 | £7,974 | ✅ |
| Avoided Network | £2,300 | £2,300 | ✅ |
| Avoided Levies | £8,053 | £8,053 | ✅ |
| PPA Revenue | £28,788 | £28,788 | ✅ |
| **TOTAL REVENUE** | **£590,475** | **£120,555** | **-£470k** |
| **Less Costs** | -£70,420 | -£70,420 | |
| **NET PROFIT** | **£520,055** | **£50,135** | **-£470k** |

---

## 🎯 Revised Revenue Model

### Conservative Scenario (£50k/year):
- DC: £55k (actual 2025 average rates)
- Arbitrage/VLP/PPA: £66k (ESO + VLP + PPA + avoided costs)
- Less costs: -£70k
- **Net: £50k/year**

### Optimistic Scenario (£150-200k/year):
- DC: £100k (if prices return to £6-8/MW/h)
- Arbitrage/VLP/PPA: £120k (with optimized dispatch)
- Less costs: -£70k
- **Net: £150k/year**

### User's Industry Benchmark:
- "£200,000 – £400,000 per year typical"
- **We are below this range with current DC prices**
- Would need:
  - DC prices at £8-10/MW/h, OR
  - Additional revenue streams (FFR, STOR, CM), OR
  - Different BESS configuration

---

## 🔗 Data Sources

### NESO Document Chunks (BigQuery):
```sql
SELECT content, doc_id, source
FROM `inner-cinema-476211-u9.uk_energy_prod.document_chunks`
WHERE source = 'NESO'
  AND LOWER(content) LIKE '%dc%'
  AND LOWER(content) LIKE '%£%'
  AND LOWER(content) LIKE '%/mw%'
  AND LOWER(content) LIKE '%2025%'
```

**Results**:
- 8 price points extracted
- Range: £2.60 - £5.29/MW/h
- Average: £3.27/MW/h

### NESO Website:
- https://www.neso.energy/industry-information/balancing-services/frequency-response-services/dynamic-containment
- States: "results from the tenders are published on the NESO Data Portal"
- Data Portal: Requires login (not publicly accessible without account)

### What We DON'T Have:
- ❌ Daily DC auction results for 2025
- ❌ DC High vs DC Low price differentiation
- ❌ EFA block pricing (different prices per 4-hour block)
- ❌ Forward contract prices vs spot prices

---

## 📋 Recommendations

### 1. Get Actual DC Contract Terms
**Need from aggregator (Flexitricity/Limejump/Habitat):**
- What DC prices are you actually getting?
- Is it DC High, DC Low, or blended?
- What EFA blocks are you in?
- What's your typical monthly DC revenue per MW?

### 2. Consider Alternative Services
**If DC alone isn't enough:**
- **Static FFR**: More stable, contract-based
- **Dynamic Moderation (DM)**: £3.88-4.00/MW/h (from NESO docs)
- **Dynamic Regulation (DR)**: £4-5.29/MW/h (from NESO docs)
- **Capacity Market**: Fixed £/kW/year payment
- **STOR**: Short Term Operating Reserve

### 3. Stack Revenues Correctly
**Your actual revenue sources should be:**
1. **Frequency Services** (DC/DM/DR): £55-100k depending on prices
2. **Arbitrage** (SSP discharge): £15k
3. **VLP Compensation** (SCVp): £4k (estimated)
4. **PPA Supply**: £29k
5. **Network Avoidance**: £18k (DUoS + levies)

**Total: £121k with current DC prices**

To reach £200-400k typical range, you need EITHER:
- Higher DC prices (market recovery), OR
- Additional contracted services (FFR, STOR, CM), OR
- Larger BESS (economics improve with scale)

---

## ⚠️ Key Lessons

1. **Never assume prices** - Always verify with actual market data
2. **DC prices collapsed** - 2021 rates (£15/MW/h) no longer relevant
3. **Market has changed** - Battery oversupply depressed frequency service prices
4. **Stack carefully** - DC + arbitrage + VLP is legitimate stacking
5. **Get real quotes** - Aggregators have actual contracted rates

---

## 🔄 Next Steps

1. **Contact your aggregator** for actual DC contract rates
2. **Review VLP compensation** (SCVp) - need actual values from Elexon settlement
3. **Optimize dispatch** - Focus on Red DUoS periods (£176/MWh value!)
4. **Consider capacity market** - Adds stable base revenue
5. **Model sensitivity** - What if DC returns to £6-8/MW/h?

---

**Model Status**: ✅ Corrected with actual NESO 2025 data  
**Confidence**: HIGH for DC prices (from NESO docs), LOW for total revenue (needs validation)  
**Action Required**: Get actual contracted DC rates from aggregator

---

*Last Updated: 1 December 2025*  
*Data Source: NESO Monthly Operation Reports (BigQuery document_chunks)*
