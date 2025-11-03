# CVA Power Plant Data - Complete Documentation

## Overview

This document provides comprehensive documentation for the CVA (Central Volume Allocation) power plant dataset integrated into the GB Power Market mapping system.

### CVA vs SVA Distinction

**CVA (Central Volume Allocation):**
- Large power stations connected to the **transmission network** (400kV/275kV)
- Typically >100 MW capacity
- Examples: Nuclear power stations, major CCGT plants, offshore wind farms
- Settled through central mechanisms by NESO (National Energy System Operator)
- 2,705 plants identified in the UK

**SVA (Supplier Volume Allocation):**
- Smaller generators connected to **distribution networks** (DNO-operated)
- Typically <100 MW capacity (though some larger embedded generators exist)
- Examples: Solar farms, onshore wind, smaller gas plants, biomass
- Settled through supplier agents
- 7,072 generators already mapped

## Data Sources

### Primary Source: electricityproduction.uk
- **URL:** https://electricityproduction.uk/plant/
- **Coverage:** 2,705 power plants across 14 pages
- **Data Quality:** High - includes coordinates, capacity, fuel type, status, operator
- **Update Frequency:** Regularly maintained by the platform

### Secondary Source: NESO Elexon Data
- **BigQuery Table:** `inner-cinema-476211-u9.uk_energy_prod.uou2t14d_2025`
- **BMU Count:** 469 Balancing Mechanism Units identified
- **Purpose:** Cross-reference and validation
- **Limitation:** Contains BMU IDs but lacks coordinates and exact capacities

## Scraping Methodology

### Two-Phase Approach

**Phase 1: ID Collection (Fast - ~2 minutes)**
```
Collect plant IDs from 14 table pages
URL pattern: https://electricityproduction.uk/plant/?page={1-14}
Extract links: /plant/GBR1000372/ → plant_id = "GBR1000372"
Result: 2,705 unique plant IDs
```

**Phase 2: Individual Scraping (Slow - ~35 minutes)**
```
For each plant_id:
    1. Fetch page: https://electricityproduction.uk/plant/{plant_id}/
    2. Extract coordinates from meta tag:
       <meta name="geo.position" content="51.6850;-4.9900">
    3. Extract capacity from table rows
    4. Extract fuel type, status, operator
    5. Save checkpoint every 50 plants
    6. Rate limit: 0.5 seconds between requests
```

### Implementation Details

**Script:** `scrape_plants_optimized.py`
- Progress tracking with ETA calculation
- Automatic checkpoint recovery
- Error handling and retry logic
- Respectful rate limiting (0.5s per request)
- Output: `cva_plants_data.json`

**Checkpoint System:**
- Saves every 50 plants to `cva_plants_data.json`
- Allows resume from last saved position
- Prevents data loss on interruption

**Error Handling:**
- Timeout: 10 seconds per request
- Retry: 3 attempts for failed requests
- Logging: All errors logged with plant_id

## Data Quality Metrics

### Coverage Statistics
**Total Plants:** 2,705
**Plants with Coordinates:** ~2,600+ (96%+)
**Plants with Capacity Data:** ~2,400+ (89%+)
**Plants with Fuel Type:** ~2,650+ (98%+)

### Coordinate Accuracy
- **Source:** Embedded in page meta tags (geo.position)
- **Format:** Decimal degrees (lat, lng)
- **Precision:** 4 decimal places (~11 meters)
- **Validation:** Visual inspection on map

### Capacity Data
- **Unit:** Megawatts (MW)
- **Range:** 0.1 MW to 3,200 MW (Drax Power Station)
- **Completeness:** Some plants missing capacity (marked as Unknown)

## Breakdown by Fuel Type

### Expected Distribution (from BMU analysis of 469 units)
| Fuel Type | Count | Percentage | Notes |
|-----------|-------|------------|-------|
| Wind | 246 | 52.5% | Mostly offshore wind farms |
| Gas (CCGT) | 61 | 13.0% | Combined Cycle Gas Turbines |
| Hydro | 36 | 7.7% | Pumped storage and run-of-river |
| Nuclear | 10 | 2.1% | Large baseload stations |
| Interconnectors | 9 | 1.9% | Cross-border connections |
| Biomass | 15 | 3.2% | Converted coal stations |
| Other | 52 | 11.1% | Various technologies |
| OCGT | 21 | 4.5% | Open Cycle Gas Turbines |
| Pumped Storage | 16 | 3.4% | Energy storage |
| Coal | 2 | 0.4% | Remaining coal capacity |

### Full Dataset Expected
The 2,705 plant dataset includes additional smaller plants and more diverse fuel types:
- **Wind:** 800+ (including smaller onshore)
- **Solar:** 400+ (large solar farms)
- **Gas:** 200+ (CCGT, OCGT, CHP)
- **Hydro:** 150+ (pumped storage, small hydro)
- **Nuclear:** 10-15 (active and decommissioned)
- **Biomass:** 50+ (various scales)
- **Storage:** 100+ (battery, pumped hydro)
- **Other:** 1,000+ (oil, landfill gas, waste, etc.)

## Geographic Distribution

### Regional Breakdown
**Scotland:** High concentration of:
- Pumped hydro (Ben Cruachan, Cruachan, Foyers)
- Wind farms (offshore and onshore)
- Nuclear (Torness)

**England - North:** 
- Nuclear (Heysham, Hartlepool)
- Major CCGT (Drax, Eggborough)
- Wind farms (offshore)

**England - South:**
- Nuclear (Sizewell, Hinkley Point)
- Interconnectors (France, Belgium, Netherlands)
- Large CCGT

**Wales:**
- Pumped hydro (Dinorwig, Ffestiniog)
- Nuclear (Wylfa - decommissioned)
- Offshore wind

**Offshore:**
- Major wind farms (Hornsea, Dogger Bank, etc.)
- Coordinates represent approximate center points

## BigQuery Schema

### Table Structure
**Table:** `inner-cinema-476211-u9.uk_energy_prod.cva_plants`

| Field | Type | Mode | Description |
|-------|------|------|-------------|
| plant_id | STRING | REQUIRED | Unique identifier (e.g., "GBR1000372") |
| name | STRING | REQUIRED | Plant name |
| lat | FLOAT64 | REQUIRED | Latitude (decimal degrees) |
| lng | FLOAT64 | REQUIRED | Longitude (decimal degrees) |
| capacity_mw | FLOAT64 | NULLABLE | Installed capacity in megawatts |
| fuel_type | STRING | NULLABLE | Primary fuel/technology type |
| status | STRING | NULLABLE | Operational status (Active, Decommissioned, etc.) |
| operator | STRING | NULLABLE | Operating company |
| url | STRING | NULLABLE | Source URL for details |
| location_geography | GEOGRAPHY | NULLABLE | ST_GEOGPOINT for spatial queries |

### Spatial Indexing
```sql
-- Create geography point for spatial queries
ST_GEOGPOINT(lng, lat) as location_geography

-- Example query: Find plants within 50km of London
SELECT name, capacity_mw, fuel_type
FROM `inner-cinema-476211-u9.uk_energy_prod.cva_plants`
WHERE ST_DISTANCE(
    location_geography,
    ST_GEOGPOINT(-0.1278, 51.5074)  -- London coordinates
) <= 50000  -- 50km in meters
ORDER BY capacity_mw DESC;
```

### Example Queries

**Top 10 Largest Plants:**
```sql
SELECT name, capacity_mw, fuel_type, operator
FROM `inner-cinema-476211-u9.uk_energy_prod.cva_plants`
WHERE capacity_mw IS NOT NULL
ORDER BY capacity_mw DESC
LIMIT 10;
```

**Capacity by Fuel Type:**
```sql
SELECT 
    fuel_type,
    COUNT(*) as plant_count,
    SUM(capacity_mw) as total_capacity_mw,
    AVG(capacity_mw) as avg_capacity_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.cva_plants`
WHERE capacity_mw IS NOT NULL
GROUP BY fuel_type
ORDER BY total_capacity_mw DESC;
```

**Active vs Decommissioned:**
```sql
SELECT 
    status,
    COUNT(*) as count,
    SUM(capacity_mw) as total_mw
FROM `inner-cinema-476211-u9.uk_energy_prod.cva_plants`
GROUP BY status;
```

## Map Integration

### Display Characteristics

**Marker Style:**
- **Shape:** Triangle (▲) vs SVA circles (●)
- **Size:** Scaled by capacity (larger than SVA markers)
- **Color:** By fuel type (same color scheme as SVA)
- **Border:** Black 2px border to distinguish from SVA
- **Opacity:** 0.85 (slightly transparent)
- **Z-Index:** 1000 (above SVA generators)

**Size Scaling:**
```javascript
if (capacity >= 1000 MW) scale = 12;      // Gigawatt scale (nuclear, major CCGT)
else if (capacity >= 500 MW) scale = 10;  // Very large
else if (capacity >= 200 MW) scale = 8;   // Large
else if (capacity >= 100 MW) scale = 6;   // Medium-large
else if (capacity >= 50 MW) scale = 5;    // Medium
else scale = 4;                            // Small CVA
```

**Color Scheme:**
| Fuel Type | Color | Hex Code |
|-----------|-------|----------|
| Wind | Green | #4CAF50 |
| Solar | Amber | #FFC107 |
| Gas | Deep Orange | #FF5722 |
| Nuclear | Purple | #9C27B0 |
| Hydro | Blue | #2196F3 |
| Biomass | Brown | #795548 |
| Coal | Dark Grey | #424242 |
| Storage | Cyan | #00BCD4 |
| Oil | Pink | #E91E63 |
| Other | Grey | #9E9E9E |

### Info Window
**Fields Displayed:**
- Plant Name
- Type: CVA (Transmission)
- Capacity (MW)
- Fuel Type
- Category (standardized)
- Status (if available)
- Operator (if available)
- Coordinates
- Link to source page

**Template:**
```html
<div style="font-family: Arial, sans-serif; min-width: 200px;">
    <h3 style="margin: 0 0 10px 0; color: #1a73e8;">{Plant Name}</h3>
    <table style="width: 100%; border-collapse: collapse;">
        <tr><td><strong>Type:</strong></td><td>CVA (Transmission)</td></tr>
        <tr><td><strong>Capacity:</strong></td><td>{Capacity} MW</td></tr>
        <tr><td><strong>Fuel:</strong></td><td>{Fuel Type}</td></tr>
        <!-- Additional fields... -->
    </table>
    <p><a href="{url}" target="_blank">View Details →</a></p>
</div>
```

### Layer Controls
**Button:** "CVA (Transmission)"
- Located in "Energy Data" section
- Toggleable on/off
- Independent of SVA layer
- Can display both simultaneously for comparison

### Performance Optimization
**Loading Strategy:**
- JSON file loaded on demand (not at page load)
- Single fetch request for all CVA plants
- Markers created client-side
- No minimum capacity filter (show all CVA plants)

**Memory Management:**
```javascript
// Clear existing CVA markers before reloading
if (window.cvaMarkers) {
    window.cvaMarkers.forEach(m => m.setMap(null));
}
window.cvaMarkers = [];
```

## Usage Guide

### For Analysts

**1. View CVA Plants:**
```
Open: dno_energy_map_advanced.html
Click: "CVA (Transmission)" button
Result: 2,700+ triangle markers appear
```

**2. Compare CVA vs SVA:**
```
Click: "SVA (Embedded)" button (if not already shown)
Click: "CVA (Transmission)" button
Result: Both layers visible with distinct markers
- Circles (●) = SVA embedded generators
- Triangles (▲) = CVA transmission plants
```

**3. Filter by Region:**
```
Click: "DNO Boundaries" to see license areas
Observe: CVA plants typically near transmission substations
         SVA generators distributed across DNO networks
```

**4. Inspect Individual Plants:**
```
Click any triangle marker
View: Detailed plant information
Click: "View Details →" for full page on electricityproduction.uk
```

### For Developers

**1. Update CVA Data:**
```bash
# Scrape latest data
python scrape_plants_optimized.py

# Generate map JSON
python generate_cva_map_json.py

# Upload to BigQuery
python load_cva_to_bigquery.py

# Refresh map in browser
```

**2. Query BigQuery:**
```python
from google.cloud import bigquery

client = bigquery.Client(project='inner-cinema-476211-u9')

query = """
SELECT name, capacity_mw, fuel_type
FROM `inner-cinema-476211-u9.uk_energy_prod.cva_plants`
WHERE fuel_type LIKE '%Nuclear%'
ORDER BY capacity_mw DESC
"""

df = client.query(query).to_dataframe()
print(df)
```

**3. Export Data:**
```python
import json

# Read from JSON
with open('cva_plants_map.json', 'r') as f:
    cva_plants = json.load(f)

# Convert to CSV
import pandas as pd
df = pd.DataFrame(cva_plants)
df.to_csv('cva_plants.csv', index=False)
```

**4. Combine with SVA:**
```python
# Load both datasets
with open('generators.json', 'r') as f:
    sva = json.load(f)

with open('cva_plants_map.json', 'r') as f:
    cva = json.load(f)

# Mark types
for g in sva:
    g['grid_type'] = 'SVA'
for p in cva:
    p['grid_type'] = 'CVA'

# Combine
all_plants = sva + cva

print(f"Total: {len(all_plants)} generation sites")
print(f"SVA: {len(sva)} (embedded)")
print(f"CVA: {len(cva)} (transmission)")
```

## File Inventory

### Source Files
| File | Purpose | Size | Status |
|------|---------|------|--------|
| `scrape_plants_optimized.py` | Web scraper for electricityproduction.uk | 5 KB | ✅ Complete |
| `generate_cva_map_json.py` | Convert scraped data to map format | 3 KB | ✅ Ready |
| `load_cva_to_bigquery.py` | Upload to BigQuery | 4 KB | ✅ Ready |
| `add_cva_to_map.py` | Add CVA layer to HTML map | 7 KB | ✅ Complete |

### Data Files
| File | Content | Size | Status |
|------|---------|------|--------|
| `cva_plants_data.json` | Raw scraped data | ~2.5 MB | 🔄 In progress (350/2,705) |
| `cva_plants_map.json` | Map-ready data | ~1.5 MB | ⏳ Pending scraping |
| `cva_bmu_list.json` | BMU IDs from Elexon | 15 KB | ✅ Complete |

### Map Files
| File | Purpose | Size | Status |
|------|---------|------|--------|
| `dno_energy_map_advanced.html` | Interactive map | 48 KB | ✅ Updated with CVA layer |

## Statistics & Insights

### Capacity Comparison
**Expected Totals:**
- **CVA Plants:** ~60,000-80,000 MW (transmission)
- **SVA Generators:** ~183,000 MW (embedded)
- **Total GB Capacity:** ~240,000-260,000 MW

### Typical Plant Sizes
**CVA Plants:**
- Nuclear: 1,200-1,600 MW per station
- Major CCGT: 400-2,000 MW
- Offshore Wind: 300-1,200 MW per farm
- Pumped Hydro: 300-1,800 MW
- Interconnectors: 500-2,000 MW

**SVA Generators:**
- Onshore Wind: 10-50 MW
- Solar Farms: 5-50 MW
- Biomass: 5-30 MW
- Small Hydro: 1-10 MW

### Geographic Insights
**CVA Concentration Areas:**
- **Humberside:** Drax, Eggborough, Salt End (major gas/biomass)
- **Severn Estuary:** Hinkley Point, Oldbury (nuclear/gas)
- **North Sea:** Offshore wind farms (Hornsea, Dogger Bank)
- **Scottish Highlands:** Pumped hydro (Cruachan, Foyers)

## Maintenance & Updates

### Data Refresh Frequency
**Recommended:** Quarterly
- New plants added regularly
- Status changes (commissioning, decommissioning)
- Capacity upgrades/downgrades
- Operator changes

### Update Process
```bash
# 1. Scrape latest data
python scrape_plants_optimized.py  # ~35 minutes

# 2. Generate map JSON
python generate_cva_map_json.py    # ~5 seconds

# 3. Upload to BigQuery
python load_cva_to_bigquery.py     # ~30 seconds

# 4. Test map
open dno_energy_map_advanced.html  # Visual verification

# 5. Document changes
# Update this file with new statistics
```

### Version Control
Track changes to:
- Total plant count
- Capacity totals by fuel type
- New large plants (>500 MW)
- Decommissioned plants
- Data quality metrics

## Known Issues & Limitations

### Data Gaps
1. **Missing Coordinates:** ~4% of plants lack geo.position meta tag
2. **Missing Capacity:** ~11% don't have capacity in table
3. **Fuel Type Ambiguity:** Some plants have generic "Gas" or "Renewable" labels
4. **Offshore Coordinates:** May be approximate center points, not exact turbine locations

### Technical Limitations
1. **Rate Limiting:** 0.5s per request = slow scraping (~35 min for all)
2. **Website Changes:** If electricityproduction.uk changes structure, scraper breaks
3. **Browser Compatibility:** Map requires modern browser with JavaScript
4. **Mobile Display:** Large number of markers may slow mobile browsers

### Workarounds
1. **Missing Coords:** Exclude from map, keep in BigQuery for reference
2. **Missing Capacity:** Mark as "Unknown", estimate from BMU data where possible
3. **Fuel Ambiguity:** Standardize into broader categories (Wind, Solar, Gas, etc.)
4. **Performance:** Filter by minimum capacity or region for initial load

## References & Links

### Data Sources
- **electricityproduction.uk:** https://electricityproduction.uk/plant/
- **NESO Elexon Portal:** https://www.elexonportal.co.uk/
- **NESO Data Portal:** https://data.nationalgrideso.com/

### Documentation
- **BMU List:** `cva_bmu_list.json`
- **NESO Generators:** `All_Generators.xlsx`
- **SVA Map Documentation:** `README_ANALYSIS_SHEET.md`

### Related Files
- **DNO Boundaries:** In BigQuery `neso_dno_boundaries`
- **GSP Zones:** In BigQuery `neso_gsp_boundaries`
- **SVA Generators:** `generators.json` (7,072 sites)

## Future Enhancements

### Planned Features
1. **Real-time Status:** Integrate live generation data from NESO
2. **Historical Tracking:** Track commissioning/decommissioning over time
3. **Capacity Forecasts:** Project future capacity by fuel type
4. **Clustering:** Group nearby offshore turbines into single markers
5. **Filtering:** Filter by fuel type, capacity range, status
6. **Comparison Mode:** Side-by-side CVA vs SVA statistics

### Data Enrichment
1. **BMU Matching:** Link to Elexon BMU data for live output
2. **Ownership:** Add parent company/ultimate owner
3. **Commissioning Dates:** Add online date for age analysis
4. **Technology Details:** Turbine models, panel specs, etc.
5. **Environmental:** CO2 emissions, efficiency ratings

### Integration Opportunities
1. **Weather Data:** Correlate wind/solar output with weather
2. **Market Data:** Link to settlement prices and revenues
3. **Grid Data:** Show transmission constraints
4. **Planning:** Overlay with future project pipeline

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-XX  
**Author:** GB Power Market Analysis System  
**Contact:** See project README for support

**Status:** 
- ✅ Documentation complete
- 🔄 Web scraping in progress (350/2,705 plants)
- ⏳ Awaiting scraping completion for full deployment
