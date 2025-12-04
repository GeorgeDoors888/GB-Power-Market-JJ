# Task 3 & 4 Completion Guide

**Date**: December 4, 2025  
**Status**: Scripts ready, awaiting execution

---

## Task 3: Import DNO Centroids to Google Sheets ✅ READY

### What It Does
Imports `dno_centroids.csv` (generated on Dell machine) to Google Sheets with interactive GeoChart setup.

### Files Created
- ✅ `python/import_dno_centroids_to_sheets.py`
- ✅ `dno_centroids.csv` (14 DNO regions with lat/lon)

### Run Command
```bash
cd ~/GB-Power-Market-JJ
python3 python/import_dno_centroids_to_sheets.py
```

### What It Creates
- New tab: **DNO_CENTROIDS**
- Columns: dno_id, dno_name, lat, lon, size, value
- Formula in column F: `=IF(B2='Dashboard V3'!$B$10, 1, 0)`
- Formatted header (blue background)

### Manual Steps After Import
1. Open: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc
2. Go to **DNO_CENTROIDS** tab
3. Select data range **A1:F15**
4. **Insert → Chart**
5. Chart type: **Geo chart**
6. Region: **World** or **United Kingdom**
7. Display mode: **Markers**
8. Setup:
   - Latitude: Column C (lat)
   - Longitude: Column D (lon)
   - Color: Column F (value)
   - Tooltip: Column B (dno_name)
9. Style:
   - Min value (0): Light grey #CCCCCC
   - Max value (1): Bright highlight #FF6B35

### Testing
1. Go to Dashboard V3
2. Change cell **B10** to a DNO ID: `ENWL`, `NPG`, `UKPN`, `NGED`, `SPEN`, `SSEN`
3. GeoChart marker should highlight
4. Tooltip shows DNO name

---

## Task 4: Update Dashboard V3 KPI Formulas ✅ READY

### Background
Phase 1 created two BigQuery objects:
1. `vlp_revenue_sp` - Fact table (295,745 rows)
2. `bod_boalf_7d_summary` - View with pre-aggregated KPIs

Dashboard V3 row 10 needs formulas updated to use the new view.

### Files Created
- ✅ `python/import_bod_summary_to_sheets.py` - Imports BigQuery data
- ✅ `python/task4_update_kpi_formulas.py` - Updates formulas
- ✅ `update_dashboard_v3_kpis.gs` - Apps Script alternative

### Execution Plan

#### Step 1: Import bod_boalf_7d_summary Data
```bash
cd ~/GB-Power-Market-JJ
python3 python/import_bod_summary_to_sheets.py
```

**What it does**:
- Queries BigQuery: `SELECT * FROM uk_energy_prod.bod_boalf_7d_summary`
- Creates/clears **BOD_SUMMARY** tab
- Imports all rows (GB_total, selected_dno, vlp_portfolio)
- Formats header (green background)

**Expected output**:
```
📊 Data Summary:
   GB Total rows: 1
   DNO rows: ~14
   Portfolio rows: ~50-100
```

#### Step 2: Update Dashboard V3 Formulas
```bash
python3 python/task4_update_kpi_formulas.py
```

**What it does**:
- Updates 5 cells in Dashboard V3 row 10:

| Cell | Current | New Formula | Purpose |
|------|---------|-------------|---------|
| F10 | ❌ Wrong | `=QUERY(BOD_SUMMARY!A:Q, "SELECT F WHERE A='GB_total' LIMIT 1")/1000` | VLP Revenue £k (All-GB) |
| I10 | ❌ Wrong | `=QUERY(BOD_SUMMARY!A:Q, "SELECT K WHERE A='GB_total' LIMIT 1")` | All-GB Net Margin (£/MWh) |
| J10 | ❌ Missing | `=QUERY(BOD_SUMMARY!A:Q, "SELECT K WHERE A='selected_dno' AND B='"&BESS!B6&"' LIMIT 1")` | Selected DNO Net Margin |
| K10 | ❌ Missing | `=QUERY(BOD_SUMMARY!A:Q, "SELECT E WHERE A='selected_dno' AND B='"&BESS!B6&"' LIMIT 1")` | Selected DNO Volume (MWh) |
| L10 | ❌ Missing | `=QUERY(BOD_SUMMARY!A:Q, "SELECT F WHERE A='selected_dno' AND B='"&BESS!B6&"' LIMIT 1")/1000` | Selected DNO Revenue £k |

**Column Mapping in BOD_SUMMARY**:
- A: breakdown (GB_total, selected_dno, vlp_portfolio)
- B: dno (DNO code)
- C: bm_unit_id
- D: BM_revenue_gbp
- E: net_balancing_volume_mwh
- F: total_revenue_gbp
- G: total_wholesale_cost_gbp
- H: total_duos_gbp
- I: total_levies_gbp
- J: avg_bm_price_gbp_per_mwh
- K: net_margin_gbp_per_mwh (£/MWh)
- L: active_units
- M: total_acceptances
- N: offer_up_volume_mwh
- O: bid_down_volume_mwh
- P: so_initiated_count
- Q: so_initiated_volume_mwh

### Verification

After running both scripts:

1. **Check BOD_SUMMARY tab**:
   - Should have ~15-120 rows
   - Header row formatted (green)
   - Column A has: GB_total, selected_dno, vlp_portfolio

2. **Check Dashboard V3 row 10**:
   - F10 should show revenue value (e.g., "480,442" for £480M)
   - I10 should show margin (e.g., "113.96" for £113.96/MWh)
   - J10, K10, L10 should show "N/A" until DNO is selected in BESS!B6

3. **Test DNO selection**:
   - Go to BESS sheet
   - Change cell B6 to a DNO code (e.g., "UKPN-EPN", "NPG", "ENWL")
   - Dashboard V3 cells J10, K10, L10 should update

### Expected Values (October 2025 Data)

From BigQuery validation:

**GB Total** (breakdown='GB_total'):
- BM Revenue: £681,750,066
- Total Revenue (F10): £480,442 (in £k) = £480.4M
- Net Margin (I10): £113.96/MWh
- Volume: -114,869 MWh (negative = net charging)
- Active Units: 402 BMUs

**Selected DNO** (breakdown='selected_dno'):
- Values depend on selected DNO in BESS!B6
- Will show N/A if no DNO selected

---

## Alternative: Apps Script Method

If Python scripts fail, use Apps Script:

1. Open: https://docs.google.com/spreadsheets/d/1LmMq4OEE639Y-XXpOJ3xnvpAmHB6vUovh5g6gaU_vzc
2. Extensions → Apps Script
3. Paste contents of `update_dashboard_v3_kpis.gs`
4. Save and run `updateDashboardV3KPIs()`
5. Or use menu: 🔧 Dashboard Tools → Update KPI Formulas

---

## Troubleshooting

### "BOD_SUMMARY sheet not found"
**Solution**: Run `python3 python/import_bod_summary_to_sheets.py` first

### "Query returned no rows"
**Cause**: No data for selected DNO in BOD_SUMMARY  
**Solution**: Check BESS!B6 has valid DNO code, re-import BOD_SUMMARY

### "Import timeout"
**Solution**: Script imports in batches of 500 rows, should handle large datasets

### "Formula shows #N/A"
**Cause**: QUERY function returned no results  
**Solution**: Check BOD_SUMMARY data exists for that breakdown type

---

## Full Execution Sequence

```bash
# Task 3: DNO Centroids
cd ~/GB-Power-Market-JJ
python3 python/import_dno_centroids_to_sheets.py
# Then manually create GeoChart (see instructions above)

# Task 4: Dashboard KPIs
python3 python/import_bod_summary_to_sheets.py  # Import data first
python3 python/task4_update_kpi_formulas.py      # Update formulas second
```

---

## Files Reference

### Scripts Created
```
python/import_dno_centroids_to_sheets.py    - Task 3 (DNO map)
python/import_bod_summary_to_sheets.py      - Task 4 Step 1 (data import)
python/task4_update_kpi_formulas.py         - Task 4 Step 2 (formula update)
update_dashboard_v3_kpis.gs                 - Apps Script alternative
```

### Data Files
```
dno_centroids.csv                           - 14 DNO lat/lon centroids
```

### Documentation
```
DNO_GEOCHART_MAPPING_GUIDE.md              - Full DNO mapping guide
DNO_CENTROIDS_READY.md                     - Dell machine generation summary
PHASE1_COMPLETION_SUMMARY.md               - Phase 1 BigQuery setup details
```

---

## Next Steps After Completion

1. ✅ Task 3 complete: DNO interactive map working
2. ✅ Task 4 complete: Dashboard V3 KPIs live
3. ⏳ Task 5-7: Additional KPI enhancements (future)
4. ⏳ IRIS integration: Add real-time data to views

---

*Last Updated: December 4, 2025*
