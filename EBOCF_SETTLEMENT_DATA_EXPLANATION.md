# EBOCF Settlement Data - Publication Timing & Dashboard Usage

**Date**: December 29, 2025  
**Dataset**: `bmrs_ebocf` (Energy Balancing Offer Cashflow)  
**Type**: Settlement output (not operational data)

---

## 🕒 Publication Schedule

### The Rule
**EBOCF is a settlement dataset, so today's values are not published until the Initial Settlement run on the following day.**

### Detailed Timeline

| Event | Timing |
|-------|--------|
| **Settlement day ends** | 23:00–23:30 (SP48 complete) |
| **Settlement systems run** | Overnight |
| **EBOCF (II) published** | Early morning D+1 (≈ 05:00–08:00 GMT) |

**Example for Settlement Date = Dec 29**:
- Dec 29 23:30: Last settlement period (SP48) completes
- Dec 29 midnight → Dec 30 ~05:00: SAA run processes settlement
- Dec 30 ~05:00–08:00: EBOCF data for Dec 29 published

---

## 📊 What is EBOCF?

**Full Name**: Energy Balancing Offer Cashflow

**Definition**: BMRS-calculated "period BM Unit cashflow" measures derived from accepted volumes and pay-as-bid prices using Section T-style rules with indicative substitutions in the BMRS context.

**Technical Details**:
- BMRA calculates indicative accepted volumes and indicative bid/offer cashflows (ICBn / ICOn)
- Follows Section T3 logic with substitutions:
  - ETLMO± (Expected Transmission Loss Multiplier)
  - Indicative BSAD terms (Balancing Services Adjustment Data)
- Published as part of **Initial Settlement (II)** run
- Later refined in Reconciliation runs (R1, R2, R3, RF)

**Data Type**: Settlement cashflow (not operational dispatch revenue)

---

## ⚠️ Critical Dashboard Implications

### ❌ WRONG: Using EBOCF as "Today" Data

If your dashboard shows:
```
💰 BM Cashflow (Today): £155k
Source: bmrs_ebocf WHERE settlementDate = CURRENT_DATE()
```

**Problem**: This shows incomplete/preliminary data (only 5 settlement periods from early morning 03:06 UTC), not today's actual activity.

### ✅ CORRECT: Using EBOCF as "Last 24h" or "Yesterday"

```sql
-- Query last complete settlement day (D-1)
SELECT SUM(ABS(totalCashflow)) as gross_cashflow
FROM bmrs_ebocf
WHERE CAST(settlementDate AS DATE) = DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
```

**Dashboard label options**:
- "💰 BM Settlement Cashflow (Last 24h) - EBOCF"
- "💰 BM Settlement Cashflow (Yesterday, II)"
- "💰 BM Settlement Activity (D-1, Initial Settlement)"

---

## 🔄 Data Source Comparison

| Dataset | Nature | Availability | Use Case | Dashboard Label |
|---------|--------|--------------|----------|-----------------|
| **EBOCF** | Settlement cashflow | D+1 (Initial Settlement) | Post-day settlement analysis | "Settlement Cashflow (D-1)" |
| **BOALF** | Operational dispatch | Near real-time / intraday | Live dispatch monitoring | "Dispatch Revenue (Operational)" |
| **BOD** | Bid–offer prices | Near real-time | Live pricing | "Bid-Offer Prices (Live)" |
| **P114** | Full settlement | D+1 (II), R1/R2/R3/RF | Legal settlement truth | "Settlement (Reconciliation Run)" |
| **RF run** | Final settlement | ~28 months later | Audited final values | "Final Settlement (RF)" |

---

## 💡 Dashboard Implementation

### What We Changed

**Before** (incorrect):
```python
# Query: CURRENT_DATE()
# Label: "BM Gross Cashflow (Today)"
# Result: £155k (incomplete, only 5 periods)
```

**After** (correct):
```python
# Query: DATE_SUB(CURRENT_DATE(), INTERVAL 1 DAY)
# Label: "BM Settlement Cashflow (Last 24h) - EBOCF"
# Result: £29.6M (complete settlement day)
```

### Code Location
**File**: `update_live_metrics.py`
**Function**: `get_bm_market_kpis()`
**Lines**: ~895-910 (EBOCF query WHERE clause)
**Lines**: ~1622 (Dashboard label)

---

## 🎯 Key Takeaways

1. **EBOCF cannot be used for "live" or "today-so-far" metrics**
   - It's settlement data published after the day completes

2. **For live/intraday activity, use BOALF (acceptances)**
   - Label as "Operational/Indicative" not "Settlement"

3. **EBOCF shows yesterday's complete settlement data**
   - This is the most recent complete, validated dataset

4. **Typical daily EBOCF: £30-90 million**
   - Not £155k (which was incomplete early-morning partial data)

5. **Proper labeling is critical**
   - Regulators, auditors, and traders need accurate data context

---

## 📚 References

- **BSC Section T**: Settlement calculations methodology
- **ELEXON BMRS Catalogue**: EBOCF dataset definition
- **Settlement Timetable**: II, R1, R2, R3, RF run schedules
- **BMRS Data Guide**: Indicative vs actual settlement values

---

## ✅ Verification

**Expected Values**:
- Dec 28 EBOCF: £29,552,143 ✓
- Dec 29 EBOCF: Not published until Dec 30 morning ✓
- Dashboard now shows: "Last 24h" = Dec 28 data ✓

**Cron Status**:
- EBOCF ingestion: Every 2 hours at :25 past even hours
- Last run: 22:25 UTC (Dec 29)
- Ingested: Dec 28 complete settlement data
- Next run: 00:25 UTC (Dec 30) will attempt Dec 29 data

---

*Last Updated: December 29, 2025*  
*Author: System Architecture Documentation*  
*Status: Production Implementation Complete*
