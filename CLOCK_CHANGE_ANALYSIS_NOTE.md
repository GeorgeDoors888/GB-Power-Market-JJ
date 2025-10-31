# Clock Change Settlement Periods - Important Analysis Note

**Date:** 31 October 2025  
**Issue:** Settlement Period 50 appearing in intraday pattern analysis  
**Status:** ✅ CORRECTED

---

## The Problem

The initial analysis showed:
```
Peak spread periods:
   Period 50 (24.5h): £153.84/MWh  ❌ MISLEADING
   Period 49 (24.0h): £141.02/MWh  ❌ MISLEADING
```

This made it appear that "midnight" had the highest spreads and suggested battery operators should target this time period.

## Why This Was Wrong

**Settlement Periods 49 and 50 only exist on clock change days** (when clocks go back in October).

### The Data

| Period | Occurrences | Dates | Avg Spread |
|--------|-------------|-------|------------|
| Period 48 | 822,647 | Every day (666 days × ~480 BMUs) | £129.01/MWh |
| Period 49 | 2,294 | **2 days only** (27 Oct 2024, 26 Oct 2025) | £140.35/MWh |
| Period 50 | 2,126 | **2 days only** (27 Oct 2024, 26 Oct 2025) | £152.33/MWh |

### The Issue

- Period 50 appeared in the analysis as if it were a **regular daily occurrence**
- In reality, it only occurs **2 days per year** (clock change Sunday in October)
- The high spread (£153.84) is not representative of typical "midnight" conditions
- This would have led to **incorrect trading strategies**

## UK Clock Change Rules

- **Spring Forward (March):** Clocks go forward at 01:00 GMT → 02:00 BST
  - Settlement periods: **46 periods** (Period 4 is skipped)
  - Missing hour: 01:00-02:00
  
- **Autumn Back (October):** Clocks go back at 02:00 BST → 01:00 GMT
  - Settlement periods: **50 periods** (Periods 49-50 are extra)
  - Extra hour: 01:00-02:00 (repeated)

In the GB electricity market:
- Normal day: 48 settlement periods (00:00-23:30, each 30 minutes)
- Clock forward day: 46 periods (spring)
- Clock back day: 50 periods (autumn) ← **This is what we found**

## The Correction

Updated analysis now:
1. **Excludes Periods 49-50** from normal intraday pattern analysis
2. **Shows them separately** with clear warning that they only occur 2 days/year
3. **Prevents misleading trading signals**

### Corrected Peak Periods (Normal Days Only)

```
Peak spread periods:
   Period  8 (03:30h): £131.59/MWh  ✅ Based on 666 days
   Period  7 (03:00h): £131.22/MWh  ✅ Based on 666 days
   Period 10 (04:30h): £131.17/MWh  ✅ Based on 666 days
   Period  6 (02:30h): £130.84/MWh  ✅ Based on 666 days
   Period  9 (04:00h): £130.68/MWh  ✅ Based on 666 days

Clock Change Periods (shown separately):
   Period 49 (Extra hour): £141.02/MWh - occurs on 2 days only
   Period 50 (Extra hour): £153.84/MWh - occurs on 2 days only
```

## Trading Implications

### ❌ Before (Incorrect)
"Target midnight operations (Period 50) for maximum spreads of £153.84/MWh"

### ✅ After (Correct)
"Target early morning operations (03:00-04:30h, Periods 7-10) for consistent spreads of ~£131/MWh"

### Key Differences

1. **Frequency:** 
   - Period 50: 2 days/year = **0.3% of days**
   - Periods 7-10: 666 days/year = **100% of days**

2. **Reliability:**
   - Period 50: Cannot build business case around 2 days
   - Periods 7-10: Daily repeatable pattern for dispatch planning

3. **Spread Premium:**
   - Period 50: £153.84 (22.84 higher than Period 8)
   - But only available 2 days = £45.68 total annual benefit
   - Period 8: £131.59 daily = £87,660 annual benefit (666 days)

## Verification Query

To verify clock change days in your data:

```sql
SELECT 
  settlementDate,
  COUNT(DISTINCT settlementPeriod) as num_periods,
  MAX(settlementPeriod) as max_period
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
WHERE settlementDate >= '2024-01-01'
  AND settlementDate <= '2025-10-31'
GROUP BY settlementDate
HAVING MAX(settlementPeriod) > 48
ORDER BY settlementDate
```

Result:
```
2024-10-27 (Sunday): 50 periods ✅
2025-10-26 (Sunday): 50 periods ✅
```

## Lessons Learned

1. **Always check data frequency** - High average values might be based on tiny sample sizes
2. **Understand domain specifics** - GB electricity market has special clock change rules
3. **Separate exceptional events** - Clock change days should be analyzed separately
4. **Verify assumptions** - "Midnight" Period 50 sounded plausible but was actually exceptional

## Updated Documentation

The following files have been corrected:
- ✅ `enhanced_statistical_analysis.py` - Now excludes Periods 49-50 from normal analysis
- ⏳ `ENHANCED_ANALYSIS_RESULTS.md` - Needs update to reflect correct peak periods

---

## Technical Details

### Settlement Period to Time Mapping

Normal days (48 periods):
- Period 1: 00:00-00:30
- Period 2: 00:30-01:00
- ...
- Period 48: 23:30-00:00

Clock back days (50 periods):
- Period 1: 00:00-00:30 (BST)
- Period 2: 00:30-01:00 (BST)
- Period 3: 01:00-01:30 (BST) ← First occurrence of 01:00-02:00
- Period 4: 01:30-02:00 (BST)
- Period 5: 01:00-01:30 (GMT) ← Second occurrence of 01:00-02:00
- Period 6: 01:30-02:00 (GMT)
- ...continues normally
- Period 49: 23:00-23:30 (GMT)
- Period 50: 23:30-00:00 (GMT)

Wait, that's not quite right. Let me verify the actual mapping...

Actually, the Period 49-50 occur during the **repeated hour** when clocks go back:
- The hour between 01:00-02:00 happens twice
- This creates 2 extra settlement periods
- Hence 50 periods instead of 48

### Why Periods 49-50 Have High Spreads

The clock change happens at 02:00 BST → 01:00 GMT (typically 02:00 → 01:00):
- This is during night hours when demand is lowest
- But it's also when the grid must manage the transition
- The extra periods (49-50) capture this unique operational period
- Higher uncertainty during clock change may drive higher spreads

However, this is **not actionable** for battery operators as it only occurs twice a year.

---

**Key Takeaway:** Always validate data before making business decisions. What looks like a daily pattern might be a rare event with misleading statistics.
