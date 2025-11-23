# Price-Demand Correlation Analysis - Explanation

**Issue Resolved:** 31 October 2025  
**Status:** ✅ Working

---

## The Problem

The correlation analysis was showing:
```
⚠️ Insufficient data for correlation analysis
```

---

## Root Causes (2 Issues)

### 1. Data Type Mismatch

The two tables have different data types for `settlementDate`:

| Table | settlementDate Type | Example |
|-------|---------------------|---------|
| `bmrs_bod` | **DATETIME** | `2024-01-01 00:00:00` |
| `demand_outturn` | **STRING** | `"2025-10-25"` |

When joining with `USING (settlementDate, settlementPeriod)`, BigQuery couldn't match:
- `DATETIME '2024-01-01 00:00:00'` ≠ `STRING "2024-01-01"`

Even casting to STRING wasn't enough because the formats differ.

### 2. Date Range Mismatch

The tables have very different data coverage:

| Table | Date Range | Days |
|-------|------------|------|
| `bmrs_bod` | 2024-01-01 to 2025-10-28 | 667 days ✅ |
| `demand_outturn` | 2025-09-27 to 2025-10-25 | **29 days only!** ⚠️ |

The `demand_outturn` table only has **recent data** (last month), not historical data.

---

## The Solution

**Changed approach:**

1. **Cast both to DATE** instead of STRING:
   ```sql
   -- Old (failed)
   CAST(settlementDate AS STRING) as settlementDate
   
   -- New (works)
   CAST(settlementDate AS DATE) as date
   ```

2. **Limit analysis to overlapping period**:
   ```sql
   -- Old
   WHERE settlementDate >= '2024-01-01'  -- No demand data here
   
   -- New
   WHERE settlementDate >= '2025-09-01'  -- Recent period only
   ```

3. **Join on DATE** (strips time component from DATETIME, matches STRING format):
   ```sql
   FROM prices p
   INNER JOIN demand d USING (date, settlementPeriod)
   ```

---

## Results (Now Working!)

✅ **Data Collected:** 1,392 matched periods (Sept-Oct 2025)

### Correlation Coefficients (Pearson)

| Relationship | Correlation | Strength | Interpretation |
|--------------|-------------|----------|----------------|
| Bid Price ↔ Demand | -0.211 | Weak negative | Higher demand → slightly lower bids |
| Offer Price ↔ Demand | -0.205 | Weak negative | Higher demand → slightly lower offers |
| Spread ↔ Demand | -0.128 | Weak negative | Higher demand → slightly lower spreads |

### Linear Regression: Spread = f(Demand)

```
Spread = -0.0005 × Demand + 152.45
```

- **Slope:** -£0.0005/MW (tiny negative impact)
- **R²:** 0.0163 (explains only 1.6% of variance)
- **P-value:** 1.73e-06 (statistically significant but weak)

### Market Impact

| Demand Change | Spread Impact |
|---------------|---------------|
| +1,000 MW | -£0.55/MWh (tiny decrease) |
| +5,000 MW | -£2.75/MWh (small decrease) |

### Spreads by Demand Quartile

| Demand Level | Avg Spread | Std | Min | Max |
|--------------|-----------|-----|-----|-----|
| Q1 (Low) | £145.71 | £26.45 | £111.47 | £217.21 |
| Q2 (Med-Low) | £133.83 | £14.86 | £108.92 | £193.37 |
| Q3 (Med-High) | £134.57 | £12.64 | £107.80 | £172.42 |
| Q4 (High) | £138.32 | £21.35 | £109.19 | £271.65 |

**Interesting:** Lowest demand periods (Q1) have **highest average spreads** (£145.71)!

---

## Key Insights

### 1. Counter-Intuitive Relationship

❌ **Expected:** Higher demand → Higher prices → Higher spreads  
✅ **Actual:** Higher demand → **Lower** spreads

**Why?**
- During high demand periods, the market is more efficient
- More participants, tighter bid-offer spreads
- During low demand (nighttime), fewer participants → wider spreads

### 2. Weak Correlation (R² = 1.6%)

Demand explains only **1.6% of spread variance**, meaning:
- **98.4% of spread behavior** is driven by other factors:
  - Time of day (we saw 3-5am peaks)
  - Day of week (weekends different)
  - Season (winter vs summer)
  - Generation mix
  - Market participant behavior
  - Renewable intermittency

### 3. Low Demand = Higher Opportunity

**Trading Strategy Implication:**
- Target **low demand periods** for higher spreads
- Confirmed by intraday analysis: 3-5am (lowest demand) has highest spreads
- Q1 (low demand) spreads: £145.71 vs Q2-Q3 (medium): £133-134

---

## Why It's Weak (Context)

The correlation is weak **by design** of the electricity market:

1. **Price Formation Complexity:**
   - Prices are set by marginal generation cost
   - Not simply supply/demand balance
   - Influenced by:
     - Generator bidding strategies
     - Renewable availability
     - Interconnector flows
     - System constraints
     - Balancing mechanism

2. **Bid-Offer Spreads Reflect:**
   - Market liquidity (not just demand)
   - Participant competition
   - Uncertainty/risk premiums
   - Time-of-day patterns
   - Generator portfolio positions

3. **Better Predictors of Spreads:**
   - Settlement period (time of day) ✅ Strong
   - Day of week ✅ Strong
   - Season ✅ Strong
   - Generation mix (renewable %)
   - System frequency/stress
   - Interconnector position

---

## Limitations

### 1. Limited Data Range
- Only 29 days (Sept-Oct 2025)
- No seasonal variation captured
- No winter peak demand periods
- More data needed for robust correlation

### 2. Data Quality Issue
- `demand_outturn` table incomplete
- Only recent data available
- Historical demand data missing or in different table

### 3. Possible Alternatives

Check if demand data exists in other tables:
```sql
-- Try these tables for more historical data
bmrs_demand_outturn_iris  -- Real-time version?
bmrs_mid                  -- Market Index Data (has volume)
```

---

## Recommendations

### For Analysis
1. ✅ Use **time-based patterns** (settlement period) - much stronger predictor
2. ✅ Use **seasonal patterns** - 30% variance explained
3. ⚠️ Don't rely heavily on demand correlation - only 1.6% explanatory power
4. 🔍 Investigate other demand data sources for longer history

### For Trading
1. **Low demand = higher spreads** - target off-peak periods
2. Demand changes have **minimal impact** on spreads (-£0.55/MWh per 1000 MW)
3. Focus on **proven patterns**: 3-5am, winter months, weekdays
4. Don't adjust strategy based on demand forecasts alone

### For Future Analysis
1. Get more historical demand data (need full 22 months)
2. Add more variables:
   - Renewable generation %
   - Interconnector flows
   - System frequency
   - Temperature
3. Try multivariate regression:
   - Spread = f(demand, renewable%, temperature, time, season)

---

## Technical Details

### Fixed Query
```sql
WITH prices AS (
  SELECT
    CAST(settlementDate AS DATE) as date,  -- ✅ DATE works
    settlementPeriod,
    AVG(CAST(bid AS FLOAT64)) as bid_price,
    AVG(CAST(offer AS FLOAT64)) as offer_price,
    AVG(CAST(offer AS FLOAT64) - CAST(bid AS FLOAT64)) as spread
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
  WHERE settlementDate >= '2025-09-01'  -- ✅ Recent only
    AND settlementDate <= '2025-10-31'
  GROUP BY date, settlementPeriod
),
demand AS (
  SELECT
    CAST(settlementDate AS DATE) as date,  -- ✅ DATE works
    settlementPeriod,
    AVG(CAST(initialDemandOutturn AS FLOAT64)) as demand_mw
  FROM `inner-cinema-476211-u9.uk_energy_prod.demand_outturn`
  WHERE settlementDate >= '2025-09-01'  -- ✅ Recent only
    AND initialDemandOutturn IS NOT NULL
  GROUP BY date, settlementPeriod
)
SELECT * FROM prices p
INNER JOIN demand d USING (date, settlementPeriod)  -- ✅ Works!
```

### Why DATE Works

- `DATETIME '2024-01-01 00:00:00'` → `DATE '2024-01-01'`
- `STRING "2024-01-01"` → `DATE '2024-01-01'`
- Both become same DATE value → join succeeds ✅

---

## Summary

**Issue:** Correlation analysis failing due to data type and range mismatches  
**Fix:** Cast to DATE and limit to overlapping period  
**Result:** Working analysis with 1,392 matched periods  
**Finding:** Weak negative correlation (-0.128) - low demand = higher spreads  
**Implication:** Time-based patterns are better predictors than demand levels  

**Status:** ✅ **RESOLVED** - Correlation analysis now functional

---

**File Updated:** `enhanced_statistical_analysis.py`  
**Analysis Period:** Sept-Oct 2025 (29 days with demand data)  
**Records Analyzed:** 1,392 settlement periods  
**Date Fixed:** 31 October 2025
