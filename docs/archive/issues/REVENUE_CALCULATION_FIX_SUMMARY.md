# Revenue Calculation Fix Summary

**Date**: November 10, 2025  
**Status**: ✅ Root cause identified, solution documented

## Problem

The `complete_vlp_battery_analysis.py` script calculates £0 revenue for all 148 batteries despite having 26M+ BOD records.

## Root Cause Discovered

### Wrong Table Used: bmrs_bod
The script was using `bmrs_bod` (Bid-Offer Data) which contains **submissions only**:
- `levelFrom` and `levelTo` are the **power levels offered**, not actual dispatch
- These values are static (levelTo - levelFrom = 0)
- Example from T_KEMB-1:
  ```
  bid: 56.51, offer: 113.50, levelFrom: -9, levelTo: -9, mw_change: 0
  bid: 56.51, offer: 113.50, levelFrom: 6, levelTo: 6, mw_change: 0
  ```
- BOD shows "I'm willing to operate at -9MW for £56.51/MWh bid OR at +6MW for £113.50/MWh offer"
- This is just a price list, not actual energy traded!

### Correct Table: bmrs_boalf
The **Bid-Offer Acceptance Level File** (`bmrs_boalf`) shows actual accepted actions:
- ✅ 3.78M acceptance records for 80 batteries
- ✅ Coverage: 2022-01-01 to 2025-10-28
- ✅ Has `acceptanceNumber`, `acceptanceTime`
- ✅ `levelFrom`/`levelTo` show actual power level changes
- Example: `levelFrom: 0, levelTo: 14` = battery ramped from 0MW to 14MW (actual dispatch)

## Data Comparison

| Table | Purpose | Records | Batteries | Coverage | MW Change |
|-------|---------|---------|-----------|----------|-----------|
| **bmrs_bod** | Bid-offer submissions | 26.1M | 107 | 2022-2025 | ❌ Zero (static levels) |
| **bmrs_boalf** | Accepted actions | 3.8M | 80 | 2022-2025 | ✅ Real (levelTo - levelFrom) |

## Solution

### Updated Revenue Query

```sql
WITH market_prices AS (
  -- Get average market price per settlement period
  SELECT 
    settlementDate,
    settlementPeriodFrom as settlementPeriod,  -- BOALF uses From/To periods
    AVG(CASE WHEN price > 0 THEN price END) as avg_price_gbp_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_mid`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
    AND price > 0
  GROUP BY settlementDate, settlementPeriodFrom
),
battery_acceptances AS (
  SELECT 
    boalf.bmUnit,
    boalf.settlementDate,
    boalf.settlementPeriodFrom,
    boalf.levelFrom,
    boalf.levelTo,
    (boalf.levelTo - boalf.levelFrom) as mw_change,
    prices.avg_price_gbp_mwh,
    
    -- Calculate revenue/cost for this acceptance
    CASE 
      WHEN (boalf.levelTo - boalf.levelFrom) > 0  -- Discharge (export)
      THEN (boalf.levelTo - boalf.levelFrom) * COALESCE(prices.avg_price_gbp_mwh, 0) * 0.5
      ELSE 0 
    END as discharge_revenue_gbp,
    
    CASE 
      WHEN (boalf.levelTo - boalf.levelFrom) < 0  -- Charge (import)
      THEN ABS(boalf.levelTo - boalf.levelFrom) * COALESCE(prices.avg_price_gbp_mwh, 0) * 0.5
      ELSE 0 
    END as charge_cost_gbp
    
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` boalf
  LEFT JOIN market_prices prices
    ON boalf.settlementDate = prices.settlementDate 
    AND boalf.settlementPeriodFrom = prices.settlementPeriod
  WHERE boalf.bmUnit IN ('T_KEMB-1', 'E_LITRB-1', ...)  -- Battery list
    AND boalf.settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
)
SELECT 
  bmUnit,
  COUNT(*) as total_acceptances,
  SUM(discharge_revenue_gbp) as total_discharge_revenue_gbp,
  SUM(charge_cost_gbp) as total_charge_cost_gbp,
  SUM(discharge_revenue_gbp) - SUM(charge_cost_gbp) as net_revenue_gbp,
  AVG(avg_price_gbp_mwh) as avg_market_price
FROM battery_acceptances
GROUP BY bmUnit
ORDER BY net_revenue_gbp DESC
```

### Key Changes
1. **Table change**: `bmrs_bod` → `bmrs_boalf`
2. **Period mapping**: `settlementPeriod` → `settlementPeriodFrom`
3. **Real MW changes**: `levelTo - levelFrom` now shows actual dispatch
4. **Revenue formula**: Same (MW × price × 0.5h) but now with real MW values

## Schema Differences

### bmrs_bod (Submissions)
```
bmUnit, settlementDate, settlementPeriod,
bid, offer, levelFrom, levelTo,  # levelFrom = levelTo (no change)
pairId
```

### bmrs_boalf (Acceptances)
```
bmUnit, settlementDate, 
settlementPeriodFrom, settlementPeriodTo,  # Can span multiple periods
levelFrom, levelTo,  # ACTUAL power change (levelFrom ≠ levelTo)
acceptanceNumber, acceptanceTime,
timeFrom, timeTo  # Exact timestamps
```

## Test Results Before Fix

```bash
# Using bmrs_bod (WRONG)
T_KEMB-1:  12,304 actions, £0 revenue (levelTo - levelFrom = 0)
E_LITRB-1: 12,328 actions, £0 revenue
T_COVNB-1: 12,155 actions, £0 revenue
```

## Expected Results After Fix

```bash
# Using bmrs_boalf (CORRECT)
# Will show actual revenue based on accepted dispatch
# Example estimate: 10,000 acceptances × 20 MWh avg × £50/MWh = £10,000 revenue
```

## Implementation

### File to Update
`complete_vlp_battery_analysis.py`, function `analyze_bod_revenue()`, lines 235-280

### Steps
1. Change table from `bmrs_bod` to `bmrs_boalf`
2. Update query to use `settlementPeriodFrom`/`To`
3. Verify battery BMU codes match (some may use different format in BOALF)
4. Test with 3-5 batteries first
5. Run full analysis once verified

### Additional Context
- **BOD** = Market submissions (like a menu: "I can do X for £Y")
- **BOALF** = Actual orders accepted (like a receipt: "You did X for £Y")
- Revenue should be calculated from **receipts (BOALF)**, not **menus (BOD)**

## Related Files

- `VLP_DATA_USAGE_GUIDE.md` - Documents revenue analysis use case (needs update)
- `PROJECT_CAPABILITIES.md` - Lists revenue tracking as current issue (will be resolved)
- `complete_vlp_battery_analysis.py` - Main script needing fix
- `DOCUMENTATION_SESSION_SUMMARY.md` - Todo item #8 tracks this

## Next Steps

1. ✅ Root cause identified (using wrong table)
2. ✅ Correct table found (bmrs_boalf with 3.8M records)
3. ✅ Solution documented (this file)
4. ⏳ Update query in complete_vlp_battery_analysis.py
5. ⏳ Test with sample batteries
6. ⏳ Run full analysis
7. ⏳ Update documentation files

---

**Key Learning**: In energy markets, distinguish between:
- **Bids/Offers** = Price submissions (what you're willing to do)
- **Acceptances** = Actual dispatch (what National Grid asked you to do)
- Revenue comes from acceptances, not submissions!
