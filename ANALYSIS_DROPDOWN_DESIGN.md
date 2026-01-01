# Analysis Sheet Dropdown System - Comprehensive Design

**Date**: December 30, 2025
**Status**: 🎯 Design Phase
**Goal**: Enable structured search across ALL Elexon/NESO data with multi-select, BMU-level filtering, and advanced capabilities

---

## 📊 DATA LANDSCAPE

### Available Data (335 BigQuery Tables)

**Historical Tables (64)**: bmrs_* prefix, 2020-present
**Real-Time Tables (38)**: *_iris suffix, last 24-48h
**Reference Tables (4)**: dim_party, dim_bmu, bmu_registration_data, neso_dno_reference
**Analysis Tables (229)**: constraints, wind forecasts, interconnectors, REMIT, custom views

### Key Data Categories

1. **Generation Data**
   - B1610 actual generation (`bmrs_indgen`, `bmrs_indgen_iris`)
   - Fuel mix aggregated (`bmrs_fuelinst`, `bmrs_fuelinst_iris`)
   - Wind/solar forecasts (`bmrs_windfor`, `generation_forecast_wind`)
   - Individual BMU generation (2000+ BMUs)

2. **Balancing Mechanism**
   - Bid-offer acceptances with prices (`bmrs_boalf_complete`) - 11M records
   - Bid-offer data (`bmrs_bod`) - 391M rows
   - Balancing costs (`bmrs_disbsad`)
   - Physical notifications (MELs/MILs)

3. **System Operations**
   - System frequency (`bmrs_freq`, `bmrs_freq_iris`)
   - System prices (`bmrs_costs`) - SSP/SBP merged
   - Imbalance volumes (`bmrs_imbalngc`)
   - Demand forecasts/actual (`bmrs_demand_forecast`, `bmrs_inddem`)

4. **Physical Constraints**
   - NESO constraint costs by region (`neso_constraint_breakdown_*`)
   - Constraint forecasts (`neso_constraint_forecast_day_ahead`)
   - Constraint alerts (`constraint_alerts_live`)
   - DNO-level breakdown (`constraint_costs_by_dno_latest`)

5. **Market Data**
   - Market Index Data (`bmrs_mid`) - wholesale prices
   - System prices (`bmrs_costs`)
   - Interconnector flows (via fuelType in fuel mix)
   - Imbalance prices (SSP/SBP merged Nov 2015+)

6. **Asset Availability**
   - REMIT unavailability messages (`bmrs_remit`, `bmrs_remit_unavailability`)
   - MELs/MILs physical limits (`bmrs_melngc`, `bmrs_mels_iris`, `bmrs_mils_iris`)
   - Outage tracking (REMIT integration)

7. **Party Analysis**
   - VTP/VLP parties (`dim_party`) - 50+ traders/aggregators
   - BMU ownership (`bmu_registration_data`) - 2000+ BMUs
   - Party performance analysis

8. **Interconnectors**
   - GB-France, GB-Ireland, GB-Norway, GB-Belgium, GB-Netherlands
   - Flow data in fuel mix (INTFR, INTIRL, INTNSL, etc.)
   - 10 interconnector codes

---

## 🎨 DROPDOWN STRUCTURE DESIGN

### Layout (Analysis Sheet Rows 1-15)

```
Row 1:  [ANALYSIS]
Row 2:
Row 3:  ━━━━ FILTERS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Row 4:  From Date: [DD/MM/YYYY]  |  To Date: [DD/MM/YYYY]  |  Quick Select: [Last 7 Days ▼]
Row 5:
Row 6:  BMU/Station Search: [Type to search 2000+ BMUs...]  |  Selected: [3 BMUs, click to view ▼]
Row 7:  Party Role: [All ▼ | VTP | VLP | Production | Consumption | etc.]  |  Multi-select: [Yes]
Row 8:  Lead Party: [All ▼ | Flexitricity | EDF | Statkraft | etc.]  |  Multi-select: [Yes]
Row 9:
Row 10: Fuel Type: [All ▼ | CCGT | WIND | NUCLEAR | etc.]  |  Location/Region: [All ▼ | Scotland | Wales | etc.]
Row 11: Constraint Type: [All ▼ | Transmission | Distribution | Outage | etc.]
Row 12:
Row 13: ━━━━ DATA CATEGORY ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Row 14: Report Category: [📊 Analytics & Derived ▼]  |  Report Type: [Trend Analysis ▼]  |  Graph: [Line Chart ▼]
Row 15: [Generate Report Button] | Data Available: [2020-01-01 → 2025-12-30 (1,234,567 rows)]
```

### Dropdown Specifications

#### 1. Date Range (B4:F4)

**From Date (B4)**: DD/MM/YYYY text input with validation
**To Date (D4)**: DD/MM/YYYY text input with validation
**Quick Select (F4)**: Dropdown
- Last 7 Days
- Last 30 Days
- Last 90 Days
- Month to Date
- Year to Date
- Custom (uses B4/D4)

#### 2. BMU/Station Search (B6:F6)

**Search Box (B6)**: Text input with autocomplete
- Search by: BMU ID (E_*, M_*, T_*, I_*, D_*, 2__*)
- Search by: Station name ("Hornsea", "Drax", etc.)
- Search by: Party name ("Flexitricity", "EDF", etc.)
- Fuzzy matching enabled

**Selected BMUs (F6)**: Multi-select display
- Shows count: "3 BMUs selected"
- Click to see list in popup
- Comma-separated format: "E_FARNB-1, E_HAWKB-1, 2__FFSEN007"
- "Select All" and "Clear All" buttons

**Data Source**: `bmu_registration_data` + `dim_bmu`
- 2000+ BMUs available
- Includes: BMU ID, station name, party, fuel type, capacity, location

#### 3. Party Role (B7)

**Options**:
- All (default)
- **VTP - Virtual Trading Party** (50+ traders: EDF, Statkraft, British Gas, OVO, E.ON)
- **VLP - Virtual Lead Party** (5 aggregators: Flexitricity, GridBeyond, Danske, SEFE, Erova)
- **Production** (E_* , M_* generators)
- **Consumption** (D_* demand units)
- **Supplier** (2__* supplier BMUs)
- **Interconnector** (I_* international links)
- **Storage** (BESS/pumped storage units)

**Multi-Select**: Yes (comma-separated)
**Data Source**: `dim_party` + BMU naming patterns

#### 4. Lead Party (B8)

**Options**: Dynamic list from `dim_party` + `bmu_registration_data`
- All (default)
- Top 20 parties by BMU count:
  - Flexitricity Limited (59 BMUs, VLP)
  - EDF Energy (125 BMUs, VTP)
  - Statkraft Markets Gmbh (123 BMUs, VTP)
  - British Gas Trading Limited (85 BMUs, VTP)
  - GridBeyond (26 BMUs, VLP)
  - ... (50+ total)

**Multi-Select**: Yes
**Search**: Enabled (fuzzy matching)

#### 5. Fuel Type (B10)

**Options** (from `bmrs_fuelinst`):
- All (default)
- **Fossil**: CCGT, COAL, OIL, OCGT
- **Renewable**: WIND, BIOMASS, NPSHYD (hydro)
- **Nuclear**: NUCLEAR
- **Interconnectors**: INTFR (France), INTIRL (Ireland), INTNSL (Norway), INTEW (Ireland), INTNED (Netherlands), etc.
- **Storage**: PS (pumped storage)
- **Other**: OTHER

**Multi-Select**: Yes
**Applicability**: Fuel mix categories only

#### 6. Location/Region (D10)

**Options**:
- All (default)
- **Countries**: Scotland, Wales, England, Northern Ireland
- **DNO Regions**: UKPN-EPN, UKPN-LPN, UKPN-SPN, SSEN-SEPD, SSEN-SHEPD, NPG-NEEB, NPG-YEEB, NGED-East, NGED-West, etc.
- **Constraint Zones**: B4, B7a, B7b, B7c, B9, etc. (from NESO data)
- **Offshore Wind Zones**: Dogger Bank, Hornsea, Moray Firth, Irish Sea, etc.

**Multi-Select**: Yes
**Data Source**: `neso_dno_reference` + `offshore_wind_farms`

#### 7. Constraint Type (B11)

**Options**:
- All (default)
- **Transmission Constraints** (B4, B7a, B9 zones)
- **Distribution Constraints** (DNO-level)
- **Outages** (planned/unplanned from REMIT)
- **Voltage Issues**
- **Thermal Overload**
- **System Frequency**

**Multi-Select**: Yes
**Applicability**: Physical Constraints category only

#### 8. Report Category (B14)

**12 Categories**:

1. **📊 Analytics & Derived** (BMU-level balancing)
   - Tables: `bmrs_boalf_complete`, `bmrs_bod`
   - Filters: ✅ BMU, ✅ Party, ✅ Date, ❌ Fuel

2. **⚡ Generation & Fuel Mix** (aggregated)
   - Tables: `bmrs_fuelinst`, `bmrs_fuelinst_iris`
   - Filters: ❌ BMU, ❌ Party, ✅ Date, ✅ Fuel

3. **🔋 Individual BMU Generation** (B1610)
   - Tables: `bmrs_indgen`, `bmrs_indgen_iris`
   - Filters: ✅ BMU, ❌ Party, ✅ Date, ❌ Fuel

4. **💰 Balancing Actions** (MELs/MILs)
   - Tables: `bmrs_boalf`, `bmrs_melngc`, `bmrs_mels_iris`, `bmrs_mils_iris`
   - Filters: ✅ BMU, ✅ Party, ✅ Date, ❌ Fuel

5. **📡 System Operations** (frequency, prices, imbalance)
   - Tables: `bmrs_freq`, `bmrs_costs`, `bmrs_imbalngc`
   - Filters: ❌ BMU, ❌ Party, ✅ Date, ❌ Fuel

6. **🚧 Physical Constraints** (NESO regional costs)
   - Tables: `neso_constraint_breakdown_*`, `constraint_costs_by_dno_latest`
   - Filters: ❌ BMU, ❌ Party, ✅ Date, ✅ Location

7. **🔌 Interconnectors** (cross-border flows)
   - Tables: `bmrs_fuelinst` (filtered to INT* fuel types)
   - Filters: ❌ BMU, ❌ Party, ✅ Date, ✅ Fuel (interconnector codes)

8. **📈 Market Prices** (MID, SSP/SBP)
   - Tables: `bmrs_mid`, `bmrs_costs`
   - Filters: ❌ BMU, ❌ Party, ✅ Date, ❌ Fuel

9. **📉 Demand Forecasts** (NESO demand predictions)
   - Tables: `bmrs_demand_forecast`, `bmrs_inddem`
   - Filters: ❌ BMU, ❌ Party, ✅ Date, ✅ Location

10. **🌬️ Wind Forecasts** (wind generation predictions)
    - Tables: `bmrs_windfor`, `generation_forecast_wind`, `wind_forecast_sp`
    - Filters: ❌ BMU, ✅ Location, ✅ Date, ❌ Fuel

11. **⚠️ REMIT Messages** (asset unavailability)
    - Tables: `bmrs_remit`, `bmrs_remit_unavailability`
    - Filters: ✅ BMU, ✅ Party, ✅ Date, ❌ Fuel

12. **🔍 Party Analysis** (VTP/VLP performance)
    - Tables: `dim_party` + `bmrs_boalf_complete` (joined)
    - Filters: ❌ BMU, ✅ Party, ✅ Date, ❌ Fuel

#### 9. Report Type (D14)

**Options**:
- Trend Analysis (30 days) - time series
- Snapshot (single date) - cross-sectional
- Summary Statistics - aggregated
- Comparison (2 periods) - before/after
- Export to CSV - raw data dump

#### 10. Graph Type (F14)

**Options**:
- Line Chart (Time Series)
- Bar Chart (Categorical)
- Stacked Area (Composition)
- Scatter Plot (Correlation)
- Heatmap (2D density)
- None (Table Only)

---

## 🔗 FILTER COMPATIBILITY MATRIX

| Category | BMU | Party | Fuel | Location | Constraint | Date |
|----------|-----|-------|------|----------|------------|------|
| Analytics & Derived | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| Generation & Fuel Mix | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Individual BMU Gen | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Balancing Actions | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| System Operations | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Physical Constraints | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ |
| Interconnectors | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ |
| Market Prices | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| Demand Forecasts | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| Wind Forecasts | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ |
| REMIT Messages | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| Party Analysis | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ |

---

## 🔍 MULTI-SELECT IMPLEMENTATION

### Syntax Options

**Option 1: Comma-Separated (Simple)**
```
B6: "E_FARNB-1, E_HAWKB-1, 2__FFSEN007"
→ Splits on comma, generates IN clause
```

**Option 2: Apps Script Multi-Select Dialog (Advanced)**
```javascript
function showBmuSelector() {
  var html = HtmlService.createHtmlOutputFromFile('bmu_selector')
    .setWidth(600)
    .setHeight(400);
  SpreadsheetApp.getUi().showModalDialog(html, 'Select BMUs');
}
```

**Option 3: Data Validation with Custom List (Native)**
```
B6: Data Validation → List from range → BMU_List!A:A
     Allow multiple selections: Manual comma entry
```

### Query Generation

**Single BMU**:
```sql
WHERE bmUnit = 'E_FARNB-1'
```

**Multiple BMUs** (comma-separated input):
```python
bmu_ids = "E_FARNB-1, E_HAWKB-1, 2__FFSEN007"
bmu_list = [b.strip() for b in bmu_ids.split(',')]
bmu_filter = f"WHERE bmUnit IN ({','.join([f\"'{b}'\" for b in bmu_list])})"
# Result: WHERE bmUnit IN ('E_FARNB-1', 'E_HAWKB-1', '2__FFSEN007')
```

**Wildcard Search** (e.g., all Flexitricity BMUs):
```sql
WHERE bmUnit LIKE '2__AFLEX%'
```

---

## 🛠️ IMPLEMENTATION PLAN

### Phase 1: Enhanced Layout (Todo #4)
- Redesign rows 1-15 with new structure
- Add 12 data category options
- Add multi-select indicators
- Add data availability display

### Phase 2: Reference Tables (Todo #6)
- Create `dim_bmu_master` table:
  ```sql
  SELECT
    r.elexonbmunit as bmu_id,
    r.bmunitname as station_name,
    r.leadpartyname as party_name,
    r.fueltype as fuel_type,
    p.is_vlp,
    p.is_vtp,
    r.demandcapacity as capacity_mw,
    r.nationalgridbmunit as ng_bmu_id
  FROM bmu_registration_data r
  LEFT JOIN dim_party p ON r.leadpartyname = p.party_name
  ```
- Upload 2000+ BMUs to BigQuery for fast lookup

### Phase 3: Multi-Select Dropdowns (Todo #5)
- Implement comma-separated parsing
- Add Apps Script dialog for BMU selection
- Add "Select All" / "Clear All" buttons
- Add search functionality

### Phase 4: Query Engine (Todo #8)
- Rewrite `get_query_with_filters()` for 12 categories
- Add multi-select BMU logic (IN clause)
- Add filter validation (warn incompatible combos)
- Add query preview before execution

### Phase 5: Testing & Documentation (Todos #13-15)
- Test all 12 categories with various filters
- Test multi-select with 10+ BMUs
- Test performance with large result sets
- Write comprehensive user guide

---

## 📋 EXAMPLE QUERIES

### Example 1: VLP Battery Performance (Analytics)
**Filters**:
- Date: 01/12/2025 → 30/12/2025
- Party Role: VLP
- Lead Party: Flexitricity Limited, GridBeyond
- Category: Analytics & Derived

**Generated Query**:
```sql
WITH bmu_parties AS (
  SELECT r.elexonbmunit as bmUnit, p.party_name, p.is_vlp
  FROM bmu_registration_data r
  JOIN dim_party p ON r.leadpartyname = p.party_name
  WHERE p.is_vlp = TRUE
  AND p.party_name IN ('Flexitricity Limited', 'GridBeyond')
)
SELECT
  CAST(b.settlementDate AS DATE) as date,
  b.settlementPeriod,
  b.bmUnit,
  bp.party_name,
  SUM(b.acceptanceVolume) as total_volume_mwh,
  AVG(b.acceptancePrice) as avg_price_gbp_mwh
FROM bmrs_boalf_complete b
JOIN bmu_parties bp ON b.bmUnit = bp.bmUnit
WHERE CAST(b.settlementDate AS DATE) >= '2025-12-01'
AND CAST(b.settlementDate AS DATE) <= '2025-12-30'
AND b.validation_flag = 'Valid'
GROUP BY date, b.settlementPeriod, b.bmUnit, bp.party_name
ORDER BY date, b.settlementPeriod
```

### Example 2: Wind Generation by Region (Wind Forecasts)
**Filters**:
- Date: 15/12/2025 → 30/12/2025
- Location: Scotland, Dogger Bank
- Category: Wind Forecasts

**Generated Query**:
```sql
SELECT
  CAST(f.startTime AS DATE) as date,
  f.settlementPeriod,
  wf.wind_farm_name,
  wf.location_region,
  f.generation_forecast_mw,
  w.generation_actual_mw
FROM generation_forecast_wind f
JOIN wind_farm_to_bmu wf ON f.bmUnit = wf.bmUnit
LEFT JOIN wind_outturn_sp w
  ON f.settlementDate = w.settlementDate
  AND f.settlementPeriod = w.settlementPeriod
  AND f.bmUnit = w.bmUnit
WHERE CAST(f.startTime AS DATE) >= '2025-12-15'
AND CAST(f.startTime AS DATE) <= '2025-12-30'
AND wf.location_region IN ('Scotland', 'Dogger Bank')
ORDER BY date, f.settlementPeriod, wf.wind_farm_name
```

### Example 3: Constraint Costs by DNO (Physical Constraints)
**Filters**:
- Date: 01/11/2025 → 30/11/2025
- Location: UKPN-EPN, SSEN-SEPD
- Constraint Type: Transmission Constraints
- Category: Physical Constraints

**Generated Query**:
```sql
SELECT
  date,
  dno_region,
  constraint_type,
  SUM(total_cost_gbp) as total_cost,
  SUM(total_volume_mwh) as total_volume,
  AVG(avg_price_gbp_mwh) as avg_price
FROM neso_constraint_breakdown_2025_2026
WHERE date >= '2025-11-01'
AND date <= '2025-11-30'
AND dno_region IN ('UKPN-EPN', 'SSEN-SEPD')
AND constraint_type = 'Transmission Constraints'
GROUP BY date, dno_region, constraint_type
ORDER BY date, dno_region
```

### Example 4: Multi-BMU Generation Comparison (Individual BMU Gen)
**Filters**:
- Date: 20/12/2025 → 30/12/2025
- BMU IDs: E_FARNB-1, E_HAWKB-1, E_CONTB-1, 2__FFSEN007
- Category: Individual BMU Generation

**Generated Query**:
```sql
SELECT
  CAST(settlementDate AS DATE) as date,
  settlementPeriod,
  bmUnit,
  generation_mw
FROM bmrs_indgen_iris
WHERE CAST(settlementDate AS DATE) >= '2025-12-20'
AND CAST(settlementDate AS DATE) <= '2025-12-30'
AND bmUnit IN ('E_FARNB-1', 'E_HAWKB-1', 'E_CONTB-1', '2__FFSEN007')
ORDER BY date, settlementPeriod, bmUnit
```

---

## 🎯 SUCCESS CRITERIA

**Functionality**:
- ✅ All 12 data categories accessible
- ✅ Multi-select works for BMU, Party, Fuel, Location
- ✅ Search finds BMUs by ID, name, party
- ✅ Filter validation prevents incompatible combinations
- ✅ Query generation handles OR logic correctly

**Performance**:
- ✅ Dropdown population: <2 seconds
- ✅ BMU search autocomplete: <500ms
- ✅ Query execution: <10 seconds for 1M rows
- ✅ Multi-select with 100+ BMUs: <15 seconds

**User Experience**:
- ✅ Intuitive layout with clear sections
- ✅ Inline help text explains each filter
- ✅ Visual indicators show applied filters
- ✅ Error messages guide user to fix issues
- ✅ Results summary shows what was filtered

---

**Document**: ANALYSIS_DROPDOWN_DESIGN.md
**Status**: 🎯 Ready for Implementation
**Next**: Todo #4 - Design Analysis Sheet Layout v2
**ETA**: 2-3 days for full implementation
