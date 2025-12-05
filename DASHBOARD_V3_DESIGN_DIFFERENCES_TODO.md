# Dashboard V3 Design Differences - Complete TODO

**Date**: 2025-12-04  
**Comparison**: Apps Script `buildDashboardV3()` vs Python `apply_dashboard_design.py`

## 📋 Executive Summary

Two distinct Dashboard V3 implementations exist:
- **Apps Script**: Simplified, self-contained design with sparklines and 6-KPI layout
- **Python**: Complex, production-grade design with 7-KPI layout, DNO filtering, and chart automation

**Recommendation**: Reconcile both approaches or choose one as the canonical design.

---

## 🎨 1. COLOR SCHEME DIFFERENCES

### Apps Script Colors
```javascript
Header:         #1E293B (dark slate)
Timestamp:      #94A3B8 (light gray text)
KPI Headers:    #E2E8F0 (light gray)
KPI Values:     #F0F9FF (very light blue)
Section Headers: #CBD5E1 (medium gray)
Table Headers:  #E2E8F0 (light gray)
```

### Python Colors (RGB 0-1)
```python
Header:         #FFA24D (orange) - ORANGE = {red: 1.0, green: 0.64, blue: 0.3}
KPI Headers:    #3367D6 (blue) - BLUE = {red: 0.2, green: 0.404, blue: 0.839}
KPI Values:     #F4F4F4 (light gray) - KPI_GREY = {red: 0.96, green: 0.96, blue: 0.96}
Tables:         #EEEEEE (light gray) - LIGHT_GREY = {red: 0.93, green: 0.93, blue: 0.93}
```

### ✅ TODO: Color Scheme Reconciliation
- [ ] **Decision Required**: Choose between dark slate (Apps Script) vs orange (Python) header
- [ ] **Decision Required**: Choose between light blue (Apps Script) vs light gray (Python) KPI values
- [ ] **Update**: Align all color constants between implementations
- [ ] **Test**: Verify color accessibility (contrast ratios for text readability)
- [ ] **Document**: Add color palette reference to PROJECT_CONFIGURATION.md

---

## 📐 2. LAYOUT STRUCTURE DIFFERENCES

### Apps Script Layout
```
Row 1:    Header (merged A1:M1)
Row 2:    Timestamp (merged A2:M2)
Row 4-6:  KPI Zone (A4:F6) - 6 KPIs with sparklines below
Row 8-18: Generation Mix Table (A8:E18)
Row 21-38: Active Outages (A21:G38) - TOP 15, includes trend column
Row 41-47: Balancing Market Summary (A41:F47) - Last 7 days
Row 55:   Footnotes (merged A55:M55)
```

### Python Layout
```
Row 1:    Header (merged A1:L1)
Row 2:    Timestamp (A2:L2)
Row 3:    Filters (Time Range: B3, Region/DNO: F3)
Row 5:    Gen vs Demand headline (formula)
Row 9-11: KPI Zone (F9:L11) - 7 KPIs with sparklines
Row 9+:   Fuel Mix Table (A9:E9+) - left side
Row 27+:  Active Outages (A27:H27+)
Row 42+:  ESO Interventions (A42:F42+)
```

### ✅ TODO: Layout Reconciliation
- [ ] **Critical**: Apps Script has NO filter dropdowns (Time Range, DNO selector) - Python has both
- [ ] **Critical**: Apps Script KPIs in A4:F6 (6 KPIs), Python in F9:L11 (7 KPIs)
- [ ] **Decide**: Keep dual-column layout (Python) or single-column layout (Apps Script)?
- [ ] **Standardize**: Row numbers for each section across both implementations
- [ ] **Add**: Filter dropdowns to Apps Script if they're missing
- [ ] **Update**: DASHBOARD_V3_README.md with canonical layout diagram

---

## 🔢 3. KPI DIFFERENCES

### Apps Script KPIs (6 total)
```
A4: 💰 Wholesale Avg (£/MWh)      =AVERAGE('Chart_Data_V2'!C:C)
B4: 📈 Market Vol (%)              =STDEV('Chart_Data_V2'!C:C)/AVERAGE('Chart_Data_V2'!C:C)*100
C4: 📊 VLP Revenue (£ k)           =SUM('VLP Revenue'!C:C)
D4: 💹 Net Margin (£/MWh)          ='Chart_Data_V2'!H2
E4: 🔋 Active BMUs                 ='BESS'!B2
F4: ⚡ Volume (MWh)                ='Chart_Data_V2'!E2
```

### Python KPIs (7 total)
```
F9:  📊 VLP Revenue (£ k)                    =AVERAGE(VLP_Data!D:D)/1000
G9:  💰 Wholesale Avg (£/MWh)                =AVERAGE(Market_Prices!C:C)
H9:  📈 Market Vol (%)                       =STDEV(Market_Prices!C:C)/AVERAGE(Market_Prices!C:C)
I9:  All-GB Net Margin (£/MWh)               =AVERAGE(FILTER('Chart Data'!J:J, NOT(ISBLANK('Chart Data'!J:J))))
J9:  Selected DNO Net Margin (£/MWh)         =IF($F$3="All GB", I10, XLOOKUP(...))
K9:  Selected DNO Volume (MWh)               =IF($F$3="All GB", SUM(...), XLOOKUP(...))
L9:  Selected DNO Revenue (£k)               =IF($F$3="All GB", SUM(DNO_Map!$G:$G)/1000, XLOOKUP(...))
```

### ✅ TODO: KPI Reconciliation
- [ ] **Critical**: Apps Script references `'Chart_Data_V2'` - Python uses `'Chart Data'` (no V2)
- [ ] **Critical**: Apps Script references `'VLP Revenue'` sheet - Python uses `VLP_Data` sheet
- [ ] **Critical**: Apps Script references `'BESS'` sheet - not mentioned in Python code
- [ ] **Add**: DNO filtering logic to Apps Script KPIs (J9, K9, L9)
- [ ] **Verify**: Sheet name consistency (`Chart_Data_V2` vs `Chart Data`)
- [ ] **Add**: VLP Revenue calculation to Apps Script (currently just SUM, Python uses AVERAGE/1000)
- [ ] **Test**: All KPI formulas return valid data
- [ ] **Document**: Create KPI_REFERENCE.md with all formulas and data sources

---

## 📊 4. DATA SOURCE DIFFERENCES

### Apps Script Data Sources
```
'Chart_Data_V2'  - Price and volume data (columns C, E, H)
'VLP Revenue'    - VLP revenue data (column C)
'BESS'          - Battery storage data (cell B2)
```

### Python Data Sources
```
'Chart Data'     - Combined timeseries (columns A-J, 49 rows)
'VLP_Data'       - VLP revenue data (column D)
'Market_Prices'  - Market price data (column C)
'DNO_Map'        - DNO mapping data (columns A, E, F, G)
'ESO_Actions'    - ESO balancing actions (columns A-F)
'Outages'        - (Populated by populate_dashboard_tables.py)
```

### ✅ TODO: Data Source Reconciliation
- [ ] **Critical**: Standardize sheet names (`Chart_Data_V2` vs `Chart Data`)
- [ ] **Critical**: Create `'BESS'` sheet if Apps Script depends on it
- [ ] **Critical**: Rename `'VLP Revenue'` to `VLP_Data` OR update Python to match
- [ ] **Audit**: Run `grep -r "Chart_Data_V2" .` to find all references
- [ ] **Audit**: Run `grep -r "'VLP Revenue'" .` to find all references
- [ ] **Create**: Missing sheets in Dashboard V3 spreadsheet
- [ ] **Update**: populate_dashboard_tables.py to populate ALL required sheets
- [ ] **Test**: All formulas resolve correctly after sheet name changes

---

## 📈 5. SPARKLINE DIFFERENCES

### Apps Script Sparklines (Row 6)
```javascript
A6: =SPARKLINE(OFFSET('Chart_Data_V2'!B2,0,0,24,1), {"charttype","line";"color","#3B82F6";"linewidth",2})
B6: =SPARKLINE(OFFSET('Chart_Data_V2'!B2,0,1,24,1), {"charttype","line";"color","#3B82F6";"linewidth",2})
C6: =SPARKLINE(OFFSET('Chart_Data_V2'!B2,0,2,24,1), {"charttype","line";"color","#3B82F6";"linewidth",2})
... (6 total sparklines, one per KPI)
Row Height: 28px
```

### Python Sparklines (Row 11)
```python
F11: =SPARKLINE(VLP_Data!D2:D8, {"charttype","column"})
G11: =SPARKLINE(Market_Prices!C2:C8, {"charttype","line"})
H11: =SPARKLINE(Market_Prices!C2:C8, {"charttype","column"})
I11: =SPARKLINE('Chart Data'!J2:J49)
... (4 sparklines only)
```

### ✅ TODO: Sparkline Reconciliation
- [ ] **Critical**: Apps Script uses 24-row OFFSET range, Python uses fixed ranges (D2:D8, C2:C8, J2:J49)
- [ ] **Decide**: Use 7-day range (Python) or 24-hour range (Apps Script)?
- [ ] **Standardize**: Sparkline chart types (line vs column)
- [ ] **Standardize**: Sparkline colors (Apps Script: #3B82F6 blue, Python: default)
- [ ] **Add**: Sparklines for DNO-specific KPIs (J11, K11, L11) in Python implementation
- [ ] **Fix**: Apps Script data source references (`'Chart_Data_V2'!B2`)
- [ ] **Test**: Sparklines display correctly with live data

---

## 🗂️ 6. TABLE SECTION DIFFERENCES

### Apps Script Tables
```
GENERATION MIX (A8:E18):
  - Row 8: Merged header "⚡ GENERATION MIX & INTERCONNECTORS"
  - Row 9: Headers [Fuel Type, GW, %, Interconnector, Flow (MW)]
  - Rows 10-18: Data rows (9 rows)
  - Conditional formatting: CCGT=tan, WIND=light blue, NUCLEAR=light green

ACTIVE OUTAGES (A21:G38):
  - Row 21: Merged header "🚨 ACTIVE OUTAGES (TOP 15 by MW Lost)"
  - Row 22: Headers [BM Unit, Plant Name, Fuel Type, MW Lost, % Lost, Start Time, <blank>]
  - Rows 23-38: Data rows (16 rows = 15 outages + 1 extra?)
  - Column G: Sparkline trend =SPARKLINE(D22:D38, {'charttype','column';'color','#EF4444'})

BALANCING MARKET SUMMARY (A41:F47):
  - Row 41: Merged header "⚡ BALANCING MARKET SUMMARY (Last 7 Days)"
  - Row 42: Headers [Metric, Value, <blank>, Metric, Value, <blank>]
  - Rows 43-46: 4 metrics displayed in 2-column format
    * Total Actions, Avg Bid Price
    * Active Units, Avg Offer Price
    * Increase MW, Avg Spread
    * Decrease MW, <blank>
  - Row 47: Actions 7-day Trend sparkline
```

### Python Tables
```
FUEL MIX (A9:E9+):
  - Row 9: Headers [Fuel Type, GW, %, Interconnector, Flow (MW)]
  - Rows 10+: Data rows (count not specified)
  - NO merged section header
  - Conditional formatting: IC imports/exports

ACTIVE OUTAGES (A27:H27+):
  - Row 27: Headers [BM Unit, Plant, Fuel, MW Lost, Region, Start Time, End Time, Status]
  - Rows 28+: Data rows (count not specified, populated by populate_dashboard_tables.py)
  - NO merged section header
  - 8 columns (vs 7 in Apps Script)

ESO INTERVENTIONS (A42:F42+):
  - Row 42: Headers [BM Unit, Mode, MW, £/MWh, Duration (min), Action Type]
  - Row 43: =QUERY(ESO_Actions!A:F,"SELECT * ORDER BY A DESC LIMIT 10",1)
  - Dynamic query formula (not static data)
```

### ✅ TODO: Table Reconciliation
- [ ] **Add**: Merged section headers to Python tables (like Apps Script)
- [ ] **Decide**: Keep "TOP 15" outages (Apps Script) or unlimited (Python)?
- [ ] **Standardize**: Outages columns - Apps Script has 7, Python has 8
- [ ] **Add**: Balancing Market Summary to Python (Apps Script has this, Python uses ESO Interventions)
- [ ] **Decide**: Keep Balancing Market Summary (Apps Script) or ESO Interventions (Python)?
- [ ] **Add**: Conditional formatting rules to Python implementation
- [ ] **Fix**: Apps Script Generation Mix has no data population logic
- [ ] **Test**: All tables populate with real data from BigQuery

---

## 🎯 7. CONDITIONAL FORMATTING DIFFERENCES

### Apps Script Conditional Formatting
```javascript
// Fuel Type cell coloring (A10:E18 range)
CCGT → #FFE4B5 (tan/wheat)
WIND → #DBEAFE (light blue)
NUCLEAR → #D1FAE5 (light green)

// Outages sparkline
Column G → RED column chart (#EF4444)
```

### Python Conditional Formatting
```python
// IC Flow conditional (column E)
IF Flow < 0 (import) → Color green
IF Flow > 0 (export) → Color red
```

### ✅ TODO: Conditional Formatting Reconciliation
- [ ] **Add**: Fuel type coloring to Python implementation (CCGT, WIND, NUCLEAR)
- [ ] **Add**: IC import/export coloring to Apps Script implementation
- [ ] **Standardize**: Color codes between implementations
- [ ] **Test**: Conditional formatting triggers correctly with live data
- [ ] **Document**: All conditional formatting rules in DATA_DICTIONARY sheet

---

## 📝 8. FOOTNOTES & DOCUMENTATION

### Apps Script Footnotes (Row 55)
```
"📘 Notes: KPIs auto-calculated from BigQuery (bmrs_mid_iris, bmrs_boalf_iris, 
bmrs_bod_iris). All prices £/MWh; Vol = 30-min price volatility; Net Margin = 
Imbalance – Market Price. Data auto-refreshes every 30 min via Railway API."
```

### Python Footnotes
```
NONE - No footnotes row in Python implementation
```

### ✅ TODO: Documentation Reconciliation
- [ ] **Add**: Footnotes row to Python implementation (similar to Apps Script row 55)
- [ ] **Update**: Refresh frequency statement (Apps Script says "30 min", cron says "15 min")
- [ ] **Clarify**: "Railway API" mention - what is this? (not documented elsewhere)
- [ ] **Add**: Data source attribution (BigQuery project, dataset, tables)
- [ ] **Add**: Cell notes to KPI headers explaining each metric
- [ ] **Create**: DATA_DICTIONARY sheet with all metric definitions

---

## 🔧 9. FORMATTING & STYLING DIFFERENCES

### Apps Script Formatting
```javascript
Font:                Roboto (all cells A1:M100)
Column Width:        120px (columns 1-13, uniform)
Row Heights:         26px (rows 1-65), 28px (sparkline row 6), 28px (row 47)
Frozen Rows:         2 (rows 1-2)
Frozen Columns:      0
Borders:             Applied to all table sections
Header Font Size:    22pt (title), 10pt (timestamp)
KPI Font Size:       11pt (headers), 14pt (values)
Alignment:           Center (most cells)
```

### Python Formatting
```python
Font:                (not specified, likely default)
Column Widths:       Varied (150px, 130px, 180px, 200px - col 0-11)
Row Heights:         (not explicitly set except frozen rows)
Frozen Rows:         3 (rows 1-3)
Frozen Columns:      0
Borders:             (not shown in excerpt)
Header Font Size:    14pt (title), 9pt (timestamp)
KPI Font Size:       10pt (headers), 16pt (values)
Alignment:           LEFT (title), RIGHT (timestamp), CENTER (KPIs)
```

### ✅ TODO: Formatting Reconciliation
- [ ] **Standardize**: Font family (add to Python if missing)
- [ ] **Standardize**: Column widths (Apps Script uniform, Python varied)
- [ ] **Decide**: Frozen rows - 2 (Apps Script) or 3 (Python)?
- [ ] **Standardize**: Font sizes across all elements
- [ ] **Add**: Border styling to Python implementation
- [ ] **Test**: Dashboard renders correctly at different zoom levels
- [ ] **Document**: Style guide in DASHBOARD_V3_STYLE_GUIDE.md

---

## 📱 10. INTERACTIVITY DIFFERENCES

### Apps Script Interactivity
```javascript
// NO custom menu
// NO onEdit triggers
// NO filter dropdowns
// NO DNO map selector
// Sparklines are passive visualizations only
```

### Python Interactivity
```python
// Apps Script Code.gs provides:
- Custom menu "⚡ GB Energy V3"
  * 1. Manual Refresh All Data
  * 2. Show DNO Map Selector
- onEdit() trigger for B3 (Time Range) and F3 (Region)
- DNO Map sidebar (DnoMap.html)
- Filter dropdowns with data validation
```

### ✅ TODO: Interactivity Reconciliation
- [ ] **Critical**: Apps Script buildDashboardV3() has NO menu - but Code.gs does
- [ ] **Add**: Call buildDashboardV3() from Code.gs menu or onOpen()
- [ ] **Add**: Data validation dropdowns to Apps Script design
- [ ] **Test**: onEdit triggers work with new layout
- [ ] **Add**: Time Range options (7d, 30d, 90d, 1y)
- [ ] **Add**: DNO dropdown options (ENWL, NPG, UKPN, SSEN, etc.)
- [ ] **Document**: User interaction flows in USER_GUIDE.md

---

## 🚀 11. DEPLOYMENT DIFFERENCES

### Apps Script Deployment
```javascript
// Single function buildDashboardV3()
// Run manually from Apps Script editor
// No automation
// No cron jobs
// Standalone formatting only
```

### Python Deployment
```python
// Multiple scripts:
1. populate_dashboard_tables.py - Load data from BigQuery
2. apply_dashboard_design.py - Apply formatting
3. rebuild_dashboard_v3_final.py - Master rebuild script
// Automation via cron (15-minute intervals)
// Service account authentication
// External Python environment required
```

### ✅ TODO: Deployment Reconciliation
- [ ] **Decide**: Use Apps Script OR Python as primary deployment method
- [ ] **Option 1**: Convert buildDashboardV3() to call Python via Web App endpoint
- [ ] **Option 2**: Convert Python formatting to Apps Script (no external dependencies)
- [ ] **Add**: buildDashboardV3() to onOpen() menu for easy manual refresh
- [ ] **Add**: Time-based trigger for Apps Script to run buildDashboardV3() every 15 min
- [ ] **Test**: Both deployment methods produce identical output
- [ ] **Document**: Deployment procedure in DEPLOYMENT_GUIDE.md

---

## 📊 12. CHART DIFFERENCES

### Apps Script Charts
```javascript
// NO charts created by buildDashboardV3()
// Only sparklines (inline mini-charts)
```

### Python Charts
```python
// Creates 2 full charts:
1. Combo Chart - System overview (prices, demand, generation)
   - Source: 'Chart Data'!A1:J49
   - Multiple series, dual Y-axes
2. Net Margin Line Chart - Portfolio profitability
   - Source: 'Chart Data'!A1:A49 & J1:J49
```

### ✅ TODO: Chart Reconciliation
- [ ] **Add**: Chart creation to Apps Script buildDashboardV3()
- [ ] **OR**: Keep charts in Python only (call from Apps Script menu)
- [ ] **Decide**: Chart placement in dashboard layout
- [ ] **Standardize**: Chart data sources and ranges
- [ ] **Add**: Chart formatting (colors, titles, axes labels)
- [ ] **Test**: Charts render correctly with live data
- [ ] **Document**: Chart configuration in CHARTS_REFERENCE.md

---

## 🔍 13. DATA QUALITY & VALIDATION

### Apps Script Data Quality
```javascript
// NO explicit validation
// Direct formula references to sheets
// Assumes data exists in Chart_Data_V2, VLP Revenue, BESS
```

### Python Data Quality
```python
// populate_dashboard_tables.py validates:
- BigQuery connection
- Query execution
- Data freshness
- Row counts
// Uses FILTER, XLOOKUP, QUERY functions with error handling
```

### ✅ TODO: Data Quality Improvements
- [ ] **Add**: IFERROR wrappers to all Apps Script formulas
- [ ] **Add**: Data validation checks in buildDashboardV3()
- [ ] **Add**: Timestamp validation (data < 2 hours old = stale warning)
- [ ] **Add**: Row count validation (outages < 1 = show message)
- [ ] **Add**: Visual indicators for stale/missing data
- [ ] **Test**: Dashboard handles missing sheets gracefully
- [ ] **Document**: Data quality rules in DATA_QUALITY_GUIDE.md

---

## 🎯 14. PRIORITY ACTION ITEMS

### CRITICAL (Do First)
1. [ ] **Standardize sheet names** - Audit all references to `'Chart_Data_V2'`, `'VLP Revenue'`, `'BESS'`
2. [ ] **Choose canonical color scheme** - Orange+Blue (Python) or Dark Slate (Apps Script)
3. [ ] **Reconcile KPI count** - 6 KPIs (Apps Script) or 7 KPIs (Python)
4. [ ] **Add filter dropdowns** - Apps Script missing Time Range + DNO selector
5. [ ] **Merge implementations** - Decide on Apps Script OR Python as primary

### HIGH PRIORITY (Do Next)
6. [ ] Add DNO filtering logic to Apps Script KPIs
7. [ ] Add section headers to Python tables (like Apps Script)
8. [ ] Standardize sparkline ranges and colors
9. [ ] Add footnotes to Python implementation
10. [ ] Test both implementations with live data

### MEDIUM PRIORITY
11. [ ] Add conditional formatting to both implementations
12. [ ] Create DATA_DICTIONARY sheet
13. [ ] Add chart creation to Apps Script
14. [ ] Standardize column widths and row heights
15. [ ] Add data validation and error handling

### LOW PRIORITY
16. [ ] Document all formulas in KPI_REFERENCE.md
17. [ ] Create DASHBOARD_V3_STYLE_GUIDE.md
18. [ ] Add user interaction documentation
19. [ ] Create automated tests for both implementations
20. [ ] Add performance monitoring

---

## 📦 15. RECOMMENDED APPROACH

### Option A: Apps Script as Primary (Recommended for Simplicity)
**Pros**: 
- No external dependencies
- Runs directly in Google Sheets
- Easier to maintain
- Faster execution

**Cons**:
- Limited to Apps Script capabilities
- No BigQuery native integration
- Harder to version control

**Steps**:
1. Add filter dropdowns to buildDashboardV3()
2. Add 7th KPI (DNO filtering)
3. Add data population logic (query BigQuery via Connected Sheets or Web App)
4. Add charts creation
5. Deprecate Python scripts

### Option B: Python as Primary (Recommended for Scale)
**Pros**:
- Full BigQuery integration
- Better version control
- More flexible data processing
- Production-grade automation

**Cons**:
- Requires external Python environment
- More complex deployment
- Service account authentication needed

**Steps**:
1. Add merged section headers to Python
2. Add footnotes row to Python
3. Port Apps Script color scheme to Python
4. Add Balancing Market Summary to Python
5. Deprecate Apps Script buildDashboardV3()

### Option C: Hybrid (Recommended for Best of Both)
**Division of Labor**:
- **Python**: Data loading from BigQuery (populate_dashboard_tables.py)
- **Apps Script**: Formatting and interactivity (buildDashboardV3())

**Steps**:
1. Python populates all backing sheets (Chart Data, VLP_Data, Market_Prices, etc.)
2. Apps Script formats and creates formulas on Dashboard V3
3. Apps Script handles user interactions (filters, DNO selector)
4. Both run on schedule (Python every 15 min, Apps Script after Python completes)

---

## 📞 16. NEXT STEPS

### Immediate Actions
1. **Audit Current State**
   - [ ] Run both implementations on test spreadsheet
   - [ ] Screenshot both outputs for visual comparison
   - [ ] Document actual differences in live environment

2. **Stakeholder Decision**
   - [ ] Present 3 options (Apps Script, Python, Hybrid)
   - [ ] Get approval on canonical approach
   - [ ] Confirm color scheme preference

3. **Implementation**
   - [ ] Create DASHBOARD_V3_RECONCILIATION_PLAN.md
   - [ ] Assign tasks from this TODO
   - [ ] Set timeline (suggest: 5-day sprint)
   - [ ] Create test checklist

### Testing Checklist
- [ ] All KPIs display correct values
- [ ] All sparklines render correctly
- [ ] All tables populated with data
- [ ] Filter dropdowns work correctly
- [ ] DNO selector updates KPIs
- [ ] Charts display correctly
- [ ] Conditional formatting triggers
- [ ] Performance < 3 seconds load time
- [ ] Mobile/tablet view renders correctly
- [ ] Works in incognito mode (auth test)

---

## 📚 17. DOCUMENTATION REQUIREMENTS

Create or update these documents:
- [ ] `DASHBOARD_V3_CANONICAL_DESIGN.md` - Single source of truth
- [ ] `DASHBOARD_V3_STYLE_GUIDE.md` - Colors, fonts, spacing
- [ ] `KPI_REFERENCE.md` - All KPI formulas and meanings
- [ ] `DATA_DICTIONARY.md` - All sheet columns explained
- [ ] `CHARTS_REFERENCE.md` - Chart configurations
- [ ] `DEPLOYMENT_GUIDE.md` - Step-by-step deployment
- [ ] `USER_GUIDE.md` - End-user instructions
- [ ] `DATA_QUALITY_GUIDE.md` - Validation rules
- [ ] `TROUBLESHOOTING.md` - Common issues and fixes

---

## ✅ COMPLETION CRITERIA

Dashboard V3 reconciliation is complete when:
- [ ] Only ONE implementation exists (or hybrid clearly defined)
- [ ] All sheet name references standardized
- [ ] All KPIs work with live data
- [ ] All tables populated correctly
- [ ] All sparklines render correctly
- [ ] Filter dropdowns functional
- [ ] DNO selector updates KPIs
- [ ] Charts display correctly
- [ ] Color scheme consistent throughout
- [ ] Documentation complete
- [ ] Tests pass 100%
- [ ] Deployed to production
- [ ] User acceptance testing complete

---

**Status**: 🔴 NOT STARTED  
**Owner**: George Major  
**Priority**: HIGH  
**Estimated Effort**: 3-5 days  
**Due Date**: 2025-12-09

---

*Last Updated: 2025-12-04*  
*For questions, contact: george@upowerenergy.uk*
