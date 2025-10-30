# Multi-Year Download Plan - 2022-2025

**Date**: October 26, 2025  
**Status**: 🚀 **IN PROGRESS** - 2025 data downloading

---

## 📊 Download Strategy

### What's Being Downloaded

Using the **dynamically discovered manifest** (`insights_manifest_dynamic.json`) with **44 verified working datasets** for each year:

| Year | Date Range | Days | Status |
|------|------------|------|--------|
| 2025 | Jan 1 - Oct 26 | 299 | 🔄 **IN PROGRESS** |
| 2024 | Jan 1 - Dec 31 | 366 | ⏳ Queued |
| 2023 | Jan 1 - Dec 31 | 365 | ⏳ Queued |
| 2022 | Jan 1 - Dec 31 | 365 | ⏳ Queued |

**Total**: 1,395 days across 44 datasets = **~61,380 dataset-days** of data!

---

## 🔍 What Makes This Different

### Previous Approach:
- Used `insights_manifest_comprehensive.json`
- 42 "datasets" (but 8 returned 404 errors)
- Missing 25 working datasets (PN, QPN, BOALF, MELS, MILS, etc.)
- **Only 34 actually working datasets**

### New Approach:
- Uses `insights_manifest_dynamic.json`
- **44 verified working datasets**
- All URLs tested and confirmed working
- Includes previously "missing" datasets:
  - ✅ PN (Physical Notifications)
  - ✅ QPN (Quiescent Physical Notifications)
  - ✅ BOALF (Bid Offer Acceptances)
  - ✅ MELS (Max Export Limits)
  - ✅ MILS (Max Import Limits)
  - ✅ And 20 more!

---

## 📋 The 44 Datasets Being Downloaded

### Balancing Mechanism (16 datasets):
1. **BOD** - Bid Offer Data
2. **BOALF** - Bid Offer Acceptance Level ✨ NEW
3. **DISBSAD** - Disaggregated Balancing Services
4. **NETBSAD** - Net Balancing Services
5. **QAS** - Quiescent Acceptances
6. **PN** - Physical Notifications ✨ NEW
7. **QPN** - Quiescent Physical Notifications ✨ NEW
8. **MELS** - Maximum Export Limits ✨ NEW
9. **MILS** - Maximum Import Limits ✨ NEW
10. **SEL** - Stable Export Limit
11. **SIL** - Stable Import Limit ✨ NEW
12. **MZT** - Minimum Zero Time ✨ NEW
13. **MNZT** - Minimum Non-Zero Time ✨ NEW
14. **MDV** - Maximum Delivery Volume ✨ NEW
15. **MDP** - Maximum Delivery Period ✨ NEW
16. **NONBM** - Non-BM STOR

### Generation (4 datasets):
17. **FUELINST** - Fuel Type Instant
18. **FUELHH** - Fuel Type Half-Hourly
19. **INDGEN** - Individual Generation
20. **WINDFOR** - Wind Forecast

### Demand (3 datasets):
21. **INDDEM** - Indicated Demand ✨ NEW
22. **MELNGC** - Max Export Limit NGC ✨ NEW
23. **IMBALNGC** - Imbalance NGC

### Forecasts (11 datasets):
24. **NDF** - National Demand Forecast
25. **NDFD** - National Demand Forecast Day Ahead
26. **NDFW** - National Demand Forecast Week Ahead
27. **TSDF** - Transmission System Demand Forecast
28. **TSDFD** - Transmission System Demand Forecast Day Ahead
29. **TSDFW** - Transmission System Demand Forecast Week Ahead ✨ NEW
30. **UOU2T14D** - Output Usable 2-14 Days
31. **UOU2T3YW** - Output Usable 2-52 Weeks ✨ NEW
32. **OCNMF3Y** - Output Capacity 2-156 Weeks ✨ NEW
33. **OCNMF3Y2** - Output Capacity variant ✨ NEW
34. **OCNMFD** - Output Capacity Day Ahead ✨ NEW

### Additional datasets (10):
35. **OCNMFD2** - Output Capacity Day Ahead variant ✨ NEW
36. **FREQ** - System Frequency
37. **MID** - Market Index Data
38. **NDZ** - Notice to Deviate from Zero ✨ NEW
39. **NTB** - Notice to Deliver Bids ✨ NEW
40. **NTO** - Notice to Deliver Offers ✨ NEW
41. **RURE** - Ramp Up Rate Export ✨ NEW
42. **RURI** - Ramp Up Rate Import ✨ NEW
43. **RDRE** - Ramp Down Rate Export ✨ NEW
44. **RDRI** - Ramp Down Rate Import ✨ NEW

**✨ NEW = 25 datasets that were previously missing!**

---

## ⏱️ Estimated Timeline

### Per Year Estimates:

**Fast Datasets (most)**: ~30-40 seconds each
- 35 datasets × 40 seconds = ~23 minutes

**Slow Datasets (with constraints)**:
- **MELS, MILS** (hourly chunks): ~2-3 hours each for a full year
  - 365 days × 24 hours = 8,760 API calls per dataset
  - At 0.1s per call = ~15 minutes per dataset per year
  - Both together: ~30 minutes

**Total per year**: ~1 hour

### Full Timeline:
- **2025** (299 days): ~50 minutes ⏳ Currently running
- **2024** (366 days): ~1 hour
- **2023** (365 days): ~1 hour  
- **2022** (365 days): ~1 hour

**Total estimated time**: **~3-4 hours for all 4 years**

---

## 📊 Expected Data Volumes

### Records per Year (rough estimates):

| Dataset Type | Records/Year | × 4 Years |
|--------------|--------------|-----------|
| High Frequency (PN, QPN, MELS, MILS, BOD) | ~15M | ~60M |
| Medium Frequency (FREQ, INDGEN, INDDEM) | ~500K | ~2M |
| Low Frequency (Forecasts, limits) | ~50K | ~200K |
| **Total** | **~20-25M** | **~80-100M records** |

### BigQuery Storage:
- Compressed: ~50-100 GB
- Uncompressed: ~200-400 GB

---

## 🔧 Special Handling

### Datasets with Constraints:

**1-Hour Maximum Range** (requires 8,760 calls per year):
- MELS (Max Export Limits)
- MILS (Max Import Limits)

These will prompt you before downloading to confirm you want to proceed with many API calls.

**1-Day Maximum Range** (requires 365 calls per year):
- BOALF (Bid Offer Acceptances)
- NONBM (Non-BM volumes)

These are handled automatically with daily chunks.

---

## 📈 What You'll Be Able to Analyze

With 4 years of complete data across 44 datasets, you'll be able to:

### Year-over-Year Analysis:
- ✅ Compare balancing costs 2022 vs 2025
- ✅ Track renewable generation growth
- ✅ Identify seasonal patterns across years
- ✅ Analyze grid constraint evolution
- ✅ Study market price trends

### Comprehensive Grid Analysis:
- ✅ Physical notifications (PN/QPN) - who's generating what, when
- ✅ Export/import limits (MELS/MILS) - grid constraints
- ✅ Bid-offer acceptances (BOALF) - what's being dispatched
- ✅ Ramp rates (RURE/RDRE) - flexibility analysis
- ✅ Forecast accuracy - predicted vs actual

### Previously Impossible Analyses (now possible with new datasets):
- ✅ BMU-level physical scheduling (PN/QPN)
- ✅ Grid constraint mapping (MELS/MILS)
- ✅ Acceptance patterns (BOALF)
- ✅ Flexibility capabilities (ramp rates)

---

## 🚀 Next Steps

### After 2025 Completes:

1. **Review 2025 results**
   - Check for any errors
   - Verify data quality
   - Identify any special cases

2. **Download remaining years**
   ```bash
   # Download 2024
   python download_multi_year.py 2024
   
   # Download 2023
   python download_multi_year.py 2023
   
   # Download 2022
   python download_multi_year.py 2022
   
   # Or all at once (will take ~4 hours)
   python download_multi_year.py
   # Then select option 5 (All years)
   ```

3. **Run analysis across years**
   - Compare data completeness across years
   - Identify any missing periods
   - Create year-over-year dashboards

---

## 📊 Monitoring Progress

### Current Download (2025):

Check terminal output for:
- ✅ Successful dataset downloads
- ⚠️ Warnings (no data for certain periods)
- ❌ Errors (API issues, rate limits)

### Results Files:

After each run, a results file is generated:
```
multi_year_download_results_YYYYMMDD_HHMMSS.json
```

Contains:
- Summary statistics per year
- Detailed results per dataset
- Error messages
- Record counts

---

## 🎯 Success Metrics

### Target Completion:

| Metric | Target | Current |
|--------|--------|---------|
| Datasets per year | 44 | ✅ 44 |
| Years | 4 | ⏳ 1/4 in progress |
| Success rate | >90% | TBD |
| Total records | ~80-100M | TBD |

### Known Challenges:

1. **Rate limiting**: Built-in delays between requests
2. **API timeouts**: Automatic retries with exponential backoff
3. **Large datasets**: PN/QPN/MELS/MILS may take longer
4. **Historical data gaps**: Some datasets may not have data for all historical periods

---

## 📝 Documentation to Create

After all downloads complete, I'll create:

1. **Data Completeness Report**
   - What datasets downloaded successfully
   - Any gaps in historical data
   - Comparison across years

2. **Year-over-Year Analysis**
   - Data volume trends
   - Dataset availability by year
   - Quality assessment

3. **Updated Comparison**
   - Old manifest (34 working datasets) vs New manifest (44 datasets)
   - What you were missing
   - Impact on analysis capabilities

---

## ⚙️ Technical Details

### BigQuery Table Structure:

Each dataset gets a table per year:
```
uk_energy_prod.dataset_name_YYYY
```

Examples:
- `uk_energy_prod.pn_2025`
- `uk_energy_prod.pn_2024`
- `uk_energy_prod.pn_2023`
- `uk_energy_prod.pn_2022`

### Query Pattern:

To analyze across all years:
```sql
SELECT * FROM (
  SELECT *, 2025 as year FROM `uk_energy_prod.pn_2025`
  UNION ALL
  SELECT *, 2024 as year FROM `uk_energy_prod.pn_2024`
  UNION ALL
  SELECT *, 2023 as year FROM `uk_energy_prod.pn_2023`
  UNION ALL
  SELECT *, 2022 as year FROM `uk_energy_prod.pn_2022`
)
WHERE settlementDate BETWEEN '2022-01-01' AND '2025-10-26'
```

---

## ✅ Summary

**What's happening now**:
- 2025 data downloading with all 44 datasets
- Using dynamically discovered manifest
- Includes 25 previously "missing" datasets
- Automatic error handling and retries

**What comes next**:
- Download 2024, 2023, 2022
- Comprehensive analysis across 4 years
- Documentation of findings
- Comparison with old approach

**Expected outcome**:
- 4 years of complete UK electricity market data
- 80-100 million records
- 44 datasets per year
- Ready for comprehensive analysis

---

**Current status**: Monitor terminal for progress. Download running in background! 🚀
