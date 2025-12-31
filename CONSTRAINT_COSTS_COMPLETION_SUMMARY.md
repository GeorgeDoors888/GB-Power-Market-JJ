# NESO Constraint Cost Rework - Completion Summary

**Date**: December 29, 2024
**Status**: ✅ **COMPLETE**

## What Was Done

### 1. Data Audit ✅
- Discovered NESO constraint breakdown data **already existed** in 9 tables (FY 2017-2026)
- Identified old `constraint_costs_by_dno` table with **equal allocation bug** (£760.34M × 14 DNOs)
- Validated schema: 4 cost types + 4 volume types per day, 3,358 total records

### 2. Unified View Created ✅
**Table**: `v_neso_constraints_unified` (VIEW)
- Combines all 9 FY tables into single queryable view
- Robust date parsing (handles both `YYYY-MM-DD` and `YYYY-MM-DDT00:00:00` formats)
- Calculated fields: Financial year, totals, constraint type breakdown
- **Rows**: 3,183 daily records (2017-04-01 to 2025-12-18)

### 3. Aggregation Tables Created ✅

#### A. `constraint_costs_monthly` (105 rows)
- Monthly totals by constraint type
- Average £/MWh prices by type
- Covers 105 months (Apr 2017 - Dec 2025)

#### B. `constraint_costs_annual` (9 rows)
- Financial year totals with breakdown percentages
- Key finding: Thermal constraints = 70-90% of costs
- **FY2024-25 total**: £1,904.6M (89.8% Thermal, 8.1% Voltage)

#### C. `constraint_trend_summary` (3,183 rows)
- Daily time-series with 7d/30d moving averages
- Dominant constraint type identification
- Designed for dashboard/visualization export

### 4. Old Data Deleted ✅
- Deleted `constraint_costs_by_dno` (1,470 rows with equal allocation bug)
- Verified new tables exist and contain correct data
- No data loss - all historical data preserved in unified view

### 5. Google Sheets Integration ✅
**Script**: `export_constraints_to_sheets.py`
- Created new "Constraint Costs" sheet in "GB Live 2" dashboard
- Exports:
  - **Annual Summary**: 9 FYs with £M totals and breakdown percentages
  - **Monthly Totals**: Last 24 months
  - **Daily Timeline**: Last 90 days with moving averages
- Successfully tested and deployed
- **URL**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

### 6. Documentation Created ✅
**File**: `CONSTRAINT_COSTS_DOCUMENTATION.md` (15KB)
- Complete schema documentation for all tables
- Query patterns (5 common use cases)
- Known limitations (no regional attribution, daily granularity only)
- Maintenance procedures
- Integration guide

## Files Created

```
/home/george/GB-Power-Market-JJ/
├── create_constraint_unified_view.sql          (7KB - VIEW definition)
├── create_constraint_aggregations.py           (6KB - Table creation script)
├── export_constraints_to_sheets.py             (7KB - Sheets integration)
└── CONSTRAINT_COSTS_DOCUMENTATION.md           (15KB - Comprehensive docs)
```

## BigQuery Objects Created

```sql
-- Views (1)
inner-cinema-476211-u9.uk_energy_prod.v_neso_constraints_unified

-- Tables (3)
inner-cinema-476211-u9.uk_energy_prod.constraint_costs_monthly      (105 rows)
inner-cinema-476211-u9.uk_energy_prod.constraint_costs_annual       (9 rows)
inner-cinema-476211-u9.uk_energy_prod.constraint_trend_summary      (3,183 rows)
```

## Key Statistics

### Coverage
- **Time Period**: April 1, 2017 - December 18, 2025
- **Financial Years**: FY2017-18 through FY2025-26 (partial)
- **Total Days**: 3,183 daily records
- **Months**: 105 months aggregated

### Constraint Breakdown (Last 5 FYs)
| Financial Year | Total Cost | Thermal % | Voltage % | Days |
|---------------|-----------|-----------|-----------|------|
| FY2025-26 | £1,500.7M | 85.6% | 11.8% | 261 (partial) |
| FY2024-25 | £1,904.6M | 89.8% | 8.1% | 365 |
| FY2023-24 | £1,390.5M | 74.8% | 19.3% | 366 |
| FY2022-23 | £1,754.3M | 85.7% | 8.1% | 365 |
| FY2021-22 | £1,420.3M | 79.9% | 7.8% | 365 |

### Recent Daily Data (Dec 14-18, 2025)
```
2025-12-18: £10.2M | -69,958 MWh | £145.14/MWh | Thermal
2025-12-17: £11.0M | -64,714 MWh | £169.49/MWh | Thermal
2025-12-16:  £1.7M | -13,153 MWh | £132.28/MWh | Thermal
2025-12-15:  £1.5M |  17,696 MWh |  £84.32/MWh | Thermal
2025-12-14: £14.4M | -93,794 MWh | £153.50/MWh | Thermal
```

## Usage Examples

### Query Recent Constraints
```sql
SELECT constraint_date, total_cost_gbp, dominant_constraint
FROM `inner-cinema-476211-u9.uk_energy_prod.constraint_trend_summary`
WHERE constraint_date >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
ORDER BY constraint_date DESC;
```

### Monthly Trend Analysis
```sql
SELECT year_month, total_cost_gbp, thermal_cost_gbp, voltage_cost_gbp
FROM `inner-cinema-476211-u9.uk_energy_prod.constraint_costs_monthly`
ORDER BY year_month DESC
LIMIT 12;
```

### Export to Sheets
```bash
python3 export_constraints_to_sheets.py
```

## Known Limitations

1. **No Regional Attribution**: National-level only (no DNO/GSP breakdown)
   - Future enhancement: Spatial join with BMU locations from BOALF

2. **Daily Granularity Only**: No settlement period level data
   - Workaround: Use BOALF acceptance spikes as intraday constraint proxy

3. **Cost Methodology Opaque**: NESO allocation methods not documented
   - Cross-validate with DISBSAD settlement data where possible

4. **Volume Sign Convention**: Negative volumes (likely bids vs offers)
   - Use absolute values for totals, investigate sign meaning

5. **Partial FY2025-26**: Only 261 days (Apr-Dec 2025)
   - Mark as partial in analysis

## Next Steps (Optional Enhancements)

### Priority 1: Regional Attribution
- Spatial join with `dim_bmu` and `bmrs_boalf_complete`
- Attribute costs to DNO regions using BMU locations
- Create `constraint_costs_by_dno_spatial` table

### Priority 2: Intraday Proxy
- Build BOALF acceptance spike detector
- Identify constraint events in real-time
- Flag high-price acceptance clusters

### Priority 3: Visualization
- Create constraint map (Geo Chart or Leaflet)
- Heat map of cost density by region
- Time-series charts in dashboard

### Priority 4: Forecasting
- Ingest NESO day-ahead constraint forecasts (CKAN API)
- Build constraint prediction model
- Add forecast vs actual comparison

## Performance Notes

- **View Query Time**: 0.5-2s for typical queries (3,183 rows)
- **Monthly Aggregation**: <1s (105 rows)
- **Annual Aggregation**: <0.5s (9 rows)
- **Sheets Export Time**: ~5-7s (125 rows exported)

## Validation Checks

### Data Quality ✅
```bash
# No missing dates in expected range: ✅ PASS
# No negative total costs: ✅ PASS
# No duplicate dates: ✅ PASS
# Financial year calculation correct: ✅ PASS
```

### Integration Testing ✅
```bash
# BigQuery view query: ✅ PASS
# Monthly aggregation: ✅ PASS
# Annual aggregation: ✅ PASS
# Sheets export: ✅ PASS
# Formatting applied: ✅ PASS
```

## References

- **Documentation**: `CONSTRAINT_COSTS_DOCUMENTATION.md`
- **Scripts**:
  - `create_constraint_aggregations.py` (table creation)
  - `export_constraints_to_sheets.py` (Sheets integration)
- **SQL**: `create_constraint_unified_view.sql` (view definition)
- **Copilot Instructions**: `.github/copilot-instructions.md` (section: DNO Lookup & DUoS Rates System)

## Contact

**Maintainer**: George Major (george@upowerenergy.uk)
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ
**Dashboard**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA

---

## Todo List Progress

**Completed** (6 of 20):
- ✅ #1: Review current spreadsheet functionality
- ✅ #3: Delete old constraint data with equal allocation bug
- ✅ #4: Ingest NESO Constraint Breakdown data (SKIP - already exists)
- ✅ #5: Create constraint cost aggregation queries
- ✅ #19: Export constraint summaries to Sheets
- ✅ #20: Document constraint data architecture

**Remaining** (14 tasks):
- #2: Review copilot instructions for missing functionality
- #6: Implement postcodes.io geocoding for constraints
- #7: Generate BigQuery data dictionary
- #8: Build canonical BMU reference model
- #9: Add P246 LLF Exclusions data
- #10: Implement NESO Day-Ahead Constraint Flows
- #11: Create live constraint proxy from BOALF
- #12-17: Dashboard KPI improvements (trader labels, battery/CHP metrics, risk, layout, alerts)
- #18: Create constraint geo-visualization

---

*Last Updated: December 29, 2024 - 15:30 UTC*
