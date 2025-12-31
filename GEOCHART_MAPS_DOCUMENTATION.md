# Google Sheets Geo Chart Maps - Implementation Guide

**Date**: December 29, 2025
**Project**: GB Power Market JJ - UK Energy Visualization Platform
**Status**: ⚠️ Partial Implementation - Zoom Issue Outstanding

---

## 🎯 Objective

Create Google Sheets-based geo-visualizations of UK energy market data using **UK postcodes** for unambiguous geographic identification. Two primary maps implemented:

1. **Constraint Costs Map** - Shows balancing mechanism constraint locations
2. **DNO Boundaries Map** - Shows Distribution Network Operator coverage areas

---

## 📊 Implementation Summary

### **Map 1: Constraint Costs by Postcode**

**Purpose**: Visualize where grid constraints occur across GB
**Data Source**: `bmrs_boalf_iris` (balancing acceptances) joined with `sva_generators_with_coords`
**Coverage**: Last 7 days of constraint data
**Postcode Areas**: 4 regions identified

**Key Findings**:
- **SR7** (Sunderland): 1,653 MW, 186 acceptances
- **BL6** (Bolton): 1,062 MW, 22 acceptances
- **PA7** (Paisley): 209 MW, 32 acceptances
- **LA13** (Barrow-in-Furness): 167 MW, 87 acceptances

**Files Created**:
- `add_geochart_postcodes.py` - Data extraction and formatting
- `geochart_postcodes_apps_script.gs` - Automatic chart generation
- Google Sheet: "Constraint Geo Map" tab

---

### **Map 2: DNO Boundaries by Postcode**

**Purpose**: Show Distribution Network Operator coverage areas via generation capacity
**Data Source**: `sva_generators_with_coords` (7,072 operational generators)
**Postcode Areas**: 2,491 unique postcode districts

**Top DNOs by Capacity**:

| DNO | Postcodes | Capacity (MW) | Generators |
|-----|-----------|--------------|------------|
| Eastern Power Networks (EPN) | 273 | 23,587 | 814 |
| National Grid (East Midlands) | 183 | 20,198 | 767 |
| Northern Powergrid (Yorkshire) | 222 | 19,614 | 580 |
| Scottish Hydro Electric | 197 | 19,444 | 709 |
| Southern Electric | 221 | 18,409 | 702 |

**Files Created**:
- `add_dno_boundaries_geochart.py` - Data extraction (2,491 rows)
- `dno_boundaries_apps_script.gs` - Multi-color DNO visualization
- Google Sheet: "DNO Boundaries Map" tab

---

## 🔧 Technical Approach

### **Why Postcodes?**

**Problem Solved**: Generic region names like "Eastern" or "Scotland" cause ambiguity in Google Geo Charts - they can match regions in other countries (e.g., "Scotland" could show Eastern Europe).

**Solution**: UK postcodes are **globally unique**. Format: `"AB12, UK"` ensures Google recognizes location as United Kingdom.

### **Data Pipeline**

```sql
-- Postcode Extraction Query
WITH postcode_districts AS (
  SELECT
    -- Extract first part of postcode (e.g., "SR7" from "SR7 9QH")
    SPLIT(postcode, ' ')[OFFSET(0)] as postcode_district,
    dno,
    gsp,
    lat,
    lng,
    capacity_mw
  FROM sva_generators_with_coords
  WHERE postcode IS NOT NULL
)
SELECT
  CONCAT(postcode_district, ', UK') as location,  -- UK suffix for Google
  SUM(capacity_mw) as value,
  dno as category
FROM postcode_districts
GROUP BY postcode_district, dno
```

### **Color Coding Strategy**

**Constraint Map**: White → Red gradient (intensity = constraint volume)

**DNO Map**: 14 unique colors for boundary identification
- Each DNO assigned a distinct color
- Color codes: `#FF6B6B` (red), `#4ECDC4` (teal), `#45B7D1` (blue), etc.
- Numeric mapping: DNO name → 1-14 → Color array index

---

## ⚠️ Known Issues

### **Critical: Zoom Level Problem**

**Issue**: Google Geo Charts display **world map view** instead of zoomed UK view

**Attempted Solutions** (All Failed):
1. ❌ `.setOption('region', 'GB')` - Shows world with GB highlight
2. ❌ `.setOption('region', '826')` - ISO numeric code (causes "Bja" error in Apps Script)
3. ❌ `.setOption('magnifyingGlass', {zoomFactor: 7.5})` - No effect
4. ❌ Removing region option entirely - Still shows world view
5. ❌ `displayMode: 'regions'` - Doesn't recognize DNO names as valid regions

**Root Cause**: Google Geo Charts API (via Apps Script) has limited zoom control compared to manual UI creation. Postcodes scattered across UK don't trigger auto-zoom to GB bounding box.

**Current Workaround**:
- Manual chart creation in Google Sheets UI allows zoom control
- OR use Leaflet HTML maps (already working in `btm_constraint_map.html`)

---

## 📁 File Structure

```
GB-Power-Market-JJ/
├── add_geochart_postcodes.py              # Constraint map data prep
├── add_dno_boundaries_geochart.py         # DNO map data prep (2,491 rows)
├── geochart_postcodes_apps_script.gs      # Constraint chart automation
├── dno_boundaries_apps_script.gs          # DNO chart automation (14 colors)
├── geochart_apps_script.gs                # Original (deprecated - region name issues)
│
├── btm_constraint_map.html                # ✅ Working Leaflet map (6.2 KB)
├── btm_map_button.gs                      # Apps Script button trigger
│
└── Google Sheets Tabs:
    ├── Constraint Geo Map                 # 4 postcode areas + instructions
    └── DNO Boundaries Map                 # 2,491 postcode areas + 14 DNO legend
```

---

## 🚀 Installation Steps

### **Method 1: Apps Script (Automated)**

1. Open Google Sheets Dashboard: https://docs.google.com/spreadsheets/d/1-u794iGngn5_Ql_XocKSwvHSKWABWO0bVsudkUJAFqA
2. Extensions → Apps Script
3. **For Constraint Map**:
   - Create file: `ConstraintGeoChart.gs`
   - Paste code from `geochart_postcodes_apps_script.gs`
   - Run: `createConstraintGeoChart()`
4. **For DNO Map**:
   - Create file: `DnoBoundaries.gs`
   - Paste code from `dno_boundaries_apps_script.gs`
   - Run: `createDnoBoundariesChart()`
5. Custom menu appears: 🗺️ Constraint Maps / 🗺️ DNO Maps

### **Method 2: Manual Chart Creation (Better Zoom Control)**

1. Navigate to "Constraint Geo Map" or "DNO Boundaries Map" sheet
2. Select cells **A1:B[lastRow]** (postcode + value columns)
3. Insert → Chart
4. Chart type: Geo chart
5. **Manually adjust zoom** in chart editor → Region settings
6. Customize → Color axis: White to Red gradient

### **Method 3: Use Existing Leaflet Map (Recommended)**

The Leaflet HTML map (`btm_constraint_map.html`) already provides proper zoom and interactivity:
- ✅ Auto-zooms to UK
- ✅ Interactive tooltips
- ✅ Color-coded regions
- ✅ 4.5 MB with full GeoJSON data

Access via Apps Script menu: 🗺️ Maps → View BTM Constraint Map

---

## 🔍 Data Quality Notes

### **Postcode Coverage**

- **Total SVA Generators**: 7,072 operational sites
- **With Valid Postcodes**: 7,072 (100%)
- **Unique Postcode Districts**: 2,491 (e.g., "SR7", "BL6")
- **Geographic Spread**: All 14 DNO regions covered

### **Constraint Data Limitations**

- **Join Method**: BMU name matching between `ref_bmu_canonical` and `sva_generators_with_coords`
- **Match Rate**: Only 4 postcode areas found in last 7 days (low constraint period)
- **Missing Data**: Most BMUs lack postcode coordinates (not SVA generators)
- **Solution**: Need to geocode BMU locations separately or use GSP group approximations

### **DNO Name Standardization**

DNO names in data don't match Google's expected format:
- Data: `"Eastern Power Networks (EPN)"`
- Google: Doesn't recognize as valid region
- Solution: Use numeric color coding (1-14) instead of region names

---

## 📈 Usage Patterns

### **Constraint Analysis**

```javascript
// Filter DNO Boundaries Map by constraint-heavy regions
=FILTER('DNO Boundaries Map'!A:H,
        'DNO Boundaries Map'!A:A = "SR7, UK")

// Result: Sunderland area with 1,653 MW constraints
```

### **DNO Coverage Comparison**

```javascript
// Aggregate capacity by DNO
=QUERY('DNO Boundaries Map'!A:H,
       "SELECT D, SUM(B) GROUP BY D ORDER BY SUM(B) DESC")

// Creates ranking: EPN (23.6 GW) > NGED East (20.2 GW) > NPg Yorkshire (19.6 GW)
```

---

## 🛠️ Future Enhancements

### **Short-Term Fixes**

1. **Geocode All BMUs**: Add postcode/lat-lng to `ref_bmu_canonical` for all 5,541 BMUs
   - Currently only SVA generators have coordinates
   - Need National Grid transmission-connected sites
   - Estimated 200+ manual lookups required

2. **Alternative Visualization**: Use Google Maps JavaScript API instead of Geo Charts
   - Full zoom/pan control
   - Custom marker clustering
   - Real-time data updates

3. **GSP Group Polygons**: Create GeoJSON boundaries for 13 GSP groups
   - More accurate than postcode approximation
   - Can overlay on Leaflet map
   - Source: National Grid ESO boundaries

### **Long-Term Roadmap**

4. **Real-Time Updates**: Webhook from BigQuery → Google Sheets API
   - Auto-refresh maps every 15 minutes
   - Trigger on new BOALF data in `bmrs_boalf_iris`

5. **Constraint Forecasting**: Overlay NESO day-ahead constraint predictions
   - Compare forecast vs actual
   - Alert when major constraints expected

6. **Interactive Filtering**: Apps Script UI with dropdowns
   - Filter by: DNO, Date range, Constraint type, Capacity threshold
   - Dynamic map regeneration

---

## 🔗 Related Documentation

- `PROJECT_CONFIGURATION.md` - BigQuery setup and credentials
- `STOP_DATA_ARCHITECTURE_REFERENCE.md` - Table schemas
- `APPS_SCRIPT_INTEGRATED.md` - Dashboard automation guide
- `btm_constraint_map.html` - Working Leaflet map implementation

---

## 📞 Support

**Issue**: Geo Chart zoom not working
**Workaround**: Use manual chart creation (Method 2) or Leaflet map (Method 3)

**Data Questions**: All data remains in BigQuery - Sheets is visualization layer only
- `sva_generators_with_coords`: 7,072 rows
- `bmrs_boalf_iris`: Real-time constraint acceptances
- `ref_bmu_canonical`: 5,541 BMU reference records

---

## ✅ Completion Status

| Task | Status | Notes |
|------|--------|-------|
| Postcode data extraction | ✅ | 2,491 areas, 100% coverage |
| Constraint map data | ✅ | 4 areas (last 7 days) |
| DNO boundaries data | ✅ | All 14 DNOs mapped |
| Apps Script automation | ⚠️ | Works but zoom issue |
| Google Sheets tabs created | ✅ | Both tabs populated |
| Color coding system | ✅ | 14 unique DNO colors |
| Leaflet HTML fallback | ✅ | Already working |
| **Geo Chart zoom fix** | ❌ | **Outstanding Issue** |

---

**Last Updated**: December 29, 2025, 23:45 GMT
**Author**: GitHub Copilot + George Major
**Repository**: https://github.com/GeorgeDoors888/GB-Power-Market-JJ
