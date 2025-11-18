# Complete DNO Data Inventory - BigQuery

**Date**: 9 November 2025  
**Project**: GB Power Market JJ  
**BigQuery Project**: `inner-cinema-476211-u9`

---

## Executive Summary

✅ **COMPREHENSIVE DNO DATA AVAILABLE**

| Data Type | Status | Records | Details |
|-----------|--------|---------|---------|
| **DNO License Areas** | ✅ COMPLETE | 14 rows | All UK DNOs |
| **DNO Boundaries** | ✅ COMPLETE | 14 polygons | Geographic coverage |
| **GSP (Grid Supply Points)** | ✅ COMPLETE | 333 points | Connection points |
| **GSP Boundaries** | ✅ COMPLETE | 333 polygons | Supply areas |
| **Generators with DNO** | ✅ COMPLETE | 7,072 assets | 183 GW capacity |
| **DUoS Tariff Data** | ⚠️ EMPTY | 0 rows | Need to populate |

---

## 1. DNO License Areas (14 UK DNOs)

### Table: `uk_energy_prod.neso_dno_reference`
**Status**: ✅ COMPLETE (14 rows)  
**Location**: US region

**All 14 UK Distribution Network Operators:**

| MPAN | GSP | DNO Code | Operator Name | Coverage Area |
|------|-----|----------|---------------|---------------|
| 10 | A | UKPN-EPN | UK Power Networks (Eastern) | Norfolk, Suffolk, Essex, Hertfordshire, Bedfordshire |
| 11 | B | NGED-EM | National Grid ED – East Midlands | Nottinghamshire, Leicestershire, Derbyshire, Lincolnshire |
| 12 | C | UKPN-LPN | UK Power Networks (London) | Greater London |
| 13 | D | SP-Manweb | SP Energy Networks (SPM) | Merseyside, North Mid Wales, Cheshire, Wirral |
| 14 | E | NGED-WM | National Grid ED – West Midlands | West Midlands, Worcestershire, Warwickshire, Shropshire, Staffordshire |
| 15 | F | NPg-NE | Northern Powergrid (North East) | Northumberland, Tyne & Wear, Durham, Teesside |
| 16 | G | ENWL | Electricity North West | Lancashire, Cumbria, Greater Manchester, Cheshire |
| 17 | P | SSE-SHEPD | Scottish Hydro Electric Power Distribution | Highlands, Islands, Northern Scotland |
| 18 | N | SP-Distribution | SP Energy Networks (SPD) | Central & Southern Scotland, Dumfries & Galloway |
| 19 | J | UKPN-SPN | UK Power Networks (South Eastern) | Kent, Surrey, Sussex |
| 20 | H | SSE-SEPD | Southern Electric Power Distribution | Berkshire, Hampshire, Dorset, Wiltshire, Oxfordshire |
| 21 | K | NGED-SWales | National Grid ED – South Wales | South Wales, Monmouthshire, Gwent |
| 22 | L | NGED-SW | National Grid ED – South West | Devon, Cornwall, Somerset, Dorset, Gloucestershire |
| 23 | M | NPg-Y | Northern Powergrid (Yorkshire) | Yorkshire, North Lincolnshire |

**Data Available:**
- MPAN distributor ID (10-23)
- DNO unique keys
- Market participant IDs
- GSP group assignments
- Website URLs
- Contact information
- Primary coverage areas

---

## 2. DNO Boundaries (Geographic Coverage)

### Table: `uk_energy_prod.neso_dno_boundaries`
**Status**: ✅ COMPLETE (14 rows)  
**Type**: GEOGRAPHY (polygons)

**Coverage:**
- All 14 DNO license area boundaries
- Geographic polygons for mapping
- Area names and identifiers
- Can be joined with generators for territorial analysis

**Use Cases:**
- Map visualization of DNO territories
- Identify which DNO serves a specific location
- Calculate generator density by DNO region
- Network planning and constraint analysis

---

## 3. GSP (Grid Supply Point) Data

### Table: `uk_energy_prod.neso_gsp_boundaries`
**Status**: ✅ COMPLETE (333 rows)  
**Location**: US region

**Summary:**
- **Total GSPs**: 333 across Great Britain
- **Total Area**: 240,058 km²
- **Coverage**: Complete GB transmission-distribution interface points

**Structure:**
```sql
gsp_id           STRING    -- Unique identifier
gsp_name         STRING    -- GSP name
gsp_group        STRING    -- GSP group code (_A to _P)
region_name      STRING    -- Region description
boundary         GEOGRAPHY -- GSP catchment area
area_sqkm        FLOAT     -- Area in km²
```

### Table: `uk_energy_prod.neso_gsp_groups`
**Status**: ✅ COMPLETE (14 rows)

**GSP Group Mapping:**
- Links GSP groups to DNO operators
- Primary coverage area descriptions
- Used for settlement and pricing

---

## 4. Generators with DNO Linkage

### Table: `uk_energy_prod.sva_generators_with_coords`
**Status**: ✅ COMPLETE (7,072 generators, 183 GW)

**Generator Coverage by DNO:**

| DNO | Generators | Total Capacity | Fuel Types |
|-----|------------|----------------|------------|
| Eastern Power Networks (EPN) | 814 | 23,586 MW | 9 types |
| National Grid ED (East Midlands) | 767 | 20,198 MW | 11 types |
| Northern Powergrid (Yorkshire) | 580 | 19,614 MW | 8 types |
| Scottish Hydro (SHEPD) | 709 | 19,444 MW | 13 types |
| Southern Electric (SEPD) | 702 | 18,409 MW | 14 types |
| National Grid ED (West Midlands) | 460 | 13,897 MW | 10 types |
| Northern Powergrid (Northeast) | 387 | 12,401 MW | 10 types |
| South Eastern Power Networks | 321 | 10,582 MW | 7 types |
| Electricity North West | 523 | 10,490 MW | 15 types |
| SP Distribution (Scotland) | 468 | 10,027 MW | 11 types |
| National Grid ED (South West) | 558 | 8,542 MW | 11 types |
| SP Manweb | 358 | 7,444 MW | 9 types |
| National Grid ED (South Wales) | 303 | 5,743 MW | 11 types |
| London Power Networks | 94 | 1,533 MW | 5 types |
| Other | 28 | 1,051 MW | various |

**Total**: 7,072 generators, **182,960 MW** capacity

**Fuel Type Diversity:**
- Solar: Most prevalent
- Wind: Onshore distributed
- Biomass: Rural areas
- Hydro: Scotland (SHEPD)
- Gas: Industrial areas
- CHP: Commercial/industrial
- Battery: Growing deployment
- Others: Landfill gas, waste, etc.

### Table: `uk_energy_prod.offshore_wind_farms`
**Status**: ✅ COMPLETE (35 projects)

**GSP Zone Linkage:**
- Offshore wind connected to specific GSP zones
- Distance to GSP calculated
- Regional assignments (East Anglia, North Sea, etc.)
- Example: Dudgeon (402 MW) → EEA1 zone, 87.3 km to GSP

---

## 5. Large Power Stations (CVA)

### Table: `uk_energy_prod.cva_plants`
**Status**: ✅ COMPLETE (1,581 plants)  
**DNO Linkage**: ⚠️ Not directly linked to DNO

**Coverage:**
- Large transmission-connected plants
- Nuclear, CCGT, coal, large offshore wind
- Typically >100 MW capacity
- Connected at transmission (400kV/275kV) not distribution level

**Note**: CVA plants connect at National Grid transmission level, above DNO networks. They don't have direct DNO assignment but affect regional supply.

---

## 6. Database Structure

### Datasets in BigQuery:

#### `uk_energy_prod` (US region) - Main Dataset
**Tables:**
- `neso_dno_reference` - 14 rows (DNO master list)
- `neso_dno_boundaries` - 14 rows (DNO geographic boundaries)
- `neso_gsp_groups` - 14 rows (GSP to DNO mapping)
- `neso_gsp_boundaries` - 333 rows (GSP catchment areas)
- `sva_generators_with_coords` - 7,072 rows (distributed generation)
- `cva_plants` - 1,581 rows (large power stations)
- `offshore_wind_farms` - 35 rows (offshore wind)

#### `gb_power` (EU region) - Secondary Dataset
**Tables:**
- `dno_license_areas` - 14 rows (DNO reference, alternative format)
- `dno_boundaries` - 0 rows (EMPTY - duplicate structure)
- `gsp_boundaries` - 0 rows (EMPTY - duplicate structure)
- `duos_tariff_definitions` - 0 rows (EMPTY - needs population)
- `duos_time_bands` - 0 rows (EMPTY - needs population)
- `duos_unit_rates` - 0 rows (EMPTY - needs population)

---

## 7. Key Relationships

### Data Hierarchy:
```
National Grid (Transmission)
    ↓
GSP (Grid Supply Point) - 333 points
    ↓
DNO Network (Distribution) - 14 operators
    ↓
Generators/Customers
    - SVA: 7,072 small-scale (embedded)
    - CVA: 1,581 large-scale (transmission)
    - Offshore Wind: 35 projects (transmission or distribution)
```

### Query Relationships:
```sql
-- Join generators to DNO
SELECT g.name, g.capacity_mw, d.dno_name
FROM sva_generators_with_coords g
JOIN neso_dno_reference d ON g.dno = d.dno_name

-- Find generators in specific DNO area
SELECT *
FROM sva_generators_with_coords
WHERE dno = 'Eastern Power Networks (EPN)'

-- GSP to DNO mapping
SELECT gsp.gsp_name, grp.dno_name, gsp.area_sqkm
FROM neso_gsp_boundaries gsp
JOIN neso_gsp_groups grp ON gsp.gsp_group = grp.gsp_group_id
```

---

## 8. Use Cases & Analysis

### What You Can Do With This Data:

#### 1. **Network Constraint Analysis**
- Identify DNO areas with high generation density
- Calculate generation/demand ratios by DNO
- Find potential network bottlenecks

```sql
SELECT 
    dno,
    COUNT(*) as generator_count,
    SUM(capacity_mw) as total_mw,
    AVG(capacity_mw) as avg_mw_per_unit
FROM sva_generators_with_coords
GROUP BY dno
ORDER BY total_mw DESC
```

#### 2. **Renewable Penetration by DNO**
- Map renewable energy adoption by region
- Identify leading/lagging DNO areas
- Solar/wind deployment patterns

```sql
SELECT 
    dno,
    fuel_type,
    COUNT(*) as count,
    SUM(capacity_mw) as capacity_mw
FROM sva_generators_with_coords
WHERE fuel_type IN ('Solar', 'Wind', 'Hydro')
GROUP BY dno, fuel_type
ORDER BY dno, capacity_mw DESC
```

#### 3. **DUoS Charge Calculations** (once tariffs populated)
- Calculate distribution costs by location
- Optimize battery arbitrage per DNO
- Model demand response value by region

```sql
-- Future query once DUoS tariffs populated
SELECT 
    g.name,
    g.dno,
    d.dno_key,
    r.unit_rate as duos_rate
FROM sva_generators_with_coords g
JOIN dno_license_areas d ON g.dno = d.dno_name
JOIN duos_unit_rates r ON d.dno_key = r.dno_key
WHERE r.time_band = 'Red'
```

#### 4. **Geographic Visualization**
- Plot generators on map by DNO territory
- Show DNO boundaries with generation overlays
- GSP-level heatmaps

```sql
-- Generators within DNO boundary
SELECT g.*, d.boundary as dno_boundary
FROM sva_generators_with_coords g
JOIN neso_dno_boundaries d 
    ON ST_WITHIN(ST_GEOGPOINT(g.longitude, g.latitude), d.boundary)
```

#### 5. **Market Analysis**
- Compare DNO charging methodologies
- Identify favorable connection locations
- Network capacity planning

---

## 9. Data Quality & Completeness

### ✅ Excellent Coverage:
- All 14 UK DNOs mapped
- 7,072 distributed generators with DNO assignment
- 333 GSPs with boundaries
- Geographic data (GEOGRAPHY type) for spatial analysis
- Generator coordinates for mapping

### ⚠️ Gaps & Limitations:
1. **CVA Plants**: No direct DNO linkage (they're transmission-connected)
2. **DUoS Tariffs**: Table structure exists but EMPTY (0 rows)
3. **Some Name Variations**: DNO names not 100% standardized across tables
4. **IDNO Data**: No Independent DNO data yet
5. **Historical Changes**: No time-series of DNO boundary changes

### 🔧 Data Quality Notes:
- **Coordinates**: High accuracy for mapping
- **Capacity**: MW values reliable
- **Fuel Types**: Well categorized
- **DNO Names**: Slight inconsistencies (e.g., "Plc" vs "plc" vs none)

---

## 10. Next Steps & Recommendations

### Immediate Use (Ready Now):
1. ✅ **Map Visualization**: Plot all generators by DNO territory
2. ✅ **Network Analysis**: Calculate generation density by DNO
3. ✅ **Renewable Tracking**: Monitor solar/wind deployment by region
4. ✅ **Constraint Identification**: Find high-generation DNO areas

### Short-Term Enhancements:
1. **Standardize DNO Names**: Create clean lookup table
2. **Add IDNO Data**: Independent DNO operators and connection points
3. **Populate DUoS Tariffs**: Import from DNO websites
4. **Link CVA Plants**: Add estimated DNO regions for large plants

### Long-Term:
1. **Demand Data by DNO**: Add consumption patterns
2. **Network Capacity**: DNO substation ratings
3. **Historical Analysis**: Time-series of generator additions
4. **Forecasting**: Predict future DNO network loading

---

## 11. Query Examples

### Find All Generators in a Specific DNO:
```sql
SELECT 
    name,
    capacity_mw,
    fuel_type,
    gsp,
    latitude,
    longitude
FROM `inner-cinema-476211-u9.uk_energy_prod.sva_generators_with_coords`
WHERE dno = 'Eastern Power Networks (EPN)'
ORDER BY capacity_mw DESC
LIMIT 10
```

### DNO Summary Statistics:
```sql
SELECT 
    d.dno_name,
    d.gsp_group_name,
    COUNT(g.name) as generator_count,
    SUM(g.capacity_mw) as total_capacity_mw,
    AVG(g.capacity_mw) as avg_capacity_mw,
    COUNT(DISTINCT g.fuel_type) as fuel_type_count
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference` d
LEFT JOIN `inner-cinema-476211-u9.uk_energy_prod.sva_generators_with_coords` g
    ON d.dno_name = g.dno
GROUP BY d.dno_name, d.gsp_group_name
ORDER BY total_capacity_mw DESC
```

### Generators Near GSP:
```sql
SELECT 
    g.name,
    g.capacity_mw,
    g.dno,
    g.gsp,
    gsp_b.gsp_name,
    gsp_b.area_sqkm
FROM `inner-cinema-476211-u9.uk_energy_prod.sva_generators_with_coords` g
JOIN `inner-cinema-476211-u9.uk_energy_prod.neso_gsp_boundaries` gsp_b
    ON ST_WITHIN(
        ST_GEOGPOINT(g.longitude, g.latitude),
        gsp_b.boundary
    )
WHERE g.capacity_mw > 10
ORDER BY g.capacity_mw DESC
LIMIT 20
```

---

## 12. Summary Table

| Data Element | Table | Rows | Status | Location |
|--------------|-------|------|--------|----------|
| DNO License Areas | `neso_dno_reference` | 14 | ✅ Complete | US |
| DNO Boundaries | `neso_dno_boundaries` | 14 | ✅ Complete | US |
| GSP Groups | `neso_gsp_groups` | 14 | ✅ Complete | US |
| GSP Boundaries | `neso_gsp_boundaries` | 333 | ✅ Complete | US |
| SVA Generators | `sva_generators_with_coords` | 7,072 | ✅ Complete | US |
| CVA Plants | `cva_plants` | 1,581 | ✅ Complete | US |
| Offshore Wind | `offshore_wind_farms` | 35 | ✅ Complete | US |
| DUoS Tariffs | `duos_*` tables | 0 | ⚠️ Empty | EU |

**Total Generation Mapped to DNOs**: **182,960 MW** across **7,072 assets**

---

## 13. Technical Details

### Accessing DNO Data:
```python
from google.cloud import bigquery
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'inner-cinema-credentials.json'

# US region (main DNO data)
client = bigquery.Client(project='inner-cinema-476211-u9', location='US')

# Query DNO reference
query = """
SELECT * 
FROM `inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference`
ORDER BY mpan_distributor_id
"""

df = client.query(query).to_dataframe()
print(df)
```

### Command Line Access:
```bash
# List all DNOs
bq query --use_legacy_sql=false --location=US "
SELECT mpan_distributor_id, dno_key, dno_name 
FROM \`inner-cinema-476211-u9.uk_energy_prod.neso_dno_reference\`
ORDER BY mpan_distributor_id"

# Count generators by DNO
bq query --use_legacy_sql=false --location=US "
SELECT dno, COUNT(*) as count, SUM(capacity_mw) as total_mw
FROM \`inner-cinema-476211-u9.uk_energy_prod.sva_generators_with_coords\`
GROUP BY dno
ORDER BY total_mw DESC"
```

---

## Conclusion

**✅ You have EXCELLENT DNO data coverage in BigQuery!**

- All 14 UK DNOs fully mapped
- 7,072 generators (183 GW) linked to DNOs
- 333 GSPs with geographic boundaries
- Complete spatial data for mapping and analysis
- Ready for network constraint analysis, renewable tracking, and geographic visualization

**The only gap is DUoS tariff data** (table structure exists but needs population from DNO websites).

---

**Report Generated**: 9 November 2025  
**Status**: Comprehensive DNO data available and ready to use  
**Next**: Consider populating DUoS tariff tables for complete coverage
