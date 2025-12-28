# £0 Average Prices Issue - Root Cause & Solution

## 🔍 Problem Identified

**You're seeing £0 for `bm_revenue_per_mwh` in Google Sheets** because the Google Sheets dashboard queries a **different data source** than the `calculate_vlp_revenue.py` script.

### Data Source Mismatch

| Component | Data Source | BM Revenue Status |
|-----------|-------------|-------------------|
| **calculate_vlp_revenue.py** (Terminal) | `mart_bm_value_by_vlp_sp` table | ✅ **£66.06/MWh avg** (correct!) |
| **Google Sheets Dashboard** | `v_btm_bess_inputs` view | ❌ **£0.00/MWh** (missing data!) |

### Evidence from Terminal Output

```python
# Your script output shows CORRECT prices:
✅ VLP REVENUE CALCULATION (Oct 17-23, 2025):
2025-10-18 Flexitricity    £8,797.63    £91.67/MWh  ← CORRECT ✅
2025-10-19 Flexitricity   £20,548.13    £37.90/MWh  ← CORRECT ✅
2025-10-20 Flexitricity   £59,667.69    £60.50/MWh  ← CORRECT ✅

Total revenue: £157,328.08
Average price: £66.06/MWh  ← CORRECT ✅
```

But the `v_btm_bess_inputs` view queried by Google Sheets shows:
```sql
settlementDate  settlementPeriod  bm_revenue_per_mwh
2025-12-27      39                0.0                 ← WRONG ❌
2025-12-27      38                0.0                 ← WRONG ❌
2025-12-27      37                0.0                 ← WRONG ❌
```

---

## 🛠️ Solution: Update the View

The `v_btm_bess_inputs` view needs to be updated to **LEFT JOIN** with the new `mart_bm_value_by_vlp_sp` table.

### Current View Structure
```sql
CREATE OR REPLACE VIEW v_btm_bess_inputs AS
WITH base_prices AS (
  -- Union of bmrs_costs + bmrs_mid_iris
  ...
),
stacked_revenue AS (
  SELECT
    ...
    0.0 AS bm_revenue_per_mwh,  ← HARDCODED TO ZERO!
    ...
  FROM base_prices
)
SELECT * FROM stacked_revenue
```

### Updated View (WITH BM Revenue)
```sql
CREATE OR REPLACE VIEW v_btm_bess_inputs AS
WITH base_prices AS (
  -- Union of bmrs_costs + bmrs_mid_iris
  ...
),
bm_revenue_lookup AS (
  -- Aggregate BM revenue by date + settlement period
  SELECT
    settlement_date,
    settlementPeriod,
    SUM(total_gross_value_gbp) / NULLIF(SUM(total_accepted_mwh), 0) AS bm_revenue_per_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.mart_bm_value_by_vlp_sp`
  GROUP BY settlement_date, settlementPeriod
),
stacked_revenue AS (
  SELECT
    bp.*,
    COALESCE(bm.bm_revenue_per_mwh, 0.0) AS bm_revenue_per_mwh,  ← NOW PULLS FROM REAL DATA!
    ...
  FROM base_prices bp
  LEFT JOIN bm_revenue_lookup bm
    ON CAST(bp.settlementDate AS DATE) = bm.settlement_date
    AND bp.settlementPeriod = bm.settlementPeriod
)
SELECT * FROM stacked_revenue
```

---

## 📊 Verification Steps

### 1. Check Current View (Shows £0)
```bash
cd /home/george/GB-Power-Market-JJ && python3 -c "
from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

query = '''
SELECT settlementDate, settlementPeriod, bm_revenue_per_mwh
FROM \`inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs\`
WHERE settlementDate >= '2025-10-17' AND settlementDate <= '2025-10-23'
ORDER BY settlementDate, settlementPeriod
LIMIT 10
'''
df = client.query(query).to_dataframe()
print(df.to_string(index=False))
"
```

**Expected Output** (currently):
```
settlementDate  settlementPeriod  bm_revenue_per_mwh
2025-10-18      25                0.0                 ← £0!
2025-10-18      30                0.0                 ← £0!
```

### 2. Check New Mart Table (Shows Real Prices)
```bash
cd /home/george/GB-Power-Market-JJ && python3 -c "
from google.cloud import bigquery
import os
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

query = '''
SELECT
  settlement_date,
  settlementPeriod,
  ROUND(total_gross_value_gbp / NULLIF(total_accepted_mwh, 0), 2) as bm_revenue_per_mwh
FROM \`inner-cinema-476211-u9.uk_energy_prod.mart_bm_value_by_vlp_sp\`
WHERE settlement_date >= '2025-10-17' AND settlement_date <= '2025-10-23'
ORDER BY settlement_date, settlementPeriod
LIMIT 10
'''
df = client.query(query).to_dataframe()
print(df.to_string(index=False))
"
```

**Expected Output** (correct prices!):
```
settlement_date  settlementPeriod  bm_revenue_per_mwh
2025-10-18       25                56.40              ← REAL PRICE!
2025-10-18       30                85.92              ← REAL PRICE!
2025-10-18       37                127.38             ← REAL PRICE!
```

---

## ✅ Action Required

### Option 1: Update the View (Recommended)

Create a script to update `v_btm_bess_inputs`:

```bash
# Script: update_btm_view_with_bm_revenue.py
cd /home/george/GB-Power-Market-JJ
python3 update_btm_view_with_bm_revenue.py
```

This will:
1. Get current view definition
2. Add LEFT JOIN to `mart_bm_value_by_vlp_sp`
3. Replace hardcoded `0.0 AS bm_revenue_per_mwh` with real data
4. Recreate view

### Option 2: Update Google Sheets to Query Mart Table Directly

Change `VlpRevenue.gs` to query `mart_bm_value_by_vlp_sp` instead of `v_btm_bess_inputs`:

```javascript
// In energy_dashboard_clasp/VlpRevenue.gs
const VIEW_NAME = 'mart_bm_value_by_vlp_sp';  // Changed!

function getLatestVlpRevenue() {
  const query = `
    SELECT
      settlement_date,
      settlementPeriod,
      vlp_name,
      total_accepted_mwh,
      total_gross_value_gbp,
      avg_price_gbp_per_mwh as bm_revenue_per_mwh  ← NOW HAS REAL PRICES!
    FROM \`${PROJECT_ID}.${DATASET}.${VIEW_NAME}\`
    ORDER BY settlement_date DESC, settlementPeriod DESC
    LIMIT 1
  `;
  ...
}
```

---

## 🎯 Summary

| Issue | Root Cause | Solution |
|-------|------------|----------|
| £0 showing for BM revenue | Google Sheets queries `v_btm_bess_inputs` view with hardcoded `0.0` | Update view to LEFT JOIN `mart_bm_value_by_vlp_sp` |
| Terminal shows correct prices | Script queries `mart_bm_value_by_vlp_sp` directly | ✅ No change needed |

**Next Step**: Choose Option 1 (update view) or Option 2 (update Google Sheets query).

---

**Created**: December 27, 2025
**Issue**: Google Sheets shows £0 for BM revenue
**Status**: Root cause identified, solution documented
**Priority**: HIGH (dashboard displaying incorrect data)
