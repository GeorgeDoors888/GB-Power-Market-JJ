# Offshore Wind & DNO API Data Sources

## ✅ Completed Tasks

### 1. Imported Wikipedia Offshore Wind Data
**Script**: `import_offshore_wind_farms.py`

**Results**:
- ✅ **43 offshore wind farms** imported (Wikipedia July 2025 data)
- ⚡ **16,410 MW** total capacity
- 🌬️ **2,869 turbines** total
- 📤 Uploaded to BigQuery: `inner-cinema-476211-u9.uk_energy_prod.offshore_wind_farms`

**Updated Table Schema**:
```sql
name                STRING    -- Farm name
country             STRING    -- England/Scotland/Wales
latitude            FLOAT64   -- GPS coordinates
longitude           FLOAT64
capacity_mw         FLOAT64   -- Total capacity
turbine_count       INT64     -- Number of turbines
manufacturer        STRING    -- Vestas, Siemens, etc.
model               STRING    -- Turbine model
commissioned_year   INT64     -- Year operational
strike_price        FLOAT64   -- CfD strike price (£/MWh)
owner               STRING    -- Operating company
status              STRING    -- Operational/Under Construction
source              STRING    -- Data source
gsp_zone            STRING    -- GSP zone assignment
gsp_region          STRING    -- Regional grouping
_uploaded_at        TIMESTAMP -- Upload time
```

### 2. Cross-Referenced with BMU Data

**Key Findings**:
- ✅ **33 offshore farms** matched with BMU registrations (14,966 MW)
- ❌ **10 offshore farms** NOT in BMU (1,444 MW missing):
  - Blyth Offshore Demonstrator (41.5 MW)
  - European Offshore Wind Deployment Centre (93 MW)
  - Gwynt y Môr (576 MW) ⚠️ Large farm missing!
  - Kentish Flats (140 MW)
  - Lynn and Inner Dowsing (194 MW)
  - Methil (7 MW)
  - Rhyl Flats (90 MW)
  - Robin Rigg (180 MW)
  - Scroby Sands (60 MW)
  - Teesside (62 MW)

**Capacity Analysis**:
- BMU Wind Total: **27,561 MW** (248 units - includes onshore + offshore)
- Offshore Only: **16,410 MW** (43 farms from Wikipedia)
- Difference: **~11,151 MW** = Onshore wind farms in BMU data

**Conclusion**: BMU registration includes BOTH onshore and offshore wind. Our new offshore_wind_farms table has more detailed metadata (turbine counts, manufacturers, strike prices, GPS coordinates).

---

## 🌐 DNO Open Data APIs Discovered

### Script: `explore_dno_apis.py`

### ✅ Active APIs (2 of 6)

#### 1. UK Power Networks (UKPN)
- **Regions**: London, South East, Eastern
- **API**: https://ukpowernetworks.opendatasoft.com/api/explore/v2.1
- **Web**: https://ukpowernetworks.opendatasoft.com/explore/
- **Status**: ✅ ACTIVE - 126 datasets
- **Format**: OpenDataSoft API v2.1

**Key Datasets**:
```
ukpn-rota-load-disconnection           - Rota load plans
ukpn-network-losses                    - Network loss data
ukpn-33kv-circuit-operational-data     - Circuit operational data
ltds-table-1-circuit-data              - Long-term circuit data
ltds-table-7-operational-restrictions  - Operational constraints
ukpn-optimise-prime                    - EV trial data
```

**API Examples**:
```bash
# List all datasets
curl "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets"

# Get records from a dataset
curl "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/DATASET_ID/records?limit=100"

# Query with filters
curl "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets/DATASET_ID/records?where=capacity>100&limit=50"
```

#### 2. Northern Powergrid (NPG)
- **Regions**: Yorkshire, North East
- **API**: https://northernpowergrid.opendatasoft.com/api/explore/v2.1
- **Web**: https://northernpowergrid.opendatasoft.com/explore/
- **Status**: ✅ ACTIVE - 86 datasets
- **Format**: OpenDataSoft API v2.1

**Key Datasets**:
```
ltds-appendix-5                        - Load information
```

### ❌ Inactive/Different Format APIs (4 of 6)

#### 3. National Grid Electricity Distribution (NGED)
- **Regions**: South West, South Wales, West Midlands, East Midlands
- **Status**: ❌ NOT FOUND at standard URL
- **Alternative**: May have custom portal at https://www.nationalgrid.co.uk/electricity-distribution/data-portal
- **Action Needed**: Manual investigation

#### 4. Scottish and Southern Electricity Networks (SSEN)
- **Regions**: Scottish Hydro, Southern England
- **Status**: ❌ NOT FOUND at standard URL
- **Alternative**: Likely at https://www.ssen.co.uk/our-services/data-portal/
- **Action Needed**: Manual investigation

#### 5. Electricity North West (ENWL)
- **Regions**: North West England
- **Status**: ❌ NOT FOUND at standard URL
- **Alternative**: May be at https://www.enwl.co.uk/zero-carbon/innovation/open-data/
- **Action Needed**: Manual investigation

#### 6. SP Energy Networks (SPEN)
- **Regions**: Central Scotland, Merseyside, Cheshire, North Wales
- **Status**: ⚠️ HTTP 403 (Authentication required)
- **Alternative**: https://www.spenergynetworks.co.uk/pages/open_data.aspx
- **Action Needed**: Check if API key required

---

## 🔍 How We Access DNO Data

### OpenDataSoft Platform (UKPN, NPG)

**Architecture**:
```
Browser/Script
    ↓
OpenDataSoft API v2.1
    ↓
/catalog/datasets        → List all datasets
/datasets/{id}/records   → Get data records
/datasets/{id}/exports   → Export CSV/JSON/GeoJSON
```

**Authentication**: None required (public API)

**Rate Limits**: Unknown, but generous for public use

**Data Formats**:
- JSON (default)
- CSV export
- GeoJSON (for geographic data)
- Excel export

### Example: Fetching UKPN Network Data

```python
import requests
import pandas as pd

# 1. List all datasets
catalog_url = "https://ukpowernetworks.opendatasoft.com/api/explore/v2.1/catalog/datasets"
response = requests.get(catalog_url)
datasets = response.json()

# 2. Get records from specific dataset
dataset_id = "ukpn-33kv-circuit-operational-data-monthly"
records_url = f"{catalog_url}/{dataset_id}/records?limit=1000"
data = requests.get(records_url).json()

# 3. Convert to DataFrame
df = pd.json_normalize(data['results'])
print(df.head())
```

### Alternative DNO Data Sources

Since 4 DNOs don't use OpenDataSoft, here are their data portals:

**NGED (National Grid ED)**:
- Portal: https://www.nationalgrid.co.uk/electricity-distribution/data-portal
- Format: Manual downloads, CSV files
- Data: Generation capacity, constraints, demand

**SSEN**:
- Portal: https://www.ssen.co.uk/our-services/data-portal/
- Format: Manual downloads, interactive maps
- Data: Generation connections, network capacity

**ENWL**:
- Portal: https://www.enwl.co.uk/zero-carbon/innovation/open-data/
- Format: CSV/Excel downloads
- Data: Low carbon technologies, flexibility services

**SPEN**:
- Portal: https://www.spenergynetworks.co.uk/pages/open_data.aspx
- Format: CSV downloads, possibly API with auth
- Data: Network information, generation register

---

## 📊 Data Quality Comparison

| Source | Coverage | Freshness | Detail Level | API Access |
|--------|----------|-----------|--------------|------------|
| **BMU Registration** | All grid-connected | Static snapshot | Basic (capacity, fuel, GSP) | ✅ BigQuery |
| **Offshore Wind Table** | Offshore only | Updated manually | High (turbines, models, GPS) | ✅ BigQuery |
| **UKPN API** | UKPN regions only | Real-time/Monthly | Very High (circuit-level) | ✅ REST API |
| **NPG API** | NPG regions only | Varies | High | ✅ REST API |
| **Other DNOs** | Per DNO | Varies | High | ⚠️ Manual downloads |

---

## 🎯 Next Steps

### Immediate (Can Do Now)
1. ✅ Query updated offshore_wind_farms table in BigQuery
2. ✅ Use UKPN API to fetch circuit-level data for London/SE/Eastern
3. ✅ Use NPG API to fetch data for Yorkshire/North East

### Short Term (This Week)
1. **Create automated ingestion** for UKPN and NPG APIs
2. **Manual scraping** of NGED, SSEN, ENWL, SPEN data portals
3. **Map offshore wind farms** to DNO connection points
4. **Update Dashboard** with offshore wind capacity by region

### Medium Term (This Month)
1. **Build unified DNO data table** combining all 6 DNO sources
2. **Cross-reference** generation capacity across:
   - BMU registration
   - Offshore wind table  
   - DNO connection data
   - SVA generator list
3. **Create data quality dashboard** showing coverage gaps
4. **Automate updates** via cron jobs for API sources

---

## 📁 Files Created

```
import_offshore_wind_farms.py                    - Wikipedia → BigQuery import
explore_dno_apis.py                              - DNO API explorer
offshore_wind_farms_backup_20251121_102008.csv   - Backup of imported data
dno_api_exploration_20251121_102013.json         - API exploration results
```

---

## 🔗 Useful Links

**BigQuery Table**:
```sql
SELECT * FROM `inner-cinema-476211-u9.uk_energy_prod.offshore_wind_farms`
ORDER BY capacity_mw DESC
```

**DNO APIs**:
- UKPN: https://ukpowernetworks.opendatasoft.com/explore/
- NPG: https://northernpowergrid.opendatasoft.com/explore/

**Data Portals** (Manual):
- NGED: https://www.nationalgrid.co.uk/electricity-distribution/data-portal
- SSEN: https://www.ssen.co.uk/our-services/data-portal/
- ENWL: https://www.enwl.co.uk/zero-carbon/innovation/open-data/
- SPEN: https://www.spenergynetworks.co.uk/pages/open_data.aspx

**Wikipedia Source**:
- https://en.wikipedia.org/wiki/List_of_offshore_wind_farms_in_the_United_Kingdom

---

**Status**: ✅ Complete  
**Date**: November 21, 2025  
**Offshore Wind Farms**: 43 farms, 16,410 MW imported  
**Active DNO APIs**: 2 of 6 (UKPN, NPG)
