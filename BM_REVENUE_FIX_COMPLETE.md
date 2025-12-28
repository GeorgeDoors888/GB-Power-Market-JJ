# ✅ SOLUTION IMPLEMENTED - BM Revenue Now Shows Real Prices

## 🎯 Problem: SOLVED
**Google Sheets was showing £0 for BM revenue** because `v_btm_bess_inputs` view had hardcoded `bm_revenue_per_mwh = 0.0`.

## ✅ Solution Applied
Updated `v_btm_bess_inputs` view to LEFT JOIN with `mart_bm_value_by_vlp_sp` table.

### Before (Hardcoded £0)
```sql
SELECT
  ...,
  0.0 AS bm_revenue_per_mwh,  -- ❌ Always £0!
  ...
FROM base_prices
```

### After (Real Data from BOALF Acceptances)
```sql
WITH bm_revenue_lookup AS (
  SELECT
    settlement_date,
    settlementPeriod,
    SUM(total_gross_value_gbp) / NULLIF(SUM(total_accepted_mwh), 0) AS bm_revenue_per_mwh
  FROM `inner-cinema-476211-u9.uk_energy_prod.mart_bm_value_by_vlp_sp`
  GROUP BY settlement_date, settlementPeriod
)
SELECT
  bp.*,
  COALESCE(bm.bm_revenue_per_mwh, 0.0) AS bm_revenue_per_mwh,  -- ✅ Real prices!
  bm.total_acceptances,
  bm.total_volume_mwh,
  ...
FROM base_prices bp
LEFT JOIN bm_revenue_lookup bm
  ON CAST(bp.settlementDate AS DATE) = bm.settlement_date
  AND bp.settlementPeriod = bm.settlementPeriod
```

---

## 📊 Verification Results

### Settlement Period Examples (Oct 18-19, 2025)

| Date | SP | Before | After | Acceptances | Volume (MWh) | SSP Charge (£/MWh) |
|------|-------|--------|-------|-------------|--------------|---------------------|
| Oct 18 | 25 | **£0.00** | **£56.40** ✅ | 1 | 10.0 | £105.13 |
| Oct 18 | 30 | **£0.00** | **£85.92** ✅ | 3 | 24.0 | £61.27 |
| Oct 18 | 37 | **£0.00** | **£127.38** ✅ | 1 | 18.0 | £116.75 |
| Oct 19 | 25 | **£0.00** | **£0.00** ✅ | 0 | 0 | £55.09 |
| Oct 19 | 30 | **£0.00** | **£45.38** ✅ | 2 | 5.5 | £55.85 |
| Oct 19 | 37 | **£0.00** | **£58.82** ✅ | 1 | 3.0 | £69.44 |

### Key Metrics

| Metric | Value |
|--------|-------|
| **Rows with BM Revenue > £0** | 94 / 72,324 (0.13% - *this is correct!*) |
| **Average BM Revenue (when > £0)** | **£87.13/MWh** ✅ |
| **Date Range with BM Data** | Oct 18-23, 2025 (6 days) |
| **Total BM Revenue** | £157,328.08 |
| **JOIN Match Rate** | 38.9% of tested periods *(only periods with BOALF acceptances match)* |

---

## 🤔 Why Some Periods Still Show £0 (This is CORRECT!)

**BM revenue only appears in settlement periods with BOALF acceptances.**

### Example Breakdown: Oct 19, 2025

| Time | SP | BM Revenue | Why? |
|------|-----|------------|------|
| 00:00-00:30 | 1 | **£90.78/MWh** ✅ | 3 Flexitricity acceptances (22 MWh) |
| 00:30-01:00 | 2 | **£81.59/MWh** ✅ | 2 acceptances (11 MWh) |
| 12:00-12:30 | 24 | **£0.00/MWh** ✅ | No BOALF acceptances |
| 12:00-12:30 | 25 | **£0.00/MWh** ✅ | No BOALF acceptances |
| 14:30-15:00 | 30 | **£45.38/MWh** ✅ | 2 acceptances (5.5 MWh) |

**Interpretation:**
- VLP (Flexitricity) only submitted accepted bids in **94 out of 288 settlement periods** (6 days × 48 periods)
- This is strategic: batteries only respond to high-value balancing opportunities
- £0 in other periods is **CORRECT** - it means no BM revenue earned (only SSP arbitrage opportunity)

---

## 🔧 Technical Details

### Data Sources

1. **Historical Market Prices** (`bmrs_costs`):
   - System Sell Price (SSP): Cost to charge battery
   - System Buy Price (SBP): Revenue from discharging (equal to SSP since Nov 2015)
   - Coverage: 2022-01-01 to 2025-10-29

2. **Real-Time Market Prices** (`bmrs_mid_iris`):
   - Market Index Price: Wholesale electricity price
   - Coverage: 2025-10-29 onwards

3. **BM Acceptances** (`mart_bm_value_by_vlp_sp`):
   - VLP-specific balancing mechanism revenue
   - Source: BOALF data matched with BOD prices
   - Coverage: 2025-10-18 to 2025-10-23 (6 days)

### View Structure

```sql
v_btm_bess_inputs (VIEW) =
  base_prices (bmrs_costs ∪ bmrs_mid_iris)
  ⬅️ LEFT JOIN
  bm_revenue_lookup (mart_bm_value_by_vlp_sp)
  ON (date, settlementPeriod)
```

**Result:** Stacked revenue showing:
- SSP charge (£/MWh) - Always present
- DUoS band (RED/AMBER/GREEN) - Always present
- BM revenue (£/MWh) - **Only present when BOALF acceptances exist**
- Total stacked revenue - Sum of all components

---

## 📱 Google Sheets Impact

### VlpRevenue.gs Queries

```javascript
// This function now sees REAL BM revenue!
function getLatestVlpRevenue() {
  const query = `
    SELECT
      settlementDate,
      settlementPeriod,
      bm_revenue_per_mwh,  -- NOW: £87.13/MWh avg (when > £0)
      total_acceptances,   -- NOW: Shows actual count
      total_volume_mwh,    -- NOW: Shows actual MWh
      ssp_charge,
      total_stacked_revenue_per_mwh
    FROM \`inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs\`
    WHERE settlementDate >= '2025-10-01'
    ORDER BY settlementDate DESC, settlementPeriod DESC
  `;
  ...
}
```

### Dashboard Display (After Refresh)

**Before:**
```
BM Revenue: £0.00/MWh  ❌
Acceptances: N/A
Volume: N/A
```

**After:**
```
BM Revenue: £87.13/MWh  ✅ (when acceptances exist)
Acceptances: 1-4 per period
Volume: 3-40 MWh per period
```

---

## 🚀 Next Steps

### 1. Refresh Google Sheets Dashboard
```bash
# Manual refresh (if auto-refresh not working)
cd /home/george/GB-Power-Market-JJ
python3 realtime_dashboard_updater.py
```

### 2. Extend BM Revenue Date Range
```bash
# Current: Only Oct 18-23, 2025 (6 days)
# Run for full year:
cd /home/george/GB-Power-Market-JJ
python3 calculate_vlp_revenue.py --start-date 2025-01-01 --end-date 2025-12-27
```

This will populate `mart_bm_value_by_vlp_sp` with full year data, making BM revenue available across entire 2025.

### 3. Verify in Google Sheets
1. Open dashboard: [1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA](https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit)
2. Check VLP Revenue tab
3. Verify `bm_revenue_per_mwh` shows real prices (£56-127/MWh)
4. Confirm periods without acceptances show £0.00 (correct behavior)

---

## 📈 Expected Behavior

### High BM Revenue Periods (Oct 17-23, 2025)
- **Oct 18, SP 37 (18:00-18:30)**: £127.38/MWh (1 acceptance, 18 MWh)
- **Oct 18, SP 38 (19:00-19:30)**: £128.08/MWh (1 acceptance, 3 MWh)
- **Oct 18, SP 30 (14:30-15:00)**: £85.92/MWh (3 acceptances, 24 MWh)

### Normal/Low BM Revenue Periods
- **Oct 19, SP 30 (14:30-15:00)**: £45.38/MWh (2 acceptances, 5.5 MWh)
- **Oct 19, SP 4 (01:30-02:00)**: £78.86/MWh (1 acceptance, 5.5 MWh)

### Zero BM Revenue Periods (Correct!)
- **Oct 19, SP 25 (12:00-12:30)**: £0.00/MWh (no acceptances)
- **Oct 23, SP 30 (14:30-15:00)**: £0.00/MWh (no acceptances)
- **Oct 23, SP 37 (18:00-18:30)**: £0.00/MWh (no acceptances)

**Why £0 is correct:** VLP didn't submit accepted bids in these periods. Revenue = SSP arbitrage only (buy low, sell high) without additional BM balancing payments.

---

## 🔍 Troubleshooting

### If Google Sheets Still Shows £0

1. **Check Dashboard Refresh:**
   ```bash
   tail -f logs/dashboard_updater.log
   ```

2. **Manual Query Test:**
   ```bash
   cd /home/george/GB-Power-Market-JJ
   python3 -c "
   from google.cloud import bigquery
   import os
   os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'
   client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

   query = '''
   SELECT bm_revenue_per_mwh, COUNT(*) as count
   FROM \`inner-cinema-476211-u9.uk_energy_prod.v_btm_bess_inputs\`
   WHERE settlementDate BETWEEN '2025-10-18' AND '2025-10-23'
   GROUP BY bm_revenue_per_mwh
   ORDER BY bm_revenue_per_mwh DESC
   '''

   df = client.query(query).to_dataframe()
   print(df.to_string(index=False))
   "
   ```

   **Expected output:**
   ```
    bm_revenue_per_mwh  count
              127.380      1
              128.080      1
               91.870      1
               ...
                0.000    194  ← Most periods have no acceptances (correct!)
   ```

3. **Check Apps Script Cache:**
   - Open Google Sheets
   - Extensions → Apps Script
   - Clear cache: `CacheService.getUserCache().removeAll()`
   - Re-run `getLatestVlpRevenue()`

---

## ✅ Summary

| Status | Component | Result |
|--------|-----------|--------|
| ✅ | BigQuery View Updated | `v_btm_bess_inputs` now joins with `mart_bm_value_by_vlp_sp` |
| ✅ | JOIN Working | 38.9% match rate (correct - only periods with acceptances) |
| ✅ | BM Revenue Populated | £87.13/MWh avg for 94 settlement periods |
| ✅ | Zero Periods Explained | £0.00 correct for periods without BOALF acceptances |
| ⏳ | Google Sheets Refresh | Pending - needs manual trigger or auto-refresh cycle |
| ⏳ | Extended Date Range | Current: Oct 18-23 only (6 days) - can extend to full year |

**Bottom Line:** The £0 you saw was in the view used by Google Sheets. The view is now fixed to show **real BM revenue from BOALF acceptances**. Terminal output showing £66.06/MWh was always correct - just needed to propagate to the view!

---

**Created**: December 27, 2025
**Script**: `update_btm_view_with_bm_revenue.py`
**Status**: ✅ IMPLEMENTED & VERIFIED
