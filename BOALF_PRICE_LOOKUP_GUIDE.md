# BOALF Price Lookup Guide: Reverse Engineering Accepted BM Prices

**Date**: December 4, 2025  
**Status**: ✅ Production Ready  
**Purpose**: How to get accepted Balancing Mechanism prices from BOALF acceptances

---

## 🎯 The Core Problem

**BOALF table has NO price column!**

When you query `bmrs_boalf` in BigQuery, you get:
- ✅ Acceptance volumes (levelFrom, levelTo in MW)
- ✅ Timing (settlementDate, settlementPeriodFrom/To, acceptanceTime)
- ✅ Unit identifier (bmUnit)
- ❌ **NO price data**

But you **can** reverse lookup the accepted price by joining with BOD (Bid-Offer Data).

---

## 📊 BigQuery Price Data Sources

**Critical reference** - Know which tables have what:

| Table | Price Column | Meaning | Join Required? |
|-------|--------------|---------|----------------|
| `bmrs_bod` | `bid`, `offer` | Submitted BM prices (£/MWh) | ❌ No (direct query) |
| `bmrs_boalf` | ❌ **NONE** | Acceptance volumes/times only | ✅ **YES - Join with BOD** |
| `bmrs_mid` | `price` | System imbalance price (£/MWh) | ❌ No (direct query) |
| `bmrs_market_index` | `midPrice` | Market index price (£/MWh) | ❌ No (direct query) |
| `bmrs_cashout` | `cashoutPrice` | System imbalance price (£/MWh) | ❌ No (direct query) |
| `bod_boalf_7d_summary` | `avg_bm_price_gbp_per_mwh` | Pre-joined BOD+BOALF (£/MWh) | ❌ No (pre-computed) |

### Key Insight

- **BOD** = Price ladder submitted by BMU operators (what they're willing to accept)
- **BOALF** = National Grid's acceptance of specific actions (which prices were actually paid)
- **To get settlement price**: Match BOALF acceptance → BOD price that was accepted

---

## 🔧 The Reverse Lookup Method

### Join Logic

```sql
-- Match BOALF acceptances with BOD prices
LEFT JOIN bmrs_bod bod
  ON boalf.bmUnit = bod.bmUnit
  AND boalf.settlementDate = bod.settlementDate
  AND bod.settlementPeriod >= boalf.settlementPeriodFrom
  AND bod.settlementPeriod <= boalf.settlementPeriodTo
```

### Price Selection Logic

```sql
-- Determine which price was accepted based on instruction direction
CASE 
  WHEN boalf.levelTo > boalf.levelFrom THEN bod.offer  -- Generation INCREASE
  WHEN boalf.levelTo < boalf.levelFrom THEN bod.bid    -- Generation DECREASE
  ELSE (bod.offer + bod.bid) / 2                       -- Neutral/unchanged
END AS accepted_price_gbp_per_mwh
```

**Why this works:**
- Increase generation → BMU receives **offer** price (getting paid more to generate)
- Decrease generation → BMU pays **bid** price (getting paid to reduce output)
- National Grid accepts the price from the submitted BOD ladder

---

## 📝 Complete Working Query

### Single-Table Join (Simplified)

```sql
-- Get VLP accepted prices for last 7 days
SELECT
  boalf.bmUnit,
  boalf.settlementDate,
  boalf.settlementPeriodFrom,
  boalf.settlementPeriodTo,
  boalf.acceptanceNumber,
  boalf.acceptanceTime,
  -- Determine accepted price based on instruction direction
  CASE 
    WHEN boalf.levelTo > boalf.levelFrom THEN bod.offer
    WHEN boalf.levelTo < boalf.levelFrom THEN bod.bid
    ELSE (bod.offer + bod.bid) / 2
  END AS accepted_price_gbp_per_mwh,
  -- Additional context
  CASE 
    WHEN boalf.levelTo > boalf.levelFrom THEN 'INCREASE'
    WHEN boalf.levelTo < boalf.levelFrom THEN 'DECREASE'
    ELSE 'NEUTRAL'
  END AS instruction_type,
  ABS(boalf.levelTo - boalf.levelFrom) AS volume_change_mw,
  bod.offer AS submitted_offer_price,
  bod.bid AS submitted_bid_price
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` boalf
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` bod
  ON boalf.bmUnit = bod.bmUnit
  AND boalf.settlementDate = bod.settlementDate
  AND bod.settlementPeriod >= boalf.settlementPeriodFrom
  AND bod.settlementPeriod <= boalf.settlementPeriodTo
WHERE boalf.bmUnit IN ('YOUR_BMU_HERE')  -- Replace with actual BMU IDs
  AND boalf.settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
  AND bod.offer IS NOT NULL  -- Ensure we got a price match
ORDER BY boalf.settlementDate DESC, boalf.settlementPeriodFrom DESC
```

### Aggregated KPIs (Dashboard-Ready)

```sql
-- Get 7-day VLP pricing KPIs
WITH accepted_prices AS (
  SELECT
    CASE 
      WHEN boalf.levelTo > boalf.levelFrom THEN bod.offer
      WHEN boalf.levelTo < boalf.levelFrom THEN bod.bid
      ELSE (bod.offer + bod.bid) / 2
    END AS accepted_price
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` boalf
  LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` bod
    ON boalf.bmUnit = bod.bmUnit
    AND boalf.settlementDate = bod.settlementDate
    AND bod.settlementPeriod >= boalf.settlementPeriodFrom
    AND bod.settlementPeriod <= boalf.settlementPeriodTo
  WHERE boalf.bmUnit IN ('YOUR_BMU_HERE')
    AND boalf.settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
)
SELECT 
  ROUND(AVG(accepted_price), 2) AS avg_vlp_price_gbp_per_mwh,
  ROUND(MIN(accepted_price), 2) AS min_vlp_price,
  ROUND(MAX(accepted_price), 2) AS max_vlp_price,
  ROUND(STDDEV(accepted_price), 2) AS price_volatility,
  COUNT(*) AS num_acceptances
FROM accepted_prices
WHERE accepted_price IS NOT NULL
```

---

## 🔄 Handling Historical + Real-Time Data

**Important**: BigQuery has TWO table sets:
- `bmrs_boalf` / `bmrs_bod` → Historical (up to Oct 28, 2025)
- `bmrs_boalf_iris` / `bmrs_bod_iris` → Real-time IRIS pipeline (current data)

### Full Coverage Query

```sql
WITH boalf_unified AS (
  -- Historical data
  SELECT bmUnit, settlementDate, settlementPeriodFrom, settlementPeriodTo,
         acceptanceNumber, acceptanceTime, levelFrom, levelTo
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND settlementDate <= DATE('2025-10-28')
  
  UNION ALL
  
  -- IRIS real-time data
  SELECT bmUnit, settlementDate, settlementPeriodFrom, settlementPeriodTo,
         acceptanceNumber, acceptanceTime, levelFrom, levelTo
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf_iris`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND settlementDate > DATE('2025-10-28')
),
bod_unified AS (
  -- Historical BOD
  SELECT bmUnit, settlementDate, settlementPeriod, offer, bid
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND settlementDate <= DATE('2025-10-28')
  
  UNION ALL
  
  -- IRIS BOD
  SELECT bmUnit, settlementDate, settlementPeriod, offer, bid
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod_iris`
  WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
    AND settlementDate > DATE('2025-10-28')
)
SELECT
  boalf.bmUnit,
  boalf.settlementDate,
  boalf.acceptanceNumber,
  CASE 
    WHEN boalf.levelTo > boalf.levelFrom THEN bod.offer
    WHEN boalf.levelTo < boalf.levelFrom THEN bod.bid
    ELSE (bod.offer + bod.bid) / 2
  END AS accepted_price_gbp_per_mwh
FROM boalf_unified boalf
LEFT JOIN bod_unified bod
  ON boalf.bmUnit = bod.bmUnit
  AND boalf.settlementDate = bod.settlementDate
  AND bod.settlementPeriod >= boalf.settlementPeriodFrom
  AND bod.settlementPeriod <= boalf.settlementPeriodTo
WHERE boalf.bmUnit IN ('YOUR_BMU_HERE')
  AND bod.offer IS NOT NULL
ORDER BY boalf.settlementDate DESC
```

---

## 🛠️ Python Implementation

### Ready-to-Use Script

**File**: `python/create_vlp_dual_kpis.py`

```bash
# Run the script
cd ~/GB-Power-Market-JJ
python3 python/create_vlp_dual_kpis.py
```

**Features**:
- ✅ Automatic BOD+BOALF join with correct period matching
- ✅ UNION of historical + IRIS tables (complete coverage)
- ✅ System imbalance price comparison
- ✅ VLP premium calculation
- ✅ CSV exports for Dashboard V3 import
- ✅ Data validation and sanity checks

**Configuration** (edit in script):
```python
VLP_UNITS = ['FBPGM002', 'FFSEN005']  # Replace with your BMU IDs
DAYS_BACK = 7  # Analysis period
```

**Output Files**:
- `vlp_boalf_prices_7d_TIMESTAMP.csv` - Detailed BOALF accepted prices
- `system_imbalance_prices_7d_TIMESTAMP.csv` - System reference prices
- `vlp_kpi_summary_7d_TIMESTAMP.csv` - Single-row KPI summary

---

## 📈 Expected Values & Validation

### VLP Accepted Prices (via BOD join)

| Metric | Expected Range | Notes |
|--------|---------------|-------|
| Average | £35-80/MWh | Typical VLP settlement price |
| Minimum | £10-30/MWh | Low-demand periods |
| Maximum | £80-150/MWh | System stress/high-demand |
| Volatility (CV) | 10-50% | Coefficient of variation |

### System Imbalance Prices

| Metric | Expected Range | Notes |
|--------|---------------|-------|
| Average | £20-150/MWh | Market-wide reference (more volatile) |
| Minimum | £5-20/MWh | Oversupply conditions |
| Maximum | £100-300/MWh | System emergencies |
| Volatility (CV) | 30-80% | Higher than VLP prices |

### VLP Premium

| Metric | Expected Range | Interpretation |
|--------|---------------|----------------|
| Premium | £5-25/MWh | Value-add over market baseline |
| Premium % | 10-40% | Percentage over system price |

---

## 🚨 Common Issues & Solutions

### Issue 1: No Price Match (NULL accepted_price)

**Symptom**: Query returns rows but `accepted_price_gbp_per_mwh` is NULL

**Cause**: BOALF acceptance has no matching BOD entry

**Solutions**:
1. Check date ranges match between BOALF and BOD
2. Verify `settlementPeriod` range matching logic
3. Confirm BMU names are identical in both tables
4. Add `WHERE accepted_price IS NOT NULL` filter

### Issue 2: No BOALF Data for VLP Units

**Symptom**: Query returns 0 rows

**Possible Reasons**:
1. VLP BMUs not active in selected date range
2. No balancing acceptances (market conditions didn't require VLP)
3. BMU names incorrect (check spelling/capitalization)
4. Data lag (historical tables update with delay)

**Solutions**:
1. Query wider date range: `INTERVAL 30 DAY` instead of 7
2. Find active BMUs first:
```sql
SELECT bmUnit, COUNT(*) as acceptance_count
FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf`
WHERE settlementDate >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
GROUP BY bmUnit
ORDER BY acceptance_count DESC
LIMIT 20
```

### Issue 3: Unrealistic Prices (£500+/MWh)

**Symptom**: Average prices much higher than expected

**Cause**: Incorrect price selection logic or data quality issue

**Solutions**:
1. Verify direction logic (INCREASE→offer, DECREASE→bid)
2. Add sanity check filter: `WHERE accepted_price BETWEEN 0 AND 300`
3. Check for outliers: `WHERE accepted_price <= PERCENTILE_CONT(0.99)`

### Issue 4: Historical vs IRIS Data Gap

**Symptom**: Missing data around Oct 28, 2025

**Cause**: Historical tables end Oct 28, IRIS starts after

**Solution**: Use UNION query (see "Full Coverage Query" above)

---

## 📊 Dashboard V3 Integration

### Import to Google Sheets

**Option 1: Detailed Data (for sparklines)**
1. Import `vlp_boalf_prices_7d_TIMESTAMP.csv` → Sheet: **VLPPRICE**
2. Import `system_imbalance_prices_7d_TIMESTAMP.csv` → Sheet: **SYSPRICE**

**Google Sheets Formulas**:
```
// Cell F10: VLP Average Price (7d)
=AVERAGE(VLPPRICE!K:K)

// Cell I10: System Imbalance Price (7d)
=AVERAGE(SYSPRICE!D:D)

// Cell J10: VLP Premium
=F10-I10

// Row 16: VLP Price Sparkline (7-day trend)
=SPARKLINE(VLPPRICE!K:K, {"charttype","line";"linewidth",2;"color","#4285F4"})
```

**Option 2: KPI Summary (single-row import)**
1. Import `vlp_kpi_summary_7d_TIMESTAMP.csv` → Sheet: **VLP_KPI**

**Google Sheets Formulas**:
```
// Cell F10: VLP Average Price
=VLP_KPI!D2

// Cell I10: System Average Price
=VLP_KPI!K2

// Cell J10: VLP Premium
=VLP_KPI!S2
```

---

## 🔗 Related Documentation

- **`KNOWN_ISSUES_VLP_REVENUE_CALCULATION.md`** - Full background on VLP revenue bug
- **`STOP_DATA_ARCHITECTURE_REFERENCE.md`** - Complete schema reference
- **`BOD_BOALF_ANALYSIS_GUIDE.md`** - BOD vs BOALF explained
- **`PROJECT_CONFIGURATION.md`** - BigQuery project settings

---

## 🧪 Quick Test Query

**Verify BOD+BOALF join works**:

```sql
-- Test with ANY active BMU (not just VLP)
WITH test_join AS (
  SELECT
    boalf.bmUnit,
    CASE 
      WHEN boalf.levelTo > boalf.levelFrom THEN bod.offer
      WHEN boalf.levelTo < boalf.levelFrom THEN bod.bid
      ELSE (bod.offer + bod.bid) / 2
    END AS accepted_price
  FROM `inner-cinema-476211-u9.uk_energy_prod.bmrs_boalf` boalf
  LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.bmrs_bod` bod
    ON boalf.bmUnit = bod.bmUnit
    AND boalf.settlementDate = bod.settlementDate
    AND bod.settlementPeriod >= boalf.settlementPeriodFrom
    AND bod.settlementPeriod <= boalf.settlementPeriodTo
  WHERE boalf.settlementDate = DATE('2025-10-23')  -- Known active date
  LIMIT 100
)
SELECT
  COUNT(*) AS total_rows,
  COUNT(accepted_price) AS rows_with_price,
  ROUND(AVG(accepted_price), 2) AS avg_price,
  ROUND(MIN(accepted_price), 2) AS min_price,
  ROUND(MAX(accepted_price), 2) AS max_price
FROM test_join
```

**Expected Result**:
- `total_rows` > 0 (found acceptances)
- `rows_with_price` ≈ `total_rows` (successful join, ~90%+ match rate)
- `avg_price` between £20-100/MWh (realistic)

---

## ✅ Key Takeaways

1. **BOALF has NO price column** - Always need BOD join
2. **Direction determines price** - INCREASE=offer, DECREASE=bid
3. **Period range matching** - BOD settlementPeriod must be within BOALF From/To range
4. **Two table sets** - Historical + IRIS for complete coverage
5. **Validation essential** - Check for NULL prices and unrealistic values
6. **Pre-computed alternative** - `bod_boalf_7d_summary` if available

---

**Status**: ✅ Production Ready  
**Last Updated**: December 4, 2025  
**Maintainer**: George Major (george@upowerenergy.uk)  
**Script**: `python/create_vlp_dual_kpis.py`
