# GB Power System Complete Map - Documentation

**Created**: 2 November 2025  
**Status**: ✅ Production Ready  
**File**: `gb_power_complete_map.html`

---

## Overview

The **GB Power System Complete Map** is a comprehensive interactive visualization showing the entire GB electricity system in one view. It combines real-time operational data with geographic infrastructure data.

## 📊 What's Included

### 1. DNO Boundaries (14 regions)
- **Source**: `dno_regions.geojson` (local file)
- **Display**: Green polygon boundaries
- **Coverage**: All Distribution Network Operator license areas across GB
- **Regions Include**:
  - Scottish Power Networks
  - Northern Powergrid (Yorkshire & Northeast)
  - Electricity North West
  - Western Power Distribution (East Midlands, West Midlands, South Wales, South West)
  - UK Power Networks (Eastern, London, South Eastern)
  - Scottish & Southern Energy Networks

**Click on any DNO region** to see:
- DNO name
- Area code
- Long name/description

---

### 2. GSP Flow Points (18 Grid Supply Points)
- **Source**: `bmrs_indgen` + `bmrs_inddem` tables (BigQuery)
- **Update Frequency**: Every 30 minutes (48 settlement periods/day)
- **Latest Data**: 30 October 2025, Settlement Period 48

#### GSP Codes & Locations:
| Code | Name | Type | Net Flow |
|------|------|------|----------|
| N | National Grid | Coordination | Varies |
| B1 | Barking | London | Net exporter |
| B2 | Ealing | London | Net exporter |
| B3 | Wimbledon | London | Net exporter |
| B4 | Brixton | London | Net exporter |
| B5 | City Road | London | Net exporter |
| B6 | Willesden | London | Net exporter |
| B7 | Hurst | Berkshire | Net exporter |
| B8 | Sundon | Bedfordshire | Net exporter |
| B9 | Pelham | Hertfordshire | Net exporter |
| B10 | Bramley | Hampshire | Net importer |
| B11 | Melksham | Wiltshire | Net exporter |
| B12 | Exeter | Devon | Net importer |
| B13 | Bristol | Bristol | Net importer |
| B14 | Indian Queens | Cornwall | Net importer |
| B15 | Landulph | Cornwall | Net exporter |
| B16 | Pembroke | South Wales | Net exporter |
| B17 | Swansea North | South Wales | Net importer |

#### Visual Encoding:
- 🟦 **Blue circles** = Net EXPORTERS (Generation > Demand)
- 🟧 **Orange circles** = Net IMPORTERS (Demand > Generation)
- **Circle size** = Magnitude of net flow (larger = more MW)

**Current Status** (30 Oct 2025, SP48):
- **12 Exporters** producing surplus power
- **6 Importers** consuming more than they generate

**Click on any GSP circle** to see:
- Generation (MW)
- Demand (MW)
- Net Flow (MW) with +/- indicator
- Export/Import status

---

### 3. Offshore Wind Farms (35 sites, 14,267 MW)
- **Source**: `offshore_wind_farms` table (BigQuery)
- **Status**: All operational
- **Display**: Cyan circles in offshore locations
- **Total Capacity**: 14.3 GW

#### Largest Offshore Wind Farms:
1. **Hornsea Two** - 1,386 MW (Yorkshire East)
2. **Hornsea One** - 1,218 MW (Yorkshire East)
3. **Moray East** - 950 MW (Scotland North)
4. **Moray West** - 882 MW (Scotland North)
5. **Triton Knoll** - 857 MW (Yorkshire East)
6. **East Anglia One** - 714 MW (East Anglia)
7. **Walney Extension** - 659 MW (North Wales)
8. **London Array** - 630 MW (East Anglia)

#### Geographic Distribution:
- **East Coast** (Yorkshire, East Anglia): ~6,500 MW
- **North Wales / Irish Sea**: ~3,200 MW
- **Scotland**: ~2,800 MW
- **South Coast**: ~400 MW

**Click on any offshore wind farm** to see:
- Name
- Capacity (MW)
- Type: Offshore Wind
- GSP Zone assignment
- GSP Region

---

### 4. CVA Power Plants (1,581 sites)
- **Source**: `cva_plants` table (BigQuery)
- **Definition**: Central Volume Allocation - Large generators >100MW
- **Connection**: Transmission network (132kV+)
- **Display**: Colored markers (clustered at low zoom)

#### Fuel Type Distribution:
- Gas/CCGT (red markers)
- Nuclear (purple markers)
- Coal (brown markers)
- Wind (blue markers)
- Hydro (light blue markers)
- Biomass (green markers)
- Solar (orange markers)

**Click on any CVA plant** to see:
- Plant name
- Type: CVA
- Fuel type
- Status

---

### 5. SVA Generators (7,072 sites)
- **Source**: `sva_generators_with_coords` table (BigQuery)
- **Definition**: Supplier Volume Allocation - Small generators <100MW
- **Connection**: Distribution network (11kV - 132kV)
- **Display**: Colored markers (clustered at low zoom)

#### Generator Types:
- **Solar PV** (orange) - Largest category
- **Onshore Wind** (blue) - Second largest
- **Gas/Diesel** (red)
- **Biomass/Biogas** (green)
- **Hydro** (light blue)
- **Battery Storage** (purple)

**Click on any SVA generator** to see:
- Generator name
- Type: SVA
- Fuel type
- Capacity (MW)
- DNO region assignment

---

## 🎮 Interactive Controls

### Layer Toggle Panel (Top Left)
Located at top-left corner with checkboxes to show/hide:

- ☑️ **DNO Boundaries (14)** - Green polygons
- ☑️ **GSP Flow (18)** - Blue/orange circles
- ☑️ **Offshore Wind (35)** - Cyan circles
- ☑️ **CVA Plants (1,581)** - Clustered markers
- ☑️ **SVA Generators (7,072)** - Clustered markers

**All layers enabled by default** - uncheck to hide

### Statistics Display
Real-time counts shown in control panel:
- Exporters: 12 GSPs
- Importers: 6 GSPs
- Offshore: 14,267 MW
- Total Generators: 8,653
- CVA: 1,581 | SVA: 7,072

### Legend (Bottom Right)
Color coding reference:
- **GSP Flow**: Blue (exporter) / Orange (importer)
- **Wind**: Cyan (offshore) / Blue (onshore)
- **Solar**: Orange
- **Gas/Fossil**: Red
- **Biomass**: Green
- **Nuclear**: Purple
- **Other**: Gray

### Map Navigation
- **Zoom**: Mouse wheel or +/- buttons
- **Pan**: Click and drag
- **Clustering**: Markers automatically cluster/expand based on zoom level
- **Popups**: Click any element for details

---

## 📁 File Structure

### Generated Output
```
gb_power_complete_map.html (214 KB)
└── Standalone HTML file with embedded data
```

### Source Files
```
create_complete_gb_power_map.py      # Generator script
├── Queries BigQuery for live data
├── Loads dno_regions.geojson
└── Generates HTML with Leaflet.js

dno_regions.geojson                  # DNO boundary polygons
├── 14 features (regions)
└── GeoJSON format with properties
```

### Dependencies (Loaded from CDN)
- **Leaflet.js** 1.9.4 - Mapping library
- **Leaflet.markercluster** 1.5.3 - Marker clustering
- **CartoDB Dark Matter** tiles - Base map

---

## 🔄 Data Sources & Updates

### BigQuery Tables

#### 1. `bmrs_indgen` - GSP Generation Data
- **Source**: Elexon BMRS API
- **Update**: Every 30 minutes
- **Fields**: boundary, generation, settlementDate, settlementPeriod
- **Purpose**: Calculate generation at each GSP

#### 2. `bmrs_inddem` - GSP Demand Data
- **Source**: Elexon BMRS API
- **Update**: Every 30 minutes
- **Fields**: boundary, demand, settlementDate, settlementPeriod
- **Purpose**: Calculate demand at each GSP
- **Note**: Demand stored as negative values

#### 3. `offshore_wind_farms` - Offshore Wind Database
- **Source**: Wikipedia UK offshore wind list
- **Status**: Static (updated manually)
- **Fields**: name, capacity_mw, latitude, longitude, gsp_zone, gsp_region
- **Count**: 35 operational sites

#### 4. `sva_generators_with_coords` - Small Generators
- **Source**: NESO All_Generators.xlsx → generators.json
- **Status**: Static (updated quarterly)
- **Fields**: name, lat, lng, capacity_mw, fuel_type, dno, gsp
- **Count**: 7,072 generators
- **Coverage**: 100% with coordinates

#### 5. `cva_plants` - Large Power Stations
- **Source**: electricityproduction.uk (scraped/geocoded)
- **Status**: Static (updated manually)
- **Fields**: plant_id, name, lat, lng, fuel_type, status
- **Count**: 1,581 plants
- **Coverage**: 100% with coordinates

### Local Files

#### `dno_regions.geojson`
- **Source**: NESO official DNO boundaries (coordinate transformed)
- **Format**: GeoJSON with EPSG:4326 (WGS84)
- **Size**: ~500 KB
- **Regions**: 14 DNO license areas

---

## 🚀 How to Regenerate

### Prerequisites
```bash
# Python 3.10+
# BigQuery access to inner-cinema-476211-u9
# Local file: dno_regions.geojson
```

### Command
```bash
cd "/Users/georgemajor/GB Power Market JJ"
python3 create_complete_gb_power_map.py
```

### Output
```
🔍 Step 1: Loading DNO boundaries from GeoJSON...
✅ Loaded 14 DNO regions

🔍 Step 2: Querying latest GSP flow data...
✅ Found 18 GSPs (12 exporters, 6 importers)

🔍 Step 3: Querying offshore wind farms...
✅ Found 35 offshore wind farms (14,267 MW)

🔍 Step 4: Querying power stations...
✅ Found 8653 generators (1581 CVA, 7072 SVA)

✅ Complete map created: gb_power_complete_map.html
```

### Open Map
```bash
open gb_power_complete_map.html
```

---

## 🎯 Use Cases

### 1. Grid Operations
- Monitor GSP-level flows to identify congestion
- See which regions are exporting vs importing
- Track offshore wind generation locations
- Identify distribution network boundaries

### 2. Trading & Market Analysis
- Understand regional generation vs demand balance
- Identify price arbitrage opportunities between GSPs
- Locate generation capacity by fuel type
- Analyze renewable penetration by region

### 3. Infrastructure Planning
- Where to build new generation capacity
- Identify grid reinforcement needs
- DNO capacity planning
- Renewable energy site selection

### 4. Research & Analysis
- Geographic distribution of generation assets
- DNO coverage and overlaps
- GSP flow patterns over time
- Renewable energy deployment tracking

---

## 🔧 Technical Details

### Performance Optimizations
1. **Marker Clustering**: 8,653 generators cluster at low zoom → expand on zoom
2. **Max Cluster Radius**: CVA = 50px, SVA = 30px (prevents overlap)
3. **Lazy Loading**: Layers only render when toggled on
4. **GeoJSON Simplification**: DNO boundaries optimized for web display

### Browser Compatibility
- ✅ Chrome/Edge (Chromium) - Recommended
- ✅ Firefox
- ✅ Safari
- ❌ IE11 (not supported)

### Map Projections
- **Base Map**: EPSG:3857 (Web Mercator)
- **Data**: EPSG:4326 (WGS84) - auto-converted by Leaflet

### Data Volume
- **DNO GeoJSON**: ~500 KB
- **GSP Data**: 18 points
- **Offshore Wind**: 35 points
- **Generators**: 8,653 points (clustered)
- **Total HTML**: 214 KB (with embedded data)

---

## 📈 Future Enhancements

### Potential Additions
- [ ] Real-time auto-refresh (every 30 mins when new settlement period available)
- [ ] Historical GSP flow playback (animate through settlement periods)
- [ ] Heat map overlay showing price by region
- [ ] Wind speed/direction overlay
- [ ] Transmission line network
- [ ] Substations and switching stations
- [ ] Battery storage sites (separate layer)
- [ ] Demand centers/population density
- [ ] Solar irradiance overlay
- [ ] Carbon intensity by region

### Data Improvements
- [ ] Add CVA capacity data from BMRS
- [ ] Link CVA plants to BMU IDs
- [ ] Add operational status (online/offline)
- [ ] Real-time generation data per plant (where available)
- [ ] Fuel mix breakdown by DNO region
- [ ] Import/export trends over 24 hours

### UI Enhancements
- [ ] Date/time picker for historical data
- [ ] Search box to find specific generators
- [ ] Filter by fuel type
- [ ] Filter by capacity range
- [ ] Export view as image/PDF
- [ ] Share link with specific view/layers
- [ ] Mobile-responsive design

---

## 🐛 Known Issues & Limitations

### Data Limitations
1. **CVA Capacity Missing**: `cva_plants` table doesn't include capacity_mw field
   - Solution: Query BMRS API for registered capacity
   
2. **GSP Flow Data Lag**: 2-5 minutes behind real-time
   - Inherent to BMRS publication schedule
   
3. **Static Generator List**: SVA/CVA data not updated daily
   - Updated quarterly from NESO source
   
4. **No Scotland GSPs**: Scotland has different GSP structure (not B-coded)
   - National Grid 'N' aggregates Scottish flows

### UI Limitations
1. **Clustering can hide detail**: Must zoom in to see individual sites
2. **Large data volume**: 8,653 markers can slow older browsers
3. **No mobile optimization**: Best viewed on desktop/laptop
4. **Fixed color scheme**: Dark theme only

### Technical Constraints
1. **Single snapshot**: Shows one settlement period at a time
2. **No live updates**: Must refresh page for new data
3. **Browser-only**: No backend API or database
4. **Static HTML**: Can't save user preferences

---

## 📚 Related Documentation

### Data Sources
- `GSP_FLOW_DOCUMENTATION.md` - Detailed GSP flow explanation
- `README.md` - Main project documentation
- `BIGQUERY_COMPLETE.md` - BigQuery tables reference

### Other Maps
- `dno_energy_map_advanced.html` - DNO-focused map with energy overlay
- `gb_generators_map.html` - Generator-only map (SVA focus)
- `gsp_flow_accurate.html` - GSP-only flow visualization

### Scripts
- `create_gsp_flow_map.py` - GSP flow only
- `create_generators_map.py` - Generators only
- `create_dno_maps_advanced.py` - DNO boundaries with data

---

## 🔐 Security & Access

### API Keys
- **Not required** - Uses open CartoDB tiles
- No Google Maps API key needed
- No authentication for viewing HTML

### Data Access
- BigQuery: Requires project access to `inner-cinema-476211-u9`
- GeoJSON: Public file, no restrictions
- Generated HTML: Can be shared publicly (data snapshot)

---

## ✅ Validation Checklist

Before using the map, verify:

- [x] All 5 layers load successfully
- [x] GSP circles show correct colors (blue/orange)
- [x] DNO boundaries display as green polygons
- [x] Offshore wind farms appear in coastal waters
- [x] Generators cluster and expand on zoom
- [x] All popups show correct information
- [x] Layer toggles work properly
- [x] Statistics panel shows correct counts
- [x] Legend matches map colors
- [x] No console errors in browser

---

## 📞 Support & Contact

### Questions?
- Check existing `.md` documentation files
- Review BigQuery table schemas
- Examine source Python scripts

### Issues?
- Verify BigQuery access
- Check `dno_regions.geojson` exists
- Ensure Python dependencies installed
- Try regenerating from scratch

---

## 📝 Version History

### v1.0 (2 November 2025)
- ✅ Initial complete map release
- ✅ All 5 layers functional
- ✅ 8,653 total generators included
- ✅ Fixed emoji encoding issues
- ✅ Clustering optimized
- ✅ Interactive controls working

---

## 🎉 Summary

**The GB Power Complete Map** is now production-ready with:
- ✅ 14 DNO boundary regions
- ✅ 18 GSP flow points (live data)
- ✅ 35 offshore wind farms (14.3 GW)
- ✅ 8,653 power stations (CVA + SVA)
- ✅ Full interactivity with toggle controls
- ✅ Clean, professional visualization
- ✅ Comprehensive documentation

**Ready for ongoing use and enhancement!** 🚀

---

**Last Updated**: 2 November 2025  
**Status**: ✅ Complete and Locked Down  
**Next Steps**: Use as reference for further analysis and development
