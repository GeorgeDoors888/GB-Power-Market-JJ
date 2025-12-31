# PHASE 1 IMPLEMENTATION - Quick Wins (1 Week)
## GB Power Market JJ - Dashboard Enhancements

**Date**: December 29, 2025
**Status**: ✅ DIAGNOSTIC COMPLETE | 🚧 IMPLEMENTATION IN PROGRESS

---

## ✅ COMPLETED: Task 1 - EWAP Data Quality Investigation

### ROOT CAUSE IDENTIFIED

**Issue**: Live Dashboard v2 shows EWAP = £0.00/MWh

**Diagnosis**:
- `update_live_metrics.py` queries `CURRENT_DATE()` only
- Early morning hours (SP1-3) have NO data yet
- EBOCF/BOAV lag 1-2 settlement periods behind real-time
- Yesterday (Dec 28): **3,140 records, £303k cashflow** ✅
- Today (Dec 29 SP1): **0 records** ❌

### SOLUTION IMPLEMENTED

**File**: `fix_ewap_data_quality.py`

**Features**:
1. ✅ Fallback to yesterday's data if today < 3 settlement periods
2. ✅ Data state indicators (Valid/No Activity/Lagging/Insufficient Volume/No Data/Error)
3. ✅ Diagnostic dashboard cell updates (L20: EWAP value with icon, M20: status message)
4. ✅ Full diagnostic mode (`--diagnostics-only` flag)

**Data State Icons**:
- ✅ Valid: Healthy data, EWAP calculated correctly
- ⚠️ No Activity: Zero BM acceptances (rare)
- 🔄 Lagging: Data lagging behind current time (normal early morning)
- ⚠️ Insufficient Volume: < 5 settlement periods with data
- ❌ No Data: No EBOCF/BOAV records found
- ❌ Error: Query or calculation failed

**Schema Fixes**:
- `bmrs_ebocf.settlementDate`: STRING → requires `CAST(settlementDate AS DATE)`
- `bmrs_boav.settlementDate`: STRING → requires `CAST(settlementDate AS DATE)`
- `bmrs_boalf.bmUnitId`: Correct field is `bmUnit`

**Usage**:
```bash
# Full diagnostic report
python3 fix_ewap_data_quality.py --diagnostics-only

# Update dashboard with fixed EWAP
python3 fix_ewap_data_quality.py
```

---

## 🚧 IN PROGRESS: Task 2 - Single-Price Frequency & Price Regime

### IMPLEMENTATION

**File**: `add_single_price_frequency_and_regime.py`

**Features**:
1. ✅ Single-price frequency calculation (% SPs where SSP=SBP over 30d)
2. ✅ Price regime classification (Low < £20 < Normal < £80 < High < £150 < Scarcity)
3. ✅ 30-day regime distribution breakdown
4. ✅ Current regime indicator with color coding

**Dashboard Updates**:
- **K24**: Single-Price Frequency label
- **L24**: Percentage value (expected ~100% since P305 Nov 2015)
- **M24**: Status note ("Single pricing (P305 since Nov 2015)")
- **K25**: Regime Distribution (30d) label
- **L25**: "Low: X% | Normal: Y% | High: Z% | Scarcity: W%"
- **M25**: Note ("30-day breakdown")
- **L23**: Updated current regime display

**Price Regimes**:
| Regime | Range | Color | Interpretation |
|--------|-------|-------|----------------|
| Low | < £20/MWh | Light Green (#90EE90) | Low demand / High renewables |
| Normal | £20-80/MWh | Sky Blue (#87CEEB) | Typical market conditions |
| High | £80-150/MWh | Gold (#FFD700) | System stress / Peak demand |
| Scarcity | > £150/MWh | Tomato Red (#FF6347) | Emergency pricing / Supply shortage |

**Historical Context**:
- **BSC Mod P305** (Nov 2015): Merged SSP/SBP into single imbalance price
- Pre-P305: Dual pricing (long → SSP, short → SBP)
- Post-P305: Single pricing for all participants (risk symmetry)
- Expected single-price frequency: **~100%** for data Nov 2015 onwards

**Usage**:
```bash
python3 add_single_price_frequency_and_regime.py
```

---

## 📋 PENDING: Task 3 - Worst 5 SP Risk Metrics

### SPECIFICATION

**Objective**: Display worst 5 settlement periods by net cashflow over 7d and 30d windows

**Data Sources**:
- `bmrs_boalf` or `boalf_with_prices`: Acceptance revenue
- `bmrs_costs`: Imbalance prices (SSP/SBP)
- `elexon_p114_s0142_bpi`: Settlement outcomes (optional, for validation)

**Calculation**:
```sql
per_sp_cashflow =
    SUM(acceptance_revenue) +  -- From BOALF × acceptance price
    SUM(imbalance_charge)      -- From position × SSP/SBP
```

**Dashboard Location**: New panel below K25 (or separate Risk Metrics section)

**Display Format**:
```
Worst 5 SP Losses (7d):
1. Dec 28 SP42: -£12,450  (18:30-19:00)
2. Dec 27 SP38: -£9,280   (17:30-18:00)
3. Dec 26 SP40: -£8,150   (18:30-19:00)
4. Dec 28 SP18: -£7,920   (08:00-08:30)
5. Dec 27 SP44: -£6,340   (20:30-21:00)

30d worst: -£18,750 (Dec 20 SP40)
```

**Implementation File**: `add_worst_sp_risk_metrics.py` (to be created)

**Dependencies**:
1. Position modeling (if not explicitly tracking position)
2. BMU-level aggregation (if tracking specific units)
3. Revenue attribution model (BOALF × price matching)

**Alternative (Simplified)**:
If position unavailable, track **acceptance cashflow only** as proxy for BM revenue volatility.

---

## 📋 PENDING: Task 4 - Dashboard Restructure (4-Block Layout)

### TARGET STRUCTURE

**Current**: Single KPI list (K13:P30) with mixed signals/actions/outcomes

**Proposed**: Four distinct panels

#### Block 1: Market Signals (K5:P12)
- Real-time imbalance price
- Price regime (Low/Normal/High/Scarcity)
- Volatility (30d StdDev)
- Single-price frequency
- Rolling averages (24h, 7d, 30d)

#### Block 2: System Operator Activity (K14:P22)
- Dispatch intensity (acceptances/hr)
- % active SPs
- Median acceptance size (MW)
- EWAP (energy-weighted average price) **with data state**
- SO-flag rate (if available)

#### Block 3: Asset Readiness (R5:V30) - NEW PANEL
- Battery SoC (%) - **Phase 2**
- Headroom/Footroom (MW) - **Phase 2**
- CHP Output (MW) - **Phase 2**
- Spark Spread (£/MWh) - **Phase 2**
- Availability flags

#### Block 4: Financial Outcomes (R32:V45) - NEW PANEL
- Pay-as-bid revenue (24h/7d) - **Phase 3**
- Imbalance settlement (24h/7d) - **Phase 3**
- Net P&L - **Phase 3**
- Value per MWh - **Phase 3**
- Worst 5 SP losses - **Phase 1 (Task 3)**

#### Block 5: 30-Day Context Table (K26:P40) - EXISTING, REFORMAT
- Daily avg price
- Daily volatility
- Total acceptances/day
- Active units/day
- Price regime distribution

**Implementation File**: `restructure_dashboard_4block.py` (to be created)

**Approach**: Create new layout, migrate existing formulas, preserve sparklines

---

## 📋 PENDING: Tasks 5-6 - Interactive DNO/NESO Constraint Maps

### OBJECTIVE

Create interactive Folium-based HTML maps accessible from BtM sheet showing:
1. BtM site locations (from postcodes)
2. DNO boundary polygons
3. DNO constraint cost heatmap
4. NESO constraint boundaries

### DATA SOURCES

**BtM Sites**:
- Google Sheets: BtM tab, column A6 (Postcode)
- Geocoding: `btm_dno_lookup.py` (postcodes.io API)

**DNO Boundaries**:
- BigQuery: `uk_energy_prod.neso_dno_boundaries` (GeoJSON, 14 regions, 1.4 MB)

**DNO Constraint Costs**:
- BigQuery: `uk_energy_prod.constraint_costs_by_dno` (1,470 rows, £10.6B total 2017-2025)

**NESO Constraints**:
- BigQuery: `neso_constraint_breakdown_YYYY_YYYY` (yearly tables)

### IMPLEMENTATION APPROACH

#### Step 1: Export BtM Postcodes to CSV
```python
# File: export_btm_sites_to_csv.py
# Read BtM sheet column A6 (Postcode)
# Geocode via postcodes.io (or use cached from btm_dno_lookup.py)
# Output: btm_sites.csv (postcode, lat, lon, name)
```

#### Step 2: Export DNO GeoJSON from BigQuery
```sql
-- Already exists: neso_dno_boundaries table
-- Export via bq command or python script
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_boundaries`
```

#### Step 3: Create Constraint GeoJSON
```python
# File: create_constraint_geojson.py
# Join constraint_costs_by_dno with neso_dno_boundaries
# Add cost attributes to GeoJSON properties
# Output: dno_constraints.geojson
```

#### Step 4: Build Folium Map
```python
# File: create_btm_constraint_map.py (based on provided template)
# Load: btm_sites.csv, dno_boundaries.geojson, dno_constraints.geojson
# Spatial join: points to polygons
# Create interactive map with layers
# Output: btm_constraint_map.html
```

#### Step 5: Integrate with Google Sheets
```javascript
// Apps Script in BtM sheet
// Add button "View Map"
// Opens btm_constraint_map.html in modal dialog or new tab
// File hosted on: GitHub Pages, Google Drive, or local server
```

### TEMPLATE PROVIDED

User provided complete Python template in request. Key features:
- ✅ Postcode normalization
- ✅ Spatial join (points to polygons)
- ✅ Multiple GeoJSON layers
- ✅ Folium interactive map
- ✅ Layer control
- ✅ Tooltips with constraint data

### DEPENDENCIES

**Python Libraries**:
```bash
pip3 install --user pandas geopandas shapely folium
```

**Data Files Needed**:
1. `btm_sites.csv` - Extract from BtM sheet
2. `uk_postcodes_lookup.csv` - Optional (postcodes.io API alternative)
3. `dno_boundaries.geojson` - From `neso_dno_boundaries` table ✅
4. `dno_constraints.geojson` - Create from `constraint_costs_by_dno` ✅
5. `neso_constraints.geojson` - From `neso_constraint_breakdown_*` tables

**Implementation Files** (to be created):
- `export_btm_sites_to_csv.py`
- `create_constraint_geojson.py`
- `create_btm_constraint_map.py`
- `btm_map_button.gs` (Apps Script)

---

## 📊 PROGRESS SUMMARY

| Task | Status | Completion | Files Created | Next Steps |
|------|--------|------------|---------------|------------|
| 1. Fix EWAP | ✅ Complete | 100% | fix_ewap_data_quality.py | Deploy to cron |
| 2. Single-Price Freq | 🚧 Ready | 95% | add_single_price_frequency_and_regime.py | Execute script |
| 3. Worst 5 SP | 📋 Planned | 0% | - | Create implementation |
| 4. Dashboard Restructure | 📋 Planned | 0% | - | Design 4-block layout |
| 5-6. Constraint Maps | 📋 Planned | 20% | Template provided | Export data, build map |

---

## 🎯 RECOMMENDED EXECUTION ORDER

### Day 1 (Today - Dec 29)
1. ✅ Run `fix_ewap_data_quality.py` → Update dashboard with data state indicators
2. ✅ Run `add_single_price_frequency_and_regime.py` → Add new KPIs
3. ✅ Verify dashboard updates in Google Sheets

### Day 2 (Dec 30)
1. Create `add_worst_sp_risk_metrics.py`
2. Implement per-SP cashflow calculation
3. Add worst 5 SP panel to dashboard
4. Test with 7d and 30d windows

### Day 3 (Dec 31)
1. Export BtM sites to CSV (`export_btm_sites_to_csv.py`)
2. Export DNO GeoJSON from BigQuery
3. Create constraint GeoJSON (`create_constraint_geojson.py`)

### Day 4 (Jan 1)
1. Build Folium map (`create_btm_constraint_map.py`)
2. Test map with BtM data
3. Host HTML file (GitHub Pages or Drive)

### Day 5 (Jan 2)
1. Add Apps Script button to BtM sheet
2. Test end-to-end map workflow
3. Documentation + user guide

### Days 6-7 (Jan 3-4)
1. Dashboard restructure planning
2. Create 4-block layout design
3. Migrate existing KPIs to new structure
4. Polish + conditional formatting

---

## 🔧 DEPLOYMENT INSTRUCTIONS

### EWAP Fix Deployment

```bash
# Test diagnostics first
python3 fix_ewap_data_quality.py --diagnostics-only

# If healthy, update dashboard
python3 fix_ewap_data_quality.py

# Verify in Google Sheets
# Check cells L20 (EWAP value) and M20 (status)

# Optional: Add to cron for automatic updates
crontab -e
# Add: */30 * * * * cd /home/george/GB-Power-Market-JJ && python3 fix_ewap_data_quality.py >> logs/ewap_fix.log 2>&1
```

### Single-Price Frequency Deployment

```bash
# Execute script
python3 add_single_price_frequency_and_regime.py

# Verify in Google Sheets
# Check cells K24-L25 (new KPI rows)

# Apply conditional formatting manually:
# Select L23 (Price Regime cell)
# Format → Conditional formatting
# Custom formula: =L23="Low" → Light Green
# Custom formula: =L23="Normal" → Sky Blue
# Custom formula: =L23="High" → Gold
# Custom formula: =L23="Scarcity" → Tomato Red
```

---

## 📝 NOTES & CAVEATS

### Data Quality Insights

1. **EBOCF/BOAV Lag**: Data lags 1-2 settlement periods behind real-time
   - Normal for operational dashboards
   - Consider fallback to yesterday for early morning hours

2. **Single-Price Frequency**: Expected ~100% for post-Nov 2015 data
   - BSC Mod P305 merged SSP/SBP
   - Any deviation < 95% warrants investigation

3. **bmrs_costs Duplicates**: Pre-existing data (2022-Oct 27) has ~55k duplicates
   - Use `GROUP BY` or `DISTINCT` for duplicate-safe queries
   - New data (Oct 29+) has zero duplicates

4. **BOALF Price Matching**: `boalf_with_prices` view has 85-95% match rate
   - Derived via BOD matching algorithm
   - Filter to `validation_flag='Valid'` (42.8% of records)
   - Coverage: 2022-2025, ~4.7M Valid acceptances

### Schema Quirks

- `bmrs_ebocf.settlementDate`: STRING (not DATE)
- `bmrs_boav.settlementDate`: STRING (not DATE)
- `bmrs_boalf.bmUnit`: Correct field (not `bmUnitId`)
- `bmrs_freq.measurementTime`: Correct field (not `recordTime`)

### External Dependencies

**Missing Data (Phase 2+)**:
- Battery telemetry (SoC, power, cycles)
- CHP telemetry (output MW, heat MWth)
- Gas prices (NBP, TTF)
- Carbon prices (UK ETS)
- Degradation models

**Resolution**: Manual input or API integration required

---

## 📚 RELATED DOCUMENTATION

- `COMPREHENSIVE_FUNCTIONALITY_DIAGNOSTIC.py` - Full diagnostic report
- `.github/copilot-instructions.md` - Project configuration & architecture
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Schema reference
- `PROJECT_CONFIGURATION.md` - All configuration settings
- `CONSTRAINT_MAP_ANALYSIS.md` - Why postcode approach was abandoned (Dec 29)
- `create_dno_constraint_map.py` - Working DNO constraint export (Dec 29)

---

**End of Phase 1 Implementation Guide**
Next: Phase 2 (Battery Operations Panel - 2 weeks)
