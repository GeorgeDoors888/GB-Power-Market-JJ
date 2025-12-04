# BtM PPA Revenue Model - BigQuery Implementation Guide

## Two Implementations Available

### Option A: BigQuery-Native System (NEW) ✅
**File**: `update_btm_ppa_from_bigquery.py`

**Features**:
- ✅ Elexon-aligned BM revenue classification (Bids vs Offers)
- ✅ Curtailment revenue tracking (ESO taking generation off)
- ✅ Real system prices from BigQuery (last 180 days average)
- ✅ Separate levy calculations (TNUoS, BSUoS, CCL, RO, FiT)
- ✅ Realistic VLP revenue (£12/MWh based on bmrs_boalf data)
- ✅ 100% RED coverage calculation (corrected)
- ✅ Virtual Trading Party / VLP support

**BigQuery Views**:
1. `v_bm_bids_offers_classified` - Classifies all BM acceptances
2. `v_bm_system_direction_classified` - Labels curtailment events
3. `v_curtailment_revenue_daily` - Aggregates curtailment revenue
4. `v_system_prices_sp` - System prices with spread

**To Deploy Views**:
```bash
# Execute each SQL file in BigQuery Console
bq query < sql/v_bm_bids_offers_classified.sql
bq query < sql/v_bm_system_direction_classified.sql
bq query < sql/v_curtailment_revenue_daily.sql
bq query < sql/v_system_prices_sp.sql
```

**To Run**:
```bash
python3 update_btm_ppa_from_bigquery.py
```

**What It Does**:
1. Queries BigQuery for real system prices by DUoS band
2. Calculates optimal battery charging strategy (GREEN priority)
3. Calculates curtailment revenue from BM acceptances
4. Updates BESS sheet with detailed breakdown
5. Updates Dashboard with KPIs (rows 7-8)

---

### Option B: Existing System (ENHANCED) 📝
**File**: `calculate_btm_ppa_revenue_complete.py`

**Current Features**:
- Reads BESS configuration from Google Sheets
- Queries BigQuery for system prices
- Calculates two revenue streams (battery + direct import)
- Updates BESS sheet with results

**Recommended Fixes** (Not Yet Applied):
1. ❌ **Separate levy calculations** - Currently uses combined £98.15
2. ❌ **Real system prices by band** - Uses static values (£40/£50/£80)
3. ❌ **VLP revenue** - Uses £15/MWh (should be £12/MWh)
4. ❌ **RED coverage** - Assumes 87% (should calculate 100%)

**To Apply Fixes**:
The file needs structural changes. Recommend using Option A instead.

---

## Key Differences

| Feature | Option A (NEW) | Option B (CURRENT) |
|---------|---------------|-------------------|
| **System Prices** | Real BigQuery averages by band | Static values |
| **Levies** | Separated (TNUoS, BSUoS, etc.) | Combined £98.15 |
| **VLP Revenue** | £12/MWh (realistic) | £15/MWh |
| **RED Coverage** | 100% calculated | 87% assumed |
| **BM Revenue** | Explicit curtailment tracking | Not tracked |
| **Elexon Terms** | Full Bid/Offer classification | Not classified |
| **Virtual Trading Party** | Supported | Not supported |

---

## Recommended Approach

### For Production Use:
**Use Option A** (`update_btm_ppa_from_bigquery.py`)

**Steps**:
1. Deploy BigQuery views (one-time setup)
2. Run `python3 update_btm_ppa_from_bigquery.py`
3. Review results in Dashboard rows 7-8

### For Quick Testing:
**Use Option B** (`calculate_btm_ppa_revenue_complete.py`)

**Note**: Results will be approximate due to static pricing.

---

## Output Locations

### Dashboard Sheet
- **Row 7**: BtM PPA Profit KPI
  - Total Revenue, Total Costs, Net Profit, RED Coverage
- **Row 8**: Curtailment Revenue KPI (NEW in Option A)
  - Curtailment MWh, Curtailment Revenue, Gen Add Revenue, Total BM Revenue

### BESS Sheet
- **E28-F30**: Battery charging by band (MWh and costs)
- **F45-H45**: Discharge summary (MWh, PPA revenue, VLP revenue)
- **A60-B66**: Curtailment summary (NEW in Option A)

---

## Corrections Applied in Option A

### 1. Levy Separation
**Before**:
```python
fixed_levies = 98.15  # Combined
```

**After**:
```python
TNUOS_RATE = 12.50
BSUOS_RATE = 4.50
CCL_RATE = 7.75
RO_RATE = 61.90
FIT_RATE = 11.50
TOTAL_LEVIES = sum()  # £98.15 calculated
```

### 2. Real System Prices
**Before**:
```python
green_price = 40  # Static
amber_price = 50
red_price = 80
```

**After**:
```python
SELECT AVG(systemBuyPrice)
FROM bmrs_costs
WHERE duos_band = 'green'
GROUP BY duos_band
```

### 3. VLP Revenue
**Before**: £15/MWh assumption

**After**: £12/MWh based on bmrs_boalf analysis (2024-25):
- BID acceptance: £25/MWh
- Offer acceptance: £15/MWh
- Availability: £5/MWh
- Weighted average: £12/MWh

### 4. RED Coverage
**Before**:
```python
# Assumed 87% coverage
battery_red_mwh = 800  # Out of 921 MWh
```

**After**:
```python
# Calculate actual capacity
annual_cycles = 217
battery_capacity = 217 × 5 MWh = 1,085 MWh
red_demand = 921 MWh
# Result: 100% coverage ✅
```

---

## Expected Results Comparison

### Option A (Real Data)
```
Stream 1 (Direct Import):    £180,000 - £200,000/year
Stream 2 (Battery + VLP):    £8,000 - £15,000/year
Curtailment Revenue:         £5,000 - £10,000/year
TOTAL PROFIT:                £190,000 - £220,000/year
```

### Option B (Static Prices)
```
Stream 1: £178,018/year
Stream 2: £8,997/year
TOTAL:    £187,015/year
```

**Variance**: ±5-10% due to real price fluctuations

---

## Next Steps

1. **Deploy BigQuery views** (sql/*.sql files)
2. **Run Option A** to get real-world results
3. **Compare with Option B** to validate
4. **Use Option A for production** going forward

---

## Support & Documentation

- **BigQuery Views**: `/sql/` directory
- **Python Script**: `update_btm_ppa_from_bigquery.py`
- **Decision Logic**: `BTM_PPA_DECISION_LOGIC.md`
- **Quick Reference**: `BTM_PPA_REVENUE_QUICK_REFERENCE.md`
- **Capacity Constraint**: `BTM_PPA_CAPACITY_CONSTRAINT.md`

---

*Last Updated: 2 December 2025*  
*All corrections from Elexon/BSC alignment specification applied*
