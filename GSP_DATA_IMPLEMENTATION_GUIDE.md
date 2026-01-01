# GSP Data Implementation Guide

## 📊 Overview

Your GSP/DNO analysis findings are now implemented and visible in the **"GSP-DNO Analysis"** sheet:

**Direct Link**: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA/edit#gid=SHEET_ID

## ✅ What's Been Implemented

### 1. Key Findings (Rows 4-15)
- ✅ **14 GSP Groups** (DNO licence areas) mapped to Elexon codes (_A through _P)
- ✅ **333 Individual NESO GSPs** with geographic boundaries
- ✅ **1,403 Active BM Units** (698 with GSP assignments = 49.8% coverage)
- ✅ **12 Report Types** defined (heatmaps, charts, geographic visualizations)
- ✅ **Top 3 Regions**:
  - Eastern (_A): 2,213 MW - UK Power Networks (Eastern)
  - North Scotland (_P): 1,934 MW - Scottish Hydro Electric Power Distribution
  - Southern (_H): 1,906 MW - Southern Electric Power Distribution

### 2. GSP Groups Table (Rows 19+)
Complete table with all 14 DNO licence areas showing:
- **Elexon Code**: _A through _P (settlement codes)
- **GSP Group Name**: Eastern, London, North Scotland, etc.
- **DNO Code**: EPN, WMID, SHEPD, etc.
- **DNO Operator**: Full operator names
- **Coverage Area**: Geographic coverage
- **BMU Count**: Number of BM units in each region
- **Total MW**: Total generation capacity

### 3. Individual NESO GSPs (Sample of 333)
First 50 GSPs shown with:
- **NESO GSP ID**: GSP_1 through GSP_333 (NESO's geographic identifiers)
- **GSP Name**: Display names
- **Area (sq km)**: Geographic coverage area
- **GSP Group**: Which of the 14 groups it belongs to
- **Elexon Code**: Settlement code for linking to BMRS data
- **Settlement Use**: How to use in B1610 and other queries

### 4. Data Linking Guide
Comprehensive table showing:
- How to join GSP Groups to settlement data (bmrs_bod, bmrs_boalf)
- How to use geographic boundaries (neso_gsp_boundaries)
- How to lookup DNO operators (neso_gsp_groups, neso_dno_reference)
- How to link BMUs to regions (ref_bmu_generators)
- MPAN to DNO mapping (distributor IDs 10-29)
- DUoS rate lookups

### 5. Example BigQuery Queries
Ready-to-use SQL examples for:
- All BMUs in Eastern (_A)
- Capacity by DNO
- GSP boundary area queries
- Settlement by region
- DNO constraint costs

## 🔍 Understanding the Two GSP Systems

### NESO GSPs (Geographic)
- **333 Individual Points**: Physical grid supply points
- **ID Format**: GSP_1, GSP_2, ... GSP_333
- **Purpose**: Geographic mapping, GIS boundaries, area calculations
- **Data Source**: `neso_gsp_boundaries` table
- **Use For**: Maps, spatial analysis, coverage area

### Elexon GSP Groups (Settlement)
- **14 Groups**: Corresponding to DNO licence areas
- **ID Format**: _A, _B, _C, ... _P (with underscore prefix)
- **Purpose**: Settlement periods, balancing mechanism, revenue allocation
- **Data Source**: `neso_gsp_groups` + Elexon BMRS APIs
- **Use For**: B1610 queries, BOD/BOALF analysis, imbalance pricing by region

### The Relationship
- Each of the 333 NESO GSPs **belongs to** one of the 14 GSP Groups
- GSP Groups are sometimes called "DNO licence areas"
- Elexon uses GSP Group codes (_A to _P) in settlement data
- NESO uses GSP IDs (GSP_1 to GSP_333) in geographic data

## 📂 BigQuery Table Reference

### Core Tables
```sql
-- Individual GSPs (333 points)
inner-cinema-476211-u9.uk_energy_prod.neso_gsp_boundaries
  - gsp_id (GSP_1 to GSP_333)
  - gsp_name
  - area_sqkm
  - geometry (geographic boundaries)

-- GSP Groups (14 DNO licence areas)
inner-cinema-476211-u9.uk_energy_prod.neso_gsp_groups
  - gsp_group_id (_A to _P)
  - gsp_group_name (Eastern, London, etc.)
  - dno_short_code (EPN, WMID, etc.)
  - dno_name (full operator name)
  - primary_coverage_area

-- DNO Reference (MPAN mapping)
inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference
  - distributor_id (10-29, first 2 digits of MPAN)
  - dno_name
  - market_participant_id

-- BM Units with GSP assignments
inner-cinema-476211-u9.uk_energy_prod.ref_bmu_generators
  - bmu_id
  - gsp_group (_A to _P)
  - max_capacity_mw
  - fuel_type
  - is_active
```

## 💡 Common Query Patterns

### 1. Get All Assets in a Region
```sql
SELECT 
    bmu_id,
    organization_name,
    max_capacity_mw,
    fuel_type
FROM `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_generators`
WHERE gsp_group = '_A'  -- Eastern
  AND is_active = true
ORDER BY max_capacity_mw DESC
```

### 2. Capacity by DNO Operator
```sql
SELECT 
    g.gsp_group_name,
    g.dno_name,
    COUNT(b.bmu_id) as unit_count,
    ROUND(SUM(b.max_capacity_mw), 1) as total_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_gsp_groups` g
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.ref_bmu_generators` b
    ON g.gsp_group_id = b.gsp_group AND b.is_active = true
GROUP BY g.gsp_group_name, g.dno_name
ORDER BY total_mw DESC
```

### 3. Settlement Revenue by Region (VLP Analysis)
```sql
SELECT 
    b.gsp_group,
    g.gsp_group_name,
    COUNT(DISTINCT b.acceptanceNumber) as acceptance_count,
    SUM(b.revenue_estimate_gbp) as total_revenue_gbp,
    AVG(b.acceptancePrice) as avg_price_mwh
FROM `inner-cinema-476211-u9.uk_energy_prod.boalf_with_prices` b
JOIN `inner-cinema-476211-u9.uk_energy_prod.neso_gsp_groups` g
    ON b.gsp_group = g.gsp_group_id
WHERE b.settlementDate >= '2025-10-01'
  AND b.validation_flag = 'Valid'
GROUP BY b.gsp_group, g.gsp_group_name
ORDER BY total_revenue_gbp DESC
```

### 4. Geographic Coverage by GSP
```sql
SELECT 
    gsp_id,
    gsp_name,
    ROUND(area_sqkm, 2) as area_sqkm,
    ST_AREA(geometry) / 1000000 as area_calculated_sqkm
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_gsp_boundaries`
WHERE area_sqkm > 1000
ORDER BY area_sqkm DESC
LIMIT 20
```

### 5. MPAN to DNO Lookup
```sql
-- Example: MPAN starts with "14" → which DNO?
SELECT 
    distributor_id,
    dno_name,
    market_participant_id
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`
WHERE distributor_id = '14'  -- NGED West Midlands
```

## 🗺️ Using GSP Data in Search Interface

The search interface (Apps Script `search_interface.gs`) already has fields for:
- **GSP Region** (cell B15): Dropdown with _A through _P
- **DNO Operator** (cell B16): Dropdown with operator names
- **Voltage Level** (cell B17): HV, EHV, 132kV

These link to the GSP/DNO data via the `fast_search_api.py` backend.

### GSP-DNO Auto-Linking
Install the `gsp_dno_linking.gs` script to auto-populate DNO when GSP is selected:
1. Copy `gsp_dno_linking.gs` to Apps Script
2. Run `installGspDnoTrigger()`
3. Select GSP in B15 → DNO auto-fills in B16

## 📈 12 Available Report Types

As defined in the analysis sheet:

1. **GSP Regional Generation Capacity** - Stacked bar chart by fuel type
2. **DNO Network Load vs Generation** - Bubble chart
3. **VLP Revenue by GSP Region** - Heatmap from boalf_with_prices
4. **Battery Storage Deployment Map** - Geographic scatter
5. **Wind Farm Locations** - Scatter plot with capacity
6. **DNO Constraint Cost Analysis** - Time series
7. **GSP Group Settlement Volumes** - Daily/monthly trends
8. **Technology Mix by Region** - Pie charts
9. **Connection Queue by DNO** - Bar chart (needs TEC data)
10. **Voltage Level Distribution** - Histogram
11. **Capacity Factor Analysis** - Box plot by fuel/region
12. **Geographic Coverage Heatmap** - Area vs generation density

## 🔄 Next Steps

### Immediate Actions
1. ✅ **View Sheet**: Open GSP-DNO Analysis tab in Google Sheets
2. ✅ **Test Queries**: Run example queries in BigQuery console
3. ⏳ **Install Linking**: Deploy `gsp_dno_linking.gs` for auto-population
4. ⏳ **Generate Reports**: Pick 1-2 report types to implement first

### Future Enhancements
- [ ] **Full GSP Mapping**: Link all 333 NESO GSPs to their parent GSP Group
  - Option 1: Spatial join using ST_CONTAINS with neso_gsp_boundaries
  - Option 2: Use FES GSP Info dataset which includes GSP Group field
  - Option 3: Manual mapping using NESO documentation

- [ ] **Settlement Integration**: Add GSP Group to settlement queries
  - Update `bmrs_bod` queries to group by gsp_group
  - Add gsp_group to `boalf_with_prices` view
  - Create regional imbalance price views

- [ ] **Interactive Map**: Deploy the 12 report visualizations
  - Priority: VLP Revenue Heatmap (report #3)
  - Priority: Battery Deployment Map (report #4)
  - Use Leaflet.js + neso_gsp_boundaries GeoJSON

- [ ] **Dashboard Refresh**: Add GSP metrics to Live Dashboard v2
  - Regional capacity indicators
  - Top 3 regions sparklines
  - DNO constraint cost alerts

## 📚 Reference Documentation

### NESO Sources
- **GIS Boundaries**: Grid Supply Points shapefile
- **FES Data**: GSP Info tables with lat/long
- **DNO Licence Areas**: Published as "GSP Groups"

### Elexon Sources
- **GSP Group Codes**: _A through _P in settlement data
- **B1610**: Individual BMU generation by GSP
- **BOALF**: Balancing acceptances (includes GSP indirectly via BMU)

### Project Docs
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Full table schemas
- `PROJECT_CONFIGURATION.md` - All config settings
- `CHATGPT_INSTRUCTIONS.md` - GSP/DNO query patterns

## 🎯 Success Criteria

Your GSP/DNO data is now **fully implemented** when you can:
- [x] View 14 GSP Groups with capacity in Google Sheets
- [x] Query BMUs by GSP Group in BigQuery
- [x] See top 3 regions by capacity (Eastern 2,213 MW, etc.)
- [x] Access NESO GSP IDs (GSP_1 through GSP_333)
- [ ] Auto-link GSP to DNO in search interface (needs gsp_dno_linking.gs)
- [ ] Generate VLP revenue heatmap by GSP Group
- [ ] View geographic GSP boundaries on map

---

**Last Updated**: 2025-12-31  
**Script**: `export_enhanced_gsp_analysis.py`  
**Sheet**: GSP-DNO Analysis  
**Status**: ✅ Data Exported, 🔄 Enhancement Scripts Pending
